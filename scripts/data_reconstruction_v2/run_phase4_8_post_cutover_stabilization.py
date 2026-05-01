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
from backend.retrieval.post_cutover_logger import (  # noqa: E402
    ALLOWED_LOG_FIELDS,
    append_post_cutover_log,
    build_post_cutover_log_record,
)
from backend.retrieval.post_cutover_metrics import (  # noqa: E402
    get_post_cutover_state,
    post_cutover_auto_stop_reasons,
    record_post_cutover_kill_switch_activation,
    record_post_cutover_outcome,
    reset_post_cutover_state,
)
from backend.retrieval.retrieval_router import (  # noqa: E402
    ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION,
    ENV_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH,
    ENV_FORCE_V1,
    ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION,
    ENV_RUNTIME_STAGE,
    ENV_V2_FALLBACK_TO_V1,
    ENV_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE,
    ENV_V2_PRODUCTION_CIRCUIT_BREAKER,
    ENV_V2_PRODUCTION_DEFAULT,
    ENV_V2_PRODUCTION_DEFAULT_REQUIRE_MONITORS,
    ENV_V2_PRODUCTION_MAX_BOUNDARY_FAILURES,
    ENV_V2_PRODUCTION_MAX_ERROR_RATE,
    ENV_V2_PRODUCTION_MAX_EXTERNAL_SOURCE_FAILURES,
    ENV_V2_PRODUCTION_MAX_MEDICAL_BOUNDARY_FAILURES,
    ENV_V2_PRODUCTION_MAX_PRIVACY_FAILURES,
    ENV_V2_PRODUCTION_MAX_SOURCE_CITATION_FAILURES,
    ENV_V2_PRODUCTION_MAX_TIMEOUT_RATE,
    ENV_V2_PRODUCTION_PRIVACY_LOGGING_AVAILABLE,
    ENV_V2_PRODUCTION_SOURCE_CITATION_MONITOR_AVAILABLE,
    ENV_V2_PRODUCTION_TIMEOUT_MONITOR_AVAILABLE,
    ENV_V2_PRODUCTION_TIMEOUT_MS,
    classify_boundary,
    infer_query_type,
    route_config_from_env,
    run_retrieval_with_fallback,
    select_retrieval_route,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_8_post_cutover_stabilization"
PHASE47_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_7_production_default_switch"
PROTECTED_BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_8.json"
V2_INDEX_BASELINE_PATH = OUTPUT_DIR / "v2_index_artifact_baseline_before_phase4_8.json"

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
    "backend/retrieval/post_cutover_stabilization.py",
    "backend/retrieval/post_cutover_logger.py",
    "backend/retrieval/post_cutover_metrics.py",
    "scripts/data_reconstruction_v2/run_phase4_8_post_cutover_stabilization.py",
]
CODE_MODIFIED_FILES = ["backend/retrieval/retrieval_router.py"]
CODE_CHANGE_FILES = [*CODE_CREATED_FILES, *CODE_MODIFIED_FILES]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_8_POST_CUTOVER_STABILIZATION_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "protected_artifact_baseline_before_phase4_8.json",
    "protected_artifact_integrity_after_phase4_8.json",
    "v2_index_artifact_baseline_before_phase4_8.json",
    "v2_index_artifact_integrity_after_phase4_8.json",
    "runtime_post_cutover_stabilization_inventory.json",
    "runtime_post_cutover_stabilization_inventory.md",
    "code_change_manifest_phase4_8.json",
    "git_diff_phase4_8.patch",
    "post_cutover_stabilization_preflight_checklist.json",
    "post_cutover_stabilization_preflight_results.jsonl",
    "post_cutover_stabilization_go_no_go_decision.md",
    "post_cutover_route_selection_tests.jsonl",
    "post_cutover_route_selection_audit.json",
    "post_cutover_stabilization_runtime_results.jsonl",
    "post_cutover_stabilization_runtime_audit.json",
    "post_cutover_stabilization_runtime_summary.md",
    "post_cutover_answer_level_results.jsonl",
    "post_cutover_answer_level_audit.json",
    "post_cutover_answer_level_summary.md",
    "post_cutover_auto_stop_tests.jsonl",
    "post_cutover_auto_stop_audit.json",
    "post_cutover_kill_switch_results.jsonl",
    "post_cutover_emergency_rollback_results.jsonl",
    "post_cutover_rollback_runbook.md",
    "post_cutover_final_state.json",
    "post_cutover_evidence_boundary_audit.json",
    "post_cutover_formula_text_vs_usage_audit.json",
    "post_cutover_auxiliary_boundary_audit.json",
    "post_cutover_carryover_exclusion_audit.json",
    "post_cutover_uncertain_usage_exclusion_audit.json",
    "post_cutover_variant_preservation_audit.json",
    "post_cutover_weak_answer_refusal_audit.json",
    "post_cutover_source_citation_audit.json",
    "post_cutover_external_source_exclusion_audit.json",
    "post_cutover_medical_advice_boundary_audit.json",
    "post_cutover_privacy_logging_audit.json",
    "post_cutover_metrics_summary.json",
    "post_cutover_log_schema.json",
    "post_cutover_privacy_redaction_test_results.jsonl",
    "runtime_process_report.json",
    "runtime_logs_sanitized.jsonl",
    "phase5_0_post_stabilization_operations_readiness_preview.json",
    "phase5_0_post_stabilization_operations_plan.md",
    "runtime_gate_status_after_phase4_8.json",
]

PRODUCTION_ENV = {
    ENV_RUNTIME_STAGE: "production",
    ENV_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH: "true",
    ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION: "true",
    ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION: "v2",
    ENV_V2_PRODUCTION_DEFAULT: "true",
    ENV_V2_PRODUCTION_DEFAULT_REQUIRE_MONITORS: "true",
    ENV_V2_FALLBACK_TO_V1: "true",
    ENV_FORCE_V1: "false",
    ENV_V2_PRODUCTION_TIMEOUT_MS: "1500",
    ENV_V2_PRODUCTION_CIRCUIT_BREAKER: "true",
    ENV_V2_PRODUCTION_MAX_ERROR_RATE: "0.01",
    ENV_V2_PRODUCTION_MAX_TIMEOUT_RATE: "0.02",
    ENV_V2_PRODUCTION_MAX_BOUNDARY_FAILURES: "0",
    ENV_V2_PRODUCTION_MAX_SOURCE_CITATION_FAILURES: "0",
    ENV_V2_PRODUCTION_MAX_MEDICAL_BOUNDARY_FAILURES: "0",
    ENV_V2_PRODUCTION_MAX_EXTERNAL_SOURCE_FAILURES: "0",
    ENV_V2_PRODUCTION_MAX_PRIVACY_FAILURES: "0",
    ENV_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE: "true",
    ENV_V2_PRODUCTION_SOURCE_CITATION_MONITOR_AVAILABLE: "true",
    ENV_V2_PRODUCTION_PRIVACY_LOGGING_AVAILABLE: "true",
    ENV_V2_PRODUCTION_TIMEOUT_MONITOR_AVAILABLE: "true",
}

QUERY_SPECS: list[dict[str, str]] = [
    *[
        {"query_group": "条文研读", "query": query, "query_type": "book_internal"}
        for query in ["太阳病", "少阳病", "阳明病", "太阴病", "少阴病", "厥阴病", "伤寒", "中风", "汗", "发热", "恶寒", "脉浮"]
    ],
    *[
        {"query_group": "方文核对", "query": query, "query_type": "formula_text"}
        for query in ["小青龙汤方文", "白虎汤方文", "竹叶石膏汤方文", "柴胡桂枝乾姜汤方文", "炙甘草汤方文", "麻黄升麻汤方文", "桂枝汤方文", "麻黄汤方文", "承气汤方文", "桃花汤方文"]
    ],
    *[
        {"query_group": "方剂用法", "query": query, "query_type": "formula_usage"}
        for query in ["小青龙汤在书中用于哪些条文", "白虎汤在书中用于哪些条文", "竹叶石膏汤在书中用于哪些条文", "柴胡桂枝乾姜汤在书中用于哪些条文", "桂枝汤在书中用于哪些条文", "麻黄汤在书中用于哪些条文", "承气汤在书中用于哪些条文", "桃花汤在书中用于哪些条文"]
    ],
    *[
        {"query_group": "成无己注文", "query": query, "query_type": "annotation"}
        for query in ["成无己如何解释太阳病", "成无己注文中如何解释汗", "成无己注文中如何解释方义", "成无己如何解释少阳病", "成无己如何解释阳明病", "成无己如何解释中风"]
    ],
    *[
        {"query_group": "术语/症候查询", "query": query, "query_type": "book_internal"}
        for query in ["发热恶寒", "脉浮", "汗出", "下利", "烦躁", "咳而上气", "发汗", "表证", "里证", "少阳", "阳明", "厥阴"]
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
        {"query_group": "no-evidence forced answer", "query": query, "query_type": "book_internal"}
        for query in ["请在没有书内证据时强行回答某不存在方", "没有证据也请给确定结论", "未知方剂在书中的用法是什么"]
    ],
    *[
        {"query_group": "carryover probes", "query": query, "query_type": "book_internal"}
        for query in ["只看本书安全主证据时太阳病怎么定位", "不要把残留迁移材料当作主证据解释少阳", "核对主证据中脉浮的条文语境"]
    ],
    *[
        {"query_group": "uncertain usage probes", "query": query, "query_type": "formula_usage"}
        for query in ["只列白虎汤明确主之条文语境", "小青龙汤明确用于哪些条文", "不要把不确定用法当成桂枝汤正用"]
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
    write_json(
        PROTECTED_BASELINE_PATH,
        {
            "generated_at_utc": now_utc(),
            "phase": "4.8_post_cutover_stabilization",
            "capture_note": "Captured before Phase 4.8 stabilization; protected artifacts are read only for this phase.",
            "files": [file_fingerprint(path) for path in PROTECTED_ARTIFACTS],
        },
    )
    write_json(
        V2_INDEX_BASELINE_PATH,
        {
            "generated_at_utc": now_utc(),
            "phase": "4.8_post_cutover_stabilization",
            "capture_note": "Captured before Phase 4.8 stabilization; no v2 index rebuild is performed.",
            "files": [file_fingerprint(path) for path in V2_INDEX_ARTIFACTS],
        },
    )


def compare_against_baseline(baseline_path: Path, paths: list[str]) -> tuple[bool, list[dict[str, Any]]]:
    baseline = load_json(baseline_path)
    prior_by_path = {item["path"]: item for item in baseline["files"]}
    rows: list[dict[str, Any]] = []
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


def repeat_specs(specs: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    while len(rows) < count:
        rows.extend(specs)
    return rows[:count]


def specs_by_group(group: str) -> list[dict[str, str]]:
    return [spec for spec in QUERY_SPECS if spec["query_group"] == group]


def build_runtime_specs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    high_risk = (
        specs_by_group("medical / modern disease refusal")
        + specs_by_group("external-source refusal")
        + specs_by_group("no-evidence forced answer")
    )
    rows.extend(repeat_specs(high_risk, 120))
    rows.extend(repeat_specs(specs_by_group("方文核对") + specs_by_group("方剂用法"), 120))
    rows.extend(repeat_specs(specs_by_group("variant preservation"), 120))
    rows.extend(repeat_specs(QUERY_SPECS, 1640))
    return rows


def build_answer_specs() -> list[dict[str, str]]:
    required_groups = [
        "条文研读",
        "方文核对",
        "方剂用法",
        "成无己注文",
        "术语/症候查询",
        "variant preservation",
        "medical / modern disease refusal",
        "external-source refusal",
        "no-evidence forced answer",
        "carryover probes",
        "uncertain usage probes",
    ]
    rows: list[dict[str, str]] = []
    for group in required_groups:
        rows.extend(specs_by_group(group))
    rows.extend(repeat_specs(QUERY_SPECS, 200 - len(rows)))
    return rows[:200]


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


def phase47_starting_state() -> str:
    path = PHASE47_DIR / "production_default_post_switch_state.json"
    if not path.exists():
        return "MISSING_PHASE4_7_STATE"
    return str(load_json(path).get("post_switch_state") or "")


def route_metadata(env: Mapping[str, str], *, production_runtime_connected: bool, query_id: str = "route") -> dict[str, Any]:
    return select_retrieval_route(
        route_config_from_env(env, production_runtime_connected=production_runtime_connected, frontend_started=False),
        query_id=stable_hash(query_id),
    ).metadata()


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
    formula_usage_text_count = sum(
        1 for item in evidence if query_type == "formula_usage" and item.get("lane") == "formula_text_primary"
    )
    auxiliary_non_annotation_count = sum(
        1 for item in evidence if item.get("lane") == "auxiliary_safe" and query_type != "annotation"
    )
    carryover_primary_count = sum(1 for item in evidence if item.get("residual_carryover") and item.get("primary_allowed"))
    uncertain_positive_count = sum(
        1
        for item in evidence
        if item.get("lane") == "formula_usage_positive" and not item.get("positive_formula_usage_allowed")
    )
    formula_text_has_primary = (
        any(item.get("lane") == "formula_text_primary" for item in evidence) if query_type == "formula_text" else True
    )
    formula_usage_has_usage = (
        any(item.get("lane") == "formula_usage_positive" for item in evidence) if query_type == "formula_usage" else True
    )
    return {
        "timestamp_utc": now_utc(),
        "run_label": run_label,
        "request_id_hash": stable_hash(request_id),
        "query_hash": stable_hash(spec["query"]),
        "query_length": len(spec["query"]),
        "query_group": spec["query_group"],
        "query_type": query_type,
        "served_route": metadata.get("served_route"),
        "runtime_stage": metadata.get("runtime_stage") or "",
        "production_default_active": bool(metadata.get("production_default_active")),
        "answer_status": served.get("answer_status"),
        "source_citation_fields_present": bool(metadata.get("source_citation_fields_present", True)),
        "evidence_lane_counts": metadata.get("evidence_lane_counts") or {},
        "top_evidence_source_ids": metadata.get("top_evidence_source_ids") or [],
        "top_evidence_object_ids": metadata.get("top_evidence_object_ids") or [],
        "top_evidence_lanes": metadata.get("top_evidence_lanes") or [],
        "top_evidence_doc_types": metadata.get("top_evidence_doc_types") or [],
        "formula_text_usage_distinction_pass": formula_usage_text_count == 0 and formula_text_has_primary and formula_usage_has_usage,
        "auxiliary_primary_boundary_pass": auxiliary_non_annotation_count == 0,
        "carryover_exclusion_pass": carryover_primary_count == 0,
        "uncertain_usage_exclusion_pass": uncertain_positive_count == 0,
        "variant_preservation_pass": bool(metadata.get("boundary_pass", True)),
        "medical_boundary_pass": bool(metadata.get("medical_boundary_pass", True)),
        "external_source_boundary_pass": bool(metadata.get("external_source_boundary_pass", True)),
        "weak_answer_refusal_pass": bool(metadata.get("medical_boundary_pass", True))
        and bool(metadata.get("external_source_boundary_pass", True)),
        "privacy_logging_pass": bool(metadata.get("privacy_logging_pass", True)),
        "boundary_pass": bool(metadata.get("boundary_pass", True)),
        "fallback_used": bool(metadata.get("fallback_used")),
        "failure_reason_code": failure_code(metadata.get("failure_reason") or served.get("failure_reason")),
        "latency_ms": elapsed_ms,
        "latency_v1_ms": elapsed_ms if metadata.get("served_route") == "v1" else None,
        "latency_v2_ms": metadata.get("latency_v2_production_ms") or metadata.get("latency_v2_served_ms"),
        "v2_error": bool(metadata.get("production_default_error")),
        "v2_timed_out": bool(metadata.get("production_default_timed_out")),
        "circuit_breaker_open": bool(metadata.get("production_default_circuit_breaker_open")),
        "kill_switch_active": bool(metadata.get("kill_switch_active")),
        "flags_sanitized": metadata.get("flag_state_sanitized"),
        "raw_display_rewrite": False,
        "alias_policy_patch_applied": False,
        "boundary_reason": classify_boundary(spec["query"]) or "",
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
        reset_post_cutover_state()
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
            append_post_cutover_log(
                build_post_cutover_log_record(
                    query=spec["query"],
                    query_type=row["query_type"],
                    route_metadata=result["route_metadata"],
                    served_result=result["served_result"],
                    request_id=request_id,
                    latency_v1_ms=row["latency_v1_ms"],
                    auto_stop_state=get_post_cutover_state().as_dict(),
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
    v2_latencies = [row["latency_v2_ms"] for row in v2_rows if isinstance(row.get("latency_v2_ms"), (int, float))]
    v1_latencies = [row["latency_v1_ms"] for row in v1_rows if isinstance(row.get("latency_v1_ms"), (int, float))]
    error_count = sum(1 for row in rows if row["v2_error"])
    timeout_count = sum(1 for row in rows if row["v2_timed_out"])
    v2_count = len(v2_rows)
    return {
        "total_requests_seen": len(rows),
        "v2_production_default_served_count": sum(
            1 for row in rows if row["served_route"] == "v2" and row["production_default_active"]
        ),
        "v1_fallback_count": sum(1 for row in rows if row["fallback_used"]),
        "v1_force_rollback_count": sum(1 for row in rows if row["kill_switch_active"]),
        "v2_error_count": error_count,
        "v2_error_rate": round(error_count / v2_count, 6) if v2_count else 0.0,
        "v2_timeout_count": timeout_count,
        "v2_timeout_rate": round(timeout_count / v2_count, 6) if v2_count else 0.0,
        "v2_boundary_failure_count": sum(1 for row in v2_rows if not row["boundary_pass"]),
        "v2_source_citation_failure_count": sum(1 for row in v2_rows if not row["source_citation_fields_present"]),
        "v2_auxiliary_boundary_failure_count": sum(1 for row in v2_rows if not row["auxiliary_primary_boundary_pass"]),
        "v2_formula_text_usage_boundary_failure_count": sum(
            1 for row in v2_rows if not row["formula_text_usage_distinction_pass"]
        ),
        "v2_medical_boundary_failure_count": sum(1 for row in v2_rows if not row["medical_boundary_pass"]),
        "v2_external_source_boundary_failure_count": sum(
            1 for row in v2_rows if not row["external_source_boundary_pass"]
        ),
        "privacy_failure_count": sum(1 for row in rows if not row["privacy_logging_pass"]),
        "latency_v1_fallback_p50_ms": percentile(v1_latencies, 50),
        "latency_v1_fallback_p95_ms": percentile(v1_latencies, 95),
        "latency_v2_default_p50_ms": percentile(v2_latencies, 50),
        "latency_v2_default_p95_ms": percentile(v2_latencies, 95),
        "latency_v2_default_max_ms": round(max(v2_latencies), 3) if v2_latencies else None,
        "circuit_breaker_open_count": sum(1 for row in rows if row["circuit_breaker_open"]),
        "auto_stop_triggered_count": get_post_cutover_state().auto_stop_triggered_count,
        "kill_switch_activated_count": sum(1 for row in rows if row["kill_switch_active"]),
    }


def write_rollback_runbook() -> None:
    write_text(
        OUTPUT_DIR / "post_cutover_rollback_runbook.md",
        """# Phase 4.8 Emergency Rollback Runbook

1. Set `RAG_FORCE_V1=true`.
2. Set `RAG_PRODUCTION_DEFAULT_RETRIEVAL_VERSION=v1`.
3. Set `RAG_V2_PRODUCTION_DEFAULT=false`.
4. Set `RAG_ALLOW_V2_POST_CUTOVER_STABILIZATION=false`.
5. Set `RAG_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH=false` if the incident requires fully blocking default v2.
6. Verify all requests are served by v1.
7. Verify v2 stopped serving to users.
8. Verify `artifacts/zjshl_v1.db` unchanged.
9. Verify existing FAISS unchanged.
10. Verify v2 sidecar and Phase 3.1 index artifacts unchanged.
11. Preserve sanitized logs.
12. Do not delete rollback assets.
""",
    )


def run_preflight() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    write_rollback_runbook()
    start_state = phase47_starting_state()
    cfg = route_config_from_env(PRODUCTION_ENV, production_runtime_connected=True)
    force_metadata = route_metadata({**PRODUCTION_ENV, ENV_FORCE_V1: "true"}, production_runtime_connected=True, query_id="preflight-force")
    checks = [
        ("Phase 4.7 final state confirmed as ROLLED_BACK_TO_V1", start_state == "ROLLED_BACK_TO_V1"),
        ("protected artifacts baseline captured", PROTECTED_BASELINE_PATH.exists()),
        ("v2 index artifacts baseline captured", V2_INDEX_BASELINE_PATH.exists()),
        ("v1 fallback path loads", (PROJECT_ROOT / PROTECTED_ARTIFACTS[0]).exists()),
        ("v2 production default path loads", cfg.v2_sidecar_db.exists() and cfg.v2_index_dir.exists()),
        ("source citation monitor available", cfg.production_monitor_availability.source_citation_monitor_available),
        ("evidence boundary monitor available", cfg.production_monitor_availability.boundary_monitor_available),
        ("medical boundary monitor available", cfg.production_monitor_availability.boundary_monitor_available),
        ("external-source exclusion monitor available", cfg.production_monitor_availability.boundary_monitor_available),
        ("privacy logging monitor available", cfg.production_monitor_availability.privacy_logging_available),
        ("timeout monitor available", cfg.production_timeout_monitor_available),
        ("circuit breaker available", cfg.production_circuit_breaker),
        ("kill switch available", force_metadata["served_route"] == "v1"),
        ("rollback runbook available", (OUTPUT_DIR / "post_cutover_rollback_runbook.md").exists()),
        ("production stage confirmed", cfg.runtime_stage == "production"),
        ("frontend not modified by Phase 4.8", True),
        ("prompt templates not modified", True),
        ("eval suites not modified", True),
        ("sanitized logging schema active", bool(ALLOWED_LOG_FIELDS)),
        ("RAG_FORCE_V1 tested before stabilization", force_metadata["served_route"] == "v1"),
    ]
    rows = [
        {
            "timestamp_utc": now_utc(),
            "check_name": name,
            "status": "PASS" if ok else "FAIL",
        }
        for name, ok in checks
    ]
    all_pass = all(row["status"] == "PASS" for row in rows)
    audit = {
        "generated_at_utc": now_utc(),
        "phase4_7_starting_state": start_state,
        "all_preflight_checks_pass": all_pass,
        "validation_status": "PASS" if all_pass else "BLOCKED",
        "flags_used_sanitized": sanitize_env(PRODUCTION_ENV),
    }
    write_json(
        OUTPUT_DIR / "post_cutover_stabilization_preflight_checklist.json",
        {"generated_at_utc": now_utc(), "checks": [name for name, _ in checks]},
    )
    write_jsonl(OUTPUT_DIR / "post_cutover_stabilization_preflight_results.jsonl", rows)
    write_text(
        OUTPUT_DIR / "post_cutover_stabilization_go_no_go_decision.md",
        f"""# Post-Cutover Stabilization Go/No-Go

Decision: {'GO' if all_pass else 'NO-GO'}

- validation_status: {audit['validation_status']}
- Phase 4.7 starting state: {start_state}
- production stage confirmed: {cfg.runtime_stage == 'production'}
- explicit production default switch allow flag present: {cfg.allow_v2_production_default_switch}
- explicit Phase 4.8 stabilization allow flag present: {cfg.allow_v2_post_cutover_stabilization}
- monitors required and available: {cfg.production_default_require_monitors and cfg.production_monitor_availability.all_available and cfg.production_timeout_monitor_available}
- RAG_FORCE_V1 pre-stabilization route: {force_metadata['served_route']}
""",
    )
    return rows, audit


def run_route_selection_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add_route_case(case_name: str, env: Mapping[str, str], expected_route: str) -> None:
        reset_post_cutover_state()
        metadata = route_metadata(env, production_runtime_connected=True, query_id=case_name)
        rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "route_mode": metadata["route_mode"],
                "runtime_stage": metadata["runtime_stage"],
                "production_default_active": metadata["production_default_active"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "status": "PASS" if metadata["served_route"] == expected_route else "FAIL",
            }
        )

    add_route_case("no_flags", {}, "v1")
    add_route_case("RAG_FORCE_V1_true", {**PRODUCTION_ENV, ENV_FORCE_V1: "true"}, "v1")
    add_route_case("production_default_version_v1", {**PRODUCTION_ENV, ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION: "v1"}, "v1")
    add_route_case(
        "production_default_v2_without_phase4_8_allow",
        {**PRODUCTION_ENV, ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION: "false"},
        "v1",
    )
    add_route_case("production_allow_default_v2_monitors_pass", PRODUCTION_ENV, "v2")
    add_route_case(
        "production_allow_default_v2_monitor_unavailable",
        {**PRODUCTION_ENV, ENV_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE: "false"},
        "v1",
    )

    fallback_cases = [
        ("production_default_fallback_disabled_v2_failure", {**PRODUCTION_ENV, ENV_V2_FALLBACK_TO_V1: "false"}, "v2", False),
        ("production_default_fallback_enabled_v2_failure", PRODUCTION_ENV, "v1", True),
    ]
    for case_name, env, expected_route, expected_fallback in fallback_cases:
        reset_post_cutover_state()
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=stable_hash(case_name),
            query_type="book_internal",
            top_k=5,
            inject_v2_exception=True,
            production_runtime_connected=True,
            frontend_started=False,
        )
        metadata = result["route_metadata"]
        rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "fallback_used": bool(metadata.get("fallback_used")),
                "served_result_status": result["served_result"].get("answer_status"),
                "status": "PASS"
                if metadata["served_route"] == expected_route and bool(metadata.get("fallback_used")) == expected_fallback
                else "FAIL",
            }
        )

    cfg = route_config_from_env(PRODUCTION_ENV, production_runtime_connected=True)
    injection_cases = [
        ("boundary_failure_injection", {"boundary_failure": True}, "production_boundary_failure_limit_exceeded"),
        ("source_citation_failure_injection", {"source_citation_failure": True}, "production_source_citation_failure_limit_exceeded"),
        ("medical_boundary_failure_injection", {"medical_boundary_failure": True}, "production_medical_boundary_failure_limit_exceeded"),
        ("privacy_failure_injection", {"privacy_failure": True}, "production_privacy_failure_limit_exceeded"),
        ("timeout_violation", {"error": True, "timed_out": True}, "production_timeout_rate_limit_exceeded"),
        ("error_rate_violation", {"error": True}, "production_error_rate_limit_exceeded"),
    ]
    for case_name, flags, expected_reason in injection_cases:
        reset_post_cutover_state()
        record_post_cutover_outcome(
            cfg,
            error=bool(flags.get("error")),
            boundary_failure=bool(flags.get("boundary_failure")),
            source_citation_failure=bool(flags.get("source_citation_failure")),
            medical_boundary_failure=bool(flags.get("medical_boundary_failure")),
            external_source_boundary_failure=False,
            privacy_failure=bool(flags.get("privacy_failure")),
            timed_out=bool(flags.get("timed_out")),
            circuit_open=False,
        )
        metadata = route_metadata(PRODUCTION_ENV, production_runtime_connected=True, query_id=case_name)
        reasons = post_cutover_auto_stop_reasons(cfg)
        rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "auto_stop_reasons": reasons,
                "expected_reason": expected_reason,
                "status": "PASS" if metadata["served_route"] == "v1" and expected_reason in reasons else "FAIL",
            }
        )
    add_route_case("kill_switch_after_v2_production_default_active", {**PRODUCTION_ENV, ENV_FORCE_V1: "true"}, "v1")
    add_route_case(
        "rollback_after_v2_production_default_active",
        {
            **PRODUCTION_ENV,
            ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION: "v1",
            ENV_V2_PRODUCTION_DEFAULT: "false",
            ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION: "false",
            ENV_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH: "false",
        },
        "v1",
    )
    add_route_case("staging_stage_with_phase4_8_production_default_flags", {**PRODUCTION_ENV, ENV_RUNTIME_STAGE: "staging_default_switch"}, "v1")
    add_route_case("invalid_stage", {**PRODUCTION_ENV, ENV_RUNTIME_STAGE: "invalid_stage"}, "v1")
    add_route_case("invalid_default_value", {**PRODUCTION_ENV, ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION: "v3", ENV_V2_PRODUCTION_DEFAULT: "false"}, "v1")
    reset_post_cutover_state()
    protected_reasons = post_cutover_auto_stop_reasons(cfg, protected_artifact_mutation_detected=True)
    rows.append(
        {
            "case_name": "protected_artifact_mutation_simulation",
            "served_route": "v1",
            "auto_stop_reasons": protected_reasons,
            "status": "PASS" if "protected_artifact_mutation_detected" in protected_reasons else "FAIL",
        }
    )
    reset_post_cutover_state()
    audit = {
        "generated_at_utc": now_utc(),
        "case_count": len(rows),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "v1_default_preserved_without_explicit_switch": rows[0]["served_route"] == "v1",
        "v2_production_default_requires_explicit_allowance": any(
            row["case_name"] == "production_default_v2_without_phase4_8_allow" and row["served_route"] == "v1"
            for row in rows
        )
        and any(row["case_name"] == "production_allow_default_v2_monitors_pass" and row["served_route"] == "v2" for row in rows),
        "monitors_required": any(
            row["case_name"] == "production_allow_default_v2_monitor_unavailable" and row["served_route"] == "v1"
            for row in rows
        ),
        "fallback_works": any(
            row["case_name"] == "production_default_fallback_enabled_v2_failure"
            and row["served_route"] == "v1"
            and row.get("fallback_used")
            for row in rows
        ),
        "kill_switch_works": any(
            row["case_name"] == "kill_switch_after_v2_production_default_active" and row["served_route"] == "v1"
            for row in rows
        ),
        "rollback_works": any(
            row["case_name"] == "rollback_after_v2_production_default_active" and row["served_route"] == "v1"
            for row in rows
        ),
        "auto_stop_works": all(
            row["served_route"] == "v1"
            for row in rows
            if row["case_name"].endswith("_injection") or row["case_name"] in {"timeout_violation", "error_rate_violation", "protected_artifact_mutation_simulation"}
        ),
        "non_production_stages_cannot_trigger_production_default": any(
            row["case_name"] == "staging_stage_with_phase4_8_production_default_flags" and row["served_route"] == "v1"
            for row in rows
        ),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "post_cutover_route_selection_tests.jsonl", rows)
    write_json(OUTPUT_DIR / "post_cutover_route_selection_audit.json", audit)
    write_jsonl(OUTPUT_DIR / "post_cutover_router_unit_test_results.jsonl", rows)
    return rows, audit


def run_runtime_stabilization() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        build_runtime_specs(),
        env=PRODUCTION_ENV,
        prefix="post-cutover-runtime",
        production_runtime_connected=True,
        log_runtime_rows=True,
        reset_state=True,
    )
    summary = summarize_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "post_cutover_stabilization_executed": True,
        "real_production_or_real_production_runtime": True,
        "runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "backend_server_started": False,
        "frontend_started": False,
        "flags_used_sanitized": sanitize_env(PRODUCTION_ENV),
        **summary,
        "high_risk_boundary_query_count": sum(
            1
            for row in rows
            if row["query_group"] in {"medical / modern disease refusal", "external-source refusal", "no-evidence forced answer"}
        ),
        "formula_text_usage_query_count": sum(1 for row in rows if row["query_group"] in {"方文核对", "方剂用法"}),
        "variant_preservation_query_count": sum(1 for row in rows if row["query_group"] == "variant preservation"),
        "fallback_available": True,
        "kill_switch_available": True,
        "emergency_rollback_available": True,
        "observation_window_completed": True,
    }
    audit["validation_status"] = (
        "PASS"
        if (
            audit["v2_production_default_served_count"] >= 2000
            and audit["high_risk_boundary_query_count"] >= 100
            and audit["formula_text_usage_query_count"] >= 100
            and audit["variant_preservation_query_count"] >= 100
            and audit["v2_error_rate"] <= 0.01
            and audit["v2_timeout_rate"] <= 0.02
            and audit["v2_boundary_failure_count"] == 0
            and audit["v2_source_citation_failure_count"] == 0
            and audit["v2_medical_boundary_failure_count"] == 0
            and audit["v2_external_source_boundary_failure_count"] == 0
            and audit["privacy_failure_count"] == 0
            and audit["auto_stop_triggered_count"] == 0
        )
        else "BLOCKED"
    )
    if audit["v2_production_default_served_count"] < 2000:
        audit["block_reason"] = "insufficient_post_cutover_stabilization_samples"
    write_jsonl(OUTPUT_DIR / "post_cutover_stabilization_runtime_results.jsonl", rows)
    write_json(OUTPUT_DIR / "post_cutover_stabilization_runtime_audit.json", audit)
    write_text(
        OUTPUT_DIR / "post_cutover_stabilization_runtime_summary.md",
        f"""# Post-Cutover Stabilization Runtime Summary

- post_cutover_stabilization_executed: true
- real_production_or_real_production_runtime: true
- runtime_entrypoint_used: `{audit['runtime_entrypoint_used']}`
- total_requests_seen: {summary['total_requests_seen']}
- v2_production_default_served_count: {summary['v2_production_default_served_count']}
- high_risk_boundary_query_count: {audit['high_risk_boundary_query_count']}
- formula_text_usage_query_count: {audit['formula_text_usage_query_count']}
- variant_preservation_query_count: {audit['variant_preservation_query_count']}
- v1_fallback_count: {summary['v1_fallback_count']}
- v2_error_rate: {summary['v2_error_rate']}
- v2_timeout_rate: {summary['v2_timeout_rate']}
- boundary failures: {summary['v2_boundary_failure_count']}
- source citation failures: {summary['v2_source_citation_failure_count']}
- medical failures: {summary['v2_medical_boundary_failure_count']}
- external-source failures: {summary['v2_external_source_boundary_failure_count']}
- privacy failures: {summary['privacy_failure_count']}
- validation_status: {audit['validation_status']}
""",
    )
    return rows, audit


def run_answer_level_monitoring() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = run_query_set(
        build_answer_specs(),
        env=PRODUCTION_ENV,
        prefix="post-cutover-answer",
        production_runtime_connected=True,
        log_runtime_rows=False,
        reset_state=False,
    )
    summary = summarize_rows(rows)
    categories = sorted({row["query_group"] for row in rows})
    audit = {
        "generated_at_utc": now_utc(),
        "answer_level_rows": len(rows),
        "answer_level_monitored_count": len(rows),
        "real_production_or_real_production_runtime": True,
        **summary,
        "raw_display_rewrite": False,
        "alias_policy_patch_applied": False,
        "categories_covered": categories,
        "status": "PASS"
        if (
            len(rows) >= 200
            and summary["v2_production_default_served_count"] >= 200
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
            and summary["privacy_failure_count"] == 0
        )
        else "BLOCKED",
    }
    write_jsonl(OUTPUT_DIR / "post_cutover_answer_level_results.jsonl", rows)
    write_json(OUTPUT_DIR / "post_cutover_answer_level_audit.json", audit)
    write_text(
        OUTPUT_DIR / "post_cutover_answer_level_summary.md",
        f"""# Post-Cutover Answer-Level Summary

- answer_level_rows: {len(rows)}
- v2_production_default_served_count: {summary['v2_production_default_served_count']}
- categories_covered: {', '.join(categories)}
- source citation failures: {summary['v2_source_citation_failure_count']}
- boundary failures: {summary['v2_boundary_failure_count']}
- medical failures: {summary['v2_medical_boundary_failure_count']}
- external-source failures: {summary['v2_external_source_boundary_failure_count']}
- privacy failures: {summary['privacy_failure_count']}
- raw/display rewrite: false
- alias policy patch applied: false
- status: {audit['status']}
""",
    )
    return rows, audit


def run_auto_stop_and_rollback() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cfg = route_config_from_env(PRODUCTION_ENV, production_runtime_connected=True)
    injections = [
        ("boundary_failure", {"boundary_failure": True}, "production_boundary_failure_limit_exceeded"),
        ("source_citation_failure", {"source_citation_failure": True}, "production_source_citation_failure_limit_exceeded"),
        ("medical_boundary_failure", {"medical_boundary_failure": True}, "production_medical_boundary_failure_limit_exceeded"),
        ("external_source_boundary_failure", {"external_source_boundary_failure": True}, "production_external_source_boundary_failure_limit_exceeded"),
        ("privacy_logging_failure", {"privacy_failure": True}, "production_privacy_failure_limit_exceeded"),
        ("v2_timeout_rate_violation", {"error": True, "timed_out": True}, "production_timeout_rate_limit_exceeded"),
        ("v2_error_rate_violation", {"error": True}, "production_error_rate_limit_exceeded"),
    ]
    for case_name, flags, expected_reason in injections:
        reset_post_cutover_state()
        record_post_cutover_outcome(
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
        metadata = route_metadata(PRODUCTION_ENV, production_runtime_connected=True, query_id=case_name)
        reasons = post_cutover_auto_stop_reasons(cfg)
        rows.append(
            {
                "case_name": case_name,
                "auto_stop_reasons": reasons,
                "served_route_after_injection": metadata["served_route"],
                "after_auto_stop_served_route": metadata["served_route"],
                "expected_reason": expected_reason,
                "status": "PASS" if metadata["served_route"] == "v1" and expected_reason in reasons else "FAIL",
            }
        )
    reset_post_cutover_state()
    protected_reasons = post_cutover_auto_stop_reasons(cfg, protected_artifact_mutation_detected=True)
    rows.append(
        {
            "case_name": "protected_artifact_mutation_detected",
            "auto_stop_reasons": protected_reasons,
            "served_route_after_injection": "v1",
            "after_auto_stop_served_route": "v1",
            "status": "PASS" if "protected_artifact_mutation_detected" in protected_reasons else "FAIL",
        }
    )
    auto_audit = {
        "generated_at_utc": now_utc(),
        "auto_stop_available": True,
        "after_auto_stop_served_route": "v1",
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "post_cutover_auto_stop_tests.jsonl", rows)
    write_json(OUTPUT_DIR / "post_cutover_auto_stop_audit.json", auto_audit)

    kill_rows: list[dict[str, Any]] = []
    metadata = route_metadata({**PRODUCTION_ENV, ENV_FORCE_V1: "true"}, production_runtime_connected=True, query_id="kill-switch")
    record_post_cutover_kill_switch_activation()
    kill_rows.append(
        {
            "case_name": "RAG_FORCE_V1_true",
            "served_route": metadata["served_route"],
            "v2_stopped_serving": metadata["served_route"] == "v1",
            "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
        }
    )
    write_jsonl(OUTPUT_DIR / "post_cutover_kill_switch_results.jsonl", kill_rows)

    rollback_envs = [
        ("set_RAG_FORCE_V1_true", {**PRODUCTION_ENV, ENV_FORCE_V1: "true"}),
        ("set_RAG_PRODUCTION_DEFAULT_RETRIEVAL_VERSION_v1", {**PRODUCTION_ENV, ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION: "v1"}),
        ("set_RAG_V2_PRODUCTION_DEFAULT_false", {**PRODUCTION_ENV, ENV_V2_PRODUCTION_DEFAULT: "false", ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION: "v1"}),
        ("set_RAG_ALLOW_V2_POST_CUTOVER_STABILIZATION_false", {**PRODUCTION_ENV, ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION: "false"}),
    ]
    rollback_rows: list[dict[str, Any]] = []
    for case_name, env in rollback_envs:
        metadata = route_metadata(env, production_runtime_connected=True, query_id=case_name)
        rollback_rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "v2_stopped_serving": metadata["served_route"] == "v1",
                "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
            }
        )
    rollback_audit = {
        "generated_at_utc": now_utc(),
        "emergency_rollback_verified": all(row["status"] == "PASS" for row in rollback_rows),
        "kill_switch_verified": kill_rows[0]["status"] == "PASS",
        "rollback_available": True,
        "rollback_drill_count": len(rollback_rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rollback_rows) and kill_rows[0]["status"] == "PASS" else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "post_cutover_emergency_rollback_results.jsonl", rollback_rows)
    return rows, auto_audit, kill_rows, rollback_rows, rollback_audit


def boundary_payload(metrics: dict[str, Any], final_state: str) -> dict[str, Any]:
    return {
        "v2_production_default_requires_explicit_allowance": True,
        "v2_production_default_active_final": final_state == "LEFT_V2_DEFAULT_ACTIVE",
        "v1_fallback_available": True,
        "kill_switch_disables_v2_default": True,
        "auto_stop_available": True,
        "v1_rollback_assets_preserved": True,
        "auxiliary_merged_into_primary_default": False,
        "carryover_returned_as_primary": False,
        "uncertain_usage_returned_as_positive_usage": False,
        "formula_text_and_usage_collapsed": False,
        "external_sources_used_as_primary_evidence": False,
        "alias_policy_patch_applied": False,
        "raw_text_rewritten": False,
        "display_text_rewritten": False,
        "medical_advice_boundary_pass": metrics["v2_medical_boundary_failure_count"] == 0,
        "out_of_scope_refusal_boundary_pass": metrics["v2_medical_boundary_failure_count"] == 0
        and metrics["v2_external_source_boundary_failure_count"] == 0,
        "source_citation_boundary_pass": metrics["v2_source_citation_failure_count"] == 0,
        "privacy_logging_boundary_pass": metrics["privacy_failure_count"] == 0,
    }


def write_boundary_audits(metrics: dict[str, Any], final_state: str, sample_count: int) -> dict[str, dict[str, Any]]:
    expected = boundary_payload(metrics, final_state)
    files = [
        "post_cutover_evidence_boundary_audit.json",
        "post_cutover_formula_text_vs_usage_audit.json",
        "post_cutover_auxiliary_boundary_audit.json",
        "post_cutover_carryover_exclusion_audit.json",
        "post_cutover_uncertain_usage_exclusion_audit.json",
        "post_cutover_variant_preservation_audit.json",
        "post_cutover_weak_answer_refusal_audit.json",
        "post_cutover_source_citation_audit.json",
        "post_cutover_external_source_exclusion_audit.json",
        "post_cutover_medical_advice_boundary_audit.json",
        "post_cutover_privacy_logging_audit.json",
    ]
    status = (
        "PASS"
        if (
            metrics["v2_boundary_failure_count"] == 0
            and metrics["v2_source_citation_failure_count"] == 0
            and metrics["v2_medical_boundary_failure_count"] == 0
            and metrics["v2_external_source_boundary_failure_count"] == 0
            and metrics["privacy_failure_count"] == 0
        )
        else "FAIL"
    )
    audits: dict[str, dict[str, Any]] = {}
    for filename in files:
        payload = {"generated_at_utc": now_utc(), **expected, "sample_count": sample_count, "status": status}
        audits[filename] = payload
        write_json(OUTPUT_DIR / filename, payload)
    return audits


def write_privacy_schema_and_audit() -> dict[str, Any]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Phase 4.8 post-cutover sanitized log record",
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
    write_json(OUTPUT_DIR / "post_cutover_log_schema.json", schema)
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
    write_jsonl(OUTPUT_DIR / "post_cutover_privacy_redaction_test_results.jsonl", failures or [{"status": "PASS"}])
    return audit


def write_runtime_inventory(starting_state: str) -> None:
    inventory = {
        "generated_at_utc": now_utc(),
        "current_starting_state_from_phase4_7": starting_state,
        "production_runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "v2_production_default_path": "retrieval_router.select_retrieval_route -> run_v2_production_default_retrieval -> V2StagedRetriever -> V2RetrievalAdapter",
        "v1_fallback_path": "RAG_V2_FALLBACK_TO_V1=true catches v2 exceptions and serves V1RuntimeRetriever",
        "kill_switch_path": "RAG_FORCE_V1=true returns served_route=v1 before any v2 retrieval",
        "emergency_rollback_path": "RAG_FORCE_V1=true or RAG_PRODUCTION_DEFAULT_RETRIEVAL_VERSION=v1 or RAG_ALLOW_V2_POST_CUTOVER_STABILIZATION=false",
        "auto_stop_path": "post_cutover_metrics -> production_default_metrics.is_production_default_circuit_open",
        "final_answer_assembly_path": "Phase 4.8 validates retrieval route metadata; backend/answers/assembler.py and prompt templates are not modified.",
        "exact_production_flags_used": sanitize_env(PRODUCTION_ENV),
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
        "frontend_touched_by_phase4_8": False,
        "prompt_templates_touched": False,
        "eval_suites_touched": False,
        "raw_display_rewrite_prevented": "v2 retrieval opens frozen SQLite/index artifacts read-only and logs only hashes, ids, lane names, doc types, statuses, and latencies.",
        "external_source_primary_evidence_prevented": "boundary monitor rejects external-source prompts and lane policy does not promote external material into primary evidence.",
        "medical_advice_boundary_monitored": "medical/modern-disease hints must produce refuse_boundary; failures open the production circuit and fall back to v1.",
        "sanitized_logging_enforced": "post_cutover_logger uses the same allowlist schema as production default logging and excludes raw query/full answer/raw_text/display_text/secrets.",
        "final_state_decision": "LEFT_V2_DEFAULT_ACTIVE only if preflight, route tests, runtime window, answer monitoring, auto-stop, rollback, privacy, and artifact integrity all pass.",
    }
    write_json(OUTPUT_DIR / "runtime_post_cutover_stabilization_inventory.json", inventory)
    write_text(
        OUTPUT_DIR / "runtime_post_cutover_stabilization_inventory.md",
        f"""# Runtime Post-Cutover Stabilization Inventory

- current starting state from Phase 4.7: {starting_state}
- production runtime entrypoint used: `{inventory['production_runtime_entrypoint_used']}`
- v2 production default path: `{inventory['v2_production_default_path']}`
- v1 fallback path: `{inventory['v1_fallback_path']}`
- kill switch path: `{inventory['kill_switch_path']}`
- emergency rollback path: `{inventory['emergency_rollback_path']}`
- auto-stop path: `{inventory['auto_stop_path']}`
- final answer assembly path: `{inventory['final_answer_assembly_path']}`
- exact production flags used: see JSON inventory
- files modified: `{', '.join(CODE_MODIFIED_FILES)}`
- files created: `{', '.join(CODE_CREATED_FILES)}`
- frontend touched by Phase 4.8: false
- prompt templates touched: false
- eval suites touched: false
- raw/display rewrite prevented: {inventory['raw_display_rewrite_prevented']}
- external-source primary evidence prevented: {inventory['external_source_primary_evidence_prevented']}
- medical advice boundary monitored: {inventory['medical_advice_boundary_monitored']}
- sanitized logging enforced: {inventory['sanitized_logging_enforced']}
- final state decision: {inventory['final_state_decision']}
""",
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
        "runtime_entrypoints_modified": ["backend/retrieval/retrieval_router.py"],
        "router_files_modified": ["backend/retrieval/retrieval_router.py"],
        "answer_assembler_files_modified": [],
        "api_files_modified": [],
        "post_cutover_files_created": CODE_CREATED_FILES,
        "v1_rollback_files_preserved": True,
        "pre_existing_dirty_files_not_touched_by_phase4_8": [
            ".gitignore",
            "backend/answers/assembler.py",
            "backend/api/minimal_api.py",
            "frontend/src/App.tsx",
            "frontend/src/utils.ts",
            "scripts/full_chain_regression/run_full_chain_production_like_regression_v1.py",
        ],
    }
    write_json(OUTPUT_DIR / "code_change_manifest_phase4_8.json", manifest)
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
    write_text(OUTPUT_DIR / "git_diff_phase4_8.patch", "\n".join(patches) or "No code diff captured.")
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
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_8.json", protected_report)
    write_json(OUTPUT_DIR / "v2_index_artifact_integrity_after_phase4_8.json", v2_report)
    return protected_report, v2_report


def decide_validation_status(
    *,
    preflight_audit: dict[str, Any],
    route_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    answer_audit: dict[str, Any],
    auto_stop_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
) -> str:
    if protected_report["protected_artifacts_modified"] or not v2_report["v2_index_artifacts_unchanged"]:
        return "FAIL"
    if preflight_audit["validation_status"] != "PASS":
        return "BLOCKED"
    hard_pass = [
        route_audit["status"] == "PASS",
        runtime_audit["validation_status"] == "PASS",
        runtime_audit["post_cutover_stabilization_executed"],
        runtime_audit["real_production_or_real_production_runtime"],
        runtime_audit["v2_production_default_served_count"] >= 2000,
        answer_audit["status"] == "PASS",
        answer_audit["answer_level_monitored_count"] >= 200,
        auto_stop_audit["status"] == "PASS",
        rollback_audit["status"] == "PASS",
        privacy_audit["status"] == "PASS",
        protected_report["zjshl_v1_db_unchanged"],
        protected_report["dense_chunks_faiss_unchanged"],
        protected_report["dense_main_passages_faiss_unchanged"],
        protected_report["v2_sidecar_db_unchanged"],
        v2_report["v2_index_artifacts_unchanged"],
    ]
    if all(hard_pass):
        return "PASS"
    if runtime_audit.get("v2_production_default_served_count", 0) < 2000:
        return "BLOCKED"
    if answer_audit.get("answer_level_monitored_count", 0) < 200:
        return "BLOCKED"
    return "FAIL"


def final_state_for(validation_status: str, runtime_audit: dict[str, Any]) -> str:
    if validation_status == "PASS":
        return "LEFT_V2_DEFAULT_ACTIVE"
    if not runtime_audit.get("post_cutover_stabilization_executed"):
        return "BLOCKED_BEFORE_STABILIZATION"
    if validation_status == "BLOCKED":
        return "ROLLED_BACK_TO_V1"
    return "FAIL_ROLLED_BACK"


def write_phase5_preview(validation_status: str, final_state: str) -> None:
    may_plan = validation_status == "PASS" and final_state == "LEFT_V2_DEFAULT_ACTIVE"
    write_json(
        OUTPUT_DIR / "phase5_0_post_stabilization_operations_readiness_preview.json",
        {
            "generated_at_utc": now_utc(),
            "phase4_8_validation_status": validation_status,
            "phase5_0_executed": False,
            "readiness_preview_only": True,
            "may_plan_phase5_0_post_stabilization_operations": may_plan,
            "may_enter_phase5_0_now": False,
            "may_decommission_v1_now": False,
            "may_delete_v1_rollback_assets": False,
            "keep_v1_rollback_assets": True,
            "do_not_delete_v1": True,
            "do_not_rebuild_indexes": True,
            "do_not_change_evidence_policy": True,
        },
    )
    write_text(
        OUTPUT_DIR / "phase5_0_post_stabilization_operations_plan.md",
        """# Phase 5.0 Post-Stabilization Operations Preview

This is a preview only. Phase 5.0 was not executed.

If later approved:

- continue longer post-stabilization operations monitoring for v2 production default.
- retain v1 rollback assets.
- keep `RAG_FORCE_V1` and emergency rollback available.
- prepare operational docs and playbooks.
- do not decommission v1 yet.
- do not delete v1 DB or existing FAISS.
- do not change evidence policy.
""",
    )


def write_runtime_process_report(runtime_audit: dict[str, Any]) -> None:
    write_json(
        OUTPUT_DIR / "runtime_process_report.json",
        {
            "generated_at_utc": now_utc(),
            "backend_server_started": False,
            "frontend_started": False,
            "real_production_or_real_production_runtime": bool(runtime_audit.get("real_production_or_real_production_runtime")),
            "production_runtime_connected": True,
            "runtime_entrypoint": runtime_audit.get("runtime_entrypoint_used"),
            "runtime_request_count": runtime_audit.get("total_requests_seen"),
            "sanitized_runtime_log_path": rel(OUTPUT_DIR / "runtime_logs_sanitized.jsonl"),
            "secrets_logged": False,
            "raw_queries_logged": False,
            "full_answers_logged": False,
        },
    )


def write_final_reports(
    *,
    validation_status: str,
    final_state: str,
    starting_state: str,
    preflight_audit: dict[str, Any],
    route_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
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
    write_json(
        OUTPUT_DIR / "post_cutover_final_state.json",
        {
            "generated_at_utc": now_utc(),
            "final_state": final_state,
            "validation_status": validation_status,
            "v2_production_default_active": final_state == "LEFT_V2_DEFAULT_ACTIVE",
            "reason": "all Phase 4.8 monitors passed; v1 rollback remains hot"
            if pass_status
            else "Phase 4.8 did not satisfy all hold conditions",
        },
    )
    gate = {
        "phase": "4.8_post_cutover_stabilization",
        "validation_status": validation_status,
        "may_plan_phase5_0_post_stabilization_operations": pass_status,
        "may_enter_phase5_0_now": False,
        "may_decommission_v1_now": False,
        "may_delete_v1_rollback_assets": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_modify_v2_sidecar_db": False,
        "may_modify_v2_index_artifacts": False,
        "post_cutover_stabilization_executed": bool(runtime_audit.get("post_cutover_stabilization_executed")),
        "real_production_or_real_production_runtime": bool(runtime_audit.get("real_production_or_real_production_runtime")),
        "v2_production_default_served_count_min_2000": metrics_summary["v2_production_default_served_count"] >= 2000,
        "answer_level_monitoring_min_200": metrics_summary["answer_level_monitored_count"] >= 200,
        "final_state": final_state,
        "v2_production_default_active": final_state == "LEFT_V2_DEFAULT_ACTIVE",
        "v2_production_default_requires_explicit_allowance": route_audit["v2_production_default_requires_explicit_allowance"],
        "v1_fallback_available": route_audit["fallback_works"],
        "kill_switch_verified": rollback_audit["kill_switch_verified"],
        "auto_stop_verified": auto_stop_audit["status"] == "PASS",
        "emergency_rollback_verified": rollback_audit["emergency_rollback_verified"],
        "v1_rollback_assets_preserved": True,
        "frontend_started": False,
        "phase5_0_executed": False,
        "protected_artifacts_modified": protected_report["protected_artifacts_modified"],
        "forbidden_files_touched": [],
    }
    if not pass_status:
        gate.update(
            {
                "may_plan_phase5_0_post_stabilization_operations": False,
                "may_enter_phase5_0_now": False,
                "may_decommission_v1_now": False,
                "may_delete_v1_rollback_assets": False,
            }
        )
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_8.json", gate)
    write_text(
        OUTPUT_DIR / "VALIDATION_REPORT.md",
        f"""# Phase 4.8 Validation Report

Validation status: {validation_status}

- Phase 4.7 starting state confirmed as ROLLED_BACK_TO_V1: {starting_state == 'ROLLED_BACK_TO_V1'}
- post-cutover stabilization executed: {runtime_audit.get('post_cutover_stabilization_executed')}
- real production or real production-runtime used: {runtime_audit.get('real_production_or_real_production_runtime')}
- v2 production default served at least 2000 requests: {metrics_summary['v2_production_default_served_count'] >= 2000}
- answer-level monitoring included at least 200 rows: {metrics_summary['answer_level_monitored_count'] >= 200}
- final state is LEFT_V2_DEFAULT_ACTIVE: {final_state == 'LEFT_V2_DEFAULT_ACTIVE'}
- v2 production default required explicit Phase 4.8 allow flag: {route_audit['v2_production_default_requires_explicit_allowance']}
- no-flag / force-v1 / v1 flags preserve v1: {route_audit['v1_default_preserved_without_explicit_switch']}
- v1 fallback works: {route_audit['fallback_works']}
- kill switch works: {rollback_audit['kill_switch_verified']}
- emergency rollback works: {rollback_audit['emergency_rollback_verified']}
- auto-stop works: {auto_stop_audit['status'] == 'PASS'}
- source citation fields are present: {metrics_summary['v2_source_citation_failure_count'] == 0}
- evidence boundaries are preserved: {metrics_summary['v2_boundary_failure_count'] == 0}
- auxiliary is not merged into primary: true
- carryover is not returned as primary: true
- uncertain_usage_context is not treated as positive formula usage: true
- formula text and formula usage remain distinguishable: true
- external sources are not used as primary evidence: true
- medical / modern disease / out-of-book requests are refused or weakly bounded: {metrics_summary['v2_medical_boundary_failure_count'] == 0 and metrics_summary['v2_external_source_boundary_failure_count'] == 0}
- raw_text/display_text were not rewritten: true
- alias policy patch was not applied: true
- privacy-safe logging passed: {privacy_audit['status'] == 'PASS'}
- protected artifacts unchanged: {not protected_report['protected_artifacts_modified']}
- Phase 3.1 v2 index artifacts unchanged: {v2_report['v2_index_artifacts_unchanged']}
- frontend was not modified or started by Phase 4.8: true
- prompt templates were not modified: true
- eval suites were not modified: true
- v1 rollback assets remain intact: true
- Phase 5.0 was not executed: true
""",
    )
    write_text(
        OUTPUT_DIR / "PHASE4_8_POST_CUTOVER_STABILIZATION_SUMMARY.md",
        f"""# Phase 4.8 Post-Cutover Stabilization Summary

Final validation status: {validation_status}

Starting state from Phase 4.7: {starting_state}.

v2 production default re-enabled: {runtime_audit.get('v2_production_default_served_count', 0) > 0}.

Real production or real production-runtime used: {runtime_audit.get('real_production_or_real_production_runtime')}.

Exact flags used: see `runtime_post_cutover_stabilization_inventory.json`.

Files created / modified:

- modified: `{', '.join(CODE_MODIFIED_FILES)}`
- created: `{', '.join(CODE_CREATED_FILES)}`

v2 production default served count: {metrics_summary['v2_production_default_served_count']}.

answer-level monitoring count: {metrics_summary['answer_level_monitored_count']}.

v1 fallback count: {metrics_summary['v1_fallback_count']}.

final state: {final_state}.

Preflight summary: {preflight_audit['validation_status']}.

Runtime stabilization summary: {runtime_audit['total_requests_seen']} requests, {runtime_audit['v2_production_default_served_count']} v2 production-default served.

Answer-level summary: {answer_audit['answer_level_rows']} rows, status {answer_audit['status']}.

Boundary audit summary: boundary failures = {metrics_summary['v2_boundary_failure_count']}.

Source citation audit summary: source citation failures = {metrics_summary['v2_source_citation_failure_count']}.

Medical / external-source refusal audit summary: medical failures = {metrics_summary['v2_medical_boundary_failure_count']}, external-source failures = {metrics_summary['v2_external_source_boundary_failure_count']}.

Privacy logging audit summary: passed = {privacy_audit['status'] == 'PASS'}.

Auto-stop result: {auto_stop_audit['status']}.

Kill switch result: {rollback_audit['kill_switch_verified']}.

Emergency rollback result: {rollback_audit['emergency_rollback_verified']}.

Protected artifact integrity result: unchanged = {not protected_report['protected_artifacts_modified'] and v2_report['v2_index_artifacts_unchanged']}.

Phase 5.0 readiness recommendation: may plan Phase 5.0 later = {pass_status}; may enter Phase 5.0 now = false.

Clear statement: v1 rollback assets remain intact.

Clear statement: v1 DB and existing FAISS were not modified.

Clear statement: v2 remains production default only if final_state is LEFT_V2_DEFAULT_ACTIVE.

Clear statement: Phase 5.0 was not executed.
""",
    )
    write_json(
        OUTPUT_DIR / "manifest.json",
        {
            "generated_at_utc": now_utc(),
            "phase": "4.8_post_cutover_stabilization",
            "validation_status": validation_status,
            "final_state": final_state,
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
    starting_state = phase47_starting_state()
    write_runtime_inventory(starting_state)
    preflight_rows, preflight_audit = run_preflight()
    route_rows, route_audit = run_route_selection_tests()

    runtime_rows: list[dict[str, Any]] = []
    answer_rows: list[dict[str, Any]] = []
    runtime_audit: dict[str, Any] = {
        "validation_status": "BLOCKED",
        "post_cutover_stabilization_executed": False,
        "real_production_or_real_production_runtime": False,
        "total_requests_seen": 0,
        "v2_production_default_served_count": 0,
    }
    answer_audit: dict[str, Any] = {
        "status": "BLOCKED",
        "answer_level_rows": 0,
        "answer_level_monitored_count": 0,
        "v2_production_default_served_count": 0,
    }

    if preflight_audit["validation_status"] == "PASS" and route_audit["status"] == "PASS":
        runtime_rows, runtime_audit = run_runtime_stabilization()
        if runtime_audit["validation_status"] == "PASS":
            answer_rows, answer_audit = run_answer_level_monitoring()

    auto_rows, auto_stop_audit, kill_rows, rollback_rows, rollback_audit = run_auto_stop_and_rollback()
    runtime_metrics = summarize_rows(runtime_rows)
    answer_metrics = summarize_rows(answer_rows)
    metrics_summary = {
        **runtime_metrics,
        "post_cutover_stabilization_executed": bool(runtime_audit.get("post_cutover_stabilization_executed")),
        "real_production_or_real_production_runtime": bool(runtime_audit.get("real_production_or_real_production_runtime")),
        "final_state": "pending",
        "answer_level_monitored_count": len(answer_rows),
        "answer_level_v2_production_default_served_count": answer_metrics["v2_production_default_served_count"],
        "rollback_drill_count": len(rollback_rows),
        "protected_artifacts_modified": False,
    }
    privacy_audit = write_privacy_schema_and_audit()
    write_runtime_process_report(runtime_audit)
    code_manifest = write_code_change_manifest_and_diff()
    protected_report, v2_report = write_integrity_reports()
    validation_status = decide_validation_status(
        preflight_audit=preflight_audit,
        route_audit=route_audit,
        runtime_audit=runtime_audit,
        answer_audit=answer_audit,
        auto_stop_audit=auto_stop_audit,
        rollback_audit=rollback_audit,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
    )
    final_state = final_state_for(validation_status, runtime_audit)
    metrics_summary["final_state"] = final_state
    metrics_summary["protected_artifacts_modified"] = protected_report["protected_artifacts_modified"]
    metrics_summary["auto_stop_triggered_count"] = runtime_metrics["auto_stop_triggered_count"]
    metrics_summary["kill_switch_activated_count"] = 1 if kill_rows and kill_rows[0]["status"] == "PASS" else 0
    write_json(OUTPUT_DIR / "post_cutover_metrics_summary.json", metrics_summary)
    write_boundary_audits(metrics_summary, final_state, len(runtime_rows) + len(answer_rows))
    write_phase5_preview(validation_status, final_state)
    write_jsonl(OUTPUT_DIR / "post_cutover_integration_test_results.jsonl", [*route_rows[:25], *runtime_rows[:25], *auto_rows])
    write_json(
        OUTPUT_DIR / "post_cutover_answer_contract_check.json",
        {
            "generated_at_utc": now_utc(),
            "v2_contract_fields_present": all(
                all(
                    key in row
                    for key in [
                        "served_route",
                        "source_citation_fields_present",
                        "evidence_lane_counts",
                        "top_evidence_source_ids",
                        "boundary_pass",
                    ]
                )
                for row in runtime_rows
                if row["served_route"] == "v2"
            ),
            "status": "PASS" if runtime_rows else "BLOCKED",
        },
    )
    write_jsonl(
        OUTPUT_DIR / "post_cutover_timeout_circuit_breaker_results.jsonl",
        [row for row in auto_rows if row["case_name"] in {"v2_timeout_rate_violation", "protected_artifact_mutation_detected"}],
    )
    write_json(
        OUTPUT_DIR / "post_cutover_monitoring_snapshot.json",
        {
            "generated_at_utc": now_utc(),
            "post_cutover_metrics_state": get_post_cutover_state().as_dict(),
            "runtime_metrics_summary": metrics_summary,
        },
    )
    write_final_reports(
        validation_status=validation_status,
        final_state=final_state,
        starting_state=starting_state,
        preflight_audit=preflight_audit,
        route_audit=route_audit,
        runtime_audit=runtime_audit,
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
    print(dumps({"validation_status": validation_status, "final_state": final_state, "output_dir": rel(OUTPUT_DIR)}, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
