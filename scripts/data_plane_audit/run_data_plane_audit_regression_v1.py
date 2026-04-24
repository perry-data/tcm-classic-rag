#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_data_plane_audit_v1.db"
DEFAULT_AFTER_DB = DEFAULT_DB_PATH
DEFAULT_OUTPUT_JSON = "artifacts/data_plane_audit/data_plane_audit_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_plane_audit/data_plane_audit_regression_v1.md"

FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}

REGRESSION_QUERIES: tuple[dict[str, str], ...] = (
    {"category": "formula", "query": "桂枝去芍药汤方的条文是什么？"},
    {"category": "formula", "query": "桂枝去芍药加附子汤方的条文是什么？"},
    {"category": "formula", "query": "四逆加人参汤方的条文是什么？"},
    {"category": "formula", "query": "四逆加猪胆汁汤方的条文是什么？"},
    {"category": "formula", "query": "桂枝去桂加茯苓白术汤方的条文是什么？"},
    {"category": "formula", "query": "桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？"},
    {"category": "formula", "query": "四逆汤方和四逆加人参汤方有什么不同？"},
    {"category": "formula", "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？"},
    {"category": "definition", "query": "什么是风温"},
    {"category": "definition", "query": "什么是下药"},
    {"category": "definition", "query": "什么是四逆"},
    {"category": "definition", "query": "什么是湿痹"},
    {"category": "definition", "query": "什么是发汗药"},
    {"category": "definition", "query": "什么是内烦"},
    {"category": "definition", "query": "什么是阳易"},
    {"category": "definition", "query": "什么是胆瘅"},
    {"category": "learner_short", "query": "睡着出汗是什么意思"},
    {"category": "learner_short", "query": "四肢不温是什么"},
    {"category": "learner_short", "query": "泻下药是什么意思"},
    {"category": "learner_short", "query": "时气是什么意思"},
    {"category": "learner_short", "query": "气从少腹上冲是什么意思"},
    {"category": "learner_short", "query": "表里两感是什么意思"},
    {"category": "learner_short", "query": "水饮结胸是什么意思"},
    {"category": "learner_short", "query": "口苦病是什么意思"},
    {"category": "review_only_boundary", "query": "神丹是什么意思"},
    {"category": "review_only_boundary", "query": "将军是什么意思"},
    {"category": "review_only_boundary", "query": "两阳是什么意思"},
    {"category": "alias_boundary", "query": "阴阳易是什么意思"},
)

DOWNGRADED_CONCEPT_IDS = {"DPO-3239213192a3"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run audit regression v1.")
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--after-db", default=DEFAULT_AFTER_DB)
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


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    forbidden: list[dict[str, Any]] = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            forbidden.append(
                {
                    "record_id": item.get("record_id"),
                    "record_type": item.get("record_type"),
                }
            )
    return forbidden


def summarize_one_result(assembler: AnswerAssembler, query: str, category: str) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    raw_top = retrieval.get("raw_candidates") or []
    term_normalization = retrieval.get("query_request", {}).get("term_normalization") or {}
    primary_ids = [item.get("record_id") for item in payload.get("primary_evidence") or []]
    downgraded_definition_primary_count = 0
    for record_id in primary_ids:
        if not str(record_id).startswith("safe:definition_terms:"):
            continue
        concept_id = str(record_id).split(":")[-1]
        if concept_id in DOWNGRADED_CONCEPT_IDS:
            downgraded_definition_primary_count += 1
    return {
        "query": query,
        "category": category,
        "answer_mode": payload.get("answer_mode"),
        "primary_ids": primary_ids,
        "primary_record_types": [item.get("record_type") for item in payload.get("primary_evidence") or []],
        "primary_forbidden_items": primary_forbidden_items(payload),
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "term_normalization": term_normalization,
        "definition_object_primary_count": sum(
            1 for item in payload.get("primary_evidence") or [] if item.get("record_type") == "definition_terms"
        ),
        "formula_bad_anchor_top5_count": sum(
            1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS
        ),
        "downgraded_definition_primary_count": downgraded_definition_primary_count,
    }


def run_suite(db_path: Path) -> dict[str, Any]:
    assembler = make_assembler(db_path)
    try:
        rows = [summarize_one_result(assembler, item["query"], item["category"]) for item in REGRESSION_QUERIES]
    finally:
        assembler.close()

    mode_counts = Counter(row["answer_mode"] for row in rows)
    category_mode_counts: dict[str, dict[str, int]] = {}
    for category in sorted({row["category"] for row in rows}):
        category_mode_counts[category] = dict(
            sorted(Counter(row["answer_mode"] for row in rows if row["category"] == category).items())
        )

    return {
        "rows": rows,
        "summary": {
            "mode_counts": dict(sorted(mode_counts.items())),
            "category_mode_counts": category_mode_counts,
            "forbidden_primary_total": sum(len(row["primary_forbidden_items"]) for row in rows),
            "formula_bad_anchor_top5_total": sum(
                row["formula_bad_anchor_top5_count"] for row in rows if row["category"] == "formula"
            ),
            "learner_short_strong_count": sum(
                1 for row in rows if row["category"] == "learner_short" and row["answer_mode"] == "strong"
            ),
            "downgraded_definition_primary_total": sum(
                row["downgraded_definition_primary_count"] for row in rows
            ),
            "ambiguous_alias_forced_normalization_count": sum(
                1
                for row in rows
                if row["category"] == "alias_boundary"
                and (row["query_focus_source"] == "term_normalization" or row["term_normalization"].get("concept_ids"))
            ),
        },
    }


def pair_results(before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before_by_query = {row["query"]: row for row in before_rows}
    paired: list[dict[str, Any]] = []
    for after_row in after_rows:
        before_row = before_by_query[after_row["query"]]
        paired.append(
            {
                "query": after_row["query"],
                "category": after_row["category"],
                "before": before_row,
                "after": after_row,
                "delta": {
                    "mode_changed": before_row["answer_mode"] != after_row["answer_mode"],
                    "focus_changed": before_row.get("query_focus_source") != after_row.get("query_focus_source"),
                    "downgraded_object_removed_from_primary": before_row["downgraded_definition_primary_count"] > 0
                    and after_row["downgraded_definition_primary_count"] == 0,
                },
            }
        )
    return paired


def write_outputs(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Data Plane Audit Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- before_db: `{payload['before_db']}`",
        f"- after_db: `{payload['after_db']}`",
        "",
        "## Summary",
        "",
        f"- before mode_counts: `{json.dumps(payload['before_summary']['mode_counts'], ensure_ascii=False)}`",
        f"- after mode_counts: `{json.dumps(payload['after_summary']['mode_counts'], ensure_ascii=False)}`",
        f"- forbidden_primary before -> after: `{payload['before_summary']['forbidden_primary_total']} -> {payload['after_summary']['forbidden_primary_total']}`",
        f"- formula bad anchors top5 before -> after: `{payload['before_summary']['formula_bad_anchor_top5_total']} -> {payload['after_summary']['formula_bad_anchor_top5_total']}`",
        f"- learner_short strong before -> after: `{payload['before_summary']['learner_short_strong_count']} -> {payload['after_summary']['learner_short_strong_count']}`",
        f"- downgraded definition primary before -> after: `{payload['before_summary']['downgraded_definition_primary_total']} -> {payload['after_summary']['downgraded_definition_primary_total']}`",
        f"- ambiguous alias forced normalization before -> after: `{payload['before_summary']['ambiguous_alias_forced_normalization_count']} -> {payload['after_summary']['ambiguous_alias_forced_normalization_count']}`",
        "",
        "## Query Table",
        "",
        "| category | query | before | after | focus_before | focus_after | primary_after |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in payload["paired_results"]:
        before = row["before"]
        after = row["after"]
        primary_after = "<br>".join(after["primary_ids"]) or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["category"],
                    row["query"],
                    before["answer_mode"],
                    after["answer_mode"],
                    str(before.get("query_focus_source")),
                    str(after.get("query_focus_source")),
                    primary_after,
                ]
            )
            + " |"
        )

    path_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    before_db = resolve_project_path(args.before_db)
    after_db = resolve_project_path(args.after_db)
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)

    before_suite = run_suite(before_db)
    after_suite = run_suite(after_db)
    paired_results = pair_results(before_suite["rows"], after_suite["rows"])

    payload = {
        "generated_at_utc": now_utc(),
        "before_db": str(before_db),
        "after_db": str(after_db),
        "before_summary": before_suite["summary"],
        "after_summary": after_suite["summary"],
        "paired_results": paired_results,
    }
    write_outputs(output_json, output_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
