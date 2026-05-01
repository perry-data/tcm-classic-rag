from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping


_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class GeneralCanaryIdentity:
    request_id_hash: str = ""
    client_id_hash: str = ""
    query_hash: str = ""
    synthetic_subject_hash: str = ""

    @property
    def has_any_hash(self) -> bool:
        return any(
            [
                self.request_id_hash,
                self.client_id_hash,
                self.query_hash,
                self.synthetic_subject_hash,
            ]
        )


@dataclass(frozen=True)
class GeneralPercentParse:
    raw_value: str | None
    percent: float
    valid: bool
    absent: bool
    cap_violation: bool
    negative: bool
    reason: str = ""


def stable_hash(value: str | None) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def normalize_hash(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(candidate):
        return ""
    return candidate


def coerce_general_identity(value: GeneralCanaryIdentity | Mapping[str, Any] | None) -> GeneralCanaryIdentity:
    if isinstance(value, GeneralCanaryIdentity):
        return value
    if isinstance(value, Mapping):
        return GeneralCanaryIdentity(
            request_id_hash=normalize_hash(value.get("request_id_hash")),
            client_id_hash=normalize_hash(value.get("client_id_hash")),
            query_hash=normalize_hash(value.get("query_hash")),
            synthetic_subject_hash=normalize_hash(value.get("synthetic_subject_hash")),
        )
    return GeneralCanaryIdentity()


def select_general_subject_hash(
    identity: GeneralCanaryIdentity | Mapping[str, Any] | None,
    *,
    query_id: str | None = None,
    query: str | None = None,
) -> str:
    normalized = coerce_general_identity(identity)
    return (
        normalized.synthetic_subject_hash
        or normalized.request_id_hash
        or normalized.client_id_hash
        or normalized.query_hash
        or normalize_hash(query_id)
        or stable_hash(query_id or query or "")
    )


def parse_general_served_percent(raw_value: str | None, *, max_percent: float = 1.0) -> GeneralPercentParse:
    if raw_value is None or str(raw_value).strip() == "":
        return GeneralPercentParse(raw_value, 0.0, True, True, False, False, "absent_defaults_to_zero")
    text = str(raw_value).strip()
    try:
        percent = float(text)
    except ValueError:
        return GeneralPercentParse(raw_value, 0.0, False, False, False, False, "invalid_percent")
    if percent < 0:
        return GeneralPercentParse(raw_value, 0.0, False, False, False, True, "negative_percent")
    if percent > max_percent:
        return GeneralPercentParse(raw_value, percent, True, False, True, False, "percent_exceeds_cap")
    return GeneralPercentParse(raw_value, percent, True, False, False, False, "")


def general_canary_decision_hash(subject_hash: str, percent: float) -> str:
    return stable_hash(f"limited-general-canary:{subject_hash}:{percent:.6f}")


def general_canary_selected(subject_hash: str, percent: float) -> bool:
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    digest = hashlib.sha256(subject_hash.encode("utf-8")).hexdigest()
    # 10,000 buckets allow deterministic 0.1%, 0.5%, and 1% checks.
    bucket = int(digest[:8], 16) % 10000
    threshold = int(round(percent * 100))
    return bucket < threshold


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
        "medical_boundary_pass": True,
        "external_source_boundary_pass": True,
        "privacy_logging_pass": True,
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
