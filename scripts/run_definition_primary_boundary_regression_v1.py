#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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


DEFAULT_OUTPUT_JSON = "artifacts/assembler_boundary_fix/definition_primary_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/assembler_boundary_fix/definition_primary_regression_v1.md"
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
RISK_SOURCE_OBJECTS = {"passages", "ambiguous_passages"}

DEFINITION_QUERIES = [
    "什么是发汗药",
    "发汗药是什么意思",
    "阳结是什么",
    "阳结是什么意思",
    "坏病是什么",
    "坏病是什么意思",
    "承气汤是下药吗",
    "桂枝汤是什么药",
]

FORMULA_QUERIES = [
    "葛根黄芩黄连汤方的条文是什么？",
    "麻黄汤方的条文是什么？",
    "大青龙汤方的条文是什么？",
    "猪苓汤方的条文是什么？",
    "甘草乾姜汤方和芍药甘草汤方的区别是什么？",
    "栀子豉汤方和栀子乾姜汤方有什么不同？",
    "白虎汤方和白虎加人参汤方的区别是什么？",
    "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run definition primary slot boundary regression v1.")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "record_table": row.get("record_table"),
        "source_object": row.get("source_object"),
        "chapter_id": row.get("chapter_id"),
        "topic_consistency": row.get("topic_consistency"),
        "formula_scope": row.get("formula_scope"),
        "combined_score": row.get("combined_score"),
        "risk_flag": row.get("risk_flag"),
        "text_preview": row.get("text_preview") or str(row.get("retrieval_text") or "")[:120],
    }


def summarize_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": item.get("record_id"),
        "record_type": item.get("record_type"),
        "display_role": item.get("display_role"),
        "evidence_level": item.get("evidence_level"),
        "chapter_id": item.get("chapter_id"),
        "risk_flags": item.get("risk_flags") or [],
        "snippet": item.get("snippet"),
    }


def summarize_retrieval_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "source_object": row.get("source_object"),
        "chapter_id": row.get("chapter_id"),
        "topic_consistency": row.get("topic_consistency"),
        "formula_scope": row.get("formula_scope"),
        "retrieval_paths": row.get("retrieval_paths") or [],
        "text_preview": row.get("text_preview"),
    }


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    forbidden = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            forbidden.append(summarize_evidence_item(item))
    return forbidden


def primary_safe_main_only(payload: dict[str, Any]) -> bool:
    primary = payload.get("primary_evidence") or []
    return bool(primary) and all(
        item.get("record_type") == "main_passages"
        and str(item.get("record_id") or "").startswith("safe:main_passages:")
        for item in primary
    )


def is_risk_candidate(row: dict[str, Any]) -> bool:
    return row.get("source_object") in RISK_SOURCE_OBJECTS or bool(row.get("risk_flag"))


def make_assembler() -> AnswerAssembler:
    return AnswerAssembler(
        db_path=resolve_project_path(DEFAULT_DB_PATH),
        policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
        embed_model=DEFAULT_EMBED_MODEL,
        rerank_model=DEFAULT_RERANK_MODEL,
        cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
        dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
        dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
        dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
        dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
    )


def run_definition_query(assembler: AnswerAssembler, query: str) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    debug = assembler.get_last_definition_priority_debug()
    support_items = payload.get("secondary_evidence", []) + payload.get("review_materials", [])
    support_full_passages = [
        summarize_evidence_item(item)
        for item in support_items
        if str(item.get("record_id") or "").startswith("full:passages:")
    ]
    return {
        "query": query,
        "retrieval_mode": retrieval.get("mode"),
        "retrieval_primary": [
            summarize_retrieval_evidence(row) for row in retrieval.get("primary_evidence", [])
        ],
        "retrieval_risk_materials": [
            summarize_retrieval_evidence(row) for row in retrieval.get("risk_materials", [])
        ],
        "raw_top_candidates": [
            summarize_candidate(row) for row in (retrieval.get("raw_candidates") or [])[:8]
        ],
        "payload_mode": payload.get("answer_mode"),
        "payload_primary": [
            summarize_evidence_item(item) for item in payload.get("primary_evidence", [])
        ],
        "payload_secondary": [
            summarize_evidence_item(item) for item in payload.get("secondary_evidence", [])
        ],
        "payload_review": [
            summarize_evidence_item(item) for item in payload.get("review_materials", [])
        ],
        "definition_priority_debug": debug,
        "primary_forbidden_items": primary_forbidden_items(payload),
        "support_full_passages": support_full_passages,
        "primary_clean": not primary_forbidden_items(payload),
    }


def run_formula_query(assembler: AnswerAssembler, query: str) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    top5 = retrieval.get("raw_candidates", [])[:5]
    bad_formula_count = sum(1 for row in top5 if row.get("topic_consistency") in BAD_FORMULA_TOPICS)
    expanded_formula_count = sum(1 for row in top5 if row.get("topic_consistency") == "expanded_formula_anchor")
    risk_count = sum(1 for row in top5 if is_risk_candidate(row))
    primary_formula_backrefs = sum(
        1
        for row in retrieval.get("primary_evidence", [])
        for path in row.get("retrieval_paths") or []
        if path.get("type") == "formula_object_backref"
    )
    formula_norm = retrieval.get("query_request", {}).get("formula_normalization") or {}
    return {
        "query": query,
        "payload_mode": payload.get("answer_mode"),
        "formula_normalization": formula_norm,
        "primary_safe_main_only": primary_safe_main_only(payload),
        "primary_forbidden_items": primary_forbidden_items(payload),
        "top5_bad_formula_anchor_count": bad_formula_count,
        "top5_expanded_formula_anchor_count": expanded_formula_count,
        "top5_risk_candidate_count": risk_count,
        "primary_formula_backref_count": primary_formula_backrefs,
        "raw_top_candidates": [summarize_candidate(row) for row in top5],
        "payload_primary": [
            summarize_evidence_item(item) for item in payload.get("primary_evidence", [])
        ],
        "retrieval_primary": [
            summarize_retrieval_evidence(row) for row in retrieval.get("primary_evidence", [])
        ],
    }


def build_report(data: dict[str, Any]) -> str:
    checks = data["checks"]
    lines = [
        "# Definition Primary Boundary Regression v1",
        "",
        f"- generated_at_utc: `{data['generated_at_utc']}`",
        f"- definition_queries: `{checks['definition_query_count']}`",
        f"- formula_queries: `{checks['formula_query_count']}`",
        f"- definition_primary_forbidden_total: `{checks['definition_primary_forbidden_total']}`",
        f"- definition_support_full_passages_count: `{checks['definition_support_full_passages_count']}`",
        f"- formula_primary_safe_main_all: `{checks['formula_primary_safe_main_all']}`",
        f"- formula_strong_count: `{checks['formula_strong_count']}`",
        f"- formula_top5_bad_formula_anchor_total: `{checks['formula_top5_bad_formula_anchor_total']}`",
        f"- primary_formula_backref_total: `{checks['primary_formula_backref_total']}`",
        "",
        "## Definition / Meaning Queries",
        "",
        "| query | mode | primary clean | primary ids | secondary/review full:passages | route |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in data["definition_results"]:
        debug = row.get("definition_priority_debug") or {}
        primary_ids = "<br>".join(item["record_id"] for item in row["payload_primary"]) or "-"
        support_ids = "<br>".join(item["record_id"] for item in row["support_full_passages"]) or "-"
        route = debug.get("family_id") or "standard/other"
        lines.append(
            f"| {row['query']} | {row['payload_mode']} | {row['primary_clean']} | "
            f"{primary_ids} | {support_ids} | {route} |"
        )

    lines.extend(
        [
            "",
            "## Formula Regression Queries",
            "",
            "| query | mode | formula norm | primary safe main | bad anchors top5 | formula backrefs |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in data["formula_results"]:
        formula_norm = row.get("formula_normalization") or {}
        lines.append(
            f"| {row['query']} | {row['payload_mode']} | {formula_norm.get('type')} | "
            f"{row['primary_safe_main_only']} | {row['top5_bad_formula_anchor_count']} | "
            f"{row['primary_formula_backref_count']} |"
        )

    if data["failed_conditions"]:
        lines.extend(["", "## Failed Conditions", ""])
        lines.extend(f"- {item}" for item in data["failed_conditions"])
    else:
        lines.extend(["", "## Failed Conditions", "", "- none"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    os.environ.setdefault("PERF_DISABLE_LLM", "1")
    os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")
    os.environ.setdefault("PERF_DISABLE_RERANK", "1")

    assembler = make_assembler()
    try:
        definition_results = [run_definition_query(assembler, query) for query in DEFINITION_QUERIES]
        formula_results = [run_formula_query(assembler, query) for query in FORMULA_QUERIES]
    finally:
        assembler.close()

    checks = {
        "definition_query_count": len(definition_results),
        "definition_primary_forbidden_total": sum(len(row["primary_forbidden_items"]) for row in definition_results),
        "definition_support_full_passages_count": sum(bool(row["support_full_passages"]) for row in definition_results),
        "formula_query_count": len(formula_results),
        "formula_primary_safe_main_all": all(row["primary_safe_main_only"] for row in formula_results),
        "formula_strong_count": sum(row["payload_mode"] == "strong" for row in formula_results),
        "formula_top5_bad_formula_anchor_total": sum(row["top5_bad_formula_anchor_count"] for row in formula_results),
        "formula_top5_expanded_formula_anchor_total": sum(
            row["top5_expanded_formula_anchor_count"] for row in formula_results
        ),
        "primary_formula_backref_total": sum(row["primary_formula_backref_count"] for row in formula_results),
    }
    failed_conditions: list[str] = []
    if checks["definition_primary_forbidden_total"] != 0:
        failed_conditions.append("definition primary contains forbidden full/risk records")
    if checks["definition_support_full_passages_count"] < 4:
        failed_conditions.append("expected full:passages support records were not retained outside primary")
    if not checks["formula_primary_safe_main_all"]:
        failed_conditions.append("formula primary evidence is not safe main passage only")
    if checks["formula_strong_count"] != checks["formula_query_count"]:
        failed_conditions.append("at least one formula regression query is no longer strong")
    if checks["formula_top5_bad_formula_anchor_total"] != 0:
        failed_conditions.append("bad formula anchors reappeared in formula top5 candidates")
    if checks["primary_formula_backref_total"] <= 0:
        failed_conditions.append("formula object backref primary support was not observed")

    data = {
        "generated_at_utc": now_utc(),
        "runtime_env": {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
            "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
        },
        "definition_results": definition_results,
        "formula_results": formula_results,
        "checks": checks,
        "failed_conditions": failed_conditions,
    }

    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(build_report(data), encoding="utf-8")
    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")
    return 1 if failed_conditions else 0


if __name__ == "__main__":
    raise SystemExit(main())
