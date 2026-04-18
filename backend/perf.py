from __future__ import annotations

import contextvars
import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PERF_LOG_PATH = PROJECT_ROOT / "artifacts/perf/request_timings.jsonl"
DEFAULT_RETRIEVAL_MODE = "hybrid"
DEFAULT_RERANK_TOP_N = 18
DEFAULT_QUERY_EMBED_CACHE_SIZE = 1024
REQUIRED_STAGE_NAMES = (
    "request_parse",
    "sparse_retrieval",
    "dense_embed",
    "dense_search_faiss",
    "fusion_rrf",
    "rerank_cross_encoder",
    "evidence_gating",
    "llm_generate",
    "response_build/serialize",
)

ENV_PERF_DISABLE_LLM = "PERF_DISABLE_LLM"
ENV_PERF_DISABLE_RERANK = "PERF_DISABLE_RERANK"
ENV_PERF_RETRIEVAL_MODE = "PERF_RETRIEVAL_MODE"
ENV_PERF_RERANK_TOP_N = "PERF_RERANK_TOP_N"
ENV_PERF_ENABLE_QUERY_EMBED_CACHE = "PERF_ENABLE_QUERY_EMBED_CACHE"
ENV_PERF_QUERY_EMBED_CACHE_SIZE = "PERF_QUERY_EMBED_CACHE_SIZE"
ENV_PERF_ENABLE_LLM_KEEPALIVE = "PERF_ENABLE_LLM_KEEPALIVE"
ENV_PERF_LOG_PATH = "PERF_LOG_PATH"

_CURRENT_TRACE: contextvars.ContextVar[RequestPerfTrace | None] = contextvars.ContextVar("request_perf_trace", default=None)
_PERF_LOG_LOCK = threading.Lock()


def env_flag_enabled(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(1, int(raw_value))
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    path = Path(raw_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


@dataclass(frozen=True)
class PerfSettings:
    disable_llm: bool
    disable_rerank: bool
    retrieval_mode: str
    rerank_top_n: int
    enable_query_embed_cache: bool
    query_embed_cache_size: int
    enable_llm_keepalive: bool
    log_path: Path


def load_perf_settings() -> PerfSettings:
    retrieval_mode = (os.getenv(ENV_PERF_RETRIEVAL_MODE, DEFAULT_RETRIEVAL_MODE) or DEFAULT_RETRIEVAL_MODE).strip().lower()
    if retrieval_mode not in {"hybrid", "sparse", "dense"}:
        retrieval_mode = DEFAULT_RETRIEVAL_MODE
    return PerfSettings(
        disable_llm=env_flag_enabled(os.getenv(ENV_PERF_DISABLE_LLM)),
        disable_rerank=env_flag_enabled(os.getenv(ENV_PERF_DISABLE_RERANK)),
        retrieval_mode=retrieval_mode,
        rerank_top_n=_env_int(ENV_PERF_RERANK_TOP_N, DEFAULT_RERANK_TOP_N),
        enable_query_embed_cache=env_flag_enabled(os.getenv(ENV_PERF_ENABLE_QUERY_EMBED_CACHE), default=True),
        query_embed_cache_size=_env_int(ENV_PERF_QUERY_EMBED_CACHE_SIZE, DEFAULT_QUERY_EMBED_CACHE_SIZE),
        enable_llm_keepalive=env_flag_enabled(os.getenv(ENV_PERF_ENABLE_LLM_KEEPALIVE), default=True),
        log_path=_env_path(ENV_PERF_LOG_PATH, DEFAULT_PERF_LOG_PATH),
    )


@dataclass
class RequestPerfTrace:
    request_id: str
    request_path: str
    query: str | None = None
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at_perf: float = field(default_factory=time.perf_counter)
    status_code: int | None = None
    stage_durations_ms: dict[str, float] = field(default_factory=dict)
    stage_counts: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def record_duration(self, stage_name: str, duration_seconds: float) -> None:
        duration_ms = round(duration_seconds * 1000.0, 3)
        with self._lock:
            self.stage_durations_ms[stage_name] = round(self.stage_durations_ms.get(stage_name, 0.0) + duration_ms, 3)
            self.stage_counts[stage_name] = self.stage_counts.get(stage_name, 0) + 1

    def set_metadata(self, key: str, value: Any) -> None:
        with self._lock:
            self.metadata[key] = value

    def total_ms(self) -> float:
        return round((time.perf_counter() - self.started_at_perf) * 1000.0, 3)

    def server_timing_value(self) -> str:
        entries = [f"total;dur={self.total_ms():.3f}"]
        for stage_name in REQUIRED_STAGE_NAMES:
            duration_ms = self.stage_durations_ms.get(stage_name)
            if duration_ms is None:
                continue
            metric_name = stage_name.replace("/", "_").replace("-", "_")
            entries.append(f"{metric_name};dur={duration_ms:.3f}")
        return ", ".join(entries)

    def to_log_record(self) -> dict[str, Any]:
        stages_ms = {stage_name: round(self.stage_durations_ms.get(stage_name, 0.0), 3) for stage_name in REQUIRED_STAGE_NAMES}
        extra_stage_names = sorted(set(self.stage_durations_ms) - set(REQUIRED_STAGE_NAMES))
        for stage_name in extra_stage_names:
            stages_ms[stage_name] = round(self.stage_durations_ms[stage_name], 3)
        return {
            "event": "request_perf",
            "request_id": self.request_id,
            "request_path": self.request_path,
            "created_at_utc": self.created_at_utc,
            "status_code": self.status_code,
            "query": self.query,
            "total_ms": self.total_ms(),
            "stages_ms": stages_ms,
            "stage_counts": dict(sorted(self.stage_counts.items())),
            "metadata": self.metadata,
        }


def new_request_trace(*, request_path: str, query: str | None = None) -> RequestPerfTrace:
    return RequestPerfTrace(
        request_id=uuid.uuid4().hex,
        request_path=request_path,
        query=query,
    )


def set_current_trace(trace: RequestPerfTrace) -> contextvars.Token[RequestPerfTrace | None]:
    return _CURRENT_TRACE.set(trace)


def reset_current_trace(token: contextvars.Token[RequestPerfTrace | None]) -> None:
    _CURRENT_TRACE.reset(token)


def current_trace() -> RequestPerfTrace | None:
    return _CURRENT_TRACE.get()


def current_request_id() -> str | None:
    trace = current_trace()
    if trace is None:
        return None
    return trace.request_id


def record_metadata(key: str, value: Any) -> None:
    trace = current_trace()
    if trace is None:
        return
    trace.set_metadata(key, value)


@contextmanager
def stage_timer(stage_name: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        trace = current_trace()
        if trace is not None:
            trace.record_duration(stage_name, time.perf_counter() - start)


def persist_request_log(record: dict[str, Any], *, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with _PERF_LOG_LOCK:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
