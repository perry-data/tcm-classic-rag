#!/usr/bin/env python3
"""Build failure_report_v1 from frozen eval artifacts.

This is a report-only merge step. It consumes eval_dataset_v1,
retrieval_eval_v1, answer_eval_v1, and the saved qa_trace log. It does not run
retrieval, answer assembly, prompt code, or any judge.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "failure_report_v1"
DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_RETRIEVAL_JSON = REPO_ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
DEFAULT_ANSWER_JSON = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
DEFAULT_TRACE_LOG = REPO_ROOT / "artifacts" / "eval" / "answer_eval_v1" / "qa_trace_answer_eval_v1.jsonl"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

PRIMARY_FAILURE_PRIORITY = [
    "out_of_scope_not_rejected",
    "correct_chunk_not_retrieved",
    "correct_chunk_low_rank",
    "citation_missing",
    "citation_not_from_top_k",
    "gold_not_cited",
    "retrieved_but_answer_wrong",
    "expected_answer_mode_mismatch",
    "scope_qualifier_missing",
    "manual_audit_required",
]

WARNING_ONLY_FAILURES = {
    "scope_qualifier_missing",
    "expected_answer_mode_mismatch",
}

RECOMMENDED_ACTION_BY_FAILURE = {
    "correct_chunk_not_retrieved": "fix_retrieval_or_chunking",
    "correct_chunk_low_rank": "fix_rerank",
    "citation_missing": "fix_answer_assembly",
    "citation_not_from_top_k": "inspect_trace_or_citation_mapping",
    "gold_not_cited": "fix_citation_mapping_or_answer_assembly",
    "retrieved_but_answer_wrong": "manual_answer_audit_required",
    "expected_answer_mode_mismatch": "inspect_answer_mode_calibration",
    "scope_qualifier_missing": "consider_answer_template_scope_phrase",
    "out_of_scope_not_rejected": "add_refusal_guard",
    "manual_audit_required": "manual_audit_required",
}

RETRIEVAL_METRIC_FIELDS = [
    "hit_at_1",
    "hit_at_3",
    "hit_at_5",
    "mrr",
    "recall_at_5",
]

ANSWER_METRIC_FIELDS = [
    "has_citation_rate",
    "citation_from_top_k_rate",
    "gold_cited_rate",
    "refuse_when_should_not_answer_rate",
    "scope_qualified_rate",
    "answer_keyword_hit_rate",
    "expected_answer_mode_match_rate",
]


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
                    "gold_answer_keywords": split_pipe(row.get("gold_answer_keywords")),
                    "notes": (row.get("notes") or "").strip(),
                    "manual_audit_required": parse_bool(row.get("manual_audit_required")),
                    "subtype": (row.get("subtype") or "").strip(),
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


def classify_example(row: dict[str, Any]) -> str:
    if row["manual_audit_required"]:
        return "diagnostic_only"
    if not row["should_answer"]:
        return "unanswerable"
    if row["gold_chunk_ids"]:
        return "answerable_metric"
    return "diagnostic_only"


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


def validate_sources(
    dataset_rows: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
    answer_payload: dict[str, Any],
    trace_by_id: dict[str, dict[str, Any]],
) -> None:
    dataset_ids = [row["id"] for row in dataset_rows]
    retrieval_ids = [str(row.get("id") or "") for row in retrieval_payload.get("per_example") or []]
    answer_ids = [str(row.get("id") or "") for row in answer_payload.get("per_example") or []]
    if dataset_ids != retrieval_ids:
        raise ValueError("dataset and retrieval_eval per_example ids are not aligned")
    if dataset_ids != answer_ids:
        raise ValueError("dataset and answer_eval per_example ids are not aligned")
    if dataset_ids != list(trace_by_id):
        raise ValueError("dataset and trace log ids are not aligned")


def first_failure_type(failure_types: list[str]) -> str | None:
    for failure_type in PRIMARY_FAILURE_PRIORITY:
        if failure_type in failure_types:
            return failure_type
    return None


def severity_for(row: dict[str, Any], failure_types: list[str]) -> str:
    if row["manual_audit_required"]:
        return "diagnostic"
    if not failure_types:
        return "ok"
    if set(failure_types).issubset(WARNING_ONLY_FAILURES):
        return "warning"
    return "fail"


def summarize_example(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "category": row["category"],
        "question": row["question"],
        "example_class": row["example_class"],
        "severity": row["severity"],
        "primary_failure_type": row["primary_failure_type"],
        "all_failure_types": row["all_failure_types"],
        "recommended_next_action": row["recommended_next_action"],
    }


def trace_top_k_ids(record: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for item in (record.get("top_k_chunks") or [])[:5]:
        if not isinstance(item, dict):
            continue
        value = item.get("record_id") or item.get("chunk_id")
        if value:
            ids.append(str(value))
    return ids


def build_per_example(
    dataset_rows: list[dict[str, Any]],
    retrieval_by_id: dict[str, dict[str, Any]],
    answer_by_id: dict[str, dict[str, Any]],
    trace_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    per_example: list[dict[str, Any]] = []
    for dataset_row in dataset_rows:
        row_id = dataset_row["id"]
        retrieval_row = retrieval_by_id[row_id]
        answer_row = answer_by_id[row_id]
        trace_record = trace_by_id[row_id]
        example_class = classify_example(dataset_row)
        should_answer = dataset_row["should_answer"]
        manual_audit_required = dataset_row["manual_audit_required"]
        actual_answer_mode = answer_row.get("actual_answer_mode")
        if actual_answer_mode is None:
            actual_answer_mode = answer_row.get("answer_mode")
        answer_mode = str(actual_answer_mode or "unknown")

        retrieval_hit_at_5 = retrieval_row.get("hit_at_5")
        first_hit_rank = retrieval_row.get("first_hit_rank")
        has_citation = answer_row.get("has_citation")
        citation_from_top_k = answer_row.get("citation_from_top_k")
        gold_cited = answer_row.get("gold_cited")
        refuse_when_should_not_answer = answer_row.get("refuse_when_should_not_answer")
        scope_qualified = answer_row.get("scope_qualified")
        answer_keyword_hit = answer_row.get("answer_keyword_hit")
        expected_answer_mode_match = answer_row.get("expected_answer_mode_match")

        failure_types: list[str] = []
        if manual_audit_required:
            failure_types.append("manual_audit_required")
        elif example_class == "answerable_metric":
            if retrieval_hit_at_5 is False:
                failure_types.append("correct_chunk_not_retrieved")
            elif retrieval_hit_at_5 is True and isinstance(first_hit_rank, int) and first_hit_rank > 3:
                failure_types.append("correct_chunk_low_rank")

            if should_answer and answer_mode != "refuse" and has_citation is False:
                failure_types.append("citation_missing")
            if citation_from_top_k is False:
                failure_types.append("citation_not_from_top_k")
            if gold_cited is False:
                failure_types.append("gold_not_cited")
            if retrieval_hit_at_5 is True and answer_keyword_hit is False:
                failure_types.append("retrieved_but_answer_wrong")
            if dataset_row["expected_answer_mode"] and expected_answer_mode_match is False:
                failure_types.append("expected_answer_mode_mismatch")
            if scope_qualified is False:
                failure_types.append("scope_qualifier_missing")
        elif example_class == "unanswerable":
            if refuse_when_should_not_answer is False or answer_mode != "refuse":
                failure_types.append("out_of_scope_not_rejected")
            if dataset_row["expected_answer_mode"] and expected_answer_mode_match is False:
                failure_types.append("expected_answer_mode_mismatch")
            if scope_qualified is False:
                failure_types.append("scope_qualifier_missing")

        primary_failure_type = first_failure_type(failure_types)
        severity = severity_for(dataset_row, failure_types)
        recommended_next_action = (
            RECOMMENDED_ACTION_BY_FAILURE[primary_failure_type] if primary_failure_type else "none"
        )

        per_example.append(
            {
                "id": row_id,
                "category": dataset_row["category"],
                "question": dataset_row["question"],
                "should_answer": should_answer,
                "manual_audit_required": manual_audit_required,
                "example_class": example_class,
                "subtype": dataset_row["subtype"],
                "gold_chunk_ids": dataset_row["gold_chunk_ids"],
                "retrieval_hit_at_5": retrieval_hit_at_5,
                "first_hit_rank": first_hit_rank,
                "retrieval_top5_record_ids": retrieval_row.get("top5_record_ids") or [],
                "trace_top_k_record_ids": trace_top_k_ids(trace_record),
                "answer_mode": answer_mode,
                "expected_answer_mode": dataset_row["expected_answer_mode"],
                "has_citation": has_citation,
                "citation_ids": answer_row.get("citation_ids") or [],
                "citation_from_top_k": citation_from_top_k,
                "gold_cited": gold_cited,
                "refuse_when_should_not_answer": refuse_when_should_not_answer,
                "scope_qualified": scope_qualified,
                "answer_keyword_hit": answer_keyword_hit,
                "expected_answer_mode_match": expected_answer_mode_match,
                "primary_failure_type": primary_failure_type,
                "all_failure_types": failure_types,
                "severity": severity,
                "recommended_next_action": recommended_next_action,
                "final_answer_excerpt": answer_row.get("final_answer_excerpt") or "",
                "retrieval_notes": retrieval_row.get("notes") or "",
                "answer_notes": answer_row.get("notes") or "",
                "dataset_notes": dataset_row["notes"],
            }
        )
    return per_example


def build_payload(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    answer_json: Path,
    trace_log: Path,
    dataset_rows: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
    answer_payload: dict[str, Any],
    per_example: list[dict[str, Any]],
) -> dict[str, Any]:
    class_counts = Counter(row["example_class"] for row in per_example)
    severity_counts = Counter(row["severity"] for row in per_example)
    failure_type_counts = Counter(
        failure_type for row in per_example for failure_type in row["all_failure_types"]
    )
    formal_failure_type_counts = Counter(
        failure_type
        for row in per_example
        if row["severity"] == "fail" and row["example_class"] != "diagnostic_only"
        for failure_type in row["all_failure_types"]
    )
    recommended_next_action_counts = Counter(row["recommended_next_action"] for row in per_example)

    formal_failures = [
        row for row in per_example if row["severity"] == "fail" and row["example_class"] != "diagnostic_only"
    ]
    warning_examples = [row for row in per_example if row["severity"] == "warning"]
    diagnostic_examples = [row for row in per_example if row["severity"] == "diagnostic"]
    p2_diagnostic_examples = [row for row in diagnostic_examples if row.get("subtype") == "p2_residual"]

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": display_path(dataset_path),
        "retrieval_eval_source": display_path(retrieval_json),
        "answer_eval_source": display_path(answer_json),
        "trace_log": display_path(trace_log),
        "judge": {"type": "rules_only_artifact_merge", "llm_judge": False},
        "total_examples": len(dataset_rows),
        "answerable_metric_examples": class_counts["answerable_metric"],
        "diagnostic_only_examples": class_counts["diagnostic_only"],
        "unanswerable_examples": class_counts["unanswerable"],
        "formal_fail_count": len(formal_failures),
        "warning_count": severity_counts["warning"],
        "diagnostic_count": severity_counts["diagnostic"],
        "ok_count": severity_counts["ok"],
        "severity_counts": dict(sorted(severity_counts.items())),
        "failure_type_counts": dict(sorted(failure_type_counts.items())),
        "formal_failure_type_counts": dict(sorted(formal_failure_type_counts.items())),
        "recommended_next_action_counts": dict(sorted(recommended_next_action_counts.items())),
        "source_metric_summary": {
            "retrieval_eval_v1": {
                key: retrieval_payload.get(key)
                for key in [
                    "total_examples",
                    "answerable_metric_examples",
                    "diagnostic_only_examples",
                    "unanswerable_examples",
                    *RETRIEVAL_METRIC_FIELDS,
                ]
            },
            "answer_eval_v1": {
                key: answer_payload.get(key)
                for key in [
                    "total_examples",
                    "answerable_metric_examples",
                    "diagnostic_only_examples",
                    "unanswerable_examples",
                    *ANSWER_METRIC_FIELDS,
                ]
            },
        },
        "top_failure_examples": [summarize_example(row) for row in formal_failures],
        "warning_examples": [summarize_example(row) for row in warning_examples],
        "p2_diagnostic_examples": [summarize_example(row) for row in p2_diagnostic_examples],
        "citation_not_from_top_k_examples": [
            summarize_example(row) for row in per_example if "citation_not_from_top_k" in row["all_failure_types"]
        ],
        "gold_not_cited_examples": [
            summarize_example(row) for row in per_example if "gold_not_cited" in row["all_failure_types"]
        ],
        "scope_qualifier_missing_examples": [
            summarize_example(row) for row in per_example if "scope_qualifier_missing" in row["all_failure_types"]
        ],
        "answer_mode_mismatch_examples": [
            summarize_example(row)
            for row in per_example
            if "expected_answer_mode_mismatch" in row["all_failure_types"]
        ],
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
        ["id", "category", "question", "primary", "all_failure_types", "action"],
        [
            [
                row["id"],
                row["category"],
                row["question"],
                row["primary_failure_type"] or "",
                ", ".join(row["all_failure_types"]),
                row["recommended_next_action"],
            ]
            for row in rows
        ],
    )


def source_metric_table(metrics: dict[str, Any], fields: list[str]) -> str:
    return md_table(["metric", "value"], [[field, metrics.get(field)] for field in fields])


def render_markdown(payload: dict[str, Any]) -> str:
    retrieval_metrics = payload["source_metric_summary"]["retrieval_eval_v1"]
    answer_metrics = payload["source_metric_summary"]["answer_eval_v1"]
    per_example = payload["per_example"]
    formal_failures = [
        row for row in per_example if row["severity"] == "fail" and row["example_class"] != "diagnostic_only"
    ]
    warnings = [row for row in per_example if row["severity"] == "warning"]
    p2_diagnostics = payload["p2_diagnostic_examples"]
    citation_rows = [
        row for row in per_example if "citation_not_from_top_k" in row["all_failure_types"]
    ]
    gold_rows = [row for row in per_example if "gold_not_cited" in row["all_failure_types"]]

    next_action_rows = [
        [action, count]
        for action, count in sorted(payload["recommended_next_action_counts"].items())
        if action != "none"
    ]

    return "\n\n".join(
        [
            "# failure_report_v1",
            (
                "本报告只合并既有 eval 产物做失败归因，不运行问答链路，也不做系统修复。"
                "当前 answer_eval_v1 已暴露 citation_from_top_k_rate、scope_qualified_rate 等诊断信号，"
                "因此报告按样本列出问题来源。"
            ),
            "## 总览\n"
            + md_table(
                ["field", "value"],
                [
                    ["total_examples", payload["total_examples"]],
                    ["answerable_metric_examples", payload["answerable_metric_examples"]],
                    ["diagnostic_only_examples", payload["diagnostic_only_examples"]],
                    ["unanswerable_examples", payload["unanswerable_examples"]],
                    ["formal_fail_count", payload["formal_fail_count"]],
                    ["warning_count", payload["warning_count"]],
                    ["diagnostic_count", payload["diagnostic_count"]],
                    ["ok_count", payload["ok_count"]],
                ],
            ),
            "## retrieval_eval_v1 指标摘要\n"
            + source_metric_table(
                retrieval_metrics,
                [
                    "total_examples",
                    "answerable_metric_examples",
                    "diagnostic_only_examples",
                    "unanswerable_examples",
                    *RETRIEVAL_METRIC_FIELDS,
                ],
            ),
            "## answer_eval_v1 指标摘要\n"
            + source_metric_table(
                answer_metrics,
                [
                    "total_examples",
                    "answerable_metric_examples",
                    "diagnostic_only_examples",
                    "unanswerable_examples",
                    *ANSWER_METRIC_FIELDS,
                ],
            ),
            "## failure_type_counts\n" + count_table(payload["failure_type_counts"]),
            "## recommended_next_action_counts\n" + count_table(payload["recommended_next_action_counts"]),
            "## 正式 fail 样本列表\n" + examples_table(formal_failures),
            "## warning 样本列表\n" + examples_table(warnings),
            "## P2 diagnostic-only 样本列表\n" + examples_table(p2_diagnostics),
            "## citation_not_from_top_k 样本列表\n" + examples_table(citation_rows),
            "## gold_not_cited 样本列表\n" + examples_table(gold_rows),
            "## 下一轮建议\n"
            + md_table(
                ["recommended_next_action", "count"],
                next_action_rows,
            ),
        ]
    ) + "\n"


def build_failure_report(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    answer_json: Path,
    trace_log: Path,
    out_dir: Path,
) -> dict[str, Any]:
    dataset_rows = load_dataset(dataset_path)
    retrieval_payload = load_json(retrieval_json)
    answer_payload = load_json(answer_json)
    trace_records = load_trace_log(trace_log)
    trace_by_id = order_trace_records(dataset_rows, trace_records)
    validate_sources(dataset_rows, retrieval_payload, answer_payload, trace_by_id)

    retrieval_by_id = index_by_id(retrieval_payload.get("per_example") or [], source_name="retrieval_eval_v1")
    answer_by_id = index_by_id(answer_payload.get("per_example") or [], source_name="answer_eval_v1")
    per_example = build_per_example(dataset_rows, retrieval_by_id, answer_by_id, trace_by_id)
    payload = build_payload(
        dataset_path=dataset_path,
        retrieval_json=retrieval_json,
        answer_json=answer_json,
        trace_log=trace_log,
        dataset_rows=dataset_rows,
        retrieval_payload=retrieval_payload,
        answer_payload=answer_payload,
        per_example=per_example,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "failure_cases_v1.json"
    md_path = out_dir / "failure_cases_v1.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build failure_report_v1 from existing eval artifacts.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--retrieval-json", default=DEFAULT_RETRIEVAL_JSON)
    parser.add_argument("--answer-json", default=DEFAULT_ANSWER_JSON)
    parser.add_argument("--trace-log", default=DEFAULT_TRACE_LOG)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    payload = build_failure_report(
        dataset_path=resolve_project_path(args.dataset),
        retrieval_json=resolve_project_path(args.retrieval_json),
        answer_json=resolve_project_path(args.answer_json),
        trace_log=resolve_project_path(args.trace_log),
        out_dir=resolve_project_path(args.out_dir),
    )
    print(
        json.dumps(
            {
                "run_id": payload["run_id"],
                "total_examples": payload["total_examples"],
                "formal_fail_count": payload["formal_fail_count"],
                "warning_count": payload["warning_count"],
                "diagnostic_count": payload["diagnostic_count"],
                "ok_count": payload["ok_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
