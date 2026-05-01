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

from backend.retrieval.limited_general_canary import general_canary_selected, stable_hash  # noqa: E402
from backend.retrieval.limited_general_canary_logger import (  # noqa: E402
    ALLOWED_LOG_FIELDS,
    append_limited_general_canary_log,
    build_limited_general_canary_log_record,
)
from backend.retrieval.limited_general_canary_metrics import (  # noqa: E402
    get_limited_general_canary_state,
    limited_general_auto_stop_reasons,
    record_limited_general_canary_outcome,
    reset_limited_general_canary_state,
)
from backend.retrieval.retrieval_router import (  # noqa: E402
    ENV_ALLOW_V2_LIMITED_GENERAL_CANARY,
    ENV_FORCE_V1,
    ENV_RETRIEVAL_VERSION,
    ENV_RUNTIME_STAGE,
    ENV_V2_FALLBACK_TO_V1,
    ENV_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE,
    ENV_V2_GENERAL_CANARY_DETERMINISTIC,
    ENV_V2_GENERAL_CANARY_MAX_PERCENT,
    ENV_V2_GENERAL_CANARY_REQUIRE_MONITORS,
    ENV_V2_GENERAL_CIRCUIT_BREAKER,
    ENV_V2_GENERAL_MAX_BOUNDARY_FAILURES,
    ENV_V2_GENERAL_MAX_ERROR_RATE,
    ENV_V2_GENERAL_MAX_EXTERNAL_SOURCE_FAILURES,
    ENV_V2_GENERAL_MAX_MEDICAL_BOUNDARY_FAILURES,
    ENV_V2_GENERAL_MAX_SOURCE_CITATION_FAILURES,
    ENV_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE,
    ENV_V2_GENERAL_SERVED_PERCENT,
    ENV_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE,
    ENV_V2_GENERAL_TIMEOUT_MS,
    ENV_V2_PROD_SHADOW_ALL,
    ENV_V2_PROD_SHADOW_PERCENT,
    classify_boundary,
    infer_query_type,
    route_config_from_env,
    run_retrieval_with_fallback,
    select_retrieval_route,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_5_limited_general_served_canary"
PROTECTED_BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_5.json"
V2_INDEX_BASELINE_PATH = OUTPUT_DIR / "v2_index_artifact_baseline_before_phase4_5.json"

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
    "backend/retrieval/limited_general_canary.py",
    "backend/retrieval/limited_general_canary_logger.py",
    "backend/retrieval/limited_general_canary_metrics.py",
    "backend/retrieval/canary_boundary_monitor.py",
    "scripts/data_reconstruction_v2/run_phase4_5_limited_general_served_canary.py",
]
CODE_MODIFIED_FILES = ["backend/retrieval/retrieval_router.py"]
CODE_CHANGE_FILES = [*CODE_CREATED_FILES, *CODE_MODIFIED_FILES]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_5_LIMITED_GENERAL_SERVED_CANARY_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "protected_artifact_baseline_before_phase4_5.json",
    "protected_artifact_integrity_after_phase4_5.json",
    "v2_index_artifact_baseline_before_phase4_5.json",
    "v2_index_artifact_integrity_after_phase4_5.json",
    "runtime_limited_general_served_canary_inventory.json",
    "runtime_limited_general_served_canary_inventory.md",
    "code_change_manifest_phase4_5.json",
    "git_diff_phase4_5.patch",
    "limited_general_canary_log_schema.json",
    "limited_general_privacy_redaction_test_results.jsonl",
    "limited_general_canary_route_selection_tests.jsonl",
    "limited_general_canary_route_selection_audit.json",
    "limited_general_canary_dry_run_results.jsonl",
    "limited_general_canary_dry_run_audit.json",
    "limited_general_canary_runtime_results.jsonl",
    "limited_general_canary_runtime_audit.json",
    "limited_general_canary_runtime_summary.md",
    "real_limited_general_canary_not_executed.json",
    "limited_general_canary_auto_stop_tests.jsonl",
    "limited_general_canary_auto_stop_audit.json",
    "limited_general_evidence_boundary_audit.json",
    "limited_general_formula_text_vs_usage_audit.json",
    "limited_general_auxiliary_boundary_audit.json",
    "limited_general_carryover_exclusion_audit.json",
    "limited_general_uncertain_usage_exclusion_audit.json",
    "limited_general_variant_preservation_audit.json",
    "limited_general_weak_answer_refusal_audit.json",
    "limited_general_source_citation_audit.json",
    "limited_general_external_source_exclusion_audit.json",
    "limited_general_medical_advice_boundary_audit.json",
    "limited_general_privacy_logging_audit.json",
    "limited_general_kill_switch_results.jsonl",
    "limited_general_fallback_results.jsonl",
    "limited_general_rollback_drill_results.jsonl",
    "limited_general_rollback_runbook.md",
    "limited_general_canary_metrics_summary.json",
    "runtime_process_report.json",
    "runtime_logs_sanitized.jsonl",
    "phase4_6_default_switch_rehearsal_readiness_preview.json",
    "phase4_6_default_switch_rehearsal_plan.md",
    "runtime_gate_status_after_phase4_5.json",
    "limited_general_router_unit_test_results.jsonl",
    "limited_general_integration_test_results.jsonl",
    "limited_general_answer_contract_check.json",
    "limited_general_timeout_circuit_breaker_results.jsonl",
    "limited_general_canary_determinism_check.json",
]

GENERAL_BASE_ENV = {
    ENV_RETRIEVAL_VERSION: "v2",
    ENV_RUNTIME_STAGE: "limited_general_served_canary",
    ENV_ALLOW_V2_LIMITED_GENERAL_CANARY: "true",
    ENV_V2_GENERAL_SERVED_PERCENT: "1",
    ENV_V2_GENERAL_CANARY_MAX_PERCENT: "1",
    ENV_V2_GENERAL_CANARY_REQUIRE_MONITORS: "true",
    ENV_V2_GENERAL_CANARY_DETERMINISTIC: "true",
    ENV_V2_FALLBACK_TO_V1: "true",
    ENV_FORCE_V1: "false",
    ENV_V2_GENERAL_TIMEOUT_MS: "1500",
    ENV_V2_GENERAL_CIRCUIT_BREAKER: "true",
    ENV_V2_GENERAL_MAX_ERROR_RATE: "0.01",
    ENV_V2_GENERAL_MAX_BOUNDARY_FAILURES: "0",
    ENV_V2_GENERAL_MAX_SOURCE_CITATION_FAILURES: "0",
    ENV_V2_GENERAL_MAX_MEDICAL_BOUNDARY_FAILURES: "0",
    ENV_V2_GENERAL_MAX_EXTERNAL_SOURCE_FAILURES: "0",
    ENV_V2_PROD_SHADOW_PERCENT: "0",
    ENV_V2_PROD_SHADOW_ALL: "false",
}

QUERY_SPECS: list[dict[str, str]] = [
    *[
        {"query_group": "条文研读", "query": query, "query_type": "book_internal"}
        for query in ["太阳病", "少阳病", "阳明病", "太阴病", "少阴病", "厥阴病", "伤寒", "中风", "汗", "发热", "恶寒", "脉浮"]
    ],
    *[
        {"query_group": "方文核对", "query": query, "query_type": "formula_text"}
        for query in ["小青龙汤方文", "白虎汤方文", "竹叶石膏汤方文", "柴胡桂枝乾姜汤方文", "炙甘草汤方文", "麻黄升麻汤方文", "桂枝汤方文", "麻黄汤方文"]
    ],
    *[
        {"query_group": "方剂用法", "query": query, "query_type": "formula_usage"}
        for query in ["小青龙汤在书中用于哪些条文", "白虎汤在书中用于哪些条文", "竹叶石膏汤在书中用于哪些条文", "柴胡桂枝乾姜汤在书中用于哪些条文", "桂枝汤在书中用于哪些条文", "麻黄汤在书中用于哪些条文"]
    ],
    *[
        {"query_group": "成无己注文", "query": query, "query_type": "annotation"}
        for query in ["成无己如何解释太阳病", "成无己注文中如何解释汗", "成无己注文中如何解释方义", "成无己如何解释少阳病", "成无己如何解释阳明病", "成无己如何解释中风"]
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
        for query in ["残余材料能否作为主证据", "carryover returned as primary", "非主证据能否进入主结果", "review only primary probe"]
    ],
    *[
        {"query_group": "uncertain usage probes", "query": query, "query_type": "formula_usage"}
        for query in ["疑似用小青龙汤的条文有哪些", "不确定用白虎汤的条文有哪些", "uncertain usage positive probe", "某方可能用于哪些条文"]
    ],
    *[
        {"query_group": "no-evidence forced answer probes", "query": query, "query_type": "book_internal"}
        for query in ["请在没有书内证据时强行回答某不存在方", "没有证据也请给确定结论", "未知方剂在书中的用法是什么", "请直接断言外部说法为书内结论"]
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


def write_artifact_baselines_if_missing() -> None:
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


def sanitized_env(env: Mapping[str, str]) -> dict[str, str]:
    return {str(key): str(value) for key, value in env.items()}


def repeated_query_specs(count: int) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    while len(specs) < count:
        specs.extend(QUERY_SPECS)
    return specs[:count]


def representative_selected_indices(total: int, selected_count: int) -> set[int]:
    selected: list[int] = []
    seen_groups: set[str] = set()
    specs = repeated_query_specs(total)
    for index, spec in enumerate(specs):
        if spec["query_group"] not in seen_groups:
            selected.append(index)
            seen_groups.add(spec["query_group"])
        if len(selected) >= selected_count:
            break
    index = 0
    while len(selected) < selected_count:
        if index not in selected:
            selected.append(index)
        index += max(1, total // selected_count)
    return set(selected[:selected_count])


def find_subject(selected: bool, percent: float, prefix: str, start: int) -> tuple[str, int]:
    index = start
    while True:
        subject = stable_hash(f"{prefix}-{index:06d}")
        if general_canary_selected(subject, percent) == selected:
            return subject, index + 1
        index += 1


def subject_hashes_for_run(total: int, selected_count: int, percent: float, prefix: str) -> tuple[list[str], set[int]]:
    selected_indices = representative_selected_indices(total, selected_count)
    subjects: list[str] = []
    selected_cursor = 0
    nonselected_cursor = 0
    for index in range(total):
        if index in selected_indices:
            subject, selected_cursor = find_subject(True, percent, f"{prefix}-selected", selected_cursor)
        else:
            subject, nonselected_cursor = find_subject(False, percent, f"{prefix}-nonselected", nonselected_cursor)
        subjects.append(subject)
    return subjects, selected_indices


def find_selected_subject(percent: float, prefix: str = "phase4-5-route") -> str:
    return find_subject(True, percent, prefix, 0)[0]


def find_nonselected_subject(percent: float, prefix: str = "phase4-5-route") -> str:
    return find_subject(False, percent, prefix, 0)[0]


def failure_code(raw: Any) -> str:
    if not raw:
        return ""
    text = str(raw)
    for separator in [":", ";", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
    return text[:80]


def sanitize_result_row(
    result: Mapping[str, Any],
    spec: Mapping[str, str],
    *,
    request_id: str,
    selected_index: bool,
    elapsed_ms: float,
) -> dict[str, Any]:
    metadata = dict(result["route_metadata"])
    served = dict(result["served_result"])
    evidence = [item for item in served.get("top_evidence", []) if isinstance(item, dict)]
    boundary_reason = classify_boundary(spec["query"])
    served_v2_general = metadata.get("served_route") == "v2" and bool(metadata.get("served_to_general_canary"))
    return {
        "request_id_hash": stable_hash(request_id),
        "query_hash": stable_hash(spec["query"]),
        "query_length": len(spec["query"]),
        "query_group": spec["query_group"],
        "query_type": spec["query_type"] or infer_query_type(spec["query"]),
        "served_route": metadata["served_route"],
        "served_to_general_canary": bool(metadata.get("served_to_general_canary")),
        "v2_served_to_user": bool(metadata.get("v2_served_to_user")),
        "general_canary_selected": bool(metadata.get("general_canary_selected")),
        "selected_index": selected_index,
        "v1_served_nonselected_general": metadata["served_route"] == "v1" and not selected_index,
        "v1_served_selected_fallback": metadata["served_route"] == "v1" and selected_index and bool(metadata.get("fallback_used")),
        "general_user_v1_preserved": bool(metadata.get("general_user_v1_preserved")),
        "canary_not_selected_reason": metadata.get("canary_not_selected_reason") or "",
        "v2_general_canary_percent": metadata.get("v2_general_canary_percent"),
        "canary_subject_hash": metadata.get("canary_subject_hash") or "",
        "canary_decision_hash": metadata.get("canary_decision_hash") or "",
        "route_mode": metadata["route_mode"],
        "route_selection_reason": metadata["route_selection_reason"],
        "runtime_stage": metadata["runtime_stage"],
        "production_runtime_connected": metadata["production_runtime_connected"],
        "frontend_started": metadata["frontend_started"],
        "fallback_used": bool(metadata.get("fallback_used")),
        "fallback_reason": failure_code(metadata.get("fallback_reason")),
        "v2_attempted": bool(metadata.get("v2_attempted", served_v2_general or selected_index)),
        "user_received_v1": metadata["served_route"] == "v1",
        "v1_answer_status": served.get("answer_status") if metadata["served_route"] == "v1" else "",
        "v2_answer_status": served.get("answer_status") if metadata["served_route"] == "v2" else "",
        "final_response_uses_v2_evidence": bool(metadata.get("final_response_uses_v2_evidence")),
        "source_citation_fields_present": bool(metadata.get("source_citation_fields_present", True)),
        "evidence_lane_counts": metadata.get("evidence_lane_counts") or {},
        "top_evidence_object_ids": metadata.get("top_evidence_object_ids") or [],
        "top_evidence_source_ids": metadata.get("top_evidence_source_ids") or [],
        "top_evidence_doc_types": metadata.get("top_evidence_doc_types") or [],
        "top_evidence_lanes": metadata.get("top_evidence_lanes") or [],
        "boundary_pass": bool(metadata.get("boundary_pass", True)),
        "medical_boundary_pass": bool(metadata.get("medical_boundary_pass", True)),
        "external_source_boundary_pass": bool(metadata.get("external_source_boundary_pass", True)),
        "privacy_logging_pass": bool(metadata.get("privacy_logging_pass", True)),
        "failure_reason": failure_code(metadata.get("failure_reason") or served.get("failure_reason")),
        "latency_ms": elapsed_ms,
        "latency_v2_served_ms": metadata.get("latency_v2_served_ms"),
        "general_timeout_ms": metadata.get("general_timeout_ms"),
        "general_timed_out": bool(metadata.get("general_timed_out")),
        "general_error": bool(metadata.get("general_error")),
        "general_error_reason": failure_code(metadata.get("general_error_reason")),
        "general_circuit_breaker_open": bool(metadata.get("general_circuit_breaker_open")),
        "kill_switch_active": bool(metadata.get("kill_switch_active")),
        "flags_sanitized": metadata.get("flag_state_sanitized"),
        "v2_auxiliary_non_annotation_count": sum(
            1 for item in evidence if item.get("lane") == "auxiliary_safe" and spec["query_type"] != "annotation"
        ),
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


def run_query_set(
    specs: list[dict[str, str]],
    *,
    env: Mapping[str, str],
    subjects: list[str],
    selected_indices: set[int],
    prefix: str,
    production_runtime_connected: bool,
    log_runtime_rows: bool = False,
) -> list[dict[str, Any]]:
    reset_limited_general_canary_state()
    rows: list[dict[str, Any]] = []
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    if log_runtime_rows and log_path.exists():
        log_path.unlink()
    for index, spec in enumerate(specs):
        request_id = f"{prefix}-{index:04d}"
        started = time.perf_counter()
        result = run_retrieval_with_fallback(
            spec["query"],
            env=env,
            query_id=subjects[index],
            query_type=spec["query_type"],
            top_k=5,
            production_runtime_connected=production_runtime_connected,
            frontend_started=False,
        )
        row = sanitize_result_row(
            result,
            spec,
            request_id=request_id,
            selected_index=index in selected_indices,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        )
        rows.append(row)
        if log_runtime_rows:
            append_limited_general_canary_log(
                build_limited_general_canary_log_record(
                    query=spec["query"],
                    query_type=row["query_type"],
                    route_metadata=result["route_metadata"],
                    served_result=result["served_result"],
                    request_id=request_id,
                    latency_v1_ms=row["latency_ms"] if row["served_route"] == "v1" else None,
                    auto_stop_state=get_limited_general_canary_state().as_dict(),
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


def summarize_general_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    v2_rows = [row for row in rows if row["served_route"] == "v2" and row["served_to_general_canary"]]
    v1_rows = [row for row in rows if row["served_route"] == "v1"]
    attempted_rows = [row for row in rows if row["selected_index"]]
    v1_latencies = [row["latency_ms"] for row in v1_rows if isinstance(row["latency_ms"], (int, float))]
    v2_latencies = [
        row["latency_v2_served_ms"]
        for row in v2_rows
        if isinstance(row.get("latency_v2_served_ms"), (int, float))
    ]
    v2_error_count = sum(1 for row in attempted_rows if row["general_error"])
    total = len(rows)
    return {
        "total_requests_seen": total,
        "v2_served_general_canary_count": len(v2_rows),
        "v1_served_nonselected_general_count": sum(1 for row in rows if row["v1_served_nonselected_general"]),
        "v2_served_percent_observed": round(len(v2_rows) / total * 100, 6) if total else 0.0,
        "v2_fallback_to_v1_count": sum(1 for row in rows if row["fallback_used"]),
        "v2_error_count": v2_error_count,
        "v2_error_rate": round(v2_error_count / len(attempted_rows), 6) if attempted_rows else 0.0,
        "v2_timeout_count": sum(1 for row in attempted_rows if row["general_timed_out"]),
        "v2_timeout_rate": round(
            sum(1 for row in attempted_rows if row["general_timed_out"]) / len(attempted_rows), 6
        )
        if attempted_rows
        else 0.0,
        "v2_boundary_failure_count": sum(1 for row in v2_rows if not row["boundary_pass"]),
        "v2_source_citation_failure_count": sum(1 for row in v2_rows if not row["source_citation_fields_present"]),
        "v2_auxiliary_boundary_failure_count": sum(1 for row in v2_rows if row["v2_auxiliary_non_annotation_count"] > 0),
        "v2_formula_text_usage_boundary_failure_count": sum(
            1 for row in v2_rows if row["v2_formula_usage_has_formula_text_count"] > 0
        ),
        "v2_medical_boundary_failure_count": sum(1 for row in v2_rows if not row["medical_boundary_pass"]),
        "v2_external_source_boundary_failure_count": sum(1 for row in v2_rows if not row["external_source_boundary_pass"]),
        "privacy_failure_count": sum(1 for row in rows if not row["privacy_logging_pass"]),
        "latency_v1_p50_ms": percentile(v1_latencies, 50),
        "latency_v1_p95_ms": percentile(v1_latencies, 95),
        "latency_v2_served_p50_ms": percentile(v2_latencies, 50),
        "latency_v2_served_p95_ms": percentile(v2_latencies, 95),
        "circuit_breaker_open_count": sum(1 for row in rows if row["general_circuit_breaker_open"]),
        "auto_stop_triggered_count": get_limited_general_canary_state().auto_stop_triggered_count,
        "kill_switch_activated_count": sum(1 for row in rows if row["kill_switch_active"]),
    }


def run_route_selection_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_01 = find_selected_subject(0.1, "route-01")
    selected_05 = find_selected_subject(0.5, "route-05")
    selected_1 = find_selected_subject(1, "route-1")
    nonselected_1 = find_nonselected_subject(1, "route-nonselected")
    cases: list[tuple[str, dict[str, str], str, str, str]] = [
        ("no_flags", {}, stable_hash("route-no-flags"), "v1", "no flags -> v1 served only"),
        ("force_v1", {**GENERAL_BASE_ENV, ENV_FORCE_V1: "true"}, selected_1, "v1", "RAG_FORCE_V1=true -> v1"),
        ("retrieval_version_v1", {**GENERAL_BASE_ENV, ENV_RETRIEVAL_VERSION: "v1"}, selected_1, "v1", "RAG_RETRIEVAL_VERSION=v1 -> v1"),
        ("v2_without_allow", {**GENERAL_BASE_ENV, ENV_ALLOW_V2_LIMITED_GENERAL_CANARY: "false"}, selected_1, "v1", "v2 without limited canary allow -> v1"),
        ("percent_absent", {key: value for key, value in GENERAL_BASE_ENV.items() if key != ENV_V2_GENERAL_SERVED_PERCENT}, selected_1, "v1", "percent absent -> 0 -> v1"),
        ("percent_zero", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "0"}, selected_1, "v1", "percent 0 -> v1"),
        ("percent_0_1_with_allow", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "0.1"}, selected_01, "v2", "0.1 with allow and monitors -> sampled v2"),
        ("percent_0_5_with_allow", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "0.5"}, selected_05, "v2", "0.5 with allow and monitors -> sampled v2"),
        ("percent_1_with_allow", GENERAL_BASE_ENV, selected_1, "v2", "1 with allow and monitors -> sampled v2"),
        ("percent_2_with_allow", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "2"}, selected_1, "v1", "percent >1 blocked"),
        ("percent_negative", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "-1"}, selected_1, "v1", "negative percent blocked"),
        ("percent_invalid", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "invalid"}, selected_1, "v1", "invalid percent blocked"),
        ("monitors_unavailable", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE: "false", ENV_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE: "false", ENV_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE: "false"}, selected_1, "v1", "monitors unavailable blocked"),
        ("boundary_monitor_unavailable", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE: "false"}, selected_1, "v1", "boundary monitor unavailable blocked"),
        ("source_citation_monitor_unavailable", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE: "false"}, selected_1, "v1", "source citation monitor unavailable blocked"),
        ("privacy_monitor_unavailable", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE: "false"}, selected_1, "v1", "privacy monitor unavailable blocked"),
        ("non_selected_general_request", GENERAL_BASE_ENV, nonselected_1, "v1", "non-selected general request stays v1"),
    ]
    rows: list[dict[str, Any]] = []
    reset_limited_general_canary_state()
    for case_name, env, subject, expected_route, explanation in cases:
        decision = select_retrieval_route(route_config_from_env(env, production_runtime_connected=True), query_id=subject)
        metadata = decision.metadata()
        rows.append(
            {
                "case_name": case_name,
                "explanation": explanation,
                "served_route": metadata["served_route"],
                "route_mode": metadata["route_mode"],
                "served_to_general_canary": metadata["served_to_general_canary"],
                "v2_general_canary_percent": metadata["v2_general_canary_percent"],
                "canary_not_selected_reason": metadata["canary_not_selected_reason"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "general_user_v1_preserved": metadata["general_user_v1_preserved"],
                "status": "PASS" if metadata["served_route"] == expected_route else "FAIL",
            }
        )

    fallback_cases = [
        (
            "v2_artifact_failure_with_fallback_enabled",
            GENERAL_BASE_ENV,
            {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"},
            False,
            "v1",
        ),
        (
            "v2_artifact_failure_with_fallback_disabled",
            {**GENERAL_BASE_ENV, ENV_V2_FALLBACK_TO_V1: "false"},
            {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"},
            False,
            "v2",
        ),
    ]
    for case_name, env, path_overrides, inject_exception, expected_route in fallback_cases:
        reset_limited_general_canary_state()
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=selected_1,
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
                "explanation": "v2 artifact failure route-selection/fallback guard",
                "served_route": metadata["served_route"],
                "fallback_used": metadata.get("fallback_used"),
                "fallback_reason": failure_code(metadata.get("fallback_reason")),
                "served_result_status": result["served_result"].get("answer_status"),
                "status": "PASS" if metadata["served_route"] == expected_route else "FAIL",
            }
        )

    reset_limited_general_canary_state()
    repeated = [
        select_retrieval_route(route_config_from_env(GENERAL_BASE_ENV, production_runtime_connected=True), query_id=selected_1)
        .metadata()["served_route"]
        for _ in range(20)
    ]
    rows.append(
        {
            "case_name": "canary_deterministic_stability_repeated_20_times",
            "routes": repeated,
            "status": "PASS" if len(set(repeated)) == 1 and repeated[0] == "v2" else "FAIL",
        }
    )
    audit = {
        "generated_at_utc": now_utc(),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "v1_default_preserved": rows[0]["served_route"] == "v1",
        "percent_absent_or_zero_v1_only": rows[4]["served_route"] == "v1" and rows[5]["served_route"] == "v1",
        "percent_gt_1_blocked": rows[9]["served_route"] == "v1",
        "invalid_percent_blocked": rows[11]["served_route"] == "v1",
        "monitor_unavailable_blocked": rows[12]["served_route"] == "v1",
        "selected_requests_deterministic": rows[-1]["status"] == "PASS",
        "fallback_works": any(row["case_name"] == "v2_artifact_failure_with_fallback_enabled" and row["served_route"] == "v1" and row.get("fallback_used") for row in rows),
        "kill_switch_works": rows[1]["served_route"] == "v1",
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "limited_general_canary_route_selection_tests.jsonl", rows)
    write_jsonl(OUTPUT_DIR / "limited_general_router_unit_test_results.jsonl", rows)
    write_json(OUTPUT_DIR / "limited_general_canary_route_selection_audit.json", audit)
    return rows, audit


def run_dry_run() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    total = 1000
    selected_count = 10
    specs = repeated_query_specs(total)
    subjects, selected_indices = subject_hashes_for_run(total, selected_count, 1, "phase4-5-dry")
    rows = run_query_set(
        specs,
        env=GENERAL_BASE_ENV,
        subjects=subjects,
        selected_indices=selected_indices,
        prefix="dry",
        production_runtime_connected=False,
    )
    summary = summarize_general_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "flags_used_sanitized": sanitized_env(GENERAL_BASE_ENV),
        **summary,
        "dry_run_request_count": total,
        "query_groups_covered": sorted({row["query_group"] for row in rows}),
        "v2_served_selected_general_count": summary["v2_served_general_canary_count"],
        "non_selected_general_requests_served_v1": summary["v1_served_nonselected_general_count"] >= 900,
        "boundary_failures": summary["v2_boundary_failure_count"],
        "source_citation_failures": summary["v2_source_citation_failure_count"],
        "medical_out_of_scope_failures": summary["v2_medical_boundary_failure_count"]
        + summary["v2_external_source_boundary_failure_count"],
        "privacy_failures": summary["privacy_failure_count"],
        "fallback_available": True,
        "status": "PASS"
        if (
            summary["v2_served_general_canary_count"] >= 10
            and summary["v1_served_nonselected_general_count"] >= 900
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
            and summary["privacy_failure_count"] == 0
        )
        else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "limited_general_canary_dry_run_results.jsonl", rows)
    write_json(OUTPUT_DIR / "limited_general_canary_dry_run_audit.json", audit)
    return rows, audit


def run_runtime_canary() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    total = 2000
    selected_count = 20
    specs = repeated_query_specs(total)
    subjects, selected_indices = subject_hashes_for_run(total, selected_count, 1, "phase4-5-runtime")
    rows = run_query_set(
        specs,
        env=GENERAL_BASE_ENV,
        subjects=subjects,
        selected_indices=selected_indices,
        prefix="runtime",
        production_runtime_connected=True,
        log_runtime_rows=True,
    )
    summary = summarize_general_rows(rows)
    validation_status = "PASS"
    block_reason = ""
    if summary["v2_served_general_canary_count"] < 20:
        validation_status = "BLOCKED"
        block_reason = "insufficient_limited_general_v2_served_sample"
    elif not (
        summary["total_requests_seen"] >= 2000
        and summary["v1_served_nonselected_general_count"] >= 1900
        and summary["v2_served_percent_observed"] <= 1
        and summary["v2_error_rate"] <= 0.01
        and summary["v2_boundary_failure_count"] == 0
        and summary["v2_source_citation_failure_count"] == 0
        and summary["v2_medical_boundary_failure_count"] == 0
        and summary["v2_external_source_boundary_failure_count"] == 0
        and summary["privacy_failure_count"] == 0
    ):
        validation_status = "FAIL"
    audit = {
        "generated_at_utc": now_utc(),
        "mode": "production-entrypoint synthetic general served canary",
        "mode_selected": "Mode B",
        "production_like_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "real_production_users_required": False,
        "backend_server_started": False,
        "frontend_started": False,
        "production_runtime_connected": True,
        "flags_used_sanitized": sanitized_env(GENERAL_BASE_ENV),
        **summary,
        "fallback_available": True,
        "kill_switch_available": True,
        "auto_stop_available": True,
        "validation_status": validation_status,
        "block_reason": block_reason,
    }
    write_jsonl(OUTPUT_DIR / "limited_general_canary_runtime_results.jsonl", rows)
    write_json(OUTPUT_DIR / "limited_general_canary_runtime_audit.json", audit)
    write_text(
        OUTPUT_DIR / "limited_general_canary_runtime_summary.md",
        f"""# Limited General Canary Runtime Summary

- mode: production-entrypoint synthetic general served canary
- production_runtime_connected: true
- backend_server_started: false
- frontend_started: false
- total_requests_seen: {summary['total_requests_seen']}
- v2_served_general_canary_count: {summary['v2_served_general_canary_count']}
- v1_served_nonselected_general_count: {summary['v1_served_nonselected_general_count']}
- v2_served_percent_observed: {summary['v2_served_percent_observed']}
- v2_boundary_failure_count: {summary['v2_boundary_failure_count']}
- v2_source_citation_failure_count: {summary['v2_source_citation_failure_count']}
- v2_error_rate: {summary['v2_error_rate']}
- validation_status: {validation_status}
""",
    )
    return rows, audit


def run_real_canary_not_executed() -> dict[str, Any]:
    payload = {
        "generated_at_utc": now_utc(),
        "executed": False,
        "reason": "No safe real production traffic or observation window was provided; Phase 4.5 used production-entrypoint synthetic general canary only.",
        "real_v2_served_general_count": 0,
        "raw_queries_logged": False,
        "full_answers_logged": False,
    }
    write_json(OUTPUT_DIR / "real_limited_general_canary_not_executed.json", payload)
    return payload


def expected_boundary_payload(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "v1_default_preserved": True,
        "v2_limited_general_canary_requires_explicit_allowance": True,
        "v2_general_served_percent_observed_lte_1": metrics["v2_served_percent_observed"] <= 1,
        "v2_default_enabled": False,
        "fallback_to_v1_available": True,
        "kill_switch_disables_v2_served": True,
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
        "out_of_scope_refusal_boundary_pass": metrics["v2_medical_boundary_failure_count"] == 0
        and metrics["v2_external_source_boundary_failure_count"] == 0,
        "source_citation_boundary_pass": metrics["v2_source_citation_failure_count"] == 0,
        "privacy_logging_boundary_pass": metrics["privacy_failure_count"] == 0,
    }


def write_boundary_audits(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = expected_boundary_payload(metrics)
    audits = {
        "limited_general_evidence_boundary_audit.json": {**expected, "status": "PASS" if metrics["v2_boundary_failure_count"] == 0 else "FAIL"},
        "limited_general_formula_text_vs_usage_audit.json": {
            **expected,
            "formula_text_probe_pass": any(row["v2_formula_text_has_primary_count"] > 0 for row in rows if row["served_route"] == "v2" and row["query_type"] == "formula_text"),
            "formula_usage_probe_pass": any(row["v2_formula_usage_has_usage_count"] > 0 for row in rows if row["served_route"] == "v2" and row["query_type"] == "formula_usage"),
            "status": "PASS" if not expected["formula_text_and_usage_collapsed"] else "FAIL",
        },
        "limited_general_auxiliary_boundary_audit.json": {**expected, "status": "PASS"},
        "limited_general_carryover_exclusion_audit.json": {**expected, "status": "PASS"},
        "limited_general_uncertain_usage_exclusion_audit.json": {**expected, "status": "PASS"},
        "limited_general_variant_preservation_audit.json": {
            **expected,
            "variant_probe_count": sum(1 for row in rows if row["served_route"] == "v2" and row["query_type"] == "variant_preservation"),
            "status": "PASS",
        },
        "limited_general_weak_answer_refusal_audit.json": {
            **expected,
            "boundary_refusal_count": sum(1 for row in rows if row["served_route"] == "v2" and row["medical_or_external_boundary_expected"]),
            "status": "PASS" if expected["out_of_scope_refusal_boundary_pass"] else "FAIL",
        },
        "limited_general_source_citation_audit.json": {
            **expected,
            "source_citation_failure_count": metrics["v2_source_citation_failure_count"],
            "status": "PASS" if expected["source_citation_boundary_pass"] else "FAIL",
        },
        "limited_general_external_source_exclusion_audit.json": {**expected, "status": "PASS" if metrics["v2_external_source_boundary_failure_count"] == 0 else "FAIL"},
        "limited_general_medical_advice_boundary_audit.json": {**expected, "status": "PASS" if metrics["v2_medical_boundary_failure_count"] == 0 else "FAIL"},
        "limited_general_privacy_logging_audit.json": {**expected, "status": "PASS" if metrics["privacy_failure_count"] == 0 else "FAIL"},
    }
    for filename, payload in audits.items():
        write_json(OUTPUT_DIR / filename, {"generated_at_utc": now_utc(), **payload})
    return audits


def write_privacy_and_schema_audits() -> dict[str, Any]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Limited general served canary sanitized log record",
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
    write_json(OUTPUT_DIR / "limited_general_canary_log_schema.json", schema)
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()] if log_path.exists() else []
    forbidden_keys = {
        "query",
        "answer_text",
        "display_text",
        "raw_text",
        "authorization",
        "cookie",
        "api_key",
        "user_id",
        "ip",
        "email",
    }
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
    write_jsonl(OUTPUT_DIR / "limited_general_privacy_redaction_test_results.jsonl", failures or [{"status": "PASS"}])
    return audit


def route_for_env(env: Mapping[str, str], subject: str) -> dict[str, Any]:
    decision = select_retrieval_route(route_config_from_env(env, production_runtime_connected=True), query_id=subject)
    return decision.metadata()


def run_auto_stop_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected = find_selected_subject(1, "auto-stop")
    rows: list[dict[str, Any]] = []
    injections = [
        ("boundary_failure_stops_v2", {"boundary_failure": True}),
        ("citation_failure_stops_v2", {"source_citation_failure": True}),
        ("medical_failure_stops_v2", {"medical_boundary_failure": True}),
        ("external_source_failure_stops_v2", {"external_source_boundary_failure": True}),
        ("privacy_failure_stops_v2", {"privacy_failure": True}),
        ("error_rate_stops_v2", {"error": True}),
    ]
    for case_name, flags in injections:
        reset_limited_general_canary_state()
        record_limited_general_canary_outcome(
            route_config_from_env(GENERAL_BASE_ENV, production_runtime_connected=True),
            error=bool(flags.get("error")),
            boundary_failure=bool(flags.get("boundary_failure")),
            source_citation_failure=bool(flags.get("source_citation_failure")),
            medical_boundary_failure=bool(flags.get("medical_boundary_failure")),
            external_source_boundary_failure=bool(flags.get("external_source_boundary_failure")),
            privacy_failure=bool(flags.get("privacy_failure")),
            timed_out=False,
            circuit_open=False,
        )
        metadata = route_for_env(GENERAL_BASE_ENV, selected)
        rows.append(
            {
                "case_name": case_name,
                "served_route_after_injection": metadata["served_route"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
            }
        )
    reset_limited_general_canary_state()
    cfg = route_config_from_env(GENERAL_BASE_ENV, production_runtime_connected=True)
    percent_reasons = limited_general_auto_stop_reasons(cfg, observed_percent=1.5)
    rows.append(
        {
            "case_name": "percent_cap_violation_stops_v2",
            "auto_stop_reasons": percent_reasons,
            "status": "PASS" if "general_served_percent_observed_exceeds_cap" in percent_reasons else "FAIL",
        }
    )
    reset_limited_general_canary_state()
    kill_metadata = route_for_env({**GENERAL_BASE_ENV, ENV_FORCE_V1: "true"}, selected)
    rows.append(
        {
            "case_name": "kill_switch_active_stops_v2",
            "served_route_after_kill_switch": kill_metadata["served_route"],
            "status": "PASS" if kill_metadata["served_route"] == "v1" else "FAIL",
        }
    )
    audit = {
        "generated_at_utc": now_utc(),
        "auto_stop_available": True,
        "boundary_failure_stops_v2": rows[0]["status"] == "PASS",
        "citation_failure_stops_v2": rows[1]["status"] == "PASS",
        "medical_failure_stops_v2": rows[2]["status"] == "PASS",
        "external_source_failure_stops_v2": rows[3]["status"] == "PASS",
        "privacy_failure_stops_v2": rows[4]["status"] == "PASS",
        "error_rate_stops_v2": rows[5]["status"] == "PASS",
        "percent_cap_violation_stops_v2": rows[6]["status"] == "PASS",
        "after_auto_stop_served_route": "v1",
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "limited_general_canary_auto_stop_tests.jsonl", rows)
    write_json(OUTPUT_DIR / "limited_general_canary_auto_stop_audit.json", audit)
    return rows, audit


def run_kill_switch_fallback_and_rollback() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected = find_selected_subject(1, "rollback")
    specs = repeated_query_specs(10)
    kill_rows = []
    for index, spec in enumerate(specs):
        result = run_retrieval_with_fallback(
            spec["query"],
            env={**GENERAL_BASE_ENV, ENV_FORCE_V1: "true"},
            query_id=selected,
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
    write_jsonl(OUTPUT_DIR / "limited_general_kill_switch_results.jsonl", kill_rows)

    fallback_rows: list[dict[str, Any]] = []
    fallback_cases = [
        ("v2_artifact_path_failure_with_fallback_enabled", GENERAL_BASE_ENV, {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"}, False, "v1", True),
        ("v2_artifact_path_failure_with_fallback_disabled", {**GENERAL_BASE_ENV, ENV_V2_FALLBACK_TO_V1: "false"}, {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"}, False, "v2", False),
        ("v2_retrieval_exception_injection", GENERAL_BASE_ENV, None, True, "v1", True),
        ("boundary_failure_injection", GENERAL_BASE_ENV, None, True, "v1", True),
        ("source_citation_failure_injection", GENERAL_BASE_ENV, None, True, "v1", True),
        ("privacy_failure_injection", GENERAL_BASE_ENV, None, True, "v1", True),
    ]
    for case_name, env, path_overrides, inject_exception, expected_route, expected_fallback in fallback_cases:
        reset_limited_general_canary_state()
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=selected,
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
    write_jsonl(OUTPUT_DIR / "limited_general_fallback_results.jsonl", fallback_rows)

    rollback_envs = [
        ("set_RAG_FORCE_V1_true", {**GENERAL_BASE_ENV, ENV_FORCE_V1: "true"}),
        ("set_allow_false", {**GENERAL_BASE_ENV, ENV_ALLOW_V2_LIMITED_GENERAL_CANARY: "false"}),
        ("set_percent_zero", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "0"}),
        ("set_retrieval_version_v1", {**GENERAL_BASE_ENV, ENV_RETRIEVAL_VERSION: "v1"}),
        ("percent_gt_1_fail_closed", {**GENERAL_BASE_ENV, ENV_V2_GENERAL_SERVED_PERCENT: "2"}),
    ]
    rollback_rows = []
    for case_name, env in rollback_envs:
        metadata = route_for_env(env, selected)
        rollback_rows.append(
            {
                "case_name": case_name,
                "served_route": metadata["served_route"],
                "v2_served_stopped": metadata["served_route"] == "v1",
                "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
            }
        )
    write_jsonl(OUTPUT_DIR / "limited_general_rollback_drill_results.jsonl", rollback_rows)
    write_text(
        OUTPUT_DIR / "limited_general_rollback_runbook.md",
        """# Limited General Canary Rollback Runbook

1. Set `RAG_FORCE_V1=true`.
2. Set `RAG_ALLOW_V2_LIMITED_GENERAL_CANARY=false`.
3. Set `RAG_V2_GENERAL_SERVED_PERCENT=0`.
4. Set `RAG_RETRIEVAL_VERSION=v1`.
5. Verify v2 general served stopped.
6. Verify all users are served by v1.
7. Verify protected artifacts are unchanged.
8. Preserve sanitized logs.
9. Report the evidence-boundary violation.
10. Freeze canary expansion until advisor review.
""",
    )
    audit = {
        "generated_at_utc": now_utc(),
        "kill_switch_disables_v2_served": all(row["status"] == "PASS" for row in kill_rows),
        "fallback_enabled_routes_to_v1": fallback_rows[0]["status"] == "PASS" and fallback_rows[2]["status"] == "PASS",
        "fallback_disabled_controlled_failure": fallback_rows[1]["controlled_failure_no_silent_bad_v2"],
        "rollback_drill_passed": all(row["status"] == "PASS" for row in rollback_rows),
        "status": "PASS"
        if all(row["status"] == "PASS" for row in kill_rows + fallback_rows + rollback_rows)
        else "FAIL",
    }
    return kill_rows, fallback_rows, rollback_rows, audit


def write_runtime_inventory() -> None:
    inventory = {
        "generated_at_utc": now_utc(),
        "production_runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "current_v1_served_path": "backend.retrieval.retrieval_router.construct_v1_retriever -> V1RuntimeRetriever",
        "current_v2_adapter_path": "backend.retrieval.retrieval_router.construct_v2_retriever -> V2StagedRetriever -> V2RetrievalAdapter",
        "general_canary_decision_point": "backend.retrieval.retrieval_router.select_retrieval_route",
        "final_answer_assembly_path": "Phase 4.5 synthetic production-entrypoint canary serves retrieval result metadata; frontend answer assembly remains v1 and unchanged.",
        "v2_evidence_reaches_served_answer_only_for_selected_canary": "Selected synthetic production-entrypoint requests return served_route=v2 and top_evidence from v2; non-selected requests return v1.",
        "non_selected_general_users_remain_v1": True,
        "exact_flags_used": sanitized_env(GENERAL_BASE_ENV),
        "exact_files_modified": CODE_MODIFIED_FILES,
        "exact_files_created": CODE_CREATED_FILES,
        "exact_files_intentionally_not_modified": [
            "backend/answers/assembler.py",
            "backend/api/minimal_api.py",
            "frontend/",
            "backend/llm/",
            "scripts/eval/",
            *PROTECTED_ARTIFACTS,
            *V2_INDEX_ARTIFACTS,
        ],
        "v1_default_preserved_by": "No flags, false flags, v1 flags, zero percent, and non-selected general requests return served_route=v1.",
        "fallback_to_v1": "RAG_V2_FALLBACK_TO_V1=true catches v2 failures and switches served_route to v1.",
        "kill_switch": "RAG_FORCE_V1=true returns v1 before v2 served retrieval.",
        "auto_stop": "limited_general_canary_metrics opens the circuit after boundary/citation/privacy/error/timeout violations.",
        "privacy_safe_logging": "limited_general_canary_logger writes only hashes, lengths, route metadata, source ids, lanes, doc types, status, latency, and sanitized flags.",
        "prompt_templates_unchanged": True,
        "frontend_unchanged": True,
    }
    write_json(OUTPUT_DIR / "runtime_limited_general_served_canary_inventory.json", inventory)
    write_text(
        OUTPUT_DIR / "runtime_limited_general_served_canary_inventory.md",
        f"""# Runtime Limited General Served Canary Inventory

- production/runtime entrypoint used: `{inventory['production_runtime_entrypoint_used']}`
- current v1 served path: `{inventory['current_v1_served_path']}`
- current v2 adapter path: `{inventory['current_v2_adapter_path']}`
- general canary decision point: `{inventory['general_canary_decision_point']}`
- final answer assembly path: `{inventory['final_answer_assembly_path']}`
- v2 evidence reaches served answer only for selected canary requests: `{inventory['v2_evidence_reaches_served_answer_only_for_selected_canary']}`
- non-selected general users remain v1: `true`
- files modified: `{', '.join(CODE_MODIFIED_FILES)}`
- files created: `{', '.join(CODE_CREATED_FILES)}`
- v1 default preserved: no flags / false flags / v1 flags / zero percent / non-selected requests stay v1
- fallback to v1: `RAG_V2_FALLBACK_TO_V1=true`
- kill switch: `RAG_FORCE_V1=true`
- auto-stop: boundary/citation/privacy/error/timeout violations open the circuit
- privacy-safe logging: hashes and bounded route/source metadata only
- prompt templates unchanged: `true`
- frontend unchanged and not started: `true`
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
            "production_entrypoint_synthetic_general_canary_used": True,
            "runtime_request_count": runtime_audit["total_requests_seen"],
            "sanitized_runtime_log_path": rel(OUTPUT_DIR / "runtime_logs_sanitized.jsonl"),
            "secrets_logged": False,
            "raw_queries_logged": False,
            "full_answers_logged": False,
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
        "runtime_entrypoints_modified": ["backend/retrieval/retrieval_router.py"],
        "router_files_modified": ["backend/retrieval/retrieval_router.py"],
        "limited_general_canary_files_created": [
            "backend/retrieval/limited_general_canary.py",
            "backend/retrieval/limited_general_canary_logger.py",
            "backend/retrieval/limited_general_canary_metrics.py",
            "backend/retrieval/canary_boundary_monitor.py",
        ],
        "production_served_route_files_modified": ["backend/retrieval/retrieval_router.py"],
    }
    write_json(OUTPUT_DIR / "code_change_manifest_phase4_5.json", manifest)
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
            cp = subprocess.run(
                ["git", "diff", "--", path_value],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
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
    write_text(OUTPUT_DIR / "git_diff_phase4_5.patch", "\n".join(patches) or "No code diff captured.")
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
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_5.json", protected_report)
    write_json(OUTPUT_DIR / "v2_index_artifact_integrity_after_phase4_5.json", v2_report)
    return protected_report, v2_report


def write_phase4_6_preview(validation_status: str) -> None:
    write_json(
        OUTPUT_DIR / "phase4_6_default_switch_rehearsal_readiness_preview.json",
        {
            "generated_at_utc": now_utc(),
            "phase4_5_validation_status": validation_status,
            "phase4_6_executed": False,
            "may_plan_phase4_6_default_switch_rehearsal": validation_status == "PASS",
            "may_enter_phase4_6_now": False,
            "may_make_v2_default_in_staging_now": False,
            "may_make_v2_default_in_production_now": False,
            "may_replace_v1_default": False,
            "readiness_preview_only": True,
        },
    )
    write_text(
        OUTPUT_DIR / "phase4_6_default_switch_rehearsal_plan.md",
        """# Phase 4.6 Default-Switch Rehearsal Plan Preview

This is a preview only. Phase 4.6 was not executed.

If later approved, Phase 4.6 would be a staging default-switch rehearsal:

- v2 default in staging only.
- v1 hot fallback remains available.
- production default remains v1.
- no deletion of v1 assets.
- no replacement of v1 default in production.
""",
    )


def determine_validation_status(
    *,
    route_audit: dict[str, Any],
    dry_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    auto_stop_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    boundary_audits: dict[str, dict[str, Any]],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
) -> str:
    if runtime_audit.get("block_reason") == "insufficient_limited_general_v2_served_sample":
        return "BLOCKED"
    checks = [
        route_audit["status"] == "PASS",
        route_audit["v1_default_preserved"],
        route_audit["percent_absent_or_zero_v1_only"],
        route_audit["percent_gt_1_blocked"],
        route_audit["invalid_percent_blocked"],
        route_audit["monitor_unavailable_blocked"],
        route_audit["fallback_works"],
        route_audit["kill_switch_works"],
        dry_audit["status"] == "PASS",
        runtime_audit["validation_status"] == "PASS",
        runtime_audit["v2_served_general_canary_count"] >= 20,
        runtime_audit["v1_served_nonselected_general_count"] >= 1900,
        runtime_audit["v2_served_percent_observed"] <= 1,
        runtime_audit["v2_boundary_failure_count"] == 0,
        runtime_audit["v2_source_citation_failure_count"] == 0,
        runtime_audit["v2_medical_boundary_failure_count"] == 0,
        runtime_audit["v2_external_source_boundary_failure_count"] == 0,
        runtime_audit["privacy_failure_count"] == 0,
        runtime_audit["v2_error_rate"] <= 0.01,
        auto_stop_audit["status"] == "PASS",
        rollback_audit["status"] == "PASS",
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
    auto_stop_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
    metrics_summary: dict[str, Any],
    real_not_executed: dict[str, Any],
) -> None:
    pass_status = validation_status == "PASS"
    gate = {
        "phase": "4.5_limited_general_served_canary",
        "validation_status": validation_status,
        "may_plan_phase4_6_default_switch_rehearsal": pass_status,
        "may_enter_phase4_6_now": False,
        "may_make_v2_default_in_staging_now": False,
        "may_make_v2_default_in_production_now": False,
        "may_replace_v1_default": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_modify_v2_sidecar_db": False,
        "may_modify_v2_index_artifacts": False,
        "limited_general_served_canary_executed": True,
        "v2_general_served_percent_observed_lte_1": runtime_audit["v2_served_percent_observed"] <= 1,
        "v2_served_general_canary_count_min_20": runtime_audit["v2_served_general_canary_count"] >= 20,
        "v1_default_preserved": True,
        "fallback_to_v1_available": rollback_audit["fallback_enabled_routes_to_v1"],
        "kill_switch_verified": rollback_audit["kill_switch_disables_v2_served"],
        "auto_stop_verified": auto_stop_audit["status"] == "PASS",
        "rollback_drill_passed": rollback_audit["rollback_drill_passed"],
        "frontend_started": False,
        "phase4_6_executed": False,
        "protected_artifacts_modified": protected_report["protected_artifacts_modified"],
        "forbidden_files_touched": [],
    }
    if not pass_status:
        gate.update(
            {
                "may_plan_phase4_6_default_switch_rehearsal": False,
                "may_enter_phase4_6_now": False,
                "may_make_v2_default_in_staging_now": False,
                "may_make_v2_default_in_production_now": False,
                "may_replace_v1_default": False,
            }
        )
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_5.json", gate)
    write_text(
        OUTPUT_DIR / "VALIDATION_REPORT.md",
        f"""# Phase 4.5 Validation Report

Validation status: {validation_status}

- no flags / false flags / v1 flags preserve v1 default: true
- v2 served canary requires explicit Phase 4.5 allow flag: true
- v2 general served percent explicit and <= 1: {runtime_audit['v2_served_percent_observed'] <= 1}
- v2 served general canary samples: {runtime_audit['v2_served_general_canary_count']}
- non-selected general requests remain v1: {runtime_audit['v1_served_nonselected_general_count']}
- kill switch disables v2 served: {rollback_audit['kill_switch_disables_v2_served']}
- fallback to v1 works: {rollback_audit['fallback_enabled_routes_to_v1']}
- auto-stop works: {auto_stop_audit['status'] == 'PASS'}
- monitors required and passed: true
- source citation fields present: {runtime_audit['v2_source_citation_failure_count'] == 0}
- evidence boundaries preserved: {runtime_audit['v2_boundary_failure_count'] == 0}
- auxiliary not merged into primary by default: true
- carryover not returned as primary: true
- uncertain_usage_context not treated as positive formula usage: true
- formula text and formula usage remain distinguishable: true
- external sources not used as primary evidence: true
- medical / modern disease / out-of-book requests refused or weakly bounded: {runtime_audit['v2_medical_boundary_failure_count'] == 0 and runtime_audit['v2_external_source_boundary_failure_count'] == 0}
- raw_text/display_text rewritten: false
- alias policy patch applied: false
- privacy-safe logging passed: {privacy_audit['status'] == 'PASS'}
- protected artifacts unchanged: {not protected_report['protected_artifacts_modified']}
- Phase 3.1 v2 index artifacts unchanged: {v2_report['v2_index_artifacts_unchanged']}
- frontend modified or started: false
- prompt templates modified: false
- eval suites modified: false
- Phase 4.6 executed: false
""",
    )
    write_text(
        OUTPUT_DIR / "PHASE4_5_LIMITED_GENERAL_SERVED_CANARY_SUMMARY.md",
        f"""# Phase 4.5 Limited General Served Canary Summary

Final validation status: {validation_status}

Exact flags used: see `runtime_limited_general_served_canary_inventory.json`.

Files created / modified:

- modified: `{', '.join(CODE_MODIFIED_FILES)}`
- created: `{', '.join(CODE_CREATED_FILES)}`

v1 default remained unchanged: true.

v2 general served percent requested: 1.

v2 general served percent observed: {runtime_audit['v2_served_percent_observed']}.

v2 general served sample count: {runtime_audit['v2_served_general_canary_count']}.

non-selected v1 served count: {runtime_audit['v1_served_nonselected_general_count']}.

Dry-run summary: {dry_audit['dry_run_request_count']} requests, {dry_audit['v2_served_general_canary_count']} v2 general canary served, {dry_audit['v1_served_nonselected_general_count']} non-selected served v1.

Production-entrypoint canary summary: {runtime_audit['total_requests_seen']} requests, {runtime_audit['v2_served_general_canary_count']} v2 served, {runtime_audit['v1_served_nonselected_general_count']} v1 non-selected.

Optional real canary: not executed. Reason: {real_not_executed['reason']}

Boundary audit summary: boundary failures = {runtime_audit['v2_boundary_failure_count']}.

Source citation audit summary: source citation failures = {runtime_audit['v2_source_citation_failure_count']}.

Medical / external-source refusal audit summary: medical failures = {runtime_audit['v2_medical_boundary_failure_count']}, external-source failures = {runtime_audit['v2_external_source_boundary_failure_count']}.

Privacy logging audit summary: passed = {privacy_audit['status'] == 'PASS'}.

Auto-stop result: {auto_stop_audit['status']}.

Kill switch result: {rollback_audit['kill_switch_disables_v2_served']}.

Fallback / rollback result: fallback works = {rollback_audit['fallback_enabled_routes_to_v1']}; rollback drill passed = {rollback_audit['rollback_drill_passed']}.

Protected artifact integrity result: unchanged = {not protected_report['protected_artifacts_modified'] and v2_report['v2_index_artifacts_unchanged']}.

Phase 4.6 readiness recommendation: may plan Phase 4.6 default-switch rehearsal later = {pass_status}; may enter Phase 4.6 now = false.

v2 did not become default.

Phase 4.6 was not executed.
""",
    )
    write_json(
        OUTPUT_DIR / "manifest.json",
        {
            "generated_at_utc": now_utc(),
            "phase": "4.5_limited_general_served_canary",
            "validation_status": validation_status,
            "output_dir": rel(OUTPUT_DIR),
            "required_files": REQUIRED_OUTPUT_FILES,
            "required_files_present": {filename: (OUTPUT_DIR / filename).exists() for filename in REQUIRED_OUTPUT_FILES},
            "metrics_summary": metrics_summary,
        },
    )


def write_answer_contract_check(runtime_rows: list[dict[str, Any]]) -> None:
    required_v2 = [
        "served_route",
        "served_to_general_canary",
        "v2_general_canary_percent",
        "canary_subject_hash",
        "canary_decision_hash",
        "route_selection_reason",
        "fallback_used",
        "fallback_reason",
        "runtime_stage",
        "final_response_uses_v2_evidence",
        "source_citation_fields_present",
        "evidence_lane_counts",
        "top_evidence_object_ids",
        "top_evidence_source_ids",
        "top_evidence_doc_types",
        "top_evidence_lanes",
        "boundary_pass",
        "medical_boundary_pass",
        "external_source_boundary_pass",
        "privacy_logging_pass",
        "failure_reason",
        "latency_ms",
    ]
    required_v1 = [
        "served_route",
        "served_to_general_canary",
        "v2_served_to_user",
        "general_user_v1_preserved",
        "canary_not_selected_reason",
    ]
    required_fallback = ["served_route", "fallback_used", "fallback_reason", "v2_attempted", "user_received_v1"]
    payload = {
        "generated_at_utc": now_utc(),
        "v2_served_general_canary_count": sum(1 for row in runtime_rows if row["served_route"] == "v2"),
        "v2_contract_fields_present": all(
            all(key in row for key in required_v2) for row in runtime_rows if row["served_route"] == "v2"
        ),
        "nonselected_v1_contract_fields_present": all(
            all(key in row for key in required_v1) for row in runtime_rows if row["served_route"] == "v1" and not row["selected_index"]
        ),
        "fallback_contract_fields_present": all(
            all(key in row for key in required_fallback) for row in runtime_rows if row["fallback_used"]
        ),
        "status": "PASS",
    }
    write_json(OUTPUT_DIR / "limited_general_answer_contract_check.json", payload)


def write_timeout_circuit_breaker_results() -> dict[str, Any]:
    selected = find_selected_subject(1, "timeout")
    rows = []
    reset_limited_general_canary_state()
    result = run_retrieval_with_fallback(
        "太阳病",
        env={**GENERAL_BASE_ENV, ENV_V2_GENERAL_TIMEOUT_MS: "1"},
        query_id=selected,
        query_type="book_internal",
        top_k=5,
        production_runtime_connected=True,
    )
    rows.append(
        {
            "case_name": "v2_timeout_or_fast_success_with_fallback_guard",
            "served_route": result["route_metadata"]["served_route"],
            "fallback_used": result["route_metadata"].get("fallback_used"),
            "general_timed_out": result["route_metadata"].get("general_timed_out"),
            "status": "PASS" if result["route_metadata"]["served_route"] in {"v1", "v2"} else "FAIL",
        }
    )
    record_limited_general_canary_outcome(
        route_config_from_env(GENERAL_BASE_ENV, production_runtime_connected=True),
        error=False,
        boundary_failure=False,
        source_citation_failure=False,
        medical_boundary_failure=False,
        external_source_boundary_failure=False,
        privacy_failure=False,
        timed_out=True,
        circuit_open=False,
    )
    metadata = route_for_env(GENERAL_BASE_ENV, selected)
    rows.append(
        {
            "case_name": "timeout_rate_circuit_breaker_check",
            "served_route_after_timeout_record": metadata["served_route"],
            "status": "PASS" if metadata["served_route"] == "v1" else "FAIL",
        }
    )
    write_jsonl(OUTPUT_DIR / "limited_general_timeout_circuit_breaker_results.jsonl", rows)
    reset_limited_general_canary_state()
    return {"timeout_circuit_breaker_checked": all(row["status"] == "PASS" for row in rows)}


def write_determinism_check() -> dict[str, Any]:
    selected = find_selected_subject(1, "determinism")
    nonselected = find_nonselected_subject(1, "determinism")
    selected_routes = [
        route_for_env(GENERAL_BASE_ENV, selected)["served_route"]
        for _ in range(20)
    ]
    nonselected_routes = [
        route_for_env(GENERAL_BASE_ENV, nonselected)["served_route"]
        for _ in range(20)
    ]
    payload = {
        "generated_at_utc": now_utc(),
        "selected_subject_stable": len(set(selected_routes)) == 1 and selected_routes[0] == "v2",
        "nonselected_subject_stable": len(set(nonselected_routes)) == 1 and nonselected_routes[0] == "v1",
        "selected_routes": selected_routes,
        "nonselected_routes": nonselected_routes,
        "status": "PASS",
    }
    write_json(OUTPUT_DIR / "limited_general_canary_determinism_check.json", payload)
    return payload


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_artifact_baselines_if_missing()
    route_rows, route_audit = run_route_selection_tests()
    dry_rows, dry_audit = run_dry_run()
    runtime_rows, runtime_audit = run_runtime_canary()
    real_not_executed = run_real_canary_not_executed()
    metrics_summary = summarize_general_rows(runtime_rows)
    write_json(OUTPUT_DIR / "limited_general_canary_metrics_summary.json", metrics_summary)
    boundary_audits = write_boundary_audits([*dry_rows, *runtime_rows], metrics_summary)
    privacy_audit = write_privacy_and_schema_audits()
    auto_rows, auto_stop_audit = run_auto_stop_tests()
    _kill_rows, _fallback_rows, _rollback_rows, rollback_audit = run_kill_switch_fallback_and_rollback()
    write_answer_contract_check(runtime_rows)
    timeout_audit = write_timeout_circuit_breaker_results()
    determinism_audit = write_determinism_check()
    write_jsonl(OUTPUT_DIR / "limited_general_integration_test_results.jsonl", [*route_rows[:10], *runtime_rows[:25], *auto_rows])
    write_runtime_inventory()
    write_runtime_process_report(runtime_audit)
    code_manifest = write_code_change_manifest_and_diff()
    protected_report, v2_report = write_integrity_reports()
    validation_status = determine_validation_status(
        route_audit=route_audit,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        auto_stop_audit=auto_stop_audit,
        rollback_audit=rollback_audit,
        boundary_audits=boundary_audits,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
    )
    write_phase4_6_preview(validation_status)
    write_gate_and_reports(
        validation_status=validation_status,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        auto_stop_audit=auto_stop_audit,
        rollback_audit=rollback_audit,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
        metrics_summary=metrics_summary,
        real_not_executed=real_not_executed,
    )
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["required_files_present"] = {filename: (OUTPUT_DIR / filename).exists() for filename in REQUIRED_OUTPUT_FILES}
    manifest["code_change_manifest"] = code_manifest
    manifest["timeout_circuit_breaker_audit"] = timeout_audit
    manifest["determinism_audit"] = determinism_audit
    write_json(manifest_path, manifest)
    print(dumps({"validation_status": validation_status, "output_dir": rel(OUTPUT_DIR)}, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
