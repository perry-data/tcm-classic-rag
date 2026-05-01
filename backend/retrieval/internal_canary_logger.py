from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from backend.retrieval.internal_canary import evidence_contract_fields, stable_hash


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_INTERNAL_CANARY_LOG_PATH = "RAG_V2_INTERNAL_CANARY_LOG_PATH"
DEFAULT_INTERNAL_CANARY_LOG_PATH = (
    PROJECT_ROOT
    / "artifacts/data_reconstruction_v2/phase4_4_internal_served_canary/runtime_logs_sanitized.jsonl"
)

ALLOWED_LOG_FIELDS = [
    "timestamp_utc",
    "request_id_hash",
    "query_hash",
    "query_length",
    "query_type",
    "served_route",
    "served_to_internal_allowlist",
    "served_to_general_production_user",
    "allowlist_match_type",
    "canary_subject_hash",
    "v1_answer_status",
    "v2_answer_status",
    "v2_source_citation_fields_present",
    "v2_boundary_pass",
    "v2_failure_reason_code",
    "v2_top_source_ids",
    "v2_top_evidence_lanes",
    "v2_top_doc_types",
    "fallback_used",
    "fallback_reason",
    "latency_v1_ms",
    "latency_v2_served_ms",
    "runtime_stage",
    "flags_sanitized",
]


def internal_canary_log_path(path_value: str | Path | None = None) -> Path:
    raw = path_value or os.environ.get(ENV_INTERNAL_CANARY_LOG_PATH) or DEFAULT_INTERNAL_CANARY_LOG_PATH
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def build_internal_canary_log_record(
    *,
    query: str,
    query_type: str,
    route_metadata: Mapping[str, Any],
    served_result: Mapping[str, Any] | None,
    request_id: str | None = None,
    latency_v1_ms: float | None = None,
) -> dict[str, Any]:
    contract = evidence_contract_fields(served_result if route_metadata.get("served_route") == "v2" else None)
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request_id_hash": stable_hash(request_id),
        "query_hash": stable_hash(query),
        "query_length": len(query),
        "query_type": query_type,
        "served_route": route_metadata.get("served_route") or "v1",
        "served_to_internal_allowlist": bool(route_metadata.get("served_to_internal_allowlist")),
        "served_to_general_production_user": bool(route_metadata.get("served_to_general_production_user")),
        "allowlist_match_type": route_metadata.get("allowlist_match_type") or "",
        "canary_subject_hash": route_metadata.get("canary_subject_hash") or "",
        "v1_answer_status": _answer_status(served_result) if route_metadata.get("served_route") == "v1" else "",
        "v2_answer_status": _answer_status(served_result) if route_metadata.get("served_route") == "v2" else "",
        "v2_source_citation_fields_present": bool(contract["source_citation_fields_present"]),
        "v2_boundary_pass": bool(contract["boundary_pass"]),
        "v2_failure_reason_code": _failure_code(contract["failure_reason"]),
        "v2_top_source_ids": contract["top_evidence_source_ids"],
        "v2_top_evidence_lanes": contract["top_evidence_lanes"],
        "v2_top_doc_types": contract["top_evidence_doc_types"],
        "fallback_used": bool(route_metadata.get("fallback_used")),
        "fallback_reason": _failure_code(route_metadata.get("fallback_reason")),
        "latency_v1_ms": latency_v1_ms,
        "latency_v2_served_ms": route_metadata.get("latency_v2_served_ms"),
        "runtime_stage": route_metadata.get("runtime_stage") or "",
        "flags_sanitized": dict(route_metadata.get("flag_state_sanitized") or {}),
    }
    return {key: record.get(key) for key in ALLOWED_LOG_FIELDS}


def append_internal_canary_log(record: Mapping[str, Any], *, path: str | Path | None = None) -> Path:
    target = internal_canary_log_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    sanitized = {key: record.get(key) for key in ALLOWED_LOG_FIELDS}
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sanitized, ensure_ascii=False, sort_keys=False) + "\n")
    return target


def _answer_status(result: Mapping[str, Any] | None) -> str:
    if not result:
        return ""
    return str(result.get("answer_status") or result.get("answer_mode") or "")


def _failure_code(raw: Any) -> str:
    if not raw:
        return ""
    text = str(raw)
    for separator in [":", ";", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
    return text[:80]
