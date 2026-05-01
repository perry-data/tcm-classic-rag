from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from backend.retrieval.production_default_logger import (
    ALLOWED_LOG_FIELDS,
    append_production_default_log,
    build_production_default_log_record,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_POST_CUTOVER_LOG_PATH = "RAG_V2_POST_CUTOVER_LOG_PATH"
DEFAULT_POST_CUTOVER_LOG_PATH = (
    PROJECT_ROOT
    / "artifacts/data_reconstruction_v2/phase4_8_post_cutover_stabilization/runtime_logs_sanitized.jsonl"
)


def post_cutover_log_path(path_value: str | Path | None = None) -> Path:
    raw = path_value or os.environ.get(ENV_POST_CUTOVER_LOG_PATH) or DEFAULT_POST_CUTOVER_LOG_PATH
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def build_post_cutover_log_record(
    *,
    query: str,
    query_type: str,
    route_metadata: Mapping[str, Any],
    served_result: Mapping[str, Any] | None,
    request_id: str | None = None,
    latency_v1_ms: float | None = None,
    auto_stop_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return build_production_default_log_record(
        query=query,
        query_type=query_type,
        route_metadata=route_metadata,
        served_result=served_result,
        request_id=request_id,
        latency_v1_ms=latency_v1_ms,
        auto_stop_state=auto_stop_state,
    )


def append_post_cutover_log(record: Mapping[str, Any], *, path: str | Path | None = None) -> Path:
    return append_production_default_log(record, path=path or post_cutover_log_path())
