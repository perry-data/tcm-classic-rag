from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping


HEADER_INTERNAL_USER_HASH = "X-RAG-Internal-Canary-User-Hash"
HEADER_INTERNAL_REQUEST_HASH = "X-RAG-Internal-Canary-Request-Hash"
HEADER_INTERNAL_QUERY_ID_HASH = "X-RAG-Internal-Canary-Query-Id-Hash"
HEADER_SYNTHETIC_CANARY_ID_HASH = "X-RAG-Synthetic-Canary-Id-Hash"

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class InternalCanaryIdentity:
    internal_user_hash: str = ""
    internal_request_hash: str = ""
    internal_query_id_hash: str = ""
    synthetic_canary_id_hash: str = ""

    @property
    def has_any_hash(self) -> bool:
        return any(
            [
                self.internal_user_hash,
                self.internal_request_hash,
                self.internal_query_id_hash,
                self.synthetic_canary_id_hash,
            ]
        )


@dataclass(frozen=True)
class InternalAllowlistMatch:
    matched: bool
    match_type: str = ""
    subject_hash: str = ""


def stable_hash(value: str | None) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def normalize_hash(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(candidate):
        return ""
    return candidate


def parse_allowlist_hashes(value: str | None) -> tuple[str, ...]:
    hashes: list[str] = []
    for item in str(value or "").split(","):
        normalized = normalize_hash(item)
        if normalized and normalized not in hashes:
            hashes.append(normalized)
    return tuple(hashes)


def identity_from_mapping(headers: Mapping[str, Any] | None) -> InternalCanaryIdentity:
    if headers is None:
        return InternalCanaryIdentity()

    def get_header(name: str) -> str:
        value = headers.get(name)
        if value is None:
            value = headers.get(name.lower())
        return normalize_hash(value)

    return InternalCanaryIdentity(
        internal_user_hash=get_header(HEADER_INTERNAL_USER_HASH),
        internal_request_hash=get_header(HEADER_INTERNAL_REQUEST_HASH),
        internal_query_id_hash=get_header(HEADER_INTERNAL_QUERY_ID_HASH),
        synthetic_canary_id_hash=get_header(HEADER_SYNTHETIC_CANARY_ID_HASH),
    )


def coerce_identity(value: InternalCanaryIdentity | Mapping[str, Any] | None) -> InternalCanaryIdentity:
    if isinstance(value, InternalCanaryIdentity):
        return value
    if isinstance(value, Mapping):
        return InternalCanaryIdentity(
            internal_user_hash=normalize_hash(value.get("internal_user_hash")),
            internal_request_hash=normalize_hash(value.get("internal_request_hash")),
            internal_query_id_hash=normalize_hash(value.get("internal_query_id_hash")),
            synthetic_canary_id_hash=normalize_hash(value.get("synthetic_canary_id_hash")),
        )
    return InternalCanaryIdentity()


def match_internal_allowlist(
    identity: InternalCanaryIdentity | Mapping[str, Any] | None,
    *,
    user_hashes: tuple[str, ...] = (),
    request_hashes: tuple[str, ...] = (),
    query_id_hashes: tuple[str, ...] = (),
) -> InternalAllowlistMatch:
    normalized = coerce_identity(identity)
    if normalized.internal_user_hash and normalized.internal_user_hash in set(user_hashes):
        return InternalAllowlistMatch(True, "internal_user_hash", normalized.internal_user_hash)
    if normalized.internal_request_hash and normalized.internal_request_hash in set(request_hashes):
        return InternalAllowlistMatch(True, "internal_request_hash", normalized.internal_request_hash)
    if normalized.internal_query_id_hash and normalized.internal_query_id_hash in set(query_id_hashes):
        return InternalAllowlistMatch(True, "internal_query_id_hash", normalized.internal_query_id_hash)
    if normalized.synthetic_canary_id_hash and normalized.synthetic_canary_id_hash in set(request_hashes):
        return InternalAllowlistMatch(True, "synthetic_canary_id_hash", normalized.synthetic_canary_id_hash)
    return InternalAllowlistMatch(False)


def evidence_contract_fields(result: Mapping[str, Any] | None) -> dict[str, Any]:
    evidence = [item for item in (result or {}).get("top_evidence", []) if isinstance(item, Mapping)]
    lane_counts: dict[str, int] = {}
    for item in evidence:
        lane = str(item.get("lane") or "")
        if lane:
            lane_counts[lane] = lane_counts.get(lane, 0) + 1
    return {
        "final_response_uses_v2_evidence": bool(evidence),
        "source_citation_fields_present": _source_fields_present(evidence),
        "evidence_lane_counts": lane_counts,
        "top_evidence_object_ids": [str(item.get("object_id") or "") for item in evidence[:5] if item.get("object_id")],
        "top_evidence_source_ids": [str(item.get("source_id") or "") for item in evidence[:5] if item.get("source_id")],
        "top_evidence_doc_types": [str(item.get("doc_type") or "") for item in evidence[:5] if item.get("doc_type")],
        "top_evidence_lanes": [str(item.get("lane") or "") for item in evidence[:5] if item.get("lane")],
        "boundary_pass": bool((result or {}).get("boundary_pass", True)),
        "failure_reason": str((result or {}).get("failure_reason") or ""),
    }


def _source_fields_present(evidence: list[Mapping[str, Any]]) -> bool:
    if not evidence:
        return True
    for item in evidence:
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
