#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


os.environ.setdefault("PERF_DISABLE_LLM", "1")
os.environ.setdefault("PERF_DISABLE_RERANK", "1")
os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.answers.assembler import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    AnswerAssembler,
    resolve_project_path,
)
from scripts.data_plane_batch_upgrade.run_ambiguous_high_value_evidence_upgrade_v1 import (  # noqa: E402
    CANDIDATES,
    DEFAULT_BEFORE_DB,
    RUN_ID,
)


DEFAULT_OUTPUT_JSON = "artifacts/data_plane_batch_upgrade/batch_upgrade_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_plane_batch_upgrade/batch_upgrade_regression_v1.md"
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
GOLD_SAFE_DEFINITION_QUERIES = (
    "发汗药是什么意思",
    "坏病是什么",
    "盗汗是什么意思",
    "水结胸是什么",
    "四逆是什么意思",
)
FORMULA_GUARD_QUERIES = (
    "桂枝去芍药汤方的条文是什么？",
    "桂枝去芍药加附子汤方的条文是什么？",
    "四逆加人参汤方的条文是什么？",
    "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
    "桂枝去桂加茯苓白术汤方的条文是什么？",
)
REVIEW_ONLY_BOUNDARY_QUERIES = (
    "神丹是什么意思",
    "将军是什么意思",
    "口苦病是什么意思",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ambiguous high-value batch upgrade regression v1.")
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--after-db", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_assembler(db_path: Path) -> AnswerAssembler:
    return AnswerAssembler(
        db_path=db_path,
        policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
        embed_model=DEFAULT_EMBED_MODEL,
        rerank_model=DEFAULT_RERANK_MODEL,
        cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
        dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
        dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
        dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
        dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
    )


def normalize_mode(answer_mode: str | None) -> str:
    if answer_mode == "strong":
        return "strong"
    if answer_mode and answer_mode.startswith("weak"):
        return "weak"
    return "refuse"


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    forbidden: list[dict[str, Any]] = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            forbidden.append({"record_id": item.get("record_id"), "record_type": item.get("record_type")})
    return forbidden


def candidate_queries() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in CANDIDATES:
        rows.append(
            {
                "query_id": item.candidate_id,
                "query": item.query,
                "category": f"candidate_{item.category}",
                "candidate_category": item.category,
                "canonical_term": item.canonical_term,
                "concept_id": item.concept_id if item.category in {"A", "B"} else None,
                "source_passage_id": item.passage_id,
            }
        )
    for index, query in enumerate(GOLD_SAFE_DEFINITION_QUERIES, start=1):
        rows.append(
            {
                "query_id": f"gold_definition_{index}",
                "query": query,
                "category": "gold_safe_definition",
                "candidate_category": None,
                "canonical_term": "",
                "concept_id": None,
                "source_passage_id": "",
            }
        )
    for index, query in enumerate(FORMULA_GUARD_QUERIES, start=1):
        rows.append(
            {
                "query_id": f"formula_guard_{index}",
                "query": query,
                "category": "formula_guard",
                "candidate_category": None,
                "canonical_term": "",
                "concept_id": None,
                "source_passage_id": "",
            }
        )
    for index, query in enumerate(REVIEW_ONLY_BOUNDARY_QUERIES, start=1):
        rows.append(
            {
                "query_id": f"review_boundary_{index}",
                "query": query,
                "category": "review_only_boundary",
                "candidate_category": "B",
                "canonical_term": "",
                "concept_id": None,
                "source_passage_id": "",
            }
        )
    return rows


def summarize_one_result(assembler: AnswerAssembler, spec: dict[str, Any]) -> dict[str, Any]:
    try:
        retrieval = assembler.engine.retrieve(spec["query"])
        payload = assembler.assemble(spec["query"])
    except Exception as exc:
        return {
            **spec,
            "answer_mode": "error",
            "mode_bucket": "refuse",
            "primary_ids": [],
            "primary_record_types": [],
            "secondary_ids": [],
            "review_ids": [],
            "primary_forbidden_items": [],
            "query_focus_source": None,
            "term_normalization": {},
            "definition_object_primary_count": 0,
            "batch_primary_hit": False,
            "support_path_hit": False,
            "formula_bad_anchor_top5_count": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }
    raw_top = retrieval.get("raw_candidates") or []
    term_normalization = retrieval.get("query_request", {}).get("term_normalization") or {}
    primary = payload.get("primary_evidence") or []
    secondary = payload.get("secondary_evidence") or []
    review = payload.get("review_materials") or []
    primary_ids = [item.get("record_id") for item in primary]
    secondary_ids = [item.get("record_id") for item in secondary]
    review_ids = [item.get("record_id") for item in review]
    concept_id = spec.get("concept_id")
    batch_primary_hit = bool(
        concept_id and any(str(record_id).endswith(f":{concept_id}") for record_id in primary_ids)
    )
    source_passage_id = spec.get("source_passage_id") or ""
    support_path_hit = bool(
        source_passage_id
        and any(source_passage_id in str(record_id) for record_id in [*secondary_ids, *review_ids])
    )
    return {
        **spec,
        "answer_mode": payload.get("answer_mode"),
        "mode_bucket": normalize_mode(payload.get("answer_mode")),
        "primary_ids": primary_ids,
        "primary_record_types": [item.get("record_type") for item in primary],
        "secondary_ids": secondary_ids,
        "review_ids": review_ids,
        "primary_forbidden_items": primary_forbidden_items(payload),
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "term_normalization": term_normalization,
        "definition_object_primary_count": sum(1 for item in primary if item.get("record_type") == "definition_terms"),
        "batch_primary_hit": batch_primary_hit,
        "support_path_hit": support_path_hit,
        "formula_bad_anchor_top5_count": sum(
            1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS
        ),
    }


def run_suite(db_path: Path, specs: list[dict[str, Any]]) -> dict[str, Any]:
    assembler = make_assembler(db_path)
    try:
        rows = [summarize_one_result(assembler, spec) for spec in specs]
    finally:
        assembler.close()
    return summarize_rows(rows)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mode_counts = Counter(row["answer_mode"] for row in rows)
    mode_bucket_counts = Counter(row["mode_bucket"] for row in rows)
    category_mode_counts: dict[str, dict[str, int]] = {}
    for category in sorted({row["category"] for row in rows}):
        category_mode_counts[category] = dict(
            sorted(Counter(row["mode_bucket"] for row in rows if row["category"] == category).items())
        )
    return {
        "rows": rows,
        "summary": {
            "mode_counts": dict(sorted(mode_counts.items())),
            "mode_bucket_counts": dict(sorted(mode_bucket_counts.items())),
            "category_mode_counts": category_mode_counts,
            "forbidden_primary_total": sum(len(row["primary_forbidden_items"]) for row in rows),
            "formula_bad_anchor_top5_total": sum(
                row["formula_bad_anchor_top5_count"] for row in rows if row["category"] == "formula_guard"
            ),
            "new_safe_object_primary_hit_count": sum(
                1 for row in rows if row["candidate_category"] == "A" and row["batch_primary_hit"]
            ),
            "support_only_registered_review_hit_count": sum(
                1 for row in rows if row["candidate_category"] == "B" and row["support_path_hit"]
            ),
            "review_only_primary_conflict_count": sum(
                1
                for row in rows
                if row["candidate_category"] == "B" and row["definition_object_primary_count"] > 0
            ),
            "alias_risk_conflict_count": sum(
                1
                for row in rows
                if row["candidate_category"] in {"B", "C"}
                and (
                    row.get("query_focus_source") == "term_normalization"
                    or bool((row.get("term_normalization") or {}).get("concept_ids"))
                )
            ),
        },
    }


def pass_after(row: dict[str, Any]) -> tuple[bool, str]:
    if row["primary_forbidden_items"]:
        return False, "forbidden primary evidence"
    category = row["category"]
    candidate_category = row.get("candidate_category")
    if candidate_category == "A":
        if not row["batch_primary_hit"]:
            return False, "A candidate did not hit batch safe definition object as primary"
        return True, "A candidate primary hit"
    if candidate_category == "B" and category.startswith("candidate_"):
        if row["definition_object_primary_count"]:
            return False, "B candidate entered definition primary"
        if not row["support_path_hit"]:
            return False, "B candidate source did not appear in secondary/review path"
        return True, "B candidate stayed support/review-only"
    if candidate_category == "C":
        if row["definition_object_primary_count"]:
            return False, "C rejected candidate entered definition primary"
        if (row.get("term_normalization") or {}).get("concept_ids"):
            return False, "C rejected candidate forced term normalization"
        return True, "C candidate stayed outside runtime normalization"
    if category == "gold_safe_definition":
        return (row["mode_bucket"] == "strong", "gold-safe definition remains strong")
    if category == "formula_guard":
        if row["mode_bucket"] != "strong":
            return False, "formula guard is not strong"
        if row["formula_bad_anchor_top5_count"]:
            return False, "formula guard has bad anchor in top5"
        return True, "formula guard remains strong"
    if category == "review_only_boundary":
        if row["definition_object_primary_count"]:
            return False, "review-only boundary entered definition primary"
        return True, "review-only boundary stayed out of primary"
    return True, "no specific assertion"


def pair_results(before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before_by_id = {row["query_id"]: row for row in before_rows}
    paired: list[dict[str, Any]] = []
    for after in after_rows:
        before = before_by_id[after["query_id"]]
        passed, reason = pass_after(after)
        paired.append(
            {
                "query_id": after["query_id"],
                "query": after["query"],
                "category": after["category"],
                "candidate_category": after.get("candidate_category"),
                "canonical_term": after.get("canonical_term"),
                "before": before,
                "after": after,
                "delta": {
                    "mode_changed": before["answer_mode"] != after["answer_mode"],
                    "new_batch_primary": not before["batch_primary_hit"] and after["batch_primary_hit"],
                    "support_path_added": not before["support_path_hit"] and after["support_path_hit"],
                },
                "pass": passed,
                "pass_reason": reason,
            }
        )
    return paired


def write_outputs(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Batch Upgrade Regression v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- before_db: `{payload['before_db']}`",
        f"- after_db: `{payload['after_db']}`",
        f"- query_count: `{payload['query_count']}`",
        "",
        "## Summary",
        "",
        f"- before strong/weak/refuse: `{json.dumps(payload['before_summary']['mode_bucket_counts'], ensure_ascii=False)}`",
        f"- after strong/weak/refuse: `{json.dumps(payload['after_summary']['mode_bucket_counts'], ensure_ascii=False)}`",
        f"- support_only_reduced_count: `{payload['metrics']['support_only_reduced_count']}`",
        f"- new_safe_object_primary_hit_count: `{payload['metrics']['new_safe_object_primary_hit_count']}`",
        f"- forbidden_primary_total: `{payload['metrics']['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_count: `{payload['metrics']['review_only_primary_conflict_count']}`",
        f"- alias_risk_conflict_count: `{payload['metrics']['alias_risk_conflict_count']}`",
        f"- formula_bad_anchor_top5_total: `{payload['metrics']['formula_bad_anchor_top5_total']}`",
        f"- regression_pass_count / fail_count: `{payload['metrics']['regression_pass_count']} / {payload['metrics']['regression_fail_count']}`",
        "",
        "## Query Table",
        "",
        "| category | query | before | after | primary_after | pass |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["paired_results"]:
        primary_after = "<br>".join(str(item) for item in row["after"]["primary_ids"]) or "-"
        lines.append(
            f"| {row['category']} | {row['query']} | {row['before']['answer_mode']} | "
            f"{row['after']['answer_mode']} | {primary_after} | {row['pass']} |"
        )
    path_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    before_db = resolve_project_path(args.before_db)
    after_db = resolve_project_path(args.after_db)
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    if not before_db.exists():
        raise SystemExit(f"Missing before DB: {before_db}. Run the upgrade script first.")

    specs = candidate_queries()
    before = run_suite(before_db, specs)
    after = run_suite(after_db, specs)
    paired = pair_results(before["rows"], after["rows"])
    pass_count = sum(1 for row in paired if row["pass"])
    fail_count = len(paired) - pass_count
    support_only_reduced_count = sum(
        1
        for row in paired
        if row["candidate_category"] == "A" and row["delta"]["new_batch_primary"]
    )
    metrics = {
        "candidate_count": sum(1 for item in CANDIDATES),
        "promoted_safe_primary_count": sum(1 for item in CANDIDATES if item.category == "A"),
        "support_only_registered_count": sum(1 for item in CANDIDATES if item.category == "B"),
        "rejected_count": sum(1 for item in CANDIDATES if item.category == "C"),
        "before_mode_distribution": before["summary"]["mode_bucket_counts"],
        "after_mode_distribution": after["summary"]["mode_bucket_counts"],
        "support_only_reduced_count": support_only_reduced_count,
        "new_safe_object_primary_hit_count": after["summary"]["new_safe_object_primary_hit_count"],
        "forbidden_primary_total": after["summary"]["forbidden_primary_total"],
        "review_only_primary_conflict_count": after["summary"]["review_only_primary_conflict_count"],
        "alias_risk_conflict_count": after["summary"]["alias_risk_conflict_count"],
        "formula_bad_anchor_top5_total": after["summary"]["formula_bad_anchor_top5_total"],
        "regression_pass_count": pass_count,
        "regression_fail_count": fail_count,
    }
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "before_db": str(before_db),
        "after_db": str(after_db),
        "query_count": len(specs),
        "before_summary": before["summary"],
        "after_summary": after["summary"],
        "metrics": metrics,
        "paired_results": paired,
        "failures": [row for row in paired if not row["pass"]],
    }
    write_outputs(output_json, output_md, payload)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
