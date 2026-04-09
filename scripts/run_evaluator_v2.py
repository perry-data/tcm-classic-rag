#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
)
from backend.retrieval.hybrid import DENSE_CHUNK_TOP_K, DENSE_MAIN_TOP_K  # noqa: E402
from backend.retrieval.minimal import compact_text  # noqa: E402
from backend.strategies.general_question import detect_general_question  # noqa: E402
from run_evaluator_v1 import (  # noqa: E402
    DEFAULT_API_URL,
    ApiRunner,
    LocalAssemblerRunner,
    bool_mark,
    command_line,
    evaluate_item as evaluate_item_v1,
    json_dumps,
    load_goldset,
    log,
    passage_id_from_record_id,
    resolve_project_path,
    summarize_results,
    unique_preserve_order,
)


DEFAULT_GOLDSET_PATH = "artifacts/evaluation/goldset_v2_working_150.json"
DEFAULT_REPORT_JSON_PATH = "artifacts/evaluation/evaluator_v2_report.json"
DEFAULT_REPORT_MD_PATH = "artifacts/evaluation/evaluator_v2_report.md"
RUNNER_VERSION = "evaluator_runner_v2_skeleton"
TOP_K_VALUES = (1, 3, 5, 10)
FAILURE_CATEGORY_ORDER = (
    "retrieval_failure",
    "citation_failure",
    "answer_mode_failure",
    "evidence_layering_failure",
    "unsupported_assertion_failure",
    "answer_text_quality_issue",
    "llm_runtime_issue",
    "latency_issue",
)
FAILURE_SUBCATEGORY_ORDER = (
    "gold_miss_in_fused_topk",
    "gold_miss_after_rerank",
    "citation_not_in_gold",
    "expected_weak_but_actual_strong",
    "expected_refuse_but_not_refuse",
    "mode_mismatch_other",
    "primary_should_be_empty",
    "evidence_should_be_zero",
    "citations_should_be_zero",
    "strong_without_gold_evidence",
    "clarity_low",
    "structure_low",
    "evidence_faithfulness_low",
    "mode_boundary_broken",
    "llm_fallback_triggered",
    "llm_validator_reject",
    "latency_over_threshold",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay goldset_v2_working_150.json against the current formal answer chain with retrieval metrics.",
    )
    parser.add_argument("--goldset", default=DEFAULT_GOLDSET_PATH, help="Path to goldset v2 JSON.")
    parser.add_argument("--report-json", default=DEFAULT_REPORT_JSON_PATH, help="Output evaluator JSON report path.")
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD_PATH, help="Output evaluator Markdown report path.")
    parser.add_argument(
        "--runner-backend",
        choices=("local_assembler", "api"),
        default="local_assembler",
        help="Replay through local AnswerAssembler by default, or an already-running formal API endpoint.",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="POST endpoint used when --runner-backend=api.")
    parser.add_argument(
        "--fail-on-evaluation-failure",
        action="store_true",
        help="Return a non-zero exit code when any enforced evaluator check fails.",
    )
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH, help="Path to layered enablement policy JSON.")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    return parser.parse_args()


class EvaluatorV2Runner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.payload_runner: LocalAssemblerRunner | ApiRunner
        self.metrics_runner: LocalAssemblerRunner
        if args.runner_backend == "api":
            self.payload_runner = ApiRunner(args.api_url)
            self.metrics_runner = LocalAssemblerRunner(args)
        else:
            self.metrics_runner = LocalAssemblerRunner(args)
            self.payload_runner = self.metrics_runner

    def answer(self, query: str) -> dict[str, Any]:
        return self.payload_runner.answer(query)

    @property
    def metrics_assembler(self) -> Any:
        return self.metrics_runner.assembler

    def close(self) -> None:
        self.payload_runner.close()
        if self.metrics_runner is not self.payload_runner:
            self.metrics_runner.close()


def match_strategy_for_item(item: dict[str, Any]) -> str:
    return item.get("retrieval_assertions", {}).get("match_strategy", "either")


def minimum_gold_hits_for_item(item: dict[str, Any]) -> int:
    return int(item.get("retrieval_assertions", {}).get("minimum_gold_hits", 0))


def item_requires_retrieval_hit(item: dict[str, Any]) -> bool:
    if minimum_gold_hits_for_item(item) > 0:
        return True
    return bool(item.get("gold_record_ids") or item.get("gold_passage_ids"))


def record_matches_gold(item: dict[str, Any], record_id: str | None) -> bool:
    if not record_id:
        return False
    gold_record_ids = set(item.get("gold_record_ids", []))
    gold_passage_ids = set(item.get("gold_passage_ids", []))
    match_strategy = match_strategy_for_item(item)
    passage_id = passage_id_from_record_id(record_id)

    if match_strategy == "exact_record_id":
        return record_id in gold_record_ids
    if match_strategy == "canonical_passage_id":
        return passage_id in gold_passage_ids
    return record_id in gold_record_ids or passage_id in gold_passage_ids


def build_attempt_plan(assembler: Any, query_text: str) -> dict[str, Any]:
    policy_refusal = assembler._detect_policy_refusal(query_text)
    if policy_refusal is not None:
        return {
            "path_type": "policy_refusal",
            "notes": policy_refusal,
            "attempts": [],
        }

    comparison_plan = assembler._detect_comparison_query(query_text)
    if comparison_plan is not None:
        if not comparison_plan["valid"]:
            return {
                "path_type": "comparison_refuse",
                "notes": comparison_plan["reason"],
                "attempts": [],
            }
        return {
            "path_type": "comparison",
            "notes": comparison_plan["query_kind"],
            "attempts": [
                {
                    "label": f"comparison_{entity['group_label']}",
                    "query_text": entity["canonical_name"],
                }
                for entity in comparison_plan["entities"]
            ],
        }

    general_plan = detect_general_question(query_text)
    if general_plan is not None:
        attempts = [
            {
                "label": "general_query",
                "query_text": query_text,
            }
        ]
        if compact_text(query_text) != general_plan.normalized_topic:
            attempts.append(
                {
                    "label": "general_topic",
                    "query_text": general_plan.topic_text,
                }
            )
        return {
            "path_type": "general",
            "notes": general_plan.general_kind,
            "attempts": attempts,
        }

    return {
        "path_type": "standard",
        "notes": None,
        "attempts": [
            {
                "label": "standard_query",
                "query_text": query_text,
            }
        ],
    }


def collect_stage_candidates(engine: Any, query_text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    request = engine.build_request(query_text)
    sparse_candidates = engine._collect_sparse_candidates(request)
    dense_chunk_candidates = engine._collect_dense_candidates(
        request,
        index=engine.dense_chunks_index,
        meta=engine.dense_chunks_meta,
        top_k=DENSE_CHUNK_TOP_K,
        stage_name="dense_chunks",
    )
    dense_main_candidates = engine._collect_dense_candidates(
        request,
        index=engine.dense_main_index,
        meta=engine.dense_main_meta,
        top_k=DENSE_MAIN_TOP_K,
        stage_name="dense_main_passages",
    )
    fused_candidates = engine._fuse_candidates(
        ("sparse", sparse_candidates),
        ("dense_chunks", dense_chunk_candidates),
        ("dense_main_passages", dense_main_candidates),
    )
    reranked_candidates = engine._rerank_candidates(request, fused_candidates)
    return fused_candidates, reranked_candidates


def first_gold_rank(candidates: list[dict[str, Any]], item: dict[str, Any]) -> int | None:
    for index, candidate in enumerate(candidates, start=1):
        if record_matches_gold(item, candidate.get("record_id")):
            return index
    return None


def top_ids(candidates: list[dict[str, Any]], limit: int) -> list[str]:
    return [candidate["record_id"] for candidate in candidates[:limit] if candidate.get("record_id")]


def build_hit_map(best_ranks: list[int | None]) -> dict[str, bool]:
    hit_map: dict[str, bool] = {}
    for top_k in TOP_K_VALUES:
        hit_map[str(top_k)] = any(rank is not None and rank <= top_k for rank in best_ranks)
    return hit_map


def collect_retrieval_metrics(assembler: Any, item: dict[str, Any]) -> dict[str, Any]:
    attempt_plan = build_attempt_plan(assembler, item["query"])
    attempts_summary: list[dict[str, Any]] = []
    fused_best_ranks: list[int | None] = []
    rerank_best_ranks: list[int | None] = []

    for attempt in attempt_plan["attempts"]:
        fused_candidates, reranked_candidates = collect_stage_candidates(assembler.engine, attempt["query_text"])
        fused_rank = first_gold_rank(fused_candidates, item)
        rerank_rank = first_gold_rank(reranked_candidates, item)
        fused_best_ranks.append(fused_rank)
        rerank_best_ranks.append(rerank_rank)
        attempts_summary.append(
            {
                "label": attempt["label"],
                "query_text": attempt["query_text"],
                "fused_top_record_ids": top_ids(fused_candidates, limit=max(TOP_K_VALUES)),
                "rerank_top_record_ids": top_ids(reranked_candidates, limit=max(TOP_K_VALUES)),
                "best_gold_rank_before_rerank": fused_rank,
                "best_gold_rank_after_rerank": rerank_rank,
            }
        )

    available_fused_ranks = [rank for rank in fused_best_ranks if rank is not None]
    available_rerank_ranks = [rank for rank in rerank_best_ranks if rank is not None]
    best_before = min(available_fused_ranks) if available_fused_ranks else None
    best_after = min(available_rerank_ranks) if available_rerank_ranks else None
    rerank_rank_delta = None if best_before is None or best_after is None else best_after - best_before

    return {
        "path_type": attempt_plan["path_type"],
        "path_notes": attempt_plan["notes"],
        "attempt_count": len(attempts_summary),
        "top_k_values": list(TOP_K_VALUES),
        "asserted_top_k_targets": list(item.get("retrieval_assertions", {}).get("top_k_targets", [])),
        "match_strategy": match_strategy_for_item(item),
        "minimum_gold_hits": minimum_gold_hits_for_item(item),
        "fused_hit_at_k": build_hit_map(fused_best_ranks),
        "rerank_hit_at_k": build_hit_map(rerank_best_ranks),
        "best_gold_rank_before_rerank": best_before,
        "best_gold_rank_after_rerank": best_after,
        "rerank_rank_delta": rerank_rank_delta,
        "attempts": attempts_summary,
    }


def empty_failure_counters(keys: tuple[str, ...]) -> dict[str, int]:
    return {key: 0 for key in keys}


def mode_failure_subcategory(expected_mode: str, actual_mode: str | None) -> str:
    if expected_mode == "weak_with_review_notice" and actual_mode == "strong":
        return "expected_weak_but_actual_strong"
    if expected_mode == "refuse" and actual_mode != "refuse":
        return "expected_refuse_but_not_refuse"
    return "mode_mismatch_other"


def classify_failure_taxonomy(result: dict[str, Any], item: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    retrieval_metrics = result["retrieval_metrics"]
    max_top_k = str(max(TOP_K_VALUES))

    if item_requires_retrieval_hit(item):
        if not retrieval_metrics["fused_hit_at_k"][max_top_k]:
            entries.append(
                {
                    "category": "retrieval_failure",
                    "subcategory": "gold_miss_in_fused_topk",
                    "severity": "error",
                    "notes": f"Gold evidence not found in fused top {max_top_k}.",
                }
            )
        if not retrieval_metrics["rerank_hit_at_k"][max_top_k]:
            entries.append(
                {
                    "category": "retrieval_failure",
                    "subcategory": "gold_miss_after_rerank",
                    "severity": "error",
                    "notes": f"Gold evidence not found after rerank within top {max_top_k}.",
                }
            )

    if not result["gold_citation_check"]["passed"]:
        entries.append(
            {
                "category": "citation_failure",
                "subcategory": "citation_not_in_gold",
                "severity": "error",
                "notes": "Citations did not match gold record_id or canonical passage_id.",
            }
        )

    if not result["mode_match"]:
        entries.append(
            {
                "category": "answer_mode_failure",
                "subcategory": mode_failure_subcategory(result["expected_mode"], result["actual_mode"]),
                "severity": "error",
                "notes": "Actual answer_mode does not match expected_mode.",
            }
        )

    if not result["primary_empty_check"]["passed"]:
        entries.append(
            {
                "category": "evidence_layering_failure",
                "subcategory": "primary_should_be_empty",
                "severity": "error",
                "notes": "primary_evidence should remain empty for this sample.",
            }
        )

    if not result["zero_evidence_check"]["passed"]:
        entries.append(
            {
                "category": "evidence_layering_failure",
                "subcategory": "evidence_should_be_zero",
                "severity": "error",
                "notes": "Evidence slots should remain empty for this sample.",
            }
        )

    if not result["zero_citations_check"]["passed"]:
        entries.append(
            {
                "category": "evidence_layering_failure",
                "subcategory": "citations_should_be_zero",
                "severity": "error",
                "notes": "Citation list should remain empty for this sample.",
            }
        )

    for reason in result["unsupported_assertion_check"]["failure_reasons"]:
        if reason == "strong_without_gold_evidence":
            subcategory = "strong_without_gold_evidence"
        elif reason == "expected_weak_but_actual_mode_strong":
            subcategory = "expected_weak_but_actual_strong"
        elif reason == "expected_refuse_but_actual_mode_not_refuse":
            subcategory = "expected_refuse_but_not_refuse"
        elif reason == "primary_evidence_should_be_empty":
            subcategory = "primary_should_be_empty"
        elif reason == "evidence_should_be_zero":
            subcategory = "evidence_should_be_zero"
        elif reason == "citations_should_be_zero":
            subcategory = "citations_should_be_zero"
        else:
            subcategory = "mode_boundary_broken"
        entries.append(
            {
                "category": "unsupported_assertion_failure",
                "subcategory": subcategory,
                "severity": "error",
                "notes": reason,
            }
        )

    return entries


def evaluate_item_v2(item: dict[str, Any], payload: dict[str, Any], assembler: Any) -> dict[str, Any]:
    result = evaluate_item_v1(item, payload)
    retrieval_metrics = collect_retrieval_metrics(assembler, item)
    failure_taxonomy = classify_failure_taxonomy({**result, "retrieval_metrics": retrieval_metrics}, item)
    result["retrieval_metrics"] = retrieval_metrics
    result["failure_taxonomy"] = failure_taxonomy
    return result


def hit_summary(results: list[dict[str, Any]], field_name: str) -> dict[str, dict[str, float | int]]:
    evaluable = [result for result in results if item_requires_retrieval_hit(result["source_item"])]
    denominator = len(evaluable)
    summary: dict[str, dict[str, float | int]] = {}
    for top_k in TOP_K_VALUES:
        hit_count = sum(1 for result in evaluable if result["retrieval_metrics"][field_name][str(top_k)])
        summary[str(top_k)] = {
            "hit_count": hit_count,
            "hit_rate": round(hit_count / denominator, 4) if denominator else 0.0,
        }
    return summary


def hit_summary_by_type(results: list[dict[str, Any]], field_name: str) -> dict[str, dict[str, Any]]:
    by_type: dict[str, dict[str, Any]] = {}
    question_types = sorted({result["question_type"] for result in results})
    for question_type in question_types:
        typed = [result for result in results if result["question_type"] == question_type]
        evaluable = [result for result in typed if item_requires_retrieval_hit(result["source_item"])]
        denominator = len(evaluable)
        hit_map: dict[str, dict[str, float | int]] = {}
        for top_k in TOP_K_VALUES:
            hit_count = sum(1 for result in evaluable if result["retrieval_metrics"][field_name][str(top_k)])
            hit_map[str(top_k)] = {
                "hit_count": hit_count,
                "hit_rate": round(hit_count / denominator, 4) if denominator else 0.0,
            }
        by_type[question_type] = {
            "count": len(typed),
            field_name: hit_map,
        }
    return by_type


def build_retrieval_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_type_fused = hit_summary_by_type(results, "fused_hit_at_k")
    by_type_rerank = hit_summary_by_type(results, "rerank_hit_at_k")
    question_types = sorted(by_type_fused)
    by_type: dict[str, dict[str, Any]] = {}
    for question_type in question_types:
        by_type[question_type] = {
            "count": by_type_fused[question_type]["count"],
            "fused_hit_at_k": by_type_fused[question_type]["fused_hit_at_k"],
            "rerank_hit_at_k": by_type_rerank[question_type]["rerank_hit_at_k"],
        }

    comparable = [
        result["retrieval_metrics"]["rerank_rank_delta"]
        for result in results
        if result["retrieval_metrics"]["best_gold_rank_before_rerank"] is not None
        and result["retrieval_metrics"]["best_gold_rank_after_rerank"] is not None
    ]
    return {
        "top_k_values": list(TOP_K_VALUES),
        "aggregate": {
            "fused_hit_at_k": hit_summary(results, "fused_hit_at_k"),
            "rerank_hit_at_k": hit_summary(results, "rerank_hit_at_k"),
        },
        "by_question_type": by_type,
        "rerank_delta_summary": {
            "count_with_gold_before_rerank": len(comparable),
            "improved_count": sum(1 for delta in comparable if delta < 0),
            "unchanged_count": sum(1 for delta in comparable if delta == 0),
            "worsened_count": sum(1 for delta in comparable if delta > 0),
        },
    }


def build_failure_taxonomy_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter()
    subcategory_counts = Counter()
    items_with_failures = 0
    for result in results:
        entries = result["failure_taxonomy"]
        if entries:
            items_with_failures += 1
        for entry in entries:
            category_counts[entry["category"]] += 1
            subcategory_counts[entry["subcategory"]] += 1

    normalized_categories = empty_failure_counters(FAILURE_CATEGORY_ORDER)
    normalized_categories.update({key: category_counts.get(key, 0) for key in FAILURE_CATEGORY_ORDER})
    normalized_subcategories = empty_failure_counters(FAILURE_SUBCATEGORY_ORDER)
    normalized_subcategories.update({key: subcategory_counts.get(key, 0) for key in FAILURE_SUBCATEGORY_ORDER})
    return {
        "category_counts": normalized_categories,
        "subcategory_counts": normalized_subcategories,
        "items_with_failures": items_with_failures,
        "artifact_path": "docs/evaluation/evaluation_failure_taxonomy_v1.md",
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    base_summary = summarize_results(results)
    return {
        "total_questions": base_summary["total_questions"],
        "mode_match_count": base_summary["mode_match_count"],
        "citation_basic_pass_count": base_summary["citation_check_required"]["basic_pass_count"],
        "failure_count": base_summary["failure_count"],
        "all_checks_passed": base_summary["all_checks_passed"],
    }


def build_report(
    goldset: dict[str, Any],
    results: list[dict[str, Any]],
    args: argparse.Namespace,
    started_at_utc: str,
    finished_at_utc: str,
) -> dict[str, Any]:
    for result, item in zip(results, goldset["items"], strict=False):
        result["source_item"] = item

    report = {
        "schema_version": "evaluator_v2_metric_schema_draft",
        "generated_at_utc": finished_at_utc,
        "report_kind": "evaluator_v2_report",
        "run_metadata": {
            "runner_version": RUNNER_VERSION,
            "runner_backend": args.runner_backend,
            "command": command_line(),
            "notes": (
                "v2 skeleton keeps v1 enforced checks, adds retrieval diagnostics and failure taxonomy, "
                "and does not yet include answer_text review or latency benchmark artifacts."
            ),
        },
        "dataset": {
            "path": str(resolve_project_path(args.goldset)),
            "schema_version": goldset.get("schema_version"),
            "dataset_name": goldset.get("dataset_name"),
            "dataset_stage": goldset.get("dataset_stage"),
            "total_questions": len(results),
        },
        "summary": build_summary(results),
        "retrieval_metrics": build_retrieval_summary(results),
        "answer_text_quality_review": None,
        "latency_benchmark": None,
        "failure_taxonomy": build_failure_taxonomy_summary(results),
        "artifacts": {
            "json_report_path": str(resolve_project_path(args.report_json)),
            "markdown_report_path": str(resolve_project_path(args.report_md)),
        },
        "items": [
            {key: value for key, value in result.items() if key != "source_item"}
            for result in results
        ],
    }
    return report


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    retrieval = report["retrieval_metrics"]
    taxonomy = report["failure_taxonomy"]
    lines = [
        "# Evaluator v2 Report",
        "",
        "## 运行信息",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- runner_version: `{report['run_metadata']['runner_version']}`",
        f"- runner_backend: `{report['run_metadata']['runner_backend']}`",
        f"- goldset: `{report['dataset']['path']}`",
        f"- command: `{report['run_metadata']['command']}`",
        f"- notes: {report['run_metadata']['notes']}",
        "",
        "## 汇总",
        "",
        f"- total_questions: `{summary['total_questions']}`",
        f"- mode_match_count: `{summary['mode_match_count']}/{summary['total_questions']}`",
        f"- citation_basic_pass_count: `{summary['citation_basic_pass_count']}`",
        f"- failure_count: `{summary['failure_count']}`",
        f"- all_checks_passed: `{summary['all_checks_passed']}`",
        "",
        "## Retrieval Metrics",
        "",
        f"- top_k_values: `{json.dumps(retrieval['top_k_values'], ensure_ascii=False)}`",
        "",
        "### Aggregate",
        "",
        "| metric | K | hit_count | hit_rate |",
        "| --- | ---: | ---: | ---: |",
    ]

    for stage_name in ("fused_hit_at_k", "rerank_hit_at_k"):
        for top_k in retrieval["top_k_values"]:
            stats = retrieval["aggregate"][stage_name][str(top_k)]
            lines.append(
                f"| `{stage_name}` | {top_k} | {stats['hit_count']} | {stats['hit_rate']} |"
            )

    lines.extend(
        [
            "",
            "### By Question Type",
            "",
            "| question_type | total | fused@1 | fused@3 | fused@5 | fused@10 | rerank@1 | rerank@3 | rerank@5 | rerank@10 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for question_type, typed in retrieval["by_question_type"].items():
        lines.append(
            f"| `{question_type}` | {typed['count']} | "
            f"{typed['fused_hit_at_k']['1']['hit_count']} ({typed['fused_hit_at_k']['1']['hit_rate']}) | "
            f"{typed['fused_hit_at_k']['3']['hit_count']} ({typed['fused_hit_at_k']['3']['hit_rate']}) | "
            f"{typed['fused_hit_at_k']['5']['hit_count']} ({typed['fused_hit_at_k']['5']['hit_rate']}) | "
            f"{typed['fused_hit_at_k']['10']['hit_count']} ({typed['fused_hit_at_k']['10']['hit_rate']}) | "
            f"{typed['rerank_hit_at_k']['1']['hit_count']} ({typed['rerank_hit_at_k']['1']['hit_rate']}) | "
            f"{typed['rerank_hit_at_k']['3']['hit_count']} ({typed['rerank_hit_at_k']['3']['hit_rate']}) | "
            f"{typed['rerank_hit_at_k']['5']['hit_count']} ({typed['rerank_hit_at_k']['5']['hit_rate']}) | "
            f"{typed['rerank_hit_at_k']['10']['hit_count']} ({typed['rerank_hit_at_k']['10']['hit_rate']}) |"
        )

    delta = retrieval["rerank_delta_summary"]
    lines.extend(
        [
            "",
            "### Rerank Delta",
            "",
            f"- count_with_gold_before_rerank: `{delta['count_with_gold_before_rerank']}`",
            f"- improved_count: `{delta['improved_count']}`",
            f"- unchanged_count: `{delta['unchanged_count']}`",
            f"- worsened_count: `{delta['worsened_count']}`",
            "",
            "## Failure Taxonomy",
            "",
            f"- items_with_failures: `{taxonomy['items_with_failures']}`",
            "",
            "### Category Counts",
            "",
            "| category | count |",
            "| --- | ---: |",
        ]
    )

    for category, count in taxonomy["category_counts"].items():
        lines.append(f"| `{category}` | {count} |")

    lines.extend(["", "### Subcategory Counts", "", "| subcategory | count |", "| --- | ---: |"])
    for subcategory, count in taxonomy["subcategory_counts"].items():
        lines.append(f"| `{subcategory}` | {count} |")

    lines.extend(
        [
            "",
            "## 逐题结果",
            "",
            "| question_id | type | expected | actual | mode | citations | fused_rank | rerank_rank | delta | taxonomy |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for result in report["items"]:
        retrieval_metrics = result["retrieval_metrics"]
        lines.append(
            f"| `{result['question_id']}` | `{result['question_type']}` | `{result['expected_mode']}` | "
            f"`{result['actual_mode']}` | {bool_mark(result['mode_match'])} | "
            f"{result['actual_counts']['citations']} | "
            f"{retrieval_metrics['best_gold_rank_before_rerank'] if retrieval_metrics['best_gold_rank_before_rerank'] is not None else '-'} | "
            f"{retrieval_metrics['best_gold_rank_after_rerank'] if retrieval_metrics['best_gold_rank_after_rerank'] is not None else '-'} | "
            f"{retrieval_metrics['rerank_rank_delta'] if retrieval_metrics['rerank_rank_delta'] is not None else '-'} | "
            f"{len(result['failure_taxonomy'])} |"
        )

    lines.extend(["", "## 失败样本", ""])
    failed_items = [result for result in report["items"] if result["failure_taxonomy"]]
    if not failed_items:
        lines.append("_No failed taxonomy items._")
    else:
        for result in failed_items:
            lines.extend(
                [
                    f"### {result['question_id']}",
                    "",
                    f"- query: {result['query']}",
                    f"- question_type: `{result['question_type']}`",
                    f"- failed_checks: `{json.dumps(result['failed_checks'], ensure_ascii=False)}`",
                    f"- failure_taxonomy: `{json.dumps(result['failure_taxonomy'], ensure_ascii=False)}`",
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "## Scope Notes",
            "",
            "- 本轮 v2 skeleton 保留了 v1 的 mode / citation / unsupported assertion 检查。",
            "- 本轮已接入 retrieval 指标字段与 failure taxonomy 字段。",
            "- `answer_text_quality_review` 与 `latency_benchmark` 仍为后续轮次范围，本报告中未实际填充。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_evaluator(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    goldset_path = resolve_project_path(args.goldset)
    goldset = load_goldset(goldset_path)
    started_at_utc = datetime.now(timezone.utc).isoformat()
    runner = EvaluatorV2Runner(args)
    results: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(goldset["items"], start=1):
            log(f"[evaluator:v2] replay {index}/{len(goldset['items'])}: {item['question_id']}")
            payload = runner.answer(item["query"])
            results.append(evaluate_item_v2(item, payload, runner.metrics_assembler))
    finally:
        runner.close()

    finished_at_utc = datetime.now(timezone.utc).isoformat()
    report = build_report(goldset, results, args, started_at_utc, finished_at_utc)
    return report, build_markdown(report)


def main() -> int:
    args = parse_args()
    report_json_path = resolve_project_path(args.report_json)
    report_md_path = resolve_project_path(args.report_md)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)

    report, markdown = run_evaluator(args)
    report_json_path.write_text(json_dumps(report) + "\n", encoding="utf-8")
    report_md_path.write_text(markdown, encoding="utf-8")
    log(f"[evaluator:v2] wrote {report_json_path}")
    log(f"[evaluator:v2] wrote {report_md_path}")

    if args.fail_on_evaluation_failure and not report["summary"]["all_checks_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
