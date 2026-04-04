#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_minimal_retrieval import (
    DEFAULT_DB_PATH,
    DEFAULT_EXAMPLES,
    DEFAULT_POLICY_PATH,
    RetrievalEngine,
    json_dumps,
    log,
)


DEFAULT_ANSWER_EXAMPLES_OUT = "artifacts/answer_examples.json"
DEFAULT_ANSWER_SMOKE_OUT = "artifacts/answer_smoke_checks.md"
SNIPPET_LIMIT = 120

REFUSE_GUIDANCE_TEMPLATES = [
    "请改问具体条文，例如：某一条文的原文或含义是什么？",
    "请改问具体方名，例如：黄连汤方的组成或条文是什么？",
    "请改问书中某个明确术语或概念，例如：某句话出自哪一条？",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble stable answer payloads from minimal retrieval results.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--query", help="Run a single query and print the assembled answer payload.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_ANSWER_EXAMPLES_OUT,
        help="Where to write the default answer examples JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_ANSWER_SMOKE_OUT,
        help="Where to write the answer smoke check markdown report.",
    )
    return parser.parse_args()


def compact_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def snippet_text(text: str | None, limit: int = SNIPPET_LIMIT) -> str:
    compact = compact_whitespace(text)
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def first_meaningful_line(text: str | None) -> str:
    if not text:
        return ""
    for line in str(text).splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def build_examples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
    }


@dataclass
class AnswerAssembler:
    db_path: Path
    policy_path: Path

    def __post_init__(self) -> None:
        self.engine = RetrievalEngine(db_path=self.db_path, policy_path=self.policy_path)
        self._record_cache: dict[str, dict[str, Any]] = {}

    def close(self) -> None:
        self.engine.close()

    def assemble(self, query_text: str) -> dict[str, Any]:
        retrieval = self.engine.retrieve(query_text)
        primary = [self._build_evidence_item(row, display_role="primary") for row in retrieval["primary_evidence"]]
        secondary = [self._build_evidence_item(row, display_role="secondary") for row in retrieval["secondary_evidence"]]
        review = [self._build_evidence_item(row, display_role="review") for row in retrieval["risk_materials"]]

        answer_mode = retrieval["mode"]
        answer_text = self._build_answer_text(retrieval, primary, secondary, review)
        review_notice = self._build_review_notice(answer_mode)
        disclaimer = self._build_disclaimer(answer_mode, bool(secondary), bool(review))
        refuse_reason = self._build_refuse_reason(answer_mode)
        suggested_followup_questions = self._build_followups(answer_mode)
        citations = self._build_citations(answer_mode, primary, secondary, review)
        display_sections = self._build_display_sections(
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            citations=citations,
            review_notice=review_notice,
            suggested_followup_questions=suggested_followup_questions,
        )

        return {
            "query": query_text,
            "answer_mode": answer_mode,
            "answer_text": answer_text,
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "review_materials": review,
            "disclaimer": disclaimer,
            "review_notice": review_notice,
            "refuse_reason": refuse_reason,
            "suggested_followup_questions": suggested_followup_questions,
            "citations": citations,
            "display_sections": display_sections,
        }

    def _fetch_record_meta(self, record_id: str) -> dict[str, Any]:
        cached = self._record_cache.get(record_id)
        if cached:
            return cached
        row = self.engine.conn.execute(
            """
            SELECT
                record_id,
                source_object,
                retrieval_text,
                chapter_id,
                chapter_name
            FROM vw_retrieval_records_unified
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            meta = {
                "record_id": record_id,
                "source_object": None,
                "retrieval_text": "",
                "chapter_id": None,
                "chapter_name": None,
            }
        else:
            meta = dict(row)
        self._record_cache[record_id] = meta
        return meta

    def _derive_title(self, row: dict[str, Any], full_text: str) -> str:
        topic_anchor = row.get("topic_anchor")
        if topic_anchor:
            return topic_anchor
        first_line = first_meaningful_line(full_text)
        if "：" in first_line:
            head = first_line.split("：", 1)[0].strip()
            if 1 <= len(head) <= 24:
                return head
        if ":" in first_line:
            head = first_line.split(":", 1)[0].strip()
            if 1 <= len(head) <= 24:
                return head
        if first_line:
            return snippet_text(first_line, limit=24)
        return row["record_id"]

    def _build_evidence_item(self, row: dict[str, Any], display_role: str) -> dict[str, Any]:
        meta = self._fetch_record_meta(row["record_id"])
        full_text = meta["retrieval_text"] or row.get("text_preview", "")
        title = self._derive_title(row, full_text)
        return {
            "record_id": row["record_id"],
            "record_type": row["source_object"],
            "display_role": display_role,
            "title": title,
            "evidence_level": row["evidence_level"],
            "chapter_id": row["chapter_id"],
            "chapter_title": row["chapter_name"],
            "snippet": snippet_text(full_text),
            "risk_flags": list(row["risk_flag"]),
        }

    def _build_answer_text(
        self,
        retrieval: dict[str, Any],
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> str:
        mode = retrieval["mode"]
        query_theme = retrieval["query_request"].get("query_theme", {})
        query_anchor = query_theme.get("anchor") or retrieval["query_request"]["query_text_normalized"]

        if mode == "strong":
            if query_theme.get("type") == "formula_name":
                header = f"根据主依据，与“{query_anchor}”直接对应的条文主要有："
            else:
                header = "根据主依据，直接相关的主条如下："
            lines = [header]
            for idx, item in enumerate(primary[:3], start=1):
                lines.append(f"{idx}. {item['snippet']}")
            return "\n".join(lines)

        if mode == "weak_with_review_notice":
            lead = "正文强证据不足，以下内容需核对，暂不能视为确定答案。"
            if secondary:
                return f"{lead} 当前可先参考辅助材料：{secondary[0]['snippet']}"
            if review:
                return f"{lead} 当前仅检索到风险层材料：{review[0]['snippet']}"
            return lead

        return "当前未检索到足以支撑回答的依据，暂不提供答案。"

    def _build_review_notice(self, answer_mode: str) -> str | None:
        if answer_mode == "strong":
            return "以下补充依据与核对材料仅作说明，不作为主依据。"
        if answer_mode == "weak_with_review_notice":
            return "正文强证据不足，以下内容需核对，不应视为确定答案。"
        return None

    def _build_disclaimer(self, answer_mode: str, has_secondary: bool, has_review: bool) -> str | None:
        if answer_mode == "strong":
            if has_secondary or has_review:
                return "主证据优先；补充依据与核对材料不参与主结论判定。"
            return None
        if answer_mode == "weak_with_review_notice":
            return "当前只输出弱表述与核对材料，不输出确定性答案。"
        if answer_mode == "refuse":
            return "当前为统一拒答结构，不输出推测性答案。"
        return None

    def _build_refuse_reason(self, answer_mode: str) -> str | None:
        if answer_mode != "refuse":
            return None
        return "未检索到足以支撑回答的主证据、辅助证据或可供核对的风险材料。"

    def _build_followups(self, answer_mode: str) -> list[str]:
        if answer_mode == "refuse":
            return list(REFUSE_GUIDANCE_TEMPLATES)
        return []

    def _build_citations(
        self,
        answer_mode: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        citation_source: list[dict[str, Any]]
        if answer_mode == "strong":
            citation_source = primary
        elif answer_mode == "weak_with_review_notice":
            citation_source = secondary + review
        else:
            citation_source = []

        citations: list[dict[str, Any]] = []
        for index, item in enumerate(citation_source, start=1):
            citations.append(
                {
                    "citation_id": f"c{index}",
                    "record_id": item["record_id"],
                    "record_type": item["record_type"],
                    "title": item["title"],
                    "evidence_level": item["evidence_level"],
                    "snippet": item["snippet"],
                    "chapter_id": item["chapter_id"],
                    "chapter_title": item["chapter_title"],
                    "citation_role": item["display_role"],
                }
            )
        return citations

    def _build_display_sections(
        self,
        answer_text: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        review_notice: str | None,
        suggested_followup_questions: list[str],
    ) -> list[dict[str, Any]]:
        return [
            {
                "section_id": "answer",
                "title": "回答",
                "section_type": "text",
                "visible": True,
                "field": "answer_text",
                "summary": snippet_text(answer_text, limit=48),
            },
            {
                "section_id": "review_notice",
                "title": "核对提示",
                "section_type": "notice",
                "visible": bool(review_notice),
                "field": "review_notice",
                "summary": review_notice or "",
            },
            {
                "section_id": "primary_evidence",
                "title": "主依据",
                "section_type": "slot_ref",
                "visible": bool(primary),
                "field": "primary_evidence",
                "item_count": len(primary),
            },
            {
                "section_id": "secondary_evidence",
                "title": "补充依据",
                "section_type": "slot_ref",
                "visible": bool(secondary),
                "field": "secondary_evidence",
                "item_count": len(secondary),
            },
            {
                "section_id": "review_materials",
                "title": "核对材料",
                "section_type": "slot_ref",
                "visible": bool(review),
                "field": "review_materials",
                "item_count": len(review),
            },
            {
                "section_id": "citations",
                "title": "引用",
                "section_type": "slot_ref",
                "visible": bool(citations),
                "field": "citations",
                "item_count": len(citations),
            },
            {
                "section_id": "refusal_guidance",
                "title": "改问建议",
                "section_type": "list",
                "visible": bool(suggested_followup_questions),
                "field": "suggested_followup_questions",
                "item_count": len(suggested_followup_questions),
            },
        ]


def build_smoke_markdown(command: str, results: list[dict[str, Any]]) -> str:
    strong_result = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    weak_result = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    refuse_result = next(result for result in results if result["example_id"] == "refuse_no_match")

    strong_primary_ids = [row["record_id"] for row in strong_result["primary_evidence"]]
    lines = [
        "# Answer Smoke Checks",
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
            f"- `{result['query']}` -> mode=`{result['answer_mode']}`, "
            f"primary={len(result['primary_evidence'])}, "
            f"secondary={len(result['secondary_evidence'])}, "
            f"review={len(result['review_materials'])}, "
            f"citations={len(result['citations'])}"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- strong_precision_patch_preserved: `{'ZJSHL-CH-009' not in ''.join(strong_primary_ids)}`",
            f"- weak_review_notice_present: `{bool(weak_result['review_notice'])}`",
            f"- refuse_guidance_present: `{bool(refuse_result['suggested_followup_questions'])}`",
        ]
    )

    for result in results:
        section_summary = [
            {
                "section_id": section["section_id"],
                "visible": section["visible"],
                "field": section["field"],
            }
            for section in result["display_sections"]
        ]
        lines.extend(
            [
                "",
                f"## Query: {result['query']}",
                "",
                f"- answer_mode: `{result['answer_mode']}`",
                f"- answer_text: {result['answer_text']}",
                f"- disclaimer: {result['disclaimer'] or 'None'}",
                f"- review_notice: {result['review_notice'] or 'None'}",
                f"- refuse_reason: {result['refuse_reason'] or 'None'}",
                f"- evidence_summary: primary={len(result['primary_evidence'])}, secondary={len(result['secondary_evidence'])}, review={len(result['review_materials'])}",
                f"- citations_summary: `{json_dumps([citation['record_id'] for citation in result['citations']])}`",
                f"- display_sections: `{json_dumps(section_summary)}`",
                "",
                "### Primary Evidence",
                "",
                json_dumps(result["primary_evidence"]) if result["primary_evidence"] else "_no rows_",
                "",
                "### Secondary Evidence",
                "",
                json_dumps(result["secondary_evidence"]) if result["secondary_evidence"] else "_no rows_",
                "",
                "### Review Materials",
                "",
                json_dumps(result["review_materials"]) if result["review_materials"] else "_no rows_",
                "",
                "### Suggested Follow-up Questions",
                "",
                json_dumps(result["suggested_followup_questions"]) if result["suggested_followup_questions"] else "_no rows_",
            ]
        )

    return "\n".join(lines) + "\n"


def run_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        payload = assembler.assemble(example["query_text"])
        payload["example_id"] = example["example_id"]
        payload["expected_mode"] = example["expected_mode"]
        results.append(payload)
    return results


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    examples = {result["example_id"]: result for result in results}

    strong = examples["strong_chunk_backref"]
    if strong["answer_mode"] != "strong":
        raise AssertionError("strong_chunk_backref mode regressed")
    if not strong["primary_evidence"]:
        raise AssertionError("strong_chunk_backref missing primary evidence")
    if any(item["record_type"] != "main_passages" for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence must contain only main_passages")
    if any("ZJSHL-CH-009" in item["chapter_id"] for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence reintroduced 葛根黄芩黄连汤方-related passages")
    if any(item["record_type"] in {"passages", "ambiguous_passages"} for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence must not include review materials")

    weak = examples["weak_with_review_notice"]
    if weak["answer_mode"] != "weak_with_review_notice":
        raise AssertionError("weak_with_review_notice mode regressed")
    if weak["primary_evidence"]:
        raise AssertionError("weak_with_review_notice should not contain primary evidence")
    if not weak["review_notice"]:
        raise AssertionError("weak_with_review_notice missing review_notice")
    if any(item["record_type"] == "annotation_links" for item in weak["secondary_evidence"] + weak["review_materials"]):
        raise AssertionError("annotation_links must remain disabled")

    refuse = examples["refuse_no_match"]
    if refuse["answer_mode"] != "refuse":
        raise AssertionError("refuse mode regressed")
    if refuse["answer_text"] == "":
        raise AssertionError("refuse answer_text should not be empty")
    if not refuse["refuse_reason"]:
        raise AssertionError("refuse missing refuse_reason")
    if len(refuse["suggested_followup_questions"]) < 3:
        raise AssertionError("refuse missing follow-up guidance")

    for result in results:
        if any(item["record_type"] == "annotation_links" for item in result["primary_evidence"]):
            raise AssertionError("annotation_links leaked into primary_evidence")
        if any(item["record_type"] == "annotation_links" for item in result["secondary_evidence"]):
            raise AssertionError("annotation_links leaked into secondary_evidence")
        if any(item["record_type"] == "annotation_links" for item in result["review_materials"]):
            raise AssertionError("annotation_links leaked into review_materials")


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    db_path = (repo_root / args.db_path).resolve()
    policy_path = (repo_root / args.policy_json).resolve()
    examples_out = (repo_root / args.examples_out).resolve()
    smoke_out = (repo_root / args.smoke_checks_out).resolve()

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)

    assembler = AnswerAssembler(db_path=db_path, policy_path=policy_path)
    try:
        log(f"[1/4] Loaded policy from {policy_path}")
        log(f"[2/4] Loaded retrieval database from {db_path}")

        if args.query:
            payload = assembler.assemble(args.query)
            print(json_dumps(payload))
            log("[3/4] Ran single-query answer assembly")
            log("[4/4] No artifact files updated in single-query mode")
            return 0

        results = run_examples(assembler)
        assert_smoke_expectations(results)
        examples_out.write_text(json_dumps(build_examples_payload(results)) + "\n", encoding="utf-8")

        command = f"{Path(sys.executable).name} {Path(__file__).name}"
        smoke_out.write_text(build_smoke_markdown(command, results), encoding="utf-8")
        log("[3/4] Ran default answer examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        assembler.close()


if __name__ == "__main__":
    raise SystemExit(main())
