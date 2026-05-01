#!/usr/bin/env python3
"""Audit citation_not_from_top_k rows from existing eval artifacts only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "citation_topk_mismatch_audit_v1"

DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_RETRIEVAL_JSON = REPO_ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
DEFAULT_ANSWER_JSON = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
DEFAULT_TRACE_LOG = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "qa_trace_answer_eval_v1.jsonl"
DEFAULT_FAILURE_JSON = REPO_ROOT / "artifacts" / "eval" / "failure_report_v1" / "failure_cases_v1.json"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

TARGET_FAILURE_TYPE = "citation_not_from_top_k"

ROOT_CAUSES = {
    "trace_topk_missing_equivalence",
    "formula_or_definition_source_expansion",
    "answer_uses_secondary_or_review_not_in_topk",
    "trace_logging_gap",
    "evaluator_id_equivalence_gap",
    "real_citation_assembly_issue",
    "manual_audit_required",
}

ACTION_BY_ROOT_CAUSE = {
    "trace_topk_missing_equivalence": "fix_trace_logging",
    "formula_or_definition_source_expansion": "allow_formula_source_expansion_in_eval",
    "answer_uses_secondary_or_review_not_in_topk": "inspect_secondary_review_citation_policy",
    "trace_logging_gap": "fix_trace_logging",
    "evaluator_id_equivalence_gap": "fix_evaluator_id_equivalence",
    "real_citation_assembly_issue": "fix_answer_assembly_citation_scope",
    "manual_audit_required": "manual_audit_required",
}

EVALUATOR_OR_TRACE_ROOT_CAUSES = {
    "trace_topk_missing_equivalence",
    "formula_or_definition_source_expansion",
    "trace_logging_gap",
    "evaluator_id_equivalence_gap",
}
OBJECT_RECORD_TABLES = {"retrieval_ready_formula_view", "retrieval_ready_definition_view"}
SECONDARY_REVIEW_SLOTS = {"secondary", "review"}


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def split_pipe(value: str | None) -> list[str]:
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, Any]] = []
        for row in reader:
            rows.append(
                {
                    "id": (row.get("id") or "").strip(),
                    "category": (row.get("category") or "").strip(),
                    "question": (row.get("question") or "").strip(),
                    "gold_chunk_ids": split_pipe(row.get("gold_chunk_ids")),
                    "should_answer": parse_bool(row.get("should_answer")),
                    "expected_answer_mode": (row.get("expected_answer_mode") or "").strip(),
                    "manual_audit_required": parse_bool(row.get("manual_audit_required")),
                    "subtype": (row.get("subtype") or "").strip(),
                    "notes": (row.get("notes") or "").strip(),
                }
            )
    return rows


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_trace_log(trace_log: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(trace_log.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL row {line_number} in {display_path(trace_log)}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"trace row {line_number} is not an object")
        records.append(record)
    return records


def index_by_id(rows: Iterable[dict[str, Any]], *, source_name: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id:
            raise ValueError(f"{source_name} has a row without id")
        if row_id in result:
            raise ValueError(f"{source_name} has duplicate id: {row_id}")
        result[row_id] = row
    return result


def order_trace_records(
    dataset_rows: list[dict[str, Any]],
    trace_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    records_by_query: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for record in trace_records:
        records_by_query[str(record.get("query") or "")].append(record)

    ordered: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for row in dataset_rows:
        queue = records_by_query.get(row["question"])
        if not queue:
            missing.append(f"{row['id']}:{row['question']}")
            continue
        ordered[row["id"]] = queue.popleft()
    if missing:
        raise ValueError("missing qa_trace rows for examples: " + "; ".join(missing))
    return ordered


def validate_source_alignment(
    dataset_rows: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
    answer_payload: dict[str, Any],
    failure_payload: dict[str, Any],
    trace_by_id: dict[str, dict[str, Any]],
) -> None:
    dataset_ids = [row["id"] for row in dataset_rows]
    retrieval_ids = [str(row.get("id") or "") for row in retrieval_payload.get("per_example") or []]
    answer_ids = [str(row.get("id") or "") for row in answer_payload.get("per_example") or []]
    failure_ids = [str(row.get("id") or "") for row in failure_payload.get("per_example") or []]
    if dataset_ids != retrieval_ids:
        raise ValueError("dataset and retrieval_eval per_example ids are not aligned")
    if dataset_ids != answer_ids:
        raise ValueError("dataset and answer_eval per_example ids are not aligned")
    if dataset_ids != failure_ids:
        raise ValueError("dataset and failure_report per_example ids are not aligned")
    if dataset_ids != list(trace_by_id):
        raise ValueError("dataset and trace log ids are not aligned")


def id_variants(value: str | None) -> set[str]:
    if not value:
        return set()
    raw = str(value).strip()
    if not raw:
        return set()

    variants = {raw}
    if raw.startswith("safe:main_passages:"):
        bare = raw.rsplit(":", 1)[-1]
        variants.update({bare, f"full:passages:{bare}"})
    elif raw.startswith("full:passages:"):
        bare = raw.rsplit(":", 1)[-1]
        variants.update({bare, f"safe:main_passages:{bare}"})
    elif raw.startswith("safe:chunks:"):
        variants.add(raw.rsplit(":", 1)[-1])
    elif raw.startswith("safe:definition_terms:"):
        variants.add(raw.rsplit(":", 1)[-1])
    elif raw.startswith("formula:"):
        variants.add(raw.split(":", 1)[1])
    elif raw.startswith("FML-"):
        variants.add(f"formula:{raw}")
    elif "-CK-" in raw:
        variants.add(f"safe:chunks:{raw}")
    elif "-P-" in raw:
        variants.update({f"safe:main_passages:{raw}", f"full:passages:{raw}"})
    return variants


def match_ranks(value: str, matchable_lists: list[list[str]]) -> list[int]:
    variants = id_variants(value)
    return [
        index
        for index, matchable_ids in enumerate(matchable_lists, start=1)
        if variants & set(str(item) for item in matchable_ids)
    ]


def trace_top_k_record_ids(record: dict[str, Any]) -> list[str]:
    return [
        str(item.get("record_id") or "")
        for item in (record.get("top_k_chunks") or [])[:5]
        if isinstance(item, dict)
    ]


def trace_top_k_chunk_ids(record: dict[str, Any]) -> list[str]:
    return [
        str(item.get("chunk_id") or "")
        for item in (record.get("top_k_chunks") or [])[:5]
        if isinstance(item, dict)
    ]


def exact_or_variant_match(value: str, record_ids: list[str], chunk_ids: list[str]) -> bool:
    variants = id_variants(value)
    candidate_ids: set[str] = set()
    for item in [*record_ids, *chunk_ids]:
        candidate_ids.update(id_variants(item))
    return bool(variants & candidate_ids)


def citation_family(value: str) -> str:
    if value.startswith("full:annotations:"):
        return "annotation"
    if value.startswith("full:ambiguous_passages:"):
        return "ambiguous_passage"
    if ":passages:" in value or "-P-" in value:
        return "passage"
    if ":chunks:" in value or "-CK-" in value:
        return "chunk"
    if value.startswith(("formula:", "FML-")):
        return "formula"
    if value.startswith("safe:definition_terms:"):
        return "definition_term"
    return "other"


def evidence_slot_membership(value: str, trace_record: dict[str, Any]) -> list[str]:
    variants = id_variants(value)
    memberships: list[str] = []
    for slot_name, trace_key in [
        ("primary", "primary_evidence_ids"),
        ("secondary", "secondary_evidence_ids"),
        ("review", "review_material_ids"),
    ]:
        slot_ids: set[str] = set()
        for item in trace_record.get(trace_key) or []:
            slot_ids.update(id_variants(str(item)))
        if variants & slot_ids:
            memberships.append(slot_name)
    return memberships


def retrieval_candidate_matches(
    citation_id: str,
    retrieval_row: dict[str, Any],
) -> list[dict[str, Any]]:
    variants = id_variants(citation_id)
    matches: list[dict[str, Any]] = []
    for rank, candidate in enumerate(retrieval_row.get("top5_candidates") or [], start=1):
        matchable_ids = set(str(item) for item in candidate.get("matchable_ids") or [])
        if not variants & matchable_ids:
            continue
        record_id = str(candidate.get("record_id") or "")
        source_record_id = str(candidate.get("source_record_id") or "")
        exact_match = exact_or_variant_match(citation_id, [record_id], [source_record_id])
        record_table = str(candidate.get("record_table") or "")
        matches.append(
            {
                "rank": rank,
                "record_id": record_id,
                "record_table": record_table,
                "source_object": candidate.get("source_object"),
                "exact_or_id_variant_match": exact_match,
                "object_source_expansion_match": record_table in OBJECT_RECORD_TABLES and not exact_match,
            }
        )
    return matches


def audit_citations(
    answer_row: dict[str, Any],
    retrieval_row: dict[str, Any],
    trace_record: dict[str, Any],
) -> list[dict[str, Any]]:
    citation_ids = [str(item) for item in answer_row.get("citation_ids") or []]
    citation_slots = [str(item) for item in answer_row.get("citation_source_slots") or []]
    answer_matchable = answer_row.get("top5_matchable_ids") or []
    retrieval_matchable = retrieval_row.get("top5_matchable_ids") or []
    trace_record_ids = trace_top_k_record_ids(trace_record)
    trace_chunk_ids = trace_top_k_chunk_ids(trace_record)
    retrieval_record_ids = [str(item) for item in retrieval_row.get("top5_record_ids") or []]
    retrieval_chunk_ids = [
        str(candidate.get("source_record_id") or "")
        for candidate in retrieval_row.get("top5_candidates") or []
    ]

    audited: list[dict[str, Any]] = []
    for index, citation_id in enumerate(citation_ids):
        source_slot = citation_slots[index] if index < len(citation_slots) else "unknown"
        existing_ranks = match_ranks(citation_id, answer_matchable)
        retrieval_ranks = match_ranks(citation_id, retrieval_matchable)
        candidate_matches = retrieval_candidate_matches(citation_id, retrieval_row)
        audited.append(
            {
                "index": index + 1,
                "citation_id": citation_id,
                "citation_family": citation_family(citation_id),
                "source_slot": source_slot,
                "evidence_slot_membership": evidence_slot_membership(citation_id, trace_record),
                "existing_equivalence_top5_match_ranks": existing_ranks,
                "retrieval_equivalence_top5_match_ranks": retrieval_ranks,
                "matched_by_existing_equivalence": bool(existing_ranks),
                "matched_by_retrieval_equivalence": bool(retrieval_ranks),
                "retrieval_match_missing_from_existing_equivalence": bool(retrieval_ranks) and not existing_ranks,
                "exact_or_variant_in_trace_topk_ids": exact_or_variant_match(
                    citation_id, trace_record_ids, trace_chunk_ids
                ),
                "exact_or_variant_in_retrieval_top5_ids": exact_or_variant_match(
                    citation_id, retrieval_record_ids, retrieval_chunk_ids
                ),
                "matched_retrieval_top5_candidates": candidate_matches,
                "object_source_expansion_match": any(
                    match["object_source_expansion_match"] for match in candidate_matches
                ),
            }
        )
    return audited


def derive_root_cause(
    *,
    answer_mode: str,
    citations: list[dict[str, Any]],
    trace_records_match_retrieval: bool,
) -> tuple[str, bool, str, str]:
    if not citations:
        return (
            "manual_audit_required",
            False,
            ACTION_BY_ROOT_CAUSE["manual_audit_required"],
            "No citation ids are available in answer_eval for this flagged row.",
        )

    missing_existing = [
        citation for citation in citations if not citation["matched_by_existing_equivalence"]
    ]
    missing_retrieval = [
        citation for citation in citations if not citation["matched_by_retrieval_equivalence"]
    ]
    retrieval_not_existing = [
        citation for citation in citations if citation["retrieval_match_missing_from_existing_equivalence"]
    ]
    primary_outside = [
        citation for citation in missing_retrieval if citation["source_slot"] == "primary"
    ]
    secondary_review_outside = [
        citation for citation in missing_retrieval if citation["source_slot"] in SECONDARY_REVIEW_SLOTS
    ]
    object_expansion = [citation for citation in citations if citation["object_source_expansion_match"]]
    not_in_trace_evidence_slots = [
        citation for citation in missing_existing if not citation["evidence_slot_membership"]
    ]

    if primary_outside:
        root_cause = "real_citation_assembly_issue"
        return (
            root_cause,
            True,
            ACTION_BY_ROOT_CAUSE[root_cause],
            "Primary citation ids are outside retrieval_eval top5 equivalence; this is the strongest runtime citation-scope signal.",
        )

    if secondary_review_outside:
        root_cause = "answer_uses_secondary_or_review_not_in_topk"
        is_runtime_bug = answer_mode == "strong"
        action = "fix_answer_assembly_citation_scope" if is_runtime_bug else ACTION_BY_ROOT_CAUSE[root_cause]
        return (
            root_cause,
            is_runtime_bug,
            action,
            "Citation ids come from secondary/review slots outside retrieval top5; weak/review rows should be policy-audited before repair.",
        )

    if retrieval_not_existing:
        root_cause = "trace_topk_missing_equivalence"
        return (
            root_cause,
            False,
            ACTION_BY_ROOT_CAUSE[root_cause],
            "retrieval_eval top5 matchable ids cover the citation, but answer_eval trace-topk equivalence does not.",
        )

    if object_expansion:
        root_cause = "formula_or_definition_source_expansion"
        return (
            root_cause,
            False,
            ACTION_BY_ROOT_CAUSE[root_cause],
            "Citation ids are source passages behind formula/definition top5 objects.",
        )

    if not_in_trace_evidence_slots:
        root_cause = "trace_logging_gap"
        return (
            root_cause,
            False,
            ACTION_BY_ROOT_CAUSE[root_cause],
            "Citation ids are not visible in trace evidence slots, so the trace is insufficient for audit.",
        )

    if missing_existing and not trace_records_match_retrieval:
        root_cause = "trace_logging_gap"
        return (
            root_cause,
            False,
            ACTION_BY_ROOT_CAUSE[root_cause],
            "Trace top_k ids disagree with retrieval_eval top5 for this query.",
        )

    if missing_existing:
        root_cause = "evaluator_id_equivalence_gap"
        return (
            root_cause,
            False,
            ACTION_BY_ROOT_CAUSE[root_cause],
            "Citation ids and retrieved ids look structurally equivalent, but the current evaluator rule did not match them.",
        )

    root_cause = "manual_audit_required"
    return (
        root_cause,
        False,
        ACTION_BY_ROOT_CAUSE[root_cause],
        "The row is flagged by failure_report, but artifact comparisons do not isolate a single automatic cause.",
    )


def audit_example(
    dataset_row: dict[str, Any],
    failure_row: dict[str, Any],
    retrieval_row: dict[str, Any],
    answer_row: dict[str, Any],
    trace_record: dict[str, Any],
) -> dict[str, Any]:
    trace_record_ids = trace_top_k_record_ids(trace_record)
    retrieval_record_ids = [str(item) for item in retrieval_row.get("top5_record_ids") or []]
    citations = audit_citations(answer_row, retrieval_row, trace_record)
    answer_mode = str(failure_row.get("answer_mode") or answer_row.get("actual_answer_mode") or "unknown")
    trace_records_match_retrieval = trace_record_ids == retrieval_record_ids
    root_cause, is_runtime_bug, recommended_next_action, root_note = derive_root_cause(
        answer_mode=answer_mode,
        citations=citations,
        trace_records_match_retrieval=trace_records_match_retrieval,
    )

    matched_existing = [
        citation["citation_id"] for citation in citations if citation["matched_by_existing_equivalence"]
    ]
    unmatched_existing = [
        citation["citation_id"] for citation in citations if not citation["matched_by_existing_equivalence"]
    ]
    matched_retrieval = [
        citation["citation_id"] for citation in citations if citation["matched_by_retrieval_equivalence"]
    ]
    unmatched_retrieval = [
        citation["citation_id"] for citation in citations if not citation["matched_by_retrieval_equivalence"]
    ]
    object_expansion_ids = [
        citation["citation_id"] for citation in citations if citation["object_source_expansion_match"]
    ]
    secondary_review_outside_ids = [
        citation["citation_id"]
        for citation in citations
        if citation["source_slot"] in SECONDARY_REVIEW_SLOTS
        and not citation["matched_by_retrieval_equivalence"]
    ]
    primary_outside_ids = [
        citation["citation_id"]
        for citation in citations
        if citation["source_slot"] == "primary"
        and not citation["matched_by_retrieval_equivalence"]
    ]

    notes = [
        root_note,
        f"trace_top_k_record_ids_match_retrieval_eval={str(trace_records_match_retrieval).lower()}",
        f"existing_equivalence_match={len(matched_existing)}/{len(citations)}",
        f"retrieval_equivalence_match={len(matched_retrieval)}/{len(citations)}",
    ]
    if object_expansion_ids:
        notes.append("object_source_expansion_ids=" + ",".join(object_expansion_ids))
    if secondary_review_outside_ids:
        notes.append("secondary_or_review_outside_top5_ids=" + ",".join(secondary_review_outside_ids))
    if primary_outside_ids:
        notes.append("primary_outside_top5_ids=" + ",".join(primary_outside_ids))
    if answer_row.get("notes"):
        notes.append("answer_eval_notes=" + str(answer_row["notes"]))

    return {
        "id": dataset_row["id"],
        "category": dataset_row["category"],
        "question": dataset_row["question"],
        "answer_mode": answer_mode,
        "citation_ids": [citation["citation_id"] for citation in citations],
        "citation_source_slots": [citation["source_slot"] for citation in citations],
        "trace_top_k_record_ids": trace_record_ids,
        "retrieval_top5_record_ids": retrieval_record_ids,
        "gold_chunk_ids": dataset_row["gold_chunk_ids"],
        "matched_by_existing_equivalence": matched_existing,
        "matched_by_retrieval_equivalence": matched_retrieval,
        "unmatched_citation_ids": unmatched_existing,
        "unmatched_after_retrieval_equivalence": unmatched_retrieval,
        "object_source_expansion_citation_ids": object_expansion_ids,
        "secondary_or_review_not_in_topk_citation_ids": secondary_review_outside_ids,
        "primary_not_in_topk_citation_ids": primary_outside_ids,
        "trace_top_k_record_ids_match_retrieval_eval": trace_records_match_retrieval,
        "root_cause": root_cause,
        "is_runtime_bug": is_runtime_bug,
        "recommended_next_action": recommended_next_action,
        "notes": " | ".join(notes),
        "citation_audit": citations,
    }


def count_roots(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(row["root_cause"] for row in rows)


def aggregate_payload(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    answer_json: Path,
    trace_log: Path,
    failure_json: Path,
    per_example: list[dict[str, Any]],
) -> dict[str, Any]:
    root_cause_counts = count_roots(per_example)
    action_counts = Counter(row["recommended_next_action"] for row in per_example)
    runtime_bug_count = sum(1 for row in per_example if row["is_runtime_bug"])
    evaluator_or_trace_issue_count = sum(
        1 for row in per_example if row["root_cause"] in EVALUATOR_OR_TRACE_ROOT_CAUSES
    )
    manual_count = root_cause_counts["manual_audit_required"]
    trace_record_mismatch_rows = sum(
        1 for row in per_example if not row["trace_top_k_record_ids_match_retrieval_eval"]
    )
    trace_missing_equivalence_rows = root_cause_counts["trace_topk_missing_equivalence"]
    object_expansion_rows = sum(1 for row in per_example if row["object_source_expansion_citation_ids"])
    secondary_review_outside_rows = root_cause_counts["answer_uses_secondary_or_review_not_in_topk"]
    primary_outside_rows = sum(1 for row in per_example if row["primary_not_in_topk_citation_ids"])
    retrieval_but_not_existing_count = sum(
        1
        for row in per_example
        for citation in row["citation_audit"]
        if citation["retrieval_match_missing_from_existing_equivalence"]
    )

    source_paths = {
        "eval_dataset_v1": dataset_path,
        "retrieval_eval_v1": retrieval_json,
        "answer_eval_v1": answer_json,
        "qa_trace_answer_eval_v1": trace_log,
        "failure_report_v1": failure_json,
    }

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_failure_report": display_path(failure_json),
        "source_artifacts": {name: display_path(path) for name, path in source_paths.items()},
        "source_sha256": {name: sha256_file(path) for name, path in source_paths.items()},
        "audit_scope": {
            "failure_type": TARGET_FAILURE_TYPE,
            "source_artifacts_only": True,
            "runs_retrieval": False,
            "runs_answer_generation": False,
            "llm_judge": False,
            "includes_p2_diagnostic": False,
        },
        "total_citation_not_from_topk": len(per_example),
        "root_cause_counts": dict(sorted(root_cause_counts.items())),
        "runtime_bug_count": runtime_bug_count,
        "evaluator_or_trace_issue_count": evaluator_or_trace_issue_count,
        "manual_audit_required_count": manual_count,
        "audit_findings": {
            "trace_top_k_chunks_record_id_mismatch_rows": trace_record_mismatch_rows,
            "trace_topk_missing_equivalence_rows": trace_missing_equivalence_rows,
            "retrieval_but_not_existing_equivalence_citation_count": retrieval_but_not_existing_count,
            "formula_or_definition_source_expansion_rows": object_expansion_rows,
            "answer_uses_secondary_or_review_not_in_topk_rows": secondary_review_outside_rows,
            "primary_citation_not_in_topk_rows": primary_outside_rows,
            "real_runtime_bug_rows": runtime_bug_count,
        },
        "recommended_next_action_counts": dict(sorted(action_counts.items())),
        "per_example": per_example,
    }


def md_escape(value: Any) -> str:
    text = " ".join(str(value if value is not None else "").split())
    return text.replace("|", "\\|")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(item) for item in row) + " |")
    return "\n".join(lines)


def count_table(counter: dict[str, int]) -> str:
    return md_table(["key", "count"], [[key, value] for key, value in sorted(counter.items())])


def rows_for_action(payload: dict[str, Any], action: str) -> list[dict[str, Any]]:
    return [row for row in payload["per_example"] if row["recommended_next_action"] == action]


def render_markdown(payload: dict[str, Any]) -> str:
    rows = payload["per_example"]
    audit_rows = [
        [
            row["id"],
            row["category"],
            row["question"],
            row["answer_mode"],
            row["root_cause"],
            row["is_runtime_bug"],
            row["recommended_next_action"],
            f"{len(row['matched_by_existing_equivalence'])}/{len(row['citation_ids'])}",
            f"{len(row['matched_by_retrieval_equivalence'])}/{len(row['citation_ids'])}",
            len(row["unmatched_after_retrieval_equivalence"]),
        ]
        for row in rows
    ]
    action_sections = [
        ("哪些应修 trace", "fix_trace_logging"),
        ("哪些应修 evaluator id equivalence", "fix_evaluator_id_equivalence"),
        ("哪些可能是真 answer assembly bug", "fix_answer_assembly_citation_scope"),
    ]

    sections = [
        "# citation_topk_mismatch_audit_v1",
        (
            "本报告只审计 failure_report_v1 中包含 citation_not_from_top_k 的样本。"
            "本轮不重新运行检索、不重新生成答案、不使用 LLM judge，也不修改系统。"
        ),
        "## 总览\n"
        + md_table(
            ["field", "value"],
            [
                ["source_failure_report", payload["source_failure_report"]],
                ["total_citation_not_from_topk", payload["total_citation_not_from_topk"]],
                ["runtime_bug_count", payload["runtime_bug_count"]],
                ["evaluator_or_trace_issue_count", payload["evaluator_or_trace_issue_count"]],
                ["manual_audit_required_count", payload["manual_audit_required_count"]],
                ["runs_retrieval", payload["audit_scope"]["runs_retrieval"]],
                ["runs_answer_generation", payload["audit_scope"]["runs_answer_generation"]],
                ["llm_judge", payload["audit_scope"]["llm_judge"]],
            ],
        ),
        "## root_cause_counts\n" + count_table(payload["root_cause_counts"]),
        "## 审计发现\n" + count_table(payload["audit_findings"]),
        "## recommended_next_action_counts\n" + count_table(payload["recommended_next_action_counts"]),
        "## 每条 citation_not_from_top_k 审计表\n"
        + md_table(
            [
                "id",
                "category",
                "question",
                "answer_mode",
                "root_cause",
                "runtime_bug",
                "next_action",
                "existing match",
                "retrieval match",
                "unmatched after retrieval",
            ],
            audit_rows,
        ),
    ]

    for title, action in action_sections:
        action_rows = rows_for_action(payload, action)
        sections.append(
            "## "
            + title
            + "\n"
            + md_table(
                ["id", "question", "root_cause", "notes"],
                [[row["id"], row["question"], row["root_cause"], row["notes"]] for row in action_rows],
            )
        )

    sections.append(
        "## 下一轮建议\n"
        + md_table(
            ["recommended_next_action", "count", "scope"],
            [
                ["fix_trace_logging", payload["recommended_next_action_counts"].get("fix_trace_logging", 0), "只改 trace/evidence logging 时再做"],
                [
                    "fix_evaluator_id_equivalence",
                    payload["recommended_next_action_counts"].get("fix_evaluator_id_equivalence", 0),
                    "只改 evaluator 等价映射时再做",
                ],
                [
                    "allow_formula_source_expansion_in_eval",
                    payload["recommended_next_action_counts"].get("allow_formula_source_expansion_in_eval", 0),
                    "只改 citation_from_top_k 评估口径时再做",
                ],
                [
                    "inspect_secondary_review_citation_policy",
                    payload["recommended_next_action_counts"].get("inspect_secondary_review_citation_policy", 0),
                    "先定 weak/review citation 政策，再决定是否修",
                ],
                [
                    "fix_answer_assembly_citation_scope",
                    payload["recommended_next_action_counts"].get("fix_answer_assembly_citation_scope", 0),
                    "下一轮若修系统，只针对真实 citation scope 问题",
                ],
            ],
        )
    )
    return "\n\n".join(sections) + "\n"


def build_audit(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    answer_json: Path,
    trace_log: Path,
    failure_json: Path,
    out_dir: Path,
) -> dict[str, Any]:
    dataset_rows = load_dataset(dataset_path)
    retrieval_payload = load_json(retrieval_json)
    answer_payload = load_json(answer_json)
    failure_payload = load_json(failure_json)
    trace_records = load_trace_log(trace_log)
    trace_by_id = order_trace_records(dataset_rows, trace_records)
    validate_source_alignment(dataset_rows, retrieval_payload, answer_payload, failure_payload, trace_by_id)

    retrieval_by_id = index_by_id(retrieval_payload.get("per_example") or [], source_name="retrieval_eval_v1")
    answer_by_id = index_by_id(answer_payload.get("per_example") or [], source_name="answer_eval_v1")
    failure_by_id = index_by_id(failure_payload.get("per_example") or [], source_name="failure_report_v1")

    per_example: list[dict[str, Any]] = []
    for dataset_row in dataset_rows:
        row_id = dataset_row["id"]
        failure_row = failure_by_id[row_id]
        if TARGET_FAILURE_TYPE not in (failure_row.get("all_failure_types") or []):
            continue
        if failure_row.get("example_class") == "diagnostic_only":
            continue
        per_example.append(
            audit_example(
                dataset_row,
                failure_row,
                retrieval_by_id[row_id],
                answer_by_id[row_id],
                trace_by_id[row_id],
            )
        )

    payload = aggregate_payload(
        dataset_path=dataset_path,
        retrieval_json=retrieval_json,
        answer_json=answer_json,
        trace_log=trace_log,
        failure_json=failure_json,
        per_example=per_example,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{RUN_ID}.json"
    md_path = out_dir / f"{RUN_ID}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit citation_not_from_top_k rows from existing eval artifacts.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--retrieval-json", default=DEFAULT_RETRIEVAL_JSON)
    parser.add_argument("--answer-json", default=DEFAULT_ANSWER_JSON)
    parser.add_argument("--trace-log", default=DEFAULT_TRACE_LOG)
    parser.add_argument("--failure-json", default=DEFAULT_FAILURE_JSON)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    payload = build_audit(
        dataset_path=resolve_project_path(args.dataset),
        retrieval_json=resolve_project_path(args.retrieval_json),
        answer_json=resolve_project_path(args.answer_json),
        trace_log=resolve_project_path(args.trace_log),
        failure_json=resolve_project_path(args.failure_json),
        out_dir=resolve_project_path(args.out_dir),
    )
    out_dir = resolve_project_path(args.out_dir)
    print(f"Wrote {display_path(out_dir / f'{RUN_ID}.json')}")
    print(f"Wrote {display_path(out_dir / f'{RUN_ID}.md')}")
    print(f"Audited {payload['total_citation_not_from_topk']} {TARGET_FAILURE_TYPE} examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
