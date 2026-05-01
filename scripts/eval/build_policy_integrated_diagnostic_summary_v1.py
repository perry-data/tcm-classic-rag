#!/usr/bin/env python3
"""Build the policy-integrated eval diagnostic summary from existing artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "eval_diagnostic_loop_policy_integrated_v1"

DEFAULT_LOOP_SUMMARY_JSON = (
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
DEFAULT_SECONDARY_POLICY_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "secondary_review_citation_policy_v1"
    / "secondary_review_citation_policy_v1.json"
)
DEFAULT_SECONDARY_POLICY_CASES_JSON = (
    REPO_ROOT
    / "artifacts"
    / "eval"
    / "secondary_review_citation_policy_v1"
    / "secondary_review_policy_cases_v1.json"
)
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

SUMMARY_JSON_NAME = "eval_diagnostic_loop_policy_integrated_summary_v1.json"
SUMMARY_MD_NAME = "eval_diagnostic_loop_policy_integrated_summary_v1.md"
NEXT_QUEUE_JSON_NAME = "next_repair_queue_policy_integrated_v1.json"

POLICY_RETRIEVAL_NOTE = (
    "policy accepted 只解决 secondary/review citation policy，不代表 retrieval/chunking 已修。"
)

DEFERRED_QUEUE_NAMES = (
    "answer_mode_calibration_observations",
    "scope_phrase_warnings",
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows_ids(rows: Iterable[dict[str, Any]]) -> list[str]:
    return [str(row.get("id") or "") for row in rows if row.get("id")]


def require_dict(payload: Any, *, source_name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{source_name} must be a JSON object")
    return payload


def require_list(payload: Any, *, source_name: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError(f"{source_name} must be a JSON array")
    result: list[dict[str, Any]] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise ValueError(f"{source_name}[{index}] must be a JSON object")
        result.append(row)
    return result


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


def append_note(row: dict[str, Any], note: str) -> dict[str, Any]:
    updated = deepcopy(row)
    existing = str(updated.get("notes") or "").strip()
    if note not in existing:
        updated["notes"] = f"{existing} {note}".strip() if existing else note
    return updated


def concise_case(row: dict[str, Any], *, retrieval_overlap: bool) -> dict[str, Any]:
    keys = (
        "id",
        "category",
        "question",
        "answer_mode",
        "policy_status",
        "recommended_next_action",
        "also_in_next_queue",
        "notes",
    )
    result = {key: deepcopy(row.get(key)) for key in keys if key in row}
    if retrieval_overlap:
        result = append_note(result, POLICY_RETRIEVAL_NOTE)
    return result


def merge_deferred_observations(next_queue_payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    source_queues: dict[str, list[str]] = defaultdict(list)
    for queue_name in DEFERRED_QUEUE_NAMES:
        for row in next_queue_payload.get(queue_name) or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            row_id = str(row["id"])
            by_id.setdefault(row_id, deepcopy(row))
            source_queues[row_id].append(queue_name)

    result: list[dict[str, Any]] = []
    for row_id in sorted(by_id):
        row = by_id[row_id]
        row["source_queues"] = source_queues[row_id]
        result.append(row)
    return result


def build_policy_integrated_queue(
    *,
    next_queue_payload: dict[str, Any],
    policy_cases: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    accepted_cases = [case for case in policy_cases if case.get("policy_status") == "policy_accepted"]
    accepted_ids = set(rows_ids(accepted_cases))
    runtime_rows = deepcopy(next_queue_payload.get("runtime_citation_scope_repairs") or [])
    runtime_ids = set(rows_ids(runtime_rows))
    runtime_policy_overlap = sorted(accepted_ids & runtime_ids)
    if runtime_policy_overlap:
        raise ValueError(
            "policy accepted ids must not enter runtime_citation_scope_repairs: "
            + ", ".join(runtime_policy_overlap)
        )

    retrieval_rows: list[dict[str, Any]] = []
    retrieval_ids = set(rows_ids(next_queue_payload.get("retrieval_or_chunking_repairs") or []))
    for row in next_queue_payload.get("retrieval_or_chunking_repairs") or []:
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("id") or "")
        if row_id in accepted_ids:
            retrieval_rows.append(append_note(row, POLICY_RETRIEVAL_NOTE))
        else:
            retrieval_rows.append(deepcopy(row))

    policy_rows = [
        concise_case(case, retrieval_overlap=str(case.get("id") or "") in retrieval_ids)
        for case in accepted_cases
    ]

    return {
        "runtime_citation_scope_repairs": runtime_rows,
        "trace_or_evaluator_repairs": deepcopy(next_queue_payload.get("trace_or_evaluator_repairs") or []),
        "retrieval_or_chunking_repairs": retrieval_rows,
        "policy_accepted_no_runtime_repair": policy_rows,
        "p2_manual_audit": deepcopy(next_queue_payload.get("p2_manual_audit") or []),
        "deferred_observations": merge_deferred_observations(next_queue_payload),
    }


def validate_inputs(
    *,
    loop_summary: dict[str, Any],
    reclassified: dict[str, Any],
    next_queue: dict[str, Any],
    secondary_policy: dict[str, Any],
    policy_cases: list[dict[str, Any]],
) -> None:
    if loop_summary.get("no_llm") is not True:
        raise ValueError("loop summary must record no_llm=true")
    if secondary_policy.get("run_id") != "secondary_review_citation_policy_v1":
        raise ValueError("unexpected secondary policy run_id")

    queue_policy_ids = set(rows_ids(next_queue.get("secondary_review_policy_decisions") or []))
    case_ids = set(rows_ids(policy_cases))
    if queue_policy_ids != case_ids:
        raise ValueError("secondary policy cases do not match next queue policy decisions")

    accepted_ids_from_summary = set(str(item) for item in secondary_policy.get("policy_accepted_ids") or [])
    accepted_ids_from_cases = {
        str(row.get("id") or "") for row in policy_cases if row.get("policy_status") == "policy_accepted"
    }
    if accepted_ids_from_summary != accepted_ids_from_cases:
        raise ValueError("policy accepted ids differ between summary and cases")

    if reclassified.get("total_examples") != loop_summary.get("dataset", {}).get("total_examples"):
        raise ValueError("total_examples differs between loop summary and reclassified report")


def build_summary(
    *,
    loop_summary_path: Path,
    reclassified_path: Path,
    next_queue_path: Path,
    secondary_policy_path: Path,
    secondary_policy_cases_path: Path,
    loop_summary: dict[str, Any],
    reclassified: dict[str, Any],
    secondary_policy: dict[str, Any],
    next_queue: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    runtime_rows = next_queue["runtime_citation_scope_repairs"]
    tooling_rows = next_queue["trace_or_evaluator_repairs"]
    retrieval_rows = next_queue["retrieval_or_chunking_repairs"]
    accepted_rows = next_queue["policy_accepted_no_runtime_repair"]
    p2_rows = next_queue["p2_manual_audit"]

    policy_blocking_count = int(secondary_policy.get("policy_violation_count") or 0) + int(
        secondary_policy.get("policy_needs_trace_improvement_count") or 0
    )
    source_paths = {
        "source_loop_summary": loop_summary_path,
        "source_reclassified_report": reclassified_path,
        "source_next_queue": next_queue_path,
        "source_secondary_policy": secondary_policy_path,
        "source_secondary_policy_cases": secondary_policy_cases_path,
    }

    total_examples = int(loop_summary.get("dataset", {}).get("total_examples") or reclassified["total_examples"])
    runtime_count = len(runtime_rows)
    tooling_count = len(tooling_rows)
    retrieval_count = len(retrieval_rows)
    diagnostic_count = len(p2_rows)

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_loop_summary": display_path(loop_summary_path),
        "source_reclassified_report": display_path(reclassified_path),
        "source_secondary_policy": display_path(secondary_policy_path),
        "source_artifacts": {name: display_path(path) for name, path in source_paths.items()},
        "source_sha256": {name: sha256_file(path) for name, path in source_paths.items()},
        "total_examples": total_examples,
        "original_failure_report_formal_fail_count": int(
            reclassified["original_formal_fail_count"]
        ),
        "reclassified_formal_fail_count_before_policy": int(
            reclassified["reclassified_formal_fail_count"]
        ),
        "retrieval_eval_hit_at_5": loop_summary.get("retrieval", {}).get("hit_at_5"),
        "answer_eval_citation_from_top_k_rate": loop_summary.get("answer", {}).get(
            "citation_from_top_k_rate"
        ),
        "secondary_review_policy_decision_count": int(
            secondary_policy["total_policy_decision_cases"]
        ),
        "secondary_review_policy_accepted_count": int(secondary_policy["policy_accepted_count"]),
        "secondary_review_policy_violation_count": int(secondary_policy["policy_violation_count"]),
        "secondary_review_policy_needs_trace_improvement_count": int(
            secondary_policy["policy_needs_trace_improvement_count"]
        ),
        "secondary_review_policy_warning_resolution": (
            "accepted"
            if int(secondary_policy["policy_accepted_count"])
            == int(secondary_policy["total_policy_decision_cases"])
            and policy_blocking_count == 0
            else "not_fully_accepted"
        ),
        "policy_integrated_runtime_bug_count": runtime_count,
        "policy_integrated_tooling_issue_count": tooling_count,
        "policy_integrated_retrieval_or_chunking_repair_count": retrieval_count,
        "policy_integrated_policy_blocking_count": policy_blocking_count,
        "policy_integrated_diagnostic_count": diagnostic_count,
        "policy_accepted_ids": rows_ids(accepted_rows),
        "runtime_citation_bug_ids": rows_ids(runtime_rows),
        "trace_or_evaluator_issue_ids": rows_ids(tooling_rows),
        "retrieval_or_chunking_repair_ids": rows_ids(retrieval_rows),
        "p2_manual_audit_ids": rows_ids(p2_rows),
        "policy_cases_also_in_retrieval_or_chunking_repairs": [
            row_id for row_id in rows_ids(accepted_rows) if row_id in set(rows_ids(retrieval_rows))
        ],
        "system_all_passed": not any(
            [
                runtime_count,
                tooling_count,
                retrieval_count,
                policy_blocking_count,
                diagnostic_count,
                next_queue["deferred_observations"],
            ]
        ),
        "runtime_changed": False,
        "prompt_changed": False,
        "api_changed": False,
        "frontend_changed": False,
        "dataset_changed": False,
        "existing_evaluator_changed": False,
        "judge": {"type": "rules_only_artifact_summary", "llm_judge": False},
        "report_scope": {
            "source_artifacts_only": True,
            "runs_retrieval": False,
            "runs_answer_generation": False,
            "runs_answer_assembly": False,
            "modifies_runtime": False,
        },
        "next_queue_counts": {queue_name: len(rows) for queue_name, rows in next_queue.items()},
        "notes": [
            "9 条 secondary/review policy warning 已被 policy 接受，不进入 runtime repair queue。",
            "policy accepted 不等于所有相关样本都没有别的问题。",
            "eval_026 policy accepted，但仍保留 retrieval/chunking repair 观察。",
            "这不是系统全通过。",
            "本轮不修 runtime、不改 prompt、不改 API、不改前端。",
        ],
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


def rows_table(rows: list[dict[str, Any]]) -> str:
    return md_table(
        ["id", "category", "question", "next_action", "notes"],
        [
            [
                row.get("id"),
                row.get("category"),
                row.get("question"),
                row.get("recommended_next_action"),
                row.get("notes"),
            ]
            for row in rows
        ],
    )


def render_markdown(summary: dict[str, Any], next_queue: dict[str, list[dict[str, Any]]]) -> str:
    accepted_rows = next_queue["policy_accepted_no_runtime_repair"]
    runtime_rows = next_queue["runtime_citation_scope_repairs"]
    tooling_rows = next_queue["trace_or_evaluator_repairs"]
    retrieval_rows = next_queue["retrieval_or_chunking_repairs"]
    p2_rows = next_queue["p2_manual_audit"]
    deferred_rows = next_queue["deferred_observations"]

    return "\n\n".join(
        [
            "# eval_diagnostic_loop_policy_integrated_summary_v1",
            "## 本轮目标\n"
            "把 `secondary_review_citation_policy_v1` 的结果纳入最终诊断总览，只更新 summary 和 next queue。"
            "这不是系统全通过；本轮不修 runtime、不改 prompt、不改 API、不改前端。"
            "本轮也不改 retrieval、trace、existing evaluator 或 dataset。",
            "## 输入 artifacts\n"
            + md_table(
                ["name", "path"],
                [
                    ["loop_summary", summary["source_loop_summary"]],
                    ["reclassified_report", summary["source_reclassified_report"]],
                    ["secondary_policy", summary["source_secondary_policy"]],
                    [
                        "next_queue_after_citation_audit",
                        summary["source_artifacts"]["source_next_queue"],
                    ],
                    [
                        "secondary_policy_cases",
                        summary["source_artifacts"]["source_secondary_policy_cases"],
                    ],
                ],
            ),
            "## 旧 reclassified summary\n"
            + md_table(
                ["field", "value"],
                [
                    ["total_examples", summary["total_examples"]],
                    [
                        "failure_report_v1 formal_fail_count",
                        summary["original_failure_report_formal_fail_count"],
                    ],
                    [
                        "reclassified_formal_fail_count_before_policy",
                        summary["reclassified_formal_fail_count_before_policy"],
                    ],
                    ["retrieval_eval_v1 Hit@5", summary["retrieval_eval_hit_at_5"]],
                    [
                        "answer_eval_v1 citation_from_top_k_rate",
                        summary["answer_eval_citation_from_top_k_rate"],
                    ],
                ],
            ),
            "## secondary_review_citation_policy_v1 结果\n"
            + md_table(
                ["field", "value"],
                [
                    [
                        "secondary_review_policy_decision_count",
                        summary["secondary_review_policy_decision_count"],
                    ],
                    [
                        "secondary_review_policy_accepted_count",
                        summary["secondary_review_policy_accepted_count"],
                    ],
                    [
                        "secondary_review_policy_violation_count",
                        summary["secondary_review_policy_violation_count"],
                    ],
                    [
                        "secondary_review_policy_needs_trace_improvement_count",
                        summary["secondary_review_policy_needs_trace_improvement_count"],
                    ],
                    ["policy_integrated_policy_blocking_count", summary["policy_integrated_policy_blocking_count"]],
                ],
            )
            + "\n\n9 条 secondary/review policy warning 已被 policy 接受。它们不再进入 runtime repair queue。",
            "## policy-integrated 后的真实待办队列\n"
            + md_table(
                ["queue", "count", "ids"],
                [
                    [
                        "runtime_citation_scope_repairs",
                        len(runtime_rows),
                        ", ".join(rows_ids(runtime_rows)),
                    ],
                    [
                        "trace_or_evaluator_repairs",
                        len(tooling_rows),
                        ", ".join(rows_ids(tooling_rows)),
                    ],
                    [
                        "retrieval_or_chunking_repairs",
                        len(retrieval_rows),
                        ", ".join(rows_ids(retrieval_rows)),
                    ],
                    [
                        "policy_accepted_no_runtime_repair",
                        len(accepted_rows),
                        ", ".join(rows_ids(accepted_rows)),
                    ],
                    ["p2_manual_audit", len(p2_rows), ", ".join(rows_ids(p2_rows))],
                    [
                        "deferred_observations",
                        len(deferred_rows),
                        ", ".join(rows_ids(deferred_rows)),
                    ],
                ],
            )
            + "\n\npolicy accepted 不等于所有相关样本都没有别的问题。"
            "eval_026 policy accepted，但仍保留 retrieval/chunking repair 观察。",
            "## 9 条 policy accepted 列表\n" + rows_table(accepted_rows),
            "## 3 条 runtime citation bug 列表\n" + rows_table(runtime_rows),
            "## 2 条 trace/evaluator issue 列表\n" + rows_table(tooling_rows),
            "## retrieval/chunking repair 列表\n" + rows_table(retrieval_rows),
            "## 5 条 P2 manual audit 列表\n" + rows_table(p2_rows),
            "## deferred observations\n"
            + rows_table(deferred_rows)
            + "\n\n这些 observation 不改变本轮 runtime citation repair、tooling repair、policy accepted 或 P2 diagnostic 的分流。",
            "## 下一步建议\n"
            "- runtime citation repair 仍只处理 eval_023 / eval_025 / eval_027。\n"
            "- trace/evaluator tooling repair 仍只处理 eval_002 / eval_009。\n"
            "- retrieval/chunking repair 队列继续保留，不因 policy accepted 被吞掉。\n"
            "- P2 manual audit 仍是 diagnostic，不进入 formal runtime repair。\n"
            "- 保持 `system_all_passed=false`；下一轮若修复，应按 queue 分流单独开任务。",
        ]
    ) + "\n"


def build_report(
    *,
    loop_summary_json: Path,
    reclassified_json: Path,
    next_queue_json: Path,
    secondary_policy_json: Path,
    secondary_policy_cases_json: Path,
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    loop_summary = require_dict(load_json(loop_summary_json), source_name=display_path(loop_summary_json))
    reclassified = require_dict(load_json(reclassified_json), source_name=display_path(reclassified_json))
    original_next_queue = require_dict(load_json(next_queue_json), source_name=display_path(next_queue_json))
    secondary_policy = require_dict(
        load_json(secondary_policy_json),
        source_name=display_path(secondary_policy_json),
    )
    policy_cases = require_list(
        load_json(secondary_policy_cases_json),
        source_name=display_path(secondary_policy_cases_json),
    )

    validate_inputs(
        loop_summary=loop_summary,
        reclassified=reclassified,
        next_queue=original_next_queue,
        secondary_policy=secondary_policy,
        policy_cases=policy_cases,
    )
    next_queue = build_policy_integrated_queue(
        next_queue_payload=original_next_queue,
        policy_cases=policy_cases,
    )
    summary = build_summary(
        loop_summary_path=loop_summary_json,
        reclassified_path=reclassified_json,
        next_queue_path=next_queue_json,
        secondary_policy_path=secondary_policy_json,
        secondary_policy_cases_path=secondary_policy_cases_json,
        loop_summary=loop_summary,
        reclassified=reclassified,
        secondary_policy=secondary_policy,
        next_queue=next_queue,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / SUMMARY_JSON_NAME).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / NEXT_QUEUE_JSON_NAME).write_text(
        json.dumps(next_queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / SUMMARY_MD_NAME).write_text(render_markdown(summary, next_queue), encoding="utf-8")
    return summary, next_queue


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loop-summary-json", default=DEFAULT_LOOP_SUMMARY_JSON)
    parser.add_argument("--reclassified-json", default=DEFAULT_RECLASSIFIED_JSON)
    parser.add_argument("--next-queue-json", default=DEFAULT_NEXT_QUEUE_JSON)
    parser.add_argument("--secondary-policy-json", default=DEFAULT_SECONDARY_POLICY_JSON)
    parser.add_argument("--secondary-policy-cases-json", default=DEFAULT_SECONDARY_POLICY_CASES_JSON)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    out_dir = resolve_project_path(args.out_dir)
    summary, next_queue = build_report(
        loop_summary_json=resolve_project_path(args.loop_summary_json),
        reclassified_json=resolve_project_path(args.reclassified_json),
        next_queue_json=resolve_project_path(args.next_queue_json),
        secondary_policy_json=resolve_project_path(args.secondary_policy_json),
        secondary_policy_cases_json=resolve_project_path(args.secondary_policy_cases_json),
        out_dir=out_dir,
    )
    print(f"Wrote {display_path(out_dir / SUMMARY_JSON_NAME)}")
    print(f"Wrote {display_path(out_dir / SUMMARY_MD_NAME)}")
    print(f"Wrote {display_path(out_dir / NEXT_QUEUE_JSON_NAME)}")
    print(
        f"Integrated policy decisions={summary['secondary_review_policy_decision_count']}; "
        f"accepted_no_runtime_repair={len(next_queue['policy_accepted_no_runtime_repair'])}; "
        f"runtime_repairs={summary['policy_integrated_runtime_bug_count']}; "
        f"tooling_repairs={summary['policy_integrated_tooling_issue_count']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
