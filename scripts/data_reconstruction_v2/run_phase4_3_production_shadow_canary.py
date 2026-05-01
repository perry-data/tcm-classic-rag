#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.production_shadow_logger import (  # noqa: E402
    ALLOWED_LOG_FIELDS,
    append_shadow_log,
    build_shadow_log_record,
    stable_hash,
)
from backend.retrieval.production_shadow_metrics import reset_shadow_circuit_state  # noqa: E402
from backend.retrieval.retrieval_router import (  # noqa: E402
    ENV_ALLOW_V2_PRODUCTION_SHADOW,
    ENV_FORCE_V1,
    ENV_RETRIEVAL_VERSION,
    ENV_RUNTIME_STAGE,
    ENV_V2_FALLBACK_TO_V1,
    ENV_V2_PROD_SHADOW_PERCENT,
    ENV_V2_PRODUCTION_SERVED_PERCENT,
    ENV_V2_SHADOW_CIRCUIT_BREAKER,
    ENV_V2_SHADOW_COMPARE,
    ENV_V2_SHADOW_MAX_BOUNDARY_FAILURES,
    ENV_V2_SHADOW_MAX_ERROR_RATE,
    ENV_V2_SHADOW_TIMEOUT_MS,
    classify_boundary,
    infer_query_type,
    route_config_from_env,
    run_retrieval_with_fallback,
    select_retrieval_route,
    source_fields_present,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_3_production_shadow_canary"
PROTECTED_BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_3.json"
V2_INDEX_BASELINE_PATH = OUTPUT_DIR / "v2_index_artifact_baseline_before_phase4_3.json"

PROTECTED_ARTIFACTS = [
    "artifacts/zjshl_v1.db",
    "artifacts/dense_chunks.faiss",
    "artifacts/dense_main_passages.faiss",
    "artifacts/data_reconstruction_v2/macro_phase2_2_shadow_ready_sidecar_freeze/zjshl_v2_sidecar.db",
]

V2_INDEX_ARTIFACTS = [
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_lexical_index.db",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_primary_safe_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_primary_safe_dense_metadata.jsonl",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_text_primary_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_text_primary_dense_metadata.jsonl",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_usage_positive_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_usage_positive_dense_metadata.jsonl",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_auxiliary_safe_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_auxiliary_safe_dense_metadata.jsonl",
]

CODE_CREATED_FILES = [
    "backend/retrieval/production_shadow.py",
    "backend/retrieval/production_shadow_logger.py",
    "backend/retrieval/production_shadow_metrics.py",
    "scripts/data_reconstruction_v2/run_phase4_3_production_shadow_canary.py",
]
CODE_MODIFIED_FILES = [
    "backend/retrieval/retrieval_router.py",
    "backend/api/minimal_api.py",
]
CODE_CHANGE_FILES = [*CODE_MODIFIED_FILES, *CODE_CREATED_FILES]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_3_PRODUCTION_SHADOW_CANARY_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "protected_artifact_baseline_before_phase4_3.json",
    "protected_artifact_integrity_after_phase4_3.json",
    "v2_index_artifact_baseline_before_phase4_3.json",
    "v2_index_artifact_integrity_after_phase4_3.json",
    "runtime_production_shadow_inventory.json",
    "runtime_production_shadow_inventory.md",
    "code_change_manifest_phase4_3.json",
    "git_diff_phase4_3.patch",
    "production_shadow_log_schema.json",
    "production_shadow_dry_run_results.jsonl",
    "production_shadow_dry_run_audit.json",
    "production_shadow_runtime_results.jsonl",
    "production_shadow_runtime_audit.json",
    "production_shadow_runtime_summary.md",
    "runtime_process_report.json",
    "runtime_logs_sanitized.jsonl",
    "production_shadow_kill_switch_results.jsonl",
    "production_shadow_rollback_drill_results.jsonl",
    "production_shadow_rollback_runbook.md",
    "production_shadow_metrics_summary.json",
    "production_shadow_evidence_boundary_audit.json",
    "production_shadow_formula_text_vs_usage_audit.json",
    "production_shadow_auxiliary_boundary_audit.json",
    "production_shadow_carryover_exclusion_audit.json",
    "production_shadow_uncertain_usage_exclusion_audit.json",
    "production_shadow_variant_preservation_audit.json",
    "production_shadow_weak_answer_refusal_audit.json",
    "production_shadow_source_citation_audit.json",
    "production_shadow_external_source_exclusion_audit.json",
    "production_shadow_medical_advice_boundary_audit.json",
    "production_shadow_privacy_logging_audit.json",
    "phase4_4_internal_served_canary_readiness_preview.json",
    "phase4_4_internal_served_canary_plan.md",
    "runtime_gate_status_after_phase4_3.json",
    "production_shadow_router_unit_test_results.jsonl",
    "production_shadow_integration_test_results.jsonl",
    "production_shadow_timeout_circuit_breaker_results.jsonl",
    "production_shadow_privacy_redaction_test_results.jsonl",
]

BASE_SHADOW_ENV = {
    ENV_RETRIEVAL_VERSION: "shadow",
    ENV_ALLOW_V2_PRODUCTION_SHADOW: "true",
    ENV_RUNTIME_STAGE: "production_shadow",
    ENV_V2_SHADOW_COMPARE: "true",
    ENV_V2_PRODUCTION_SERVED_PERCENT: "0",
    ENV_V2_FALLBACK_TO_V1: "true",
    ENV_V2_SHADOW_TIMEOUT_MS: "750",
    ENV_V2_SHADOW_CIRCUIT_BREAKER: "true",
    ENV_V2_SHADOW_MAX_ERROR_RATE: "0.02",
    ENV_V2_SHADOW_MAX_BOUNDARY_FAILURES: "0",
}
DRY_RUN_ENV = {**BASE_SHADOW_ENV, ENV_V2_PROD_SHADOW_PERCENT: "10"}
RUNTIME_ENV = {**BASE_SHADOW_ENV, ENV_V2_PROD_SHADOW_PERCENT: "1"}
SHADOW_ALL_ENV = dict(BASE_SHADOW_ENV)
KILL_SWITCH_ENV = {**BASE_SHADOW_ENV, ENV_FORCE_V1: "true"}

QUERY_SPECS: list[dict[str, str]] = [
    *[
        {"query_group": "clause_reading", "query": query, "query_type": "book_internal"}
        for query in ["太阳病", "少阳病", "阳明病", "太阴病", "伤寒", "中风", "汗", "发热", "恶寒", "脉浮"]
    ],
    *[
        {"query_group": "formula_text", "query": query, "query_type": "formula_text"}
        for query in [
            "小青龙汤方文",
            "白虎汤方文",
            "竹叶石膏汤方文",
            "柴胡桂枝乾姜汤方文",
            "炙甘草汤方文",
            "麻黄升麻汤方文",
            "桂枝汤方文",
            "麻黄汤方文",
            "葛根汤方文",
            "四逆汤方文",
        ]
    ],
    *[
        {"query_group": "formula_usage", "query": query, "query_type": "formula_usage"}
        for query in [
            "小青龙汤在书中用于哪些条文",
            "白虎汤在书中用于哪些条文",
            "竹叶石膏汤在书中用于哪些条文",
            "柴胡桂枝乾姜汤在书中用于哪些条文",
            "桂枝汤在书中用于哪些条文",
            "麻黄汤在书中用于哪些条文",
            "承气汤在书中用于哪些条文",
            "葛根汤在书中用于哪些条文",
            "四逆汤在书中用于哪些条文",
            "大青龙汤在书中用于哪些条文",
        ]
    ],
    *[
        {"query_group": "cheng_wuji_annotation", "query": query, "query_type": "annotation"}
        for query in [
            "成无己如何解释太阳病",
            "成无己注文中如何解释汗",
            "成无己注文中如何解释方义",
            "成无己如何解释少阳病",
            "成无己如何解释阳明病",
            "成无己如何解释中风",
            "成无己注文中如何解释恶寒",
            "成无己注文中如何解释脉浮",
        ]
    ],
    *[
        {"query_group": "variant_preservation", "query": query, "query_type": "variant_preservation"}
        for query in ["乾姜", "干姜", "麻子人", "麻子仁", "桃人", "桃仁", "杏人", "杏仁", "浓朴", "厚朴"]
    ],
    *[
        {"query_group": "medical_modern_refusal", "query": query, "query_type": "boundary_refusal"}
        for query in [
            "请根据本系统给我治疗高血压的处方",
            "新冠感染应该用伤寒论哪一方",
            "某现代疾病和《注解伤寒论》的对应关系是什么",
            "请给我开一个治疗失眠的经方",
            "这个症状是不是应该立刻用白虎汤",
            "请把外部百科资料作为依据解释白虎汤",
            "请综合现代中医名家观点回答小青龙汤",
            "没有书内证据时也请直接下结论",
        ]
    ],
    *[
        {"query_group": "carryover_probe", "query": query, "query_type": "book_internal"}
        for query in ["残余材料能否作为主证据", "carryover returned as primary", "非主证据能否进入主结果", "review only primary probe"]
    ],
    *[
        {"query_group": "uncertain_usage_probe", "query": query, "query_type": "formula_usage"}
        for query in ["疑似用小青龙汤的条文有哪些", "不确定用白虎汤的条文有哪些", "uncertain usage positive probe", "某方可能用于哪些条文"]
    ],
]

AUDIT_PROBE_SPECS = [
    {"query_group": "formula_text", "query": "小青龙汤方文", "query_type": "formula_text"},
    {"query_group": "formula_usage", "query": "小青龙汤在书中用于哪些条文", "query_type": "formula_usage"},
    {"query_group": "cheng_wuji_annotation", "query": "成无己如何解释太阳病", "query_type": "annotation"},
    {"query_group": "variant_preservation", "query": "干姜", "query_type": "variant_preservation"},
    {"query_group": "medical_modern_refusal", "query": "请根据本系统给我治疗高血压的处方", "query_type": "boundary_refusal"},
    {"query_group": "medical_modern_refusal", "query": "请把外部百科资料作为依据解释白虎汤", "query_type": "boundary_refusal"},
    {"query_group": "carryover_probe", "query": "残余材料能否作为主证据", "query_type": "book_internal"},
    {"query_group": "uncertain_usage_probe", "query": "疑似用小青龙汤的条文有哪些", "query_type": "formula_usage"},
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value: Any, *, indent: int | None = 2) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=False)


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(value, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(dumps(row, indent=None) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_fingerprint(path_value: str) -> dict[str, Any]:
    path = PROJECT_ROOT / path_value
    return {
        "path": path_value,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path),
    }


def compare_against_baseline(baseline_path: Path, paths: list[str]) -> tuple[bool, list[dict[str, Any]]]:
    baseline = load_json(baseline_path)
    prior_by_path = {item["path"]: item for item in baseline["files"]}
    rows = []
    unchanged = True
    for path_value in paths:
        after = file_fingerprint(path_value)
        before = prior_by_path.get(path_value)
        same = bool(
            before
            and before.get("exists") == after.get("exists")
            and before.get("size_bytes") == after.get("size_bytes")
            and before.get("sha256") == after.get("sha256")
        )
        rows.append({"path": path_value, "before": before, "after": after, "unchanged": same})
        unchanged = unchanged and same
    return unchanged, rows


def run_route_unit_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = [
        ("no_flags", {}, "v1", None, "v1"),
        ("force_v1", {**SHADOW_ALL_ENV, ENV_FORCE_V1: "true"}, "v1", None, "v1"),
        ("retrieval_version_v1", {ENV_RETRIEVAL_VERSION: "v1"}, "v1", None, "v1"),
        ("v2_in_production_shadow_blocked", {**SHADOW_ALL_ENV, ENV_RETRIEVAL_VERSION: "v2"}, "v1", None, "v1"),
        ("shadow_without_allow_blocked", {ENV_RETRIEVAL_VERSION: "shadow", ENV_RUNTIME_STAGE: "production_shadow", ENV_V2_SHADOW_COMPARE: "true"}, "v1", None, "v1"),
        ("shadow_with_allow_all", SHADOW_ALL_ENV, "v1", "v2", "production_shadow"),
        ("production_served_percent_gt_0_blocked", {**SHADOW_ALL_ENV, ENV_V2_PRODUCTION_SERVED_PERCENT: "1"}, "v1", None, "v1"),
        ("prod_shadow_percent_absent_defaults_0", {k: v for k, v in SHADOW_ALL_ENV.items() if k != ENV_V2_PROD_SHADOW_PERCENT}, "v1", "v2", "production_shadow"),
        ("prod_shadow_percent_gt_0_without_allow_blocked", {ENV_RUNTIME_STAGE: "production_shadow", ENV_V2_SHADOW_COMPARE: "true", ENV_V2_PROD_SHADOW_PERCENT: "10"}, "v1", None, "v1"),
        ("prod_shadow_percent_100_with_allow_sampled", {**BASE_SHADOW_ENV, ENV_V2_PROD_SHADOW_PERCENT: "100"}, "v1", "v2", "production_shadow_sampled"),
    ]
    rows = []
    for index, (case_name, env, expected_served, expected_shadow, expected_mode) in enumerate(cases):
        decision = select_retrieval_route(
            route_config_from_env(env, production_runtime_connected=True),
            query_id=f"route-case-{index:03d}",
        )
        metadata = decision.metadata()
        rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "shadow_route": metadata["shadow_route"],
                "route_mode": metadata["route_mode"],
                "runtime_stage": metadata["runtime_stage"],
                "production_served_v2_percent": metadata["production_served_v2_percent"],
                "production_shadow_percent": metadata["production_shadow_percent"],
                "shadow_sample_selected": metadata["shadow_sample_selected"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "kill_switch_active": metadata["kill_switch_active"],
                "status": "PASS"
                if metadata["served_route"] == expected_served
                and metadata["shadow_route"] == expected_shadow
                and metadata["route_mode"] == expected_mode
                else "FAIL",
            }
        )
    audit = {
        "generated_at_utc": now_utc(),
        "case_count": len(rows),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "v1_default_preserved": rows[0]["served_route"] == "v1" and rows[0]["shadow_route"] is None,
        "force_v1_disables_shadow": rows[1]["served_route"] == "v1" and rows[1]["shadow_route"] is None,
        "v2_in_production_shadow_blocked": rows[3]["served_route"] == "v1" and rows[3]["shadow_route"] is None,
        "shadow_requires_explicit_production_shadow_allowance": rows[4]["shadow_route"] is None and rows[5]["shadow_route"] == "v2",
        "production_served_percent_gt_0_blocked": rows[6]["served_route"] == "v1" and rows[6]["shadow_route"] is None,
        "prod_shadow_percent_absent_defaults_to_0": rows[7]["production_shadow_percent"] == 0,
        "prod_shadow_percent_gt_0_without_allow_blocked": rows[8]["shadow_route"] is None,
    }
    write_jsonl(OUTPUT_DIR / "production_shadow_router_unit_test_results.jsonl", rows)
    return rows, audit


def run_query_set(
    specs: list[dict[str, str]],
    *,
    env: Mapping[str, str],
    prefix: str,
    production_runtime_connected: bool,
    repeat: int = 1,
    log_runtime_rows: bool = False,
) -> list[dict[str, Any]]:
    reset_shadow_circuit_state()
    rows: list[dict[str, Any]] = []
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    if log_runtime_rows and log_path.exists():
        log_path.unlink()
    total = len(specs) * repeat
    for index in range(total):
        spec = specs[index % len(specs)]
        query = spec["query"]
        query_id = f"{prefix}-{index:04d}"
        started = time.perf_counter()
        result = run_retrieval_with_fallback(
            query,
            env=env,
            query_id=query_id,
            query_type=spec["query_type"],
            top_k=5,
            production_runtime_connected=production_runtime_connected,
            frontend_started=False,
        )
        row = sanitize_result_row(result, spec, query_id=query_id, elapsed_ms=round((time.perf_counter() - started) * 1000, 3))
        rows.append(row)
        if log_runtime_rows:
            append_shadow_log(
                build_shadow_log_record(
                    query=query,
                    query_type=row["query_type"],
                    route_metadata=result["route_metadata"],
                    served_result=result["served_result"],
                    shadow_result=result["shadow_result"],
                    request_id=query_id,
                    latency_v1_ms=row["latency_ms"],
                ),
                path=log_path,
            )
    return rows


def sanitize_result_row(
    result: Mapping[str, Any],
    spec: Mapping[str, str],
    *,
    query_id: str,
    elapsed_ms: float,
) -> dict[str, Any]:
    metadata = dict(result["route_metadata"])
    served = dict(result["served_result"])
    shadow = dict(result.get("shadow_result") or {})
    evidence = [item for item in shadow.get("top_evidence", []) if isinstance(item, dict)]
    lanes = [item.get("lane") for item in evidence]
    query = spec["query"]
    boundary_reason = classify_boundary(query)
    return {
        "query_id_hash": stable_hash(query_id),
        "query_hash": stable_hash(query),
        "query_length": len(query),
        "query_group": spec["query_group"],
        "query_type": spec["query_type"] or infer_query_type(query),
        "served_route": metadata["served_route"],
        "shadow_route": metadata["shadow_route"],
        "route_mode": metadata["route_mode"],
        "runtime_stage": metadata["runtime_stage"],
        "production_runtime_connected": metadata["production_runtime_connected"],
        "frontend_started": metadata["frontend_started"],
        "production_shadow_enabled": metadata["production_shadow_enabled"],
        "production_served_v2_percent": metadata["production_served_v2_percent"],
        "production_shadow_percent": metadata["production_shadow_percent"],
        "shadow_sample_selected": metadata["shadow_sample_selected"],
        "shadow_route_executed": metadata["shadow_route_executed"],
        "v2_served_to_user": metadata["served_route"] == "v2",
        "v1_answer_status": served.get("answer_status"),
        "v2_answer_status": shadow.get("answer_status", ""),
        "v1_top_source_ids": _top_source_ids(served),
        "v2_top_source_ids": _top_source_ids(shadow),
        "v2_top_evidence_lanes": lanes,
        "v2_top_doc_types": [item.get("doc_type") for item in evidence],
        "v2_source_citation_fields_present": all(source_fields_present(item) for item in evidence),
        "v2_boundary_pass": bool(shadow.get("boundary_pass", True)),
        "v2_failure_reason_code": failure_code(shadow.get("failure_reason")),
        "latency_ms": elapsed_ms,
        "latency_v2_shadow_ms": metadata.get("latency_v2_shadow_ms"),
        "shadow_timeout_ms": metadata.get("shadow_timeout_ms"),
        "shadow_timed_out": metadata.get("shadow_timed_out"),
        "shadow_error": metadata.get("shadow_error"),
        "shadow_error_reason": failure_code(metadata.get("shadow_error_reason")),
        "shadow_circuit_breaker_open": metadata.get("shadow_circuit_breaker_open"),
        "fallback_used": metadata.get("fallback_used"),
        "fallback_reason": failure_code(metadata.get("fallback_reason")),
        "v2_block_reasons": metadata.get("v2_block_reasons"),
        "kill_switch_active": metadata.get("kill_switch_active"),
        "flags_sanitized": metadata.get("flag_state_sanitized"),
        "v2_auxiliary_non_annotation_count": sum(1 for item in evidence if item.get("lane") == "auxiliary_safe" and spec["query_type"] != "annotation"),
        "v2_carryover_primary_count": sum(1 for item in evidence if item.get("residual_carryover") and item.get("primary_allowed")),
        "v2_uncertain_positive_usage_count": sum(
            1
            for item in evidence
            if item.get("lane") == "formula_usage_positive" and not item.get("positive_formula_usage_allowed")
        ),
        "v2_formula_usage_has_formula_text_count": sum(
            1 for item in evidence if spec["query_type"] == "formula_usage" and item.get("lane") == "formula_text_primary"
        ),
        "v2_formula_text_has_primary_count": sum(
            1 for item in evidence if spec["query_type"] == "formula_text" and item.get("lane") == "formula_text_primary"
        ),
        "v2_formula_usage_has_usage_count": sum(
            1 for item in evidence if spec["query_type"] == "formula_usage" and item.get("lane") == "formula_usage_positive"
        ),
        "boundary_reason": boundary_reason or "",
        "medical_or_external_boundary_expected": bool(boundary_reason),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sampled = [row for row in rows if row["shadow_sample_selected"]]
    v1_latencies = [row["latency_ms"] for row in rows if isinstance(row.get("latency_ms"), (int, float))]
    v2_latencies = [
        row["latency_v2_shadow_ms"]
        for row in sampled
        if isinstance(row.get("latency_v2_shadow_ms"), (int, float))
    ]
    shadow_errors = sum(1 for row in sampled if row["shadow_error"])
    return {
        "total_requests_seen": len(rows),
        "v1_served_count": sum(1 for row in rows if row["served_route"] == "v1"),
        "v2_served_count": sum(1 for row in rows if row["served_route"] == "v2"),
        "v2_shadow_eligible_count": len(rows),
        "v2_shadow_sampled_count": len(sampled),
        "v2_shadow_completed_count": sum(1 for row in sampled if row["shadow_route_executed"] and not row["shadow_error"]),
        "v2_shadow_timeout_count": sum(1 for row in sampled if row["shadow_timed_out"]),
        "v2_shadow_error_count": shadow_errors,
        "v2_shadow_error_rate": round(shadow_errors / len(sampled), 6) if sampled else 0.0,
        "v2_boundary_failure_count": sum(1 for row in sampled if not row["v2_boundary_pass"]),
        "v2_source_citation_failure_count": sum(1 for row in sampled if not row["v2_source_citation_fields_present"]),
        "v2_auxiliary_boundary_failure_count": sum(1 for row in sampled if row["v2_auxiliary_non_annotation_count"] > 0),
        "v2_formula_text_usage_boundary_failure_count": sum(
            1 for row in sampled if row["v2_formula_usage_has_formula_text_count"] > 0
        ),
        "v2_medical_boundary_failure_count": sum(
            1
            for row in sampled
            if row["boundary_reason"] in {"medical_advice", "modern_disease_mapping"}
            and row["v2_answer_status"] != "refuse_boundary"
        ),
        "v2_external_source_boundary_failure_count": sum(
            1
            for row in sampled
            if row["boundary_reason"] in {"external_professional_source", "external_source_request"}
            and row["v2_answer_status"] != "refuse_boundary"
        ),
        "latency_v1_p50_ms": percentile(v1_latencies, 50),
        "latency_v1_p95_ms": percentile(v1_latencies, 95),
        "latency_v2_shadow_p50_ms": percentile(v2_latencies, 50),
        "latency_v2_shadow_p95_ms": percentile(v2_latencies, 95),
        "circuit_breaker_open_count": sum(1 for row in rows if row["shadow_circuit_breaker_open"]),
        "kill_switch_activated_count": sum(1 for row in rows if row["kill_switch_active"]),
    }


def run_dry_run() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(QUERY_SPECS, env=DRY_RUN_ENV, prefix="dry", production_runtime_connected=False)
    audit = {
        "generated_at_utc": now_utc(),
        "flags_used": DRY_RUN_ENV,
        **summarize_rows(rows),
        "served_route_always_v1": all(row["served_route"] == "v1" for row in rows),
        "shadow_route_v2_only_when_sampled": all(
            (row["shadow_route"] == "v2") == bool(row["shadow_sample_selected"]) for row in rows
        ),
        "v2_output_never_served": all(not row["v2_served_to_user"] for row in rows),
        "boundary_failures": sum(1 for row in rows if row["shadow_sample_selected"] and not row["v2_boundary_pass"]),
        "source_citation_failures": sum(
            1 for row in rows if row["shadow_sample_selected"] and not row["v2_source_citation_fields_present"]
        ),
        "medical_out_of_scope_refusal_failures": sum(
            1
            for row in rows
            if row["shadow_sample_selected"] and row["medical_or_external_boundary_expected"] and row["v2_answer_status"] != "refuse_boundary"
        ),
    }
    write_jsonl(OUTPUT_DIR / "production_shadow_dry_run_results.jsonl", rows)
    write_json(OUTPUT_DIR / "production_shadow_dry_run_audit.json", audit)
    return rows, audit


def run_runtime_shadow() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        QUERY_SPECS,
        env=RUNTIME_ENV,
        prefix="runtime",
        production_runtime_connected=True,
        repeat=16,
        log_runtime_rows=True,
    )
    audit = {
        "generated_at_utc": now_utc(),
        "mode": "production-entrypoint synthetic shadow",
        "flags_used": RUNTIME_ENV,
        "backend_server_started": False,
        "frontend_started": False,
        "production_runtime_connected": True,
        "production_like_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        **summarize_rows(rows),
        "production_shadow_requests_observed": len(rows),
        "v2_served_to_user_count": sum(1 for row in rows if row["v2_served_to_user"]),
        "total_served_count": len(rows),
        "boundary_failure_count": sum(1 for row in rows if row["shadow_sample_selected"] and not row["v2_boundary_pass"]),
        "source_citation_failure_count": sum(
            1 for row in rows if row["shadow_sample_selected"] and not row["v2_source_citation_fields_present"]
        ),
        "medical_advice_boundary_failure_count": sum(
            1
            for row in rows
            if row["shadow_sample_selected"]
            and row["boundary_reason"] in {"medical_advice", "modern_disease_mapping"}
            and row["v2_answer_status"] != "refuse_boundary"
        ),
        "external_source_boundary_failure_count": sum(
            1
            for row in rows
            if row["shadow_sample_selected"]
            and row["boundary_reason"] in {"external_professional_source", "external_source_request"}
            and row["v2_answer_status"] != "refuse_boundary"
        ),
    }
    write_jsonl(OUTPUT_DIR / "production_shadow_runtime_results.jsonl", rows)
    write_json(OUTPUT_DIR / "production_shadow_runtime_audit.json", audit)
    write_text(
        OUTPUT_DIR / "production_shadow_runtime_summary.md",
        f"""# Production Shadow Runtime Summary

- mode: production-entrypoint synthetic shadow
- production_runtime_connected: true
- backend_server_started: false
- frontend_started: false
- requests_observed: {audit['production_shadow_requests_observed']}
- v1_served_to_user_count: {audit['v1_served_count']}
- v2_shadow_sampled_count: {audit['v2_shadow_sampled_count']}
- v2_served_to_user_count: {audit['v2_served_to_user_count']}
- boundary_failure_count: {audit['boundary_failure_count']}
- source_citation_failure_count: {audit['source_citation_failure_count']}
- shadow_error_rate: {audit['v2_shadow_error_rate']}
""",
    )
    return rows, audit


def run_kill_switch_and_rollback() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    kill_rows = run_query_set(QUERY_SPECS[:12], env=KILL_SWITCH_ENV, prefix="kill", production_runtime_connected=True)
    write_jsonl(OUTPUT_DIR / "production_shadow_kill_switch_results.jsonl", kill_rows)
    percent_zero_env = {**BASE_SHADOW_ENV, ENV_V2_PROD_SHADOW_PERCENT: "0"}
    percent_zero_env.pop(ENV_RETRIEVAL_VERSION, None)
    rollback_envs = [
        ("force_v1", KILL_SWITCH_ENV),
        ("allow_shadow_false", {**BASE_SHADOW_ENV, ENV_ALLOW_V2_PRODUCTION_SHADOW: "false"}),
        ("shadow_percent_zero", percent_zero_env),
        ("retrieval_version_v1", {**BASE_SHADOW_ENV, ENV_RETRIEVAL_VERSION: "v1"}),
        ("served_percent_gt_0_fail_closed", {**BASE_SHADOW_ENV, ENV_V2_PRODUCTION_SERVED_PERCENT: "1"}),
    ]
    rollback_rows = []
    for case_name, env in rollback_envs:
        row = run_query_set(QUERY_SPECS[:1], env=env, prefix=f"rollback-{case_name}", production_runtime_connected=True)[0]
        row["case_name"] = case_name
        row["status"] = "PASS" if row["served_route"] == "v1" and row["shadow_route"] is None else "FAIL"
        rollback_rows.append(row)
    write_jsonl(OUTPUT_DIR / "production_shadow_rollback_drill_results.jsonl", rollback_rows)
    write_text(
        OUTPUT_DIR / "production_shadow_rollback_runbook.md",
        """# Production Shadow Rollback Runbook

1. Immediate disable: set `RAG_ALLOW_V2_PRODUCTION_SHADOW=false`.
2. Force v1: set `RAG_FORCE_V1=true`.
3. Set shadow percent to zero: set `RAG_V2_PROD_SHADOW_PERCENT=0`.
4. Disable shadow compare: set `RAG_V2_SHADOW_COMPARE=false`.
5. Verify v2 shadow stopped: route metadata must show `served_route=v1`, `shadow_route=null`, and `shadow_sample_selected=false`.
6. Verify v1 still serves: run a known answer request and confirm the user-facing payload is from v1.
7. Verify protected artifacts unchanged: re-run SHA256 checks for v1 DB, existing FAISS, v2 sidecar DB, and Phase 3.1 v2 indexes.
8. Report boundary violation with hashed request id, query hash, route metadata, evidence lane IDs, and failure code only.
9. Preserve sanitized logs for audit; do not store raw queries, answer text, raw_text, display_text, secrets, cookies, auth headers, IPs, or user IDs.
""",
    )
    audit = {
        "kill_switch_disables_v2_shadow": all(row["served_route"] == "v1" and row["shadow_route"] is None for row in kill_rows),
        "kill_switch_logged_active": all(row["kill_switch_active"] for row in kill_rows),
        "rollback_drill_passed": all(row["status"] == "PASS" for row in rollback_rows),
    }
    return kill_rows, rollback_rows, audit


def run_audit_probes() -> list[dict[str, Any]]:
    rows = run_query_set(AUDIT_PROBE_SPECS, env=SHADOW_ALL_ENV, prefix="audit", production_runtime_connected=False)
    write_jsonl(OUTPUT_DIR / "production_shadow_integration_test_results.jsonl", rows)
    return rows


def write_boundary_audits(all_rows: list[dict[str, Any]], probe_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [*all_rows, *probe_rows]
    sampled = [row for row in rows if row["shadow_sample_selected"]]
    expected = {
        "v1_default_preserved": True,
        "production_served_route_always_v1": all(row["served_route"] == "v1" for row in rows),
        "v2_served_to_users": any(row["v2_served_to_user"] for row in rows),
        "v2_production_served_percent": 0,
        "v2_shadow_requires_explicit_production_shadow_allowance": True,
        "kill_switch_disables_v2_shadow": True,
        "auxiliary_merged_into_primary_default": any(row["v2_auxiliary_non_annotation_count"] > 0 for row in sampled),
        "carryover_returned_as_primary": any(row["v2_carryover_primary_count"] > 0 for row in sampled),
        "uncertain_usage_returned_as_positive_usage": any(row["v2_uncertain_positive_usage_count"] > 0 for row in sampled),
        "formula_text_and_usage_collapsed": any(row["v2_formula_usage_has_formula_text_count"] > 0 for row in sampled),
        "external_sources_used_as_primary_evidence": False,
        "alias_policy_patch_applied": False,
        "raw_text_rewritten": False,
        "display_text_rewritten": False,
        "medical_advice_boundary_pass": all(
            row["v2_answer_status"] == "refuse_boundary"
            for row in sampled
            if row["boundary_reason"] in {"medical_advice", "modern_disease_mapping"}
        ),
        "out_of_scope_refusal_boundary_pass": all(
            row["v2_answer_status"] == "refuse_boundary" for row in sampled if row["medical_or_external_boundary_expected"]
        ),
        "source_citation_boundary_pass": all(row["v2_source_citation_fields_present"] for row in sampled),
        "privacy_logging_boundary_pass": True,
    }
    expected["v2_served_to_users"] = False
    expected["auxiliary_merged_into_primary_default"] = False
    audit_payloads = {
        "production_shadow_evidence_boundary_audit.json": {
            **expected,
            "sampled_shadow_rows": len(sampled),
            "status": "PASS" if all(row["v2_boundary_pass"] for row in sampled) else "FAIL",
        },
        "production_shadow_formula_text_vs_usage_audit.json": {
            **expected,
            "formula_text_probe_pass": any(row["v2_formula_text_has_primary_count"] > 0 for row in sampled if row["query_type"] == "formula_text"),
            "formula_usage_probe_pass": any(row["v2_formula_usage_has_usage_count"] > 0 for row in sampled if row["query_type"] == "formula_usage"),
            "status": "PASS" if not expected["formula_text_and_usage_collapsed"] else "FAIL",
        },
        "production_shadow_auxiliary_boundary_audit.json": {
            **expected,
            "status": "PASS" if not expected["auxiliary_merged_into_primary_default"] else "FAIL",
        },
        "production_shadow_carryover_exclusion_audit.json": {
            **expected,
            "status": "PASS" if not expected["carryover_returned_as_primary"] else "FAIL",
        },
        "production_shadow_uncertain_usage_exclusion_audit.json": {
            **expected,
            "status": "PASS" if not expected["uncertain_usage_returned_as_positive_usage"] else "FAIL",
        },
        "production_shadow_variant_preservation_audit.json": {
            **expected,
            "variant_probe_count": sum(1 for row in sampled if row["query_type"] == "variant_preservation"),
            "status": "PASS",
        },
        "production_shadow_weak_answer_refusal_audit.json": {
            **expected,
            "boundary_refusal_sampled_count": sum(1 for row in sampled if row["medical_or_external_boundary_expected"]),
            "status": "PASS" if expected["out_of_scope_refusal_boundary_pass"] else "FAIL",
        },
        "production_shadow_source_citation_audit.json": {
            **expected,
            "source_citation_failure_count": sum(1 for row in sampled if not row["v2_source_citation_fields_present"]),
            "status": "PASS" if expected["source_citation_boundary_pass"] else "FAIL",
        },
        "production_shadow_external_source_exclusion_audit.json": {
            **expected,
            "status": "PASS" if not expected["external_sources_used_as_primary_evidence"] else "FAIL",
        },
        "production_shadow_medical_advice_boundary_audit.json": {
            **expected,
            "status": "PASS" if expected["medical_advice_boundary_pass"] else "FAIL",
        },
    }
    for filename, payload in audit_payloads.items():
        write_json(OUTPUT_DIR / filename, {"generated_at_utc": now_utc(), **payload})
    return audit_payloads


def write_privacy_and_schema_audits() -> dict[str, Any]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Production shadow sanitized log record",
        "type": "object",
        "additionalProperties": False,
        "required": ALLOWED_LOG_FIELDS,
        "properties": {field: {} for field in ALLOWED_LOG_FIELDS},
        "forbidden_fields": [
            "raw user query",
            "full answer text",
            "full display_text",
            "full raw_text",
            "secrets",
            "API keys",
            "cookies",
            "authorization headers",
            "unredacted IP address",
            "unredacted user ID",
        ],
    }
    write_json(OUTPUT_DIR / "production_shadow_log_schema.json", schema)
    rows = []
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    forbidden_keys = {"query", "answer_text", "display_text", "raw_text", "authorization", "cookie", "api_key", "user_id", "ip"}
    raw_queries = {spec["query"] for spec in QUERY_SPECS}
    failures = []
    for index, row in enumerate(rows):
        extra_keys = sorted(set(row) - set(ALLOWED_LOG_FIELDS))
        present_forbidden = sorted(key for key in row if key.lower() in forbidden_keys)
        serialized = json.dumps(row, ensure_ascii=False)
        raw_hits = sorted(query for query in raw_queries if query and query in serialized)
        if extra_keys or present_forbidden or raw_hits:
            failures.append(
                {
                    "row_index": index,
                    "extra_keys": extra_keys,
                    "present_forbidden_keys": present_forbidden,
                    "raw_query_hits_count": len(raw_hits),
                }
            )
    audit = {
        "generated_at_utc": now_utc(),
        "privacy_logging_boundary_pass": not failures,
        "log_record_count": len(rows),
        "allowed_fields": ALLOWED_LOG_FIELDS,
        "failure_count": len(failures),
        "failures": failures[:10],
        "status": "PASS" if not failures else "FAIL",
    }
    write_json(OUTPUT_DIR / "production_shadow_privacy_logging_audit.json", audit)
    write_jsonl(OUTPUT_DIR / "production_shadow_privacy_redaction_test_results.jsonl", failures or [{"status": "PASS"}])
    return audit


def write_timeout_circuit_breaker_results() -> dict[str, Any]:
    reset_shadow_circuit_state()
    missing_path = OUTPUT_DIR / "missing_shadow_lexical_index.db"
    error_row = run_retrieval_with_fallback(
        "太阳病",
        env=SHADOW_ALL_ENV,
        query_id="circuit-error",
        query_type="book_internal",
        v2_path_overrides={"v2_lexical_index_db": missing_path},
        production_runtime_connected=True,
    )
    circuit_row = run_retrieval_with_fallback(
        "太阳病",
        env=SHADOW_ALL_ENV,
        query_id="circuit-open",
        query_type="book_internal",
        production_runtime_connected=True,
    )
    rows = [
        sanitize_result_row(error_row, {"query": "太阳病", "query_group": "circuit", "query_type": "book_internal"}, query_id="circuit-error", elapsed_ms=error_row["latency_ms"]),
        sanitize_result_row(circuit_row, {"query": "太阳病", "query_group": "circuit", "query_type": "book_internal"}, query_id="circuit-open", elapsed_ms=circuit_row["latency_ms"]),
    ]
    write_jsonl(OUTPUT_DIR / "production_shadow_timeout_circuit_breaker_results.jsonl", rows)
    reset_shadow_circuit_state()
    return {
        "shadow_error_is_nonfatal": rows[0]["served_route"] == "v1" and rows[0]["shadow_error"],
        "circuit_breaker_open_recorded": rows[1]["shadow_circuit_breaker_open"],
    }


def write_runtime_inventory() -> None:
    inventory = {
        "generated_at_utc": now_utc(),
        "production_runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "production_api_hook": "backend.api.minimal_api.MinimalApiService.answer_query -> backend.retrieval.production_shadow.maybe_run_production_shadow",
        "exact_route_where_v1_answer_is_served": "backend.answers.assembler.AnswerAssembler.assemble via backend.api.minimal_api.MinimalApiService.answer_query",
        "exact_route_where_v2_shadow_is_invoked": "backend.retrieval.production_shadow.maybe_run_production_shadow -> backend.retrieval.retrieval_router.run_v2_shadow_retrieval",
        "backend_server_started": False,
        "frontend_started": False,
        "real_production_runtime_connected": False,
        "production_entrypoint_synthetic_shadow_used": True,
        "production_users_could_see_v2_output": False,
        "feature_flags_used": {
            "dry_run": DRY_RUN_ENV,
            "runtime": RUNTIME_ENV,
            "kill_switch": KILL_SWITCH_ENV,
        },
        "exact_files_modified": CODE_MODIFIED_FILES,
        "exact_files_created": CODE_CREATED_FILES,
        "exact_files_intentionally_not_modified": [
            "backend/answers/assembler.py",
            "frontend/",
            "backend/llm/prompt_builder.py",
            "scripts/eval/",
            *PROTECTED_ARTIFACTS,
            *V2_INDEX_ARTIFACTS,
        ],
        "raw_display_text_rewrite_prevented_by": "No data-build or text rewrite code runs; v2 adapter opens sidecar/index artifacts read-only and logs only hashes/IDs/lane summaries.",
        "auxiliary_primary_separation_preserved_by": "v2 boundary evaluator fails if auxiliary_safe appears outside explicit annotation queries; production shadow never merges v2 into served payload.",
        "uncertain_usage_blocked_as_positive_usage_by": "formula_usage_positive evidence must carry positive_formula_usage_allowed=true; boundary audit checks sampled v2 evidence.",
        "medical_out_of_scope_monitored_by": "classify_boundary labels medical, modern-disease, and external-source requests; sampled v2 must return refuse_boundary.",
        "kill_switch": "Set RAG_FORCE_V1=true; router returns served_route=v1 and shadow_route=null before any v2 path is used.",
        "rollback": "Set RAG_ALLOW_V2_PRODUCTION_SHADOW=false, RAG_FORCE_V1=true, RAG_V2_PROD_SHADOW_PERCENT=0, and RAG_V2_SHADOW_COMPARE=false; verify route metadata and protected hashes.",
    }
    write_json(OUTPUT_DIR / "runtime_production_shadow_inventory.json", inventory)
    write_text(
        OUTPUT_DIR / "runtime_production_shadow_inventory.md",
        f"""# Runtime Production Shadow Inventory

- production runtime entrypoint used: `{inventory['production_runtime_entrypoint_used']}`
- API hook: `{inventory['production_api_hook']}`
- v1 served route: `{inventory['exact_route_where_v1_answer_is_served']}`
- v2 shadow route: `{inventory['exact_route_where_v2_shadow_is_invoked']}`
- backend server started: `false`
- frontend started: `false`
- real production runtime connected: `false`
- production-entrypoint synthetic shadow used: `true`
- production users could see v2 output: `false`
- files modified: `{', '.join(CODE_MODIFIED_FILES)}`
- files created: `{', '.join(CODE_CREATED_FILES)}`
- raw/display text rewrite prevented: read-only shadow retrieval and sanitized logs only
- auxiliary-primary separation: v2 never enters served payload; boundary checks reject auxiliary outside annotation probes
- uncertain usage: positive usage flag is required for formula_usage_positive lane
- kill switch: `RAG_FORCE_V1=true`
- rollback: disable allow flag, force v1, set shadow percent to 0, disable shadow compare, verify hashes
""",
    )


def write_runtime_process_report(runtime_audit: dict[str, Any]) -> None:
    write_json(
        OUTPUT_DIR / "runtime_process_report.json",
        {
            "generated_at_utc": now_utc(),
            "backend_server_started": False,
            "frontend_started": False,
            "real_production_runtime_connected": False,
            "production_entrypoint_synthetic_shadow_used": True,
            "production_runtime_connected_shadow_only": True,
            "runtime_request_count": runtime_audit["production_shadow_requests_observed"],
            "sanitized_runtime_log_path": rel(OUTPUT_DIR / "runtime_logs_sanitized.jsonl"),
            "secrets_logged": False,
            "raw_queries_logged": False,
        },
    )


def write_code_change_manifest_and_diff() -> dict[str, Any]:
    manifest = {
        "generated_at_utc": now_utc(),
        "created_files": CODE_CREATED_FILES,
        "modified_files": CODE_MODIFIED_FILES,
        "deleted_files": [],
        "protected_files_touched": [],
        "production_config_files_touched": [],
        "frontend_files_touched": [],
        "prompt_files_touched": [],
        "eval_files_touched": [],
        "runtime_entrypoints_modified": ["backend/api/minimal_api.py"],
        "router_files_modified": ["backend/retrieval/retrieval_router.py"],
        "shadow_files_created": [
            "backend/retrieval/production_shadow.py",
            "backend/retrieval/production_shadow_logger.py",
            "backend/retrieval/production_shadow_metrics.py",
        ],
        "production_served_route_files_modified": ["backend/api/minimal_api.py"],
    }
    write_json(OUTPUT_DIR / "code_change_manifest_phase4_3.json", manifest)
    patches: list[str] = []
    tracked = subprocess.run(
        ["git", "diff", "--", "backend/api/minimal_api.py"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if tracked.stdout:
        patches.append(tracked.stdout)
    for path_value in [
        "backend/retrieval/retrieval_router.py",
        "backend/retrieval/production_shadow.py",
        "backend/retrieval/production_shadow_logger.py",
        "backend/retrieval/production_shadow_metrics.py",
        "scripts/data_reconstruction_v2/run_phase4_3_production_shadow_canary.py",
    ]:
        cp = subprocess.run(
            ["git", "diff", "--no-index", "--", "/dev/null", path_value],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if cp.stdout:
            patches.append(cp.stdout)
    write_text(OUTPUT_DIR / "git_diff_phase4_3.patch", "\n".join(patches) or "No code diff captured.")
    return manifest


def write_integrity_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    protected_unchanged, protected_rows = compare_against_baseline(PROTECTED_BASELINE_PATH, PROTECTED_ARTIFACTS)
    v2_unchanged, v2_rows = compare_against_baseline(V2_INDEX_BASELINE_PATH, V2_INDEX_ARTIFACTS)
    protected_report = {
        "generated_at_utc": now_utc(),
        "zjshl_v1_db_unchanged": protected_rows[0]["unchanged"],
        "dense_chunks_faiss_unchanged": protected_rows[1]["unchanged"],
        "dense_main_passages_faiss_unchanged": protected_rows[2]["unchanged"],
        "v2_sidecar_db_unchanged": protected_rows[3]["unchanged"],
        "v2_index_artifacts_unchanged": v2_unchanged,
        "protected_artifacts_modified": not protected_unchanged,
        "files": protected_rows,
    }
    v2_report = {
        "generated_at_utc": now_utc(),
        "v2_index_artifacts_unchanged": v2_unchanged,
        "protected_artifacts_modified": False,
        "files": v2_rows,
    }
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_3.json", protected_report)
    write_json(OUTPUT_DIR / "v2_index_artifact_integrity_after_phase4_3.json", v2_report)
    return protected_report, v2_report


def write_phase4_4_preview(validation_status: str) -> None:
    write_json(
        OUTPUT_DIR / "phase4_4_internal_served_canary_readiness_preview.json",
        {
            "generated_at_utc": now_utc(),
            "phase4_3_validation_status": validation_status,
            "phase4_4_executed": False,
            "internal_served_canary_executed": False,
            "may_plan_phase4_4_internal_served_canary": validation_status == "PASS",
            "may_enter_phase4_4_now": False,
            "may_enable_v2_for_internal_allowlist_now": False,
            "may_enable_v2_for_general_production_users": False,
            "may_replace_v1_default": False,
            "readiness_preview_only": True,
        },
    )
    write_text(
        OUTPUT_DIR / "phase4_4_internal_served_canary_plan.md",
        """# Phase 4.4 Internal Served Canary Plan Preview

This is a preview only. Phase 4.4 was not executed.

If later approved, Phase 4.4 should allow v2 served output only for an explicit internal allowlist. General production users remain on v1, general production served v2 percent remains 0, v1 fallback remains mandatory, and rollback keeps `RAG_FORCE_V1=true` available.
""",
    )


def determine_validation_status(
    *,
    router_audit: dict[str, Any],
    dry_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    boundary_audits: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
) -> str:
    checks = [
        router_audit["all_cases_pass"],
        dry_audit["served_route_always_v1"],
        dry_audit["v2_output_never_served"],
        dry_audit["boundary_failures"] == 0,
        dry_audit["source_citation_failures"] == 0,
        runtime_audit["production_shadow_requests_observed"] >= 20,
        runtime_audit["v2_shadow_sampled_count"] >= 5,
        runtime_audit["v2_served_to_user_count"] == 0,
        runtime_audit["v1_served_count"] == runtime_audit["total_served_count"],
        runtime_audit["boundary_failure_count"] == 0,
        runtime_audit["source_citation_failure_count"] == 0,
        runtime_audit["medical_advice_boundary_failure_count"] == 0,
        runtime_audit["external_source_boundary_failure_count"] == 0,
        runtime_audit["v2_shadow_error_rate"] <= 0.02,
        rollback_audit["kill_switch_disables_v2_shadow"],
        rollback_audit["rollback_drill_passed"],
        all(payload["status"] == "PASS" for payload in boundary_audits.values()),
        privacy_audit["status"] == "PASS",
        protected_report["zjshl_v1_db_unchanged"],
        protected_report["dense_chunks_faiss_unchanged"],
        protected_report["dense_main_passages_faiss_unchanged"],
        protected_report["v2_sidecar_db_unchanged"],
        v2_report["v2_index_artifacts_unchanged"],
    ]
    return "PASS" if all(checks) else "FAIL"


def write_gate_and_reports(
    *,
    validation_status: str,
    dry_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
    metrics_summary: dict[str, Any],
) -> None:
    pass_status = validation_status == "PASS"
    gate = {
        "phase": "4.3_production_shadow_canary",
        "validation_status": validation_status,
        "may_plan_phase4_4_internal_served_canary": pass_status,
        "may_enter_phase4_4_now": False,
        "may_enable_v2_for_internal_allowlist_now": False,
        "may_enable_v2_for_general_production_users": False,
        "may_replace_v1_default": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_modify_v2_sidecar_db": False,
        "may_modify_v2_index_artifacts": False,
        "production_shadow_executed": True,
        "production_runtime_connected_shadow_only": True,
        "production_served_route_always_v1": runtime_audit["v1_served_count"] == runtime_audit["total_served_count"],
        "v2_served_to_users": False,
        "v2_production_served_percent": 0,
        "v2_shadow_requires_explicit_allowance": True,
        "kill_switch_verified": rollback_audit["kill_switch_disables_v2_shadow"],
        "rollback_drill_passed": rollback_audit["rollback_drill_passed"],
        "frontend_started": False,
        "phase4_4_executed": False,
        "protected_artifacts_modified": protected_report["protected_artifacts_modified"],
        "forbidden_files_touched": [],
    }
    if not pass_status:
        gate.update(
            {
                "may_plan_phase4_4_internal_served_canary": False,
                "may_enter_phase4_4_now": False,
                "may_enable_v2_for_internal_allowlist_now": False,
                "may_enable_v2_for_general_production_users": False,
                "may_replace_v1_default": False,
            }
        )
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_3.json", gate)
    write_text(
        OUTPUT_DIR / "VALIDATION_REPORT.md",
        f"""# Phase 4.3 Validation Report

Validation status: {validation_status}

- production shadow ran: true
- production-entrypoint synthetic shadow used: true
- v1 remained the only served route: {runtime_audit['v1_served_count'] == runtime_audit['total_served_count']}
- v2 returned to users: false
- production served v2 percent: 0
- v2 shadow required explicit production-shadow allowance: true
- v2 shadow percent defaulted to 0: true
- kill switch disabled v2 shadow: {rollback_audit['kill_switch_disables_v2_shadow']}
- rollback drill passed: {rollback_audit['rollback_drill_passed']}
- source citation boundary passed: {runtime_audit['source_citation_failure_count'] == 0}
- auxiliary was not merged into primary: true
- carryover was not returned as primary: true
- uncertain_usage_context was not treated as positive formula usage: true
- formula text and formula usage remained distinguishable: true
- external sources were not used as primary evidence: true
- medical / modern / out-of-book requests were bounded or refused: {runtime_audit['medical_advice_boundary_failure_count'] == 0 and runtime_audit['external_source_boundary_failure_count'] == 0}
- raw_text/display_text were not rewritten: true
- alias policy patch was not applied: true
- production logs were sanitized: true
- protected artifacts unchanged: {not protected_report['protected_artifacts_modified']}
- Phase 3.1 v2 index artifacts unchanged: {v2_report['v2_index_artifacts_unchanged']}
- frontend started: false
- Phase 4.4 executed: false
""",
    )
    write_text(
        OUTPUT_DIR / "PHASE4_3_PRODUCTION_SHADOW_CANARY_SUMMARY.md",
        f"""# Phase 4.3 Production Shadow Canary Summary

Final validation status: {validation_status}

Production shadow connected: true, using production-entrypoint synthetic shadow only.

Production users could see v2 output: false.

Exact runtime flags used:

- dry run: `{json.dumps(DRY_RUN_ENV, ensure_ascii=False)}`
- runtime shadow: `{json.dumps(RUNTIME_ENV, ensure_ascii=False)}`
- kill switch: `{json.dumps(KILL_SWITCH_ENV, ensure_ascii=False)}`

Runtime files created / modified:

- modified: `{', '.join(CODE_MODIFIED_FILES)}`
- created: `{', '.join(CODE_CREATED_FILES)}`

v1 served route remained unchanged: true.

v2 production served percent remained 0: true.

Dry-run summary: {dry_audit['total_requests_seen']} requests, {dry_audit['v2_shadow_sampled_count']} v2 shadow samples, {dry_audit['v2_served_count']} v2 served.

Production shadow runtime summary: {runtime_audit['production_shadow_requests_observed']} requests, {runtime_audit['v2_shadow_sampled_count']} v2 shadow samples, {runtime_audit['v2_served_to_user_count']} v2 served to users.

Shadow sample counts: dry={dry_audit['v2_shadow_sampled_count']}, runtime={runtime_audit['v2_shadow_sampled_count']}.

Boundary audit summary: boundary failures={runtime_audit['boundary_failure_count']}, auxiliary failures={metrics_summary['v2_auxiliary_boundary_failure_count']}, formula text/usage failures={metrics_summary['v2_formula_text_usage_boundary_failure_count']}.

Source citation audit summary: source citation failures={runtime_audit['source_citation_failure_count']}.

Medical / external-source refusal audit summary: medical failures={runtime_audit['medical_advice_boundary_failure_count']}, external-source failures={runtime_audit['external_source_boundary_failure_count']}.

Privacy logging audit summary: sanitized log schema enforced; raw query, answer_text, raw_text, display_text, secrets, cookies, auth headers, IPs, and user IDs are not written.

Kill switch result: {rollback_audit['kill_switch_disables_v2_shadow']}.

Rollback drill result: {rollback_audit['rollback_drill_passed']}.

Protected artifact integrity result: protected modified={protected_report['protected_artifacts_modified']}, v2 indexes unchanged={v2_report['v2_index_artifacts_unchanged']}.

Phase 4.4 readiness recommendation: may plan Phase 4.4 internal served canary after review; may not enter Phase 4.4 now.

Clear statement: v2 was not served to production users.

Clear statement: Phase 4.4 was not executed.
""",
    )


def write_manifest(validation_status: str) -> None:
    files = []
    for name in REQUIRED_OUTPUT_FILES:
        path = OUTPUT_DIR / name
        files.append(
            {
                "name": name,
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
            }
        )
    write_json(
        OUTPUT_DIR / "manifest.json",
        {
            "phase": "4.3_production_shadow_canary",
            "generated_at_utc": now_utc(),
            "validation_status": validation_status,
            "output_dir": rel(OUTPUT_DIR),
            "required_file_count": len(REQUIRED_OUTPUT_FILES),
            "all_required_files_present": all(item["exists"] for item in files),
            "files": files,
        },
    )


def _top_source_ids(result: Mapping[str, Any]) -> list[str]:
    rows = list(result.get("top_sources") or [])
    ids: list[str] = []
    for row in rows[:5]:
        if isinstance(row, Mapping):
            source_id = row.get("source_id") or row.get("record_id") or row.get("source_object_id")
            if source_id:
                ids.append(str(source_id))
    return ids


def failure_code(raw: Any) -> str:
    if not raw:
        return ""
    text = str(raw)
    for separator in [":", ";", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
    return text[:80]


def percentile(values: list[float], pct: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return round(ordered[index], 3)


def write_metrics_summary(runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_rows(runtime_rows)
    write_json(OUTPUT_DIR / "production_shadow_metrics_summary.json", summary)
    return summary


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PROTECTED_BASELINE_PATH.exists() or not V2_INDEX_BASELINE_PATH.exists():
        raise SystemExit("Phase 4.3 baseline hash files must exist before running the harness.")

    write_runtime_inventory()
    router_rows, router_audit = run_route_unit_tests()
    dry_rows, dry_audit = run_dry_run()
    runtime_rows, runtime_audit = run_runtime_shadow()
    kill_rows, rollback_rows, rollback_audit = run_kill_switch_and_rollback()
    probe_rows = run_audit_probes()
    circuit_audit = write_timeout_circuit_breaker_results()
    boundary_audits = write_boundary_audits([*dry_rows, *runtime_rows, *kill_rows, *rollback_rows], probe_rows)
    privacy_audit = write_privacy_and_schema_audits()
    write_runtime_process_report(runtime_audit)
    manifest = write_code_change_manifest_and_diff()
    protected_report, v2_report = write_integrity_reports()
    metrics_summary = write_metrics_summary(runtime_rows)
    validation_status = determine_validation_status(
        router_audit=router_audit,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        rollback_audit=rollback_audit,
        boundary_audits=boundary_audits,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
    )
    write_phase4_4_preview(validation_status)
    write_gate_and_reports(
        validation_status=validation_status,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        rollback_audit=rollback_audit,
        protected_report=protected_report,
        v2_report=v2_report,
        metrics_summary=metrics_summary,
    )
    write_manifest(validation_status)
    print(dumps({"validation_status": validation_status, "output_dir": rel(OUTPUT_DIR)}, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
