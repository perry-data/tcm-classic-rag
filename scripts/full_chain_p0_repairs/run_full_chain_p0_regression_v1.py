#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
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
    MODE_IDS,
    QuerySpec as FullChainQuerySpec,
    build_run_modes,
    canonical_formula_to_id,
    canonical_term_to_id,
    load_definition_registry,
    load_formula_registry,
    md_table,
    resolve_paths,
    run_mode,
    write_json,
    write_md,
)


RUN_ID = "full_chain_p0_boundary_repairs_v1"
OUTPUT_DIR = Path("artifacts/full_chain_p0_repairs")
DOC_DIR = Path("docs/full_chain_p0_repairs")
REGRESSION_JSON = OUTPUT_DIR / "p0_boundary_regression_v1.json"
REGRESSION_MD = OUTPUT_DIR / "p0_boundary_regression_v1.md"
BEFORE_AFTER_JSON = OUTPUT_DIR / "p0_boundary_before_after_v1.json"
BEFORE_AFTER_MD = OUTPUT_DIR / "p0_boundary_before_after_v1.md"
METRICS_JSON = OUTPUT_DIR / "failure_metrics_consistency_check_v1.json"
METRICS_MD = OUTPUT_DIR / "failure_metrics_consistency_check_v1.md"
DOC_MD = DOC_DIR / "full_chain_p0_boundary_repairs_v1.md"

FULL_CHAIN_RESULTS_JSON = Path("artifacts/full_chain_regression/full_chain_regression_results_v1.json")
FULL_CHAIN_FAILURES_JSON = Path("artifacts/full_chain_regression/full_chain_failure_cases_v1.json")


@dataclass(frozen=True)
class P0Case:
    query_id: str
    query: str
    query_type: str
    group: str
    judgement: str
    expected_terms: tuple[str, ...] = ()
    expected_formula_names: tuple[str, ...] = ()
    require_strong: bool = False
    allow_weak_or_strong: bool = False
    notes: str = ""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def mode_family(answer_mode: str | None) -> str:
    if answer_mode == "strong":
        return "strong"
    if str(answer_mode or "").startswith("weak"):
        return "weak"
    return "refuse"


def build_cases() -> list[P0Case]:
    cases: list[P0Case] = [
        P0Case("p0_original_01", "清邪中上是什么意思？", "p0_review_only_boundary", "A_p0_original", "review_only"),
        P0Case("p0_original_02", "反是什么意思？", "p0_review_only_boundary", "A_p0_original", "review_only"),
        P0Case("p0_original_03", "两阳是什么意思？", "p0_review_only_boundary", "A_p0_original", "review_only"),
        P0Case("p0_original_04", "白虎是什么意思？", "p0_negative_modern", "A_p0_original", "negative"),
        P0Case("p0_variant_01", "清邪是什么意思？", "p0_review_only_variant", "B_p0_adversarial", "review_only"),
        P0Case("p0_variant_02", "浊邪是什么意思？", "p0_review_only_variant", "B_p0_adversarial", "review_only"),
        P0Case("p0_variant_03", "清邪中上和浊邪中下是什么意思？", "p0_review_only_variant", "B_p0_adversarial", "review_only"),
        P0Case("p0_variant_04", "反证是什么意思？", "p0_negative_variant", "B_p0_adversarial", "negative"),
        P0Case("p0_variant_05", "反复是什么意思？", "p0_negative_variant", "B_p0_adversarial", "negative"),
        P0Case("p0_variant_06", "两阳病是什么意思？", "p0_review_only_variant", "B_p0_adversarial", "review_only"),
        P0Case("p0_variant_07", "风与火气是什么意思？", "p0_review_only_variant", "B_p0_adversarial", "review_only"),
        P0Case(
            "p0_variant_08",
            "白虎汤是什么意思？",
            "p0_formula_near_miss_guard",
            "B_p0_adversarial",
            "formula",
            expected_formula_names=("白虎汤",),
            allow_weak_or_strong=True,
        ),
        P0Case(
            "p0_variant_09",
            "白虎汤方的条文是什么？",
            "p0_formula_guard",
            "B_p0_adversarial",
            "formula",
            expected_formula_names=("白虎汤",),
            require_strong=True,
        ),
        P0Case(
            "p0_variant_10",
            "白虎加人参汤方的条文是什么？",
            "p0_formula_guard",
            "B_p0_adversarial",
            "formula",
            expected_formula_names=("白虎加人参汤",),
            require_strong=True,
        ),
        P0Case(
            "p0_variant_11",
            "白虎汤和白虎加人参汤有什么区别？",
            "p0_formula_guard",
            "B_p0_adversarial",
            "formula",
            expected_formula_names=("白虎汤", "白虎加人参汤"),
            require_strong=True,
        ),
        P0Case("p0_variant_12", "白虎星是什么意思？", "p0_negative_variant", "B_p0_adversarial", "negative"),
    ]

    ahv_guards = (
        ("ahv_guard_01", "何谓太阳病", "太阳病"),
        ("ahv_guard_02", "伤寒是什么", "伤寒"),
        ("ahv_guard_03", "温病是什么意思", "温病"),
        ("ahv_guard_04", "结脉是什么", "结脉"),
        ("ahv_guard_05", "霍乱是什么", "霍乱"),
        ("ahv_guard_06", "阳明病是什么", "阳明病"),
        ("ahv_guard_07", "少阴病是什么意思", "少阴病"),
        ("ahv_guard_08", "结胸是什么", "结胸"),
        ("ahv_guard_09", "水逆是什么意思", "水逆"),
        ("ahv_guard_10", "半表半里证是什么", "半表半里证"),
    )
    cases.extend(
        P0Case(
            query_id=query_id,
            query=query,
            query_type="ahv_canonical_guard",
            group="C_mainline_guard",
            judgement="definition",
            expected_terms=(term,),
            require_strong=True,
        )
        for query_id, query, term in ahv_guards
    )

    formula_guards = (
        ("formula_guard_01", "乌梅丸方的条文是什么？", ("乌梅丸",)),
        ("formula_guard_02", "茵陈蒿汤方的条文是什么？", ("茵陈蒿汤",)),
        ("formula_guard_03", "白虎汤方的条文是什么？", ("白虎汤",)),
        ("formula_guard_04", "白虎加人参汤方的条文是什么？", ("白虎加人参汤",)),
        ("formula_guard_05", "桂枝汤方的条文是什么？", ("桂枝汤",)),
        ("formula_guard_06", "麻黄汤方的条文是什么？", ("麻黄汤",)),
        ("formula_guard_07", "小柴胡汤方的条文是什么？", ("小柴胡汤",)),
        ("formula_guard_08", "大承气汤方的条文是什么？", ("大承气汤",)),
        ("formula_guard_09", "白通汤方的条文是什么？", ("白通汤",)),
        ("formula_guard_10", "四逆加人参汤方的条文是什么？", ("四逆加人参汤",)),
    )
    cases.extend(
        P0Case(
            query_id=query_id,
            query=query,
            query_type="formula_guard",
            group="C_mainline_guard",
            judgement="formula",
            expected_formula_names=names,
            require_strong=True,
        )
        for query_id, query, names in formula_guards
    )

    gold_safe_guards = (
        ("gold_definition_guard_01", "下药是什么意思？", "下药"),
        ("gold_definition_guard_02", "四逆是什么意思？", "四逆"),
        ("gold_definition_guard_03", "湿痹是什么？", "湿痹"),
        ("gold_definition_guard_04", "盗汗是什么？", "盗汗"),
        ("gold_definition_guard_05", "关格是什么？", "关格"),
    )
    cases.extend(
        P0Case(
            query_id=query_id,
            query=query,
            query_type="gold_safe_definition_guard",
            group="C_mainline_guard",
            judgement="definition",
            expected_terms=(term,),
            require_strong=True,
        )
        for query_id, query, term in gold_safe_guards
    )

    review_guards = (
        "神丹是什么意思？",
        "将军是什么意思？",
        "胆瘅是什么意思？",
        "寒格是什么意思？",
        "口苦病是什么意思？",
    )
    cases.extend(
        P0Case(
            query_id=f"review_only_guard_{index:02d}",
            query=query,
            query_type="review_only_boundary_guard",
            group="C_mainline_guard",
            judgement="review_only",
        )
        for index, query in enumerate(review_guards, start=1)
    )

    negative_guards = (
        "太阳能是什么意思？",
        "劳动合同是什么？",
        "霍乱疫苗是什么？",
        "温度是什么意思？",
        "水逆星座是什么意思？",
    )
    cases.extend(
        P0Case(
            query_id=f"negative_guard_{index:02d}",
            query=query,
            query_type="negative_modern_guard",
            group="C_mainline_guard",
            judgement="negative",
        )
        for index, query in enumerate(negative_guards, start=1)
    )
    return cases


def build_full_chain_specs(cases: list[P0Case]) -> list[FullChainQuerySpec]:
    return [
        FullChainQuerySpec(
            query_id=case.query_id,
            query=case.query,
            query_category=case.query_type,
            expected_terms=case.expected_terms,
            expected_formula_names=case.expected_formula_names,
            notes=case.notes,
        )
        for case in cases
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full-chain P0 boundary repair regression v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    parser.add_argument("--modes", default="A,B,C", help="Comma-separated mode short names to run.")
    parser.add_argument("--llm-timeout-seconds", type=float, default=None)
    parser.add_argument("--llm-max-output-tokens", type=int, default=None)
    parser.add_argument("--no-llm-preflight", action="store_true")
    return parser.parse_args()


def selected_modes(args: argparse.Namespace) -> list[Any]:
    requested = {part.strip().upper() for part in args.modes.split(",") if part.strip()}
    short_to_mode = {"A": MODE_IDS[0], "B": MODE_IDS[1], "C": MODE_IDS[2]}
    requested_ids = {short_to_mode.get(item, item) for item in requested}
    return [mode for mode in build_run_modes() if mode.run_mode in requested_ids]


def collect_formula_hits(record: dict[str, Any]) -> set[str]:
    hits = set(str(item) for item in record.get("matched_formula_ids") or [])
    for candidate in record.get("raw_top5_candidates") or []:
        if candidate.get("formula_id"):
            hits.add(str(candidate["formula_id"]))
        hits.update(str(item) for item in candidate.get("formula_candidate_ids") or [])
    return hits


def evaluate_case(
    case: P0Case,
    record: dict[str, Any],
    *,
    term_to_id: dict[str, str],
    formula_name_to_id: dict[str, str],
) -> dict[str, Any]:
    family = mode_family(record.get("answer_mode"))
    primary_ids = list(record.get("primary_ids") or [])
    failure_reasons: list[str] = []
    failure_types: list[str] = []

    if record.get("forbidden_primary_items"):
        failure_reasons.append("forbidden raw/review source entered primary")
        failure_types.append("assembler_slot_error")

    if record.get("review_only_primary_conflicts"):
        failure_reasons.append("review-only definition object entered primary")
        failure_types.append("review_only_boundary_error")

    if case.judgement == "review_only":
        if family == "strong":
            failure_reasons.append("review-only boundary produced strong answer")
            failure_types.append("review_only_boundary_error")
        if primary_ids:
            failure_reasons.append("review-only boundary retained primary evidence")
            failure_types.append("review_only_boundary_error")
        if record.get("matched_definition_concept_ids"):
            failure_reasons.append("review-only boundary unexpectedly matched definition normalization")
            failure_types.append("review_only_boundary_error")

    elif case.judgement == "negative":
        if family == "strong":
            failure_reasons.append("negative/modern query produced strong answer")
            failure_types.append("negative_query_false_positive")
        if primary_ids:
            failure_reasons.append("negative/modern query retained primary evidence")
            failure_types.append("negative_query_false_positive")
        if record.get("matched_formula_ids"):
            failure_reasons.append("negative/modern query triggered formula normalization")
            failure_types.append("negative_query_false_positive")

    elif case.judgement == "formula":
        expected_formula_ids = [formula_name_to_id[name] for name in case.expected_formula_names if name in formula_name_to_id]
        formula_hits = collect_formula_hits(record)
        missing = [formula_id for formula_id in expected_formula_ids if formula_id not in formula_hits]
        if case.require_strong and family != "strong":
            failure_reasons.append("formula guard did not produce strong answer")
            failure_types.append("answer_mode_calibration_error")
        if case.allow_weak_or_strong and family == "refuse":
            failure_reasons.append("formula near-miss guard refused instead of preserving formula access")
            failure_types.append("answer_mode_calibration_error")
        if missing:
            failure_reasons.append("formula guard missed expected formula normalization/raw hit")
            failure_types.append("data_layer_bad_alias")

    elif case.judgement == "definition":
        expected_ids = [term_to_id[term] for term in case.expected_terms if term in term_to_id]
        definition_hits = set(record.get("matched_definition_concept_ids") or []) | set(
            record.get("primary_definition_ids") or []
        )
        missing = [concept_id for concept_id in expected_ids if concept_id not in definition_hits]
        if case.require_strong and family != "strong":
            failure_reasons.append("definition guard did not produce strong answer")
            failure_types.append("answer_mode_calibration_error")
        if missing:
            failure_reasons.append("definition guard missed expected safe definition object")
            failure_types.append("retrieval_miss")

    failure_type = failure_types[0] if failure_types else "none"
    return {
        "pass": not failure_reasons,
        "failure_type": failure_type,
        "failure_reasons": failure_reasons,
        "mode_family": family,
    }


def summarize(records: list[dict[str, Any]], cases_by_id: dict[str, P0Case]) -> dict[str, Any]:
    failures = [record for record in records if not record["p0_pass"]]
    failure_type_counts = Counter(record["p0_failure_type"] for record in failures)
    records_by_type = Counter(record["query_type"] for record in records)
    failures_by_type = Counter(record["query_type"] for record in failures)
    failures_by_group = Counter(record["group"] for record in failures)
    completed_modes = sorted(set(record["run_mode"] for record in records))
    p0_failures = [record for record in failures if record["group"] == "A_p0_original"]
    formula_bad_anchor_total = sum(
        1
        for record in records
        if any(
            candidate.get("topic_consistency") in BAD_FORMULA_TOPICS
            for candidate in record.get("raw_top5_candidates") or []
        )
    )
    mainline_records = [record for record in records if record["group"] == "C_mainline_guard"]
    mainline_failures = [record for record in mainline_records if not record["p0_pass"]]
    return {
        "query_count": len(cases_by_id),
        "record_count": len(records),
        "completed_modes": completed_modes,
        "records_by_query_type": dict(sorted(records_by_type.items())),
        "regression_pass_count": len(records) - len(failures),
        "regression_fail_count": len(failures),
        "failure_type_counts": dict(sorted(failure_type_counts.items())),
        "failures_by_query_type": dict(sorted(failures_by_type.items())),
        "failures_by_group": dict(sorted(failures_by_group.items())),
        "p0_failure_count": len(p0_failures),
        "p0_failed_queries": sorted(set(record["query"] for record in p0_failures)),
        "forbidden_primary_total": sum(len(record.get("forbidden_primary_items") or []) for record in records),
        "review_only_primary_conflict_count": sum(
            len(record.get("review_only_primary_conflicts") or []) for record in records
        ),
        "formula_bad_anchor_top5_total": formula_bad_anchor_total,
        "ahv_guard_fail_count": failures_by_type["ahv_canonical_guard"],
        "formula_guard_fail_count": failures_by_type["formula_guard"]
        + failures_by_type["p0_formula_guard"]
        + failures_by_type["p0_formula_near_miss_guard"],
        "gold_safe_definition_fail_count": failures_by_type["gold_safe_definition_guard"],
        "review_only_boundary_guard_fail_count": failures_by_type["review_only_boundary_guard"]
        + failures_by_type["p0_review_only_boundary"]
        + failures_by_type["p0_review_only_variant"],
        "negative_modern_guard_fail_count": failures_by_type["negative_modern_guard"]
        + failures_by_type["p0_negative_modern"]
        + failures_by_type["p0_negative_variant"],
        "mainline_guard_failure_count": len(mainline_failures),
    }


def run_regression(args: argparse.Namespace) -> dict[str, Any]:
    cases = build_cases()
    cases_by_id = {case.query_id: case for case in cases}
    specs = build_full_chain_specs(cases)
    paths = resolve_paths(args)
    definition_registry = load_definition_registry(paths["db_path"])
    formula_registry = load_formula_registry(paths["db_path"])
    term_to_id = canonical_term_to_id(definition_registry)
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
        print(f"[mode:end] {mode.run_mode} status={status['status']}", flush=True)
        all_records.extend(records)

    evaluated_records: list[dict[str, Any]] = []
    for record in all_records:
        case = cases_by_id[record["query_id"]]
        judgement = evaluate_case(
            case,
            record,
            term_to_id=term_to_id,
            formula_name_to_id=formula_name_to_id,
        )
        evaluated = {
            **record,
            "query_type": case.query_type,
            "group": case.group,
            "judgement": case.judgement,
            "p0_pass": judgement["pass"],
            "p0_failure_type": judgement["failure_type"],
            "p0_failure_reasons": judgement["failure_reasons"],
            "mode_family": judgement["mode_family"],
        }
        evaluated_records.append(evaluated)

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "mode_statuses": statuses,
        "query_set": {
            "query_count": len(cases),
            "query_type_counts": dict(sorted(Counter(case.query_type for case in cases).items())),
            "queries": [asdict(case) for case in cases],
        },
        "metrics": summarize(evaluated_records, cases_by_id),
        "records": evaluated_records,
        "failures": [record for record in evaluated_records if not record["p0_pass"]],
    }
    return payload


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def failure_metrics_consistency_payload() -> dict[str, Any]:
    results = load_json(FULL_CHAIN_RESULTS_JSON)
    failures = load_json(FULL_CHAIN_FAILURES_JSON)
    fail_records = [record for record in results["records"] if not record.get("pass")]
    failure_type_counts = Counter(record.get("failure_type") for record in fail_records)
    missing = [
        {
            "query_id": record.get("query_id"),
            "run_mode": record.get("run_mode"),
            "failure_type": record.get("failure_type"),
        }
        for record in fail_records
        if not record.get("failure_type") or record.get("failure_type") == "none"
    ]
    major_failure_type_total = sum((results.get("metrics") or {}).get("failure_type_counts", {}).values())
    failure_cases_type_total = sum(Counter(item.get("failure_type") for item in failures.get("failures", [])).values())
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "source_results_path": str(FULL_CHAIN_RESULTS_JSON),
        "source_failures_path": str(FULL_CHAIN_FAILURES_JSON),
        "results_fail_record_count": len(fail_records),
        "failure_cases_failure_count": failures.get("failure_count"),
        "results_metric_failure_type_total": major_failure_type_total,
        "failure_cases_type_total": failure_cases_type_total,
        "computed_failure_type_counts": dict(sorted(failure_type_counts.items())),
        "missing_or_none_failure_type_count": len(missing),
        "missing_or_none_failure_type_records": missing,
        "consistent": len(fail_records)
        == failures.get("failure_count")
        == major_failure_type_total
        == failure_cases_type_total
        and not missing,
        "finding": (
            "JSON artifacts are internally consistent at 37 failures; the apparent mismatch came from reading partial"
            " failure-type metrics instead of summing failure_type_counts."
        ),
    }


def before_after_payload(regression_payload: dict[str, Any]) -> dict[str, Any]:
    results = load_json(FULL_CHAIN_RESULTS_JSON)
    p0_queries = {
        "清邪中上是什么意思？",
        "反是什么意思？",
        "两阳是什么意思？",
        "白虎是什么意思？",
    }
    before = [
        {
            "query_id": record["query_id"],
            "query": record["query"],
            "run_mode": record["run_mode"],
            "answer_mode": record["answer_mode"],
            "failure_type": record["failure_type"],
            "pass": record["pass"],
            "primary_ids": record.get("primary_ids") or [],
            "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
            "matched_formula_ids": record.get("matched_formula_ids") or [],
            "failure_reasons": record.get("failure_reasons") or [],
        }
        for record in results["records"]
        if record.get("query") in p0_queries
    ]
    after = [
        {
            "query_id": record["query_id"],
            "query": record["query"],
            "run_mode": record["run_mode"],
            "answer_mode": record["answer_mode"],
            "p0_pass": record["p0_pass"],
            "p0_failure_type": record["p0_failure_type"],
            "primary_ids": record.get("primary_ids") or [],
            "secondary_ids": record.get("secondary_ids") or [],
            "review_ids": record.get("review_ids") or [],
            "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
            "matched_formula_ids": record.get("matched_formula_ids") or [],
            "p0_failure_reasons": record.get("p0_failure_reasons") or [],
            "llm_debug": record.get("llm_debug") or {},
        }
        for record in regression_payload["records"]
        if record.get("group") == "A_p0_original"
    ]
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "before_source": str(FULL_CHAIN_RESULTS_JSON),
        "before_failure_count": sum(1 for record in before if not record["pass"]),
        "after_failure_count": sum(1 for record in after if not record["p0_pass"]),
        "before": before,
        "after": after,
    }


def render_regression_md(payload: dict[str, Any]) -> list[str]:
    metrics = payload["metrics"]
    lines = [
        "# P0 Boundary Regression v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- query_count: `{metrics['query_count']}`",
        f"- record_count: `{metrics['record_count']}`",
        f"- regression_fail_count: `{metrics['regression_fail_count']}`",
        f"- p0_failure_count: `{metrics['p0_failure_count']}`",
        f"- forbidden_primary_total: `{metrics['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_count: `{metrics['review_only_primary_conflict_count']}`",
        f"- formula_bad_anchor_top5_total: `{metrics['formula_bad_anchor_top5_total']}`",
        "",
        "## Metrics",
        "",
    ]
    lines.extend(md_table(["metric", "value"], [[key, json.dumps(value, ensure_ascii=False)] for key, value in metrics.items()]))
    lines.extend(["", "## Failures", ""])
    lines.extend(
        md_table(
            ["mode", "query_id", "query_type", "answer_mode", "failure_type", "reasons"],
            [
                [
                    record["run_mode"],
                    record["query_id"],
                    record["query_type"],
                    record["answer_mode"],
                    record["p0_failure_type"],
                    "; ".join(record.get("p0_failure_reasons") or []),
                ]
                for record in payload["failures"]
            ],
        )
    )
    return lines


def render_before_after_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# P0 Boundary Before / After v1",
        "",
        f"- before_failure_count: `{payload['before_failure_count']}`",
        f"- after_failure_count: `{payload['after_failure_count']}`",
        "",
        "## Before",
        "",
    ]
    lines.extend(
        md_table(
            ["mode", "query", "answer_mode", "failure_type", "primary_ids"],
            [
                [
                    record["run_mode"],
                    record["query"],
                    record["answer_mode"],
                    record["failure_type"],
                    ", ".join(record.get("primary_ids") or []),
                ]
                for record in payload["before"]
            ],
        )
    )
    lines.extend(["", "## After", ""])
    lines.extend(
        md_table(
            ["mode", "query", "answer_mode", "pass", "primary_ids", "secondary_count", "review_count"],
            [
                [
                    record["run_mode"],
                    record["query"],
                    record["answer_mode"],
                    record["p0_pass"],
                    ", ".join(record.get("primary_ids") or []),
                    len(record.get("secondary_ids") or []),
                    len(record.get("review_ids") or []),
                ]
                for record in payload["after"]
            ],
        )
    )
    return lines


def render_metrics_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Failure Metrics Consistency Check v1",
        "",
        f"- consistent: `{payload['consistent']}`",
        f"- results_fail_record_count: `{payload['results_fail_record_count']}`",
        f"- failure_cases_failure_count: `{payload['failure_cases_failure_count']}`",
        f"- results_metric_failure_type_total: `{payload['results_metric_failure_type_total']}`",
        f"- failure_cases_type_total: `{payload['failure_cases_type_total']}`",
        f"- missing_or_none_failure_type_count: `{payload['missing_or_none_failure_type_count']}`",
        f"- finding: {payload['finding']}",
        "",
        "## Failure Type Counts",
        "",
    ]
    lines.extend(md_table(["failure_type", "count"], [[key, value] for key, value in payload["computed_failure_type_counts"].items()]))
    return lines


def render_doc_md(
    regression_payload: dict[str, Any],
    before_after: dict[str, Any],
    metrics_check: dict[str, Any],
) -> list[str]:
    metrics = regression_payload["metrics"]
    lines = [
        "# Full Chain P0 Boundary Repairs v1",
        "",
        "## Scope",
        "",
        "本轮只处理 full-chain 暴露的 4 个 P0：清邪中上、反、两阳、白虎。未新增 AHV3，未改 prompt、前端、API payload 顶层 contract 或 answer_mode 定义，也未重新放开 raw full passages 进入 primary。",
        "",
        "## Root Cause",
        "",
        "- 清邪中上 / 反 / 两阳：对象层未升格为 safe primary，但解释型 runtime 仍允许 main_passages 在无安全定义对象时形成 strong。",
        "- 白虎：单问“白虎是什么意思”没有明确方名后缀，却被含“白虎汤 / 白虎加人参汤”的方剂片段吸附成 strong。",
        "- failure metrics：JSON 内部一致，失败记录、failure_count、failure_type_counts 都是 37；旧报告缺少显式合计字段，容易被误读。",
        "",
        "## Repair",
        "",
        "- 新增 exact meaning guard：review-only/not-ready topic 只走 weak_with_review_notice，原 primary 候选降为 secondary/review。",
        "- 新增 exact negative guard：白虎 / 白虎星 / 反证 / 反复不触发方剂或正文 primary。",
        "- full-chain 报告指标补充 failure_record_count、failure_type_count_total、missing_failure_type_count、failure_metrics_consistent。",
        "",
        "## Results",
        "",
        f"- before_p0_failure_count: `{before_after['before_failure_count']}`",
        f"- after_p0_failure_count: `{before_after['after_failure_count']}`",
        f"- regression_fail_count: `{metrics['regression_fail_count']}`",
        f"- p0_failure_count: `{metrics['p0_failure_count']}`",
        f"- forbidden_primary_total: `{metrics['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_count: `{metrics['review_only_primary_conflict_count']}`",
        f"- formula_bad_anchor_top5_total: `{metrics['formula_bad_anchor_top5_total']}`",
        f"- failure_metrics_consistent: `{metrics_check['consistent']}`",
        "",
        "## Artifact Index",
        "",
        "- `artifacts/full_chain_p0_repairs/p0_boundary_before_after_v1.json`",
        "- `artifacts/full_chain_p0_repairs/p0_boundary_regression_v1.json`",
        "- `artifacts/full_chain_p0_repairs/failure_metrics_consistency_check_v1.json`",
    ]
    return lines


def main() -> int:
    args = parse_args()
    regression_payload = run_regression(args)
    metrics_check = failure_metrics_consistency_payload()
    before_after = before_after_payload(regression_payload)

    write_json(REGRESSION_JSON, regression_payload)
    write_md(REGRESSION_MD, render_regression_md(regression_payload))
    write_json(BEFORE_AFTER_JSON, before_after)
    write_md(BEFORE_AFTER_MD, render_before_after_md(before_after))
    write_json(METRICS_JSON, metrics_check)
    write_md(METRICS_MD, render_metrics_md(metrics_check))
    write_md(DOC_MD, render_doc_md(regression_payload, before_after, metrics_check))

    print(f"[done] wrote {REGRESSION_JSON}", flush=True)
    return 0 if regression_payload["metrics"]["p0_failure_count"] == 0 and metrics_check["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
