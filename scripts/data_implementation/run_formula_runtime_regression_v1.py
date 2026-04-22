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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_POLICY_PATH = "config/layered_enablement_policy.json"
DEFAULT_POOL_PATH = "artifacts/data_diagnostics/suspected_failure_pool_v1.json"
DEFAULT_OUTPUT_JSON = "artifacts/data_implementation/formula_runtime_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_implementation/formula_runtime_regression_v1.md"
FORMULA_OBJECT_DISABLE_ENV = "TCM_DISABLE_FORMULA_OBJECT_RETRIEVAL"

BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
TARGET_FORMULA_TOPICS = {
    "formula_object_exact",
    "same_formula_span",
    "comparison_formula_object",
    "comparison_formula_span",
    "exact_formula_anchor",
}
RISK_SOURCE_OBJECTS = {"passages", "ambiguous_passages"}
PREFERRED_QUERIES = [
    "桂枝去芍药汤方和桂枝去芍药加附子汤方的条文语境有什么不同？",
    "葛根黄芩黄连汤方的条文是什么？",
    "甘草乾姜汤方和芍药甘草汤方的区别是什么？",
    "麻黄汤方的条文是什么？",
    "大青龙汤方的条文是什么？",
    "葛根加半夏汤方的条文是什么？",
    "调胃承气汤方的条文是什么？",
    "栀子豉汤方和栀子乾姜汤方有什么不同？",
    "白虎汤方和白虎加人参汤方的区别是什么？",
    "茯苓桂枝甘草大枣汤方的条文是什么？",
    "茯苓桂枝白术甘草汤方的条文是什么？",
    "猪苓汤方的条文是什么？",
    "桃核承气汤方的条文是什么？",
    "麻黄汤方和大青龙汤方的区别是什么？",
    "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay formula-related suspected failures before/after formula object runtime.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--pool-path", default=DEFAULT_POOL_PATH)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--engine", choices=("hybrid", "minimal"), default="hybrid")
    parser.add_argument("--limit", type=int, default=15)
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_pool(pool_path: Path) -> dict[str, Any]:
    return json.loads(pool_path.read_text(encoding="utf-8"))


def signal_ids(candidate: dict[str, Any]) -> list[str]:
    return [signal.get("signal_id") for signal in candidate.get("signals") or [] if signal.get("signal_id")]


def select_queries(pool: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    by_query = {candidate.get("query"): candidate for candidate in pool.get("suspected_candidates") or []}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in PREFERRED_QUERIES:
        candidate = by_query.get(query)
        if not candidate:
            continue
        selected.append(
            {
                "query": query,
                "candidate_id": candidate.get("candidate_id"),
                "question_type": candidate.get("question_type"),
                "target_formula": candidate.get("target_formula"),
                "pool_signals": signal_ids(candidate),
            }
        )
        seen.add(query)
        if len(selected) >= limit:
            return selected

    for candidate in pool.get("suspected_candidates") or []:
        query = candidate.get("query")
        if not query or query in seen:
            continue
        if "formula_cross_target_candidates" not in signal_ids(candidate):
            continue
        selected.append(
            {
                "query": query,
                "candidate_id": candidate.get("candidate_id"),
                "question_type": candidate.get("question_type"),
                "target_formula": candidate.get("target_formula"),
                "pool_signals": signal_ids(candidate),
            }
        )
        seen.add(query)
        if len(selected) >= limit:
            break
    return selected


def make_engine(args: argparse.Namespace):
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    if args.engine == "minimal":
        from backend.retrieval.minimal import RetrievalEngine

        return RetrievalEngine(db_path, policy_path)

    from backend.retrieval.hybrid import HybridRetrievalEngine

    return HybridRetrievalEngine(
        db_path,
        policy_path,
        embed_model="BAAI/bge-small-zh-v1.5",
        rerank_model="BAAI/bge-reranker-base",
        cache_dir=resolve_project_path("artifacts/hf_cache"),
        dense_chunks_index=resolve_project_path("artifacts/dense_chunks.faiss"),
        dense_chunks_meta=resolve_project_path("artifacts/dense_chunks_meta.json"),
        dense_main_index=resolve_project_path("artifacts/dense_main_passages.faiss"),
        dense_main_meta=resolve_project_path("artifacts/dense_main_passages_meta.json"),
    )


def risk_flags(row: dict[str, Any]) -> list[str]:
    value = row.get("risk_flag")
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
        except Exception:
            return [value] if value and value != "[]" else []
        return loaded if isinstance(loaded, list) else []
    return []


def is_risk_candidate(row: dict[str, Any]) -> bool:
    return row.get("source_object") in RISK_SOURCE_OBJECTS or bool(risk_flags(row))


def summarize_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "record_table": row.get("record_table"),
        "source_object": row.get("source_object"),
        "chapter_id": row.get("chapter_id"),
        "topic_consistency": row.get("topic_consistency"),
        "formula_scope": row.get("formula_scope"),
        "combined_score": row.get("combined_score"),
        "text_match_score": row.get("text_match_score"),
        "stage_sources": row.get("stage_sources") or [],
        "risk_flag": risk_flags(row),
        "text_preview": row.get("text_preview") or row.get("retrieval_text", "")[:90],
    }


def summarize_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "source_object": row.get("source_object"),
        "chapter_id": row.get("chapter_id"),
        "topic_consistency": row.get("topic_consistency"),
        "formula_scope": row.get("formula_scope"),
        "retrieval_paths": row.get("retrieval_paths") or [],
        "text_preview": row.get("text_preview"),
    }


def run_query(engine: Any, query: str) -> dict[str, Any]:
    result = engine.retrieve(query)
    top5 = result.get("raw_candidates", [])[:5]
    bad_formula_count = sum(1 for row in top5 if row.get("topic_consistency") in BAD_FORMULA_TOPICS)
    expanded_formula_count = sum(1 for row in top5 if row.get("topic_consistency") == "expanded_formula_anchor")
    different_formula_count = sum(
        1
        for row in top5
        if row.get("topic_consistency") in {"different_formula_anchor", "comparison_out_of_scope_formula_anchor"}
    )
    risk_count = sum(1 for row in top5 if is_risk_candidate(row))
    primary = result.get("primary_evidence") or []
    primary_formula_backrefs = sum(
        1
        for row in primary
        for path in row.get("retrieval_paths") or []
        if path.get("type") == "formula_object_backref"
    )
    formula_norm = (result.get("query_request") or {}).get("formula_normalization") or {}
    return {
        "mode": result.get("mode"),
        "formula_normalization": formula_norm,
        "raw_candidate_count": len(result.get("raw_candidates") or []),
        "top5_bad_formula_anchor_count": bad_formula_count,
        "top5_different_formula_anchor_count": different_formula_count,
        "top5_expanded_formula_anchor_count": expanded_formula_count,
        "top5_risk_candidate_count": risk_count,
        "formula_cross_target_candidates_triggered": bad_formula_count > 0,
        "high_risk_candidate_dominance_triggered": risk_count >= 2 or bool(top5 and is_risk_candidate(top5[0])),
        "primary_record_ids": [row.get("record_id") for row in primary],
        "primary_formula_backref_count": primary_formula_backrefs,
        "primary_target_topic_count": sum(1 for row in primary if row.get("topic_consistency") in TARGET_FORMULA_TOPICS),
        "top5_candidates": [summarize_candidate(row) for row in top5],
        "primary_evidence": [summarize_evidence(row) for row in primary],
        "secondary_evidence": [summarize_evidence(row) for row in (result.get("secondary_evidence") or [])[:5]],
        "risk_materials": [summarize_evidence(row) for row in (result.get("risk_materials") or [])[:5]],
    }


def run_pass(args: argparse.Namespace, specs: list[dict[str, Any]], *, formula_enabled: bool) -> list[dict[str, Any]]:
    old_disable = os.environ.get(FORMULA_OBJECT_DISABLE_ENV)
    if formula_enabled:
        os.environ.pop(FORMULA_OBJECT_DISABLE_ENV, None)
    else:
        os.environ[FORMULA_OBJECT_DISABLE_ENV] = "1"
    try:
        engine = make_engine(args)
        try:
            return [
                {
                    **spec,
                    **run_query(engine, spec["query"]),
                }
                for spec in specs
            ]
        finally:
            engine.close()
    finally:
        if old_disable is None:
            os.environ.pop(FORMULA_OBJECT_DISABLE_ENV, None)
        else:
            os.environ[FORMULA_OBJECT_DISABLE_ENV] = old_disable


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mode_counts = Counter(row["mode"] for row in rows)
    normalization_counts = Counter((row.get("formula_normalization") or {}).get("type") for row in rows)
    return {
        "query_count": len(rows),
        "mode_counts": dict(sorted(mode_counts.items())),
        "formula_normalization_counts": dict(sorted(normalization_counts.items())),
        "top5_bad_formula_anchor_total": sum(row["top5_bad_formula_anchor_count"] for row in rows),
        "top5_different_formula_anchor_total": sum(row["top5_different_formula_anchor_count"] for row in rows),
        "top5_expanded_formula_anchor_total": sum(row["top5_expanded_formula_anchor_count"] for row in rows),
        "top5_risk_candidate_total": sum(row["top5_risk_candidate_count"] for row in rows),
        "formula_cross_target_candidates_trigger_count": sum(
            1 for row in rows if row["formula_cross_target_candidates_triggered"]
        ),
        "high_risk_candidate_dominance_trigger_count": sum(
            1 for row in rows if row["high_risk_candidate_dominance_triggered"]
        ),
        "primary_formula_backref_total": sum(row["primary_formula_backref_count"] for row in rows),
        "primary_target_topic_total": sum(row["primary_target_topic_count"] for row in rows),
    }


def build_markdown(payload: dict[str, Any]) -> str:
    before = payload["aggregate_before"]
    after = payload["aggregate_after"]
    lines = [
        "# Formula Runtime Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- engine: `{payload['engine']}`",
        f"- query_count: `{payload['query_count']}`",
        f"- before formula object: disabled via `{FORMULA_OBJECT_DISABLE_ENV}=1`",
        f"- after formula object: enabled",
        "",
        "## Aggregate Before / After",
        "",
        "| metric | before | after | delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    metric_keys = [
        "top5_bad_formula_anchor_total",
        "top5_different_formula_anchor_total",
        "top5_expanded_formula_anchor_total",
        "top5_risk_candidate_total",
        "formula_cross_target_candidates_trigger_count",
        "high_risk_candidate_dominance_trigger_count",
        "primary_formula_backref_total",
        "primary_target_topic_total",
    ]
    for key in metric_keys:
        before_value = before.get(key, 0)
        after_value = after.get(key, 0)
        lines.append(f"| {key} | {before_value} | {after_value} | {after_value - before_value} |")

    lines.extend(
        [
            "",
            "## Per Query Summary",
            "",
            "| query | type | before bad top5 | after bad top5 | before risk top5 | after risk top5 | after formula ids | after primary |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in payload["comparisons"]:
        after_norm = item["after"].get("formula_normalization") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    item["query"],
                    item.get("question_type") or "",
                    str(item["before"]["top5_bad_formula_anchor_count"]),
                    str(item["after"]["top5_bad_formula_anchor_count"]),
                    str(item["before"]["top5_risk_candidate_count"]),
                    str(item["after"]["top5_risk_candidate_count"]),
                    json.dumps(after_norm.get("formula_ids") or [], ensure_ascii=False),
                    json.dumps(item["after"]["primary_record_ids"], ensure_ascii=False),
                ]
            )
            + " |"
        )

    improved = [
        item
        for item in payload["comparisons"]
        if item["before"]["top5_bad_formula_anchor_count"] > item["after"]["top5_bad_formula_anchor_count"]
    ][:5]
    lines.extend(["", "## Typical Before / After Traces", ""])
    for item in improved:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- before top5: `{json.dumps([row['record_id'] + ':' + str(row['topic_consistency']) for row in item['before']['top5_candidates']], ensure_ascii=False)}`",
                f"- after top5: `{json.dumps([row['record_id'] + ':' + str(row['topic_consistency']) for row in item['after']['top5_candidates']], ensure_ascii=False)}`",
                f"- after formula_normalization: `{json.dumps(item['after'].get('formula_normalization') or {}, ensure_ascii=False)}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    os.environ.setdefault("PERF_DISABLE_LLM", "1")
    os.environ.setdefault("TCM_RAG_LLM_ENABLED", "false")
    os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")
    os.environ.setdefault("PERF_DISABLE_RERANK", "1")

    pool = load_pool(resolve_project_path(args.pool_path))
    specs = select_queries(pool, args.limit)
    before_rows = run_pass(args, specs, formula_enabled=False)
    after_rows = run_pass(args, specs, formula_enabled=True)
    before_by_query = {row["query"]: row for row in before_rows}
    after_by_query = {row["query"]: row for row in after_rows}
    comparisons = [
        {
            **spec,
            "before": before_by_query[spec["query"]],
            "after": after_by_query[spec["query"]],
        }
        for spec in specs
    ]
    payload = {
        "generated_at_utc": now_utc(),
        "engine": args.engine,
        "runtime_env": {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "TCM_RAG_LLM_ENABLED": os.environ.get("TCM_RAG_LLM_ENABLED"),
            "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
            "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
        },
        "query_count": len(specs),
        "aggregate_before": aggregate(before_rows),
        "aggregate_after": aggregate(after_rows),
        "comparisons": comparisons,
    }

    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(build_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
