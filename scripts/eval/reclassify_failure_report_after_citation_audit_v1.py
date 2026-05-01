#!/usr/bin/env python3
"""Reclassify failure_report_v1 using citation_topk_mismatch_audit_v1 only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "failure_report_reclassified_after_citation_audit_v1"

DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_RETRIEVAL_JSON = REPO_ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
DEFAULT_ANSWER_JSON = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
DEFAULT_FAILURE_JSON = REPO_ROOT / "artifacts" / "eval" / "failure_report_v1" / "failure_cases_v1.json"
DEFAULT_CITATION_AUDIT_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "citation_topk_mismatch_audit_v1"
    / "citation_topk_mismatch_audit_v1.json"
)
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

RESULT_JSON_NAME = "failure_cases_reclassified_v1.json"
RESULT_MD_NAME = "failure_cases_reclassified_v1.md"
NEXT_QUEUE_JSON_NAME = "next_repair_queue_after_citation_audit_v1.json"

TARGET_ORIGINAL_FAILURE_TYPE = "citation_not_from_top_k"

CITATION_RECLASSIFIED_BY_ROOT = {
    "trace_topk_missing_equivalence": "trace_or_evaluator_equivalence_gap",
    "real_citation_assembly_issue": "real_citation_assembly_issue",
}

FORMAL_FAILURE_TYPES = {
    "out_of_scope_not_rejected",
    "correct_chunk_not_retrieved",
    "correct_chunk_low_rank",
    "citation_missing",
    "citation_not_from_top_k",
    "gold_not_cited",
    "retrieved_but_answer_wrong",
    "real_citation_assembly_issue",
    "strong_answer_secondary_review_citation_leak",
}

TOOLING_FAILURE_TYPES = {"trace_or_evaluator_equivalence_gap"}
POLICY_WARNING_TYPES = {"secondary_review_citation_policy_needs_decision"}
WARNING_ONLY_FAILURE_TYPES = {
    "scope_qualifier_missing",
    "expected_answer_mode_mismatch",
}

PRIMARY_FAILURE_PRIORITY = [
    "out_of_scope_not_rejected",
    "real_citation_assembly_issue",
    "strong_answer_secondary_review_citation_leak",
    "correct_chunk_not_retrieved",
    "correct_chunk_low_rank",
    "citation_missing",
    "citation_not_from_top_k",
    "gold_not_cited",
    "retrieved_but_answer_wrong",
    "trace_or_evaluator_equivalence_gap",
    "secondary_review_citation_policy_needs_decision",
    "expected_answer_mode_mismatch",
    "scope_qualifier_missing",
    "manual_audit_required",
]

ACTION_BY_FAILURE_TYPE = {
    "out_of_scope_not_rejected": "add_refusal_guard",
    "real_citation_assembly_issue": "fix_answer_assembly_citation_scope",
    "strong_answer_secondary_review_citation_leak": "fix_answer_assembly_citation_scope",
    "correct_chunk_not_retrieved": "fix_retrieval_or_chunking",
    "correct_chunk_low_rank": "fix_rerank",
    "citation_missing": "fix_answer_assembly",
    "citation_not_from_top_k": "inspect_trace_or_citation_mapping",
    "gold_not_cited": "fix_citation_mapping_or_answer_assembly",
    "retrieved_but_answer_wrong": "manual_answer_audit_required",
    "trace_or_evaluator_equivalence_gap": "fix_trace_logging_or_eval_equivalence",
    "secondary_review_citation_policy_needs_decision": "define_secondary_review_citation_policy",
    "expected_answer_mode_mismatch": "inspect_answer_mode_calibration",
    "scope_qualifier_missing": "consider_answer_template_scope_phrase",
    "manual_audit_required": "manual_audit_required",
}


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


def validate_source_alignment(
    dataset_rows: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
    answer_payload: dict[str, Any],
    failure_payload: dict[str, Any],
    citation_audit_payload: dict[str, Any],
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

    citation_rows = citation_audit_payload.get("per_example") or []
    if citation_audit_payload.get("total_citation_not_from_topk") != len(citation_rows):
        raise ValueError("citation audit total_citation_not_from_topk does not match per_example length")

    failure_by_id = index_by_id(failure_payload.get("per_example") or [], source_name="failure_report_v1")
    for row in citation_rows:
        row_id = str(row.get("id") or "")
        if row_id not in failure_by_id:
            raise ValueError(f"citation audit id is missing from failure_report: {row_id}")
        original_types = failure_by_id[row_id].get("all_failure_types") or []
        if TARGET_ORIGINAL_FAILURE_TYPE not in original_types:
            raise ValueError(f"citation audit row lacks original citation failure: {row_id}")


def dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def reclassified_citation_type(
    *,
    audit_row: dict[str, Any] | None,
    answer_mode: str,
) -> tuple[str, bool, str]:
    if audit_row is None:
        return (
            TARGET_ORIGINAL_FAILURE_TYPE,
            False,
            "citation_not_from_top_k has no citation audit row, so the original formal failure is preserved.",
        )

    root_cause = str(audit_row.get("root_cause") or "")
    if root_cause == "answer_uses_secondary_or_review_not_in_topk":
        if answer_mode == "strong":
            return (
                "strong_answer_secondary_review_citation_leak",
                True,
                "strong answer cites secondary/review material outside top-k, so it remains a formal citation-scope failure.",
            )
        return (
            "secondary_review_citation_policy_needs_decision",
            False,
            "weak answer cites secondary/review material outside top-k; this is separated as a policy decision before repair.",
        )

    reclassified_type = CITATION_RECLASSIFIED_BY_ROOT.get(root_cause)
    if reclassified_type:
        return (
            reclassified_type,
            reclassified_type == "real_citation_assembly_issue",
            f"citation audit root_cause={root_cause} reclassifies the original citation_not_from_top_k signal.",
        )

    return (
        TARGET_ORIGINAL_FAILURE_TYPE,
        bool(audit_row.get("is_runtime_bug")),
        f"unsupported citation audit root_cause={root_cause}; preserving the original citation failure.",
    )


def first_by_priority(failure_types: list[str]) -> str | None:
    for failure_type in PRIMARY_FAILURE_PRIORITY:
        if failure_type in failure_types:
            return failure_type
    return failure_types[0] if failure_types else None


def severity_for(row: dict[str, Any], failure_types: list[str]) -> str:
    if row.get("manual_audit_required") or "manual_audit_required" in failure_types:
        return "diagnostic"
    if not failure_types:
        return "ok"
    if any(failure_type in FORMAL_FAILURE_TYPES for failure_type in failure_types):
        return "fail"
    if any(failure_type in TOOLING_FAILURE_TYPES for failure_type in failure_types):
        return "tooling"
    if any(failure_type in POLICY_WARNING_TYPES for failure_type in failure_types):
        return "policy_warning"
    if set(failure_types).issubset(WARNING_ONLY_FAILURE_TYPES):
        return "warning"
    return "fail"


def build_reclassified_example(
    *,
    dataset_row: dict[str, Any],
    failure_row: dict[str, Any],
    answer_row: dict[str, Any],
    citation_audit_row: dict[str, Any] | None,
) -> dict[str, Any]:
    original_failure_types = list(failure_row.get("all_failure_types") or [])
    answer_mode = str(
        failure_row.get("answer_mode")
        or answer_row.get("actual_answer_mode")
        or answer_row.get("answer_mode")
        or "unknown"
    )

    reclassified_types: list[str] = []
    notes: list[str] = []
    is_runtime_bug = False
    for failure_type in original_failure_types:
        if failure_type != TARGET_ORIGINAL_FAILURE_TYPE:
            reclassified_types.append(failure_type)
            continue
        reclassified_type, citation_runtime_bug, note = reclassified_citation_type(
            audit_row=citation_audit_row,
            answer_mode=answer_mode,
        )
        reclassified_types.append(reclassified_type)
        is_runtime_bug = is_runtime_bug or citation_runtime_bug
        notes.append(note)

    reclassified_types = dedupe_preserving_order(reclassified_types)
    severity = severity_for(dataset_row, reclassified_types)
    primary_failure_type = first_by_priority(reclassified_types)
    recommended_next_actions = dedupe_preserving_order(
        ACTION_BY_FAILURE_TYPE[failure_type]
        for failure_type in reclassified_types
        if failure_type in ACTION_BY_FAILURE_TYPE
    )
    recommended_next_action = (
        ACTION_BY_FAILURE_TYPE[primary_failure_type]
        if primary_failure_type in ACTION_BY_FAILURE_TYPE
        else "none"
    )

    if dataset_row.get("manual_audit_required"):
        notes.append("P2 residual remains diagnostic-only and is excluded from runtime repair queues.")
    if dataset_row.get("should_answer") is False and answer_row.get("refuse_when_should_not_answer") is True:
        notes.append("unanswerable sample was already refused, so no out_of_scope_not_rejected failure is added.")
    if (
        "secondary_review_citation_policy_needs_decision" in reclassified_types
        and severity == "fail"
    ):
        notes.append("policy warning coexists with a still-valid formal retrieval or gold-citation failure.")

    citation_root = citation_audit_row.get("root_cause") if citation_audit_row else None
    audit_action = citation_audit_row.get("recommended_next_action") if citation_audit_row else None

    return {
        "id": dataset_row["id"],
        "category": dataset_row["category"],
        "question": dataset_row["question"],
        "should_answer": dataset_row["should_answer"],
        "manual_audit_required": dataset_row["manual_audit_required"],
        "example_class": failure_row.get("example_class"),
        "subtype": dataset_row.get("subtype") or failure_row.get("subtype") or "",
        "answer_mode": answer_mode,
        "expected_answer_mode": dataset_row.get("expected_answer_mode") or failure_row.get("expected_answer_mode") or "",
        "original_severity": failure_row.get("severity"),
        "original_primary_failure_type": failure_row.get("primary_failure_type"),
        "original_failure_types": original_failure_types,
        "citation_audit_root_cause": citation_root,
        "citation_audit_recommended_next_action": audit_action,
        "reclassified_severity": severity,
        "reclassified_primary_failure_type": primary_failure_type,
        "reclassified_failure_types": reclassified_types,
        "is_runtime_bug": is_runtime_bug,
        "recommended_next_action": recommended_next_action,
        "recommended_next_actions": recommended_next_actions,
        "gold_chunk_ids": dataset_row.get("gold_chunk_ids") or failure_row.get("gold_chunk_ids") or [],
        "retrieval_hit_at_5": failure_row.get("retrieval_hit_at_5"),
        "first_hit_rank": failure_row.get("first_hit_rank"),
        "retrieval_top5_record_ids": failure_row.get("retrieval_top5_record_ids") or [],
        "citation_ids": failure_row.get("citation_ids") or answer_row.get("citation_ids") or [],
        "citation_from_top_k": failure_row.get("citation_from_top_k"),
        "gold_cited": failure_row.get("gold_cited"),
        "refuse_when_should_not_answer": failure_row.get("refuse_when_should_not_answer"),
        "scope_qualified": failure_row.get("scope_qualified"),
        "expected_answer_mode_match": failure_row.get("expected_answer_mode_match"),
        "notes": " ".join(notes),
    }


def summarize_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "category": row["category"],
        "question": row["question"],
        "answer_mode": row.get("answer_mode"),
        "citation_audit_root_cause": row.get("citation_audit_root_cause"),
        "reclassified_severity": row["reclassified_severity"],
        "reclassified_primary_failure_type": row["reclassified_primary_failure_type"],
        "reclassified_failure_types": row["reclassified_failure_types"],
        "recommended_next_action": row["recommended_next_action"],
        "recommended_next_actions": row["recommended_next_actions"],
        "notes": row.get("notes") or "",
    }


def rows_with_type(rows: list[dict[str, Any]], failure_type: str) -> list[dict[str, Any]]:
    return [row for row in rows if failure_type in row["reclassified_failure_types"]]


def rows_with_root(rows: list[dict[str, Any]], root_cause: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("citation_audit_root_cause") == root_cause]


def build_next_repair_queue(
    *,
    source_reclassified_report: Path,
    per_example: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_rows = [
        row
        for row in per_example
        if row.get("citation_audit_root_cause") == "real_citation_assembly_issue"
        or "strong_answer_secondary_review_citation_leak" in row["reclassified_failure_types"]
    ]
    retrieval_rows = [
        row
        for row in per_example
        if "correct_chunk_not_retrieved" in row["reclassified_failure_types"]
        or "correct_chunk_low_rank" in row["reclassified_failure_types"]
    ]
    p2_rows = [
        row
        for row in per_example
        if row.get("subtype") == "p2_residual"
        or "manual_audit_required" in row["reclassified_failure_types"]
    ]

    return {
        "run_id": "next_repair_queue_after_citation_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_reclassified_report": display_path(source_reclassified_report),
        "runtime_citation_scope_repairs": [summarize_candidate(row) for row in runtime_rows],
        "retrieval_or_chunking_repairs": [summarize_candidate(row) for row in retrieval_rows],
        "trace_or_evaluator_repairs": [
            summarize_candidate(row)
            for row in rows_with_root(per_example, "trace_topk_missing_equivalence")
        ],
        "secondary_review_policy_decisions": [
            summarize_candidate(row)
            for row in rows_with_root(per_example, "answer_uses_secondary_or_review_not_in_topk")
        ],
        "scope_phrase_warnings": [
            summarize_candidate(row)
            for row in rows_with_type(per_example, "scope_qualifier_missing")
        ],
        "answer_mode_calibration_observations": [
            summarize_candidate(row)
            for row in rows_with_type(per_example, "expected_answer_mode_mismatch")
        ],
        "p2_manual_audit": [summarize_candidate(row) for row in p2_rows],
    }


def build_payload(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    answer_json: Path,
    failure_json: Path,
    citation_audit_json: Path,
    dataset_rows: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
    answer_payload: dict[str, Any],
    failure_payload: dict[str, Any],
    citation_audit_payload: dict[str, Any],
    per_example: list[dict[str, Any]],
) -> dict[str, Any]:
    severity_counts = Counter(row["reclassified_severity"] for row in per_example)
    reclassified_type_counts = Counter(
        failure_type for row in per_example for failure_type in row["reclassified_failure_types"]
    )
    action_counts = Counter(row["recommended_next_action"] for row in per_example)
    original_formal_fail_count = int(failure_payload.get("formal_fail_count") or 0)
    formal_failures = [row for row in per_example if row["reclassified_severity"] == "fail"]
    runtime_bug_rows = [row for row in per_example if row["is_runtime_bug"]]
    tooling_rows = rows_with_type(per_example, "trace_or_evaluator_equivalence_gap")
    policy_rows = rows_with_type(per_example, "secondary_review_citation_policy_needs_decision")
    retrieval_rows = [
        row
        for row in per_example
        if "correct_chunk_not_retrieved" in row["reclassified_failure_types"]
        or "correct_chunk_low_rank" in row["reclassified_failure_types"]
    ]
    p2_rows = [
        row
        for row in per_example
        if row.get("subtype") == "p2_residual"
        or "manual_audit_required" in row["reclassified_failure_types"]
    ]

    source_paths = {
        "eval_dataset_v1": dataset_path,
        "retrieval_eval_v1": retrieval_json,
        "answer_eval_v1": answer_json,
        "failure_report_v1": failure_json,
        "citation_topk_mismatch_audit_v1": citation_audit_json,
    }

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": display_path(dataset_path),
        "retrieval_eval_source": display_path(retrieval_json),
        "answer_eval_source": display_path(answer_json),
        "source_failure_report": display_path(failure_json),
        "source_citation_audit": display_path(citation_audit_json),
        "source_artifacts": {name: display_path(path) for name, path in source_paths.items()},
        "source_sha256": {name: sha256_file(path) for name, path in source_paths.items()},
        "report_scope": {
            "source_artifacts_only": True,
            "runs_retrieval": False,
            "runs_answer_generation": False,
            "llm_judge": False,
            "modifies_runtime": False,
        },
        "judge": {"type": "rules_only_artifact_reclassification", "llm_judge": False},
        "total_examples": len(dataset_rows),
        "original_formal_fail_count": original_formal_fail_count,
        "reclassified_formal_fail_count": len(formal_failures),
        "tooling_count": len(tooling_rows),
        "policy_warning_count": len(policy_rows),
        "policy_warning_only_count": severity_counts["policy_warning"],
        "warning_count": severity_counts["warning"],
        "diagnostic_count": severity_counts["diagnostic"],
        "ok_count": severity_counts["ok"],
        "runtime_bug_count": len(runtime_bug_rows),
        "severity_counts": dict(sorted(severity_counts.items())),
        "reclassified_failure_type_counts": dict(sorted(reclassified_type_counts.items())),
        "recommended_next_action_counts": dict(sorted(action_counts.items())),
        "source_metric_summary": {
            "failure_report_v1": {
                "formal_fail_count": failure_payload.get("formal_fail_count"),
                "warning_count": failure_payload.get("warning_count"),
                "diagnostic_count": failure_payload.get("diagnostic_count"),
                "ok_count": failure_payload.get("ok_count"),
                "citation_not_from_top_k": (failure_payload.get("failure_type_counts") or {}).get(
                    TARGET_ORIGINAL_FAILURE_TYPE
                ),
            },
            "citation_topk_mismatch_audit_v1": {
                "total_citation_not_from_topk": citation_audit_payload.get("total_citation_not_from_topk"),
                "root_cause_counts": citation_audit_payload.get("root_cause_counts") or {},
                "runtime_bug_count": citation_audit_payload.get("runtime_bug_count"),
                "evaluator_or_trace_issue_count": citation_audit_payload.get(
                    "evaluator_or_trace_issue_count"
                ),
                "manual_audit_required_count": citation_audit_payload.get("manual_audit_required_count"),
            },
            "retrieval_eval_v1": {
                key: retrieval_payload.get(key)
                for key in [
                    "total_examples",
                    "answerable_metric_examples",
                    "diagnostic_only_examples",
                    "unanswerable_examples",
                    "hit_at_1",
                    "hit_at_3",
                    "hit_at_5",
                    "mrr",
                    "recall_at_5",
                ]
            },
            "answer_eval_v1": {
                key: answer_payload.get(key)
                for key in [
                    "total_examples",
                    "answerable_metric_examples",
                    "diagnostic_only_examples",
                    "unanswerable_examples",
                    "has_citation_rate",
                    "citation_from_top_k_rate",
                    "gold_cited_rate",
                    "refuse_when_should_not_answer_rate",
                ]
            },
        },
        "formal_runtime_repair_candidates": [summarize_candidate(row) for row in runtime_bug_rows],
        "tooling_repair_candidates": [summarize_candidate(row) for row in tooling_rows],
        "policy_decision_candidates": [summarize_candidate(row) for row in policy_rows],
        "retrieval_repair_candidates": [summarize_candidate(row) for row in retrieval_rows],
        "p2_diagnostic_examples": [summarize_candidate(row) for row in p2_rows],
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


def examples_table(rows: list[dict[str, Any]]) -> str:
    return md_table(
        ["id", "category", "question", "severity", "primary", "types", "action"],
        [
            [
                row["id"],
                row["category"],
                row["question"],
                row["reclassified_severity"],
                row["reclassified_primary_failure_type"] or "",
                ", ".join(row["reclassified_failure_types"]),
                row["recommended_next_action"],
            ]
            for row in rows
        ],
    )


def render_markdown(payload: dict[str, Any], next_queue: dict[str, Any]) -> str:
    failure_summary = payload["source_metric_summary"]["failure_report_v1"]
    citation_summary = payload["source_metric_summary"]["citation_topk_mismatch_audit_v1"]
    per_example = payload["per_example"]
    runtime_rows = [
        row for row in per_example if row.get("citation_audit_root_cause") == "real_citation_assembly_issue"
    ]
    trace_rows = rows_with_root(per_example, "trace_topk_missing_equivalence")
    policy_rows = rows_with_root(per_example, "answer_uses_secondary_or_review_not_in_topk")
    retrieval_rows = [
        row
        for row in per_example
        if "correct_chunk_not_retrieved" in row["reclassified_failure_types"]
        or "correct_chunk_low_rank" in row["reclassified_failure_types"]
    ]
    p2_rows = [
        row
        for row in per_example
        if row.get("subtype") == "p2_residual"
        or "manual_audit_required" in row["reclassified_failure_types"]
    ]

    return "\n\n".join(
        [
            "# failure_report_reclassified_after_citation_audit_v1",
            (
                "本报告只基于 citation_topk_mismatch_audit_v1 对 failure_report_v1 做诊断归因重分类。"
                "它不重新生成答案、不重新跑检索，也不修改原始评测产物或系统实现。"
            ),
            "## 总览\n"
            + md_table(
                ["field", "value"],
                [
                    ["total_examples", payload["total_examples"]],
                    ["original_formal_fail_count", payload["original_formal_fail_count"]],
                    ["reclassified_formal_fail_count", payload["reclassified_formal_fail_count"]],
                    ["runtime_bug_count", payload["runtime_bug_count"]],
                    ["tooling_count", payload["tooling_count"]],
                    ["policy_warning_count", payload["policy_warning_count"]],
                    ["policy_warning_only_count", payload["policy_warning_only_count"]],
                    ["warning_count", payload["warning_count"]],
                    ["diagnostic_count", payload["diagnostic_count"]],
                    ["ok_count", payload["ok_count"]],
                ],
            ),
            "## 原 failure_report_v1 计数\n"
            + md_table(
                ["field", "value"],
                [
                    ["formal_fail_count", failure_summary.get("formal_fail_count")],
                    ["warning_count", failure_summary.get("warning_count")],
                    ["diagnostic_count", failure_summary.get("diagnostic_count")],
                    ["ok_count", failure_summary.get("ok_count")],
                    ["citation_not_from_top_k", failure_summary.get("citation_not_from_top_k")],
                ],
            ),
            "## citation audit 计数\n"
            + md_table(
                ["field", "value"],
                [
                    ["total_citation_not_from_topk", citation_summary.get("total_citation_not_from_topk")],
                    ["runtime_bug_count", citation_summary.get("runtime_bug_count")],
                    ["evaluator_or_trace_issue_count", citation_summary.get("evaluator_or_trace_issue_count")],
                    ["manual_audit_required_count", citation_summary.get("manual_audit_required_count")],
                ],
            )
            + "\n\n"
            + count_table(citation_summary.get("root_cause_counts") or {}),
            "## 重分类后的计数\n"
            + count_table(payload["severity_counts"])
            + "\n\n"
            + count_table(payload["reclassified_failure_type_counts"]),
            "## 真 runtime citation bug 列表\n" + examples_table(runtime_rows),
            "## trace / evaluator 问题列表\n" + examples_table(trace_rows),
            "## secondary / review citation policy 问题列表\n" + examples_table(policy_rows),
            "## retrieval / chunking 仍需修复的问题列表\n" + examples_table(retrieval_rows),
            "## P2 diagnostic-only 列表\n" + examples_table(p2_rows),
            "## 下一步建议\n"
            + md_table(
                ["queue", "count", "next_action"],
                [
                    [
                        "runtime_citation_scope_repairs",
                        len(next_queue["runtime_citation_scope_repairs"]),
                        "fix_answer_assembly_citation_scope",
                    ],
                    [
                        "retrieval_or_chunking_repairs",
                        len(next_queue["retrieval_or_chunking_repairs"]),
                        "fix_retrieval_or_chunking",
                    ],
                    [
                        "trace_or_evaluator_repairs",
                        len(next_queue["trace_or_evaluator_repairs"]),
                        "fix_trace_logging_or_eval_equivalence",
                    ],
                    [
                        "secondary_review_policy_decisions",
                        len(next_queue["secondary_review_policy_decisions"]),
                        "define_secondary_review_citation_policy",
                    ],
                    ["p2_manual_audit", len(next_queue["p2_manual_audit"]), "manual_audit_required"],
                ],
            ),
        ]
    ) + "\n"


def build_report(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    answer_json: Path,
    failure_json: Path,
    citation_audit_json: Path,
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dataset_rows = load_dataset(dataset_path)
    retrieval_payload = load_json(retrieval_json)
    answer_payload = load_json(answer_json)
    failure_payload = load_json(failure_json)
    citation_audit_payload = load_json(citation_audit_json)
    validate_source_alignment(
        dataset_rows,
        retrieval_payload,
        answer_payload,
        failure_payload,
        citation_audit_payload,
    )

    answer_by_id = index_by_id(answer_payload.get("per_example") or [], source_name="answer_eval_v1")
    failure_by_id = index_by_id(failure_payload.get("per_example") or [], source_name="failure_report_v1")
    citation_audit_by_id = index_by_id(
        citation_audit_payload.get("per_example") or [],
        source_name="citation_topk_mismatch_audit_v1",
    )

    per_example = [
        build_reclassified_example(
            dataset_row=dataset_row,
            failure_row=failure_by_id[dataset_row["id"]],
            answer_row=answer_by_id[dataset_row["id"]],
            citation_audit_row=citation_audit_by_id.get(dataset_row["id"]),
        )
        for dataset_row in dataset_rows
    ]

    payload = build_payload(
        dataset_path=dataset_path,
        retrieval_json=retrieval_json,
        answer_json=answer_json,
        failure_json=failure_json,
        citation_audit_json=citation_audit_json,
        dataset_rows=dataset_rows,
        retrieval_payload=retrieval_payload,
        answer_payload=answer_payload,
        failure_payload=failure_payload,
        citation_audit_payload=citation_audit_payload,
        per_example=per_example,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    result_json_path = out_dir / RESULT_JSON_NAME
    result_md_path = out_dir / RESULT_MD_NAME
    next_queue_json_path = out_dir / NEXT_QUEUE_JSON_NAME
    next_queue = build_next_repair_queue(
        source_reclassified_report=result_json_path,
        per_example=per_example,
    )

    result_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    next_queue_json_path.write_text(
        json.dumps(next_queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result_md_path.write_text(render_markdown(payload, next_queue), encoding="utf-8")
    return payload, next_queue


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reclassify failure_report_v1 using existing citation audit artifacts."
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--retrieval-json", default=DEFAULT_RETRIEVAL_JSON)
    parser.add_argument("--answer-json", default=DEFAULT_ANSWER_JSON)
    parser.add_argument("--failure-json", default=DEFAULT_FAILURE_JSON)
    parser.add_argument("--citation-audit-json", default=DEFAULT_CITATION_AUDIT_JSON)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    out_dir = resolve_project_path(args.out_dir)
    payload, next_queue = build_report(
        dataset_path=resolve_project_path(args.dataset),
        retrieval_json=resolve_project_path(args.retrieval_json),
        answer_json=resolve_project_path(args.answer_json),
        failure_json=resolve_project_path(args.failure_json),
        citation_audit_json=resolve_project_path(args.citation_audit_json),
        out_dir=out_dir,
    )
    print(f"Wrote {display_path(out_dir / RESULT_JSON_NAME)}")
    print(f"Wrote {display_path(out_dir / RESULT_MD_NAME)}")
    print(f"Wrote {display_path(out_dir / NEXT_QUEUE_JSON_NAME)}")
    print(
        "Reclassified "
        f"{payload['total_examples']} examples; "
        f"runtime citation repairs={len(next_queue['runtime_citation_scope_repairs'])}, "
        f"trace/evaluator repairs={len(next_queue['trace_or_evaluator_repairs'])}, "
        f"policy decisions={len(next_queue['secondary_review_policy_decisions'])}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
