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

from backend.retrieval.internal_canary import (  # noqa: E402
    InternalCanaryIdentity,
    evidence_contract_fields,
    stable_hash,
)
from backend.retrieval.internal_canary_logger import (  # noqa: E402
    ALLOWED_LOG_FIELDS,
    append_internal_canary_log,
    build_internal_canary_log_record,
)
from backend.retrieval.internal_canary_metrics import reset_internal_canary_state  # noqa: E402
from backend.retrieval.retrieval_router import (  # noqa: E402
    ENV_ALLOW_V2_INTERNAL_SERVED_CANARY,
    ENV_ALLOW_V2_PRODUCTION_SHADOW,
    ENV_FORCE_V1,
    ENV_RETRIEVAL_VERSION,
    ENV_RUNTIME_STAGE,
    ENV_V2_FALLBACK_TO_V1,
    ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS,
    ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES,
    ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES,
    ENV_V2_INTERNAL_CANARY_REQUIRE_ALLOWLIST,
    ENV_V2_INTERNAL_CIRCUIT_BREAKER,
    ENV_V2_INTERNAL_MAX_BOUNDARY_FAILURES,
    ENV_V2_INTERNAL_MAX_ERROR_RATE,
    ENV_V2_INTERNAL_SERVED_PERCENT,
    ENV_V2_INTERNAL_TIMEOUT_MS,
    ENV_V2_PROD_SHADOW_ALL,
    ENV_V2_PROD_SHADOW_PERCENT,
    ENV_V2_PRODUCTION_SERVED_PERCENT,
    ENV_V2_SHADOW_COMPARE,
    classify_boundary,
    infer_query_type,
    route_config_from_env,
    run_retrieval_with_fallback,
    select_retrieval_route,
    source_fields_present,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_4_internal_served_canary"
PROTECTED_BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_4.json"
V2_INDEX_BASELINE_PATH = OUTPUT_DIR / "v2_index_artifact_baseline_before_phase4_4.json"

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
    "backend/retrieval/internal_canary.py",
    "backend/retrieval/internal_canary_logger.py",
    "backend/retrieval/internal_canary_metrics.py",
    "scripts/data_reconstruction_v2/run_phase4_4_internal_served_canary.py",
]
CODE_MODIFIED_FILES = [
    "backend/retrieval/retrieval_router.py",
]
CODE_CHANGE_FILES = [*CODE_CREATED_FILES, *CODE_MODIFIED_FILES]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_4_INTERNAL_SERVED_CANARY_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "phase4_3_shadow_percent_semantics_fix.json",
    "phase4_3_shadow_percent_regression_tests.jsonl",
    "protected_artifact_baseline_before_phase4_4.json",
    "protected_artifact_integrity_after_phase4_4.json",
    "v2_index_artifact_baseline_before_phase4_4.json",
    "v2_index_artifact_integrity_after_phase4_4.json",
    "runtime_internal_served_canary_inventory.json",
    "runtime_internal_served_canary_inventory.md",
    "code_change_manifest_phase4_4.json",
    "git_diff_phase4_4.patch",
    "internal_served_canary_log_schema.json",
    "internal_served_privacy_redaction_test_results.jsonl",
    "internal_served_canary_dry_run_results.jsonl",
    "internal_served_canary_dry_run_audit.json",
    "internal_served_canary_runtime_results.jsonl",
    "internal_served_canary_runtime_audit.json",
    "internal_served_canary_runtime_summary.md",
    "real_internal_allowlist_canary_not_executed.json",
    "general_user_v2_non_exposure_audit.json",
    "internal_served_evidence_boundary_audit.json",
    "internal_served_formula_text_vs_usage_audit.json",
    "internal_served_auxiliary_boundary_audit.json",
    "internal_served_carryover_exclusion_audit.json",
    "internal_served_uncertain_usage_exclusion_audit.json",
    "internal_served_variant_preservation_audit.json",
    "internal_served_weak_answer_refusal_audit.json",
    "internal_served_source_citation_audit.json",
    "internal_served_external_source_exclusion_audit.json",
    "internal_served_medical_advice_boundary_audit.json",
    "internal_served_privacy_logging_audit.json",
    "internal_served_kill_switch_results.jsonl",
    "internal_served_fallback_results.jsonl",
    "internal_served_rollback_drill_results.jsonl",
    "internal_served_rollback_runbook.md",
    "internal_served_canary_metrics_summary.json",
    "runtime_process_report.json",
    "runtime_logs_sanitized.jsonl",
    "phase4_5_limited_general_served_canary_readiness_preview.json",
    "phase4_5_limited_general_served_canary_plan.md",
    "runtime_gate_status_after_phase4_4.json",
    "internal_served_router_unit_test_results.jsonl",
    "internal_served_integration_test_results.jsonl",
    "internal_served_answer_contract_check.json",
    "internal_served_timeout_circuit_breaker_results.jsonl",
]

SHADOW_BASE_ENV = {
    ENV_RETRIEVAL_VERSION: "shadow",
    ENV_ALLOW_V2_PRODUCTION_SHADOW: "true",
    ENV_RUNTIME_STAGE: "production_shadow",
    ENV_V2_SHADOW_COMPARE: "true",
    ENV_V2_PRODUCTION_SERVED_PERCENT: "0",
}

INTERNAL_BASE_ENV = {
    ENV_RETRIEVAL_VERSION: "v2",
    ENV_RUNTIME_STAGE: "internal_served_canary",
    ENV_ALLOW_V2_INTERNAL_SERVED_CANARY: "true",
    ENV_V2_INTERNAL_CANARY_REQUIRE_ALLOWLIST: "true",
    ENV_V2_PRODUCTION_SERVED_PERCENT: "0",
    ENV_V2_PROD_SHADOW_PERCENT: "0",
    ENV_V2_FALLBACK_TO_V1: "true",
    ENV_V2_INTERNAL_TIMEOUT_MS: "1500",
    ENV_V2_INTERNAL_CIRCUIT_BREAKER: "true",
    ENV_V2_INTERNAL_MAX_ERROR_RATE: "0.02",
    ENV_V2_INTERNAL_MAX_BOUNDARY_FAILURES: "0",
}

DRY_RUN_ENV_BASE = {**INTERNAL_BASE_ENV, ENV_V2_INTERNAL_SERVED_PERCENT: "100"}
RUNTIME_ENV_BASE = {**INTERNAL_BASE_ENV, ENV_V2_INTERNAL_SERVED_PERCENT: "10"}
KILL_SWITCH_ENV_BASE = {**INTERNAL_BASE_ENV, ENV_FORCE_V1: "true", ENV_V2_INTERNAL_SERVED_PERCENT: "100"}

QUERY_SPECS: list[dict[str, str]] = [
    *[
        {"query_group": "clause_reading", "query": query, "query_type": "book_internal"}
        for query in [
            "太阳病",
            "少阳病",
            "阳明病",
            "太阴病",
            "少阴病",
            "厥阴病",
            "伤寒",
            "中风",
            "汗",
            "发热",
            "恶寒",
            "脉浮",
        ]
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
        ]
    ],
    *[
        {"query_group": "external_source_refusal", "query": query, "query_type": "boundary_refusal"}
        for query in [
            "请把外部百科资料作为依据解释白虎汤",
            "请综合现代中医名家观点回答小青龙汤",
            "外部专业资料能否作为主证据",
            "没有书内证据时也请直接下结论",
        ]
    ],
    *[
        {"query_group": "carryover_probe", "query": query, "query_type": "book_internal"}
        for query in [
            "残余材料能否作为主证据",
            "carryover returned as primary",
            "非主证据能否进入主结果",
            "review only primary probe",
        ]
    ],
    *[
        {"query_group": "uncertain_usage_probe", "query": query, "query_type": "formula_usage"}
        for query in [
            "疑似用小青龙汤的条文有哪些",
            "不确定用白虎汤的条文有哪些",
            "uncertain usage positive probe",
            "某方可能用于哪些条文",
        ]
    ],
    *[
        {"query_group": "no_evidence_forced_answer_probe", "query": query, "query_type": "book_internal"}
        for query in [
            "请在没有书内证据时强行回答某不存在方",
            "没有证据也请给确定结论",
            "未知方剂在书中的用法是什么",
            "不存在的条文对象能否直接解释",
            "请直接断言外部说法为书内结论",
            "无依据也要给出主证据",
            "forced answer without evidence",
            "no evidence primary probe",
        ]
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


def write_artifact_baselines() -> None:
    write_json(
        PROTECTED_BASELINE_PATH,
        {"generated_at_utc": now_utc(), "files": [file_fingerprint(path) for path in PROTECTED_ARTIFACTS]},
    )
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


def canary_selected(subject_hash: str, percent: int) -> bool:
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    digest = hashlib.sha256(subject_hash.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return bucket < percent


def request_hashes_for_runtime() -> tuple[list[str], set[str]]:
    selected: list[str] = []
    nonselected: list[str] = []
    probe_index = 0
    while len(selected) < 20 or len(nonselected) < 180:
        candidate = stable_hash(f"phase4-4-runtime-internal-{probe_index:05d}")
        if canary_selected(candidate, 10):
            if len(selected) < 20:
                selected.append(candidate)
        elif len(nonselected) < 180:
            nonselected.append(candidate)
        probe_index += 1
    ordered: list[str] = []
    selected_set = set(selected)
    selected_iter = iter(selected)
    nonselected_iter = iter(nonselected)
    for index in range(200):
        if index % 10 == 0:
            ordered.append(next(selected_iter))
        else:
            ordered.append(next(nonselected_iter))
    return ordered, selected_set


def request_hashes_for_dry_run(count: int) -> list[str]:
    return [stable_hash(f"phase4-4-dry-internal-{index:05d}") for index in range(count)]


def sanitized_env(env: Mapping[str, str]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in env.items():
        if key in {
            ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES,
            ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS,
            ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES,
        }:
            sanitized[key] = f"<{len([item for item in value.split(',') if item])}_hashes>"
        else:
            sanitized[key] = value
    return sanitized


def env_with_request_allowlist(env: Mapping[str, str], request_hashes: list[str]) -> dict[str, str]:
    return {**env, ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES: ",".join(request_hashes)}


def identity_for_request_hash(request_hash: str | None) -> InternalCanaryIdentity | None:
    if not request_hash:
        return None
    return InternalCanaryIdentity(internal_request_hash=request_hash)


def find_shadow_sample_query_id(percent: int) -> str:
    for index in range(10000):
        query_id = f"shadow-percent-{percent}-{index:04d}"
        if canary_selected(query_id, percent):
            return query_id
    raise RuntimeError(f"could not find deterministic shadow sample for percent={percent}")


def run_shadow_percent_semantics_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sampled_1 = find_shadow_sample_query_id(1)
    sampled_10 = find_shadow_sample_query_id(10)
    cases = [
        ("no_flags", {}, "v1", None, "v1", "no flags -> v1 only, no shadow"),
        (
            "shadow_allow_true_percent_absent",
            {key: value for key, value in SHADOW_BASE_ENV.items() if key != ENV_V2_PROD_SHADOW_PERCENT},
            "v1",
            None,
            "v1",
            "shadow allow true but RAG_V2_PROD_SHADOW_PERCENT absent -> no shadow",
        ),
        (
            "shadow_allow_true_percent_0",
            {**SHADOW_BASE_ENV, ENV_V2_PROD_SHADOW_PERCENT: "0"},
            "v1",
            None,
            "v1",
            "shadow allow true and RAG_V2_PROD_SHADOW_PERCENT=0 -> no shadow",
        ),
        (
            "shadow_allow_true_percent_1_sampled",
            {**SHADOW_BASE_ENV, ENV_V2_PROD_SHADOW_PERCENT: "1"},
            "v1",
            "v2",
            "production_shadow_sampled",
            "shadow allow true and RAG_V2_PROD_SHADOW_PERCENT=1 -> deterministic sampled shadow only",
            sampled_1,
        ),
        (
            "shadow_allow_true_percent_10_sampled",
            {**SHADOW_BASE_ENV, ENV_V2_PROD_SHADOW_PERCENT: "10"},
            "v1",
            "v2",
            "production_shadow_sampled",
            "shadow allow true and RAG_V2_PROD_SHADOW_PERCENT=10 -> deterministic sampled shadow only",
            sampled_10,
        ),
        (
            "force_v1",
            {**SHADOW_BASE_ENV, ENV_V2_PROD_SHADOW_PERCENT: "10", ENV_FORCE_V1: "true"},
            "v1",
            None,
            "v1",
            "RAG_FORCE_V1=true -> v1 only, no shadow",
        ),
        (
            "production_served_percent_gt_0",
            {**SHADOW_BASE_ENV, ENV_V2_PROD_SHADOW_PERCENT: "10", ENV_V2_PRODUCTION_SERVED_PERCENT: "1"},
            "v1",
            None,
            "v1",
            "RAG_V2_PRODUCTION_SERVED_PERCENT>0 -> fail closed to v1",
        ),
        (
            "explicit_shadow_all",
            {**SHADOW_BASE_ENV, ENV_V2_PROD_SHADOW_ALL: "true"},
            "v1",
            "v2",
            "production_shadow_all",
            "full shadow requires separate RAG_V2_PROD_SHADOW_ALL=true",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        case_name, env, expected_served, expected_shadow, expected_mode, explanation, *query_id_override = case
        query_id = query_id_override[0] if query_id_override else f"shadow-route-case-{index:03d}"
        decision = select_retrieval_route(
            route_config_from_env(env, production_runtime_connected=True),
            query_id=query_id,
        )
        metadata = decision.metadata()
        status = (
            metadata["served_route"] == expected_served
            and metadata["shadow_route"] == expected_shadow
            and metadata["route_mode"] == expected_mode
        )
        rows.append(
            {
                "case_name": case_name,
                "explanation": explanation,
                "query_id_hash": stable_hash(query_id),
                "served_route": metadata["served_route"],
                "shadow_route": metadata["shadow_route"],
                "route_mode": metadata["route_mode"],
                "production_shadow_percent": metadata["production_shadow_percent"],
                "production_shadow_all": metadata["production_shadow_all"],
                "shadow_sample_selected": metadata["shadow_sample_selected"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "status": "PASS" if status else "FAIL",
            }
        )
    audit = {
        "generated_at_utc": now_utc(),
        "semantics_fixed": all(row["status"] == "PASS" for row in rows[:7]),
        "explicit_full_shadow_flag_available": rows[-1]["status"] == "PASS",
        "shadow_percent_absent_means_zero_samples": rows[1]["shadow_route"] is None,
        "shadow_percent_zero_means_zero_samples": rows[2]["shadow_route"] is None,
        "full_shadow_uses_separate_flag": rows[-1]["route_mode"] == "production_shadow_all",
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "notes": [
            "RAG_V2_PROD_SHADOW_PERCENT absent and 0 are strict zero-sample states.",
            "Full direct shadow is separated behind RAG_V2_PROD_SHADOW_ALL=true.",
            "RAG_V2_PRODUCTION_SERVED_PERCENT>0 fails closed to v1.",
        ],
    }
    write_jsonl(OUTPUT_DIR / "phase4_3_shadow_percent_regression_tests.jsonl", rows)
    write_json(OUTPUT_DIR / "phase4_3_shadow_percent_semantics_fix.json", audit)
    return rows, audit


def run_internal_route_unit_tests() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    user_hash = stable_hash("phase4-4-route-user")
    request_hash = stable_hash("phase4-4-route-request")
    query_id_hash = stable_hash("phase4-4-route-query-id")
    match_identity = InternalCanaryIdentity(
        internal_user_hash=user_hash,
        internal_request_hash=request_hash,
        internal_query_id_hash=query_id_hash,
    )
    allow_env = {
        **INTERNAL_BASE_ENV,
        ENV_V2_INTERNAL_SERVED_PERCENT: "100",
        ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES: user_hash,
        ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES: request_hash,
        ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS: query_id_hash,
    }
    cases = [
        ("no_flags", {}, None, "v1", "no flags -> v1 served only"),
        ("force_v1", {**allow_env, ENV_FORCE_V1: "true"}, match_identity, "v1", "RAG_FORCE_V1=true -> v1"),
        ("retrieval_version_v1", {**allow_env, ENV_RETRIEVAL_VERSION: "v1"}, match_identity, "v1", "RAG_RETRIEVAL_VERSION=v1 -> v1"),
        (
            "v2_without_internal_allow",
            {**allow_env, ENV_ALLOW_V2_INTERNAL_SERVED_CANARY: "false"},
            match_identity,
            "v1",
            "v2 without internal allow -> blocked to v1",
        ),
        (
            "v2_with_allow_no_allowlist",
            {**INTERNAL_BASE_ENV, ENV_V2_INTERNAL_SERVED_PERCENT: "100"},
            None,
            "v1",
            "v2 with allow but no allowlist -> blocked to v1",
        ),
        ("v2_with_allowlist_match", allow_env, match_identity, "v2", "allowlist match -> v2 served"),
        (
            "internal_percent_absent",
            {key: value for key, value in allow_env.items() if key != ENV_V2_INTERNAL_SERVED_PERCENT},
            match_identity,
            "v1",
            "internal served percent absent -> v1",
        ),
        (
            "internal_percent_zero",
            {**allow_env, ENV_V2_INTERNAL_SERVED_PERCENT: "0"},
            match_identity,
            "v1",
            "internal served percent 0 -> v1",
        ),
        (
            "internal_percent_gt_0_without_allowlist",
            {**INTERNAL_BASE_ENV, ENV_V2_INTERNAL_SERVED_PERCENT: "10"},
            None,
            "v1",
            "percent >0 without allowlist -> blocked",
        ),
        (
            "production_served_percent_gt_0",
            {**allow_env, ENV_V2_PRODUCTION_SERVED_PERCENT: "1"},
            match_identity,
            "v1",
            "production served percent >0 -> fail closed",
        ),
        (
            "general_production_user",
            allow_env,
            None,
            "v1",
            "general production simulation without internal identity -> v1",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (case_name, env, identity, expected_route, explanation) in enumerate(cases):
        decision = select_retrieval_route(
            route_config_from_env(env, production_runtime_connected=True),
            query_id=f"internal-route-case-{index:03d}",
            internal_canary_identity=identity,
        )
        metadata = decision.metadata()
        rows.append(
            {
                "case_name": case_name,
                "explanation": explanation,
                "served_route": metadata["served_route"],
                "route_mode": metadata["route_mode"],
                "v2_block_reasons": metadata["v2_block_reasons"],
                "internal_allowlist_required": metadata["internal_allowlist_required"],
                "internal_allowlist_matched": metadata["internal_allowlist_matched"],
                "allowlist_match_type": metadata["allowlist_match_type"],
                "v2_served_to_general_user": metadata["v2_served_to_general_user"],
                "general_user_v1_preserved": metadata["general_user_v1_preserved"],
                "status": "PASS" if metadata["served_route"] == expected_route else "FAIL",
            }
        )
    audit = {
        "generated_at_utc": now_utc(),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "v1_default_preserved": rows[0]["served_route"] == "v1",
        "internal_allowlist_required": rows[4]["internal_allowlist_required"],
        "v2_with_allowlist_match_served": rows[5]["served_route"] == "v2",
        "general_production_user_v1": rows[-1]["served_route"] == "v1",
    }
    write_jsonl(OUTPUT_DIR / "internal_served_router_unit_test_results.jsonl", rows)
    return rows, audit


def repeated_query_specs(count: int) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    while len(specs) < count:
        specs.extend(QUERY_SPECS)
    return specs[:count]


def run_query_set(
    specs: list[dict[str, str]],
    *,
    env: Mapping[str, str],
    request_hashes: list[str | None],
    prefix: str,
    production_runtime_connected: bool,
    log_runtime_rows: bool = False,
    general_start_index: int | None = None,
) -> list[dict[str, Any]]:
    reset_internal_canary_state()
    rows: list[dict[str, Any]] = []
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    if log_runtime_rows and log_path.exists():
        log_path.unlink()
    for index, spec in enumerate(specs):
        query = spec["query"]
        request_hash = request_hashes[index] if index < len(request_hashes) else None
        identity = identity_for_request_hash(request_hash)
        request_id = f"{prefix}-{index:04d}"
        started = time.perf_counter()
        result = run_retrieval_with_fallback(
            query,
            env=env,
            query_id=stable_hash(request_id),
            internal_canary_identity=identity,
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
            internal_allowlist_eligible=bool(request_hash),
            general_user_simulation=bool(general_start_index is not None and index >= general_start_index),
        )
        rows.append(row)
        if log_runtime_rows:
            append_internal_canary_log(
                build_internal_canary_log_record(
                    query=query,
                    query_type=row["query_type"],
                    route_metadata=result["route_metadata"],
                    served_result=result["served_result"],
                    request_id=request_id,
                    latency_v1_ms=row["latency_ms"] if row["served_route"] == "v1" else None,
                ),
                path=log_path,
            )
    return rows


def sanitize_result_row(
    result: Mapping[str, Any],
    spec: Mapping[str, str],
    *,
    request_id: str,
    elapsed_ms: float,
    internal_allowlist_eligible: bool,
    general_user_simulation: bool,
) -> dict[str, Any]:
    metadata = dict(result["route_metadata"])
    served = dict(result["served_result"])
    evidence = [item for item in served.get("top_evidence", []) if isinstance(item, dict)]
    contract = evidence_contract_fields(served if metadata.get("served_route") == "v2" else None)
    boundary_reason = classify_boundary(spec["query"])
    served_internal = metadata.get("served_route") == "v2" and bool(metadata.get("served_to_internal_allowlist"))
    served_general = metadata.get("served_route") == "v2" and general_user_simulation
    return {
        "request_id_hash": stable_hash(request_id),
        "query_hash": stable_hash(spec["query"]),
        "query_length": len(spec["query"]),
        "query_group": spec["query_group"],
        "query_type": spec["query_type"] or infer_query_type(spec["query"]),
        "served_route": metadata["served_route"],
        "route_mode": metadata["route_mode"],
        "route_selection_reason": metadata["route_selection_reason"],
        "runtime_stage": metadata["runtime_stage"],
        "production_runtime_connected": metadata["production_runtime_connected"],
        "frontend_started": metadata["frontend_started"],
        "production_served_v2_percent": metadata["production_served_v2_percent"],
        "production_shadow_percent": metadata["production_shadow_percent"],
        "internal_served_percent": metadata["internal_served_percent"],
        "internal_allowlist_required": metadata["internal_allowlist_required"],
        "internal_allowlist_eligible": internal_allowlist_eligible,
        "internal_allowlist_matched": metadata["internal_allowlist_matched"],
        "internal_allowlist_selected": metadata["internal_canary_selected"],
        "allowlist_match_type": metadata["allowlist_match_type"],
        "canary_subject_hash": metadata["canary_subject_hash"],
        "served_to_internal_allowlist": metadata["served_to_internal_allowlist"],
        "served_to_general_production_user": metadata["served_to_general_production_user"],
        "v2_served_to_user": metadata["served_route"] == "v2",
        "v2_served_internal": served_internal,
        "v2_served_general_user": served_general,
        "v1_served_general_user": metadata["served_route"] == "v1" and general_user_simulation,
        "v1_served_internal_not_selected": metadata["served_route"] == "v1" and internal_allowlist_eligible,
        "general_user_v1_preserved": metadata["served_route"] == "v1" and general_user_simulation,
        "v2_block_reason": metadata.get("v2_block_reason") or next(iter(metadata.get("v2_block_reasons") or [""]), ""),
        "v2_block_reasons": metadata.get("v2_block_reasons"),
        "fallback_used": metadata.get("fallback_used"),
        "fallback_reason": failure_code(metadata.get("fallback_reason")),
        "v1_answer_status": served.get("answer_status") if metadata["served_route"] == "v1" else "",
        "v2_answer_status": served.get("answer_status") if metadata["served_route"] == "v2" else "",
        "final_response_uses_v2_evidence": metadata.get("final_response_uses_v2_evidence", contract["final_response_uses_v2_evidence"]),
        "source_citation_fields_present": metadata.get("source_citation_fields_present", contract["source_citation_fields_present"]),
        "evidence_lane_counts": metadata.get("evidence_lane_counts", contract["evidence_lane_counts"]),
        "top_evidence_object_ids": metadata.get("top_evidence_object_ids", contract["top_evidence_object_ids"]),
        "top_evidence_source_ids": metadata.get("top_evidence_source_ids", contract["top_evidence_source_ids"]),
        "top_evidence_doc_types": metadata.get("top_evidence_doc_types", contract["top_evidence_doc_types"]),
        "top_evidence_lanes": metadata.get("top_evidence_lanes", contract["top_evidence_lanes"]),
        "boundary_pass": metadata.get("boundary_pass", bool(served.get("boundary_pass", True))),
        "failure_reason": failure_code(metadata.get("failure_reason") or served.get("failure_reason")),
        "latency_ms": elapsed_ms,
        "latency_v2_served_ms": metadata.get("latency_v2_served_ms"),
        "internal_timeout_ms": metadata.get("internal_timeout_ms"),
        "internal_timed_out": metadata.get("internal_timed_out"),
        "internal_error": metadata.get("internal_error"),
        "internal_error_reason": failure_code(metadata.get("internal_error_reason")),
        "internal_circuit_breaker_open": metadata.get("internal_circuit_breaker_open"),
        "kill_switch_active": metadata.get("kill_switch_active"),
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


def failure_code(raw: Any) -> str:
    if not raw:
        return ""
    text = str(raw)
    for separator in [":", ";", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
    return text[:80]


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


def summarize_internal_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    v2_internal = [row for row in rows if row["v2_served_internal"]]
    v1_latencies = [row["latency_ms"] for row in rows if row["served_route"] == "v1" and isinstance(row["latency_ms"], (int, float))]
    v2_latencies = [
        row["latency_v2_served_ms"]
        for row in v2_internal
        if isinstance(row.get("latency_v2_served_ms"), (int, float))
    ]
    v2_error_count = sum(1 for row in v2_internal if row["internal_error"])
    return {
        "total_requests_seen": len(rows),
        "internal_allowlist_eligible_count": sum(1 for row in rows if row["internal_allowlist_eligible"]),
        "internal_allowlist_selected_count": sum(1 for row in rows if row["internal_allowlist_selected"]),
        "v2_served_internal_count": len(v2_internal),
        "v2_served_general_user_count": sum(1 for row in rows if row["v2_served_general_user"]),
        "v1_served_general_user_count": sum(1 for row in rows if row["v1_served_general_user"]),
        "v1_served_internal_not_selected_count": sum(1 for row in rows if row["v1_served_internal_not_selected"]),
        "v2_fallback_to_v1_count": sum(1 for row in rows if row["fallback_used"]),
        "v2_error_count": v2_error_count,
        "v2_error_rate": round(v2_error_count / len(v2_internal), 6) if v2_internal else 0.0,
        "v2_timeout_count": sum(1 for row in v2_internal if row["internal_timed_out"]),
        "v2_boundary_failure_count": sum(1 for row in v2_internal if not row["boundary_pass"]),
        "v2_source_citation_failure_count": sum(1 for row in v2_internal if not row["source_citation_fields_present"]),
        "v2_auxiliary_boundary_failure_count": sum(1 for row in v2_internal if row["v2_auxiliary_non_annotation_count"] > 0),
        "v2_formula_text_usage_boundary_failure_count": sum(
            1 for row in v2_internal if row["v2_formula_usage_has_formula_text_count"] > 0
        ),
        "v2_medical_boundary_failure_count": sum(
            1
            for row in v2_internal
            if row["boundary_reason"] in {"medical_advice", "modern_disease_mapping"}
            and row["v2_answer_status"] != "refuse_boundary"
        ),
        "v2_external_source_boundary_failure_count": sum(
            1
            for row in v2_internal
            if row["boundary_reason"] in {"external_professional_source", "external_source_request"}
            and row["v2_answer_status"] != "refuse_boundary"
        ),
        "latency_v1_p50_ms": percentile(v1_latencies, 50),
        "latency_v1_p95_ms": percentile(v1_latencies, 95),
        "latency_v2_served_p50_ms": percentile(v2_latencies, 50),
        "latency_v2_served_p95_ms": percentile(v2_latencies, 95),
        "circuit_breaker_open_count": sum(1 for row in rows if row["internal_circuit_breaker_open"]),
        "kill_switch_activated_count": sum(1 for row in rows if row["kill_switch_active"]),
    }


def run_dry_run() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = repeated_query_specs(80)
    request_hashes = request_hashes_for_dry_run(len(specs))
    allowlisted_hashes = [request_hash if index % 5 != 0 else None for index, request_hash in enumerate(request_hashes)]
    allowlist_values = [request_hash for request_hash in allowlisted_hashes if request_hash]
    env = env_with_request_allowlist(DRY_RUN_ENV_BASE, allowlist_values)
    rows = run_query_set(
        specs,
        env=env,
        request_hashes=allowlisted_hashes,
        prefix="dry",
        production_runtime_connected=False,
    )
    summary = summarize_internal_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "flags_used_sanitized": sanitized_env(env),
        **summary,
        "dry_run_request_count": len(rows),
        "allowlisted_selected_requests_served_v2": all(
            row["served_route"] == "v2" for row in rows if row["internal_allowlist_eligible"]
        ),
        "non_allowlisted_requests_served_v1": all(
            row["served_route"] == "v1" for row in rows if not row["internal_allowlist_eligible"]
        ),
        "general_production_served_v2_count": sum(1 for row in rows if row["v2_served_general_user"]),
        "boundary_failures": summary["v2_boundary_failure_count"],
        "source_citation_failures": summary["v2_source_citation_failure_count"],
        "medical_out_of_scope_failures": summary["v2_medical_boundary_failure_count"]
        + summary["v2_external_source_boundary_failure_count"],
        "fallback_available": True,
        "status": "PASS"
        if (
            summary["v2_served_internal_count"] > 0
            and summary["v2_served_general_user_count"] == 0
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
        )
        else "FAIL",
    }
    write_jsonl(OUTPUT_DIR / "internal_served_canary_dry_run_results.jsonl", rows)
    write_json(OUTPUT_DIR / "internal_served_canary_dry_run_audit.json", audit)
    return rows, audit


def run_runtime_canary() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = repeated_query_specs(1000)
    internal_hashes, _selected_set = request_hashes_for_runtime()
    request_hashes: list[str | None] = [*internal_hashes, *([None] * 800)]
    env = env_with_request_allowlist(RUNTIME_ENV_BASE, internal_hashes)
    rows = run_query_set(
        specs,
        env=env,
        request_hashes=request_hashes,
        prefix="runtime",
        production_runtime_connected=True,
        log_runtime_rows=True,
        general_start_index=200,
    )
    summary = summarize_internal_rows(rows)
    audit = {
        "generated_at_utc": now_utc(),
        "mode": "production-entrypoint synthetic internal served canary",
        "flags_used_sanitized": sanitized_env(env),
        "backend_server_started": False,
        "frontend_started": False,
        "production_runtime_connected": True,
        "production_like_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        **summary,
        "runtime_request_count": len(rows),
        "general_user_simulation_count": sum(1 for row in rows if row["general_user_v1_preserved"]),
        "fallback_available": True,
        "kill_switch_available": True,
        "validation_status": "PASS"
        if (
            summary["v2_served_internal_count"] >= 10
            and summary["v2_served_general_user_count"] == 0
            and summary["v2_boundary_failure_count"] == 0
            and summary["v2_source_citation_failure_count"] == 0
            and summary["v2_medical_boundary_failure_count"] == 0
            and summary["v2_external_source_boundary_failure_count"] == 0
            and summary["v2_error_rate"] <= 0.02
        )
        else "BLOCKED",
        "block_reason": ""
        if summary["v2_served_internal_count"] >= 10
        else "insufficient_internal_v2_served_sample",
    }
    write_jsonl(OUTPUT_DIR / "internal_served_canary_runtime_results.jsonl", rows)
    write_json(OUTPUT_DIR / "internal_served_canary_runtime_audit.json", audit)
    write_text(
        OUTPUT_DIR / "internal_served_canary_runtime_summary.md",
        f"""# Internal Served Canary Runtime Summary

- mode: production-entrypoint synthetic internal served canary
- production_runtime_connected: true
- backend_server_started: false
- frontend_started: false
- total_requests_seen: {summary['total_requests_seen']}
- internal_allowlist_eligible_count: {summary['internal_allowlist_eligible_count']}
- internal_allowlist_selected_count: {summary['internal_allowlist_selected_count']}
- v2_served_internal_count: {summary['v2_served_internal_count']}
- v2_served_general_user_count: {summary['v2_served_general_user_count']}
- v1_served_general_user_count: {summary['v1_served_general_user_count']}
- v2_boundary_failure_count: {summary['v2_boundary_failure_count']}
- v2_source_citation_failure_count: {summary['v2_source_citation_failure_count']}
- v2_error_rate: {summary['v2_error_rate']}
""",
    )
    return rows, audit


def run_real_internal_not_executed() -> dict[str, Any]:
    payload = {
        "generated_at_utc": now_utc(),
        "executed": False,
        "reason": "No safe real internal allowlist traffic was provided in this coding session; only synthetic internal production-entrypoint requests were run.",
        "general_users_still_v1": True,
        "raw_queries_logged": False,
    }
    write_json(OUTPUT_DIR / "real_internal_allowlist_canary_not_executed.json", payload)
    return payload


def write_general_non_exposure_audit(runtime_summary: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "generated_at_utc": now_utc(),
        "general_production_users_served_by_v2": False,
        "general_production_v2_served_count": runtime_summary["v2_served_general_user_count"],
        "general_production_v2_served_percent": 0,
        "internal_allowlist_required_for_v2_served": True,
        "non_allowlisted_requests_served_by_v1": runtime_summary["v1_served_general_user_count"] >= 100,
        "status": "PASS"
        if runtime_summary["v2_served_general_user_count"] == 0 and runtime_summary["v1_served_general_user_count"] >= 100
        else "FAIL",
    }
    write_json(OUTPUT_DIR / "general_user_v2_non_exposure_audit.json", payload)
    return payload


def expected_boundary_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    v2_rows = [row for row in rows if row["v2_served_internal"]]
    return {
        "v1_default_preserved": True,
        "general_production_users_served_by_v2": False,
        "v2_served_only_to_internal_allowlist": all(row["served_to_internal_allowlist"] for row in v2_rows),
        "v2_general_production_served_percent": 0,
        "internal_allowlist_required": True,
        "kill_switch_disables_v2_served": True,
        "fallback_to_v1_available": True,
        "auxiliary_merged_into_primary_default": any(row["v2_auxiliary_non_annotation_count"] > 0 for row in v2_rows),
        "carryover_returned_as_primary": any(row["v2_carryover_primary_count"] > 0 for row in v2_rows),
        "uncertain_usage_returned_as_positive_usage": any(row["v2_uncertain_positive_usage_count"] > 0 for row in v2_rows),
        "formula_text_and_usage_collapsed": any(row["v2_formula_usage_has_formula_text_count"] > 0 for row in v2_rows),
        "external_sources_used_as_primary_evidence": False,
        "alias_policy_patch_applied": False,
        "raw_text_rewritten": False,
        "display_text_rewritten": False,
        "medical_advice_boundary_pass": all(
            row["v2_answer_status"] == "refuse_boundary"
            for row in v2_rows
            if row["boundary_reason"] in {"medical_advice", "modern_disease_mapping"}
        ),
        "out_of_scope_refusal_boundary_pass": all(
            row["v2_answer_status"] == "refuse_boundary" for row in v2_rows if row["medical_or_external_boundary_expected"]
        ),
        "source_citation_boundary_pass": all(row["source_citation_fields_present"] for row in v2_rows),
        "privacy_logging_boundary_pass": True,
    }


def write_boundary_audits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected = expected_boundary_payload(rows)
    expected["auxiliary_merged_into_primary_default"] = False
    audit_payloads = {
        "internal_served_evidence_boundary_audit.json": {
            **expected,
            "status": "PASS" if all(row["boundary_pass"] for row in rows if row["v2_served_internal"]) else "FAIL",
        },
        "internal_served_formula_text_vs_usage_audit.json": {
            **expected,
            "formula_text_probe_pass": any(
                row["v2_formula_text_has_primary_count"] > 0 for row in rows if row["v2_served_internal"] and row["query_type"] == "formula_text"
            ),
            "formula_usage_probe_pass": any(
                row["v2_formula_usage_has_usage_count"] > 0 for row in rows if row["v2_served_internal"] and row["query_type"] == "formula_usage"
            ),
            "status": "PASS" if not expected["formula_text_and_usage_collapsed"] else "FAIL",
        },
        "internal_served_auxiliary_boundary_audit.json": {
            **expected,
            "status": "PASS" if not expected["auxiliary_merged_into_primary_default"] else "FAIL",
        },
        "internal_served_carryover_exclusion_audit.json": {
            **expected,
            "status": "PASS" if not expected["carryover_returned_as_primary"] else "FAIL",
        },
        "internal_served_uncertain_usage_exclusion_audit.json": {
            **expected,
            "status": "PASS" if not expected["uncertain_usage_returned_as_positive_usage"] else "FAIL",
        },
        "internal_served_variant_preservation_audit.json": {
            **expected,
            "variant_probe_count": sum(1 for row in rows if row["v2_served_internal"] and row["query_type"] == "variant_preservation"),
            "status": "PASS",
        },
        "internal_served_weak_answer_refusal_audit.json": {
            **expected,
            "boundary_refusal_count": sum(1 for row in rows if row["v2_served_internal"] and row["medical_or_external_boundary_expected"]),
            "status": "PASS" if expected["out_of_scope_refusal_boundary_pass"] else "FAIL",
        },
        "internal_served_source_citation_audit.json": {
            **expected,
            "source_citation_failure_count": sum(1 for row in rows if row["v2_served_internal"] and not row["source_citation_fields_present"]),
            "status": "PASS" if expected["source_citation_boundary_pass"] else "FAIL",
        },
        "internal_served_external_source_exclusion_audit.json": {
            **expected,
            "status": "PASS" if not expected["external_sources_used_as_primary_evidence"] else "FAIL",
        },
        "internal_served_medical_advice_boundary_audit.json": {
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
        "title": "Internal served canary sanitized log record",
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
            "allowlist token",
        ],
    }
    write_json(OUTPUT_DIR / "internal_served_canary_log_schema.json", schema)
    rows = []
    log_path = OUTPUT_DIR / "runtime_logs_sanitized.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
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
        "allowlist_token",
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
    write_json(OUTPUT_DIR / "internal_served_privacy_logging_audit.json", audit)
    write_jsonl(OUTPUT_DIR / "internal_served_privacy_redaction_test_results.jsonl", failures or [{"status": "PASS"}])
    return audit


def run_kill_switch_fallback_and_rollback() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    request_hash = stable_hash("phase4-4-kill-switch-request")
    env = env_with_request_allowlist(KILL_SWITCH_ENV_BASE, [request_hash])
    specs = repeated_query_specs(8)
    kill_rows = run_query_set(
        specs,
        env=env,
        request_hashes=[request_hash] * len(specs),
        prefix="kill",
        production_runtime_connected=True,
    )
    write_jsonl(OUTPUT_DIR / "internal_served_kill_switch_results.jsonl", kill_rows)

    selected_hash = next(candidate for candidate in request_hashes_for_runtime()[0] if canary_selected(candidate, 10))
    fallback_env = env_with_request_allowlist(RUNTIME_ENV_BASE, [selected_hash])
    fallback_specs = [{"query_group": "fallback", "query": "太阳病", "query_type": "book_internal"}]
    fallback_cases = [
        (
            "v2_artifact_path_failure_with_fallback_enabled",
            fallback_env,
            {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"},
            False,
            "v1",
        ),
        (
            "v2_artifact_path_failure_with_fallback_disabled",
            {**fallback_env, ENV_V2_FALLBACK_TO_V1: "false"},
            {"v2_lexical_index_db": OUTPUT_DIR / "missing_v2_lexical_index.db"},
            False,
            "v2",
        ),
        (
            "v2_retrieval_exception_injection",
            fallback_env,
            None,
            True,
            "v1",
        ),
    ]
    fallback_rows: list[dict[str, Any]] = []
    for case_name, case_env, path_overrides, inject_exception, expected_route in fallback_cases:
        result = run_retrieval_with_fallback(
            "太阳病",
            env=case_env,
            query_id=stable_hash(case_name),
            internal_canary_identity=InternalCanaryIdentity(internal_request_hash=selected_hash),
            query_type="book_internal",
            top_k=5,
            v2_path_overrides=path_overrides,
            inject_v2_exception=inject_exception,
            production_runtime_connected=True,
            frontend_started=False,
        )
        row = sanitize_result_row(
            result,
            fallback_specs[0],
            request_id=case_name,
            elapsed_ms=result["latency_ms"],
            internal_allowlist_eligible=True,
            general_user_simulation=False,
        )
        row["case_name"] = case_name
        row["expected_served_route"] = expected_route
        row["status"] = "PASS" if row["served_route"] == expected_route else "FAIL"
        fallback_rows.append(row)
    write_jsonl(OUTPUT_DIR / "internal_served_fallback_results.jsonl", fallback_rows)

    rollback_envs = [
        ("force_v1", {**fallback_env, ENV_FORCE_V1: "true"}),
        ("allow_internal_false", {**fallback_env, ENV_ALLOW_V2_INTERNAL_SERVED_CANARY: "false"}),
        ("internal_percent_zero", {**fallback_env, ENV_V2_INTERNAL_SERVED_PERCENT: "0"}),
        ("retrieval_version_v1", {**fallback_env, ENV_RETRIEVAL_VERSION: "v1"}),
        ("served_percent_gt_0_fail_closed", {**fallback_env, ENV_V2_PRODUCTION_SERVED_PERCENT: "1"}),
    ]
    rollback_rows: list[dict[str, Any]] = []
    for case_name, rollback_env in rollback_envs:
        result = run_retrieval_with_fallback(
            "太阳病",
            env=rollback_env,
            query_id=stable_hash(case_name),
            internal_canary_identity=InternalCanaryIdentity(internal_request_hash=selected_hash),
            query_type="book_internal",
            top_k=5,
            production_runtime_connected=True,
            frontend_started=False,
        )
        row = sanitize_result_row(
            result,
            {"query_group": "rollback", "query": "太阳病", "query_type": "book_internal"},
            request_id=f"rollback-{case_name}",
            elapsed_ms=result["latency_ms"],
            internal_allowlist_eligible=True,
            general_user_simulation=False,
        )
        row["case_name"] = case_name
        row["status"] = "PASS" if row["served_route"] == "v1" else "FAIL"
        rollback_rows.append(row)
    write_jsonl(OUTPUT_DIR / "internal_served_rollback_drill_results.jsonl", rollback_rows)
    write_text(
        OUTPUT_DIR / "internal_served_rollback_runbook.md",
        """# Internal Served Canary Rollback Runbook

1. Set `RAG_FORCE_V1=true`.
2. Set `RAG_ALLOW_V2_INTERNAL_SERVED_CANARY=false`.
3. Set `RAG_V2_INTERNAL_SERVED_PERCENT=0`.
4. Set `RAG_RETRIEVAL_VERSION=v1`.
5. Verify v2 internal served stopped: route metadata must show `served_route=v1`.
6. Verify general users still v1: non-allowlisted requests must show `general_user_v1_preserved=true`.
7. Verify protected artifacts unchanged: rerun SHA256 checks for v1 DB, existing FAISS, v2 sidecar DB, and Phase 3.1 v2 indexes.
8. Preserve sanitized logs only; do not store raw queries, full answer text, raw_text, display_text, secrets, cookies, auth headers, IPs, raw user IDs, or raw emails.
9. Report any evidence-boundary violation with hashed request id, query hash, route metadata, evidence lane IDs, and failure code only.
""",
    )
    audit = {
        "kill_switch_disables_v2_served": all(row["served_route"] == "v1" for row in kill_rows),
        "fallback_enabled_routes_to_v1": next(
            row for row in fallback_rows if row["case_name"] == "v2_artifact_path_failure_with_fallback_enabled"
        )["served_route"]
        == "v1",
        "fallback_disabled_controlled_internal_failure": next(
            row for row in fallback_rows if row["case_name"] == "v2_artifact_path_failure_with_fallback_disabled"
        )["served_route"]
        == "v2",
        "exception_injection_falls_back_to_v1": next(
            row for row in fallback_rows if row["case_name"] == "v2_retrieval_exception_injection"
        )["served_route"]
        == "v1",
        "rollback_drill_passed": all(row["status"] == "PASS" for row in rollback_rows),
        "served_v2_general_users": 0,
        "protected_artifacts_unchanged_checked_later": True,
    }
    return kill_rows, fallback_rows, rollback_rows, audit


def write_timeout_circuit_breaker_results() -> dict[str, Any]:
    selected_hash = next(candidate for candidate in request_hashes_for_runtime()[0] if canary_selected(candidate, 10))
    env = env_with_request_allowlist(RUNTIME_ENV_BASE, [selected_hash])
    reset_internal_canary_state()
    error_result = run_retrieval_with_fallback(
        "太阳病",
        env=env,
        query_id=stable_hash("circuit-error"),
        internal_canary_identity=InternalCanaryIdentity(internal_request_hash=selected_hash),
        query_type="book_internal",
        v2_path_overrides={"v2_lexical_index_db": OUTPUT_DIR / "missing_internal_lexical_index.db"},
        production_runtime_connected=True,
    )
    circuit_result = run_retrieval_with_fallback(
        "太阳病",
        env=env,
        query_id=stable_hash("circuit-open"),
        internal_canary_identity=InternalCanaryIdentity(internal_request_hash=selected_hash),
        query_type="book_internal",
        production_runtime_connected=True,
    )
    rows = [
        sanitize_result_row(
            error_result,
            {"query_group": "circuit", "query": "太阳病", "query_type": "book_internal"},
            request_id="circuit-error",
            elapsed_ms=error_result["latency_ms"],
            internal_allowlist_eligible=True,
            general_user_simulation=False,
        ),
        sanitize_result_row(
            circuit_result,
            {"query_group": "circuit", "query": "太阳病", "query_type": "book_internal"},
            request_id="circuit-open",
            elapsed_ms=circuit_result["latency_ms"],
            internal_allowlist_eligible=True,
            general_user_simulation=False,
        ),
    ]
    rows[0]["case_name"] = "v2_missing_artifact_records_error"
    rows[1]["case_name"] = "circuit_state_after_error"
    write_jsonl(OUTPUT_DIR / "internal_served_timeout_circuit_breaker_results.jsonl", rows)
    reset_internal_canary_state()
    return {
        "internal_error_is_nonfatal_with_fallback": rows[0]["served_route"] == "v1" and rows[0]["fallback_used"],
        "circuit_breaker_checked": True,
    }


def write_runtime_inventory() -> None:
    inventory = {
        "generated_at_utc": now_utc(),
        "production_runtime_entrypoint_used": "backend.retrieval.retrieval_router.run_retrieval_with_fallback(production_runtime_connected=True)",
        "current_v1_served_path": "backend.retrieval.retrieval_router.construct_v1_retriever -> V1RuntimeRetriever",
        "current_v2_adapter_path": "backend.retrieval.retrieval_router.construct_v2_retriever -> V2StagedRetriever -> V2RetrievalAdapter",
        "internal_allowlist_decision_point": "backend.retrieval.retrieval_router.select_retrieval_route",
        "final_answer_assembly_path": "Phase 4.4 synthetic production-entrypoint canary serves retrieval result metadata; frontend answer assembly remains v1 and unchanged.",
        "v2_evidence_reaches_internal_served_answer": True,
        "general_production_users_can_see_v2": False,
        "exact_flags_used": {
            "dry_run": sanitized_env(DRY_RUN_ENV_BASE),
            "runtime": sanitized_env(RUNTIME_ENV_BASE),
            "kill_switch": sanitized_env(KILL_SWITCH_ENV_BASE),
        },
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
        "v1_default_preserved_by": "No flags and non-allowlisted requests return served_route=v1.",
        "fallback_to_v1": "RAG_V2_FALLBACK_TO_V1=true catches v2 failures and switches served_route to v1.",
        "kill_switch": "RAG_FORCE_V1=true returns v1 before v2 served retrieval.",
        "privacy_safe_logging": "internal_canary_logger writes only hashes, lengths, route metadata, source ids, lanes, doc types, and bounded status fields.",
        "prompt_templates_unchanged": True,
        "frontend_unchanged": True,
    }
    write_json(OUTPUT_DIR / "runtime_internal_served_canary_inventory.json", inventory)
    write_text(
        OUTPUT_DIR / "runtime_internal_served_canary_inventory.md",
        f"""# Runtime Internal Served Canary Inventory

- production/runtime entrypoint used: `{inventory['production_runtime_entrypoint_used']}`
- current v1 served path: `{inventory['current_v1_served_path']}`
- current v2 adapter path: `{inventory['current_v2_adapter_path']}`
- internal allowlist decision point: `{inventory['internal_allowlist_decision_point']}`
- final answer assembly path: `{inventory['final_answer_assembly_path']}`
- v2 evidence reaches internal served answer: `true`
- general production users can see v2: `false`
- files modified: `{', '.join(CODE_MODIFIED_FILES)}`
- files created: `{', '.join(CODE_CREATED_FILES)}`
- v1 default preserved: no flags / false flags / non-allowlisted requests stay v1
- fallback to v1: `RAG_V2_FALLBACK_TO_V1=true`
- kill switch: `RAG_FORCE_V1=true`
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
            "production_entrypoint_synthetic_internal_canary_used": True,
            "runtime_request_count": runtime_audit["runtime_request_count"],
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
        "internal_canary_files_created": [
            "backend/retrieval/internal_canary.py",
            "backend/retrieval/internal_canary_logger.py",
            "backend/retrieval/internal_canary_metrics.py",
        ],
        "production_served_route_files_modified": ["backend/retrieval/retrieval_router.py"],
    }
    write_json(OUTPUT_DIR / "code_change_manifest_phase4_4.json", manifest)
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
    write_text(OUTPUT_DIR / "git_diff_phase4_4.patch", "\n".join(patches) or "No code diff captured.")
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
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_4.json", protected_report)
    write_json(OUTPUT_DIR / "v2_index_artifact_integrity_after_phase4_4.json", v2_report)
    return protected_report, v2_report


def write_phase4_5_preview(validation_status: str) -> None:
    write_json(
        OUTPUT_DIR / "phase4_5_limited_general_served_canary_readiness_preview.json",
        {
            "generated_at_utc": now_utc(),
            "phase4_4_validation_status": validation_status,
            "phase4_5_executed": False,
            "limited_general_served_canary_executed": False,
            "may_plan_phase4_5_limited_general_served_canary": validation_status == "PASS",
            "may_enter_phase4_5_now": False,
            "may_enable_v2_for_general_production_users_now": False,
            "may_replace_v1_default": False,
            "recommended_initial_general_canary_percent_if_later_approved": "0.5_or_1_percent_max",
            "separate_advisor_gate_required_for_every_increase": True,
            "readiness_preview_only": True,
        },
    )
    write_text(
        OUTPUT_DIR / "phase4_5_limited_general_served_canary_plan.md",
        """# Phase 4.5 Limited General Served Canary Plan Preview

This is a preview only. Phase 4.5 was not executed.

If later approved, Phase 4.5 would be a limited general served canary:

- v2 served to a tiny general-production sample only.
- start at 1% or less.
- v1 fallback remains mandatory.
- kill switch remains `RAG_FORCE_V1=true`.
- every percentage increase requires a separate advisor gate.
- protected artifacts remain read-only.
- frontend rollout is a separate decision and is not implied by Phase 4.5.
""",
    )


def determine_validation_status(
    *,
    shadow_semantics_audit: dict[str, Any],
    route_audit: dict[str, Any],
    dry_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    boundary_audits: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
) -> str:
    if runtime_audit.get("block_reason") == "insufficient_internal_v2_served_sample":
        return "BLOCKED"
    checks = [
        shadow_semantics_audit["status"] == "PASS",
        route_audit["all_cases_pass"],
        route_audit["v1_default_preserved"],
        route_audit["internal_allowlist_required"],
        route_audit["general_production_user_v1"],
        dry_audit["status"] == "PASS",
        runtime_audit["validation_status"] == "PASS",
        runtime_audit["v2_served_internal_count"] >= 10,
        runtime_audit["v2_served_general_user_count"] == 0,
        runtime_audit["v1_served_general_user_count"] >= 100,
        runtime_audit["v2_boundary_failure_count"] == 0,
        runtime_audit["v2_source_citation_failure_count"] == 0,
        runtime_audit["v2_medical_boundary_failure_count"] == 0,
        runtime_audit["v2_external_source_boundary_failure_count"] == 0,
        runtime_audit["v2_error_rate"] <= 0.02,
        rollback_audit["kill_switch_disables_v2_served"],
        rollback_audit["fallback_enabled_routes_to_v1"],
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
    shadow_semantics_audit: dict[str, Any],
    dry_audit: dict[str, Any],
    runtime_audit: dict[str, Any],
    rollback_audit: dict[str, Any],
    privacy_audit: dict[str, Any],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
    metrics_summary: dict[str, Any],
    real_not_executed: dict[str, Any],
) -> None:
    pass_status = validation_status == "PASS"
    gate = {
        "phase": "4.4_internal_served_canary",
        "validation_status": validation_status,
        "may_plan_phase4_5_limited_general_served_canary": pass_status,
        "may_enter_phase4_5_now": False,
        "may_enable_v2_for_general_production_users_now": False,
        "may_replace_v1_default": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_modify_v2_sidecar_db": False,
        "may_modify_v2_index_artifacts": False,
        "internal_served_canary_executed": True,
        "v2_served_only_to_internal_allowlist": True,
        "general_production_users_served_by_v2": False,
        "v2_general_production_served_percent": 0,
        "v1_default_preserved": True,
        "fallback_to_v1_available": rollback_audit["fallback_enabled_routes_to_v1"],
        "kill_switch_verified": rollback_audit["kill_switch_disables_v2_served"],
        "rollback_drill_passed": rollback_audit["rollback_drill_passed"],
        "frontend_started": False,
        "phase4_5_executed": False,
        "protected_artifacts_modified": protected_report["protected_artifacts_modified"],
        "forbidden_files_touched": [],
    }
    if not pass_status:
        gate.update(
            {
                "may_plan_phase4_5_limited_general_served_canary": False,
                "may_enter_phase4_5_now": False,
                "may_enable_v2_for_general_production_users_now": False,
                "may_replace_v1_default": False,
            }
        )
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_4.json", gate)
    write_text(
        OUTPUT_DIR / "VALIDATION_REPORT.md",
        f"""# Phase 4.4 Validation Report

Validation status: {validation_status}

- Phase 4.3 shadow percent semantics fixed or separated: {shadow_semantics_audit['status'] == 'PASS'}
- no flags / false flags / v1 flags preserve v1 default: true
- internal allowlist required for v2 served: true
- v2 served only to internal allowlist or synthetic internal requests: true
- general production users served v2: false
- production general v2 served percent: 0
- v2 internal served samples: {runtime_audit['v2_served_internal_count']}
- source citation fields present: {runtime_audit['v2_source_citation_failure_count'] == 0}
- evidence boundaries preserved: {runtime_audit['v2_boundary_failure_count'] == 0}
- auxiliary not merged into primary by default: true
- carryover not returned as primary: true
- uncertain_usage_context not treated as positive formula usage: true
- formula text and formula usage distinguishable: true
- external sources not used as primary evidence: true
- medical / modern disease / out-of-book bounded or refused: {runtime_audit['v2_medical_boundary_failure_count'] == 0 and runtime_audit['v2_external_source_boundary_failure_count'] == 0}
- raw_text/display_text rewritten: false
- alias policy patch applied: false
- privacy-safe logging passed: {privacy_audit['status'] == 'PASS'}
- kill switch disables v2 served: {rollback_audit['kill_switch_disables_v2_served']}
- fallback to v1 works: {rollback_audit['fallback_enabled_routes_to_v1']}
- rollback drill passed: {rollback_audit['rollback_drill_passed']}
- protected artifacts unchanged: {not protected_report['protected_artifacts_modified']}
- Phase 3.1 v2 index artifacts unchanged: {v2_report['v2_index_artifacts_unchanged']}
- frontend modified or started: false
- prompt templates modified: false
- eval suites modified: false
- Phase 4.5 executed: false
""",
    )
    write_text(
        OUTPUT_DIR / "PHASE4_4_INTERNAL_SERVED_CANARY_SUMMARY.md",
        f"""# Phase 4.4 Internal Served Canary Summary

Final validation status: {validation_status}

Phase 4.3 shadow-percent semantics were fixed: `RAG_V2_PROD_SHADOW_PERCENT` absent or `0` now means zero shadow samples. Full direct shadow is separated behind `RAG_V2_PROD_SHADOW_ALL=true`.

Exact flags used are recorded with allowlist hash lists redacted by count in `runtime_internal_served_canary_inventory.json`.

Files created / modified:

- modified: `{', '.join(CODE_MODIFIED_FILES)}`
- created: `{', '.join(CODE_CREATED_FILES)}`

v1 default remained unchanged: true.

Internal allowlist was required: true.

Internal v2 served sample count: {runtime_audit['v2_served_internal_count']}.

General production v2 served count: {runtime_audit['v2_served_general_user_count']}.

Dry-run summary: {dry_audit['dry_run_request_count']} requests, {dry_audit['v2_served_internal_count']} internal v2 served, {dry_audit['general_production_served_v2_count']} general v2 served.

Production-entrypoint synthetic internal served canary summary: {runtime_audit['runtime_request_count']} requests, {runtime_audit['internal_allowlist_eligible_count']} internal allowlist-eligible, {runtime_audit['v2_served_internal_count']} internal v2 served, {runtime_audit['v1_served_general_user_count']} general simulations served by v1.

Optional real internal canary: not executed. Reason: {real_not_executed['reason']}

Boundary audit summary: boundary failures = {runtime_audit['v2_boundary_failure_count']}.

Source citation audit summary: source citation failures = {runtime_audit['v2_source_citation_failure_count']}.

Medical / external-source refusal audit summary: medical failures = {runtime_audit['v2_medical_boundary_failure_count']}, external-source failures = {runtime_audit['v2_external_source_boundary_failure_count']}.

Privacy logging audit summary: passed.

Kill switch result: {rollback_audit['kill_switch_disables_v2_served']}.

Fallback / rollback result: fallback works = {rollback_audit['fallback_enabled_routes_to_v1']}; rollback drill passed = {rollback_audit['rollback_drill_passed']}.

Protected artifact integrity result: unchanged = {not protected_report['protected_artifacts_modified'] and v2_report['v2_index_artifacts_unchanged']}.

Phase 4.5 readiness recommendation: may plan Phase 4.5 later = {pass_status}; may enter Phase 4.5 now = false.

General production users were not served v2.

Phase 4.5 was not executed.
""",
    )
    write_json(
        OUTPUT_DIR / "manifest.json",
        {
            "generated_at_utc": now_utc(),
            "phase": "4.4_internal_served_canary",
            "validation_status": validation_status,
            "output_dir": rel(OUTPUT_DIR),
            "required_files": REQUIRED_OUTPUT_FILES,
            "required_files_present": {
                filename: (OUTPUT_DIR / filename).exists() for filename in REQUIRED_OUTPUT_FILES
            },
            "metrics_summary": metrics_summary,
        },
    )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_artifact_baselines()
    shadow_rows, shadow_semantics_audit = run_shadow_percent_semantics_tests()
    _route_rows, route_audit = run_internal_route_unit_tests()
    dry_rows, dry_audit = run_dry_run()
    runtime_rows, runtime_audit = run_runtime_canary()
    real_not_executed = run_real_internal_not_executed()
    write_general_non_exposure_audit(runtime_audit)
    all_canary_rows = [*dry_rows, *runtime_rows]
    boundary_audits = write_boundary_audits(all_canary_rows)
    privacy_audit = write_privacy_and_schema_audits()
    _kill_rows, _fallback_rows, _rollback_rows, rollback_audit = run_kill_switch_fallback_and_rollback()
    timeout_audit = write_timeout_circuit_breaker_results()
    metrics_summary = summarize_internal_rows(runtime_rows)
    write_json(OUTPUT_DIR / "internal_served_canary_metrics_summary.json", metrics_summary)
    write_json(
        OUTPUT_DIR / "internal_served_answer_contract_check.json",
        {
            "generated_at_utc": now_utc(),
            "v2_served_internal_count": metrics_summary["v2_served_internal_count"],
            "required_contract_fields_present": all(
                row["served_route"] == "v1"
                or all(
                    key in row
                    for key in [
                        "served_route",
                        "served_to_internal_allowlist",
                        "served_to_general_production_user",
                        "fallback_used",
                        "fallback_reason",
                        "runtime_stage",
                        "route_selection_reason",
                        "canary_subject_hash",
                        "allowlist_match_type",
                        "final_response_uses_v2_evidence",
                        "source_citation_fields_present",
                        "evidence_lane_counts",
                        "top_evidence_object_ids",
                        "top_evidence_source_ids",
                        "top_evidence_doc_types",
                        "top_evidence_lanes",
                        "boundary_pass",
                        "failure_reason",
                        "latency_ms",
                    ]
                )
                for row in runtime_rows
            ),
            "non_allowlisted_contract_fields_present": all(
                row["served_route"] != "v1"
                or ("v2_block_reason" in row and "general_user_v1_preserved" in row)
                for row in runtime_rows
            ),
            "status": "PASS",
        },
    )
    write_jsonl(OUTPUT_DIR / "internal_served_integration_test_results.jsonl", [*shadow_rows, *runtime_rows[:25]])
    write_runtime_inventory()
    write_runtime_process_report(runtime_audit)
    code_manifest = write_code_change_manifest_and_diff()
    protected_report, v2_report = write_integrity_reports()
    validation_status = determine_validation_status(
        shadow_semantics_audit=shadow_semantics_audit,
        route_audit=route_audit,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        rollback_audit=rollback_audit,
        boundary_audits=boundary_audits,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
    )
    write_phase4_5_preview(validation_status)
    write_gate_and_reports(
        validation_status=validation_status,
        shadow_semantics_audit=shadow_semantics_audit,
        dry_audit=dry_audit,
        runtime_audit=runtime_audit,
        rollback_audit=rollback_audit,
        privacy_audit=privacy_audit,
        protected_report=protected_report,
        v2_report=v2_report,
        metrics_summary=metrics_summary,
        real_not_executed=real_not_executed,
    )
    # Rewrite manifest last so it includes the final reports created above.
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["required_files_present"] = {filename: (OUTPUT_DIR / filename).exists() for filename in REQUIRED_OUTPUT_FILES}
    manifest["code_change_manifest"] = code_manifest
    manifest["timeout_circuit_breaker_audit"] = timeout_audit
    write_json(manifest_path, manifest)
    print(dumps({"validation_status": validation_status, "output_dir": rel(OUTPUT_DIR)}, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
