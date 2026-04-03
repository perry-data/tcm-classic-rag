#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DB_PATH = "artifacts/zjshl_mvp.db"
DEFAULT_POLICY_PATH = "layered_enablement_policy.json"
DEFAULT_EXAMPLES_OUT = "artifacts/retrieval_examples.json"
DEFAULT_SMOKE_OUT = "artifacts/retrieval_smoke_checks.md"

DEFAULT_EXAMPLES = [
    {
        "example_id": "strong_chunk_backref",
        "query_text": "黄连汤方的条文是什么？",
        "expected_mode": "strong",
    },
    {
        "example_id": "weak_with_review_notice",
        "query_text": "烧针益阳而损阴是什么意思？",
        "expected_mode": "weak_with_review_notice",
    },
    {
        "example_id": "refuse_no_match",
        "query_text": "书中有没有提到量子纠缠？",
        "expected_mode": "refuse",
    },
]

SOURCE_BUDGETS = {
    "safe_chunks": 8,
    "safe_main_passages_primary": 6,
    "safe_main_passages_secondary": 4,
    "full_annotations_raw": 3,
    "full_passages_ledger": 2,
    "ambiguous_related_material": 1,
}

DEFAULT_TOTAL_LIMIT = 24
PRIMARY_LIMIT = 3
SECONDARY_LIMIT = 5
RISK_LIMIT = 5

WEIGHT_BONUS = {
    "highest": 6.0,
    "high": 5.0,
    "medium": 4.0,
    "medium_low": 3.0,
    "low": 2.0,
    "lowest": 1.0,
    "off": 0.0,
}

QUESTION_NOISE_PHRASES = [
    "请问",
    "书中",
    "文中",
    "伤寒论里",
    "伤寒论中",
    "有没有",
    "有无",
    "是否",
    "怎么",
    "如何",
    "是什么意思",
    "是什么",
    "什么意思",
    "条文",
    "原文",
    "提到",
    "讲到",
    "说到",
    "关于",
    "的吗",
    "吗",
    "呢",
    "么",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal retrieval on zjshl_mvp.db.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--query", help="Run a single query and print JSON to stdout.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_EXAMPLES_OUT,
        help="Where to write the default example results JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_SMOKE_OUT,
        help="Where to write the smoke check markdown report.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=DEFAULT_TOTAL_LIMIT,
        help="Maximum number of raw candidates kept after ranking.",
    )
    return parser.parse_args()


def log(message: str) -> None:
    print(message, flush=True)


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = text.lower()
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized)
    return normalized


def extract_focus_text(query_text: str) -> str:
    focus = compact_text(query_text)
    for phrase in sorted(QUESTION_NOISE_PHRASES, key=len, reverse=True):
        focus = focus.replace(compact_text(phrase), "")
    focus = re.sub(r"[的是呢吗么]+$", "", focus)
    return focus or compact_text(query_text)


def build_query_terms(focus_text: str) -> list[str]:
    if not focus_text:
        return []
    terms: set[str] = {focus_text}
    if 2 <= len(focus_text) <= 24:
        for n in range(min(4, len(focus_text)), 1, -1):
            for idx in range(0, len(focus_text) - n + 1):
                terms.add(focus_text[idx : idx + n])
    return sorted(terms, key=lambda item: (-len(item), item))


def compute_text_match_score(query_focus: str, query_terms: list[str], candidate_text: str) -> tuple[float, list[str]]:
    candidate_compact = compact_text(candidate_text)
    if not candidate_compact:
        return 0.0, []

    score = 0.0
    matched_terms: list[str] = []

    if query_focus and query_focus in candidate_compact:
        score += 100.0 + min(len(query_focus) * 4.0, 40.0)
        matched_terms.append(query_focus)

    for term in query_terms:
        if term == query_focus:
            continue
        if term in candidate_compact:
            if len(term) >= 4:
                score += 8.0
            elif len(term) == 3:
                score += 4.0
            else:
                score += 1.5
            if term not in matched_terms and len(matched_terms) < 12:
                matched_terms.append(term)

    return score, matched_terms


def preview_text(text: str | None, limit: int = 80) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[:limit] + "..."


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


@dataclass
class RetrievalEngine:
    db_path: Path
    policy_path: Path
    candidate_limit: int = DEFAULT_TOTAL_LIMIT

    def __post_init__(self) -> None:
        self.policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._assert_policy_guards()
        self.unified_rows = [dict(row) for row in self.conn.execute("SELECT * FROM vw_retrieval_records_unified")]

    def close(self) -> None:
        self.conn.close()

    def _assert_policy_guards(self) -> None:
        annotation_link_count = self.conn.execute(
            "SELECT COUNT(*) FROM vw_retrieval_records_unified WHERE source_object = 'annotation_links'"
        ).fetchone()[0]
        if annotation_link_count != 0:
            raise ValueError("annotation_links leaked into vw_retrieval_records_unified")

    def build_request(self, query_text: str) -> dict[str, Any]:
        query_focus = extract_focus_text(query_text)
        return {
            "query_text": query_text,
            "query_text_normalized": query_focus,
            "target_mode": "strong_first",
            "allow_levels": ["A", "B", "C"],
            "blocked_sources": ["annotation_links"],
            "source_priority": self.policy["stage_policy"]["retrieval_stage"]["priority_order"],
            "candidate_budget": {
                "total_limit": self.candidate_limit,
                "per_source_soft_limit": SOURCE_BUDGETS,
            },
            "scope_filters": {"book_id": "ZJSHL", "chapter_id": None},
        }

    def retrieve(self, query_text: str) -> dict[str, Any]:
        request = self.build_request(query_text)
        raw_candidates = self._collect_raw_candidates(request)
        resolved = self._resolve_candidates(raw_candidates)
        slots = self._assemble_slots(resolved)
        mode_info = self._determine_mode(slots)
        return {
            "query_request": request,
            "raw_candidates": raw_candidates,
            "primary_evidence": slots["primary_evidence"],
            "secondary_evidence": slots["secondary_evidence"],
            "risk_materials": slots["risk_materials"],
            "retrieval_trace": resolved["retrieval_trace"],
            "mode": mode_info["mode"],
            "mode_reason": mode_info["mode_reason"],
            "runtime_risk_flags": mode_info["runtime_risk_flags"],
            "annotation_links_enabled": False,
        }

    def _collect_raw_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query_focus = request["query_text_normalized"]
        query_terms = build_query_terms(query_focus)
        scored: list[dict[str, Any]] = []

        for row in self.unified_rows:
            if row["source_object"] == "annotation_links":
                continue
            text_score, matched_terms = compute_text_match_score(query_focus, query_terms, row["normalized_text"])
            if text_score <= 0:
                continue
            weight_bonus = WEIGHT_BONUS.get(row["default_weight_tier"], 0.0)
            combined_score = text_score + weight_bonus
            candidate = dict(row)
            candidate.update(
                {
                    "text_match_score": round(text_score, 3),
                    "weight_bonus": weight_bonus,
                    "combined_score": round(combined_score, 3),
                    "matched_terms": matched_terms,
                }
            )
            scored.append(candidate)

        if not scored:
            return []

        max_text_score = max(candidate["text_match_score"] for candidate in scored)
        minimum_text_score = max(2.0, max_text_score * 0.2)
        scored = [candidate for candidate in scored if candidate["text_match_score"] >= minimum_text_score]

        scored.sort(
            key=lambda row: (
                -row["combined_score"],
                -row["text_match_score"],
                -WEIGHT_BONUS.get(row["default_weight_tier"], 0.0),
                row["record_id"],
            )
        )

        selected: list[dict[str, Any]] = []
        per_source_counts: Counter[str] = Counter()
        for candidate in scored:
            policy_source_id = candidate["policy_source_id"]
            limit = SOURCE_BUDGETS.get(policy_source_id, self.candidate_limit)
            if per_source_counts[policy_source_id] >= limit:
                continue
            selected.append(candidate)
            per_source_counts[policy_source_id] += 1
            if len(selected) >= self.candidate_limit:
                break

        return selected

    def _fetch_chunk_backrefs(self, chunk_record_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                l.link_order,
                l.main_passage_record_id,
                l.main_passage_id,
                m.record_id,
                m.passage_id,
                m.chapter_id,
                m.chapter_name,
                m.text,
                m.normalized_text,
                m.evidence_level,
                m.display_allowed,
                m.risk_flag,
                m.default_weight_tier,
                m.policy_source_id,
                m.requires_disclaimer
            FROM record_chunk_passage_links AS l
            JOIN records_main_passages AS m
              ON m.record_id = l.main_passage_record_id
            WHERE l.chunk_record_id = ?
            ORDER BY l.link_order
        """
        return [dict(row) for row in self.conn.execute(query, (chunk_record_id,))]

    def _resolve_candidates(self, raw_candidates: list[dict[str, Any]]) -> dict[str, Any]:
        primary_pool: dict[str, dict[str, Any]] = {}
        secondary_pool: dict[str, dict[str, Any]] = {}
        risk_pool: dict[str, dict[str, Any]] = {}
        chunk_hits: list[dict[str, Any]] = []
        used_sources: list[str] = []

        for candidate in raw_candidates:
            used_sources.append(candidate["record_table"])
            if candidate["record_table"] == "records_chunks":
                backrefs = self._fetch_chunk_backrefs(candidate["record_id"])
                chunk_hit = {
                    "chunk_record_id": candidate["record_id"],
                    "chunk_score": candidate["combined_score"],
                    "matched_terms": candidate["matched_terms"],
                    "linked_main_passages": [],
                }
                for backref in backrefs:
                    main_entry = self._build_main_passage_entry_from_chunk(candidate, backref)
                    chunk_hit["linked_main_passages"].append(
                        {
                            "main_passage_record_id": backref["record_id"],
                            "passage_id": backref["passage_id"],
                            "evidence_level": backref["evidence_level"],
                            "display_allowed": backref["display_allowed"],
                        }
                    )
                    if backref["evidence_level"] == "A":
                        self._merge_evidence_entry(primary_pool, main_entry)
                    else:
                        self._merge_evidence_entry(secondary_pool, main_entry)
                chunk_hits.append(chunk_hit)
                continue

            if candidate["record_table"] == "records_main_passages":
                entry = self._build_direct_entry(candidate, retrieval_path="direct")
                if candidate["evidence_level"] == "A":
                    self._merge_evidence_entry(primary_pool, entry)
                else:
                    self._merge_evidence_entry(secondary_pool, entry)
                continue

            if candidate["record_table"] == "records_annotations":
                entry = self._build_direct_entry(candidate, retrieval_path="direct")
                self._merge_evidence_entry(secondary_pool, entry)
                continue

            if candidate["record_table"] in {"records_passages", "risk_registry_ambiguous"}:
                entry = self._build_direct_entry(candidate, retrieval_path="direct")
                self._merge_evidence_entry(risk_pool, entry)
                continue

        return {
            "primary_pool": primary_pool,
            "secondary_pool": secondary_pool,
            "risk_pool": risk_pool,
            "retrieval_trace": {
                "chunk_hits": chunk_hits,
                "blocked_sources": ["annotation_links"],
                "used_sources": unique_preserve_order(used_sources),
                "raw_candidate_count": len(raw_candidates),
            },
        }

    def _build_main_passage_entry_from_chunk(self, chunk_candidate: dict[str, Any], main_row: dict[str, Any]) -> dict[str, Any]:
        return {
            "record_id": main_row["record_id"],
            "source_object": "main_passages",
            "evidence_level": main_row["evidence_level"],
            "display_allowed": main_row["display_allowed"],
            "risk_flag": json.loads(main_row["risk_flag"]),
            "default_weight_tier": main_row["default_weight_tier"],
            "combined_score": round(chunk_candidate["combined_score"] + 0.5, 3),
            "text_match_score": chunk_candidate["text_match_score"],
            "matched_terms": list(chunk_candidate["matched_terms"]),
            "text_preview": preview_text(main_row["text"]),
            "chapter_id": main_row["chapter_id"],
            "chapter_name": main_row["chapter_name"],
            "requires_disclaimer": bool(main_row["requires_disclaimer"]),
            "policy_source_id": main_row["policy_source_id"],
            "retrieval_paths": [
                {
                    "type": "chunk_backref",
                    "chunk_record_id": chunk_candidate["record_id"],
                    "chunk_score": chunk_candidate["combined_score"],
                }
            ],
        }

    def _build_direct_entry(self, candidate: dict[str, Any], retrieval_path: str) -> dict[str, Any]:
        return {
            "record_id": candidate["record_id"],
            "source_object": candidate["source_object"],
            "evidence_level": candidate["evidence_level"],
            "display_allowed": candidate["display_allowed"],
            "risk_flag": json.loads(candidate["risk_flag"]),
            "default_weight_tier": candidate["default_weight_tier"],
            "combined_score": candidate["combined_score"],
            "text_match_score": candidate["text_match_score"],
            "matched_terms": list(candidate["matched_terms"]),
            "text_preview": preview_text(candidate["retrieval_text"]),
            "chapter_id": candidate["chapter_id"],
            "chapter_name": candidate["chapter_name"],
            "requires_disclaimer": bool(candidate["requires_disclaimer"]),
            "policy_source_id": candidate["policy_source_id"],
            "retrieval_paths": [{"type": retrieval_path}],
        }

    def _merge_evidence_entry(self, pool: dict[str, dict[str, Any]], entry: dict[str, Any]) -> None:
        existing = pool.get(entry["record_id"])
        if not existing:
            pool[entry["record_id"]] = entry
            return
        existing["combined_score"] = max(existing["combined_score"], entry["combined_score"])
        existing["text_match_score"] = max(existing["text_match_score"], entry["text_match_score"])
        existing["matched_terms"] = unique_preserve_order(existing["matched_terms"] + entry["matched_terms"])
        existing["retrieval_paths"] = existing["retrieval_paths"] + entry["retrieval_paths"]
        existing["risk_flag"] = unique_preserve_order(existing["risk_flag"] + entry["risk_flag"])

    def _assemble_slots(self, resolved: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        primary = self._sort_and_trim(resolved["primary_pool"].values(), PRIMARY_LIMIT)
        secondary = self._sort_and_trim(resolved["secondary_pool"].values(), SECONDARY_LIMIT)
        risk = self._sort_and_trim(resolved["risk_pool"].values(), RISK_LIMIT)
        return {
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "risk_materials": risk,
        }

    def _sort_and_trim(self, entries: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        ordered = sorted(
            entries,
            key=lambda row: (
                -row["combined_score"],
                -row["text_match_score"],
                -WEIGHT_BONUS.get(row["default_weight_tier"], 0.0),
                row["record_id"],
            ),
        )
        return ordered[:limit]

    def _determine_mode(self, slots: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        primary = slots["primary_evidence"]
        secondary = slots["secondary_evidence"]
        risk = slots["risk_materials"]

        if primary:
            if secondary:
                reason = self.policy["answer_modes"]["strong_with_auxiliary"]["default_user_message"]
            else:
                reason = self.policy["answer_modes"]["strong"]["default_user_message"]
            return {
                "mode": "strong",
                "mode_reason": reason,
                "runtime_risk_flags": [],
            }

        if secondary or risk:
            runtime_risk_flags = list(
                self.policy["answer_modes"]["weak_with_review_notice"]["must_add_risk_labels"]
            )
            for entry in secondary + risk:
                runtime_risk_flags.extend(entry["risk_flag"])
            return {
                "mode": "weak_with_review_notice",
                "mode_reason": self.policy["answer_modes"]["weak_with_review_notice"]["default_user_message"],
                "runtime_risk_flags": unique_preserve_order(runtime_risk_flags),
            }

        return {
            "mode": "refuse",
            "mode_reason": self.policy["answer_modes"]["refuse"]["default_user_message"],
            "runtime_risk_flags": [],
        }


def markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_no rows_"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header)
            if isinstance(value, (dict, list)):
                values.append(json.dumps(value, ensure_ascii=False))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_examples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
    }


def build_smoke_markdown(command: str, results: list[dict[str, Any]]) -> str:
    lines = [
        "# Retrieval Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 结论",
        "",
    ]

    for result in results:
        lines.append(
            f"- `{result['example_id']}`: mode=`{result['mode']}`, "
            f"primary={len(result['primary_evidence'])}, "
            f"secondary={len(result['secondary_evidence'])}, "
            f"risk={len(result['risk_materials'])}, "
            f"chunk_hits={len(result['retrieval_trace']['chunk_hits'])}"
        )

    for result in results:
        lines.extend(
            [
                "",
                f"## Example: {result['example_id']}",
                "",
                f"- query: `{result['query_request']['query_text']}`",
                f"- mode: `{result['mode']}`",
                f"- mode_reason: {result['mode_reason']}",
                f"- runtime_risk_flags: `{json.dumps(result['runtime_risk_flags'], ensure_ascii=False)}`",
                "",
                "### Raw Candidates",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "evidence_level": row["evidence_level"],
                            "combined_score": row["combined_score"],
                            "matched_terms": json.dumps(row["matched_terms"], ensure_ascii=False),
                            "backref_target_type": row["backref_target_type"],
                        }
                        for row in result["raw_candidates"][:6]
                    ]
                ),
                "",
                "### Primary Evidence",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "combined_score": row["combined_score"],
                            "retrieval_paths": json.dumps(row["retrieval_paths"], ensure_ascii=False),
                        }
                        for row in result["primary_evidence"]
                    ]
                ),
                "",
                "### Secondary Evidence",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "combined_score": row["combined_score"],
                            "risk_flag": json.dumps(row["risk_flag"], ensure_ascii=False),
                        }
                        for row in result["secondary_evidence"]
                    ]
                ),
                "",
                "### Risk Materials",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "combined_score": row["combined_score"],
                            "risk_flag": json.dumps(row["risk_flag"], ensure_ascii=False),
                        }
                        for row in result["risk_materials"]
                    ]
                ),
                "",
                "### Chunk Hits",
                "",
                markdown_table(
                    [
                        {
                            "chunk_record_id": row["chunk_record_id"],
                            "chunk_score": row["chunk_score"],
                            "linked_main_passages": json.dumps(row["linked_main_passages"], ensure_ascii=False),
                        }
                        for row in result["retrieval_trace"]["chunk_hits"]
                    ]
                ),
            ]
        )

    return "\n".join(lines) + "\n"


def run_examples(engine: RetrievalEngine) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        result = engine.retrieve(example["query_text"])
        result["example_id"] = example["example_id"]
        result["expected_mode"] = example["expected_mode"]
        results.append(result)
    return results


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    mode_counts = Counter(result["mode"] for result in results)
    if mode_counts["strong"] < 1:
        raise AssertionError("expected at least one strong example")
    if mode_counts["weak_with_review_notice"] < 1:
        raise AssertionError("expected at least one weak_with_review_notice example")
    if mode_counts["refuse"] < 1:
        raise AssertionError("expected at least one refuse example")

    if not any(result["retrieval_trace"]["chunk_hits"] for result in results):
        raise AssertionError("expected at least one example with chunk backrefs")

    if any(result["annotation_links_enabled"] for result in results):
        raise AssertionError("annotation_links should remain disabled")

    for result in results:
        if result["mode"] == "strong" and not result["primary_evidence"]:
            raise AssertionError("strong result missing primary_evidence")
        if result["mode"] == "weak_with_review_notice" and result["primary_evidence"]:
            raise AssertionError("weak_with_review_notice must not include primary_evidence")


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    db_path = (repo_root / args.db_path).resolve()
    policy_path = (repo_root / args.policy_json).resolve()
    examples_out = (repo_root / args.examples_out).resolve()
    smoke_out = (repo_root / args.smoke_checks_out).resolve()

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)

    engine = RetrievalEngine(db_path=db_path, policy_path=policy_path, candidate_limit=args.candidate_limit)
    try:
        log(f"[1/4] Loaded policy from {policy_path}")
        log(f"[2/4] Loaded retrieval database from {db_path} with {len(engine.unified_rows)} unified rows")

        if args.query:
            result = engine.retrieve(args.query)
            print(json_dumps(result))
            log("[3/4] Ran single-query retrieval")
            log("[4/4] No artifact files updated in single-query mode")
            return 0

        results = run_examples(engine)
        assert_smoke_expectations(results)
        examples_payload = build_examples_payload(results)
        examples_out.write_text(json_dumps(examples_payload) + "\n", encoding="utf-8")

        command = f"{Path(sys.executable).name} " + " ".join(sys.argv)
        smoke_out.write_text(build_smoke_markdown(command, results), encoding="utf-8")
        log("[3/4] Ran default retrieval examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
