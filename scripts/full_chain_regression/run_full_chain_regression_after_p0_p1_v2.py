#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.full_chain_regression.run_full_chain_production_like_regression_v1 import (  # noqa: E402
    BAD_FORMULA_TOPICS,
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    build_query_specs,
    build_repair_queue,
    build_run_modes,
    canonical_formula_to_id,
    load_definition_registry,
    load_formula_registry,
    mark_cross_mode_rerank_regressions,
    md_table,
    recommend_next_action,
    resolve_paths,
    run_mode,
    summarize_metrics,
    write_json,
    write_md,
)


RUN_ID = "full_chain_regression_after_p0_p1_v2"
OUTPUT_DIR = Path("artifacts/full_chain_regression")
DOC_DIR = Path("docs/full_chain_regression")
V1_RESULTS_JSON = OUTPUT_DIR / "full_chain_regression_results_v1.json"
V1_FAILURES_JSON = OUTPUT_DIR / "full_chain_failure_cases_v1.json"
P0_REGRESSION_JSON = Path("artifacts/full_chain_p0_repairs/p0_boundary_regression_v1.json")
P1_REGRESSION_JSON = Path("artifacts/full_chain_p1_repairs/p1_regression_v1.json")
RESULTS_JSON = OUTPUT_DIR / "full_chain_regression_results_v2.json"
FAILURES_JSON = OUTPUT_DIR / "full_chain_failure_cases_v2.json"
DELTA_JSON = OUTPUT_DIR / "full_chain_v1_vs_v2_delta.json"
RESIDUAL_QUEUE_JSON = OUTPUT_DIR / "residual_repair_queue_after_p0_p1_v2.json"
DOC_MD = DOC_DIR / "full_chain_regression_after_p0_p1_v2.md"

P0_GUARD_QUERIES = {
    "review_only_boundary_08": "清邪中上是什么意思？",
    "review_only_boundary_10": "反是什么意思？",
    "review_only_boundary_04": "两阳是什么意思？",
    "negative_modern_09": "白虎是什么意思？",
}
P1_GUARD_QUERIES = {
    "formula_07": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
    "formula_18": "麻黄汤方和桂枝汤方的区别是什么？",
    "learner_short_21": "干呕是什么意思？",
}
MODE_IDS = (
    "A_data_plane_baseline",
    "B_retrieval_rerank",
    "C_production_like_full_chain",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full-chain regression v2 after P0/P1 repairs.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    parser.add_argument("--modes", default="A,B,C")
    parser.add_argument("--llm-timeout-seconds", type=float, default=None)
    parser.add_argument("--llm-max-output-tokens", type=int, default=None)
    parser.add_argument("--no-llm-preflight", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_modes(args: argparse.Namespace) -> list[Any]:
    requested = {part.strip().upper() for part in args.modes.split(",") if part.strip()}
    short_to_id = {"A": MODE_IDS[0], "B": MODE_IDS[1], "C": MODE_IDS[2]}
    requested_ids = {short_to_id.get(item, item) for item in requested}
    return [mode for mode in build_run_modes() if mode.run_mode in requested_ids]


def enrich_records(records: list[dict[str, Any]]) -> None:
    for record in records:
        llm_debug = record.get("llm_debug") or {}
        record["llm_answer_source"] = llm_debug.get("answer_source")


def wrong_definition_primary(record: dict[str, Any]) -> bool:
    if record.get("query_category") not in {"ahv_v1_canonical", "ahv2_canonical"}:
        return False
    expected = set(record.get("expected_concept_ids") or [])
    primary = set(record.get("primary_definition_ids") or [])
    return bool(expected and primary and not (expected & primary))


def formula_bad_anchor_top5_count(record: dict[str, Any]) -> int:
    return sum(
        1
        for row in record.get("raw_top5_candidates") or []
        if row.get("primary_allowed") and row.get("topic_consistency") in BAD_FORMULA_TOPICS
    )


def build_guard_summary(records: list[dict[str, Any]], guard_queries: dict[str, str]) -> dict[str, Any]:
    by_query_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_query_id[record["query_id"]].append(record)

    queries: dict[str, Any] = {}
    for query_id, query in guard_queries.items():
        query_records = sorted(by_query_id.get(query_id, []), key=lambda item: item["run_mode"])
        queries[query_id] = {
            "query": query,
            "covered_mode_count": len(query_records),
            "covered_modes": [record["run_mode"] for record in query_records],
            "pass_all_modes": len(query_records) == 3 and all(record.get("pass") for record in query_records),
            "records": [
                {
                    "run_mode": record["run_mode"],
                    "pass": record["pass"],
                    "answer_mode": record["answer_mode"],
                    "failure_type": record["failure_type"],
                    "primary_ids": record.get("primary_ids") or [],
                    "matched_formula_ids": record.get("matched_formula_ids") or [],
                    "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
                    "llm_used": record.get("llm_used"),
                    "llm_answer_source": record.get("llm_answer_source"),
                }
                for record in query_records
            ],
        }
    return {
        "query_count": len(guard_queries),
        "pass": all(item["pass_all_modes"] for item in queries.values()),
        "queries": queries,
    }


def build_mode_result(records: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    mode_records = [record for record in records if record["run_mode"] == mode]
    failures = [record for record in mode_records if not record.get("pass")]
    return {
        "total": len(mode_records),
        "passed": len(mode_records) - len(failures),
        "failed": len(failures),
        "status": "pass" if not failures else "fail",
    }


def build_results_payload(
    specs: list[Any],
    records: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
) -> dict[str, Any]:
    repair_queue = build_repair_queue(records)
    metrics = summarize_metrics(specs, records, statuses, repair_queue)
    metrics["wrong_definition_primary_total"] = sum(1 for record in records if wrong_definition_primary(record))
    metrics["formula_bad_anchor_top5_total"] = sum(formula_bad_anchor_top5_count(record) for record in records)
    metrics["forbidden_primary_total"] = sum(len(record.get("forbidden_primary_items") or []) for record in records)
    metrics["review_only_primary_conflict_total"] = sum(
        len(record.get("review_only_primary_conflicts") or []) for record in records
    )
    failures = [record for record in records if not record.get("pass")]
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "source_query_set": "artifacts/full_chain_regression/full_chain_query_set_v1.json",
        "query_count": len(specs),
        "record_count": len(records),
        "passed_cases": len(records) - len(failures),
        "failed_cases": len(failures),
        "mode_statuses": statuses,
        "mode_A_result": build_mode_result(records, MODE_IDS[0]),
        "mode_B_result": build_mode_result(records, MODE_IDS[1]),
        "mode_C_result": build_mode_result(records, MODE_IDS[2]),
        "metrics": metrics,
        "p0_guard_summary": build_guard_summary(records, P0_GUARD_QUERIES),
        "p1_guard_summary": build_guard_summary(records, P1_GUARD_QUERIES),
        "records": records,
    }


def slim_failure(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_id": record["query_id"],
        "query": record["query"],
        "query_category": record["query_category"],
        "run_mode": record["run_mode"],
        "answer_mode": record["answer_mode"],
        "primary_ids": record.get("primary_ids") or [],
        "secondary_ids": record.get("secondary_ids") or [],
        "review_ids": record.get("review_ids") or [],
        "matched_formula_ids": record.get("matched_formula_ids") or [],
        "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
        "forbidden_primary_items": record.get("forbidden_primary_items") or [],
        "review_only_primary_conflicts": record.get("review_only_primary_conflicts") or [],
        "citation_judgement": record.get("citation_judgement"),
        "faithfulness_judgement": record.get("faithfulness_judgement"),
        "mode_judgement": record.get("mode_judgement"),
        "failure_type": record.get("failure_type"),
        "failure_reasons": record.get("failure_reasons") or [],
        "pass": record.get("pass"),
        "llm_used": record.get("llm_used"),
        "llm_answer_source": record.get("llm_answer_source"),
        "recommended_next_action": recommend_next_action(record),
    }


def build_failure_payload(results: dict[str, Any]) -> dict[str, Any]:
    failures = [slim_failure(record) for record in results["records"] if not record.get("pass")]
    failure_type_counts = Counter(item["failure_type"] for item in failures)
    failures_by_mode = Counter(item["run_mode"] for item in failures)
    failures_by_query_category = Counter(item["query_category"] for item in failures)
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "failure_count": len(failures),
        "failure_type_counts": dict(sorted(failure_type_counts.items())),
        "failures_by_mode": dict(sorted(failures_by_mode.items())),
        "failures_by_query_category": dict(sorted(failures_by_query_category.items())),
        "per_failure_record": failures,
        "suggested_next_action": (
            "Use residual_repair_queue_after_p0_p1_v2.json as the P2/P3 queue; do not change acceptance rules in this run."
            if failures
            else "No residual failures in v2; keep this artifact as the post-P0/P1 baseline."
        ),
    }


def failure_key(record: dict[str, Any]) -> tuple[str, str]:
    return str(record["query_id"]), str(record["run_mode"])


def build_guard_delta(
    v1_records: list[dict[str, Any]],
    v2_records: list[dict[str, Any]],
    guard_queries: dict[str, str],
) -> dict[str, Any]:
    v1_by_key = {failure_key(record): record for record in v1_records if record["query_id"] in guard_queries}
    v2_by_key = {failure_key(record): record for record in v2_records if record["query_id"] in guard_queries}
    rows: list[dict[str, Any]] = []
    for query_id, query in guard_queries.items():
        for mode in MODE_IDS:
            before = v1_by_key.get((query_id, mode))
            after = v2_by_key.get((query_id, mode))
            rows.append(
                {
                    "query_id": query_id,
                    "query": query,
                    "run_mode": mode,
                    "v1_pass": None if before is None else before.get("pass"),
                    "v1_failure_type": None if before is None else before.get("failure_type"),
                    "v2_pass": None if after is None else after.get("pass"),
                    "v2_failure_type": None if after is None else after.get("failure_type"),
                    "fixed": bool(before is not None and not before.get("pass") and after is not None and after.get("pass")),
                }
            )
    return {
        "guard_query_count": len(guard_queries),
        "v1_failed_cases": sum(1 for row in rows if row["v1_pass"] is False),
        "v2_failed_cases": sum(1 for row in rows if row["v2_pass"] is False),
        "all_v2_pass": all(row["v2_pass"] is True for row in rows),
        "records": rows,
    }


def build_delta_payload(results: dict[str, Any]) -> dict[str, Any]:
    v1 = load_json(V1_RESULTS_JSON)
    v1_records = v1["records"]
    v2_records = results["records"]
    v1_failed = {failure_key(record): record for record in v1_records if not record.get("pass")}
    v2_failed = {failure_key(record): record for record in v2_records if not record.get("pass")}
    fixed_keys = sorted(set(v1_failed) - set(v2_failed))
    persistent_keys = sorted(set(v1_failed) & set(v2_failed))
    new_keys = sorted(set(v2_failed) - set(v1_failed))
    v1_type_counts = Counter(record["failure_type"] for record in v1_failed.values())
    v2_type_counts = Counter(record["failure_type"] for record in v2_failed.values())
    all_types = sorted(set(v1_type_counts) | set(v2_type_counts))

    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "comparison_key": ["query_id", "run_mode"],
        "v1_total_failures": len(v1_failed),
        "v2_total_failures": len(v2_failed),
        "fixed_failures": [
            {
                "query_id": query_id,
                "run_mode": run_mode,
                "query": v1_failed[(query_id, run_mode)]["query"],
                "v1_failure_type": v1_failed[(query_id, run_mode)]["failure_type"],
                "v1_failure_reasons": v1_failed[(query_id, run_mode)].get("failure_reasons") or [],
            }
            for query_id, run_mode in fixed_keys
        ],
        "persistent_failures": [
            {
                "query_id": query_id,
                "run_mode": run_mode,
                "query": v2_failed[(query_id, run_mode)]["query"],
                "v1_failure_type": v1_failed[(query_id, run_mode)]["failure_type"],
                "v2_failure_type": v2_failed[(query_id, run_mode)]["failure_type"],
                "v2_failure_reasons": v2_failed[(query_id, run_mode)].get("failure_reasons") or [],
            }
            for query_id, run_mode in persistent_keys
        ],
        "new_failures": [
            {
                "query_id": query_id,
                "run_mode": run_mode,
                "query": v2_failed[(query_id, run_mode)]["query"],
                "v2_failure_type": v2_failed[(query_id, run_mode)]["failure_type"],
                "v2_failure_reasons": v2_failed[(query_id, run_mode)].get("failure_reasons") or [],
            }
            for query_id, run_mode in new_keys
        ],
        "p0_delta": build_guard_delta(v1_records, v2_records, P0_GUARD_QUERIES),
        "p1_delta": build_guard_delta(v1_records, v2_records, P1_GUARD_QUERIES),
        "failure_type_delta": {
            failure_type: {
                "v1": v1_type_counts.get(failure_type, 0),
                "v2": v2_type_counts.get(failure_type, 0),
                "delta": v2_type_counts.get(failure_type, 0) - v1_type_counts.get(failure_type, 0),
            }
            for failure_type in all_types
        },
        "notes": [
            "v2 reused the 120-query full_chain_query_set_v1 query set and reran A/B/C modes.",
            "Fixed/persistent/new are computed by query_id + run_mode, not by relaxed failure criteria.",
            "P0/P1 deltas are guard coverage summaries; no P2 repair is applied in this run.",
        ],
    }


def grouped_residual_failures(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.get("pass"):
            continue
        entry = grouped.setdefault(
            record["query_id"],
            {
                "query_id": record["query_id"],
                "query": record["query"],
                "query_category": record["query_category"],
                "failure_types": [],
                "run_modes": [],
                "failure_reasons": [],
                "recommended_next_action": recommend_next_action(record),
                "primary_ids": record.get("primary_ids") or [],
                "matched_formula_ids": record.get("matched_formula_ids") or [],
                "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
                "suitable_for_thesis_limitations_and_future_work": True,
            },
        )
        if record["failure_type"] not in entry["failure_types"]:
            entry["failure_types"].append(record["failure_type"])
        entry["run_modes"].append(record["run_mode"])
        for reason in record.get("failure_reasons") or []:
            if reason not in entry["failure_reasons"]:
                entry["failure_reasons"].append(reason)
    return sorted(grouped.values(), key=lambda item: (item["query_category"], item["query_id"]))


def build_residual_queue_payload(results: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    residuals = grouped_residual_failures(results["records"])
    failure_types = Counter(
        failure_type
        for item in residuals
        for failure_type in item["failure_types"]
    )
    p3_observations = [
        {
            "observation": "Post-P0/P1 residuals remain bounded to the listed P2 candidate queue.",
            "failure_type_counts": dict(sorted(failure_types.items())),
            "recommended_next_action": "Use these as separate future repair rounds or summarize them in the thesis limitations section.",
            "suitable_for_thesis_limitations_and_future_work": True,
        }
    ] if residuals else []
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "source_results": str(RESULTS_JSON),
        "source_delta": str(DELTA_JSON),
        "P2_candidates": residuals,
        "P3_observations": p3_observations,
        "new_failure_count": len(delta["new_failures"]),
        "recommended_next_action": (
            "Continue with a scoped P2 repair round if product correctness is prioritized; otherwise this is usable as a thesis testing baseline with residual limitations documented."
            if residuals
            else "No residual repair queue remains after P0/P1; proceed to thesis test-result整理."
        ),
        "notes": [
            "This queue is descriptive only; no AHV3, definition object, alias, learner normalization, prompt, frontend, or API changes were made.",
            "Raw full passages, ambiguous passages, review-only, and risk-only materials remain prohibited from primary evidence.",
        ],
    }


def render_doc_md(
    results: dict[str, Any],
    failures: dict[str, Any],
    delta: dict[str, Any],
    residual_queue: dict[str, Any],
) -> list[str]:
    metrics = results["metrics"]
    status_rows = [
        [
            status["run_mode"],
            status["status"],
            status.get("production_like"),
            (status.get("llm_preflight") or {}).get("llm_used"),
            status.get("unavailable_reason") or "",
        ]
        for status in results["mode_statuses"]
    ]
    lines = [
        "# Full Chain Regression After P0/P1 v2",
        "",
        "## 本轮目标",
        "",
        "在 P0 boundary repairs 和 P1 minimal repairs 完成后，复用完整 120 条 full-chain query set，重新运行 A/B/C 三种模式，生成新的系统级回归基线。本轮只做验证与归档，不做 AHV3、不新增 definition object、不修 P2、不改 prompt、不改前端、不改 API contract。",
        "",
        "## 与 v1 的区别",
        "",
        "- v1 是 P0/P1 修复前的 full_chain_production_like_regression_v1 基线。",
        "- v2 使用当前代码库、当前 artifacts/zjshl_v1.db，以及 P0/P1 修复后的运行时行为重新跑同一 120-query set。",
        "- v2 额外显式归档 P0 四个原始 query 与 P1 三个 query 的 guard 状态，并生成 v1-v2 delta 与剩余 P2/P3 队列。",
        "",
        "## A / B / C 运行情况",
        "",
    ]
    lines.extend(md_table(["mode", "status", "production_like", "llm_preflight_used", "reason"], status_rows))
    lines.extend(
        [
            "",
            "## 总体结果",
            "",
            f"- query_count: `{results['query_count']}`",
            f"- record_count: `{results['record_count']}`",
            f"- pass_count: `{results['passed_cases']}`",
            f"- fail_count: `{results['failed_cases']}`",
            f"- v1_total_failures: `{delta['v1_total_failures']}`",
            f"- v2_total_failures: `{delta['v2_total_failures']}`",
            f"- fixed_failures: `{len(delta['fixed_failures'])}`",
            f"- persistent_failures: `{len(delta['persistent_failures'])}`",
            f"- new_failures: `{len(delta['new_failures'])}`",
            "",
            "## Failure Type 统计",
            "",
        ]
    )
    lines.extend(
        md_table(
            ["failure_type", "count"],
            [[key, value] for key, value in failures["failure_type_counts"].items()],
        )
    )
    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            f"- forbidden_primary_total: `{metrics['forbidden_primary_total']}`",
            f"- review_only_primary_conflict_total: `{metrics['review_only_primary_conflict_total']}`",
            f"- wrong_definition_primary_total: `{metrics['wrong_definition_primary_total']}`",
            f"- formula_bad_anchor_top5_total: `{metrics['formula_bad_anchor_top5_total']}`",
            "",
            "## P0 / P1 Guard 状态",
            "",
            f"- P0 四个原始 query 仍通过: `{results['p0_guard_summary']['pass']}`",
            f"- P1 三个 query 仍通过: `{results['p1_guard_summary']['pass']}`",
            f"- P0 v1_failed_cases -> v2_failed_cases: `{delta['p0_delta']['v1_failed_cases']} -> {delta['p0_delta']['v2_failed_cases']}`",
            f"- P1 v1_failed_cases -> v2_failed_cases: `{delta['p1_delta']['v1_failed_cases']} -> {delta['p1_delta']['v2_failed_cases']}`",
            "",
            "## 新失败与剩余队列",
            "",
            f"- 是否有新失败: `{bool(delta['new_failures'])}`",
            f"- P2 candidates: `{len(residual_queue['P2_candidates'])}`",
            f"- P3 observations: `{len(residual_queue['P3_observations'])}`",
            "",
            "## 论文测试结果整理判断",
            "",
        ]
    )
    can_enter_thesis = (
        results["p0_guard_summary"]["pass"]
        and results["p1_guard_summary"]["pass"]
        and metrics["forbidden_primary_total"] == 0
        and metrics["review_only_primary_conflict_total"] == 0
        and metrics["wrong_definition_primary_total"] == 0
        and metrics["formula_bad_anchor_top5_total"] == 0
        and not delta["new_failures"]
        and results["mode_C_result"]["total"] == results["query_count"]
    )
    lines.extend(
        [
            f"- 是否可以进入论文第 4 章测试结果整理: `{can_enter_thesis}`",
            "- 建议：v2 已可作为 P0/P1 后的系统级测试基线；若要继续提升系统正确性，下一轮再单独处理 residual P2 queue。论文写作可基于本基线整理整体测试结果，并把剩余失败作为系统不足与展望。",
        ]
    )
    return lines


def main() -> None:
    args = parse_args()
    paths = resolve_paths(args)
    specs = build_query_specs()
    definition_registry = load_definition_registry(paths["db_path"])
    formula_registry = load_formula_registry(paths["db_path"])
    formula_name_to_id = canonical_formula_to_id(formula_registry)

    all_records: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    for mode in selected_modes(args):
        print(f"[mode:start] {mode.run_mode}", flush=True)
        records, status = run_mode(
            args=args,
            paths=paths,
            mode=mode,
            specs=specs,
            definition_registry=definition_registry,
            formula_name_to_id=formula_name_to_id,
        )
        statuses.append(status)
        all_records.extend(records)
        print(f"[mode:end] {mode.run_mode} status={status['status']}", flush=True)

    enrich_records(all_records)
    mark_cross_mode_rerank_regressions(all_records)
    results = build_results_payload(specs, all_records, statuses)
    failures = build_failure_payload(results)
    delta = build_delta_payload(results)
    residual_queue = build_residual_queue_payload(results, delta)

    write_json(RESULTS_JSON, results)
    write_json(FAILURES_JSON, failures)
    write_json(DELTA_JSON, delta)
    write_json(RESIDUAL_QUEUE_JSON, residual_queue)
    write_md(DOC_MD, render_doc_md(results, failures, delta, residual_queue))
    print(f"[done] wrote {RESULTS_JSON}, {FAILURES_JSON}, {DELTA_JSON}, {RESIDUAL_QUEUE_JSON}, {DOC_MD}")


if __name__ == "__main__":
    main()
