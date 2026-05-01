from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.perf import current_request_id, current_trace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QA_TRACE_DIR = PROJECT_ROOT / "logs" / "qa_traces"
ENV_QA_TRACE_DIR = "TCM_QA_TRACE_DIR"
ENV_QA_TRACE_ENABLED = "TCM_QA_TRACE_ENABLED"
DEFAULT_TOP_K = 5
SUMMARY_LIMIT = 120
FINAL_ANSWER_LIMIT = 2000
FORBIDDEN_PRIMARY_PREFIXES = (
    "full:passages:",
    "full:ambiguous_passages:",
)
TRACE_FIELDS = (
    "trace_id",
    "timestamp_utc",
    "query",
    "normalized_query",
    "answer_mode",
    "retrieval_method",
    "top_k_chunks",
    "primary_evidence_ids",
    "secondary_evidence_ids",
    "review_material_ids",
    "citations",
    "final_answer",
    "latency_ms",
    "stage_durations_ms",
    "model_name",
    "llm_used",
    "llm_answer_source",
    "fallback_used",
    "fallback_reason",
    "guard_triggered",
)

_LOGGER = logging.getLogger(__name__)
_WRITE_LOCK = threading.Lock()


def compact_text(text: Any) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split())


def clip_text(text: Any, *, limit: int) -> str:
    compact = compact_text(text)
    if len(compact) <= limit:
        return compact
    return compact[:limit]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def qa_trace_enabled() -> bool:
    raw = os.getenv(ENV_QA_TRACE_ENABLED)
    if raw is None:
        return True
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def resolve_trace_dir(log_dir: Path | str | None = None) -> Path:
    if log_dir is not None:
        path = Path(log_dir).expanduser()
    else:
        raw = os.getenv(ENV_QA_TRACE_DIR)
        path = Path(raw).expanduser() if raw else DEFAULT_QA_TRACE_DIR
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def trace_path_for_timestamp(timestamp_utc: str, *, log_dir: Path | str | None = None) -> Path:
    date_part = timestamp_utc[:10]
    return resolve_trace_dir(log_dir) / f"qa_trace_{date_part}.jsonl"


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _source_object(item: dict[str, Any]) -> str:
    value = item.get("source_object") or item.get("record_type")
    return str(value) if value else "unknown"


def _record_id(item: dict[str, Any]) -> str | None:
    value = item.get("record_id") or item.get("id")
    return str(value) if value else None


def _evidence_id_from_record_id(record_id: str | None) -> str | None:
    if not record_id:
        return None
    if ":" in record_id:
        return record_id.rsplit(":", 1)[-1] or None
    return record_id


def _summary_fields(item: dict[str, Any]) -> tuple[str | None, str | None]:
    source_object = _source_object(item)
    text = _first_present(
        item.get("retrieval_text"),
        item.get("text_preview"),
        item.get("snippet"),
        item.get("primary_evidence_text"),
    )
    summary = clip_text(text, limit=SUMMARY_LIMIT) if text else None
    if source_object == "annotations":
        return None, summary
    return summary, None


def _candidate_score(item: dict[str, Any]) -> float | int | None:
    score = _first_present(
        item.get("combined_score"),
        item.get("rrf_score"),
        item.get("sparse_score"),
        item.get("dense_score"),
        item.get("text_match_score"),
    )
    return score if isinstance(score, (int, float)) else None


def _rerank_score(item: dict[str, Any]) -> float | int | None:
    score = item.get("rerank_score")
    return score if isinstance(score, (int, float)) else None


def _primary_allowed(item: dict[str, Any]) -> bool:
    record_id = _record_id(item) or ""
    if record_id.startswith(FORBIDDEN_PRIMARY_PREFIXES):
        return False
    display_allowed = item.get("display_allowed")
    if display_allowed:
        return str(display_allowed) == "primary"
    if str(item.get("display_role") or "") == "primary":
        return True
    source_object = _source_object(item)
    return source_object in {"chunks", "main_passages", "formulas", "definition_terms"}


def candidate_to_top_k_item(item: dict[str, Any], *, rank: int) -> dict[str, Any]:
    record_id = _record_id(item)
    main_text_summary, annotation_summary = _summary_fields(item)
    return {
        "rank": rank,
        "chunk_id": _first_present(
            item.get("chunk_id"),
            item.get("passage_id"),
            item.get("formula_id"),
            item.get("concept_id"),
            _evidence_id_from_record_id(record_id),
        ),
        "record_id": record_id,
        "record_type": _source_object(item),
        "score": _candidate_score(item),
        "rerank_score": _rerank_score(item),
        "volume": _first_present(item.get("volume"), item.get("volume_title")),
        "chapter": _first_present(item.get("chapter_name"), item.get("chapter_title"), item.get("chapter_id")),
        "main_text_summary": main_text_summary,
        "annotation_summary": annotation_summary,
        "primary_allowed": _primary_allowed(item),
        "topic_consistency": str(item.get("topic_consistency") or "unknown"),
    }


def _select_retrieval(query: str, retrievals: dict[str, Any] | list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if isinstance(retrievals, dict):
        return retrievals
    if not retrievals:
        return None
    for retrieval in retrievals:
        request = retrieval.get("query_request") or {}
        if request.get("query_text") == query:
            return retrieval
    return retrievals[0]


def _top_k_from_retrieval(retrieval: dict[str, Any] | None, *, limit: int) -> list[dict[str, Any]]:
    if not retrieval:
        return []
    raw_candidates = retrieval.get("raw_candidates")
    if isinstance(raw_candidates, list) and raw_candidates:
        return [candidate_to_top_k_item(row, rank=index) for index, row in enumerate(raw_candidates[:limit], start=1)]
    candidates: list[dict[str, Any]] = []
    for slot_name in ("primary_evidence", "secondary_evidence", "risk_materials"):
        slot_rows = retrieval.get(slot_name)
        if isinstance(slot_rows, list):
            candidates.extend(row for row in slot_rows if isinstance(row, dict))
    return [candidate_to_top_k_item(row, rank=index) for index, row in enumerate(candidates[:limit], start=1)]


def _top_k_from_payload(payload: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for slot_name in ("primary_evidence", "secondary_evidence", "review_materials"):
        for item in payload.get(slot_name) or []:
            if isinstance(item, dict):
                candidates.append(item)
    return [candidate_to_top_k_item(row, rank=index) for index, row in enumerate(candidates[:limit], start=1)]


def _normalized_query(query: str, retrieval: dict[str, Any] | None) -> str | None:
    request = (retrieval or {}).get("query_request") or {}
    normalized = request.get("query_text_normalized")
    if normalized:
        return str(normalized)
    query_text = request.get("query_text")
    if query_text and query_text != query:
        return str(query_text)
    return None


def _retrieval_method(retrieval: dict[str, Any] | None, top_k_chunks: list[dict[str, Any]], payload: dict[str, Any]) -> str:
    record_ids = [str(item.get("record_id") or "") for item in top_k_chunks]
    record_types = {str(item.get("record_type") or "") for item in top_k_chunks}
    if any(record_id.startswith("formula:") for record_id in record_ids) or "formulas" in record_types:
        return "formula_object"
    if any(record_id.startswith("safe:definition_terms:") for record_id in record_ids) or "definition_terms" in record_types:
        return "definition_object"
    if retrieval:
        trace = retrieval.get("retrieval_trace") or {}
        perf_flags = trace.get("perf_flags") or {}
        retrieval_mode = str(perf_flags.get("retrieval_mode") or "").lower()
        if retrieval_mode == "sparse":
            return "sparse"
        if retrieval_mode == "dense":
            return "hybrid"
        if perf_flags.get("disable_rerank") is True:
            return "hybrid"
        return "hybrid+rerank"
    if top_k_chunks:
        return "guarded_baseline"
    if payload.get("answer_mode") == "refuse":
        return "guarded_baseline"
    return "unknown"


def _slot_ids(payload: dict[str, Any], slot_name: str) -> list[str]:
    ids: list[str] = []
    for item in payload.get(slot_name) or []:
        if isinstance(item, dict) and item.get("record_id"):
            ids.append(str(item["record_id"]))
    return ids


def _citation_slot_maps(payload: dict[str, Any]) -> dict[str, str]:
    slot_by_id: dict[str, str] = {}
    for slot_name, source_slot in (
        ("primary_evidence", "primary"),
        ("secondary_evidence", "secondary"),
        ("review_materials", "review"),
    ):
        for item in payload.get(slot_name) or []:
            if isinstance(item, dict) and item.get("record_id"):
                slot_by_id[str(item["record_id"])] = source_slot
    return slot_by_id


def _citations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    slot_by_id = _citation_slot_maps(payload)
    citations: list[dict[str, Any]] = []
    for citation in payload.get("citations") or []:
        if not isinstance(citation, dict):
            continue
        record_id = _record_id(citation)
        citations.append(
            {
                "chunk_id": record_id,
                "source_slot": str(citation.get("citation_role") or slot_by_id.get(record_id or "", "unknown")),
            }
        )
    return citations


def _stage_durations_ms() -> dict[str, Any]:
    trace = current_trace()
    if trace is None:
        return {}
    return dict(trace.stage_durations_ms)


def _guard_triggered(payload: dict[str, Any], llm_debug: dict[str, Any] | None) -> str | None:
    skipped_reason = (llm_debug or {}).get("skipped_reason")
    if skipped_reason in {"p0_boundary_guard", "p1_conservative_learner_guard"}:
        return str(skipped_reason)
    for slot_name in ("primary_evidence", "secondary_evidence", "review_materials"):
        for item in payload.get(slot_name) or []:
            for flag in item.get("risk_flags") or []:
                if str(flag) in {"p0_boundary_guard", "p1_conservative_learner_guard"}:
                    return str(flag)
    return None


def build_qa_trace_record(
    *,
    query: str,
    payload: dict[str, Any],
    retrievals: dict[str, Any] | list[dict[str, Any]] | None = None,
    llm_debug: dict[str, Any] | None = None,
    started_at_perf: float | None = None,
    model_name: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    timestamp = utc_timestamp()
    retrieval = _select_retrieval(query, retrievals)
    top_k_chunks = _top_k_from_retrieval(retrieval, limit=top_k) or _top_k_from_payload(payload, limit=top_k)
    debug = dict(llm_debug or {})
    fallback_reason = debug.get("fallback_reason") or debug.get("skipped_reason")
    final_answer = clip_text(payload.get("answer_text"), limit=FINAL_ANSWER_LIMIT)
    if not final_answer:
        final_answer = clip_text(payload.get("refuse_reason") or "refuse", limit=FINAL_ANSWER_LIMIT)
    request_id = current_request_id()
    latency_ms = round((time.perf_counter() - started_at_perf) * 1000.0, 3) if started_at_perf else 0
    record = {
        "trace_id": request_id or uuid.uuid4().hex,
        "timestamp_utc": timestamp,
        "query": query,
        "normalized_query": _normalized_query(query, retrieval),
        "answer_mode": str(payload.get("answer_mode") or "unknown"),
        "retrieval_method": _retrieval_method(retrieval, top_k_chunks, payload),
        "top_k_chunks": top_k_chunks,
        "primary_evidence_ids": _slot_ids(payload, "primary_evidence"),
        "secondary_evidence_ids": _slot_ids(payload, "secondary_evidence"),
        "review_material_ids": _slot_ids(payload, "review_materials"),
        "citations": _citations(payload),
        "final_answer": final_answer,
        "latency_ms": latency_ms,
        "stage_durations_ms": _stage_durations_ms(),
        "model_name": debug.get("model") or model_name,
        "llm_used": bool(debug.get("used_llm")),
        "llm_answer_source": str(debug.get("answer_source") or "unknown"),
        "fallback_used": bool(debug.get("fallback_used")),
        "fallback_reason": str(fallback_reason) if fallback_reason else None,
        "guard_triggered": _guard_triggered(payload, debug),
    }
    return {field: record.get(field) for field in TRACE_FIELDS}


def write_qa_trace_record(record: dict[str, Any], *, log_dir: Path | str | None = None) -> Path:
    path = trace_path_for_timestamp(str(record.get("timestamp_utc") or utc_timestamp()), log_dir=log_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({field: record.get(field) for field in TRACE_FIELDS}, ensure_ascii=False, sort_keys=True)
    with _WRITE_LOCK:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return path


def write_qa_trace_safely(
    *,
    query: str,
    payload: dict[str, Any],
    retrievals: dict[str, Any] | list[dict[str, Any]] | None = None,
    llm_debug: dict[str, Any] | None = None,
    started_at_perf: float | None = None,
    model_name: str | None = None,
    log_dir: Path | str | None = None,
) -> Path | None:
    if not qa_trace_enabled():
        return None
    try:
        record = build_qa_trace_record(
            query=query,
            payload=payload,
            retrievals=retrievals,
            llm_debug=llm_debug,
            started_at_perf=started_at_perf,
            model_name=model_name,
        )
        return write_qa_trace_record(record, log_dir=log_dir)
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.warning("qa trace write failed: %s", exc)
        return None
