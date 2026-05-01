from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_SHADOW_LOG_PATH = "RAG_V2_PRODUCTION_SHADOW_LOG_PATH"
DEFAULT_SHADOW_LOG_PATH = (
    PROJECT_ROOT
    / "artifacts/data_reconstruction_v2/phase4_3_production_shadow_canary/runtime_logs_sanitized.jsonl"
)

ALLOWED_LOG_FIELDS = [
    "timestamp_utc",
    "request_id_hash",
    "query_hash",
    "query_length",
    "query_type",
    "served_route",
    "shadow_route",
    "route_mode",
    "shadow_sample_selected",
    "v1_answer_status",
    "v2_answer_status",
    "v1_top_source_ids",
    "v2_top_source_ids",
    "v2_top_evidence_lanes",
    "v2_top_doc_types",
    "v2_source_citation_fields_present",
    "v2_boundary_pass",
    "v2_failure_reason_code",
    "latency_v1_ms",
    "latency_v2_shadow_ms",
    "shadow_timed_out",
    "shadow_error",
    "shadow_circuit_breaker_open",
    "fallback_used",
    "runtime_stage",
    "flags_sanitized",
]


def stable_hash(value: str | None) -> str:
    text = value or ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def shadow_log_path(path_value: str | Path | None = None) -> Path:
    raw = path_value or os.environ.get(ENV_SHADOW_LOG_PATH) or DEFAULT_SHADOW_LOG_PATH
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def build_shadow_log_record(
    *,
    query: str,
    query_type: str,
    route_metadata: Mapping[str, Any],
    served_result: Mapping[str, Any] | None,
    shadow_result: Mapping[str, Any] | None,
    request_id: str | None = None,
    latency_v1_ms: float | None = None,
) -> dict[str, Any]:
    v2_evidence = list((shadow_result or {}).get("top_evidence") or [])
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request_id_hash": stable_hash(request_id),
        "query_hash": stable_hash(query),
        "query_length": len(query),
        "query_type": query_type,
        "served_route": route_metadata.get("served_route") or "v1",
        "shadow_route": route_metadata.get("shadow_route"),
        "route_mode": route_metadata.get("route_mode") or "v1",
        "shadow_sample_selected": bool(route_metadata.get("shadow_sample_selected")),
        "v1_answer_status": _answer_status(served_result),
        "v2_answer_status": _answer_status(shadow_result),
        "v1_top_source_ids": _source_ids(served_result),
        "v2_top_source_ids": _source_ids(shadow_result),
        "v2_top_evidence_lanes": [item.get("lane") for item in v2_evidence if isinstance(item, Mapping)],
        "v2_top_doc_types": [item.get("doc_type") for item in v2_evidence if isinstance(item, Mapping)],
        "v2_source_citation_fields_present": _source_fields_present(v2_evidence),
        "v2_boundary_pass": bool((shadow_result or {}).get("boundary_pass", True)),
        "v2_failure_reason_code": _failure_code((shadow_result or {}).get("failure_reason")),
        "latency_v1_ms": latency_v1_ms,
        "latency_v2_shadow_ms": route_metadata.get("latency_v2_shadow_ms"),
        "shadow_timed_out": bool(route_metadata.get("shadow_timed_out")),
        "shadow_error": bool(route_metadata.get("shadow_error")),
        "shadow_circuit_breaker_open": bool(route_metadata.get("shadow_circuit_breaker_open")),
        "fallback_used": bool(route_metadata.get("fallback_used")),
        "runtime_stage": route_metadata.get("runtime_stage") or "",
        "flags_sanitized": dict(route_metadata.get("flag_state_sanitized") or {}),
    }
    return {key: record.get(key) for key in ALLOWED_LOG_FIELDS}


def append_shadow_log(record: Mapping[str, Any], *, path: str | Path | None = None) -> Path:
    target = shadow_log_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    sanitized = {key: record.get(key) for key in ALLOWED_LOG_FIELDS}
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sanitized, ensure_ascii=False, sort_keys=False) + "\n")
    return target


def _answer_status(result: Mapping[str, Any] | None) -> str:
    if not result:
        return ""
    return str(result.get("answer_status") or result.get("answer_mode") or "")


def _source_ids(result: Mapping[str, Any] | None) -> list[str]:
    if not result:
        return []
    rows = list(result.get("top_sources") or [])
    if not rows:
        rows = list(result.get("primary_evidence") or []) + list(result.get("secondary_evidence") or [])
    ids: list[str] = []
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        source_id = row.get("source_id") or row.get("record_id") or row.get("source_object_id")
        if source_id:
            ids.append(str(source_id))
    return ids


def _source_fields_present(evidence: list[Any]) -> bool:
    if not evidence:
        return True
    for item in evidence:
        if not isinstance(item, Mapping):
            return False
        if not (
            item.get("record_id")
            and item.get("object_id")
            and item.get("source_id")
            and item.get("source_ref")
            and item.get("display_text")
            and item.get("evidence_text")
        ):
            return False
    return True


def _failure_code(raw: Any) -> str:
    if not raw:
        return ""
    text = str(raw)
    for separator in [":", ";", "\n"]:
        if separator in text:
            text = text.split(separator, 1)[0]
    return text[:80]
