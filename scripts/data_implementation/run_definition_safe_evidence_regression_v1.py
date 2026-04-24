#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
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


DEFAULT_OUTPUT_JSON = "artifacts/data_implementation/definition_safe_evidence_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_implementation/definition_safe_evidence_regression_v1.md"
DEFAULT_BASELINE_JSON = "artifacts/assembler_boundary_fix/definition_primary_regression_v1.json"
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
ALLOWED_DEFINITION_PRIMARY_TYPES = {"definition_terms", "main_passages"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}

DEFINITION_QUERIES = [
    "什么是发汗药",
    "发汗药是什么意思",
    "坏病是什么",
    "坏病是什么意思",
    "下药是什么意思",
    "阳结是什么",
    "阳结是什么意思",
    "阴结是什么意思",
    "承气汤是下药吗",
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
    parser = argparse.ArgumentParser(description="Run definition safe evidence upgrade regression v1.")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--baseline-json", default=DEFAULT_BASELINE_JSON)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_baseline(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row.get("query"): row for row in payload.get("definition_results") or [] if row.get("query")}


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
        "stage_sources": row.get("stage_sources") or [],
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


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    forbidden = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            forbidden.append(summarize_evidence_item(item))
    return forbidden


def definition_primary_allowed(payload: dict[str, Any]) -> bool:
    primary = payload.get("primary_evidence") or []
    return bool(primary) and all(item.get("record_type") in ALLOWED_DEFINITION_PRIMARY_TYPES for item in primary)


def formula_primary_safe_main_only(payload: dict[str, Any]) -> bool:
    primary = payload.get("primary_evidence") or []
    return bool(primary) and all(
        item.get("record_type") == "main_passages"
        and str(item.get("record_id") or "").startswith("safe:main_passages:")
        for item in primary
    )


def run_definition_query(
    assembler: AnswerAssembler,
    query: str,
    baseline_by_query: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    debug = assembler.get_last_definition_priority_debug()
    baseline = baseline_by_query.get(query) or {}
    support_items = payload.get("secondary_evidence", []) + payload.get("review_materials", [])
    return {
        "query": query,
        "previous_payload_mode": baseline.get("payload_mode"),
        "payload_mode": payload.get("answer_mode"),
        "promoted_from_weak": baseline.get("payload_mode") == "weak_with_review_notice"
        and payload.get("answer_mode") == "strong",
        "primary_allowed_definition_source": definition_primary_allowed(payload),
        "primary_forbidden_items": primary_forbidden_items(payload),
        "payload_primary": [summarize_evidence_item(item) for item in payload.get("primary_evidence", [])],
        "payload_secondary": [summarize_evidence_item(item) for item in payload.get("secondary_evidence", [])],
        "payload_review": [summarize_evidence_item(item) for item in payload.get("review_materials", [])],
        "support_full_passages": [
            summarize_evidence_item(item)
            for item in support_items
            if str(item.get("record_id") or "").startswith("full:passages:")
        ],
        "raw_top_candidates": [summarize_candidate(row) for row in (retrieval.get("raw_candidates") or [])[:8]],
        "definition_priority_debug": debug,
    }


def run_formula_query(assembler: AnswerAssembler, query: str) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    top5 = retrieval.get("raw_candidates", [])[:5]
    bad_formula_count = sum(1 for row in top5 if row.get("topic_consistency") in BAD_FORMULA_TOPICS)
    primary_formula_backrefs = sum(
        1
        for row in retrieval.get("primary_evidence", [])
        for path in row.get("retrieval_paths") or []
        if path.get("type") == "formula_object_backref"
    )
    return {
        "query": query,
        "payload_mode": payload.get("answer_mode"),
        "formula_normalization": retrieval.get("query_request", {}).get("formula_normalization") or {},
        "primary_safe_main_only": formula_primary_safe_main_only(payload),
        "primary_forbidden_items": primary_forbidden_items(payload),
        "top5_bad_formula_anchor_count": bad_formula_count,
        "primary_formula_backref_count": primary_formula_backrefs,
        "raw_top_candidates": [summarize_candidate(row) for row in top5],
        "payload_primary": [summarize_evidence_item(item) for item in payload.get("primary_evidence", [])],
    }


def write_outputs(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Definition Safe Evidence Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- definition_queries: `{len(payload['definition_results'])}`",
        f"- formula_queries: `{len(payload['formula_results'])}`",
        f"- definition_strong_count: `{payload['summary']['definition_strong_count']}`",
        f"- definition_promoted_from_weak_count: `{payload['summary']['definition_promoted_from_weak_count']}`",
        f"- definition_primary_forbidden_total: `{payload['summary']['definition_primary_forbidden_total']}`",
        f"- formula_strong_count: `{payload['summary']['formula_strong_count']}`",
        f"- formula_primary_safe_main_all: `{payload['summary']['formula_primary_safe_main_all']}`",
        f"- formula_top5_bad_formula_anchor_total: `{payload['summary']['formula_top5_bad_formula_anchor_total']}`",
        "",
        "## Definition / Meaning Queries",
        "",
        "| query | previous mode | current mode | promoted | primary ids | route | forbidden primary |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["definition_results"]:
        debug = row.get("definition_priority_debug") or {}
        primary_ids = "<br>".join(item["record_id"] for item in row.get("payload_primary") or []) or "-"
        lines.append(
            "| {query} | {previous} | {current} | {promoted} | {primary} | {route} | {forbidden} |".format(
                query=row["query"],
                previous=row.get("previous_payload_mode") or "-",
                current=row.get("payload_mode"),
                promoted="yes" if row.get("promoted_from_weak") else "no",
                primary=primary_ids,
                route=debug.get("family_id") or "-",
                forbidden=len(row.get("primary_forbidden_items") or []),
            )
        )

    lines.extend(
        [
            "",
            "## Formula Regression Queries",
            "",
            "| query | mode | primary safe main | bad anchors top5 | formula backrefs |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["formula_results"]:
        lines.append(
            "| {query} | {mode} | {safe} | {bad} | {backrefs} |".format(
                query=row["query"],
                mode=row.get("payload_mode"),
                safe=row.get("primary_safe_main_only"),
                bad=row.get("top5_bad_formula_anchor_count"),
                backrefs=row.get("primary_formula_backref_count"),
            )
        )

    lines.extend(["", "## Failed Conditions", ""])
    failures = payload.get("failed_conditions") or []
    lines.extend([f"- {failure}" for failure in failures] or ["- none"])
    path_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    baseline_by_query = load_baseline(resolve_project_path(args.baseline_json))

    old_env = {
        "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
        "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
        "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
    }
    os.environ["PERF_DISABLE_LLM"] = "1"
    os.environ["PERF_RETRIEVAL_MODE"] = "sparse"
    os.environ["PERF_DISABLE_RERANK"] = "1"
    assembler = make_assembler()
    try:
        definition_results = [
            run_definition_query(assembler, query, baseline_by_query) for query in DEFINITION_QUERIES
        ]
        formula_results = [run_formula_query(assembler, query) for query in FORMULA_QUERIES]
    finally:
        assembler.close()
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    summary = {
        "definition_strong_count": sum(1 for row in definition_results if row["payload_mode"] == "strong"),
        "definition_promoted_from_weak_count": sum(1 for row in definition_results if row["promoted_from_weak"]),
        "definition_primary_forbidden_total": sum(len(row["primary_forbidden_items"]) for row in definition_results),
        "definition_primary_allowed_all": all(row["primary_allowed_definition_source"] for row in definition_results),
        "formula_strong_count": sum(1 for row in formula_results if row["payload_mode"] == "strong"),
        "formula_primary_safe_main_all": all(row["primary_safe_main_only"] for row in formula_results),
        "formula_top5_bad_formula_anchor_total": sum(row["top5_bad_formula_anchor_count"] for row in formula_results),
        "formula_primary_forbidden_total": sum(len(row["primary_forbidden_items"]) for row in formula_results),
    }
    failed_conditions: list[str] = []
    if summary["definition_strong_count"] < 8:
        failed_conditions.append("definition strong count below 8")
    if summary["definition_promoted_from_weak_count"] < 4:
        failed_conditions.append("fewer than 4 baseline weak definition queries promoted to strong")
    if summary["definition_primary_forbidden_total"]:
        failed_conditions.append("forbidden full/risk source leaked into definition primary")
    if not summary["definition_primary_allowed_all"]:
        failed_conditions.append("definition primary source outside definition_terms/main_passages")
    if summary["formula_strong_count"] != len(FORMULA_QUERIES):
        failed_conditions.append("formula regression query did not remain strong")
    if not summary["formula_primary_safe_main_all"]:
        failed_conditions.append("formula primary evidence is not safe main only")
    if summary["formula_top5_bad_formula_anchor_total"]:
        failed_conditions.append("formula bad anchors appeared in top5")
    if summary["formula_primary_forbidden_total"]:
        failed_conditions.append("forbidden source leaked into formula primary")

    payload = {
        "generated_at_utc": now_utc(),
        "runtime_env": {
            "PERF_DISABLE_LLM": "1",
            "PERF_RETRIEVAL_MODE": "sparse",
            "PERF_DISABLE_RERANK": "1",
        },
        "summary": summary,
        "definition_results": definition_results,
        "formula_results": formula_results,
        "failed_conditions": failed_conditions,
    }
    write_outputs(output_json, output_md, payload)
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 1 if failed_conditions else 0


if __name__ == "__main__":
    raise SystemExit(main())
