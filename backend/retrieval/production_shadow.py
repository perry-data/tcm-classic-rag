from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Mapping

from backend.retrieval.production_shadow_logger import append_shadow_log, build_shadow_log_record, stable_hash
from backend.retrieval.production_shadow_metrics import record_kill_switch_activation
from backend.retrieval.retrieval_router import (
    infer_query_type,
    route_config_from_env,
    run_v2_shadow_retrieval,
    select_retrieval_route,
)


def maybe_run_production_shadow(
    query: str,
    *,
    served_response_payload: Mapping[str, Any] | None = None,
    request_id: str | None = None,
    source_route: str = "runtime",
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    config = route_config_from_env(production_runtime_connected=True)
    decision = select_retrieval_route(config, query_id=stable_hash(query))
    route_metadata = decision.metadata()
    route_metadata["source_route"] = source_route
    query_type = infer_query_type(query)

    if route_metadata.get("kill_switch_active"):
        record_kill_switch_activation()

    should_log = (
        route_metadata.get("runtime_stage") == "production_shadow"
        or route_metadata.get("kill_switch_active")
        or route_metadata.get("shadow_sample_selected")
    )
    shadow_result: dict[str, Any] | None = None
    started = time.perf_counter()
    if decision.shadow_route == "v2":
        shadow_result, shadow_metadata = run_v2_shadow_retrieval(
            config,
            decision,
            query,
            query_type=query_type,
            top_k=5,
        )
        route_metadata.update(shadow_metadata)
        should_log = True

    latency_v1_ms = round((time.perf_counter() - started) * 1000, 3) if served_response_payload else None
    if should_log:
        record = build_shadow_log_record(
            query=query,
            query_type=query_type,
            route_metadata=route_metadata,
            served_result=served_response_payload,
            shadow_result=shadow_result,
            request_id=request_id,
            latency_v1_ms=latency_v1_ms,
        )
        append_shadow_log(record, path=log_path)

    return {
        "route_metadata": route_metadata,
        "shadow_result": shadow_result,
        "logged": should_log,
    }
