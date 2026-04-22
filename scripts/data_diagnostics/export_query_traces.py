#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import math
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


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
)
from backend.perf import (  # noqa: E402
    REQUIRED_STAGE_NAMES,
    new_request_trace,
    reset_current_trace,
    set_current_trace,
    stage_timer,
)
from backend.retrieval.minimal import compact_text, preview_text  # noqa: E402


DEFAULT_GOLDSET = "artifacts/evaluation/goldset_v2_working_150.json"
DEFAULT_OUTPUT = "artifacts/data_diagnostics/query_trace_bundle_v1.json"
DEFAULT_LATENCY_SOURCE = "artifacts/perf/latency_after.json"

TRACE_QUERY_SPECS = [
    {"trace_id": "trace_source_formula_huanglian", "category": "条文定位题", "query": "黄连汤方的条文是什么？"},
    {"trace_id": "trace_source_passage_first", "category": "条文定位题", "query": "第一条原文是什么？"},
    {"trace_id": "trace_formula_composition_guizhi", "category": "方剂题", "query": "桂枝汤方由什么组成？"},
    {"trace_id": "trace_formula_effect_mahuang", "category": "方剂题", "query": "麻黄汤方有什么作用？"},
    {"trace_id": "trace_meaning_shaozhen", "category": "术语解释题", "query": "烧针益阳而损阴是什么意思？"},
    {"trace_id": "trace_meaning_yingwei", "category": "术语解释题", "query": "卫气者所以温分肉是什么意思？"},
    {
        "trace_id": "trace_comparison_guizhi_plus",
        "category": "对比题",
        "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
    },
    {
        "trace_id": "trace_comparison_chengqi",
        "category": "对比题",
        "query": "大承气汤方和小承气汤方有什么不同？",
    },
    {"trace_id": "trace_commentarial_liu_taiyang", "category": "commentarial 辅助题", "query": "刘渡舟怎么看太阳病提纲？"},
    {"trace_id": "trace_commentarial_two_guizhi", "category": "commentarial 辅助题", "query": "两位老师怎么讲桂枝汤？"},
    {"trace_id": "trace_refuse_quantum", "category": "应拒答题", "query": "书中有没有提到量子纠缠？"},
    {"trace_id": "trace_refuse_personal", "category": "应拒答题", "query": "我发烧了能不能用麻黄汤？"},
]


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def percentile(values: list[float], ratio: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 3)
    ordered = sorted(values)
    index = (len(ordered) - 1) * ratio
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(ordered[lower], 3)
    fraction = index - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 3)


def stats(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "avg_ms": round(sum(values) / len(values), 3) if values else None,
        "p50_ms": percentile(values, 0.50),
        "p95_ms": percentile(values, 0.95),
        "max_ms": round(max(values), 3) if values else None,
    }


def normalize_stage_name(stage_name: str) -> str:
    return stage_name.replace("/", "_").replace("-", "_")


def summarize_latency_source(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"source_path": str(path), "available": False, "reason": "missing_latency_source"}

    payload = load_json(path)
    results = payload.get("results") or []
    values_by_stage: dict[str, list[float]] = {}
    for row in results:
        for stage_name, value in (row.get("server_timing") or {}).items():
            if isinstance(value, (int, float)):
                values_by_stage.setdefault(normalize_stage_name(stage_name), []).append(float(value))

    retrieval_parts = [
        "sparse_retrieval",
        "dense_embed",
        "dense_search_faiss",
        "fusion_rrf",
        "rerank_cross_encoder",
    ]
    retrieval_values: list[float] = []
    for row in results:
        timing = {normalize_stage_name(k): v for k, v in (row.get("server_timing") or {}).items()}
        if any(part in timing for part in retrieval_parts):
            retrieval_values.append(round(sum(float(timing.get(part, 0.0)) for part in retrieval_parts), 3))
    if retrieval_values:
        values_by_stage["retrieval_total_without_gating"] = retrieval_values

    required_aliases = {
        "retrieval": "retrieval_total_without_gating",
        "sparse": "sparse_retrieval",
        "dense_embed": "dense_embed",
        "dense_search": "dense_search_faiss",
        "fusion": "fusion_rrf",
        "rerank": "rerank_cross_encoder",
        "evidence_gating": "evidence_gating",
        "llm_generate": "llm_generate",
        "response_build_serialize": "response_build_serialize",
        "total": "total",
    }
    required_summary = {
        label: stats(values_by_stage.get(source_name, []))
        for label, source_name in required_aliases.items()
    }
    return {
        "source_path": str(path),
        "available": True,
        "label": payload.get("label"),
        "total_requests": payload.get("total_requests") or len(results),
        "rounds": payload.get("rounds"),
        "query_count": payload.get("query_count"),
        "required_stage_summary": required_summary,
        "raw_server_timing_summary": payload.get("server_timing_summary") or {},
    }


def compact_row(row: dict[str, Any], *, include_text: bool = False) -> dict[str, Any]:
    selected = {
        "record_id": row.get("record_id"),
        "record_table": row.get("record_table"),
        "source_object": row.get("source_object"),
        "chapter_id": row.get("chapter_id"),
        "chapter_name": row.get("chapter_name"),
        "evidence_level": row.get("evidence_level"),
        "display_allowed": row.get("display_allowed"),
        "policy_source_id": row.get("policy_source_id"),
        "default_weight_tier": row.get("default_weight_tier"),
        "topic_consistency": row.get("topic_consistency"),
        "topic_anchor": row.get("topic_anchor"),
        "primary_allowed": row.get("primary_allowed"),
        "primary_block_reason": row.get("primary_block_reason"),
        "text_match_score": row.get("text_match_score"),
        "sparse_score": row.get("sparse_score"),
        "dense_score": row.get("dense_score"),
        "dense_rank_score": row.get("dense_rank_score"),
        "rrf_score": row.get("rrf_score"),
        "rerank_score": row.get("rerank_score"),
        "combined_score": row.get("combined_score"),
        "stage_sources": row.get("stage_sources"),
        "stage_ranks": row.get("stage_ranks"),
        "matched_terms": row.get("matched_terms"),
        "risk_flag": row.get("risk_flag"),
        "retrieval_paths": row.get("retrieval_paths"),
        "text_preview": row.get("text_preview") or preview_text(row.get("retrieval_text"), limit=120),
    }
    if include_text:
        selected["retrieval_text"] = row.get("retrieval_text")
    return {key: value for key, value in selected.items() if value not in (None, [], {})}


def summarize_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": item.get("record_id"),
        "record_type": item.get("record_type"),
        "display_role": item.get("display_role"),
        "title": item.get("title"),
        "evidence_level": item.get("evidence_level"),
        "chapter_id": item.get("chapter_id"),
        "chapter_title": item.get("chapter_title"),
        "risk_flags": item.get("risk_flags") or [],
        "snippet": item.get("snippet"),
    }


def summarize_retrieval_call(call_index: int, query_text: str, retrieval: dict[str, Any]) -> dict[str, Any]:
    trace = retrieval.get("retrieval_trace") or {}
    return {
        "call_index": call_index,
        "query_text": query_text,
        "query_request": retrieval.get("query_request"),
        "mode": retrieval.get("mode"),
        "mode_reason": retrieval.get("mode_reason"),
        "runtime_risk_flags": retrieval.get("runtime_risk_flags") or [],
        "raw_candidate_count": len(retrieval.get("raw_candidates") or []),
        "raw_candidates_after_final_gate_top": [
            compact_row(row) for row in (retrieval.get("raw_candidates") or [])[:12]
        ],
        "sparse_top_k": trace.get("sparse_top_candidates") or [],
        "dense_top_k": trace.get("dense_top_candidates") or {},
        "fusion_top_k": trace.get("fusion_top_candidates") or [],
        "rerank_top_k": trace.get("rerank_top_candidates") or [],
        "final_slots_from_retrieval": {
            "primary": [compact_row(row) for row in retrieval.get("primary_evidence") or []],
            "secondary": [compact_row(row) for row in retrieval.get("secondary_evidence") or []],
            "review": [compact_row(row) for row in retrieval.get("risk_materials") or []],
        },
        "gate_filter_demotion_signals": {
            "annotation_links_disabled": trace.get("annotation_links_disabled")
            or retrieval.get("annotation_links_enabled") is False,
            "blocked_sources": trace.get("blocked_sources") or [],
            "chunk_hits": trace.get("chunk_hits") or [],
            "sparse_backend": trace.get("sparse_backend") or {},
            "controlled_replay": trace.get("controlled_replay") or {},
            "perf_flags": trace.get("perf_flags") or {},
            "topic_mismatch_demotions": [
                compact_row(row)
                for row in (retrieval.get("secondary_evidence") or [])
                if "topic_mismatch_demoted" in (row.get("risk_flag") or [])
            ],
            "primary_blocked_raw_candidates": [
                compact_row(row)
                for row in (retrieval.get("raw_candidates") or [])
                if row.get("primary_block_reason")
            ][:8],
        },
    }


def trace_query(assembler: AnswerAssembler, query_spec: dict[str, Any]) -> dict[str, Any]:
    retrieval_calls: list[dict[str, Any]] = []
    original_retrieve = assembler.engine.retrieve

    def traced_retrieve(query_text: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original_retrieve(query_text, *args, **kwargs)
        retrieval_calls.append(summarize_retrieval_call(len(retrieval_calls) + 1, query_text, result))
        return result

    assembler.engine.retrieve = traced_retrieve  # type: ignore[method-assign]
    perf_trace = new_request_trace(request_path="offline_data_diagnostics", query=query_spec["query"])
    token = set_current_trace(perf_trace)
    try:
        with stage_timer("request_parse"):
            query_text = str(query_spec["query"]).strip()
        payload = assembler.assemble(query_text)
        perf_trace.status_code = 200
    finally:
        reset_current_trace(token)
        assembler.engine.retrieve = original_retrieve  # type: ignore[method-assign]

    commentarial_route_debug = None
    if hasattr(assembler.commentarial_layer, "get_last_route_debug"):
        commentarial_route_debug = assembler.commentarial_layer.get_last_route_debug()
    response_summary = {
        "answer_mode": payload.get("answer_mode"),
        "answer_text_excerpt": preview_text(payload.get("answer_text"), limit=220),
        "primary_evidence": [summarize_evidence_item(item) for item in payload.get("primary_evidence") or []],
        "secondary_evidence": [summarize_evidence_item(item) for item in payload.get("secondary_evidence") or []],
        "review_materials": [summarize_evidence_item(item) for item in payload.get("review_materials") or []],
        "citations": payload.get("citations") or [],
        "review_notice": payload.get("review_notice"),
        "refuse_reason": payload.get("refuse_reason"),
        "commentarial": payload.get("commentarial"),
    }
    return {
        "trace_id": query_spec["trace_id"],
        "category": query_spec["category"],
        "query": query_spec["query"],
        "route_and_rewrite_debug": {
            "commentarial_route_debug": commentarial_route_debug,
            "comparison_debug": assembler.get_last_comparison_debug(),
            "general_debug": getattr(assembler, "_last_general_debug", None),
            "definition_priority_debug": assembler.get_last_definition_priority_debug(),
            "llm_debug": assembler.get_last_llm_debug(),
        },
        "retrieval_calls": retrieval_calls,
        "final_response": response_summary,
        "offline_perf_trace": perf_trace.to_log_record(),
    }


def instantiate_assembler(args: argparse.Namespace) -> AnswerAssembler:
    return AnswerAssembler(
        db_path=resolve_project_path(args.db_path),
        policy_path=resolve_project_path(args.policy_json),
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=resolve_project_path(args.cache_dir),
        dense_chunks_index=resolve_project_path(args.dense_chunks_index),
        dense_chunks_meta=resolve_project_path(args.dense_chunks_meta),
        dense_main_index=resolve_project_path(args.dense_main_index),
        dense_main_meta=resolve_project_path(args.dense_main_meta),
    )


def literal_assignments(path: Path, names: set[str]) -> dict[str, Any]:
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except Exception:
                    pass
    return values


def infer_smoke_type(query: str, expected_mode: str | None) -> str:
    if expected_mode == "refuse":
        return "refusal"
    if any(hint in query for hint in ("区别", "不同", "异同", "比较")):
        return "comparison"
    if any(hint in query for hint in ("怎么办", "怎么处理", "如何处理")):
        return "general_overview"
    if any(hint in query for hint in ("是什么意思", "什么意思", "怎么理解")):
        return "meaning_explanation"
    if any(hint in query for hint in ("条文", "原文", "方")):
        return "source_lookup_or_formula"
    return "other"


def summarize_eval_distribution(goldset_path: Path) -> dict[str, Any]:
    goldset = load_json(goldset_path)
    items = goldset.get("items") or []
    type_counts = Counter(item.get("question_type") or "unknown" for item in items)
    mode_counts = Counter(item.get("expected_mode") or "unknown" for item in items)
    total = len(items)
    distributions = [
        {
            "question_type": question_type,
            "count": count,
            "percent": round(count * 100 / total, 2) if total else 0.0,
        }
        for question_type, count in sorted(type_counts.items())
    ]
    smoke_sources: dict[str, Any] = {}
    constants = {
        "scripts/bench_latency.py": {"DEFAULT_QUERY_SET"},
        "backend/api/minimal_api.py": {"LLM_SMOKE_EXAMPLES"},
        "backend/retrieval/minimal.py": {"DEFAULT_EXAMPLES"},
        "backend/answers/assembler.py": {"ANSWER_SMOKE_EXAMPLES"},
    }
    for rel_path, names in constants.items():
        assignments = literal_assignments(PROJECT_ROOT / rel_path, names)
        rows: list[dict[str, Any]] = []
        for value in assignments.values():
            if isinstance(value, list):
                rows.extend([row for row in value if isinstance(row, dict)])
        smoke_sources[rel_path] = {
            "query_count": len(rows),
            "type_counts": dict(
                Counter(
                    infer_smoke_type(str(row.get("query") or row.get("query_text") or ""), row.get("expected_mode"))
                    for row in rows
                )
            ),
            "queries": [
                {
                    "query_id": row.get("query_id") or row.get("example_id"),
                    "query": row.get("query") or row.get("query_text"),
                    "expected_mode": row.get("expected_mode"),
                }
                for row in rows
            ],
        }
    return {
        "goldset_path": str(goldset_path),
        "dataset_name": goldset.get("dataset_name"),
        "total_questions": total,
        "question_type_distribution": distributions,
        "expected_mode_distribution": dict(sorted(mode_counts.items())),
        "least_represented_question_types": [
            {"question_type": question_type, "count": count}
            for question_type, count in sorted(type_counts.items(), key=lambda item: (item[1], item[0]))[:3]
        ],
        "smoke_sources": smoke_sources,
    }


def sqlite_inventory(db_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    objects = [dict(row) for row in conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    )]
    table_names = [
        row["name"]
        for row in objects
        if row["type"] in {"table", "view"} and not row["name"].startswith("retrieval_sparse_fts_")
    ]
    table_info: dict[str, Any] = {}
    for table_name in table_names:
        columns = [dict(row) for row in conn.execute(f"PRAGMA table_info({table_name})")]
        count = None
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        except sqlite3.DatabaseError:
            pass
        table_info[table_name] = {"row_count": count, "columns": columns}

    unified_counts = [
        dict(row)
        for row in conn.execute(
            """
            SELECT record_table, source_object, evidence_level, display_allowed,
                   policy_source_id, default_weight_tier, COUNT(*) AS count
            FROM vw_retrieval_records_unified
            GROUP BY record_table, source_object, evidence_level, display_allowed,
                     policy_source_id, default_weight_tier
            ORDER BY record_table, source_object
            """
        )
    ]
    chunk_types = [
        dict(row)
        for row in conn.execute(
            """
            SELECT chunk_type, retrieval_tier_raw, COUNT(*) AS count,
                   MIN(length(chunk_text)) AS min_len,
                   ROUND(AVG(length(chunk_text)), 1) AS avg_len,
                   MAX(length(chunk_text)) AS max_len
            FROM records_chunks
            GROUP BY chunk_type, retrieval_tier_raw
            ORDER BY count DESC, chunk_type
            """
        )
    ]
    conn.close()
    return {
        "db_path": str(db_path),
        "sqlite_objects": [{"type": row["type"], "name": row["name"]} for row in objects],
        "tables_and_views": table_info,
        "unified_view_counts": unified_counts,
        "chunk_type_stats": chunk_types,
    }


def json_source_inventory() -> dict[str, Any]:
    source_paths = [
        "data/processed/zjshl_dataset_v2/books.json",
        "data/processed/zjshl_dataset_v2/chapters.json",
        "data/processed/zjshl_dataset_v2/main_passages.json",
        "data/processed/zjshl_dataset_v2/chunks.json",
        "data/processed/zjshl_dataset_v2/annotations.json",
        "data/processed/zjshl_dataset_v2/passages.json",
        "data/processed/zjshl_dataset_v2/ambiguous_passages.json",
        "data/processed/zjshl_dataset_v2/aliases.json",
        "data/processed/zjshl_dataset_v2/annotation_links.json",
    ]
    inventory: dict[str, Any] = {}
    for rel_path in source_paths:
        path = PROJECT_ROOT / rel_path
        if not path.exists():
            inventory[rel_path] = {"exists": False}
            continue
        payload = load_json(path)
        rows = payload if isinstance(payload, list) else payload.get("items") if isinstance(payload, dict) else None
        entry: dict[str, Any] = {"exists": True, "json_type": type(payload).__name__}
        if isinstance(rows, list):
            keys = sorted({key for row in rows if isinstance(row, dict) for key in row})
            entry.update(
                {
                    "row_count": len(rows),
                    "fields": keys,
                    "sample": {key: rows[0].get(key) for key in keys[:10]} if rows else {},
                }
            )
        elif isinstance(payload, dict):
            entry.update({"top_level_keys": sorted(payload.keys())})
        inventory[rel_path] = entry
    return inventory


def commentarial_inventory() -> dict[str, Any]:
    bundle_dir = PROJECT_ROOT / "data/processed/commentarial_layer_round3/commentarial_handoff_bundle"
    units_path = bundle_dir / "commentarial_units.jsonl"
    links_path = bundle_dir / "commentarial_anchor_links_resolved.jsonl"
    units: list[dict[str, Any]] = []
    if units_path.exists():
        with units_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    units.append(json.loads(line))
    links: list[dict[str, Any]] = []
    if links_path.exists():
        with links_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    links.append(json.loads(line))
    return {
        "bundle_dir": str(bundle_dir),
        "unit_count": len(units),
        "resolved_link_count": len(links),
        "unit_fields": sorted({key for row in units for key in row.keys()}),
        "anchor_type_counts": dict(Counter(str(row.get("anchor_type") or "unknown") for row in units)),
        "commentator_counts": dict(Counter(str(row.get("commentator") or "unknown") for row in units)),
        "eligibility_counts": {
            field: sum(1 for row in units if row.get(field))
            for field in (
                "eligible_for_default_assistive_retrieval",
                "eligible_for_named_view",
                "eligible_for_comparison_retrieval",
                "eligible_for_meta_learning_view",
                "never_use_in_primary",
                "use_for_confidence_gate",
                "needs_manual_anchor_review",
                "needs_manual_content_review",
            )
        },
        "resolved_link_status_counts": dict(
            Counter(str(row.get("resolution_status") or "unknown") for row in links)
        ),
    }


def build_data_inventory(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "sqlite": sqlite_inventory(resolve_project_path(args.db_path)),
        "json_sources": json_source_inventory(),
        "commentarial": commentarial_inventory(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export data-layer diagnostics and representative query traces.")
    parser.add_argument("--goldset", default=DEFAULT_GOLDSET)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--latency-source", default=DEFAULT_LATENCY_SOURCE)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Allow configured LLM calls. Default keeps diagnostics offline/rule-only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.enable_llm:
        os.environ["PERF_DISABLE_LLM"] = "1"
        os.environ.setdefault("TCM_RAG_LLM_ENABLED", "false")

    output_path = resolve_project_path(args.output)
    goldset_path = resolve_project_path(args.goldset)
    latency_source = resolve_project_path(args.latency_source)

    assembler = instantiate_assembler(args)
    try:
        traces = [trace_query(assembler, spec) for spec in TRACE_QUERY_SPECS]
    finally:
        assembler.close()

    payload = {
        "generated_at_utc": now_utc(),
        "scope_note": "Diagnostics-only export. No prompt, API, frontend, payload contract, answer_mode, or retrieval logic was changed.",
        "runtime_flags": {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "TCM_RAG_LLM_ENABLED": os.environ.get("TCM_RAG_LLM_ENABLED"),
        },
        "trace_query_count": len(traces),
        "trace_categories": dict(Counter(trace["category"] for trace in traces)),
        "required_perf_stage_names": list(REQUIRED_STAGE_NAMES),
        "eval_distribution_snapshot": summarize_eval_distribution(goldset_path),
        "latency_breakdown_snapshot": summarize_latency_source(latency_source),
        "data_inventory_snapshot": build_data_inventory(args),
        "traces": traces,
    }
    write_json(output_path, payload)
    print(f"[data-diagnostics] wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
