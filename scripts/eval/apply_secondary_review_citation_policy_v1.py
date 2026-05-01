#!/usr/bin/env python3
"""Apply the secondary/review citation policy to existing eval artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "secondary_review_citation_policy_v1"
POLICY_VERSION = "v1"

DEFAULT_SUMMARY_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "eval_diagnostic_loop_v1"
    / "eval_diagnostic_loop_summary_v1.json"
)
DEFAULT_RECLASSIFIED_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "failure_report_reclassified_after_citation_audit_v1"
    / "failure_cases_reclassified_v1.json"
)
DEFAULT_NEXT_QUEUE_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "failure_report_reclassified_after_citation_audit_v1"
    / "next_repair_queue_after_citation_audit_v1.json"
)
DEFAULT_CITATION_AUDIT_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "citation_topk_mismatch_audit_v1"
    / "citation_topk_mismatch_audit_v1.json"
)
DEFAULT_ANSWER_JSON = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
DEFAULT_TRACE_LOG = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "qa_trace_answer_eval_v1.jsonl"
DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_DOCS_MD = REPO_ROOT / "docs" / "eval" / "secondary_review_citation_policy_v1.md"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

SUMMARY_JSON_NAME = "secondary_review_citation_policy_v1.json"
CASES_JSON_NAME = "secondary_review_policy_cases_v1.json"

POLICY_STATUSES = {
    "policy_accepted",
    "policy_needs_trace_improvement",
    "policy_violation",
    "manual_audit_required",
}

CONSERVATIVE_LANGUAGE_MARKERS = (
    "目前不作为",
    "只能作为核对线索",
    "建议回到原文核对",
    "建议先回看",
    "证据不足",
    "不足以强答",
    "缺少更稳定",
    "保守地",
    "只能先保守",
    "只能先这样说",
    "不强答",
    "可参考",
    "再核对",
)

FORBIDDEN_PRIMARY_PREFIXES = (
    "full:passages:",
    "full:ambiguous_passages:",
)
FORBIDDEN_PRIMARY_MARKERS = (
    "review-only",
    "risk-only",
)


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{display_path(path)} line {line_number} is not a JSON object")
            rows.append(row)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def has_conservative_language(answer_text: str) -> bool:
    compact = " ".join(answer_text.split())
    return any(marker in compact for marker in CONSERVATIVE_LANGUAGE_MARKERS)


def contains_forbidden_primary_id(record_id: str) -> bool:
    lowered = record_id.lower()
    return record_id.startswith(FORBIDDEN_PRIMARY_PREFIXES) or any(
        marker in lowered for marker in FORBIDDEN_PRIMARY_MARKERS
    )


def audit_membership_by_citation(audit_row: dict[str, Any] | None) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not audit_row:
        return result
    for item in audit_row.get("citation_audit") or []:
        citation_id = str(item.get("citation_id") or "")
        if not citation_id:
            continue
        memberships = as_list(item.get("evidence_slot_membership"))
        source_slot = str(item.get("source_slot") or "")
        if source_slot:
            memberships.append(source_slot)
        result[citation_id] = dedupe_preserving_order(memberships)
    return result


def source_slots_trace_secondary_review(
    *,
    citation_ids: list[str],
    citation_source_slots: list[str],
    secondary_evidence_ids: list[str],
    review_material_ids: list[str],
    audit_row: dict[str, Any] | None,
) -> bool:
    if not citation_ids:
        return False

    secondary_or_review = {"secondary", "review"}
    if len(citation_source_slots) == len(citation_ids) and all(
        slot in secondary_or_review for slot in citation_source_slots
    ):
        return True

    secondary_review_ids = set(secondary_evidence_ids) | set(review_material_ids)
    audit_membership = audit_membership_by_citation(audit_row)
    for citation_id in citation_ids:
        if citation_id in secondary_review_ids:
            continue
        memberships = set(audit_membership.get(citation_id) or [])
        if memberships & secondary_or_review:
            continue
        return False
    return True


def has_secondary_review_citation(
    *,
    citation_ids: list[str],
    citation_source_slots: list[str],
    secondary_evidence_ids: list[str],
    review_material_ids: list[str],
    audit_row: dict[str, Any] | None,
) -> bool:
    if any(slot in {"secondary", "review"} for slot in citation_source_slots):
        return True
    secondary_review_ids = set(secondary_evidence_ids) | set(review_material_ids)
    if any(citation_id in secondary_review_ids for citation_id in citation_ids):
        return True
    memberships = audit_membership_by_citation(audit_row)
    return any(
        set(memberships.get(citation_id) or []) & {"secondary", "review"}
        for citation_id in citation_ids
    )


def classify_case(
    *,
    answer_mode: str,
    has_conservative: bool,
    secondary_review_citation: bool,
    source_slot_traceable: bool,
    primary_contains_forbidden_full_passage: bool,
) -> tuple[str, str, str]:
    if answer_mode == "strong":
        if secondary_review_citation or primary_contains_forbidden_full_passage:
            return (
                "policy_violation",
                "fix_answer_assembly_citation_scope",
                "strong answer cannot use secondary/review citations as main citations.",
            )
        return (
            "manual_audit_required",
            "manual_audit_required",
            "strong answer appeared in the policy queue without a secondary/review citation signal.",
        )

    if answer_mode == "weak_with_review_notice":
        if primary_contains_forbidden_full_passage:
            return (
                "policy_violation",
                "fix_answer_assembly_citation_scope",
                "weak answer put forbidden raw/review-risk material into primary evidence.",
            )
        if not secondary_review_citation:
            return (
                "manual_audit_required",
                "manual_audit_required",
                "policy queue row does not expose a secondary/review citation signal.",
            )
        if not has_conservative:
            return (
                "policy_violation",
                "fix_answer_template_or_answer_mode_calibration",
                "weak answer cites secondary/review material without conservative language.",
            )
        if not source_slot_traceable:
            return (
                "policy_needs_trace_improvement",
                "improve_trace_evidence_slot_visibility",
                "weak answer tone is acceptable, but citation source slots are not traceable enough.",
            )
        return (
            "policy_accepted",
            "none",
            "weak answer cites secondary/review material with conservative language and traceable slots.",
        )

    if answer_mode == "refuse":
        if source_slot_traceable or not secondary_review_citation:
            return (
                "policy_accepted",
                "none",
                "refuse answer citation, if present, is treated only as range or retrieval context.",
            )
        return (
            "policy_needs_trace_improvement",
            "improve_trace_evidence_slot_visibility",
            "refuse answer has citation context but source slots are not traceable enough.",
        )

    return (
        "manual_audit_required",
        "manual_audit_required",
        f"unsupported answer_mode={answer_mode}.",
    )


def build_trace_index(
    *,
    answer_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    question_to_id = {
        str(row.get("question") or ""): str(row.get("id") or "")
        for row in answer_rows
        if row.get("id") and row.get("question")
    }
    result: dict[str, dict[str, Any]] = {}
    for trace_row in trace_rows:
        row_id = question_to_id.get(str(trace_row.get("query") or ""))
        if row_id:
            result[row_id] = trace_row
    return result


def validate_scope(
    *,
    summary_payload: dict[str, Any],
    next_queue_payload: dict[str, Any],
    reclassified_payload: dict[str, Any],
) -> None:
    if summary_payload.get("all_steps_passed") is not True:
        raise ValueError("eval diagnostic loop summary does not have all_steps_passed=true")
    queue_policy_rows = next_queue_payload.get("secondary_review_policy_decisions")
    if not isinstance(queue_policy_rows, list):
        raise ValueError("next queue has no secondary_review_policy_decisions list")
    reclassified_policy_rows = reclassified_payload.get("policy_decision_candidates") or []
    if len(queue_policy_rows) != len(reclassified_policy_rows):
        raise ValueError("policy decision counts differ between next queue and reclassified report")

    policy_ids = {str(row.get("id") or "") for row in queue_policy_rows}
    exclusive_queue_names = (
        "runtime_citation_scope_repairs",
        "trace_or_evaluator_repairs",
        "p2_manual_audit",
    )
    for queue_name in exclusive_queue_names:
        excluded_ids = {
            str(row.get("id") or "")
            for row in next_queue_payload.get(queue_name) or []
            if row.get("id")
        }
        overlap = policy_ids & excluded_ids
        if overlap:
            raise ValueError(f"policy queue overlaps {queue_name}: {sorted(overlap)}")


def next_queue_memberships(next_queue_payload: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for queue_name, queue_rows in next_queue_payload.items():
        if not isinstance(queue_rows, list):
            continue
        for row in queue_rows:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            result.setdefault(str(row["id"]), []).append(queue_name)
    return result


def build_policy_case(
    *,
    queue_row: dict[str, Any],
    answer_row: dict[str, Any],
    audit_row: dict[str, Any] | None,
    trace_row: dict[str, Any] | None,
    queue_memberships: list[str],
) -> dict[str, Any]:
    trace_row = trace_row or {}
    answer_mode = str(
        answer_row.get("actual_answer_mode")
        or answer_row.get("answer_mode")
        or queue_row.get("answer_mode")
        or "unknown"
    )
    citation_ids = as_list(answer_row.get("citation_ids"))
    citation_source_slots = as_list(answer_row.get("citation_source_slots"))
    primary_evidence_ids = as_list(trace_row.get("primary_evidence_ids"))
    secondary_evidence_ids = as_list(trace_row.get("secondary_evidence_ids"))
    review_material_ids = as_list(trace_row.get("review_material_ids"))
    final_answer = str(trace_row.get("final_answer") or answer_row.get("final_answer_excerpt") or "")
    conservative = has_conservative_language(final_answer)
    primary_contains_forbidden = any(
        contains_forbidden_primary_id(record_id) for record_id in primary_evidence_ids
    )
    secondary_review_citation = has_secondary_review_citation(
        citation_ids=citation_ids,
        citation_source_slots=citation_source_slots,
        secondary_evidence_ids=secondary_evidence_ids,
        review_material_ids=review_material_ids,
        audit_row=audit_row,
    )
    source_slot_traceable = source_slots_trace_secondary_review(
        citation_ids=citation_ids,
        citation_source_slots=citation_source_slots,
        secondary_evidence_ids=secondary_evidence_ids,
        review_material_ids=review_material_ids,
        audit_row=audit_row,
    )
    policy_status, recommended_next_action, note = classify_case(
        answer_mode=answer_mode,
        has_conservative=conservative,
        secondary_review_citation=secondary_review_citation,
        source_slot_traceable=source_slot_traceable,
        primary_contains_forbidden_full_passage=primary_contains_forbidden,
    )
    if policy_status not in POLICY_STATUSES:
        raise ValueError(f"unsupported policy status: {policy_status}")

    return {
        "id": str(queue_row.get("id") or ""),
        "category": str(queue_row.get("category") or answer_row.get("category") or ""),
        "question": str(queue_row.get("question") or answer_row.get("question") or ""),
        "answer_mode": answer_mode,
        "citation_audit_root_cause": str(
            queue_row.get("citation_audit_root_cause")
            or (audit_row or {}).get("root_cause")
            or ""
        ),
        "citation_ids": citation_ids,
        "citation_source_slots": citation_source_slots,
        "has_conservative_language": conservative,
        "primary_evidence_ids": primary_evidence_ids,
        "secondary_evidence_ids": secondary_evidence_ids,
        "review_material_ids": review_material_ids,
        "primary_contains_forbidden_full_passage": primary_contains_forbidden,
        "secondary_review_citation_detected": secondary_review_citation,
        "source_slot_traceable": source_slot_traceable,
        "trace_found": bool(trace_row),
        "source_queue": "secondary_review_policy_decisions",
        "also_in_next_queue": [
            queue_name
            for queue_name in queue_memberships
            if queue_name != "secondary_review_policy_decisions"
        ],
        "policy_status": policy_status,
        "recommended_next_action": recommended_next_action,
        "notes": note,
    }


def build_policy_cases(
    *,
    next_queue_payload: dict[str, Any],
    answer_payload: dict[str, Any],
    citation_audit_payload: dict[str, Any],
    trace_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    answer_rows = answer_payload.get("per_example") or []
    answer_by_id = index_by_id(answer_rows, source_name="answer_eval_v1")
    audit_by_id = index_by_id(
        citation_audit_payload.get("per_example") or [],
        source_name="citation_topk_mismatch_audit_v1",
    )
    trace_by_id = build_trace_index(answer_rows=answer_rows, trace_rows=trace_rows)
    memberships_by_id = next_queue_memberships(next_queue_payload)

    cases: list[dict[str, Any]] = []
    for queue_row in next_queue_payload.get("secondary_review_policy_decisions") or []:
        row_id = str(queue_row.get("id") or "")
        if row_id not in answer_by_id:
            raise ValueError(f"policy queue id is missing from answer_eval_v1: {row_id}")
        cases.append(
            build_policy_case(
                queue_row=queue_row,
                answer_row=answer_by_id[row_id],
                audit_row=audit_by_id.get(row_id),
                trace_row=trace_by_id.get(row_id),
                queue_memberships=memberships_by_id.get(row_id) or [],
            )
        )
    return cases


def build_summary_payload(
    *,
    summary_json: Path,
    reclassified_json: Path,
    next_queue_json: Path,
    citation_audit_json: Path,
    answer_json: Path,
    trace_log: Path,
    dataset: Path,
    next_queue_payload: dict[str, Any],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts = Counter(case["policy_status"] for case in cases)
    strong_secondary_review_violations = [
        case
        for case in cases
        if case["answer_mode"] == "strong" and case["policy_status"] == "policy_violation"
    ]
    source_paths = {
        "eval_diagnostic_loop_summary_v1": summary_json,
        "failure_cases_reclassified_v1": reclassified_json,
        "next_repair_queue_after_citation_audit_v1": next_queue_json,
        "citation_topk_mismatch_audit_v1": citation_audit_json,
        "answer_eval_v1": answer_json,
        "qa_trace_answer_eval_v1": trace_log,
    }

    return {
        "run_id": RUN_ID,
        "policy_version": POLICY_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "weak_with_review_notice secondary/review citation policy",
        "source_artifacts": {name: display_path(path) for name, path in source_paths.items()},
        "source_sha256": {name: sha256_file(path) for name, path in source_paths.items()},
        "guarded_non_input_sha256": {
            "eval_dataset_v1": sha256_file(dataset) if dataset.exists() else None,
        },
        "report_scope": {
            "source_artifacts_only": True,
            "runs_retrieval": False,
            "runs_answer_generation": False,
            "runs_answer_assembly": False,
            "llm_judge": False,
            "modifies_runtime": False,
        },
        "judge": {"type": "rules_only_policy_classification", "llm_judge": False},
        "total_policy_decision_cases": len(cases),
        "policy_accepted_count": status_counts["policy_accepted"],
        "policy_needs_trace_improvement_count": status_counts["policy_needs_trace_improvement"],
        "policy_violation_count": status_counts["policy_violation"],
        "manual_audit_required_count": status_counts["manual_audit_required"],
        "strong_secondary_review_violation_count": len(strong_secondary_review_violations),
        "weak_secondary_review_allowed": True,
        "runtime_changed": False,
        "prompt_changed": False,
        "api_changed": False,
        "frontend_changed": False,
        "existing_evaluator_changed": False,
        "dataset_changed": False,
        "policy_status_counts": dict(sorted(status_counts.items())),
        "excluded_queue_counts": {
            "runtime_citation_scope_repairs": len(
                next_queue_payload.get("runtime_citation_scope_repairs") or []
            ),
            "trace_or_evaluator_repairs": len(next_queue_payload.get("trace_or_evaluator_repairs") or []),
            "p2_manual_audit": len(next_queue_payload.get("p2_manual_audit") or []),
            "retrieval_or_chunking_repairs": len(
                next_queue_payload.get("retrieval_or_chunking_repairs") or []
            ),
        },
        "policy_cases_also_in_retrieval_or_chunking_repairs": [
            case["id"]
            for case in cases
            if "retrieval_or_chunking_repairs" in case.get("also_in_next_queue", [])
        ],
        "policy_case_ids": [case["id"] for case in cases],
        "policy_accepted_ids": [
            case["id"] for case in cases if case["policy_status"] == "policy_accepted"
        ],
        "policy_needs_trace_improvement_ids": [
            case["id"]
            for case in cases
            if case["policy_status"] == "policy_needs_trace_improvement"
        ],
        "policy_violation_ids": [
            case["id"] for case in cases if case["policy_status"] == "policy_violation"
        ],
        "manual_audit_required_ids": [
            case["id"] for case in cases if case["policy_status"] == "manual_audit_required"
        ],
        "notes": (
            "Only next_queue.secondary_review_policy_decisions is classified here. "
            "Accepted weak secondary/review citations do not mean the whole system passed."
        ),
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


def ids_for_status(cases: list[dict[str, Any]], status: str) -> str:
    ids = [case["id"] for case in cases if case["policy_status"] == status]
    return ", ".join(ids) if ids else "none"


def render_markdown(summary: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    accepted = [case for case in cases if case["policy_status"] == "policy_accepted"]
    trace_improvement = [
        case for case in cases if case["policy_status"] == "policy_needs_trace_improvement"
    ]
    violations = [case for case in cases if case["policy_status"] == "policy_violation"]
    manual = [case for case in cases if case["policy_status"] == "manual_audit_required"]

    case_rows = [
        [
            case["id"],
            case["category"],
            case["question"],
            case["answer_mode"],
            ", ".join(case["citation_source_slots"]),
            case["has_conservative_language"],
            case["source_slot_traceable"],
            case["primary_contains_forbidden_full_passage"],
            case["policy_status"],
            case["recommended_next_action"],
        ]
        for case in cases
    ]

    return "\n\n".join(
        [
            "# secondary_review_citation_policy_v1",
            (
                "本轮目标是只定义 secondary/review citation policy，处理 "
                "`next_repair_queue_after_citation_audit_v1.json` 中的 "
                "`secondary_review_policy_decisions`。本轮不修 runtime，不修 retrieval，"
                "不改已有 evaluator，不改 dataset，不改 prompt，不改前端，不改 API。"
            ),
            "## 本轮目标\n"
            + md_table(
                ["field", "value"],
                [
                    ["run_id", summary["run_id"]],
                    ["policy_version", summary["policy_version"]],
                    ["total_policy_decision_cases", summary["total_policy_decision_cases"]],
                    ["policy_accepted_count", summary["policy_accepted_count"]],
                    [
                        "policy_needs_trace_improvement_count",
                        summary["policy_needs_trace_improvement_count"],
                    ],
                    ["policy_violation_count", summary["policy_violation_count"]],
                    ["manual_audit_required_count", summary["manual_audit_required_count"]],
                    [
                        "strong_secondary_review_violation_count",
                        summary["strong_secondary_review_violation_count"],
                    ],
                    [
                        "policy_cases_also_in_retrieval_or_chunking_repairs",
                        ", ".join(summary["policy_cases_also_in_retrieval_or_chunking_repairs"])
                        or "none",
                    ],
                ],
            ),
            "## 为什么要定义 secondary/review citation policy\n"
            + (
                "citation_topk_mismatch_audit_v1 将 9 条弱答 citation warning 归因为 "
                "`answer_uses_secondary_or_review_not_in_topk`。这些样本不是 P2 manual audit，"
                "也不属于已确认的 runtime citation bug。必须先明确弱答是否允许引用 "
                "secondary/review 材料，才能避免把政策空白误判成 answer assembly 缺陷。"
            ),
            "## answer_mode citation 规则\n"
            + md_table(
                ["answer_mode", "policy"],
                [
                    [
                        "strong",
                        (
                            "strong answer 不允许引用 secondary/review 作为主引用；"
                            "citations 必须来自 primary evidence。若 strong 引用 secondary/review，"
                            "标记 policy_violation，下一步是 fix_answer_assembly_citation_scope。"
                        ),
                    ],
                    [
                        "weak_with_review_notice",
                        (
                            "weak answer 可以引用 secondary/review，但必须带保守语气和可追踪证据槽；"
                            "final answer 要说明目前不作为稳定定义、只能作为核对线索、建议回到原文核对、"
                            "证据不足以强答等；citation source slot 或 trace/evidence slots 必须能追踪到 "
                            "secondary/review；raw full:passages、full:ambiguous_passages、review-only、risk-only "
                            "不能进入 primary。"
                        ),
                    ],
                    [
                        "refuse",
                        (
                            "refuse answer 通常不要求 citation；若有 citation，只能作为范围说明或检索线索，"
                            "不应写成实质回答依据。本轮只记录政策，不修回答。"
                        ),
                    ],
                ],
            ),
            "## 9 条 policy decision 逐条表格\n"
            + md_table(
                [
                    "id",
                    "category",
                    "question",
                    "answer_mode",
                    "citation_source_slots",
                    "conservative",
                    "source_traceable",
                    "primary_forbidden_full",
                    "policy_status",
                    "recommended_next_action",
                ],
                case_rows,
            ),
            "## 队列边界\n"
            + (
                "本轮 cases 的唯一入口是 `secondary_review_policy_decisions`。"
                "`runtime_citation_scope_repairs`、`trace_or_evaluator_repairs`、"
                "`p2_manual_audit` 不进入本轮 cases。"
                "若某个 id 同时带有 retrieval/chunking 失败类型，本轮也只裁定它的 "
                "secondary/review citation policy 状态，不修 retrieval/chunking。"
            ),
            "## policy_accepted\n"
            + (
                f"Accepted ids: {ids_for_status(cases, 'policy_accepted')}.\n\n"
                "这些 case 都是 `weak_with_review_notice`，最终回答包含保守语气，"
                "citation source slots 明确落在 secondary/review，trace 中 primary_evidence_ids 未放入 "
                "raw full passage 或 ambiguous passage。"
            ),
            "## policy_needs_trace_improvement\n"
            + (
                f"Trace-improvement ids: {ids_for_status(cases, 'policy_needs_trace_improvement')}.\n\n"
                "若后续出现弱答语气合格但 source slot 或 trace/evidence slot 不清楚的样本，"
                "应归到这里，下一步只改 trace 可见性，不直接修 answer assembly。"
            ),
            "## policy_violation\n"
            + (
                f"Violation ids: {ids_for_status(cases, 'policy_violation')}.\n\n"
                "若 strong answer 引用 secondary/review、weak answer 没有保守语气却引用 secondary/review，"
                "或 forbidden full/review-risk 材料进入 primary，才进入 violation。"
            ),
            "## manual_audit_required\n"
            + (
                f"Manual-audit ids: {ids_for_status(cases, 'manual_audit_required')}.\n\n"
                "无法从 answer_eval、citation audit、trace slots 自动判断时才进入 manual_audit_required。"
                "P2 manual audit 不进入本轮 cases。"
            ),
            "## 为什么本轮不修 runtime\n"
            + (
                "本轮产物只是 policy 分类：`runtime_changed=false`，`prompt_changed=false`，"
                "`api_changed=false`，`frontend_changed=false`，`dataset_changed=false`。"
                "这不是系统全通过；这不是修 P2；这不是 prompt 修改。"
            ),
            "## 下一步建议\n"
            + md_table(
                ["bucket", "count", "next_action"],
                [
                    ["policy_accepted", summary["policy_accepted_count"], "none"],
                    [
                        "policy_needs_trace_improvement",
                        summary["policy_needs_trace_improvement_count"],
                        "improve_trace_evidence_slot_visibility",
                    ],
                    ["policy_violation", summary["policy_violation_count"], "repair in a later runtime task"],
                    ["manual_audit_required", summary["manual_audit_required_count"], "manual_audit_required"],
                ],
            ),
        ]
    ) + "\n"


def build_report(
    *,
    summary_json: Path,
    reclassified_json: Path,
    next_queue_json: Path,
    citation_audit_json: Path,
    answer_json: Path,
    trace_log: Path,
    dataset: Path,
    out_dir: Path,
    docs_md: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary_payload = load_json(summary_json)
    reclassified_payload = load_json(reclassified_json)
    next_queue_payload = load_json(next_queue_json)
    citation_audit_payload = load_json(citation_audit_json)
    answer_payload = load_json(answer_json)
    trace_rows = load_jsonl(trace_log)

    validate_scope(
        summary_payload=summary_payload,
        next_queue_payload=next_queue_payload,
        reclassified_payload=reclassified_payload,
    )
    cases = build_policy_cases(
        next_queue_payload=next_queue_payload,
        answer_payload=answer_payload,
        citation_audit_payload=citation_audit_payload,
        trace_rows=trace_rows,
    )
    summary = build_summary_payload(
        summary_json=summary_json,
        reclassified_json=reclassified_json,
        next_queue_json=next_queue_json,
        citation_audit_json=citation_audit_json,
        answer_json=answer_json,
        trace_log=trace_log,
        dataset=dataset,
        next_queue_payload=next_queue_payload,
        cases=cases,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    docs_md.parent.mkdir(parents=True, exist_ok=True)
    (out_dir / SUMMARY_JSON_NAME).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / CASES_JSON_NAME).write_text(
        json.dumps(cases, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    docs_md.write_text(render_markdown(summary, cases), encoding="utf-8")
    return summary, cases


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply the secondary/review citation policy to existing eval artifacts."
    )
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--reclassified-json", default=DEFAULT_RECLASSIFIED_JSON)
    parser.add_argument("--next-queue-json", default=DEFAULT_NEXT_QUEUE_JSON)
    parser.add_argument("--citation-audit-json", default=DEFAULT_CITATION_AUDIT_JSON)
    parser.add_argument("--answer-json", default=DEFAULT_ANSWER_JSON)
    parser.add_argument("--trace-log", default=DEFAULT_TRACE_LOG)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--docs-md", default=DEFAULT_DOCS_MD)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    out_dir = resolve_project_path(args.out_dir)
    docs_md = resolve_project_path(args.docs_md)
    summary, cases = build_report(
        summary_json=resolve_project_path(args.summary_json),
        reclassified_json=resolve_project_path(args.reclassified_json),
        next_queue_json=resolve_project_path(args.next_queue_json),
        citation_audit_json=resolve_project_path(args.citation_audit_json),
        answer_json=resolve_project_path(args.answer_json),
        trace_log=resolve_project_path(args.trace_log),
        dataset=resolve_project_path(args.dataset),
        out_dir=out_dir,
        docs_md=docs_md,
    )
    print(f"Wrote {display_path(out_dir / SUMMARY_JSON_NAME)}")
    print(f"Wrote {display_path(out_dir / CASES_JSON_NAME)}")
    print(f"Wrote {display_path(docs_md)}")
    print(
        f"Classified {summary['total_policy_decision_cases']} secondary/review policy cases: "
        f"accepted={summary['policy_accepted_count']}, "
        f"trace_improvement={summary['policy_needs_trace_improvement_count']}, "
        f"violation={summary['policy_violation_count']}, "
        f"manual_audit={summary['manual_audit_required_count']}."
    )
    if len(cases) != summary["total_policy_decision_cases"]:
        raise RuntimeError("case count mismatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
