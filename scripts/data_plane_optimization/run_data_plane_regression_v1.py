#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
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


DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_data_plane_v1.db"
DEFAULT_AFTER_DB = DEFAULT_DB_PATH
DEFAULT_OUTPUT_JSON = "artifacts/data_plane_optimization/data_plane_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_plane_optimization/data_plane_regression_v1.md"
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}

REGRESSION_QUERIES: tuple[dict[str, str], ...] = (
    {"category": "formula_exact", "query": "桂枝汤方的条文是什么？"},
    {"category": "formula_exact", "query": "麻黄汤方的条文是什么？"},
    {"category": "formula_exact", "query": "猪苓汤方的条文是什么？"},
    {"category": "formula_exact", "query": "葛根黄芩黄连汤方的条文是什么？"},
    {"category": "formula_similar", "query": "桂枝去芍药汤方的条文是什么？"},
    {"category": "formula_similar", "query": "桂枝去芍药加附子汤方的条文是什么？"},
    {"category": "formula_comparison", "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？"},
    {"category": "formula_comparison", "query": "栀子豉汤方和栀子干姜汤方有什么不同？"},
    {"category": "formula_comparison", "query": "白虎汤方和白虎加人参汤方的区别是什么？"},
    {"category": "formula_comparison", "query": "甘草乾姜汤方和芍药甘草汤方的区别是什么？"},
    {"category": "formula_easy_confuse", "query": "桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？"},
    {"category": "formula_easy_confuse", "query": "四逆汤方和四逆加人参汤方有什么不同？"},
    {"category": "definition", "query": "什么是发汗药"},
    {"category": "definition", "query": "发汗药是什么意思"},
    {"category": "definition", "query": "什么是下药"},
    {"category": "definition", "query": "下药是什么意思"},
    {"category": "definition", "query": "什么是坏病"},
    {"category": "definition", "query": "坏病是什么意思"},
    {"category": "definition", "query": "什么是消渴"},
    {"category": "definition", "query": "什么是风温"},
    {"category": "definition", "query": "风温是什么意思"},
    {"category": "definition", "query": "什么是小结胸"},
    {"category": "definition", "query": "什么是脏结"},
    {"category": "definition", "query": "什么是虚烦"},
    {"category": "definition", "query": "什么是内烦"},
    {"category": "definition", "query": "什么是伏气"},
    {"category": "definition", "query": "什么是两感"},
    {"category": "definition", "query": "什么是湿痹"},
    {"category": "definition", "query": "什么是胆瘅"},
    {"category": "learner_short", "query": "下药是干什么的"},
    {"category": "learner_short", "query": "睡着出汗是什么意思"},
    {"category": "learner_short", "query": "四肢不温是什么"},
    {"category": "learner_short", "query": "口苦病是什么意思"},
    {"category": "learner_short", "query": "时气是什么意思"},
    {"category": "learner_short", "query": "气从少腹上冲是什么意思"},
    {"category": "learner_short", "query": "表里两感是什么意思"},
    {"category": "learner_short", "query": "水饮结胸是什么意思"},
    {"category": "learner_short", "query": "泻下药是什么意思"},
    {"category": "boundary_review_only", "query": "神丹是什么意思"},
    {"category": "boundary_review_only", "query": "两阳是什么意思"},
    {"category": "boundary_review_only", "query": "将军是什么意思"},
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run data-plane regression v1.")
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
                    "chapter_id": item.get("chapter_id"),
                    "snippet": item.get("snippet"),
                }
            )
    return forbidden


def summarize_one_result(assembler: AnswerAssembler, query: str, category: str) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    definition_debug = assembler.get_last_definition_priority_debug() or {}
    primary = payload.get("primary_evidence") or []
    secondary = payload.get("secondary_evidence") or []
    review = payload.get("review_materials") or []
    raw_top = retrieval.get("raw_candidates") or []
    bad_formula_anchor_count = sum(1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS)
    support_only = payload.get("answer_mode") == "weak_with_review_notice" and not primary and bool(secondary or review)
    return {
        "query": query,
        "category": category,
        "answer_mode": payload.get("answer_mode"),
        "primary_ids": [item.get("record_id") for item in primary],
        "secondary_ids": [item.get("record_id") for item in secondary],
        "review_ids": [item.get("record_id") for item in review],
        "primary_record_types": [item.get("record_type") for item in primary],
        "primary_forbidden_items": primary_forbidden_items(payload),
        "formula_normalization": retrieval.get("query_request", {}).get("formula_normalization") or {},
        "term_normalization": retrieval.get("query_request", {}).get("term_normalization") or {},
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "definition_debug": definition_debug,
        "definition_object_primary_count": sum(
            1 for item in primary if item.get("record_type") == "definition_terms"
        ),
        "formula_bad_anchor_top5_count": bad_formula_anchor_count,
        "support_only": support_only,
        "raw_top_candidates": [
            {
                "record_id": row.get("record_id"),
                "record_table": row.get("record_table"),
                "source_object": row.get("source_object"),
                "topic_consistency": row.get("topic_consistency"),
                "definition_scope": row.get("definition_scope"),
                "formula_scope": row.get("formula_scope"),
                "matched_terms": row.get("matched_terms") or [],
            }
            for row in raw_top[:6]
        ],
    }


def load_registry_snapshot(db_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        snapshot = {}
        for table_name in (
            "definition_term_registry",
            "retrieval_ready_definition_view",
            "term_alias_registry",
            "learner_query_normalization_lexicon",
            "formula_canonical_registry",
        ):
            try:
                snapshot[f"{table_name}_count"] = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            except sqlite3.Error:
                snapshot[f"{table_name}_count"] = None
        return snapshot
    finally:
        conn.close()


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
                row["formula_bad_anchor_top5_count"]
                for row in rows
                if row["category"].startswith("formula")
            ),
            "support_only_count": sum(1 for row in rows if row["support_only"]),
            "definition_object_primary_query_count": sum(1 for row in rows if row["definition_object_primary_count"]),
            "short_term_strong_count": sum(
                1 for row in rows if row["category"] == "learner_short" and row["answer_mode"] == "strong"
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
                    "promoted_to_strong": before_row["answer_mode"] != "strong" and after_row["answer_mode"] == "strong",
                    "support_only_reduced": before_row["support_only"] and not after_row["support_only"],
                    "definition_object_now_primary": after_row["definition_object_primary_count"] > 0,
                    "short_term_focus_now_normalized": before_row.get("query_focus_source") != "term_normalization"
                    and after_row.get("query_focus_source") == "term_normalization",
                },
            }
        )
    return paired


def write_outputs(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Data Plane Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- before_db: `{payload['before_db']}`",
        f"- after_db: `{payload['after_db']}`",
        "",
        "## Registry Snapshot",
        "",
        f"- before definition_term_registry_count: `{payload['before_registry'].get('definition_term_registry_count')}`",
        f"- after definition_term_registry_count: `{payload['after_registry'].get('definition_term_registry_count')}`",
        f"- before retrieval_ready_definition_view_count: `{payload['before_registry'].get('retrieval_ready_definition_view_count')}`",
        f"- after retrieval_ready_definition_view_count: `{payload['after_registry'].get('retrieval_ready_definition_view_count')}`",
        f"- after term_alias_registry_count: `{payload['after_registry'].get('term_alias_registry_count')}`",
        f"- after learner_query_normalization_lexicon_count: `{payload['after_registry'].get('learner_query_normalization_lexicon_count')}`",
        "",
        "## Summary",
        "",
        f"- before mode_counts: `{json.dumps(payload['before_summary']['mode_counts'], ensure_ascii=False)}`",
        f"- after mode_counts: `{json.dumps(payload['after_summary']['mode_counts'], ensure_ascii=False)}`",
        f"- forbidden_primary before -> after: `{payload['before_summary']['forbidden_primary_total']} -> {payload['after_summary']['forbidden_primary_total']}`",
        f"- formula bad anchors top5 before -> after: `{payload['before_summary']['formula_bad_anchor_top5_total']} -> {payload['after_summary']['formula_bad_anchor_top5_total']}`",
        f"- support_only before -> after: `{payload['before_summary']['support_only_count']} -> {payload['after_summary']['support_only_count']}`",
        f"- promoted_to_strong_count: `{payload['delta_summary']['promoted_to_strong_count']}`",
        f"- short_term_strong before -> after: `{payload['before_summary']['short_term_strong_count']} -> {payload['after_summary']['short_term_strong_count']}`",
        "",
        "## Query Table",
        "",
        "| category | query | before | after | promoted | support_only_reduced | focus_source_before | focus_source_after | primary_after |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in payload["paired_results"]:
        lines.append(
            "| {category} | {query} | {before_mode} | {after_mode} | {promoted} | {support} | {focus_before} | {focus_after} | {primary_after} |".format(
                category=row["category"],
                query=row["query"],
                before_mode=row["before"]["answer_mode"],
                after_mode=row["after"]["answer_mode"],
                promoted="yes" if row["delta"]["promoted_to_strong"] else "no",
                support="yes" if row["delta"]["support_only_reduced"] else "no",
                focus_before=row["before"].get("query_focus_source") or "-",
                focus_after=row["after"].get("query_focus_source") or "-",
                primary_after="<br>".join(row["after"]["primary_ids"]) or "-",
            )
        )

    lines.extend(
        [
            "",
            "## Typical Before / After",
            "",
        ]
    )
    for row in payload["delta_summary"]["typical_examples"][:8]:
        lines.extend(
            [
                f"### {row['query']}",
                "",
                f"- category: `{row['category']}`",
                f"- before: `{row['before_mode']}`",
                f"- after: `{row['after_mode']}`",
                f"- before primary: `{json.dumps(row['before_primary_ids'], ensure_ascii=False)}`",
                f"- after primary: `{json.dumps(row['after_primary_ids'], ensure_ascii=False)}`",
                f"- after term_normalization: `{json.dumps(row['after_term_normalization'], ensure_ascii=False)}`",
                "",
            ]
        )
    path_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    before_db = resolve_project_path(args.before_db)
    after_db = resolve_project_path(args.after_db)
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)

    before_registry = load_registry_snapshot(before_db)
    after_registry = load_registry_snapshot(after_db)
    before_suite = run_suite(before_db)
    after_suite = run_suite(after_db)
    paired_results = pair_results(before_suite["rows"], after_suite["rows"])

    promoted_rows = [row for row in paired_results if row["delta"]["promoted_to_strong"]]
    support_reduced_rows = [row for row in paired_results if row["delta"]["support_only_reduced"]]
    short_term_normalized_rows = [row for row in paired_results if row["delta"]["short_term_focus_now_normalized"]]
    typical_examples = promoted_rows[:4] + support_reduced_rows[:2] + short_term_normalized_rows[:2]

    payload = {
        "generated_at_utc": now_utc(),
        "before_db": str(before_db),
        "after_db": str(after_db),
        "before_registry": before_registry,
        "after_registry": after_registry,
        "before_summary": before_suite["summary"],
        "after_summary": after_suite["summary"],
        "paired_results": paired_results,
        "delta_summary": {
            "promoted_to_strong_count": len(promoted_rows),
            "support_only_reduced_count": len(support_reduced_rows),
            "short_term_focus_now_normalized_count": len(short_term_normalized_rows),
            "typical_examples": [
                {
                    "query": row["query"],
                    "category": row["category"],
                    "before_mode": row["before"]["answer_mode"],
                    "after_mode": row["after"]["answer_mode"],
                    "before_primary_ids": row["before"]["primary_ids"],
                    "after_primary_ids": row["after"]["primary_ids"],
                    "after_term_normalization": row["after"]["term_normalization"],
                }
                for row in typical_examples
            ],
        },
    }
    write_outputs(output_json, output_md, payload)
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
