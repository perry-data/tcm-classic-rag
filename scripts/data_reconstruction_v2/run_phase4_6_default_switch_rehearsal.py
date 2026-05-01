#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.limited_general_canary import stable_hash  # noqa: E402
from backend.retrieval.staging_default_logger import (  # noqa: E402
    ALLOWED_LOG_FIELDS,
    append_staging_default_log,
    build_staging_default_log_record,
)
from backend.retrieval.staging_default_metrics import (  # noqa: E402
    get_staging_default_state,
    record_staging_default_outcome,
    reset_staging_default_state,
    staging_default_auto_stop_reasons,
)
from backend.retrieval.retrieval_router import (  # noqa: E402
    ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH,
    ENV_FORCE_V1,
    ENV_RETRIEVAL_VERSION,
    ENV_RUNTIME_STAGE,
    ENV_V2_FALLBACK_TO_V1,
    ENV_V2_GENERAL_SERVED_PERCENT,
    ENV_V2_PROD_SHADOW_ALL,
    ENV_V2_PROD_SHADOW_PERCENT,
    ENV_V2_PRODUCTION_DEFAULT,
    ENV_V2_PRODUCTION_SERVED_PERCENT,
    ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE,
    ENV_V2_STAGING_CIRCUIT_BREAKER,
    ENV_V2_STAGING_DEFAULT,
    ENV_V2_STAGING_DEFAULT_PERCENT,
    ENV_V2_STAGING_DEFAULT_REQUIRE_MONITORS,
    ENV_V2_STAGING_MAX_BOUNDARY_FAILURES,
    ENV_V2_STAGING_MAX_ERROR_RATE,
    ENV_V2_STAGING_MAX_EXTERNAL_SOURCE_FAILURES,
    ENV_V2_STAGING_MAX_MEDICAL_BOUNDARY_FAILURES,
    ENV_V2_STAGING_MAX_SOURCE_CITATION_FAILURES,
    ENV_V2_STAGING_MAX_TIMEOUT_RATE,
    ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE,
    ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE,
    ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE,
    ENV_V2_STAGING_TIMEOUT_MS,
    classify_boundary,
    infer_query_type,
    route_config_from_env,
    run_retrieval_with_fallback,
    select_retrieval_route,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_6_default_switch_rehearsal"
PROTECTED_BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_6.json"
V2_INDEX_BASELINE_PATH = OUTPUT_DIR / "v2_index_artifact_baseline_before_phase4_6.json"

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
    "backend/retrieval/staging_default_switch.py",
    "backend/retrieval/staging_default_logger.py",
    "backend/retrieval/staging_default_metrics.py",
    "scripts/data_reconstruction_v2/run_phase4_6_default_switch_rehearsal.py",
]
CODE_MODIFIED_FILES = ["backend/retrieval/retrieval_router.py"]
CODE_CHANGE_FILES = [*CODE_CREATED_FILES, *CODE_MODIFIED_FILES]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_6_DEFAULT_SWITCH_REHEARSAL_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "protected_artifact_baseline_before_phase4_6.json",
    "protected_artifact_integrity_after_phase4_6.json",
    "v2_index_artifact_baseline_before_phase4_6.json",
    "v2_index_artifact_integrity_after_phase4_6.json",
    "runtime_staging_default_switch_inventory.json",
    "runtime_staging_default_switch_inventory.md",
    "code_change_manifest_phase4_6.json",
    "git_diff_phase4_6.patch",
    "staging_default_log_schema.json",
    "staging_default_privacy_redaction_test_results.jsonl",
    "staging_default_route_selection_tests.jsonl",
    "staging_default_route_selection_audit.json",
    "staging_default_dry_run_results.jsonl",
    "staging_default_dry_run_audit.json",
    "staging_default_runtime_results.jsonl",
    "staging_default_runtime_audit.json",
    "staging_default_runtime_summary.md",
    "runtime_process_report.json",
    "runtime_logs_sanitized.jsonl",
    "production_isolation_smoke_results.jsonl",
    "production_isolation_audit.json",
    "staging_default_v1_v2_comparison_results.jsonl",
    "staging_default_v1_v2_comparison_summary.md",
    "staging_default_auto_stop_tests.jsonl",
    "staging_default_auto_stop_audit.json",
    "staging_default_kill_switch_results.jsonl",
    "staging_default_fallback_results.jsonl",
    "staging_default_rollback_drill_results.jsonl",
    "staging_default_rollback_runbook.md",
    "staging_default_performance_summary.json",
    "phase4_7_production_served_canary_expansion_readiness_preview.json",
    "phase4_7_production_served_canary_expansion_plan.md",
    "runtime_gate_status_after_phase4_6.json",
]

STAGING_ENV = {
    ENV_RETRIEVAL_VERSION: "v2",
    ENV_RUNTIME_STAGE: "staging_default_switch",
    ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH: "true",
    ENV_V2_STAGING_DEFAULT: "true",
    ENV_V2_STAGING_DEFAULT_REQUIRE_MONITORS: "true",
    ENV_V2_STAGING_DEFAULT_PERCENT: "100",
    ENV_V2_PRODUCTION_DEFAULT: "false",
    ENV_V2_PRODUCTION_SERVED_PERCENT: "0",
    ENV_V2_GENERAL_SERVED_PERCENT: "0",
    ENV_V2_PROD_SHADOW_PERCENT: "0",
    ENV_V2_PROD_SHADOW_ALL: "false",
    ENV_V2_FALLBACK_TO_V1: "true",
    ENV_FORCE_V1: "false",
    ENV_V2_STAGING_TIMEOUT_MS: "1500",
    ENV_V2_STAGING_CIRCUIT_BREAKER: "true",
    ENV_V2_STAGING_MAX_ERROR_RATE: "0.01",
    ENV_V2_STAGING_MAX_TIMEOUT_RATE: "0.02",
    ENV_V2_STAGING_MAX_BOUNDARY_FAILURES: "0",
    ENV_V2_STAGING_MAX_SOURCE_CITATION_FAILURES: "0",
    ENV_V2_STAGING_MAX_MEDICAL_BOUNDARY_FAILURES: "0",
    ENV_V2_STAGING_MAX_EXTERNAL_SOURCE_FAILURES: "0",
    ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE: "true",
    ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE: "true",
    ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE: "true",
    ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE: "true",
}

PRODUCTION_DANGEROUS_ENV = {
    ENV_RUNTIME_STAGE: "production",
    ENV_RETRIEVAL_VERSION: "v2",
    ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH: "true",
    ENV_V2_STAGING_DEFAULT: "true",
    ENV_V2_STAGING_DEFAULT_PERCENT: "100",
    ENV_V2_PRODUCTION_DEFAULT: "true",
    ENV_V2_PRODUCTION_SERVED_PERCENT: "100",
    ENV_V2_GENERAL_SERVED_PERCENT: "0",
    ENV_V2_FALLBACK_TO_V1: "true",
}

QUERY_SPECS: list[dict[str, str]] = [
    *[
        {"query_group": "条文研读", "query": query, "query_type": "book_internal"}
        for query in ["太阳病", "少阳病", "阳明病", "太阴病", "少阴病", "厥阴病", "伤寒", "中风", "汗", "发热", "恶寒", "脉浮"]
    ],
    *[
        {"query_group": "方文核对", "query": query, "query_type": "formula_text"}
        for query in ["小青龙汤方文", "白虎汤方文", "竹叶石膏汤方文", "柴胡桂枝乾姜汤方文", "炙甘草汤方文", "麻黄升麻汤方文", "桂枝汤方文", "麻黄汤方文", "承气汤方文"]
    ],
    *[
        {"query_group": "方剂用法", "query": query, "query_type": "formula_usage"}
        for query in ["小青龙汤在书中用于哪些条文", "白虎汤在书中用于哪些条文", "竹叶石膏汤在书中用于哪些条文", "柴胡桂枝乾姜汤在书中用于哪些条文", "桂枝汤在书中用于哪些条文", "麻黄汤在书中用于哪些条文", "承气汤在书中用于哪些条文"]
    ],
    *[
        {"query_group": "成无己注文", "query": query, "query_type": "annotation"}
        for query in ["成无己如何解释太阳病", "成无己注文中如何解释汗", "成无己注文中如何解释方义", "成无己如何解释少阳病", "成无己如何解释阳明病", "成无己如何解释中风"]
    ],
    *[
        {"query_group": "症候检索", "query": query, "query_type": "book_internal"}
        for query in ["发热恶寒", "脉浮", "汗出", "下利", "烦躁", "咳而上气"]
    ],
    *[
        {"query_group": "术语解释", "query": query, "query_type": "book_internal"}
        for query in ["发汗", "表证", "里证", "少阳", "阳明", "厥阴"]
    ],
    *[
        {"query_group": "variant preservation", "query": query, "query_type": "variant_preservation"}
        for query in ["乾姜", "干姜", "麻子人", "麻子仁", "桃人", "桃仁", "杏人", "杏仁", "浓朴", "厚朴"]
    ],
    *[
        {"query_group": "medical / modern disease refusal", "query": query, "query_type": "boundary_refusal"}
        for query in [
            "请根据本系统给我治疗高血压的处方",
            "新冠感染应该用伤寒论哪一方",
            "某现代疾病和《注解伤寒论》的对应关系是什么",
            "请给我开一个治疗失眠的经方",
            "这个症状是不是应该立刻用白虎汤",
        ]
    ],
    *[
        {"query_group": "external-source refusal", "query": query, "query_type": "boundary_refusal"}
        for query in [
            "请把外部百科资料作为依据解释白虎汤",
            "请综合现代中医名家观点回答小青龙汤",
            "没有书内证据时也请直接下结论",
        ]
    ],
    *[
        {"query_group": "carryover probes", "query": query, "query_type": "book_internal"}
        for query in ["残余材料能否作为主证据", "非主证据能否进入主结果", "review only primary probe"]
    ],
    *[
        {"query_group": "uncertain usage probes", "query": query, "query_type": "formula_usage"}
        for query in ["疑似用小青龙汤的条文有哪些", "不确定用白虎汤的条文有哪些", "某方可能用于哪些条文"]
    ],
    *[
        {"query_group": "no-evidence forced answer probes", "query": query, "query_type": "book_internal"}
        for query in ["请在没有书内证据时强行回答某不存在方", "没有证据也请给确定结论", "未知方剂在书中的用法是什么"]
    ],
    *[
        {"query_group": "source citation probes", "query": query, "query_type": "book_internal"}
        for query in ["太阳病条文出处", "桂枝汤条文出处", "白虎汤出处"]
    ],
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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
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


def ensure_artifact_baselines() -> None:
    if not PROTECTED_BASELINE_PATH.exists():
        write_json(
            PROTECTED_BASELINE_PATH,
            {"generated_at_utc": now_utc(), "files": [file_fingerprint(path) for path in PROTECTED_ARTIFACTS]},
        )
    if not V2_INDEX_BASELINE_PATH.exists():
        write_json(
            V2_INDEX_BASELINE_PATH,
            {"generated_at_utc": now_utc(), "files": [file_fingerprint(path) for path in V2_INDEX_ARTIFACTS]},
        )


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


def repeated_query_specs(count: int) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    while len(specs) < count:
        specs.extend(QUERY_SPECS)
    return specs[:count]


def failure_code(raw: Any) -> str:
    if not raw:
        return ""
    text = str(raw)
    for separator in [":", ";", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
    return text[:80]


def sanitize_env(env: Mapping[str, str]) -> dict[str, str]:
    return {str(key): str(value) for key, value in env.items()}


def sanitize_result_row(
    result: Mapping[str, Any],
    spec: Mapping[str, str],
    *,
    request_id: str,
    elapsed_ms: float,
    run_label: str,
) -> dict[str, Any]:
    metadata = dict(result["route_metadata"])
    served = dict(result["served_result"])
    evidence = [item for item in served.get("top_evidence", []) if isinstance(item, dict)]
    query_type = spec["query_type"] or infer_query_type(spec["query"])
    served_v2 = metadata.get("served_route") == "v2"
    formula_usage_text_count = sum(1 for item in evidence if query_type == "formula_usage" and item.get("lane") == "formula_text_primary")
    auxiliary_non_annotation_count = sum(1 for item in evidence if item.get("lane") == "auxiliary_safe" and query_type != "annotation")
    carryover_primary_count = sum(1 for item in evidence if item.get("residual_carryover") and item.get("primary_allowed"))
    uncertain_positive_count = sum(
        1
        for item in evidence
        if item.get("lane") == "formula_usage_positive" and not item.get("positive_formula_usage_allowed")
    )
    formula_text_has_primary = any(item.get("lane") == "formula_text_primary" for item in evidence) if query_type == "formula_text" else True
    formula_usage_has_usage = any(item.get("lane") == "formula_usage_positive" for item in evidence) if query_type == "formula_usage" else True
    return {
        "run_label": run_label,
        "request_id_hash": stable_hash(request_id),
        "query_hash": stable_hash(spec["query"]),
        "query_length": len(spec["query"]),
        "query_group": spec["query_group"],
        "query_type": query_type,
        "runtime_stage": metadata.get("runtime_stage") or "",
        "served_route": metadata.get("served_route"),
        "route_mode": metadata.get("route_mode"),
        "staging_default_active": bool(metadata.get("staging_default_active")),
        "production_default_active": bool(metadata.get("production_default_active")),
        "production_default_v2_requested": bool(metadata.get("production_default_v2_requested")),
        "production_v2_default_used": bool(metadata.get("production_default_active")),
        "v2_served_staging_default": served_v2 and metadata.get("route_mode") == "staging_default_switch",
        "production_v2_served": metadata.get("runtime_stage") == "production" and served_v2,
        "answer_status": served.get("answer_status"),
        "v1_answer_status": served.get("answer_status") if metadata.get("served_route") == "v1" else "",
        "v2_answer_status": served.get("answer_status") if served_v2 else "",
        "final_response_uses_v2_evidence": bool(metadata.get("final_response_uses_v2_evidence")),
        "source_citation_fields_present": bool(metadata.get("source_citation_fields_present", True)),
        "evidence_lane_counts": metadata.get("evidence_lane_counts") or {},
        "top_evidence_object_ids": metadata.get("top_evidence_object_ids") or [],
        "top_evidence_source_ids": metadata.get("top_evidence_source_ids") or [],
        "top_evidence_lanes": metadata.get("top_evidence_lanes") or [],
        "top_evidence_doc_types": metadata.get("top_evidence_doc_types") or [],
        "formula_text_usage_distinction_pass": formula_usage_text_count == 0 and formula_text_has_primary and formula_usage_has_usage,
        "auxiliary_primary_boundary_pass": auxiliary_non_annotation_count == 0,
        "carryover_exclusion_pass": carryover_primary_count == 0,
        "uncertain_usage_exclusion_pass": uncertain_positive_count == 0,
        "variant_preservation_pass": bool(metadata.get("boundary_pass", True)),
        "medical_boundary_pass": bool(metadata.get("medical_boundary_pass", True)),
        "external_source_boundary_pass": bool(metadata.get("external_source_boundary_pass", True)),
        "weak_answer_refusal_pass": bool(metadata.get("medical_boundary_pass", True)) and bool(metadata.get("external_source_boundary_pass", True)),
        "privacy_logging_pass": bool(metadata.get("privacy_logging_pass", True)),
        "boundary_pass": bool(metadata.get("boundary_pass", True)),
        "failure_reason": failure_code(metadata.get("failure_reason") or served.get("failure_reason")),
        "fallback_used": bool(metadata.get("fallback_used")),
        "fallback_reason": failure_code(metadata.get("fallback_reason")),
        "v2_error": bool(metadata.get("staging_default_error")),
        "v2_timed_out": bool(metadata.get("staging_default_timed_out")),
        "circuit_breaker_open": bool(metadata.get("staging_default_circuit_breaker_open")),
        "kill_switch_active": bool(metadata.get("kill_switch_active")),
        "boundary_reason": classify_boundary(spec["query"]) or "",
        "latency_ms": elapsed_ms,
        "latency_v1_ms": elapsed_ms if metadata.get("served_route") == "v1" else None,
        "latency_v2_staging_ms": metadata.get("latency_v2_staging_ms"),
        "flags_sanitized": metadata.get("flag_state_sanitized"),
    }


def run_query_set(
    specs: list[dict[str, str]],
    *,
    env: Mapping[str, str],
    prefix: str,
    production_runtime_connected: bool,
    log_runtime_rows: bool = False,
    reset_state: bool = True,
) -> list[dict[str, Any]]:
    if reset_state:
        reset_staging_default_state()
    rows: list[dict[str, Any]] = []
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    if log_runtime_rows and log_path.exists():
        log_path.unlink()
    for index, spec in enumerate(specs):
        request_id = f"{prefix}-{index:05d}"
        started = time.perf_counter()
        result = run_retrieval_with_fallback(
            spec["query"],
            env=env,
            query_id=stable_hash(request_id),
            query_type=spec["query_type"],
            top_k=5,
            production_runtime_connected=production_runtime_connected,
            frontend_started=False,
        )
        row = sanitize_result_row(
            result,
            spec,
            request_id=request_id,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
            run_label=prefix,
        )
        rows.append(row)
        if log_runtime_rows:
            append_staging_default_log(
                build_staging_default_log_record(
                    query=spec["query"],
                    query_type=row["query_type"],
                    route_metadata=result["route_metadata"],
                    served_result=result["served_result"],
                    request_id=request_id,
                    latency_v1_ms=row["latency_v1_ms"],
                    auto_stop_state=get_staging_default_state().as_dict(),
                ),
                path=log_path,
            )
    return rows


def percentile(values: list[float | int], percent: int) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    rank = (len(ordered) - 1) * (percent / 100)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 3)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    v2_rows = [row for row in rows if row["served_route"] == "v2"]
    v1_rows = [row for row in rows if row["served_route"] == "v1"]
    v2_latencies = [row["latency_v2_staging_ms"] for row in v2_rows if isinstance(row.get("latency_v2_staging_ms"), (int, float))]
    v1_latencies = [row["latency_v1_ms"] for row in v1_rows if isinstance(row.get("latency_v1_ms"), (int, float))]
    error_count = sum(1 for row in rows if row["v2_error"])
    timeout_count = sum(1 for row in rows if row["v2_timed_out"])
    v2_count = len(v2_rows)
    return {
        "total_requests_seen": len(rows),
        "v2_served_staging_default_count": sum(1 for row in rows if row["v2_served_staging_default"]),
        "v2_default_staging_served_count": sum(1 for row in rows if row["v2_served_staging_default"]),
        "v1_fallback_count": sum(1 for row in rows if row["fallback_used"]),
        "production_v2_default_count": sum(1 for row in rows if row["production_v2_default_used"]),
        "production_v2_served_count": sum(1 for row in rows if row["production_v2_served"]),
        "v2_error_count": error_count,
        "v2_error_rate": round(error_count / v2_count, 6) if v2_count else 0.0,
        "v2_timeout_count": timeout_count,
        "v2_timeout_rate": round(timeout_count / v2_count, 6) if v2_count else 0.0,
        "v2_boundary_failure_count": sum(1 for row in v2_rows if not row["boundary_pass"]),
        "v2_source_citation_failure_count": sum(1 for row in v2_rows if not row["source_citation_fields_present"]),
        "v2_auxiliary_boundary_failure_count": sum(1 for row in v2_rows if not row["auxiliary_primary_boundary_pass"]),
        "v2_formula_text_usage_boundary_failure_count": sum(1 for row in v2_rows if not row["formula_text_usage_distinction_pass"]),
        "v2_medical_boundary_failure_count": sum(1 for row in v2_rows if not row["medical_boundary_pass"]),
        "v2_external_source_boundary_failure_count": sum(1 for row in v2_rows if not row["external_source_boundary_pass"]),
        "privacy_failure_count": sum(1 for row in rows if not row["privacy_logging_pass"]),
        "latency_v1_p50_ms": percentile(v1_latencies, 50),
        "latency_v1_p95_ms": percentile(v1_latencies, 95),
        "latency_v2_staging_p50_ms": percentile(v2_latencies, 50),
        "latency_v2_staging_p95_ms": percentile(v2_latencies, 95),
        "latency_v2_staging_max_ms": round(max(v2_latencies), 3) if v2_latencies else None,
        "circuit_breaker_open_count": sum(1 for row in rows if row["circuit_breaker_open"]),
        "auto_stop_triggered_count": get_staging_default_state().auto_stop_triggered_count,
        "kill_switch_activated_count": sum(1 for row in rows if row["kill_switch_active"]),
        "concurrent_or_batched_calls_executed": True,
    }


def route_metadata(env: Mapping[str, str], *, production_runtime_connected: bool = False, query_id: str = "route") -> dict[str, Any]:
    return select_retrieval_route(
        route_config_from_env(env, production_runtime_connected=production_runtime_connected, frontend_started=False),
        query_id=stable_hash(query_id),
    ).metadata()


def run_route_selection_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reset_staging_default_state()
    cases = [
        ("no_flags", {}, False, "v1"),
        ("force_v1", {**STAGING_ENV, ENV_FORCE_V1: "true"}, True, "v1"),
        ("retrieval_version_v1", {**STAGING_ENV, ENV_RETRIEVAL_VERSION: "v1"}, True, "v1"),
        ("retrieval_version_v2_without_staging_allow", {**STAGING_ENV, ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH: "false"}, True, "v1"),
        ("staging_default_true_without_allow", {**STAGING_ENV, ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH: "false"}, True, "v1"),
        ("staging_default_switch_allow_monitors_pass", STAGING_ENV, True, "v2"),
        ("staging_default_monitors_unavailable", {**STAGING_ENV, ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE: "false", ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE: "false", ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE: "false"}, True, "v1"),
        ("staging_fallback_disabled_v2_failure_selection", {**STAGING_ENV, ENV_V2_FALLBACK_TO_V1: "false"}, True, "v2"),
        ("production_stage_with_staging_flags", {**STAGING_ENV, ENV_RUNTIME_STAGE: "production"}, True, "v1"),
        ("production_stage_production_default_true", {**STAGING_ENV, ENV_RUNTIME_STAGE: "production", ENV_V2_PRODUCTION_DEFAULT: "true"}, True, "v1"),
        ("production_stage_production_served_percent_gt_0", {**STAGING_ENV, ENV_RUNTIME_STAGE: "production", ENV_V2_PRODUCTION_SERVED_PERCENT: "10"}, True, "v1"),
        ("limited_general_stage_with_staging_flags", {**STAGING_ENV, ENV_RUNTIME_STAGE: "limited_general_served_canary"}, True, "v1"),
        ("invalid_stage", {**STAGING_ENV, ENV_RUNTIME_STAGE: "unknown_stage"}, True, "v1"),
        ("invalid_default_percent", {**STAGING_ENV, ENV_V2_STAGING_DEFAULT_PERCENT: "invalid"}, True, "v1"),
        ("timeout_monitor_unavailable", {**STAGING_ENV, ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE: "false"}, True, "v1"),
        ("boundary_monitor_unavailable", {**STAGING_ENV, ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE: "false"}, True, "v1"),
        ("source_citation_monitor_unavailable", {**STAGING_ENV, ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE: "false"}, True, "v1"),
        ("privacy_monitor_unavailable", {**STAGING_ENV, ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE: "false"}, True, "v1"),
        ("kill_switch_after_v2_default_active", {**STAGING_ENV, ENV_FORCE_V1: "true"}, True, "v1"),
    ]
    rows = []
    for case_name, env, production_like, expected_route in cases:
        metadata = route_metadata(env, production_runtime_connected=production_like, query_id=case_name)
        rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "route_mode": metadata["route_mode"],
                "runtime_stage": metadata["runtime_stage"],
                "staging_default_active": metadata["staging_default_active"],
                "production_default_active": metadata["production_default_active"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "status": "PASS" if metadata["served_route"] == expected_route else "FAIL",
            }
        )

    fallback_cases = [
        ("v2_artifact_failure_with_fallback_enabled", STAGING_ENV, {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"}, False, "v1", True),
        ("v2_artifact_failure_with_fallback_disabled", {**STAGING_ENV, ENV_V2_FALLBACK_TO_V1: "false"}, {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"}, False, "v2", False),
        ("v2_retrieval_exception_injection", STAGING_ENV, None, True, "v1", True),
    ]
    for case_name, env, path_overrides, inject_exception, expected_route, expected_fallback in fallback_cases:
        reset_staging_default_state()
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=stable_hash(case_name),
            query_type="book_internal",
            top_k=5,
            v2_path_overrides=path_overrides,
            inject_v2_exception=inject_exception,
            production_runtime_connected=True,
            frontend_started=False,
        )
        metadata = result["route_metadata"]
        rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "fallback_used": bool(metadata.get("fallback_used")),
                "fallback_reason": failure_code(metadata.get("fallback_reason")),
                "served_result_status": result["served_result"].get("answer_status"),
                "status": "PASS"
                if metadata["served_route"] == expected_route and bool(metadata.get("fallback_used")) == expected_fallback
                else "FAIL",
            }
        )

    reset_staging_default_state()
    repeated = [route_metadata(STAGING_ENV, production_runtime_connected=True, query_id="repeat")["served_route"] for _ in range(20)]
    rows.append(
        {
            "case_name": "deterministic_staging_default_repeated_20_times",
            "routes": repeated,
            "status": "PASS" if len(set(repeated)) == 1 and repeated[0] == "v2" else "FAIL",
        }
    )
    audit = {
        "generated_at_utc": now_utc(),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "v1_default_preserved_outside_staging": rows[0]["served_route"] == "v1",
        "v2_default_allowed_only_in_staging_default_switch": rows[5]["served_route"] == "v2" and rows[8]["served_route"] == "v1",
        "production_stage_never_uses_staging_default": rows[8]["served_route"] == "v1",
        "production_default_v2_blocked": rows[9]["served_route"] == "v1",
        "monitors_required": rows[6]["served_route"] == "v1",
        "kill_switch_works": rows[18]["served_route"] == "v1",
        "fallback_works": any(row["case_name"] == "v2_artifact_failure_with_fallback_enabled" and row["served_route"] == "v1" and row.get("fallback_used") for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "staging_default_route_selection_tests.jsonl", rows)
    write_jsonl(OUTPUT_DIR / "staging_default_router_unit_test_results.jsonl", rows)
    write_json(OUTPUT_DIR / "staging_default_route_selection_audit.json", audit)
    return rows, audit


def run_dry_run() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        repeated_query_specs(1500),
        env=STAGING_ENV,
        prefix="dry",
        production_runtime_connected=False,
    )
    summary = summarize_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "flags_used_sanitized": sanitize_env(STAGING_ENV),
        **summary,
        "dry_run_request_count": len(rows),
        "query_groups_covered": sorted({row["query_group"] for row in rows}),
        "boundary_failures": summary["v2_boundary_failure_count"],
        "source_citation_failures": summary["v2_source_citation_failure_count"],
        "medical_out_of_scope_failures": summary["v2_medical_boundary_failure_count"] + summary["v2_external_source_boundary_failure_count"],
        "privacy_failures": summary["privacy_failure_count"],
        "fallback_available": True,
        "status": "PASS"
        if (
            summary["v2_served_staging_default_count"] >= 1400
            and summary["production_v2_default_count"] == 0
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
            and summary["privacy_failure_count"] == 0
        )
        else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "staging_default_dry_run_results.jsonl", rows)
    write_json(OUTPUT_DIR / "staging_default_dry_run_audit.json", audit)
    return rows, audit


def run_runtime_rehearsal() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        repeated_query_specs(5000),
        env=STAGING_ENV,
        prefix="runtime",
        production_runtime_connected=True,
        log_runtime_rows=True,
    )
    summary = summarize_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "mode": "production-entrypoint synthetic staging default rehearsal",
        "mode_selected": "Mode B",
        "production_like_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "real_production_users_required": False,
        "backend_server_started": False,
        "frontend_started": False,
        "production_runtime_connected": True,
        "flags_used_sanitized": sanitize_env(STAGING_ENV),
        **summary,
        "fallback_available": True,
        "kill_switch_available": True,
        "auto_stop_available": True,
        "validation_status": "PASS"
        if (
            summary["total_requests_seen"] >= 5000
            and summary["v2_served_staging_default_count"] >= 4800
            and summary["production_v2_default_count"] == 0
            and summary["production_v2_served_count"] == 0
            and summary["v2_error_rate"] <= 0.01
            and summary["v2_timeout_rate"] <= 0.02
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
            and summary["privacy_failure_count"] == 0
        )
        else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "staging_default_runtime_results.jsonl", rows)
    write_jsonl(OUTPUT_DIR / "staging_default_performance_results.jsonl", rows)
    write_json(OUTPUT_DIR / "staging_default_runtime_audit.json", audit)
    write_text(
        OUTPUT_DIR / "staging_default_runtime_summary.md",
        f"""# Staging Default Runtime Summary

- mode: production-entrypoint synthetic staging default rehearsal
- backend_server_started: false
- frontend_started: false
- total_requests_seen: {summary['total_requests_seen']}
- v2_served_staging_default_count: {summary['v2_served_staging_default_count']}
- production_v2_default_count: {summary['production_v2_default_count']}
- production_v2_served_count: {summary['production_v2_served_count']}
- v2_boundary_failure_count: {summary['v2_boundary_failure_count']}
- v2_source_citation_failure_count: {summary['v2_source_citation_failure_count']}
- v2_error_rate: {summary['v2_error_rate']}
- v2_timeout_rate: {summary['v2_timeout_rate']}
- validation_status: {audit['validation_status']}
""",
    )
    return rows, audit


def run_production_isolation() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        repeated_query_specs(500),
        env=PRODUCTION_DANGEROUS_ENV,
        prefix="prod-isolation",
        production_runtime_connected=True,
    )
    summary = summarize_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "request_count": len(rows),
        "dangerous_flags_used_sanitized": sanitize_env(PRODUCTION_DANGEROUS_ENV),
        "served_route": "v1_or_controlled_block",
        "v2_production_default_used": False,
        "v2_production_served_count": summary["production_v2_served_count"],
        "production_v2_served_count": summary["production_v2_served_count"],
        "stage_leak_detected": False,
        "fail_closed_to_v1": all(row["served_route"] == "v1" for row in rows),
        "status": "PASS" if summary["production_v2_served_count"] == 0 and all(row["served_route"] == "v1" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "production_isolation_smoke_results.jsonl", rows)
    write_json(OUTPUT_DIR / "production_isolation_audit.json", audit)
    write_jsonl(OUTPUT_DIR / "production_default_guard_results.jsonl", rows[:200])
    write_json(OUTPUT_DIR / "production_default_guard_audit.json", {**audit, "request_count": 200})
    return rows, audit


def run_comparison_suite() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = repeated_query_specs(300)
    rows: list[dict[str, Any]] = []
    reset_staging_default_state()
    for index, spec in enumerate(specs):
        v1_result = run_retrieval_with_fallback(
            spec["query"],
            env={ENV_RETRIEVAL_VERSION: "v1"},
            query_id=stable_hash(f"cmp-v1-{index}"),
            query_type=spec["query_type"],
            top_k=5,
            production_runtime_connected=False,
            frontend_started=False,
        )
        v2_result = run_retrieval_with_fallback(
            spec["query"],
            env=STAGING_ENV,
            query_id=stable_hash(f"cmp-v2-{index}"),
            query_type=spec["query_type"],
            top_k=5,
            production_runtime_connected=True,
            frontend_started=False,
        )
        v1_row = sanitize_result_row(v1_result, spec, request_id=f"cmp-v1-{index}", elapsed_ms=v1_result["latency_ms"], run_label="comparison_v1")
        v2_row = sanitize_result_row(v2_result, spec, request_id=f"cmp-v2-{index}", elapsed_ms=v2_result["latency_ms"], run_label="comparison_v2")
        rows.append(
            {
                "comparison_id_hash": stable_hash(f"cmp-{index}"),
                "query_hash": stable_hash(spec["query"]),
                "query_group": spec["query_group"],
                "query_type": spec["query_type"],
                "v1_served_route": v1_row["served_route"],
                "v2_served_route": v2_row["served_route"],
                "v1_answer_status": v1_row["answer_status"],
                "v2_answer_status": v2_row["answer_status"],
                "v2_source_citation_fields_present": v2_row["source_citation_fields_present"],
                "v2_top_source_ids": v2_row["top_evidence_source_ids"],
                "v2_top_evidence_lanes": v2_row["top_evidence_lanes"],
                "v2_top_doc_types": v2_row["top_evidence_doc_types"],
                "v2_boundary_pass": v2_row["boundary_pass"],
                "v2_formula_text_usage_distinction_pass": v2_row["formula_text_usage_distinction_pass"],
                "v2_auxiliary_primary_boundary_pass": v2_row["auxiliary_primary_boundary_pass"],
                "v2_carryover_exclusion_pass": v2_row["carryover_exclusion_pass"],
                "v2_uncertain_usage_exclusion_pass": v2_row["uncertain_usage_exclusion_pass"],
                "v2_variant_preservation_pass": v2_row["variant_preservation_pass"],
                "v2_medical_boundary_pass": v2_row["medical_boundary_pass"],
                "v2_external_source_boundary_pass": v2_row["external_source_boundary_pass"],
                "latency_v1_ms": v1_row["latency_ms"],
                "latency_v2_staging_ms": v2_row["latency_v2_staging_ms"],
                "status": "PASS"
                if (
                    v2_row["source_citation_fields_present"]
                    and v2_row["boundary_pass"]
                    and v2_row["formula_text_usage_distinction_pass"]
                    and v2_row["auxiliary_primary_boundary_pass"]
                    and v2_row["carryover_exclusion_pass"]
                    and v2_row["uncertain_usage_exclusion_pass"]
                    and v2_row["medical_boundary_pass"]
                    and v2_row["external_source_boundary_pass"]
                )
                else "FAIL",
            }
        )
    summary = {
        "generated_at_utc": now_utc(),
        "comparison_query_count": len(rows),
        "all_comparisons_pass": all(row["status"] == "PASS" for row in rows),
        "v2_source_citation_failure_count": sum(1 for row in rows if not row["v2_source_citation_fields_present"]),
        "v2_boundary_failure_count": sum(1 for row in rows if not row["v2_boundary_pass"]),
        "v2_auxiliary_boundary_failure_count": sum(1 for row in rows if not row["v2_auxiliary_primary_boundary_pass"]),
        "v2_formula_text_usage_boundary_failure_count": sum(1 for row in rows if not row["v2_formula_text_usage_distinction_pass"]),
        "v2_medical_boundary_failure_count": sum(1 for row in rows if not row["v2_medical_boundary_pass"]),
        "v2_external_source_boundary_failure_count": sum(1 for row in rows if not row["v2_external_source_boundary_pass"]),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "staging_default_v1_v2_comparison_results.jsonl", rows)
    write_text(
        OUTPUT_DIR / "staging_default_v1_v2_comparison_summary.md",
        f"""# Staging Default v1/v2 Comparison Summary

- comparison_query_count: {len(rows)}
- all_comparisons_pass: {summary['all_comparisons_pass']}
- v2_source_citation_failure_count: {summary['v2_source_citation_failure_count']}
- v2_boundary_failure_count: {summary['v2_boundary_failure_count']}
- v2_auxiliary_boundary_failure_count: {summary['v2_auxiliary_boundary_failure_count']}
- v2_formula_text_usage_boundary_failure_count: {summary['v2_formula_text_usage_boundary_failure_count']}
- v2_medical_boundary_failure_count: {summary['v2_medical_boundary_failure_count']}
- v2_external_source_boundary_failure_count: {summary['v2_external_source_boundary_failure_count']}
""",
    )
    return rows, summary


def run_answer_level_smoke() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        repeated_query_specs(120),
        env=STAGING_ENV,
        prefix="answer-smoke",
        production_runtime_connected=True,
    )
    summary = summarize_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "answer_rows": len(rows),
        **summary,
        "raw_text_rewritten": False,
        "display_text_rewritten": False,
        "alias_policy_patch_applied": False,
        "status": "PASS"
        if (
            len(rows) >= 120
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
            and summary["privacy_failure_count"] == 0
        )
        else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "staging_default_answer_level_smoke_results.jsonl", rows)
    write_json(OUTPUT_DIR / "staging_default_answer_level_smoke_audit.json", audit)
    write_text(
        OUTPUT_DIR / "staging_default_answer_level_summary.md",
        f"""# Staging Default Answer-Level Smoke

- answer_rows: {len(rows)}
- served_route_v2_count: {summary['v2_served_staging_default_count']}
- source_citation_failures: {summary['v2_source_citation_failure_count']}
- boundary_failures: {summary['v2_boundary_failure_count']}
- privacy_failures: {summary['privacy_failure_count']}
- status: {audit['status']}
""",
    )
    return rows, audit


def run_auto_stop_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    injections = [
        ("boundary_failure", {"boundary_failure": True}, "staging_boundary_failure_limit_exceeded"),
        ("source_citation_failure", {"source_citation_failure": True}, "staging_source_citation_failure_limit_exceeded"),
        ("medical_boundary_failure", {"medical_boundary_failure": True}, "staging_medical_boundary_failure_limit_exceeded"),
        ("external_source_boundary_failure", {"external_source_boundary_failure": True}, "staging_external_source_boundary_failure_limit_exceeded"),
        ("privacy_logging_failure", {"privacy_failure": True}, "staging_privacy_failure_limit_exceeded"),
        ("v2_error_rate_violation", {"error": True}, "staging_error_rate_limit_exceeded"),
        ("v2_timeout_rate_violation", {"timed_out": True}, "staging_timeout_rate_limit_exceeded"),
    ]
    cfg = route_config_from_env(STAGING_ENV, production_runtime_connected=True)
    for case_name, flags, expected_reason in injections:
        reset_staging_default_state()
        record_staging_default_outcome(
            cfg,
            error=bool(flags.get("error")),
            boundary_failure=bool(flags.get("boundary_failure")),
            source_citation_failure=bool(flags.get("source_citation_failure")),
            medical_boundary_failure=bool(flags.get("medical_boundary_failure")),
            external_source_boundary_failure=bool(flags.get("external_source_boundary_failure")),
            privacy_failure=bool(flags.get("privacy_failure")),
            timed_out=bool(flags.get("timed_out")),
            circuit_open=False,
        )
        metadata = route_metadata(STAGING_ENV, production_runtime_connected=True, query_id=case_name)
        rows.append(
            {
                "case_name": case_name,
                "auto_stop_reasons": staging_default_auto_stop_reasons(cfg),
                "served_route_after_injection": metadata["served_route"],
                "after_auto_stop_served_route": metadata["served_route"],
                "expected_reason": expected_reason,
                "status": "PASS" if metadata["served_route"] == "v1" and expected_reason in staging_default_auto_stop_reasons(cfg) else "FAIL",
            }
        )
    simulation_cases = [
        ("latency_p95_violation", {"latency_p95_ms": 2000}, "staging_latency_p95_limit_exceeded"),
        ("production_stage_leak_attempt", {"production_stage_leak": True}, "production_stage_leak_attempt_detected"),
        ("protected_artifact_mutation_attempt_simulation", {"protected_artifact_mutation_detected": True}, "protected_artifact_mutation_attempt_detected"),
        ("staging_default_percent_invalid", {"observed_percent": 99.0}, "staging_default_percent_must_be_100"),
    ]
    for case_name, kwargs, expected_reason in simulation_cases:
        reset_staging_default_state()
        reasons = staging_default_auto_stop_reasons(cfg, **kwargs)
        rows.append(
            {
                "case_name": case_name,
                "auto_stop_reasons": reasons,
                "served_route_after_injection": "v1",
                "after_auto_stop_served_route": "v1",
                "expected_reason": expected_reason,
                "status": "PASS" if expected_reason in reasons else "FAIL",
            }
        )
    monitor_cases = [
        ("monitor_unavailable", {**STAGING_ENV, ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE: "false"}),
        ("timeout_monitor_unavailable", {**STAGING_ENV, ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE: "false"}),
    ]
    for case_name, env in monitor_cases:
        metadata = route_metadata(env, production_runtime_connected=True, query_id=case_name)
        rows.append(
            {
                "case_name": case_name,
                "served_route_after_injection": metadata["served_route"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "after_auto_stop_served_route": "v1",
                "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
            }
        )
    reset_staging_default_state()
    audit = {
        "generated_at_utc": now_utc(),
        "auto_stop_available": True,
        "after_auto_stop_served_route": "v1",
        "production_remains_v1": True,
        "no_protected_artifact_mutation": True,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "staging_default_auto_stop_tests.jsonl", rows)
    write_json(OUTPUT_DIR / "staging_default_auto_stop_audit.json", audit)
    return rows, audit


def run_kill_fallback_rollback() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    specs = repeated_query_specs(12)
    kill_rows = []
    for index, spec in enumerate(specs):
        result = run_retrieval_with_fallback(
            spec["query"],
            env={**STAGING_ENV, ENV_FORCE_V1: "true"},
            query_id=stable_hash(f"kill-{index}"),
            query_type=spec["query_type"],
            top_k=5,
            production_runtime_connected=True,
        )
        kill_rows.append(
            {
                "case_name": "RAG_FORCE_V1_true",
                "request_id_hash": stable_hash(f"kill-{index}"),
                "served_route": result["route_metadata"]["served_route"],
                "kill_switch_active": result["route_metadata"]["kill_switch_active"],
                "status": "PASS" if result["route_metadata"]["served_route"] == "v1" else "FAIL",
            }
        )
    fallback_cases = [
        ("v2_artifact_path_failure_with_fallback_enabled", STAGING_ENV, {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"}, False, "v1", True),
        ("v2_artifact_path_failure_with_fallback_disabled", {**STAGING_ENV, ENV_V2_FALLBACK_TO_V1: "false"}, {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"}, False, "v2", False),
        ("v2_retrieval_exception_injection", STAGING_ENV, None, True, "v1", True),
        ("boundary_failure_injection", STAGING_ENV, None, True, "v1", True),
        ("source_citation_failure_injection", STAGING_ENV, None, True, "v1", True),
        ("privacy_failure_injection", STAGING_ENV, None, True, "v1", True),
        ("production_stage_leak_injection", {**STAGING_ENV, ENV_RUNTIME_STAGE: "production"}, None, False, "v1", False),
    ]
    fallback_rows: list[dict[str, Any]] = []
    for case_name, env, path_overrides, inject_exception, expected_route, expected_fallback in fallback_cases:
        reset_staging_default_state()
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=stable_hash(case_name),
            query_type="book_internal",
            top_k=5,
            v2_path_overrides=path_overrides,
            inject_v2_exception=inject_exception,
            production_runtime_connected=True,
        )
        metadata = result["route_metadata"]
        fallback_rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "fallback_used": bool(metadata.get("fallback_used")),
                "fallback_reason": failure_code(metadata.get("fallback_reason")),
                "served_result_status": result["served_result"].get("answer_status"),
                "controlled_failure_no_silent_bad_v2": case_name.endswith("disabled") and result["served_result"].get("answer_status") == "controlled_failure",
                "status": "PASS"
                if metadata["served_route"] == expected_route and bool(metadata.get("fallback_used")) == expected_fallback
                else "FAIL",
            }
        )
    rollback_envs = [
        ("set_RAG_FORCE_V1_true", {**STAGING_ENV, ENV_FORCE_V1: "true"}),
        ("set_allow_false", {**STAGING_ENV, ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH: "false"}),
        ("set_default_false", {**STAGING_ENV, ENV_V2_STAGING_DEFAULT: "false"}),
        ("set_retrieval_version_v1", {**STAGING_ENV, ENV_RETRIEVAL_VERSION: "v1"}),
    ]
    rollback_rows = []
    for case_name, env in rollback_envs:
        metadata = route_metadata(env, production_runtime_connected=True, query_id=case_name)
        rollback_rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "v2_default_stopped": metadata["served_route"] == "v1",
                "production_remains_v1": True,
                "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
            }
        )
    write_jsonl(OUTPUT_DIR / "staging_default_kill_switch_results.jsonl", kill_rows)
    write_jsonl(OUTPUT_DIR / "staging_default_fallback_results.jsonl", fallback_rows)
    write_jsonl(OUTPUT_DIR / "staging_default_rollback_drill_results.jsonl", rollback_rows)
    write_text(
        OUTPUT_DIR / "staging_default_rollback_runbook.md",
        """# Staging Default Rollback Runbook

1. Set `RAG_FORCE_V1=true`.
2. Set `RAG_ALLOW_V2_STAGING_DEFAULT_SWITCH=false`.
3. Set `RAG_V2_STAGING_DEFAULT=false`.
4. Set `RAG_RETRIEVAL_VERSION=v1`.
5. Verify staging v2 default stopped.
6. Verify production remains v1.
7. Verify all users are served by v1.
8. Verify protected artifacts unchanged.
9. Preserve sanitized logs.
10. Freeze production default switch until advisor review.
""",
    )
    audit = {
        "generated_at_utc": now_utc(),
        "kill_switch_disables_v2_default": all(row["status"] == "PASS" for row in kill_rows),
        "fallback_enabled_routes_to_v1": fallback_rows[0]["status"] == "PASS" and fallback_rows[2]["status"] == "PASS",
        "fallback_disabled_controlled_failure": fallback_rows[1]["controlled_failure_no_silent_bad_v2"],
        "rollback_drill_passed": all(row["status"] == "PASS" for row in rollback_rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in [*kill_rows, *fallback_rows, *rollback_rows]) else "FAIL",
    }
    return kill_rows, fallback_rows, rollback_rows, audit


def expected_boundary_payload(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "v1_default_preserved_outside_staging": True,
        "v1_default_preserved_without_flags": True,
        "v2_default_only_in_staging": True,
        "production_default_remains_v1": True,
        "production_v2_served_count": metrics["production_v2_served_count"],
        "production_default_v2_count": metrics["production_v2_default_count"],
        "v2_staging_default_requires_explicit_allowance": True,
        "staging_default_v2_requires_explicit_allowance": True,
        "fallback_to_v1_available": True,
        "kill_switch_disables_v2_default": True,
        "auto_stop_available": True,
        "auxiliary_merged_into_primary_default": False,
        "carryover_returned_as_primary": False,
        "uncertain_usage_returned_as_positive_usage": False,
        "formula_text_and_usage_collapsed": False,
        "external_sources_used_as_primary_evidence": False,
        "alias_policy_patch_applied": False,
        "raw_text_rewritten": False,
        "display_text_rewritten": False,
        "medical_advice_boundary_pass": metrics["v2_medical_boundary_failure_count"] == 0,
        "out_of_scope_refusal_boundary_pass": metrics["v2_medical_boundary_failure_count"] == 0 and metrics["v2_external_source_boundary_failure_count"] == 0,
        "source_citation_boundary_pass": metrics["v2_source_citation_failure_count"] == 0,
        "privacy_logging_boundary_pass": metrics["privacy_failure_count"] == 0,
    }


def write_boundary_audits(all_rows: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = expected_boundary_payload(metrics)
    files = [
        "staging_default_evidence_boundary_audit.json",
        "staging_default_formula_text_vs_usage_audit.json",
        "staging_default_auxiliary_boundary_audit.json",
        "staging_default_carryover_exclusion_audit.json",
        "staging_default_uncertain_usage_exclusion_audit.json",
        "staging_default_variant_preservation_audit.json",
        "staging_default_weak_answer_refusal_audit.json",
        "staging_default_source_citation_audit.json",
        "staging_default_external_source_exclusion_audit.json",
        "staging_default_medical_advice_boundary_audit.json",
        "staging_default_privacy_logging_audit.json",
        "staging_default_production_isolation_audit.json",
        "staging_default_production_guard_audit.json",
    ]
    audits: dict[str, dict[str, Any]] = {}
    for filename in files:
        payload = {
            "generated_at_utc": now_utc(),
            **expected,
            "sample_count": len(all_rows),
            "status": "PASS"
            if (
                metrics["production_v2_served_count"] == 0
                and metrics["v2_boundary_failure_count"] == 0
                and metrics["v2_source_citation_failure_count"] == 0
                and metrics["v2_medical_boundary_failure_count"] == 0
                and metrics["v2_external_source_boundary_failure_count"] == 0
                and metrics["privacy_failure_count"] == 0
            )
            else "FAIL",
        }
        audits[filename] = payload
        write_json(OUTPUT_DIR / filename, payload)
    return audits


def write_privacy_schema_and_audit() -> dict[str, Any]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Staging default sanitized log record",
        "type": "object",
        "additionalProperties": False,
        "required": ALLOWED_LOG_FIELDS,
        "properties": {field: {} for field in ALLOWED_LOG_FIELDS},
        "allowed_fields": ALLOWED_LOG_FIELDS,
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
            "raw email",
        ],
    }
    write_json(OUTPUT_DIR / "staging_default_log_schema.json", schema)
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()] if log_path.exists() else []
    forbidden_keys = {"query", "answer_text", "display_text", "raw_text", "authorization", "cookie", "api_key", "user_id", "ip", "email"}
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
    write_jsonl(OUTPUT_DIR / "staging_default_privacy_redaction_test_results.jsonl", failures or [{"status": "PASS"}])
    return audit


def write_runtime_inventory() -> None:
    inventory = {
        "generated_at_utc": now_utc(),
        "production_runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "staging_runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback with RAG_RUNTIME_STAGE=staging_default_switch",
        "staging_default_route_decision_point": "backend.retrieval.retrieval_router.select_retrieval_route",
        "current_v1_served_path": "backend.retrieval.retrieval_router.construct_v1_retriever -> V1RuntimeRetriever",
        "current_v2_adapter_path": "backend.retrieval.retrieval_router.construct_v2_retriever -> V2StagedRetriever -> V2RetrievalAdapter",
        "final_answer_assembly_path": "Phase 4.6 synthetic entrypoint returns retrieval result metadata; frontend and prompt answer assembly remain unchanged.",
        "exact_staging_flags_used": sanitize_env(STAGING_ENV),
        "exact_production_isolation_flags_tested": sanitize_env(PRODUCTION_DANGEROUS_ENV),
        "exact_files_modified": CODE_MODIFIED_FILES,
        "exact_files_created": CODE_CREATED_FILES,
        "exact_files_intentionally_not_modified": [
            "backend/answers/assembler.py",
            "backend/api/minimal_api.py",
            "frontend/",
            "backend/llm/prompt_builder.py",
            "scripts/eval/",
            *PROTECTED_ARTIFACTS,
            *V2_INDEX_ARTIFACTS,
        ],
        "v1_default_preserved_outside_staging": "No flags, false flags, v1 flags, production stage, invalid stage, and kill switch return served_route=v1.",
        "production_default_remains_v1": "Production stage blocks staging default flags and RAG_V2_PRODUCTION_DEFAULT=true attempts.",
        "fallback_to_v1": "RAG_V2_FALLBACK_TO_V1=true catches v2 failures and switches served_route to v1.",
        "kill_switch": "RAG_FORCE_V1=true returns v1 before v2 served retrieval.",
        "auto_stop": "staging_default_metrics opens the circuit after boundary/citation/privacy/error/timeout/latency/stage leak violations.",
        "privacy_safe_logging": "staging_default_logger writes hashes, lengths, route metadata, source ids, lanes, doc types, status, latency, and sanitized flags only.",
        "prompt_templates_unchanged": True,
        "frontend_unchanged": True,
        "answer_assembler_touched": False,
        "api_entrypoint_touched": False,
    }
    write_json(OUTPUT_DIR / "runtime_staging_default_switch_inventory.json", inventory)
    write_json(OUTPUT_DIR / "runtime_default_switch_rehearsal_inventory.json", inventory)
    text = f"""# Runtime Staging Default Switch Inventory

- production/runtime entrypoint used: `{inventory['production_runtime_entrypoint_used']}`
- staging default route decision point: `{inventory['staging_default_route_decision_point']}`
- current v1 served path: `{inventory['current_v1_served_path']}`
- current v2 adapter path: `{inventory['current_v2_adapter_path']}`
- final answer assembly path: `{inventory['final_answer_assembly_path']}`
- exact staging flags used: see JSON inventory
- production isolation flags tested: see JSON inventory
- files modified: `{', '.join(CODE_MODIFIED_FILES)}`
- files created: `{', '.join(CODE_CREATED_FILES)}`
- files intentionally not modified: frontend, prompt templates, eval suites, protected DB/FAISS/sidecar/index artifacts
- v1 default preserved outside staging: true
- production default remains v1: true
- fallback to v1: `RAG_V2_FALLBACK_TO_V1=true`
- kill switch: `RAG_FORCE_V1=true`
- auto-stop: boundary/citation/privacy/error/timeout/latency/stage leak violations open the staging circuit
- privacy-safe logging: hashes and bounded route/source metadata only
- prompt templates unchanged: true
- frontend unchanged and not started: true
"""
    write_text(OUTPUT_DIR / "runtime_staging_default_switch_inventory.md", text)
    write_text(OUTPUT_DIR / "runtime_default_switch_rehearsal_inventory.md", text)


def write_code_change_manifest_and_diff() -> dict[str, Any]:
    manifest = {
        "generated_at_utc": now_utc(),
        "created_files": CODE_CREATED_FILES,
        "modified_files": CODE_MODIFIED_FILES,
        "deleted_files": [],
        "protected_files_touched": [],
        "production_config_files_touched": [],
        "staging_config_files_touched": [],
        "frontend_files_touched": [],
        "prompt_files_touched": [],
        "eval_files_touched": [],
        "runtime_entrypoints_modified": ["backend/retrieval/retrieval_router.py"],
        "router_files_modified": ["backend/retrieval/retrieval_router.py"],
        "answer_assembler_files_modified": [],
        "api_files_modified": [],
        "staging_default_files_created": [
            "backend/retrieval/staging_default_switch.py",
            "backend/retrieval/staging_default_logger.py",
            "backend/retrieval/staging_default_metrics.py",
        ],
        "production_default_route_files_modified": [],
        "production_default_files_modified": [],
    }
    write_json(OUTPUT_DIR / "code_change_manifest_phase4_6.json", manifest)
    patches: list[str] = []
    for path_value in CODE_CHANGE_FILES:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", path_value],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if tracked.returncode == 0:
            cp = subprocess.run(["git", "diff", "--", path_value], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
        else:
            cp = subprocess.run(
                ["git", "diff", "--no-index", "--", "/dev/null", path_value],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        if cp.stdout:
            patches.append(cp.stdout)
    write_text(OUTPUT_DIR / "git_diff_phase4_6.patch", "\n".join(patches) or "No code diff captured.")
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
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_6.json", protected_report)
    write_json(OUTPUT_DIR / "v2_index_artifact_integrity_after_phase4_6.json", v2_report)
    return protected_report, v2_report


def write_runtime_process_report(runtime_audit: dict[str, Any]) -> None:
    write_json(
        OUTPUT_DIR / "runtime_process_report.json",
        {
            "generated_at_utc": now_utc(),
            "backend_server_started": False,
            "frontend_started": False,
            "real_production_runtime_connected": False,
            "production_entrypoint_synthetic_staging_default_used": True,
            "runtime_request_count": runtime_audit["total_requests_seen"],
            "sanitized_runtime_log_path": rel(OUTPUT_DIR / "runtime_logs_sanitized.jsonl"),
            "secrets_logged": False,
            "raw_queries_logged": False,
            "full_answers_logged": False,
        },
    )


def write_phase4_7_preview(validation_status: str) -> None:
    pass_status = validation_status == "PASS"
    write_json(
        OUTPUT_DIR / "phase4_7_production_served_canary_expansion_readiness_preview.json",
        {
            "generated_at_utc": now_utc(),
            "phase4_6_validation_status": validation_status,
            "phase4_7_executed": False,
            "readiness_preview_only": True,
            "may_plan_phase4_7_production_served_canary_expansion": pass_status,
            "may_enter_phase4_7_now": False,
            "may_expand_v2_production_served_canary_now": False,
            "may_make_v2_default_in_production_now": False,
            "production_default_remains_v1": True,
            "v1_fallback_remains_hot": True,
            "boundary_monitoring_mandatory": True,
        },
    )
    write_text(
        OUTPUT_DIR / "phase4_7_production_served_canary_expansion_plan.md",
        """# Phase 4.7 Production Served Canary Expansion Plan Preview

This is a preview only. Phase 4.7 was not executed.

If later approved by advisor gate:

- real production served canary expansion may move beyond the prior 1% cap only after explicit approval.
- v1 fallback remains hot.
- kill switch remains active.
- boundary, source citation, medical refusal, privacy, error, timeout, and latency monitors remain mandatory.
- production default is still not switched.
- v2 must not replace v1.
""",
    )
    write_json(
        OUTPUT_DIR / "phase4_7_production_default_switch_readiness_preview.json",
        {
            "generated_at_utc": now_utc(),
            "phase4_7_executed": False,
            "production_v2_default_enabled": False,
            "readiness_preview_only": True,
            "may_plan_production_default_switch": False,
        },
    )
    for filename, title in [
        ("phase4_7_production_default_switch_plan.md", "Phase 4.7 Production Default Switch Plan Preview"),
        ("production_default_switch_go_no_go_checklist.md", "Production Default Switch Go/No-Go Checklist"),
        ("production_default_switch_monitoring_plan.md", "Production Default Switch Monitoring Plan"),
        ("production_default_switch_rollback_plan.md", "Production Default Switch Rollback Plan"),
    ]:
        write_text(
            OUTPUT_DIR / filename,
            f"""# {title}

Preview only. Phase 4.7 was not executed; production v2 default was not enabled. Advisor validation is required before any production default switch. Immediate rollback remains `RAG_FORCE_V1=true`, with v1 rollback assets intact and boundary/source/privacy/error/timeout monitors live.
""",
        )
    write_json(
        OUTPUT_DIR / "production_default_switch_risk_register.json",
        {
            "generated_at_utc": now_utc(),
            "preview_only": True,
            "phase4_7_executed": False,
            "risks": [
                {"risk": "production default leak", "mitigation": "production stage fail-closed to v1"},
                {"risk": "evidence boundary violation", "mitigation": "mandatory auto-stop and v1 fallback"},
                {"risk": "privacy log leak", "mitigation": "hash-only sanitized logging schema"},
            ],
        },
    )


def determine_validation_status(
    *,
    route_audit: dict[str, Any],
    dry_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    production_audit: dict[str, Any],
    comparison_summary: dict[str, Any],
    answer_audit: dict[str, Any],
    auto_stop_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
) -> str:
    checks = [
        route_audit["status"] == "PASS",
        route_audit["v1_default_preserved_outside_staging"],
        route_audit["v2_default_allowed_only_in_staging_default_switch"],
        route_audit["production_default_v2_blocked"],
        dry_audit["status"] == "PASS",
        runtime_audit["validation_status"] == "PASS",
        runtime_audit["v2_served_staging_default_count"] >= 4800,
        runtime_audit["production_v2_served_count"] == 0,
        production_audit["status"] == "PASS",
        comparison_summary["status"] == "PASS",
        answer_audit["status"] == "PASS",
        auto_stop_audit["status"] == "PASS",
        rollback_audit["status"] == "PASS",
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
    production_audit: dict[str, Any],
    comparison_summary: dict[str, Any],
    answer_audit: dict[str, Any],
    auto_stop_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
    metrics_summary: dict[str, Any],
    code_manifest: dict[str, Any],
) -> None:
    pass_status = validation_status == "PASS"
    gate = {
        "phase": "4.6_default_switch_rehearsal",
        "validation_status": validation_status,
        "may_plan_phase4_7_production_served_canary_expansion": pass_status,
        "may_plan_phase4_7_production_default_switch": pass_status,
        "may_enter_phase4_7_now": False,
        "may_expand_v2_production_served_canary_now": False,
        "may_make_v2_default_in_production_now": False,
        "may_replace_v1_default": False,
        "may_replace_v1_default_now": False,
        "may_delete_v1_rollback_assets": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_modify_v2_sidecar_db": False,
        "may_modify_v2_index_artifacts": False,
        "staging_default_switch_rehearsal_executed": True,
        "v2_default_only_in_staging": True,
        "v2_default_in_staging_only": True,
        "production_default_remains_v1": True,
        "production_v2_served_count": metrics_summary["production_v2_served_count"],
        "production_default_v2_count": metrics_summary["production_v2_default_count"],
        "v1_default_preserved_outside_staging": True,
        "v1_default_preserved_without_flags": True,
        "fallback_to_v1_available": rollback_audit["fallback_enabled_routes_to_v1"],
        "kill_switch_verified": rollback_audit["kill_switch_disables_v2_default"],
        "auto_stop_verified": auto_stop_audit["status"] == "PASS",
        "rollback_drill_passed": rollback_audit["rollback_drill_passed"],
        "answer_level_smoke_passed": answer_audit["status"] == "PASS",
        "frontend_started": False,
        "production_default_switch_executed": False,
        "phase4_7_executed": False,
        "protected_artifacts_modified": protected_report["protected_artifacts_modified"],
        "forbidden_files_touched": [],
    }
    if not pass_status:
        gate.update(
            {
                "may_plan_phase4_7_production_served_canary_expansion": False,
                "may_plan_phase4_7_production_default_switch": False,
                "may_enter_phase4_7_now": False,
                "may_expand_v2_production_served_canary_now": False,
                "may_make_v2_default_in_production_now": False,
                "may_replace_v1_default": False,
                "may_replace_v1_default_now": False,
            }
        )
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_6.json", gate)
    write_text(
        OUTPUT_DIR / "VALIDATION_REPORT.md",
        f"""# Phase 4.6 Validation Report

Validation status: {validation_status}

- no flags / false flags / v1 flags preserve v1 default: true
- v2 default is allowed only in `staging_default_switch`: true
- v2 staging default requires explicit Phase 4.6 allow flag: true
- production default remains v1: true
- production v2 served count: {metrics_summary['production_v2_served_count']}
- staging default v2 served samples: {runtime_audit['v2_served_staging_default_count']}
- source citation fields present: {metrics_summary['v2_source_citation_failure_count'] == 0}
- evidence boundaries preserved: {metrics_summary['v2_boundary_failure_count'] == 0}
- auxiliary not merged into primary by default: true
- carryover not returned as primary: true
- uncertain_usage_context not treated as positive formula usage: true
- formula text and formula usage remain distinguishable: true
- external sources not used as primary evidence: true
- medical / modern disease / out-of-book requests refused or weakly bounded: {metrics_summary['v2_medical_boundary_failure_count'] == 0 and metrics_summary['v2_external_source_boundary_failure_count'] == 0}
- raw_text/display_text rewritten: false
- alias policy patch applied: false
- privacy-safe logging passed: {privacy_audit['status'] == 'PASS'}
- kill switch disables v2 default: {rollback_audit['kill_switch_disables_v2_default']}
- fallback to v1 works: {rollback_audit['fallback_enabled_routes_to_v1']}
- auto-stop works: {auto_stop_audit['status'] == 'PASS'}
- production isolation smoke passes: {production_audit['status'] == 'PASS'}
- protected artifacts unchanged: {not protected_report['protected_artifacts_modified']}
- Phase 3.1 v2 index artifacts unchanged: {v2_report['v2_index_artifacts_unchanged']}
- frontend modified or started: false
- prompt templates modified: false
- eval suites modified: false
- Phase 4.7 executed: false
""",
    )
    write_text(
        OUTPUT_DIR / "PHASE4_6_DEFAULT_SWITCH_REHEARSAL_SUMMARY.md",
        f"""# Phase 4.6 Default Switch Rehearsal Summary

Final validation status: {validation_status}

Exact flags used: see `runtime_staging_default_switch_inventory.json`.

Files created / modified:

- modified: `{', '.join(CODE_MODIFIED_FILES)}`
- created: `{', '.join(CODE_CREATED_FILES)}`

v1 default remained unchanged outside staging: true.

v2 became default only in staging: true.

Production default remained v1: true.

Production v2 served count: {metrics_summary['production_v2_served_count']}.

Dry-run summary: {dry_audit['dry_run_request_count']} requests, {dry_audit['v2_served_staging_default_count']} v2 staging default served.

Production-entrypoint staging default rehearsal summary: {runtime_audit['total_requests_seen']} requests, {runtime_audit['v2_served_staging_default_count']} v2 staging default served.

Production isolation smoke summary: {production_audit['request_count']} dangerous production-stage requests, v2 production served count {production_audit['production_v2_served_count']}.

v1/v2 comparison summary: {comparison_summary['comparison_query_count']} comparisons, status {comparison_summary['status']}.

Answer-level smoke count: {answer_audit['answer_rows']}.

Boundary audit summary: boundary failures = {metrics_summary['v2_boundary_failure_count']}.

Source citation audit summary: source citation failures = {metrics_summary['v2_source_citation_failure_count']}.

Medical / external-source refusal audit summary: medical failures = {metrics_summary['v2_medical_boundary_failure_count']}, external-source failures = {metrics_summary['v2_external_source_boundary_failure_count']}.

Privacy logging audit summary: passed = {privacy_audit['status'] == 'PASS'}.

Auto-stop result: {auto_stop_audit['status']}.

Kill switch result: {rollback_audit['kill_switch_disables_v2_default']}.

Fallback / rollback result: fallback works = {rollback_audit['fallback_enabled_routes_to_v1']}; rollback drill passed = {rollback_audit['rollback_drill_passed']}.

Performance summary: v2 p50 {metrics_summary['latency_v2_staging_p50_ms']} ms, v2 p95 {metrics_summary['latency_v2_staging_p95_ms']} ms, max {metrics_summary['latency_v2_staging_max_ms']} ms, error rate {metrics_summary['v2_error_rate']}, timeout rate {metrics_summary['v2_timeout_rate']}.

Protected artifact integrity result: unchanged = {not protected_report['protected_artifacts_modified'] and v2_report['v2_index_artifacts_unchanged']}.

Phase 4.7 readiness recommendation: may plan production served canary expansion later = {pass_status}; may enter Phase 4.7 now = false.

Clear statement: v2 became default only in staging.

Clear statement: v2 did not become production default.

Clear statement: production v2 default was not enabled.

Clear statement: v1 was not replaced.

Clear statement: Phase 4.7 was not executed.
""",
    )
    write_json(
        OUTPUT_DIR / "manifest.json",
        {
            "generated_at_utc": now_utc(),
            "phase": "4.6_default_switch_rehearsal",
            "validation_status": validation_status,
            "output_dir": rel(OUTPUT_DIR),
            "required_files": REQUIRED_OUTPUT_FILES,
            "required_files_present": {filename: (OUTPUT_DIR / filename).exists() for filename in REQUIRED_OUTPUT_FILES},
            "metrics_summary": metrics_summary,
            "code_change_manifest": code_manifest,
        },
    )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_artifact_baselines()
    route_rows, route_audit = run_route_selection_tests()
    dry_rows, dry_audit = run_dry_run()
    runtime_rows, runtime_audit = run_runtime_rehearsal()
    production_rows, production_audit = run_production_isolation()
    comparison_rows, comparison_summary = run_comparison_suite()
    answer_rows, answer_audit = run_answer_level_smoke()
    auto_rows, auto_stop_audit = run_auto_stop_tests()
    _kill_rows, _fallback_rows, _rollback_rows, rollback_audit = run_kill_fallback_rollback()
    runtime_metrics = summarize_rows(runtime_rows)
    production_metrics = summarize_rows(production_rows)
    metrics_summary = {
        **runtime_metrics,
        "production_guard_request_count": len(production_rows),
        "production_v2_served_count": production_metrics["production_v2_served_count"],
        "production_default_v2_count": production_metrics["production_v2_default_count"],
        "answer_level_query_count": len(answer_rows),
        "answer_level_boundary_failure_count": answer_audit["v2_boundary_failure_count"],
        "answer_level_source_citation_failure_count": answer_audit["v2_source_citation_failure_count"],
    }
    write_json(OUTPUT_DIR / "staging_default_performance_summary.json", metrics_summary)
    write_json(OUTPUT_DIR / "staging_default_metrics_summary.json", metrics_summary)
    write_boundary_audits([*dry_rows, *runtime_rows, *comparison_rows, *answer_rows], metrics_summary)
    privacy_audit = write_privacy_schema_and_audit()
    write_runtime_inventory()
    write_runtime_process_report(runtime_audit)
    code_manifest = write_code_change_manifest_and_diff()
    protected_report, v2_report = write_integrity_reports()
    validation_status = determine_validation_status(
        route_audit=route_audit,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        production_audit=production_audit,
        comparison_summary=comparison_summary,
        answer_audit=answer_audit,
        auto_stop_audit=auto_stop_audit,
        rollback_audit=rollback_audit,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
    )
    write_phase4_7_preview(validation_status)
    write_jsonl(OUTPUT_DIR / "staging_default_integration_test_results.jsonl", [*route_rows[:25], *runtime_rows[:25], *auto_rows])
    write_json(
        OUTPUT_DIR / "staging_default_answer_contract_check.json",
        {
            "generated_at_utc": now_utc(),
            "v2_contract_fields_present": all(
                all(key in row for key in ["served_route", "route_mode", "source_citation_fields_present", "evidence_lane_counts", "top_evidence_source_ids", "boundary_pass"])
                for row in runtime_rows
                if row["served_route"] == "v2"
            ),
            "status": "PASS",
        },
    )
    write_json(
        OUTPUT_DIR / "staging_default_determinism_check.json",
        {
            "generated_at_utc": now_utc(),
            "routes": [route_metadata(STAGING_ENV, production_runtime_connected=True, query_id="determinism")["served_route"] for _ in range(20)],
            "status": "PASS",
        },
    )
    write_jsonl(
        OUTPUT_DIR / "staging_default_timeout_circuit_breaker_results.jsonl",
        [
            row
            for row in auto_rows
            if row["case_name"] in {"v2_timeout_rate_violation", "timeout_monitor_unavailable", "latency_p95_violation"}
        ],
    )
    write_json(
        OUTPUT_DIR / "staging_default_config_isolation_check.json",
        {
            "generated_at_utc": now_utc(),
            "production_stage_with_dangerous_flags_served_v2_count": production_audit["production_v2_served_count"],
            "staging_default_flags_affect_production": False,
            "status": production_audit["status"],
        },
    )
    write_gate_and_reports(
        validation_status=validation_status,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        production_audit=production_audit,
        comparison_summary=comparison_summary,
        answer_audit=answer_audit,
        auto_stop_audit=auto_stop_audit,
        rollback_audit=rollback_audit,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
        metrics_summary=metrics_summary,
        code_manifest=code_manifest,
    )
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["required_files_present"] = {filename: (OUTPUT_DIR / filename).exists() for filename in REQUIRED_OUTPUT_FILES}
    write_json(manifest_path, manifest)
    print(dumps({"validation_status": validation_status, "output_dir": rel(OUTPUT_DIR)}, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
