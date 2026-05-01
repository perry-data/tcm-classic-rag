from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from backend.retrieval.internal_canary import (
    InternalAllowlistMatch,
    InternalCanaryIdentity,
    coerce_identity,
    evidence_contract_fields,
    match_internal_allowlist,
    parse_allowlist_hashes,
)
from backend.retrieval.canary_boundary_monitor import (
    CanaryMonitorAvailability,
    audit_v2_general_canary_result,
)
from backend.retrieval.limited_general_canary import (
    GeneralCanaryIdentity,
    coerce_general_identity,
    general_canary_decision_hash,
    general_canary_selected,
    parse_general_served_percent,
    select_general_subject_hash,
)
from backend.retrieval.v2_adapter import (
    DEFAULT_V1_DB_PATH,
    DEFAULT_V1_DENSE_CHUNKS_INDEX,
    DEFAULT_V1_DENSE_MAIN_INDEX,
    DEFAULT_V2_INDEX_DIR,
    DEFAULT_V2_SIDECAR_DB,
    V2_LANE_SPECS,
    V2RetrievalAdapter,
    resolve_project_path,
)


ENV_RETRIEVAL_VERSION = "RAG_RETRIEVAL_VERSION"
ENV_V2_ENABLED = "RAG_V2_ENABLED"
ENV_ALLOW_V2_CONTROLLED_ROLLOUT = "RAG_ALLOW_V2_CONTROLLED_ROLLOUT"
ENV_ALLOW_V2_PRODUCTION_SHADOW = "RAG_ALLOW_V2_PRODUCTION_SHADOW"
ENV_RUNTIME_STAGE = "RAG_RUNTIME_STAGE"
ENV_V2_SHADOW_COMPARE = "RAG_V2_SHADOW_COMPARE"
ENV_V2_CANARY_PERCENT = "RAG_V2_CANARY_PERCENT"
ENV_V2_PROD_SHADOW_PERCENT = "RAG_V2_PROD_SHADOW_PERCENT"
ENV_V2_PROD_SHADOW_ALL = "RAG_V2_PROD_SHADOW_ALL"
ENV_V2_PRODUCTION_SERVED_PERCENT = "RAG_V2_PRODUCTION_SERVED_PERCENT"
ENV_ALLOW_V2_INTERNAL_SERVED_CANARY = "RAG_ALLOW_V2_INTERNAL_SERVED_CANARY"
ENV_V2_INTERNAL_SERVED_PERCENT = "RAG_V2_INTERNAL_SERVED_PERCENT"
ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES = "RAG_V2_INTERNAL_ALLOWLIST_USER_HASHES"
ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS = "RAG_V2_INTERNAL_ALLOWLIST_QUERY_IDS"
ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES = "RAG_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES"
ENV_V2_INTERNAL_CANARY_REQUIRE_ALLOWLIST = "RAG_V2_INTERNAL_CANARY_REQUIRE_ALLOWLIST"
ENV_V2_INTERNAL_MAX_ERROR_RATE = "RAG_V2_INTERNAL_MAX_ERROR_RATE"
ENV_V2_INTERNAL_MAX_BOUNDARY_FAILURES = "RAG_V2_INTERNAL_MAX_BOUNDARY_FAILURES"
ENV_V2_INTERNAL_TIMEOUT_MS = "RAG_V2_INTERNAL_TIMEOUT_MS"
ENV_V2_INTERNAL_CIRCUIT_BREAKER = "RAG_V2_INTERNAL_CIRCUIT_BREAKER"
ENV_ALLOW_V2_LIMITED_GENERAL_CANARY = "RAG_ALLOW_V2_LIMITED_GENERAL_CANARY"
ENV_V2_GENERAL_SERVED_PERCENT = "RAG_V2_GENERAL_SERVED_PERCENT"
ENV_V2_GENERAL_CANARY_MAX_PERCENT = "RAG_V2_GENERAL_CANARY_MAX_PERCENT"
ENV_V2_GENERAL_CANARY_REQUIRE_MONITORS = "RAG_V2_GENERAL_CANARY_REQUIRE_MONITORS"
ENV_V2_GENERAL_CANARY_DETERMINISTIC = "RAG_V2_GENERAL_CANARY_DETERMINISTIC"
ENV_V2_GENERAL_TIMEOUT_MS = "RAG_V2_GENERAL_TIMEOUT_MS"
ENV_V2_GENERAL_CIRCUIT_BREAKER = "RAG_V2_GENERAL_CIRCUIT_BREAKER"
ENV_V2_GENERAL_MAX_ERROR_RATE = "RAG_V2_GENERAL_MAX_ERROR_RATE"
ENV_V2_GENERAL_MAX_BOUNDARY_FAILURES = "RAG_V2_GENERAL_MAX_BOUNDARY_FAILURES"
ENV_V2_GENERAL_MAX_SOURCE_CITATION_FAILURES = "RAG_V2_GENERAL_MAX_SOURCE_CITATION_FAILURES"
ENV_V2_GENERAL_MAX_MEDICAL_BOUNDARY_FAILURES = "RAG_V2_GENERAL_MAX_MEDICAL_BOUNDARY_FAILURES"
ENV_V2_GENERAL_MAX_EXTERNAL_SOURCE_FAILURES = "RAG_V2_GENERAL_MAX_EXTERNAL_SOURCE_FAILURES"
ENV_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE = "RAG_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE"
ENV_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE = "RAG_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE"
ENV_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE = "RAG_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE"
ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH = "RAG_ALLOW_V2_STAGING_DEFAULT_SWITCH"
ENV_ALLOW_V2_STAGING_DEFAULT = "RAG_ALLOW_V2_STAGING_DEFAULT"
ENV_STAGING_DEFAULT_RETRIEVAL_VERSION = "RAG_STAGING_DEFAULT_RETRIEVAL_VERSION"
ENV_V2_STAGING_DEFAULT = "RAG_V2_STAGING_DEFAULT"
ENV_V2_STAGING_DEFAULT_REQUIRE_MONITORS = "RAG_V2_STAGING_DEFAULT_REQUIRE_MONITORS"
ENV_V2_STAGING_DEFAULT_PERCENT = "RAG_V2_STAGING_DEFAULT_PERCENT"
ENV_V2_STAGING_TIMEOUT_MS = "RAG_V2_STAGING_TIMEOUT_MS"
ENV_V2_STAGING_DEFAULT_TIMEOUT_MS = "RAG_V2_STAGING_DEFAULT_TIMEOUT_MS"
ENV_V2_STAGING_CIRCUIT_BREAKER = "RAG_V2_STAGING_CIRCUIT_BREAKER"
ENV_V2_STAGING_DEFAULT_CIRCUIT_BREAKER = "RAG_V2_STAGING_DEFAULT_CIRCUIT_BREAKER"
ENV_V2_STAGING_MAX_ERROR_RATE = "RAG_V2_STAGING_MAX_ERROR_RATE"
ENV_V2_STAGING_DEFAULT_MAX_ERROR_RATE = "RAG_V2_STAGING_DEFAULT_MAX_ERROR_RATE"
ENV_V2_STAGING_MAX_TIMEOUT_RATE = "RAG_V2_STAGING_MAX_TIMEOUT_RATE"
ENV_V2_STAGING_DEFAULT_MAX_TIMEOUT_RATE = "RAG_V2_STAGING_DEFAULT_MAX_TIMEOUT_RATE"
ENV_V2_STAGING_MAX_BOUNDARY_FAILURES = "RAG_V2_STAGING_MAX_BOUNDARY_FAILURES"
ENV_V2_STAGING_DEFAULT_MAX_BOUNDARY_FAILURES = "RAG_V2_STAGING_DEFAULT_MAX_BOUNDARY_FAILURES"
ENV_V2_STAGING_MAX_SOURCE_CITATION_FAILURES = "RAG_V2_STAGING_MAX_SOURCE_CITATION_FAILURES"
ENV_V2_STAGING_DEFAULT_MAX_SOURCE_CITATION_FAILURES = "RAG_V2_STAGING_DEFAULT_MAX_SOURCE_CITATION_FAILURES"
ENV_V2_STAGING_MAX_MEDICAL_BOUNDARY_FAILURES = "RAG_V2_STAGING_MAX_MEDICAL_BOUNDARY_FAILURES"
ENV_V2_STAGING_DEFAULT_MAX_MEDICAL_BOUNDARY_FAILURES = "RAG_V2_STAGING_DEFAULT_MAX_MEDICAL_BOUNDARY_FAILURES"
ENV_V2_STAGING_MAX_EXTERNAL_SOURCE_FAILURES = "RAG_V2_STAGING_MAX_EXTERNAL_SOURCE_FAILURES"
ENV_V2_STAGING_DEFAULT_MAX_EXTERNAL_SOURCE_FAILURES = "RAG_V2_STAGING_DEFAULT_MAX_EXTERNAL_SOURCE_FAILURES"
ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE = "RAG_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE"
ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE = "RAG_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE"
ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE = "RAG_V2_STAGING_PRIVACY_LOGGING_AVAILABLE"
ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE = "RAG_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE"
ENV_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH = "RAG_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH"
ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION = "RAG_ALLOW_V2_POST_CUTOVER_STABILIZATION"
ENV_ALLOW_V2_POST_STABILIZATION_OPERATIONS = "RAG_ALLOW_V2_POST_STABILIZATION_OPERATIONS"
ENV_V2_PRODUCTION_DEFAULT = "RAG_V2_PRODUCTION_DEFAULT"
ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION = "RAG_PRODUCTION_DEFAULT_RETRIEVAL_VERSION"
ENV_V2_PRODUCTION_DEFAULT_REQUIRE_MONITORS = "RAG_V2_PRODUCTION_DEFAULT_REQUIRE_MONITORS"
ENV_V2_PRODUCTION_TIMEOUT_MS = "RAG_V2_PRODUCTION_TIMEOUT_MS"
ENV_V2_PRODUCTION_CIRCUIT_BREAKER = "RAG_V2_PRODUCTION_CIRCUIT_BREAKER"
ENV_V2_PRODUCTION_MAX_ERROR_RATE = "RAG_V2_PRODUCTION_MAX_ERROR_RATE"
ENV_V2_PRODUCTION_MAX_TIMEOUT_RATE = "RAG_V2_PRODUCTION_MAX_TIMEOUT_RATE"
ENV_V2_PRODUCTION_MAX_BOUNDARY_FAILURES = "RAG_V2_PRODUCTION_MAX_BOUNDARY_FAILURES"
ENV_V2_PRODUCTION_MAX_SOURCE_CITATION_FAILURES = "RAG_V2_PRODUCTION_MAX_SOURCE_CITATION_FAILURES"
ENV_V2_PRODUCTION_MAX_MEDICAL_BOUNDARY_FAILURES = "RAG_V2_PRODUCTION_MAX_MEDICAL_BOUNDARY_FAILURES"
ENV_V2_PRODUCTION_MAX_EXTERNAL_SOURCE_FAILURES = "RAG_V2_PRODUCTION_MAX_EXTERNAL_SOURCE_FAILURES"
ENV_V2_PRODUCTION_MAX_PRIVACY_FAILURES = "RAG_V2_PRODUCTION_MAX_PRIVACY_FAILURES"
ENV_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE = "RAG_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE"
ENV_V2_PRODUCTION_SOURCE_CITATION_MONITOR_AVAILABLE = "RAG_V2_PRODUCTION_SOURCE_CITATION_MONITOR_AVAILABLE"
ENV_V2_PRODUCTION_PRIVACY_LOGGING_AVAILABLE = "RAG_V2_PRODUCTION_PRIVACY_LOGGING_AVAILABLE"
ENV_V2_PRODUCTION_TIMEOUT_MONITOR_AVAILABLE = "RAG_V2_PRODUCTION_TIMEOUT_MONITOR_AVAILABLE"
ENV_V2_FORCE_QUERY_IDS = "RAG_V2_FORCE_QUERY_IDS"
ENV_V2_FALLBACK_TO_V1 = "RAG_V2_FALLBACK_TO_V1"
ENV_V2_SHADOW_TIMEOUT_MS = "RAG_V2_SHADOW_TIMEOUT_MS"
ENV_V2_SHADOW_CIRCUIT_BREAKER = "RAG_V2_SHADOW_CIRCUIT_BREAKER"
ENV_V2_SHADOW_MAX_ERROR_RATE = "RAG_V2_SHADOW_MAX_ERROR_RATE"
ENV_V2_SHADOW_MAX_BOUNDARY_FAILURES = "RAG_V2_SHADOW_MAX_BOUNDARY_FAILURES"
ENV_FORCE_V1 = "RAG_FORCE_V1"
ENV_V2_MODEL_MANIFEST_PATH = "RAG_V2_MODEL_MANIFEST_PATH"
ENV_V2_SIMULATE_FAISS_UNAVAILABLE = "RAG_V2_SIMULATE_FAISS_UNAVAILABLE"

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"", "0", "false", "no", "off"}
CONTROLLED_STAGES = {"local_smoke", "controlled_rollout"}
PRODUCTION_SHADOW_STAGE = "production_shadow"
INTERNAL_SERVED_CANARY_STAGE = "internal_served_canary"
LIMITED_GENERAL_SERVED_CANARY_STAGE = "limited_general_served_canary"
STAGING_DEFAULT_SWITCH_STAGE = "staging_default_switch"
STAGING_DEFAULT_REHEARSAL_STAGE = "staging_default_rehearsal"
STAGING_DEFAULT_STAGES = {STAGING_DEFAULT_SWITCH_STAGE, STAGING_DEFAULT_REHEARSAL_STAGE}
PRODUCTION_DEFAULT_SWITCH_STAGE = "production"
PRODUCTION_BLOCKING_STAGES = {"prod", "production"}

LANE_TABLES = {
    "primary_safe": "lexical_primary_docs",
    "main_text_primary": "lexical_main_text_docs",
    "formula_text_primary": "lexical_formula_text_docs",
    "formula_usage_positive": "lexical_formula_usage_docs",
    "auxiliary_safe": "lexical_auxiliary_docs",
}

LANE_INDEX_NAMES = {
    "primary_safe": "primary_safe",
    "main_text_primary": "main_text_primary_lexical_only",
    "formula_text_primary": "formula_text_primary",
    "formula_usage_positive": "formula_usage_positive",
    "auxiliary_safe": "auxiliary_safe",
}

EXPECTED_PHASE31_COUNTS = {
    "primary_safe": 1161,
    "main_text_primary": 772,
    "formula_text_primary": 112,
    "formula_usage_positive": 273,
    "auxiliary_safe": 3600,
}

VARIANT_NORMALIZATION = {
    "干姜": "乾姜",
    "桃仁": "桃人",
}

BOUNDARY_REFUSAL_HINTS = {
    "高血压": "medical_advice",
    "新冠": "medical_advice",
    "现代疾病": "modern_disease_mapping",
    "现代中医名家": "external_professional_source",
    "外部百科": "external_source_request",
    "没有书内证据": "insufficient_evidence_forced_conclusion",
    "开一个": "medical_advice",
    "处方": "medical_advice",
    "立刻用": "medical_advice",
}

VARIANT_PROBE_TERMS = {
    "乾姜",
    "干姜",
    "麻子人",
    "麻子仁",
    "桃人",
    "桃仁",
    "杏人",
    "杏仁",
    "浓朴",
    "厚朴",
}


@dataclass(frozen=True)
class StagingDefaultPercentParse:
    raw_value: str | None
    percent: float
    valid: bool
    absent: bool
    full_default: bool
    reason: str = ""


@dataclass(frozen=True)
class RetrievalRouteConfig:
    requested_version: str = "v1"
    raw_requested_version: str | None = None
    requested_version_valid: bool = True
    v2_enabled_raw: str | None = None
    v2_enabled_false: bool = False
    allow_v2_controlled_rollout: bool = False
    allow_v2_production_shadow: bool = False
    runtime_stage: str = ""
    shadow_compare: bool = False
    canary_percent: int = 0
    production_shadow_percent: int = 0
    production_shadow_all: bool = False
    production_served_v2_percent: int = 0
    allow_v2_internal_served_canary: bool = False
    internal_served_percent: int = 0
    internal_allowlist_user_hashes: tuple[str, ...] = ()
    internal_allowlist_query_id_hashes: tuple[str, ...] = ()
    internal_allowlist_request_hashes: tuple[str, ...] = ()
    internal_canary_require_allowlist: bool = True
    internal_timeout_ms: int = 1500
    internal_circuit_breaker: bool = True
    internal_max_error_rate: float = 0.02
    internal_max_boundary_failures: int = 0
    allow_v2_limited_general_canary: bool = False
    general_served_percent: float = 0.0
    general_served_percent_raw: str | None = None
    general_served_percent_valid: bool = True
    general_served_percent_absent: bool = True
    general_served_percent_cap_violation: bool = False
    general_served_percent_negative: bool = False
    general_canary_max_percent: float = 1.0
    general_canary_require_monitors: bool = True
    general_canary_deterministic: bool = True
    general_timeout_ms: int = 1500
    general_circuit_breaker: bool = True
    general_max_error_rate: float = 0.01
    general_max_boundary_failures: int = 0
    general_max_source_citation_failures: int = 0
    general_max_medical_boundary_failures: int = 0
    general_max_external_source_failures: int = 0
    general_monitor_availability: CanaryMonitorAvailability = field(default_factory=CanaryMonitorAvailability)
    allow_v2_staging_default_switch: bool = False
    staging_default_requested: bool = False
    staging_default_version: str = "v1"
    staging_default_percent: float = 100.0
    staging_default_percent_raw: str | None = None
    staging_default_percent_valid: bool = True
    staging_default_percent_absent: bool = True
    staging_default_percent_full: bool = False
    staging_default_require_monitors: bool = True
    staging_timeout_ms: int = 1500
    staging_circuit_breaker: bool = True
    staging_max_error_rate: float = 0.01
    staging_max_timeout_rate: float = 0.02
    staging_max_boundary_failures: int = 0
    staging_max_source_citation_failures: int = 0
    staging_max_medical_boundary_failures: int = 0
    staging_max_external_source_failures: int = 0
    staging_monitor_availability: CanaryMonitorAvailability = field(default_factory=CanaryMonitorAvailability)
    staging_timeout_monitor_available: bool = True
    allow_v2_production_default_switch: bool = False
    allow_v2_post_cutover_stabilization: bool = False
    allow_v2_post_stabilization_operations: bool = False
    production_default_version: str = "v1"
    production_default_version_valid: bool = True
    production_default_require_monitors: bool = True
    production_timeout_ms: int = 1500
    production_circuit_breaker: bool = True
    production_max_error_rate: float = 0.01
    production_max_timeout_rate: float = 0.02
    production_max_boundary_failures: int = 0
    production_max_source_citation_failures: int = 0
    production_max_medical_boundary_failures: int = 0
    production_max_external_source_failures: int = 0
    production_max_privacy_failures: int = 0
    production_monitor_availability: CanaryMonitorAvailability = field(default_factory=CanaryMonitorAvailability)
    production_timeout_monitor_available: bool = False
    production_default_v2_requested: bool = False
    force_query_ids: tuple[str, ...] = ()
    fallback_to_v1: bool = True
    force_v1: bool = False
    shadow_timeout_ms: int = 750
    shadow_circuit_breaker: bool = True
    shadow_max_error_rate: float = 0.02
    shadow_max_boundary_failures: int = 0
    production_runtime_connected: bool = False
    frontend_started: bool = False
    v2_sidecar_db: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V2_SIDECAR_DB))
    v2_index_dir: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V2_INDEX_DIR))
    v1_db_path: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V1_DB_PATH))
    v1_dense_chunks_index: Path = field(
        default_factory=lambda: resolve_project_path(DEFAULT_V1_DENSE_CHUNKS_INDEX)
    )
    v1_dense_main_index: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V1_DENSE_MAIN_INDEX))
    v2_model_manifest_path: Path | None = None
    simulate_faiss_unavailable: bool = False
    v2_path_overrides: dict[str, Path] = field(default_factory=dict)
    flag_state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalRouteDecision:
    served_route: str
    shadow_route: str | None
    route_mode: str
    route_selection_reason: str
    runtime_stage: str
    flag_state: dict[str, Any]
    v2_allowed: bool
    v2_block_reason: str
    v2_block_reasons: tuple[str, ...]
    fallback_to_v1: bool
    canary_percent: int
    production_shadow_enabled: bool
    production_served_v2_percent: int
    production_shadow_percent: int
    production_shadow_all: bool
    shadow_sample_selected: bool
    shadow_timeout_ms: int
    shadow_circuit_breaker_open: bool
    internal_served_percent: int
    internal_allowlist_required: bool
    internal_allowlist_matched: bool
    allowlist_match_type: str
    canary_subject_hash: str
    served_to_internal_allowlist: bool
    served_to_general_production_user: bool
    internal_canary_selected: bool
    internal_timeout_ms: int
    internal_circuit_breaker_open: bool
    allow_v2_limited_general_canary: bool
    served_to_general_canary: bool
    general_canary_selected: bool
    general_canary_percent: float
    general_canary_max_percent: float
    general_canary_subject_hash: str
    canary_decision_hash: str
    canary_not_selected_reason: str
    general_timeout_ms: int
    general_circuit_breaker_open: bool
    general_monitors_required: bool
    general_monitors_available: bool
    boundary_monitor_available: bool
    source_citation_monitor_available: bool
    privacy_logging_available: bool
    allow_v2_staging_default_switch: bool
    staging_default_requested: bool
    staging_default_percent: float
    staging_default_percent_valid: bool
    staging_default_percent_full: bool
    staging_default_timeout_ms: int
    staging_default_circuit_breaker_open: bool
    staging_default_monitors_required: bool
    staging_default_monitors_available: bool
    staging_boundary_monitor_available: bool
    staging_source_citation_monitor_available: bool
    staging_privacy_logging_available: bool
    staging_timeout_monitor_available: bool
    allow_v2_production_default_switch: bool
    allow_v2_post_cutover_stabilization: bool
    allow_v2_post_stabilization_operations: bool
    production_default_version: str
    production_default_version_valid: bool
    production_default_timeout_ms: int
    production_default_circuit_breaker_open: bool
    production_default_monitors_required: bool
    production_default_monitors_available: bool
    production_boundary_monitor_available: bool
    production_source_citation_monitor_available: bool
    production_privacy_logging_available: bool
    production_timeout_monitor_available: bool
    production_default_v2_requested: bool
    production_runtime_connected: bool
    frontend_started: bool
    kill_switch_active: bool

    def metadata(self) -> dict[str, Any]:
        return {
            "served_route": self.served_route,
            "shadow_route": self.shadow_route,
            "route_mode": self.route_mode,
            "runtime_stage": self.runtime_stage,
            "flag_state": self.flag_state,
            "flag_state_sanitized": sanitize_flag_state(self.flag_state),
            "production_shadow_enabled": self.production_shadow_enabled,
            "production_served_v2_percent": self.production_served_v2_percent,
            "production_shadow_percent": self.production_shadow_percent,
            "production_shadow_all": self.production_shadow_all,
            "shadow_sample_selected": self.shadow_sample_selected,
            "shadow_timeout_ms": self.shadow_timeout_ms,
            "shadow_timed_out": False,
            "shadow_error": False,
            "shadow_error_reason": "",
            "shadow_circuit_breaker_open": self.shadow_circuit_breaker_open,
            "internal_served_percent": self.internal_served_percent,
            "internal_allowlist_required": self.internal_allowlist_required,
            "internal_allowlist_matched": self.internal_allowlist_matched,
            "allowlist_match_type": self.allowlist_match_type,
            "canary_subject_hash": self.canary_subject_hash,
            "served_to_internal_allowlist": self.served_to_internal_allowlist,
            "served_to_general_production_user": self.served_to_general_production_user,
            "internal_canary_selected": self.internal_canary_selected,
            "internal_timeout_ms": self.internal_timeout_ms,
            "internal_timed_out": False,
            "internal_error": False,
            "internal_error_reason": "",
            "internal_circuit_breaker_open": self.internal_circuit_breaker_open,
            "allow_v2_limited_general_canary": self.allow_v2_limited_general_canary,
            "served_to_general_canary": self.served_to_general_canary,
            "general_canary_selected": self.general_canary_selected,
            "v2_general_canary_percent": self.general_canary_percent,
            "general_canary_max_percent": self.general_canary_max_percent,
            "canary_decision_hash": self.canary_decision_hash,
            "canary_not_selected_reason": self.canary_not_selected_reason,
            "general_timeout_ms": self.general_timeout_ms,
            "general_timed_out": False,
            "general_error": False,
            "general_error_reason": "",
            "general_circuit_breaker_open": self.general_circuit_breaker_open,
            "general_monitors_required": self.general_monitors_required,
            "general_monitors_available": self.general_monitors_available,
            "boundary_monitor_available": self.boundary_monitor_available,
            "source_citation_monitor_available": self.source_citation_monitor_available,
            "privacy_logging_available": self.privacy_logging_available,
            "allow_v2_staging_default_switch": self.allow_v2_staging_default_switch,
            "staging_default_requested": self.staging_default_requested,
            "staging_default_percent": self.staging_default_percent,
            "staging_default_percent_valid": self.staging_default_percent_valid,
            "staging_default_percent_full": self.staging_default_percent_full,
            "staging_default_active": self.served_route == "v2" and self.route_mode == "staging_default_switch",
            "production_default_active": self.served_route == "v2" and self.route_mode == "production_default_switch",
            "production_default_v2_requested": self.production_default_v2_requested,
            "staging_default_timeout_ms": self.staging_default_timeout_ms,
            "staging_default_timed_out": False,
            "staging_default_error": False,
            "staging_default_error_reason": "",
            "staging_default_circuit_breaker_open": self.staging_default_circuit_breaker_open,
            "staging_default_monitors_required": self.staging_default_monitors_required,
            "staging_default_monitors_available": self.staging_default_monitors_available,
            "staging_boundary_monitor_available": self.staging_boundary_monitor_available,
            "staging_source_citation_monitor_available": self.staging_source_citation_monitor_available,
            "staging_privacy_logging_available": self.staging_privacy_logging_available,
            "staging_timeout_monitor_available": self.staging_timeout_monitor_available,
            "latency_v2_staging_ms": None,
            "allow_v2_production_default_switch": self.allow_v2_production_default_switch,
            "allow_v2_post_cutover_stabilization": self.allow_v2_post_cutover_stabilization,
            "allow_v2_post_stabilization_operations": self.allow_v2_post_stabilization_operations,
            "production_default_version": self.production_default_version,
            "production_default_version_valid": self.production_default_version_valid,
            "production_default_timeout_ms": self.production_default_timeout_ms,
            "production_default_timed_out": False,
            "production_default_error": False,
            "production_default_error_reason": "",
            "production_default_circuit_breaker_open": self.production_default_circuit_breaker_open,
            "production_default_monitors_required": self.production_default_monitors_required,
            "production_default_monitors_available": self.production_default_monitors_available,
            "production_boundary_monitor_available": self.production_boundary_monitor_available,
            "production_source_citation_monitor_available": self.production_source_citation_monitor_available,
            "production_privacy_logging_available": self.production_privacy_logging_available,
            "production_timeout_monitor_available": self.production_timeout_monitor_available,
            "latency_v2_production_ms": None,
            "latency_v2_served_ms": None,
            "fallback_used": False,
            "fallback_reason": "",
            "v2_allowed": self.v2_allowed,
            "v2_block_reason": self.v2_block_reason,
            "v2_block_reasons": list(self.v2_block_reasons),
            "evidence_scope": "primary_default_no_auxiliary_merge",
            "retrieval_scope": self.route_mode,
            "source_route": self.served_route,
            "selected_served_route": self.served_route,
            "shadow_route_executed": False,
            "v2_served_route_executed": self.served_route == "v2",
            "v2_served_to_user": self.served_route == "v2",
            "v2_served_to_general_user": self.served_route == "v2" and self.served_to_general_canary,
            "v2_block_reason": self.v2_block_reason,
            "general_user_v1_preserved": self.served_route == "v1" and not self.served_to_internal_allowlist,
            "route_selection_reason": self.route_selection_reason,
            "production_runtime_connected": self.production_runtime_connected,
            "frontend_started": self.frontend_started,
            "kill_switch_active": self.kill_switch_active,
        }


def route_config_from_env(
    env: Mapping[str, str] | None = None,
    *,
    v2_sidecar_db: str | Path = DEFAULT_V2_SIDECAR_DB,
    v2_index_dir: str | Path = DEFAULT_V2_INDEX_DIR,
    v1_db_path: str | Path = DEFAULT_V1_DB_PATH,
    v2_path_overrides: Mapping[str, str | Path] | None = None,
    production_runtime_connected: bool = False,
    frontend_started: bool = False,
) -> RetrievalRouteConfig:
    values = dict(os.environ if env is None else env)
    raw_version = values.get(ENV_RETRIEVAL_VERSION)
    raw_enabled = values.get(ENV_V2_ENABLED)
    version_value = _clean_flag(raw_version)
    enabled_value = _clean_flag(raw_enabled)

    requested_version = "v1"
    requested_version_valid = True
    if raw_version is not None:
        if version_value in {"", "v1", "1", "false", "no", "off", "0"}:
            requested_version = "v1"
        elif version_value in {"v2", "2", "true", "yes", "on"}:
            requested_version = "v2"
        elif version_value == "shadow":
            requested_version = "shadow"
        else:
            requested_version = "v1"
            requested_version_valid = False
    elif enabled_value in TRUE_VALUES or enabled_value in {"v2", "2"}:
        requested_version = "v2"

    v2_enabled_false = raw_enabled is not None and enabled_value in FALSE_VALUES
    canary_percent = _parse_canary_percent(values.get(ENV_V2_CANARY_PERCENT))
    production_shadow_percent = _parse_canary_percent(values.get(ENV_V2_PROD_SHADOW_PERCENT))
    production_served_v2_percent = _parse_canary_percent(values.get(ENV_V2_PRODUCTION_SERVED_PERCENT))
    internal_served_percent = _parse_canary_percent(values.get(ENV_V2_INTERNAL_SERVED_PERCENT))
    general_canary_max_percent = min(
        1.0,
        _parse_float(values.get(ENV_V2_GENERAL_CANARY_MAX_PERCENT), default=1.0),
    )
    general_percent = parse_general_served_percent(
        values.get(ENV_V2_GENERAL_SERVED_PERCENT),
        max_percent=general_canary_max_percent,
    )
    staging_percent = parse_staging_default_percent(values.get(ENV_V2_STAGING_DEFAULT_PERCENT))
    staging_default_version_raw = values.get(ENV_STAGING_DEFAULT_RETRIEVAL_VERSION)
    staging_default_version = "v2" if _clean_flag(staging_default_version_raw) in {"v2", "2"} else "v1"
    staging_default_requested = (
        _truthy(values.get(ENV_V2_STAGING_DEFAULT))
        or staging_default_version == "v2"
    )
    production_default_version_raw = values.get(ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION)
    production_default_version_clean = _clean_flag(production_default_version_raw)
    production_default_version_valid = True
    if production_default_version_clean in {"", "v1", "1", "false", "no", "off", "0"}:
        production_default_version = "v1"
    elif production_default_version_clean in {"v2", "2", "true", "yes", "on"}:
        production_default_version = "v2"
    else:
        production_default_version = "v1"
        production_default_version_valid = False
    production_default_v2_requested = (
        production_default_version == "v2"
        or (production_default_version_raw is None and _truthy(values.get(ENV_V2_PRODUCTION_DEFAULT)))
    )
    force_query_ids = tuple(
        item.strip()
        for item in str(values.get(ENV_V2_FORCE_QUERY_IDS) or "").split(",")
        if item.strip()
    )
    manifest_value = values.get(ENV_V2_MODEL_MANIFEST_PATH)
    manifest_path = resolve_project_path(manifest_value) if manifest_value else None
    overrides = {
        key: resolve_project_path(path_value)
        for key, path_value in dict(v2_path_overrides or {}).items()
    }
    flag_state = {
        key: values.get(key)
        for key in [
            ENV_RETRIEVAL_VERSION,
            ENV_V2_ENABLED,
            ENV_ALLOW_V2_CONTROLLED_ROLLOUT,
            ENV_ALLOW_V2_PRODUCTION_SHADOW,
            ENV_RUNTIME_STAGE,
            ENV_V2_SHADOW_COMPARE,
            ENV_V2_CANARY_PERCENT,
            ENV_V2_PROD_SHADOW_PERCENT,
            ENV_V2_PROD_SHADOW_ALL,
            ENV_V2_PRODUCTION_SERVED_PERCENT,
            ENV_ALLOW_V2_INTERNAL_SERVED_CANARY,
            ENV_V2_INTERNAL_SERVED_PERCENT,
            ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES,
            ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS,
            ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES,
            ENV_V2_INTERNAL_CANARY_REQUIRE_ALLOWLIST,
            ENV_V2_INTERNAL_MAX_ERROR_RATE,
            ENV_V2_INTERNAL_MAX_BOUNDARY_FAILURES,
            ENV_V2_INTERNAL_TIMEOUT_MS,
            ENV_V2_INTERNAL_CIRCUIT_BREAKER,
            ENV_ALLOW_V2_LIMITED_GENERAL_CANARY,
            ENV_V2_GENERAL_SERVED_PERCENT,
            ENV_V2_GENERAL_CANARY_MAX_PERCENT,
            ENV_V2_GENERAL_CANARY_REQUIRE_MONITORS,
            ENV_V2_GENERAL_CANARY_DETERMINISTIC,
            ENV_V2_GENERAL_TIMEOUT_MS,
            ENV_V2_GENERAL_CIRCUIT_BREAKER,
            ENV_V2_GENERAL_MAX_ERROR_RATE,
            ENV_V2_GENERAL_MAX_BOUNDARY_FAILURES,
            ENV_V2_GENERAL_MAX_SOURCE_CITATION_FAILURES,
            ENV_V2_GENERAL_MAX_MEDICAL_BOUNDARY_FAILURES,
            ENV_V2_GENERAL_MAX_EXTERNAL_SOURCE_FAILURES,
            ENV_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE,
            ENV_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE,
            ENV_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE,
            ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH,
            ENV_ALLOW_V2_STAGING_DEFAULT,
            ENV_STAGING_DEFAULT_RETRIEVAL_VERSION,
            ENV_V2_STAGING_DEFAULT,
            ENV_V2_STAGING_DEFAULT_REQUIRE_MONITORS,
            ENV_V2_STAGING_DEFAULT_PERCENT,
            ENV_V2_STAGING_TIMEOUT_MS,
            ENV_V2_STAGING_DEFAULT_TIMEOUT_MS,
            ENV_V2_STAGING_CIRCUIT_BREAKER,
            ENV_V2_STAGING_DEFAULT_CIRCUIT_BREAKER,
            ENV_V2_STAGING_MAX_ERROR_RATE,
            ENV_V2_STAGING_DEFAULT_MAX_ERROR_RATE,
            ENV_V2_STAGING_MAX_TIMEOUT_RATE,
            ENV_V2_STAGING_DEFAULT_MAX_TIMEOUT_RATE,
            ENV_V2_STAGING_MAX_BOUNDARY_FAILURES,
            ENV_V2_STAGING_DEFAULT_MAX_BOUNDARY_FAILURES,
            ENV_V2_STAGING_MAX_SOURCE_CITATION_FAILURES,
            ENV_V2_STAGING_DEFAULT_MAX_SOURCE_CITATION_FAILURES,
            ENV_V2_STAGING_MAX_MEDICAL_BOUNDARY_FAILURES,
            ENV_V2_STAGING_DEFAULT_MAX_MEDICAL_BOUNDARY_FAILURES,
            ENV_V2_STAGING_MAX_EXTERNAL_SOURCE_FAILURES,
            ENV_V2_STAGING_DEFAULT_MAX_EXTERNAL_SOURCE_FAILURES,
            ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE,
            ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE,
            ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE,
            ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE,
            ENV_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH,
            ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION,
            ENV_ALLOW_V2_POST_STABILIZATION_OPERATIONS,
            ENV_V2_PRODUCTION_DEFAULT,
            ENV_PRODUCTION_DEFAULT_RETRIEVAL_VERSION,
            ENV_V2_PRODUCTION_DEFAULT_REQUIRE_MONITORS,
            ENV_V2_PRODUCTION_TIMEOUT_MS,
            ENV_V2_PRODUCTION_CIRCUIT_BREAKER,
            ENV_V2_PRODUCTION_MAX_ERROR_RATE,
            ENV_V2_PRODUCTION_MAX_TIMEOUT_RATE,
            ENV_V2_PRODUCTION_MAX_BOUNDARY_FAILURES,
            ENV_V2_PRODUCTION_MAX_SOURCE_CITATION_FAILURES,
            ENV_V2_PRODUCTION_MAX_MEDICAL_BOUNDARY_FAILURES,
            ENV_V2_PRODUCTION_MAX_EXTERNAL_SOURCE_FAILURES,
            ENV_V2_PRODUCTION_MAX_PRIVACY_FAILURES,
            ENV_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE,
            ENV_V2_PRODUCTION_SOURCE_CITATION_MONITOR_AVAILABLE,
            ENV_V2_PRODUCTION_PRIVACY_LOGGING_AVAILABLE,
            ENV_V2_PRODUCTION_TIMEOUT_MONITOR_AVAILABLE,
            ENV_V2_FORCE_QUERY_IDS,
            ENV_V2_FALLBACK_TO_V1,
            ENV_V2_SHADOW_TIMEOUT_MS,
            ENV_V2_SHADOW_CIRCUIT_BREAKER,
            ENV_V2_SHADOW_MAX_ERROR_RATE,
            ENV_V2_SHADOW_MAX_BOUNDARY_FAILURES,
            ENV_FORCE_V1,
            ENV_V2_MODEL_MANIFEST_PATH,
            ENV_V2_SIMULATE_FAISS_UNAVAILABLE,
        ]
        if values.get(key) is not None
    }
    return RetrievalRouteConfig(
        requested_version=requested_version,
        raw_requested_version=raw_version,
        requested_version_valid=requested_version_valid,
        v2_enabled_raw=raw_enabled,
        v2_enabled_false=v2_enabled_false,
        allow_v2_controlled_rollout=_truthy(values.get(ENV_ALLOW_V2_CONTROLLED_ROLLOUT)),
        allow_v2_production_shadow=_truthy(values.get(ENV_ALLOW_V2_PRODUCTION_SHADOW)),
        runtime_stage=str(values.get(ENV_RUNTIME_STAGE) or "").strip(),
        shadow_compare=_truthy(values.get(ENV_V2_SHADOW_COMPARE)),
        canary_percent=canary_percent,
        production_shadow_percent=production_shadow_percent,
        production_shadow_all=_truthy(values.get(ENV_V2_PROD_SHADOW_ALL)),
        production_served_v2_percent=production_served_v2_percent,
        allow_v2_internal_served_canary=_truthy(values.get(ENV_ALLOW_V2_INTERNAL_SERVED_CANARY)),
        internal_served_percent=internal_served_percent,
        internal_allowlist_user_hashes=parse_allowlist_hashes(values.get(ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES)),
        internal_allowlist_query_id_hashes=parse_allowlist_hashes(values.get(ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS)),
        internal_allowlist_request_hashes=parse_allowlist_hashes(values.get(ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES)),
        internal_canary_require_allowlist=not _falsey(
            values.get(ENV_V2_INTERNAL_CANARY_REQUIRE_ALLOWLIST), default=False
        ),
        internal_timeout_ms=_parse_positive_int(values.get(ENV_V2_INTERNAL_TIMEOUT_MS), default=1500),
        internal_circuit_breaker=not _falsey(values.get(ENV_V2_INTERNAL_CIRCUIT_BREAKER), default=False),
        internal_max_error_rate=_parse_float(values.get(ENV_V2_INTERNAL_MAX_ERROR_RATE), default=0.02),
        internal_max_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_INTERNAL_MAX_BOUNDARY_FAILURES), default=0
        ),
        allow_v2_limited_general_canary=_truthy(values.get(ENV_ALLOW_V2_LIMITED_GENERAL_CANARY)),
        general_served_percent=general_percent.percent,
        general_served_percent_raw=general_percent.raw_value,
        general_served_percent_valid=general_percent.valid,
        general_served_percent_absent=general_percent.absent,
        general_served_percent_cap_violation=general_percent.cap_violation,
        general_served_percent_negative=general_percent.negative,
        general_canary_max_percent=general_canary_max_percent,
        general_canary_require_monitors=not _falsey(
            values.get(ENV_V2_GENERAL_CANARY_REQUIRE_MONITORS), default=False
        ),
        general_canary_deterministic=not _falsey(
            values.get(ENV_V2_GENERAL_CANARY_DETERMINISTIC), default=False
        ),
        general_timeout_ms=_parse_positive_int(values.get(ENV_V2_GENERAL_TIMEOUT_MS), default=1500),
        general_circuit_breaker=not _falsey(values.get(ENV_V2_GENERAL_CIRCUIT_BREAKER), default=False),
        general_max_error_rate=_parse_float(values.get(ENV_V2_GENERAL_MAX_ERROR_RATE), default=0.01),
        general_max_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_GENERAL_MAX_BOUNDARY_FAILURES), default=0
        ),
        general_max_source_citation_failures=_parse_nonnegative_int(
            values.get(ENV_V2_GENERAL_MAX_SOURCE_CITATION_FAILURES), default=0
        ),
        general_max_medical_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_GENERAL_MAX_MEDICAL_BOUNDARY_FAILURES), default=0
        ),
        general_max_external_source_failures=_parse_nonnegative_int(
            values.get(ENV_V2_GENERAL_MAX_EXTERNAL_SOURCE_FAILURES), default=0
        ),
        general_monitor_availability=CanaryMonitorAvailability(
            boundary_monitor_available=not _falsey(
                values.get(ENV_V2_GENERAL_BOUNDARY_MONITOR_AVAILABLE), default=False
            ),
            source_citation_monitor_available=not _falsey(
                values.get(ENV_V2_GENERAL_SOURCE_CITATION_MONITOR_AVAILABLE), default=False
            ),
            privacy_logging_available=not _falsey(
                values.get(ENV_V2_GENERAL_PRIVACY_LOGGING_AVAILABLE), default=False
            ),
        ),
        allow_v2_staging_default_switch=(
            _truthy(values.get(ENV_ALLOW_V2_STAGING_DEFAULT_SWITCH))
            or _truthy(values.get(ENV_ALLOW_V2_STAGING_DEFAULT))
        ),
        staging_default_requested=staging_default_requested,
        staging_default_version=staging_default_version,
        staging_default_percent=staging_percent.percent,
        staging_default_percent_raw=staging_percent.raw_value,
        staging_default_percent_valid=staging_percent.valid,
        staging_default_percent_absent=staging_percent.absent,
        staging_default_percent_full=staging_percent.full_default,
        staging_default_require_monitors=not _falsey(
            values.get(ENV_V2_STAGING_DEFAULT_REQUIRE_MONITORS), default=False
        ),
        staging_timeout_ms=_parse_positive_int(
            values.get(ENV_V2_STAGING_TIMEOUT_MS) or values.get(ENV_V2_STAGING_DEFAULT_TIMEOUT_MS),
            default=1500,
        ),
        staging_circuit_breaker=not _falsey(
            values.get(ENV_V2_STAGING_CIRCUIT_BREAKER) or values.get(ENV_V2_STAGING_DEFAULT_CIRCUIT_BREAKER),
            default=False,
        ),
        staging_max_error_rate=_parse_float(
            values.get(ENV_V2_STAGING_MAX_ERROR_RATE) or values.get(ENV_V2_STAGING_DEFAULT_MAX_ERROR_RATE),
            default=0.01,
        ),
        staging_max_timeout_rate=_parse_float(
            values.get(ENV_V2_STAGING_MAX_TIMEOUT_RATE) or values.get(ENV_V2_STAGING_DEFAULT_MAX_TIMEOUT_RATE),
            default=0.02,
        ),
        staging_max_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_STAGING_MAX_BOUNDARY_FAILURES) or values.get(ENV_V2_STAGING_DEFAULT_MAX_BOUNDARY_FAILURES),
            default=0,
        ),
        staging_max_source_citation_failures=_parse_nonnegative_int(
            values.get(ENV_V2_STAGING_MAX_SOURCE_CITATION_FAILURES)
            or values.get(ENV_V2_STAGING_DEFAULT_MAX_SOURCE_CITATION_FAILURES),
            default=0,
        ),
        staging_max_medical_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_STAGING_MAX_MEDICAL_BOUNDARY_FAILURES)
            or values.get(ENV_V2_STAGING_DEFAULT_MAX_MEDICAL_BOUNDARY_FAILURES),
            default=0,
        ),
        staging_max_external_source_failures=_parse_nonnegative_int(
            values.get(ENV_V2_STAGING_MAX_EXTERNAL_SOURCE_FAILURES)
            or values.get(ENV_V2_STAGING_DEFAULT_MAX_EXTERNAL_SOURCE_FAILURES),
            default=0,
        ),
        staging_monitor_availability=CanaryMonitorAvailability(
            boundary_monitor_available=not _falsey(
                values.get(ENV_V2_STAGING_BOUNDARY_MONITOR_AVAILABLE), default=False
            ),
            source_citation_monitor_available=not _falsey(
                values.get(ENV_V2_STAGING_SOURCE_CITATION_MONITOR_AVAILABLE), default=False
            ),
            privacy_logging_available=not _falsey(
                values.get(ENV_V2_STAGING_PRIVACY_LOGGING_AVAILABLE), default=False
            ),
        ),
        staging_timeout_monitor_available=not _falsey(
            values.get(ENV_V2_STAGING_TIMEOUT_MONITOR_AVAILABLE), default=False
        ),
        allow_v2_production_default_switch=_truthy(values.get(ENV_ALLOW_V2_PRODUCTION_DEFAULT_SWITCH)),
        allow_v2_post_stabilization_operations=_truthy(
            values.get(ENV_ALLOW_V2_POST_STABILIZATION_OPERATIONS)
        ),
        production_default_version=production_default_version,
        production_default_version_valid=production_default_version_valid,
        production_default_require_monitors=not _falsey(
            values.get(ENV_V2_PRODUCTION_DEFAULT_REQUIRE_MONITORS), default=False
        ),
        production_timeout_ms=_parse_positive_int(values.get(ENV_V2_PRODUCTION_TIMEOUT_MS), default=1500),
        production_circuit_breaker=not _falsey(values.get(ENV_V2_PRODUCTION_CIRCUIT_BREAKER), default=False),
        production_max_error_rate=_parse_float(values.get(ENV_V2_PRODUCTION_MAX_ERROR_RATE), default=0.01),
        production_max_timeout_rate=_parse_float(values.get(ENV_V2_PRODUCTION_MAX_TIMEOUT_RATE), default=0.02),
        production_max_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_PRODUCTION_MAX_BOUNDARY_FAILURES), default=0
        ),
        production_max_source_citation_failures=_parse_nonnegative_int(
            values.get(ENV_V2_PRODUCTION_MAX_SOURCE_CITATION_FAILURES), default=0
        ),
        production_max_medical_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_PRODUCTION_MAX_MEDICAL_BOUNDARY_FAILURES), default=0
        ),
        production_max_external_source_failures=_parse_nonnegative_int(
            values.get(ENV_V2_PRODUCTION_MAX_EXTERNAL_SOURCE_FAILURES), default=0
        ),
        production_max_privacy_failures=_parse_nonnegative_int(
            values.get(ENV_V2_PRODUCTION_MAX_PRIVACY_FAILURES), default=0
        ),
        production_monitor_availability=CanaryMonitorAvailability(
            boundary_monitor_available=not _falsey(
                values.get(ENV_V2_PRODUCTION_BOUNDARY_MONITOR_AVAILABLE), default=False
            ),
            source_citation_monitor_available=not _falsey(
                values.get(ENV_V2_PRODUCTION_SOURCE_CITATION_MONITOR_AVAILABLE), default=False
            ),
            privacy_logging_available=not _falsey(
                values.get(ENV_V2_PRODUCTION_PRIVACY_LOGGING_AVAILABLE), default=False
            ),
        ),
        production_timeout_monitor_available=not _falsey(
            values.get(ENV_V2_PRODUCTION_TIMEOUT_MONITOR_AVAILABLE), default=False
        ),
        allow_v2_post_cutover_stabilization=_truthy(values.get(ENV_ALLOW_V2_POST_CUTOVER_STABILIZATION)),
        production_default_v2_requested=production_default_v2_requested,
        force_query_ids=force_query_ids,
        fallback_to_v1=not _falsey(values.get(ENV_V2_FALLBACK_TO_V1), default=False),
        force_v1=_truthy(values.get(ENV_FORCE_V1)),
        shadow_timeout_ms=_parse_positive_int(values.get(ENV_V2_SHADOW_TIMEOUT_MS), default=750),
        shadow_circuit_breaker=not _falsey(values.get(ENV_V2_SHADOW_CIRCUIT_BREAKER), default=False),
        shadow_max_error_rate=_parse_float(values.get(ENV_V2_SHADOW_MAX_ERROR_RATE), default=0.02),
        shadow_max_boundary_failures=_parse_nonnegative_int(
            values.get(ENV_V2_SHADOW_MAX_BOUNDARY_FAILURES), default=0
        ),
        production_runtime_connected=production_runtime_connected,
        frontend_started=frontend_started,
        v2_sidecar_db=resolve_project_path(v2_sidecar_db),
        v2_index_dir=resolve_project_path(v2_index_dir),
        v1_db_path=resolve_project_path(v1_db_path),
        v2_model_manifest_path=manifest_path,
        simulate_faiss_unavailable=_truthy(values.get(ENV_V2_SIMULATE_FAISS_UNAVAILABLE)),
        v2_path_overrides=overrides,
        flag_state=flag_state,
    )


def select_retrieval_route(
    config: RetrievalRouteConfig,
    *,
    query_id: str | None = None,
    internal_canary_identity: InternalCanaryIdentity | Mapping[str, Any] | None = None,
    general_canary_identity: GeneralCanaryIdentity | Mapping[str, Any] | None = None,
) -> RetrievalRouteDecision:
    stage_allowed = config.runtime_stage in CONTROLLED_STAGES
    production_shadow_stage = config.runtime_stage == PRODUCTION_SHADOW_STAGE
    internal_served_stage = config.runtime_stage == INTERNAL_SERVED_CANARY_STAGE
    limited_general_stage = config.runtime_stage == LIMITED_GENERAL_SERVED_CANARY_STAGE
    staging_default_stage = config.runtime_stage in STAGING_DEFAULT_STAGES
    production_default_stage = config.runtime_stage == PRODUCTION_DEFAULT_SWITCH_STAGE
    identity = coerce_identity(internal_canary_identity)
    general_identity = coerce_general_identity(general_canary_identity)
    allowlist_match = match_internal_allowlist(
        identity,
        user_hashes=config.internal_allowlist_user_hashes,
        request_hashes=config.internal_allowlist_request_hashes,
        query_id_hashes=config.internal_allowlist_query_id_hashes,
    )
    production_blocked = (
        config.production_runtime_connected
        or config.runtime_stage in PRODUCTION_BLOCKING_STAGES
        or production_shadow_stage
    )
    served_percent_violation = config.production_served_v2_percent > 0
    v2_allowed = (
        config.allow_v2_controlled_rollout
        and stage_allowed
        and not production_blocked
        and not served_percent_violation
        and not config.force_v1
    )
    production_shadow_allowed = (
        production_shadow_stage
        and config.allow_v2_production_shadow
        and config.shadow_compare
        and not served_percent_violation
        and not config.force_v1
    )
    internal_canary_prereqs_met = (
        internal_served_stage
        and config.allow_v2_internal_served_canary
        and not served_percent_violation
        and not config.force_v1
        and config.internal_served_percent > 0
        and (allowlist_match.matched or not config.internal_canary_require_allowlist)
    )
    internal_canary_subject_hash = allowlist_match.subject_hash or identity.internal_request_hash or identity.internal_query_id_hash
    internal_canary_selected = (
        internal_canary_prereqs_met
        and _canary_selected(internal_canary_subject_hash or query_id or "", config.internal_served_percent)
    )
    general_subject_hash = select_general_subject_hash(general_identity, query_id=query_id)
    general_decision_hash = general_canary_decision_hash(general_subject_hash, config.general_served_percent)
    general_circuit_open = False
    general_circuit_reason = ""
    if limited_general_stage:
        from backend.retrieval.limited_general_canary_metrics import is_limited_general_canary_circuit_open

        general_circuit_open, general_circuit_reason = is_limited_general_canary_circuit_open(config)
    staging_circuit_open = False
    staging_circuit_reason = ""
    if staging_default_stage:
        from backend.retrieval.staging_default_metrics import is_staging_default_circuit_open

        staging_circuit_open, staging_circuit_reason = is_staging_default_circuit_open(config)
    production_circuit_open = False
    production_circuit_reason = ""
    if production_default_stage:
        from backend.retrieval.production_default_metrics import is_production_default_circuit_open

        production_circuit_open, production_circuit_reason = is_production_default_circuit_open(config)
    general_monitor_reasons = config.general_monitor_availability.missing_reasons()
    general_monitors_pass = (
        not config.general_canary_require_monitors
        or config.general_monitor_availability.all_available
    )
    staging_monitor_reasons = config.staging_monitor_availability.missing_reasons()
    if not config.staging_timeout_monitor_available:
        staging_monitor_reasons.append("timeout_monitor_unavailable")
    staging_monitors_pass = (
        not config.staging_default_require_monitors
        or (config.staging_monitor_availability.all_available and config.staging_timeout_monitor_available)
    )
    production_monitor_reasons = config.production_monitor_availability.missing_reasons()
    if not config.production_timeout_monitor_available:
        production_monitor_reasons.append("timeout_monitor_unavailable")
    production_monitors_pass = (
        not config.production_default_require_monitors
        or (config.production_monitor_availability.all_available and config.production_timeout_monitor_available)
    )
    general_canary_prereqs_met = (
        limited_general_stage
        and config.allow_v2_limited_general_canary
        and not config.force_v1
        and not served_percent_violation
        and config.general_served_percent_valid
        and not config.general_served_percent_cap_violation
        and config.general_served_percent > 0
        and config.general_served_percent <= config.general_canary_max_percent
        and config.general_canary_deterministic
        and general_monitors_pass
        and not general_circuit_open
    )
    general_canary_is_selected = (
        general_canary_prereqs_met
        and general_canary_selected(general_subject_hash, config.general_served_percent)
    )
    staging_default_prereqs_met = (
        staging_default_stage
        and config.allow_v2_staging_default_switch
        and config.staging_default_requested
        and config.requested_version == "v2"
        and not config.force_v1
        and not served_percent_violation
        and not config.production_default_v2_requested
        and config.staging_default_percent_valid
        and config.staging_default_percent_full
        and staging_monitors_pass
        and not staging_circuit_open
    )
    production_default_prereqs_met = (
        production_default_stage
        and config.allow_v2_production_default_switch
        and config.allow_v2_post_cutover_stabilization
        and config.allow_v2_post_stabilization_operations
        and config.production_default_v2_requested
        and config.production_default_version == "v2"
        and config.production_default_version_valid
        and not config.force_v1
        and not served_percent_violation
        and production_monitors_pass
        and not production_circuit_open
    )
    v2_block_reasons: list[str] = []
    if config.force_v1:
        v2_block_reasons.append("force_v1_kill_switch_active")
    if served_percent_violation:
        v2_block_reasons.append("production_served_v2_percent_must_remain_0")
    if not config.production_default_version_valid:
        v2_block_reasons.append("production_default_retrieval_version_invalid")
    if config.production_default_v2_requested:
        if not production_default_stage:
            v2_block_reasons.append("production_default_requires_runtime_stage_production")
        if not config.allow_v2_production_default_switch:
            v2_block_reasons.append("missing_production_default_switch_allowance")
        if not config.allow_v2_post_cutover_stabilization:
            v2_block_reasons.append("missing_post_cutover_stabilization_allowance")
        if not config.allow_v2_post_stabilization_operations:
            v2_block_reasons.append("missing_post_stabilization_operations_allowance")
        if config.production_default_version != "v2":
            v2_block_reasons.append("production_default_retrieval_version_not_v2")
        if config.production_default_require_monitors and not production_monitors_pass:
            v2_block_reasons.extend(production_monitor_reasons or ["production_default_monitor_unavailable"])
        if production_circuit_open:
            v2_block_reasons.append(production_circuit_reason or "production_default_circuit_breaker_open")
    if production_shadow_stage:
        v2_block_reasons.append("production_shadow_blocks_served_v2")
    elif production_blocked and not internal_served_stage and not limited_general_stage and not staging_default_stage and not production_default_stage:
        v2_block_reasons.append("production_runtime_or_stage_blocks_v2")
    if internal_served_stage:
        if not config.allow_v2_internal_served_canary:
            v2_block_reasons.append("missing_internal_served_canary_allowance")
        if config.internal_canary_require_allowlist and not allowlist_match.matched:
            v2_block_reasons.append("missing_internal_allowlist_match")
        if config.internal_served_percent <= 0:
            v2_block_reasons.append("internal_served_percent_must_be_gt_0")
    if limited_general_stage:
        if not config.allow_v2_limited_general_canary:
            v2_block_reasons.append("missing_limited_general_canary_allowance")
        if not config.general_served_percent_valid:
            v2_block_reasons.append("general_served_percent_invalid")
        if config.general_served_percent_negative:
            v2_block_reasons.append("general_served_percent_negative")
        if config.general_served_percent_cap_violation or config.general_served_percent > config.general_canary_max_percent:
            v2_block_reasons.append("general_served_percent_exceeds_cap")
        if config.general_served_percent <= 0:
            v2_block_reasons.append("general_served_percent_must_be_gt_0")
        if not config.general_canary_deterministic:
            v2_block_reasons.append("general_canary_deterministic_required")
        if config.general_canary_require_monitors and not config.general_monitor_availability.all_available:
            v2_block_reasons.extend(general_monitor_reasons or ["general_canary_monitor_unavailable"])
        if general_circuit_open:
            v2_block_reasons.append(general_circuit_reason or "general_circuit_breaker_open")
    if staging_default_stage:
        if not config.allow_v2_staging_default_switch:
            v2_block_reasons.append("missing_staging_default_switch_allowance")
        if not config.staging_default_requested:
            v2_block_reasons.append("staging_default_flag_not_enabled")
        if config.staging_default_version == "v1" and not _truthy(config.flag_state.get(ENV_V2_STAGING_DEFAULT)):
            v2_block_reasons.append("staging_default_retrieval_version_not_v2")
        if not config.staging_default_percent_valid:
            v2_block_reasons.append("staging_default_percent_invalid")
        elif not config.staging_default_percent_full:
            v2_block_reasons.append("staging_default_percent_must_be_100")
        if config.staging_default_require_monitors and not staging_monitors_pass:
            v2_block_reasons.extend(staging_monitor_reasons or ["staging_default_monitor_unavailable"])
        if staging_circuit_open:
            v2_block_reasons.append(staging_circuit_reason or "staging_default_circuit_breaker_open")
    if not config.allow_v2_controlled_rollout and not production_shadow_stage and not internal_served_stage and not staging_default_stage and not production_default_stage:
        v2_block_reasons.append("missing_controlled_rollout_allowance")
    if limited_general_stage and "missing_controlled_rollout_allowance" in v2_block_reasons:
        v2_block_reasons.remove("missing_controlled_rollout_allowance")
    if not stage_allowed and not production_shadow_stage and not internal_served_stage and not limited_general_stage and not staging_default_stage and not production_default_stage:
        v2_block_reasons.append("runtime_stage_not_controlled")
    if production_shadow_stage and not config.allow_v2_production_shadow:
        v2_block_reasons.append("missing_production_shadow_allowance")
    if production_shadow_stage and not config.shadow_compare:
        v2_block_reasons.append("shadow_compare_flag_missing")
    v2_block_reason = v2_block_reasons[0] if v2_block_reasons else ""

    if config.force_v1:
        return _decision(
            config,
            "v1",
            None,
            "v1",
            "RAG_FORCE_V1=true forces v1 and disables v2 shadow",
            v2_allowed,
            v2_block_reason,
            v2_block_reasons,
        )
    if config.v2_enabled_false:
        return _decision(
            config,
            "v1",
            None,
            "v1",
            "RAG_V2_ENABLED=false forces v1",
            v2_allowed,
            v2_block_reason,
            v2_block_reasons,
        )
    if not config.requested_version_valid:
        return _decision(
            config,
            "v1",
            None,
            "v1",
            "invalid retrieval version fails closed to v1",
            v2_allowed,
            v2_block_reason,
            v2_block_reasons,
        )
    if config.production_default_v2_requested:
        if production_default_prereqs_met:
            return _decision(
                config,
                "v2",
                None,
                "production_default_switch",
                "Phase 4.7 production default switch selected v2 served route",
                True,
                "",
                [],
            )
        return _decision(
            config,
            "v1",
            None,
            "v1",
            "v2 production default requested but blocked",
            False,
            v2_block_reason,
            v2_block_reasons,
        )
    if config.requested_version == "v2":
        if staging_default_stage:
            if staging_default_prereqs_met:
                return _decision(
                    config,
                    "v2",
                    None,
                    "staging_default_switch",
                    "staging default switch selected v2 served route",
                    True,
                    "",
                    [],
                )
            return _decision(
                config,
                "v1",
                None,
                "v1",
                "v2 staging default requested but blocked",
                False,
                v2_block_reason,
                v2_block_reasons,
            )
        if limited_general_stage:
            if general_canary_is_selected:
                return _decision(
                    config,
                    "v2",
                    None,
                    "limited_general_served_canary",
                    "limited general deterministic canary selected v2 served route",
                    True,
                    "",
                    [],
                    general_subject_hash=general_subject_hash,
                    general_decision_hash=general_decision_hash,
                    general_canary_selected=True,
                    canary_not_selected_reason="",
                )
            reason = "v2 limited general canary requested but blocked"
            not_selected_reason = v2_block_reason
            if general_canary_prereqs_met:
                reason = "general request kept on v1 by deterministic served percent"
                not_selected_reason = "deterministic_sample_not_selected"
            return _decision(
                config,
                "v1",
                None,
                "v1",
                reason,
                False,
                v2_block_reason,
                v2_block_reasons,
                general_subject_hash=general_subject_hash,
                general_decision_hash=general_decision_hash,
                general_canary_selected=False,
                canary_not_selected_reason=not_selected_reason or "limited_general_canary_not_allowed",
            )
        if internal_served_stage:
            if internal_canary_selected:
                return _decision(
                    config,
                    "v2",
                    None,
                    "internal_served_canary",
                    "internal allowlist selected v2 served canary route",
                    True,
                    "",
                    [],
                    allowlist_match=allowlist_match,
                    internal_canary_selected=True,
                )
            reason = "v2 internal served canary requested but blocked"
            if internal_canary_prereqs_met:
                reason = "internal allowlist request kept on v1 by deterministic served percent"
            return _decision(
                config,
                "v1",
                None,
                "v1",
                reason,
                False,
                v2_block_reason,
                v2_block_reasons,
                allowlist_match=allowlist_match,
                internal_canary_selected=False,
            )
        if v2_allowed:
            return _decision(
                config,
                "v2",
                None,
                "v2_served",
                "explicit v2 controlled rollout route",
                v2_allowed,
                "",
                [],
            )
        return _decision(
            config,
            "v1",
            None,
            "v1",
            "v2 requested but blocked",
            v2_allowed,
            v2_block_reason,
            v2_block_reasons,
        )
    if config.requested_version == "shadow":
        if production_shadow_stage:
            if production_shadow_allowed:
                if config.production_shadow_all:
                    return _decision(
                        config,
                        "v1",
                        "v2",
                        "production_shadow_all",
                        "production shadow all mode explicitly compares v2 for background only",
                        False,
                        "",
                        [],
                    )
                if config.production_shadow_percent > 0:
                    if _canary_selected(query_id or "", config.production_shadow_percent):
                        return _decision(
                            config,
                            "v1",
                            "v2",
                            "production_shadow_sampled",
                            "production shadow mode sampled v2 for background comparison only",
                            False,
                            "",
                            [],
                        )
                    return _decision(
                        config,
                        "v1",
                        None,
                        "v1",
                        "production shadow mode sample kept v1 only",
                        False,
                        "",
                        [],
                    )
                return _decision(
                    config,
                    "v1",
                    None,
                    "v1",
                    "production shadow percent is zero, so no direct shadow sample is executed",
                    False,
                    "",
                    [],
                )
            return _decision(
                config,
                "v1",
                None,
                "v1",
                "production shadow requested but blocked",
                False,
                v2_block_reason,
                v2_block_reasons,
            )
        if v2_allowed and config.shadow_compare:
            return _decision(config, "v1", "v2", "shadow", "shadow mode serves v1 and compares v2", v2_allowed, "", [])
        reason = "shadow requested but blocked"
        if v2_allowed and not config.shadow_compare:
            reason = "shadow requested without RAG_V2_SHADOW_COMPARE=true"
            v2_block_reason = "shadow_compare_flag_missing"
            v2_block_reasons = ["shadow_compare_flag_missing"]
        return _decision(config, "v1", None, "v1", reason, v2_allowed, v2_block_reason, v2_block_reasons)

    if query_id and query_id in config.force_query_ids:
        if v2_allowed:
            return _decision(config, "v2", None, "forced_query_id", "query id forced to v2", v2_allowed, "", [])
        return _decision(config, "v1", None, "v1", "forced query id blocked", v2_allowed, v2_block_reason, v2_block_reasons)

    if production_shadow_stage and config.production_shadow_percent > 0:
        if not production_shadow_allowed:
            return _decision(
                config,
                "v1",
                None,
                "v1",
                "production shadow sampling blocked",
                False,
                v2_block_reason,
                v2_block_reasons,
            )
        if _canary_selected(query_id or "", config.production_shadow_percent):
            return _decision(
                config,
                "v1",
                "v2",
                "production_shadow_sampled",
                "production shadow sampled v2 for background comparison only",
                False,
                "",
                [],
            )
        return _decision(
            config,
            "v1",
            None,
            "v1",
            "production shadow sample kept v1 only",
            False,
            "",
            [],
        )

    if config.canary_percent > 0:
        if not v2_allowed:
            return _decision(
                config,
                "v1",
                None,
                "v1",
                "synthetic canary blocked without allowance",
                v2_allowed,
                v2_block_reason,
                v2_block_reasons,
            )
        if _canary_selected(query_id or "", config.canary_percent):
            return _decision(config, "v2", None, "synthetic_canary", "deterministic canary selected v2", v2_allowed, "", [])
        return _decision(config, "v1", None, "v1", "deterministic canary kept v1", v2_allowed, "", [])

    return _decision(config, "v1", None, "v1", "default v1 route", v2_allowed, v2_block_reason, v2_block_reasons)


def construct_v1_retriever(config: RetrievalRouteConfig | None = None) -> "V1RuntimeRetriever":
    cfg = config or route_config_from_env({})
    return V1RuntimeRetriever(db_path=cfg.v1_db_path)


def construct_v2_retriever(config: RetrievalRouteConfig) -> "V2StagedRetriever":
    return V2StagedRetriever(config=config)


def maybe_construct_shadow_retriever(
    config: RetrievalRouteConfig,
    decision: RetrievalRouteDecision,
) -> "V2StagedRetriever | None":
    if decision.shadow_route != "v2":
        return None
    return construct_v2_retriever(config)


def run_retrieval_with_fallback(
    query: str,
    *,
    env: Mapping[str, str] | None = None,
    query_id: str | None = None,
    internal_canary_identity: InternalCanaryIdentity | Mapping[str, Any] | None = None,
    general_canary_identity: GeneralCanaryIdentity | Mapping[str, Any] | None = None,
    query_type: str | None = None,
    top_k: int = 5,
    v2_path_overrides: Mapping[str, str | Path] | None = None,
    inject_v2_exception: bool = False,
    production_runtime_connected: bool = False,
    frontend_started: bool = False,
) -> dict[str, Any]:
    config = route_config_from_env(
        env,
        v2_path_overrides=v2_path_overrides,
        production_runtime_connected=production_runtime_connected,
        frontend_started=frontend_started,
    )
    decision = select_retrieval_route(
        config,
        query_id=query_id,
        internal_canary_identity=internal_canary_identity,
        general_canary_identity=general_canary_identity,
    )
    route_metadata = decision.metadata()
    query_kind = query_type or infer_query_type(query)
    started = time.perf_counter()
    served_result: dict[str, Any]
    shadow_result: dict[str, Any] | None = None

    if decision.served_route == "v2":
        error: Exception | None = None
        try:
            if decision.route_mode == "limited_general_served_canary":
                served_result, served_metadata, error = run_v2_limited_general_served_retrieval(
                    config,
                    decision,
                    query,
                    query_type=query_kind,
                    top_k=top_k,
                    inject_v2_exception=inject_v2_exception,
                )
                route_metadata.update(served_metadata)
                if error is not None:
                    raise error
            elif decision.route_mode == "internal_served_canary":
                served_result, served_metadata, error = run_v2_internal_served_retrieval(
                    config,
                    decision,
                    query,
                    query_type=query_kind,
                    top_k=top_k,
                    inject_v2_exception=inject_v2_exception,
                )
                route_metadata.update(served_metadata)
                if error is not None:
                    raise error
            elif decision.route_mode == "staging_default_switch":
                served_result, served_metadata, error = run_v2_staging_default_retrieval(
                    config,
                    decision,
                    query,
                    query_type=query_kind,
                    top_k=top_k,
                    inject_v2_exception=inject_v2_exception,
                )
                route_metadata.update(served_metadata)
                if error is not None:
                    raise error
            elif decision.route_mode == "production_default_switch":
                served_result, served_metadata, error = run_v2_production_default_retrieval(
                    config,
                    decision,
                    query,
                    query_type=query_kind,
                    top_k=top_k,
                    inject_v2_exception=inject_v2_exception,
                )
                route_metadata.update(served_metadata)
                if error is not None:
                    raise error
            else:
                if inject_v2_exception:
                    raise RuntimeError("simulated_v2_retrieval_exception")
                served_result = construct_v2_retriever(config).retrieve(query, query_type=query_kind, top_k=top_k)
        except Exception as exc:
            if config.fallback_to_v1:
                served_result = construct_v1_retriever(config).retrieve(query, query_type=query_kind, top_k=top_k)
                route_metadata.update(
                    {
                        "served_route": "v1",
                        "selected_served_route": "v1",
                        "source_route": "v1",
                        "fallback_used": True,
                        "fallback_reason": f"{type(exc).__name__}: {exc}",
                        "v2_attempted": True,
                        "user_received_v1": True,
                        "retrieval_scope": served_result.get("retrieval_scope", "v1_fallback"),
                        "v2_served_to_user": False,
                        "v2_served_to_general_user": False,
                        "staging_default_active": False,
                        "production_default_active": False,
                        "general_user_v1_preserved": not bool(route_metadata.get("served_to_internal_allowlist")),
                        "served_to_general_canary": False,
                    }
                )
            else:
                served_result = {
                    "answer_status": "controlled_failure",
                    "retrieval_scope": "v2_failure_no_fallback",
                    "top_evidence": [],
                    "top_sources": [],
                    "boundary_pass": False,
                    "failure_reason": f"{type(exc).__name__}: {exc}",
                }
                route_metadata.update(
                    {
                        "fallback_used": False,
                        "fallback_reason": "",
                        "retrieval_scope": "v2_failure_no_fallback",
                    }
                )
    else:
        served_result = construct_v1_retriever(config).retrieve(query, query_type=query_kind, top_k=top_k)

    if decision.shadow_route == "v2":
        shadow_result, shadow_metadata = run_v2_shadow_retrieval(
            config,
            decision,
            query,
            query_type=query_kind,
            top_k=top_k,
        )
        route_metadata.update(shadow_metadata)

    route_metadata["retrieval_scope"] = served_result.get("retrieval_scope", route_metadata["retrieval_scope"])
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    if route_metadata.get("served_route") == "v2":
        route_metadata.update(evidence_contract_fields(served_result))
    else:
        route_metadata.update(
            {
                "final_response_uses_v2_evidence": False,
                "source_citation_fields_present": True,
                "evidence_lane_counts": {},
                "top_evidence_object_ids": [],
                "top_evidence_source_ids": [],
                "top_evidence_doc_types": [],
                "top_evidence_lanes": [],
                "boundary_pass": bool(served_result.get("boundary_pass", True)),
                "failure_reason": str(served_result.get("failure_reason") or ""),
            }
        )
    route_metadata["latency_ms"] = latency_ms
    return {
        "query": query,
        "query_id": query_id,
        "query_type": query_kind,
        "route_metadata": route_metadata,
        "served_result": served_result,
        "shadow_result": shadow_result,
        "latency_ms": latency_ms,
    }


class V1RuntimeRetriever:
    def __init__(self, *, db_path: Path) -> None:
        self.db_path = db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"v1 db missing: {self.db_path}")

    def retrieve(self, query: str, *, query_type: str | None = None, top_k: int = 5) -> dict[str, Any]:
        boundary_reason = classify_boundary(query)
        if boundary_reason:
            return {
                "answer_status": "refuse_boundary",
                "retrieval_scope": f"blocked_boundary:{boundary_reason}",
                "top_sources": [],
                "top_evidence": [],
                "boundary_pass": True,
                "failure_reason": "",
                "source_route": "v1",
            }
        focus, terms, _normalization = query_focus(query, query_type or infer_query_type(query))
        scored: list[dict[str, Any]] = []
        with open_sqlite_ro(self.db_path) as conn:
            for row in conn.execute("SELECT * FROM vw_retrieval_records_unified"):
                text = compact_text(row["retrieval_text"])
                score = 0.0
                matched: list[str] = []
                for term in terms[:24]:
                    count = text.count(term)
                    if count:
                        score += len(term) * 3.0 + count * 5.0
                        matched.append(term)
                if focus and focus in text:
                    score += 80.0
                if score <= 0:
                    continue
                scored.append(
                    {
                        "record_id": row["record_id"],
                        "source_object": row["source_object"],
                        "record_table": row["record_table"],
                        "policy_source_id": row["policy_source_id"],
                        "chapter_id": row["chapter_id"],
                        "chapter_name": row["chapter_name"],
                        "evidence_level": row["evidence_level"],
                        "score": round(score, 6),
                        "matched_terms": matched[:8],
                    }
                )
        scored.sort(key=lambda item: (-item["score"], item["record_id"]))
        return {
            "answer_status": "retrieval_complete" if scored else "weak_no_evidence",
            "retrieval_scope": "v1_sqlite_runtime_smoke",
            "top_sources": scored[:top_k],
            "top_evidence": [],
            "boundary_pass": True,
            "failure_reason": "",
            "source_route": "v1",
        }


def run_v2_shadow_retrieval(
    config: RetrievalRouteConfig,
    decision: RetrievalRouteDecision,
    query: str,
    *,
    query_type: str | None = None,
    top_k: int = 5,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    from backend.retrieval.production_shadow_metrics import (
        is_shadow_circuit_open,
        record_shadow_outcome,
    )

    metadata: dict[str, Any] = {
        "shadow_route_executed": False,
        "shadow_timed_out": False,
        "shadow_error": False,
        "shadow_error_reason": "",
        "shadow_circuit_breaker_open": False,
        "latency_v2_shadow_ms": None,
    }
    if decision.shadow_route != "v2":
        return None, metadata
    circuit_open, open_reason = is_shadow_circuit_open(config)
    if circuit_open:
        metadata.update(
            {
                "shadow_circuit_breaker_open": True,
                "shadow_error_reason": open_reason or "shadow_circuit_breaker_open",
            }
        )
        record_shadow_outcome(config, error=False, boundary_failure=False, timed_out=False, circuit_open=True)
        return {
            "answer_status": "shadow_skipped_circuit_open",
            "retrieval_scope": "v2_shadow_circuit_open",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": open_reason or "shadow_circuit_breaker_open",
            "source_route": "v2",
        }, metadata

    started = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        lambda: maybe_construct_shadow_retriever(config, decision).retrieve(  # type: ignore[union-attr]
            query,
            query_type=query_type,
            top_k=top_k,
        )
    )
    try:
        shadow_result = future.result(timeout=max(1, config.shadow_timeout_ms) / 1000)
        metadata["shadow_route_executed"] = True
        boundary_failure = not bool(shadow_result.get("boundary_pass", False))
        record_shadow_outcome(
            config,
            error=False,
            boundary_failure=boundary_failure,
            timed_out=False,
            circuit_open=False,
        )
        return shadow_result, metadata
    except TimeoutError:
        metadata.update(
            {
                "shadow_timed_out": True,
                "shadow_error": True,
                "shadow_error_reason": "shadow_timeout",
            }
        )
        record_shadow_outcome(config, error=True, boundary_failure=False, timed_out=True, circuit_open=False)
        return {
            "answer_status": "shadow_timeout",
            "retrieval_scope": "v2_shadow_timeout",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "shadow_timeout",
            "source_route": "v2",
        }, metadata
    except Exception as exc:
        metadata.update(
            {
                "shadow_error": True,
                "shadow_error_reason": f"{type(exc).__name__}: {exc}",
            }
        )
        record_shadow_outcome(config, error=True, boundary_failure=False, timed_out=False, circuit_open=False)
        return {
            "answer_status": "shadow_failure",
            "retrieval_scope": "v2_shadow_failure",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": False,
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "source_route": "v2",
        }, metadata
    finally:
        metadata["latency_v2_shadow_ms"] = round((time.perf_counter() - started) * 1000, 3)
        executor.shutdown(wait=False, cancel_futures=True)


def run_v2_internal_served_retrieval(
    config: RetrievalRouteConfig,
    decision: RetrievalRouteDecision,
    query: str,
    *,
    query_type: str | None = None,
    top_k: int = 5,
    inject_v2_exception: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], Exception | None]:
    from backend.retrieval.internal_canary_metrics import (
        is_internal_canary_circuit_open,
        record_internal_canary_outcome,
    )

    metadata: dict[str, Any] = {
        "v2_served_route_executed": False,
        "internal_timed_out": False,
        "internal_error": False,
        "internal_error_reason": "",
        "internal_circuit_breaker_open": False,
        "latency_v2_served_ms": None,
    }
    if decision.served_route != "v2":
        return {
            "answer_status": "internal_canary_not_selected",
            "retrieval_scope": "v1",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "",
            "source_route": "v1",
        }, metadata, None

    circuit_open, open_reason = is_internal_canary_circuit_open(config)
    if circuit_open:
        metadata.update(
            {
                "internal_circuit_breaker_open": True,
                "internal_error_reason": open_reason or "internal_circuit_breaker_open",
            }
        )
        record_internal_canary_outcome(config, error=False, boundary_failure=False, timed_out=False, circuit_open=True)
        return {
            "answer_status": "internal_canary_circuit_open",
            "retrieval_scope": "v2_internal_canary_circuit_open",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": open_reason or "internal_circuit_breaker_open",
            "source_route": "v2",
        }, metadata, RuntimeError(open_reason or "internal_circuit_breaker_open")

    started = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)

    def retrieve_v2() -> dict[str, Any]:
        if inject_v2_exception:
            raise RuntimeError("simulated_v2_retrieval_exception")
        return construct_v2_retriever(config).retrieve(query, query_type=query_type, top_k=top_k)

    future = executor.submit(retrieve_v2)
    try:
        served_result = future.result(timeout=max(1, config.internal_timeout_ms) / 1000)
        metadata["v2_served_route_executed"] = True
        boundary_failure = not bool(served_result.get("boundary_pass", False))
        record_internal_canary_outcome(
            config,
            error=False,
            boundary_failure=boundary_failure,
            timed_out=False,
            circuit_open=False,
        )
        return served_result, metadata, None
    except TimeoutError:
        metadata.update(
            {
                "internal_timed_out": True,
                "internal_error": True,
                "internal_error_reason": "internal_served_timeout",
            }
        )
        record_internal_canary_outcome(config, error=True, boundary_failure=False, timed_out=True, circuit_open=False)
        return {
            "answer_status": "internal_served_timeout",
            "retrieval_scope": "v2_internal_served_timeout",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "internal_served_timeout",
            "source_route": "v2",
        }, metadata, TimeoutError("internal_served_timeout")
    except Exception as exc:
        metadata.update(
            {
                "internal_error": True,
                "internal_error_reason": f"{type(exc).__name__}: {exc}",
            }
        )
        record_internal_canary_outcome(config, error=True, boundary_failure=False, timed_out=False, circuit_open=False)
        return {
            "answer_status": "internal_served_failure",
            "retrieval_scope": "v2_internal_served_failure",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": False,
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "source_route": "v2",
        }, metadata, exc
    finally:
        metadata["latency_v2_served_ms"] = round((time.perf_counter() - started) * 1000, 3)
        executor.shutdown(wait=False, cancel_futures=True)


def run_v2_limited_general_served_retrieval(
    config: RetrievalRouteConfig,
    decision: RetrievalRouteDecision,
    query: str,
    *,
    query_type: str | None = None,
    top_k: int = 5,
    inject_v2_exception: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], Exception | None]:
    from backend.retrieval.limited_general_canary_metrics import (
        is_limited_general_canary_circuit_open,
        record_limited_general_canary_outcome,
    )

    metadata: dict[str, Any] = {
        "v2_served_route_executed": False,
        "general_timed_out": False,
        "general_error": False,
        "general_error_reason": "",
        "general_circuit_breaker_open": False,
        "latency_v2_served_ms": None,
    }
    if decision.served_route != "v2":
        return {
            "answer_status": "limited_general_canary_not_selected",
            "retrieval_scope": "v1",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "",
            "source_route": "v1",
        }, metadata, None

    circuit_open, open_reason = is_limited_general_canary_circuit_open(config)
    if circuit_open:
        metadata.update(
            {
                "general_circuit_breaker_open": True,
                "general_error_reason": open_reason or "general_circuit_breaker_open",
            }
        )
        record_limited_general_canary_outcome(
            config,
            error=False,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=False,
            circuit_open=True,
        )
        return {
            "answer_status": "limited_general_canary_circuit_open",
            "retrieval_scope": "v2_limited_general_canary_circuit_open",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": open_reason or "general_circuit_breaker_open",
            "source_route": "v2",
        }, metadata, RuntimeError(open_reason or "general_circuit_breaker_open")

    started = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)

    def retrieve_v2() -> dict[str, Any]:
        if inject_v2_exception:
            raise RuntimeError("simulated_v2_retrieval_exception")
        return construct_v2_retriever(config).retrieve(query, query_type=query_type, top_k=top_k)

    try:
        served_result = future_result = executor.submit(retrieve_v2).result(timeout=max(1, config.general_timeout_ms) / 1000)
        monitor = audit_v2_general_canary_result(query, query_type or infer_query_type(query), future_result)
        metadata.update(monitor)
        metadata["v2_served_route_executed"] = True
        boundary_failure = not bool(monitor["boundary_pass"])
        source_failure = not bool(monitor["source_citation_boundary_pass"])
        medical_failure = not bool(monitor["medical_boundary_pass"])
        external_failure = not bool(monitor["external_source_boundary_pass"])
        privacy_failure = not bool(monitor["privacy_logging_pass"])
        record_limited_general_canary_outcome(
            config,
            error=False,
            boundary_failure=boundary_failure,
            source_citation_failure=source_failure,
            medical_boundary_failure=medical_failure,
            external_source_boundary_failure=external_failure,
            privacy_failure=privacy_failure,
            timed_out=False,
            circuit_open=False,
        )
        if boundary_failure or source_failure or medical_failure or external_failure or privacy_failure:
            reason = monitor.get("failure_reason") or "limited_general_canary_monitor_failure"
            return served_result, metadata, RuntimeError(str(reason))
        return served_result, metadata, None
    except TimeoutError:
        metadata.update(
            {
                "general_timed_out": True,
                "general_error": True,
                "general_error_reason": "limited_general_served_timeout",
            }
        )
        record_limited_general_canary_outcome(
            config,
            error=True,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=True,
            circuit_open=False,
        )
        return {
            "answer_status": "limited_general_served_timeout",
            "retrieval_scope": "v2_limited_general_served_timeout",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "limited_general_served_timeout",
            "source_route": "v2",
        }, metadata, TimeoutError("limited_general_served_timeout")
    except Exception as exc:
        metadata.update(
            {
                "general_error": True,
                "general_error_reason": f"{type(exc).__name__}: {exc}",
            }
        )
        record_limited_general_canary_outcome(
            config,
            error=True,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=False,
            circuit_open=False,
        )
        return {
            "answer_status": "limited_general_served_failure",
            "retrieval_scope": "v2_limited_general_served_failure",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": False,
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "source_route": "v2",
        }, metadata, exc
    finally:
        metadata["latency_v2_served_ms"] = round((time.perf_counter() - started) * 1000, 3)
        executor.shutdown(wait=False, cancel_futures=True)


def run_v2_staging_default_retrieval(
    config: RetrievalRouteConfig,
    decision: RetrievalRouteDecision,
    query: str,
    *,
    query_type: str | None = None,
    top_k: int = 5,
    inject_v2_exception: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], Exception | None]:
    from backend.retrieval.staging_default_metrics import (
        is_staging_default_circuit_open,
        record_staging_default_outcome,
    )

    metadata: dict[str, Any] = {
        "v2_served_route_executed": False,
        "staging_default_timed_out": False,
        "staging_default_error": False,
        "staging_default_error_reason": "",
        "staging_default_circuit_breaker_open": False,
        "latency_v2_staging_ms": None,
        "latency_v2_served_ms": None,
    }
    if decision.served_route != "v2":
        return {
            "answer_status": "staging_default_not_selected",
            "retrieval_scope": "v1",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "",
            "source_route": "v1",
        }, metadata, None

    circuit_open, open_reason = is_staging_default_circuit_open(config)
    if circuit_open:
        metadata.update(
            {
                "staging_default_circuit_breaker_open": True,
                "staging_default_error_reason": open_reason or "staging_default_circuit_breaker_open",
            }
        )
        record_staging_default_outcome(
            config,
            error=False,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=False,
            circuit_open=True,
        )
        return {
            "answer_status": "staging_default_circuit_open",
            "retrieval_scope": "v2_staging_default_circuit_open",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": open_reason or "staging_default_circuit_breaker_open",
            "source_route": "v2",
        }, metadata, RuntimeError(open_reason or "staging_default_circuit_breaker_open")

    started = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)

    def retrieve_v2() -> dict[str, Any]:
        if inject_v2_exception:
            raise RuntimeError("simulated_v2_retrieval_exception")
        return construct_v2_retriever(config).retrieve(query, query_type=query_type, top_k=top_k)

    try:
        served_result = executor.submit(retrieve_v2).result(timeout=max(1, config.staging_timeout_ms) / 1000)
        monitor = audit_v2_general_canary_result(query, query_type or infer_query_type(query), served_result)
        metadata.update(monitor)
        metadata["v2_served_route_executed"] = True
        boundary_failure = not bool(monitor["boundary_pass"])
        source_failure = not bool(monitor["source_citation_boundary_pass"])
        medical_failure = not bool(monitor["medical_boundary_pass"])
        external_failure = not bool(monitor["external_source_boundary_pass"])
        privacy_failure = not bool(monitor["privacy_logging_pass"])
        record_staging_default_outcome(
            config,
            error=False,
            boundary_failure=boundary_failure,
            source_citation_failure=source_failure,
            medical_boundary_failure=medical_failure,
            external_source_boundary_failure=external_failure,
            privacy_failure=privacy_failure,
            timed_out=False,
            circuit_open=False,
        )
        if boundary_failure or source_failure or medical_failure or external_failure or privacy_failure:
            reason = monitor.get("failure_reason") or "staging_default_monitor_failure"
            return served_result, metadata, RuntimeError(str(reason))
        return served_result, metadata, None
    except TimeoutError:
        metadata.update(
            {
                "staging_default_timed_out": True,
                "staging_default_error": True,
                "staging_default_error_reason": "staging_default_timeout",
            }
        )
        record_staging_default_outcome(
            config,
            error=True,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=True,
            circuit_open=False,
        )
        return {
            "answer_status": "staging_default_timeout",
            "retrieval_scope": "v2_staging_default_timeout",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "staging_default_timeout",
            "source_route": "v2",
        }, metadata, TimeoutError("staging_default_timeout")
    except Exception as exc:
        metadata.update(
            {
                "staging_default_error": True,
                "staging_default_error_reason": f"{type(exc).__name__}: {exc}",
            }
        )
        record_staging_default_outcome(
            config,
            error=True,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=False,
            circuit_open=False,
        )
        return {
            "answer_status": "staging_default_failure",
            "retrieval_scope": "v2_staging_default_failure",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": False,
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "source_route": "v2",
        }, metadata, exc
    finally:
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        metadata["latency_v2_staging_ms"] = elapsed
        metadata["latency_v2_served_ms"] = elapsed
        executor.shutdown(wait=False, cancel_futures=True)


def run_v2_production_default_retrieval(
    config: RetrievalRouteConfig,
    decision: RetrievalRouteDecision,
    query: str,
    *,
    query_type: str | None = None,
    top_k: int = 5,
    inject_v2_exception: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], Exception | None]:
    from backend.retrieval.production_default_metrics import (
        is_production_default_circuit_open,
        record_production_default_outcome,
    )

    metadata: dict[str, Any] = {
        "v2_served_route_executed": False,
        "production_default_timed_out": False,
        "production_default_error": False,
        "production_default_error_reason": "",
        "production_default_circuit_breaker_open": False,
        "latency_v2_production_ms": None,
        "latency_v2_served_ms": None,
    }
    if decision.served_route != "v2":
        return {
            "answer_status": "production_default_not_selected",
            "retrieval_scope": "v1",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "",
            "source_route": "v1",
        }, metadata, None

    circuit_open, open_reason = is_production_default_circuit_open(config)
    if circuit_open:
        metadata.update(
            {
                "production_default_circuit_breaker_open": True,
                "production_default_error_reason": open_reason or "production_default_circuit_breaker_open",
            }
        )
        record_production_default_outcome(
            config,
            error=False,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=False,
            circuit_open=True,
        )
        return {
            "answer_status": "production_default_circuit_open",
            "retrieval_scope": "v2_production_default_circuit_open",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": open_reason or "production_default_circuit_breaker_open",
            "source_route": "v2",
        }, metadata, RuntimeError(open_reason or "production_default_circuit_breaker_open")

    started = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)

    def retrieve_v2() -> dict[str, Any]:
        if inject_v2_exception:
            raise RuntimeError("simulated_v2_retrieval_exception")
        return construct_v2_retriever(config).retrieve(query, query_type=query_type, top_k=top_k)

    try:
        served_result = executor.submit(retrieve_v2).result(timeout=max(1, config.production_timeout_ms) / 1000)
        monitor = audit_v2_general_canary_result(query, query_type or infer_query_type(query), served_result)
        metadata.update(monitor)
        metadata["v2_served_route_executed"] = True
        boundary_failure = not bool(monitor["boundary_pass"])
        source_failure = not bool(monitor["source_citation_boundary_pass"])
        medical_failure = not bool(monitor["medical_boundary_pass"])
        external_failure = not bool(monitor["external_source_boundary_pass"])
        privacy_failure = not bool(monitor["privacy_logging_pass"])
        record_production_default_outcome(
            config,
            error=False,
            boundary_failure=boundary_failure,
            source_citation_failure=source_failure,
            medical_boundary_failure=medical_failure,
            external_source_boundary_failure=external_failure,
            privacy_failure=privacy_failure,
            timed_out=False,
            circuit_open=False,
        )
        if boundary_failure or source_failure or medical_failure or external_failure or privacy_failure:
            reason = monitor.get("failure_reason") or "production_default_monitor_failure"
            return served_result, metadata, RuntimeError(str(reason))
        return served_result, metadata, None
    except TimeoutError:
        metadata.update(
            {
                "production_default_timed_out": True,
                "production_default_error": True,
                "production_default_error_reason": "production_default_timeout",
            }
        )
        record_production_default_outcome(
            config,
            error=True,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=True,
            circuit_open=False,
        )
        return {
            "answer_status": "production_default_timeout",
            "retrieval_scope": "v2_production_default_timeout",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": True,
            "failure_reason": "production_default_timeout",
            "source_route": "v2",
        }, metadata, TimeoutError("production_default_timeout")
    except Exception as exc:
        metadata.update(
            {
                "production_default_error": True,
                "production_default_error_reason": f"{type(exc).__name__}: {exc}",
            }
        )
        record_production_default_outcome(
            config,
            error=True,
            boundary_failure=False,
            source_citation_failure=False,
            medical_boundary_failure=False,
            external_source_boundary_failure=False,
            privacy_failure=False,
            timed_out=False,
            circuit_open=False,
        )
        return {
            "answer_status": "production_default_failure",
            "retrieval_scope": "v2_production_default_failure",
            "top_evidence": [],
            "top_sources": [],
            "boundary_pass": False,
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "source_route": "v2",
        }, metadata, exc
    finally:
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        metadata["latency_v2_production_ms"] = elapsed
        metadata["latency_v2_served_ms"] = elapsed
        executor.shutdown(wait=False, cancel_futures=True)


class V2StagedRetriever:
    def __init__(self, *, config: RetrievalRouteConfig) -> None:
        self.config = config
        self.adapter = V2RetrievalAdapter(sidecar_db=config.v2_sidecar_db, index_dir=config.v2_index_dir)
        self._validate_artifacts()

    def retrieve(self, query: str, *, query_type: str | None = None, top_k: int = 5) -> dict[str, Any]:
        query_kind = query_type or infer_query_type(query)
        boundary_reason = classify_boundary(query)
        if boundary_reason:
            return {
                "query": query,
                "answer_status": "refuse_boundary",
                "retrieval_scope": f"blocked_boundary:{boundary_reason}",
                "top_evidence": [],
                "top_sources": [],
                "evidence_lane_counts": {},
                "boundary_pass": True,
                "failure_reason": "",
                "source_route": "v2",
            }

        retrieval_scope, lanes = lanes_for_query(query_kind)
        focus, terms, normalization = query_focus(query, query_kind)
        scored: list[dict[str, Any]] = []
        lane_bonus = {
            "formula_text_primary": 80.0 if query_kind == "formula_text" else 16.0,
            "formula_usage_positive": 80.0 if query_kind == "formula_usage" else 14.0,
            "main_text_primary": 36.0 if query_kind in {"book_internal", "formula_usage"} else 8.0,
            "primary_safe": 30.0 if query_kind in {"book_internal", "variant_preservation"} else 10.0,
            "auxiliary_safe": 82.0 if query_kind == "annotation" else -100.0,
        }
        with open_sqlite_ro(self.adapter.lexical_index_path) as conn:
            for lane in lanes:
                table = LANE_TABLES[lane]
                for row in conn.execute(f"SELECT * FROM {table}"):
                    display_compact = compact_text(row["display_text"])
                    index_compact = compact_text(row["text_for_index"])
                    score = lane_bonus.get(lane, 0.0)
                    matched: list[str] = []
                    for term in terms:
                        count = display_compact.count(term) + index_compact.count(term)
                        if count:
                            score += min(60.0, (len(term) * 4.0 + count * 6.0))
                            matched.append(term)
                    if focus and (focus in display_compact or focus in index_compact):
                        score += 120.0
                    if query_kind == "formula_text" and row["object_type"] == "formula_text":
                        score += 70.0
                    if query_kind == "formula_usage" and row["object_type"] == "formula_usage_context":
                        score += 70.0
                    if query_kind == "annotation" and row["object_type"] == "annotation":
                        score += 70.0
                    if query_kind == "book_internal" and row["object_type"] == "main_text":
                        score += 28.0
                    if query_kind == "variant_preservation" and compact_text(query) in display_compact:
                        score += 80.0
                    if query_kind == "variant_preservation" and normalization["variant_normalization_applied"]:
                        normalized = compact_text(normalization["normalized_to"])
                        if normalized and normalized in display_compact:
                            score += 65.0
                    if matched or score >= lane_bonus.get(lane, 0.0) + 60.0:
                        item = summarize_v2_evidence(row, lane, score)
                        item["matched_terms"] = matched[:8]
                        item["query_focus"] = focus
                        item.update(normalization)
                        scored.append(item)

        lane_priority = lane_priority_for_query(query_kind)
        scored.sort(
            key=lambda item: (
                lane_priority.get(item["lane"], 99),
                -item["score"],
                item["record_id"],
            )
        )
        selected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for item in scored:
            dedupe_key = str(item.get("object_id") or item["record_id"])
            if dedupe_key in seen_ids:
                continue
            seen_ids.add(dedupe_key)
            selected.append(item)
            if len(selected) >= top_k:
                break

        answer_status = "weak_no_evidence"
        if selected:
            answer_status = "weak_with_labeled_auxiliary" if query_kind == "annotation" else "retrieval_complete"
        boundary_pass, failure_reason = evaluate_v2_boundary(query, query_kind, selected)
        return {
            "query": query,
            "answer_status": answer_status,
            "retrieval_scope": retrieval_scope,
            "top_evidence": selected,
            "top_sources": [
                {
                    "record_id": item["record_id"],
                    "source_object_id": item.get("source_object_id"),
                    "lane": item["lane"],
                    "doc_type": item["doc_type"],
                    "score": item["score"],
                }
                for item in selected
            ],
            "evidence_lane_counts": dict(Counter(item["lane"] for item in selected)),
            "boundary_pass": boundary_pass,
            "failure_reason": failure_reason,
            "source_route": "v2",
        }

    def _validate_artifacts(self) -> None:
        if self.config.simulate_faiss_unavailable:
            raise RuntimeError("simulated_faiss_dependency_unavailable")
        if self.config.v2_model_manifest_path is not None and not self.config.v2_model_manifest_path.exists():
            raise FileNotFoundError(f"v2 model manifest missing: {self.config.v2_model_manifest_path}")
        required_paths = self._required_paths()
        missing = [f"{name}: {path}" for name, path in required_paths.items() if not path.exists()]
        if missing:
            raise FileNotFoundError("; ".join(missing))
        for lane, expected in EXPECTED_PHASE31_COUNTS.items():
            metadata_path = self._path_for(f"{lane}_dense_metadata")
            if metadata_path is None:
                continue
            count = sum(1 for line in metadata_path.read_text(encoding="utf-8").splitlines() if line.strip())
            if count != expected:
                raise ValueError(f"{lane} metadata count mismatch: expected {expected}, got {count}")

    def _required_paths(self) -> dict[str, Path]:
        paths = {
            "v2_sidecar_db": self.config.v2_sidecar_db,
            "v2_lexical_index_db": self._path_for("v2_lexical_index_db") or self.adapter.lexical_index_path,
        }
        for lane in ["primary_safe", "formula_text_primary", "formula_usage_positive", "auxiliary_safe"]:
            dense_index = self._path_for(f"{lane}_dense_index") or self.adapter.dense_index_path(lane)
            dense_metadata = self._path_for(f"{lane}_dense_metadata") or self.adapter.dense_metadata_path(lane)
            if dense_index is not None:
                paths[f"{lane}_dense_index"] = dense_index
            if dense_metadata is not None:
                paths[f"{lane}_dense_metadata"] = dense_metadata
        return paths

    def _path_for(self, key: str) -> Path | None:
        return self.config.v2_path_overrides.get(key)


def infer_query_type(query: str) -> str:
    if classify_boundary(query):
        return "boundary_refusal"
    if "方文" in query:
        return "formula_text"
    if "用于哪些" in query or "哪些条文" in query:
        return "formula_usage"
    if "成无己" in query or "注文" in query:
        return "annotation"
    if query.strip() in VARIANT_PROBE_TERMS:
        return "variant_preservation"
    return "book_internal"


def classify_boundary(query: str) -> str | None:
    for hint, reason in BOUNDARY_REFUSAL_HINTS.items():
        if hint in query:
            return reason
    return None


def lanes_for_query(query_type: str) -> tuple[str, list[str]]:
    if query_type == "formula_text":
        return "formula_text_primary_preferred", ["formula_text_primary", "primary_safe", "main_text_primary"]
    if query_type == "formula_usage":
        return "formula_usage_positive_preferred", ["formula_usage_positive", "main_text_primary", "primary_safe"]
    if query_type == "annotation":
        return "explicit_auxiliary_requested", ["auxiliary_safe", "main_text_primary"]
    if query_type == "variant_preservation":
        return "primary_variant_preservation", [
            "primary_safe",
            "formula_text_primary",
            "formula_usage_positive",
            "main_text_primary",
        ]
    return "primary_book_internal", ["main_text_primary", "primary_safe"]


def lane_priority_for_query(query_type: str) -> dict[str, int]:
    if query_type == "formula_text":
        return {"formula_text_primary": 0, "primary_safe": 1, "main_text_primary": 2}
    if query_type == "formula_usage":
        return {"formula_usage_positive": 0, "main_text_primary": 1, "primary_safe": 2}
    if query_type == "annotation":
        return {"auxiliary_safe": 0, "main_text_primary": 1}
    if query_type == "book_internal":
        return {"main_text_primary": 0, "primary_safe": 1}
    return {"primary_safe": 0, "formula_text_primary": 1, "formula_usage_positive": 2, "main_text_primary": 3}


def query_focus(query: str, query_type: str) -> tuple[str, list[str], dict[str, Any]]:
    raw = query.strip()
    normalized_applied = False
    normalized_from = None
    normalized_to = None
    search_text = VARIANT_NORMALIZATION.get(raw, raw) if query_type == "variant_preservation" else raw
    if search_text != raw:
        normalized_applied = True
        normalized_from = raw
        normalized_to = search_text

    focus = search_text
    removals = [
        "请问",
        "请",
        "本系统",
        "书中",
        "在书中",
        "《注解伤寒论》",
        "伤寒论",
        "方文",
        "用于哪些条文",
        "用于哪些",
        "哪些条文",
        "如何解释",
        "注文中",
        "注文",
        "成无己",
        "解释",
        "回答",
        "中",
        "里",
    ]
    for item in removals:
        focus = focus.replace(item, "")
    focus_compact = compact_text(focus) or compact_text(search_text)

    terms = [focus_compact, compact_text(search_text), compact_text(raw)]
    if query_type in {"formula_text", "formula_usage"} and focus_compact.endswith("方"):
        terms.append(focus_compact[:-1])
    for n in range(min(4, len(focus_compact)), 0, -1):
        for idx in range(0, len(focus_compact) - n + 1):
            terms.append(focus_compact[idx : idx + n])
    unique_terms: list[str] = []
    for term in terms:
        if term and term not in unique_terms:
            unique_terms.append(term)
    return focus_compact, unique_terms[:24], {
        "variant_normalization_applied": normalized_applied,
        "normalized_from": normalized_from,
        "normalized_to": normalized_to,
    }


def summarize_v2_evidence(row: sqlite3.Row, lane: str, score: float) -> dict[str, Any]:
    metadata = parse_metadata(row)
    payload = metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {}
    risk_flags = payload.get("risk_flags") or metadata.get("risk_flags") or []
    if isinstance(risk_flags, str):
        try:
            risk_flags = json.loads(risk_flags)
        except Exception:
            risk_flags = [risk_flags]
    display_text = row["display_text"] or ""
    indexed_text = row["text_for_index"] or ""
    source_span = payload.get("source_span") or {}
    source_file = row["source_file"] or payload.get("source_file") or ""
    source_item_no = str(row["source_item_no"] or payload.get("source_item_no") or "")
    object_id = row["source_object_id"] or payload.get("source_object") or row["record_id"]
    formula_id = payload.get("formula_id") or payload.get("parent_formula_id") or ""
    formula_name = payload.get("formula_name") or payload.get("canonical_name") or ""
    chapter_title = payload.get("chapter_title") or payload.get("canonical_title") or ""
    evidence_text = payload.get("text") or display_text
    return {
        "score": round(score, 6),
        "index_doc_id": row["index_doc_id"],
        "record_id": row["record_id"],
        "source_object_id": row["source_object_id"],
        "source_id": row["record_id"],
        "object_id": object_id,
        "object_type": row["object_type"],
        "doc_type": row["object_type"],
        "lane": lane,
        "index_lane": LANE_INDEX_NAMES[lane],
        "source_view": row["source_view"],
        "retrieval_lane": row["retrieval_lane"],
        "evidence_scope": "auxiliary" if lane == "auxiliary_safe" else "primary",
        "evidence_level": row["evidence_level"],
        "primary_allowed": bool(row["primary_allowed"]),
        "review_only": bool(row["review_only"]),
        "residual_carryover": bool(row["residual_carryover"]),
        "excluded_from_primary_retrieval": bool(row["excluded_from_primary_retrieval"]),
        "positive_formula_usage_allowed": bool(
            metadata.get("positive_formula_usage_allowed", payload.get("positive_formula_usage_allowed", False))
        ),
        "source_file": source_file,
        "source_item_no": source_item_no,
        "source_ref": f"{source_file}:{source_item_no}" if source_file and source_item_no else "",
        "source_span": source_span,
        "source_citation_fields_present": bool(row["record_id"] and source_file and source_item_no),
        "risk_flags": risk_flags,
        "formula_id": formula_id,
        "formula_name": formula_name,
        "clause_id": payload.get("clause_id") or payload.get("main_text_id") or "",
        "juanpian": chapter_title,
        "display_text": display_text,
        "evidence_text": evidence_text,
        "display_text_sha256": hashlib.sha256(display_text.encode("utf-8")).hexdigest(),
        "text_for_index_sha256": hashlib.sha256(indexed_text.encode("utf-8")).hexdigest(),
        "payload_display_text_matches_row": payload.get("display_text") in {None, display_text},
        "payload_text": payload.get("text"),
        "payload_normalized_text": payload.get("normalized_text"),
    }


def evaluate_v2_boundary(query: str, query_type: str, evidence: list[dict[str, Any]]) -> tuple[bool, str]:
    if query_type == "formula_text" and not any(item["lane"] == "formula_text_primary" for item in evidence):
        return False, "formula_text_primary_not_available"
    if query_type == "formula_usage" and any(item["lane"] == "formula_text_primary" for item in evidence):
        return False, "formula_usage_collapsed_into_formula_text"
    if query_type != "annotation" and any(item["lane"] == "auxiliary_safe" for item in evidence):
        return False, "auxiliary_returned_without_explicit_request"
    if any(item["residual_carryover"] and item["primary_allowed"] for item in evidence):
        return False, "carryover_returned_as_primary"
    if query_type == "formula_usage" and any(
        item["lane"] == "formula_usage_positive" and not item["positive_formula_usage_allowed"] for item in evidence
    ):
        return False, "formula_usage_positive_without_positive_usage_flag"
    if not all(source_fields_present(item) for item in evidence):
        return False, "missing_source_citation_fields"
    if query_type == "variant_preservation":
        expected = compact_text(VARIANT_NORMALIZATION.get(query, query))
        query_raw = compact_text(query)
        if evidence and not any(
            expected in compact_text(item["display_text"]) or query_raw in compact_text(item["display_text"])
            for item in evidence
        ):
            return False, "variant_not_visible_in_display_text"
    return True, ""


def source_fields_present(evidence: dict[str, Any]) -> bool:
    return bool(
        evidence.get("record_id")
        and evidence.get("object_id")
        and evidence.get("source_id")
        and evidence.get("source_ref")
        and evidence.get("display_text")
        and evidence.get("evidence_text")
    )


def parse_metadata(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    raw = row["metadata_json"] if isinstance(row, sqlite3.Row) else row.get("metadata_json")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def open_sqlite_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(text).lower())


def _decision(
    config: RetrievalRouteConfig,
    served_route: str,
    shadow_route: str | None,
    route_mode: str,
    reason: str,
    v2_allowed: bool,
    v2_block_reason: str,
    v2_block_reasons: list[str],
    *,
    allowlist_match: InternalAllowlistMatch | None = None,
    internal_canary_selected: bool = False,
    general_subject_hash: str = "",
    general_decision_hash: str = "",
    general_canary_selected: bool = False,
    canary_not_selected_reason: str = "",
) -> RetrievalRouteDecision:
    match = allowlist_match or InternalAllowlistMatch(False)
    served_to_internal = served_route == "v2" and config.runtime_stage == INTERNAL_SERVED_CANARY_STAGE and match.matched
    served_to_general = (
        served_route == "v2"
        and config.runtime_stage == LIMITED_GENERAL_SERVED_CANARY_STAGE
        and general_canary_selected
    )
    subject_hash = general_subject_hash or match.subject_hash
    return RetrievalRouteDecision(
        served_route=served_route,
        shadow_route=shadow_route,
        route_mode=route_mode,
        route_selection_reason=reason,
        runtime_stage=config.runtime_stage,
        flag_state=config.flag_state,
        v2_allowed=v2_allowed,
        v2_block_reason=v2_block_reason,
        v2_block_reasons=tuple(v2_block_reasons),
        fallback_to_v1=config.fallback_to_v1,
        canary_percent=config.canary_percent,
        production_shadow_enabled=shadow_route == "v2" and config.runtime_stage == PRODUCTION_SHADOW_STAGE,
        production_served_v2_percent=config.production_served_v2_percent,
        production_shadow_percent=config.production_shadow_percent,
        production_shadow_all=config.production_shadow_all,
        shadow_sample_selected=shadow_route == "v2",
        shadow_timeout_ms=config.shadow_timeout_ms,
        shadow_circuit_breaker_open=False,
        internal_served_percent=config.internal_served_percent,
        internal_allowlist_required=config.internal_canary_require_allowlist,
        internal_allowlist_matched=match.matched,
        allowlist_match_type=match.match_type,
        canary_subject_hash=subject_hash,
        served_to_internal_allowlist=served_to_internal,
        served_to_general_production_user=served_to_general,
        internal_canary_selected=internal_canary_selected,
        internal_timeout_ms=config.internal_timeout_ms,
        internal_circuit_breaker_open=False,
        allow_v2_limited_general_canary=config.allow_v2_limited_general_canary,
        served_to_general_canary=served_to_general,
        general_canary_selected=general_canary_selected,
        general_canary_percent=config.general_served_percent,
        general_canary_max_percent=config.general_canary_max_percent,
        general_canary_subject_hash=general_subject_hash,
        canary_decision_hash=general_decision_hash,
        canary_not_selected_reason=canary_not_selected_reason,
        general_timeout_ms=config.general_timeout_ms,
        general_circuit_breaker_open=False,
        general_monitors_required=config.general_canary_require_monitors,
        general_monitors_available=config.general_monitor_availability.all_available,
        boundary_monitor_available=config.general_monitor_availability.boundary_monitor_available,
        source_citation_monitor_available=config.general_monitor_availability.source_citation_monitor_available,
        privacy_logging_available=config.general_monitor_availability.privacy_logging_available,
        allow_v2_staging_default_switch=config.allow_v2_staging_default_switch,
        staging_default_requested=config.staging_default_requested,
        staging_default_percent=config.staging_default_percent,
        staging_default_percent_valid=config.staging_default_percent_valid,
        staging_default_percent_full=config.staging_default_percent_full,
        staging_default_timeout_ms=config.staging_timeout_ms,
        staging_default_circuit_breaker_open=False,
        staging_default_monitors_required=config.staging_default_require_monitors,
        staging_default_monitors_available=(
            config.staging_monitor_availability.all_available and config.staging_timeout_monitor_available
        ),
        staging_boundary_monitor_available=config.staging_monitor_availability.boundary_monitor_available,
        staging_source_citation_monitor_available=config.staging_monitor_availability.source_citation_monitor_available,
        staging_privacy_logging_available=config.staging_monitor_availability.privacy_logging_available,
        staging_timeout_monitor_available=config.staging_timeout_monitor_available,
        allow_v2_production_default_switch=config.allow_v2_production_default_switch,
        allow_v2_post_cutover_stabilization=config.allow_v2_post_cutover_stabilization,
        allow_v2_post_stabilization_operations=config.allow_v2_post_stabilization_operations,
        production_default_version=config.production_default_version,
        production_default_version_valid=config.production_default_version_valid,
        production_default_timeout_ms=config.production_timeout_ms,
        production_default_circuit_breaker_open=False,
        production_default_monitors_required=config.production_default_require_monitors,
        production_default_monitors_available=(
            config.production_monitor_availability.all_available and config.production_timeout_monitor_available
        ),
        production_boundary_monitor_available=config.production_monitor_availability.boundary_monitor_available,
        production_source_citation_monitor_available=config.production_monitor_availability.source_citation_monitor_available,
        production_privacy_logging_available=config.production_monitor_availability.privacy_logging_available,
        production_timeout_monitor_available=config.production_timeout_monitor_available,
        production_default_v2_requested=config.production_default_v2_requested,
        production_runtime_connected=config.production_runtime_connected,
        frontend_started=config.frontend_started,
        kill_switch_active=config.force_v1,
    )


def _canary_selected(query_id: str, percent: int) -> bool:
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    digest = hashlib.sha256(query_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return bucket < percent


def _parse_canary_percent(value: str | None) -> int:
    if value is None or str(value).strip() == "":
        return 0
    try:
        return max(0, min(100, int(str(value).strip())))
    except ValueError:
        return 0


def parse_staging_default_percent(value: str | None) -> StagingDefaultPercentParse:
    if value is None or str(value).strip() == "":
        return StagingDefaultPercentParse(value, 100.0, True, True, True, "absent_defaults_to_100")
    try:
        percent = float(str(value).strip())
    except ValueError:
        return StagingDefaultPercentParse(value, 0.0, False, False, False, "invalid_percent")
    return StagingDefaultPercentParse(value, percent, True, False, percent == 100.0, "")


def _parse_positive_int(value: str | None, *, default: int) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return max(1, int(str(value).strip()))
    except ValueError:
        return default


def _parse_nonnegative_int(value: str | None, *, default: int) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return max(0, int(str(value).strip()))
    except ValueError:
        return default


def _parse_float(value: str | None, *, default: float) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        return max(0.0, float(str(value).strip()))
    except ValueError:
        return default


def sanitize_flag_state(flag_state: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in flag_state.items():
        key_text = str(key)
        if any(token in key_text.upper() for token in ["KEY", "TOKEN", "SECRET", "COOKIE", "AUTH"]):
            sanitized[key_text] = "<redacted>"
        elif key_text in {
            ENV_V2_INTERNAL_ALLOWLIST_USER_HASHES,
            ENV_V2_INTERNAL_ALLOWLIST_QUERY_IDS,
            ENV_V2_INTERNAL_ALLOWLIST_REQUEST_HASHES,
        }:
            sanitized[key_text] = f"<{len(parse_allowlist_hashes(str(value)))}_hashes>"
        elif key_text == ENV_V2_MODEL_MANIFEST_PATH:
            sanitized[key_text] = bool(value)
        else:
            sanitized[key_text] = value
    sanitized["kill_switch_active"] = _truthy(str(flag_state.get(ENV_FORCE_V1))) if ENV_FORCE_V1 in flag_state else False
    return sanitized


def _truthy(value: str | None) -> bool:
    return _clean_flag(value) in TRUE_VALUES


def _falsey(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return _clean_flag(value) in FALSE_VALUES


def _clean_flag(value: str | None) -> str:
    return str(value or "").strip().lower()
