#!/usr/bin/env python3
"""Validate the small eval_dataset_v1 CSV without running retrieval or answer eval."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "eval_dataset_v1"

REQUIRED_FIELDS = [
    "id",
    "category",
    "question",
    "gold_chunk_ids",
    "gold_answer",
    "should_answer",
]

ALLOWED_CATEGORIES = {
    "原文定位",
    "术语解释",
    "方剂关联",
    "症候检索",
    "注文理解",
    "超范围拒答",
}

ALLOWED_BOOL = {"true", "false"}
ALLOWED_ANSWER_MODES = {"", "strong", "weak_with_review_notice", "refuse"}

P2_RESIDUAL_QUERIES = {
    "少阴病是什么意思",
    "半表半里证和过经有什么不同",
    "荣气微和卫气衰有什么区别",
    "霍乱和伤寒有什么区别",
    "痓病和太阳病有什么不同",
}

DEFAULT_DB_PATH = REPO_ROOT / "artifacts" / "zjshl_v1.db"
DEFAULT_ARTIFACT_PATHS = [
    REPO_ROOT / "artifacts" / "full_chain_regression" / "full_chain_regression_results_v2.json",
    REPO_ROOT / "artifacts" / "full_chain_regression" / "full_chain_failure_cases_v2.json",
    REPO_ROOT / "artifacts" / "full_chain_regression" / "residual_repair_queue_after_p0_p1_v2.json",
    REPO_ROOT / "artifacts" / "full_chain_p0_repairs" / "p0_boundary_regression_v1.json",
    REPO_ROOT / "artifacts" / "full_chain_p1_repairs" / "p1_regression_v1.json",
    REPO_ROOT / "logs" / "qa_traces" / "qa_trace_2026-04-26.jsonl",
]

GOLD_ID_RE = re.compile(
    r"^(?:(?:safe|full|risk):[A-Za-z0-9_:-]+|ZJSHL-[A-Za-z0-9_-]+|FML-[A-Za-z0-9_-]+|DPO-[A-Za-z0-9_-]+|AHV-[A-Za-z0-9_-]+)$"
)


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _split_gold_ids(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [item.strip() for item in raw.split("|")]


def _parse_json_array(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.Error:
        return set()
    return {row[1] for row in rows}


def _add_column_values(
    conn: sqlite3.Connection,
    ids: set[str],
    table: str,
    columns: list[str],
) -> None:
    existing = _table_columns(conn, table)
    selected = [column for column in columns if column in existing]
    if not selected:
        return
    query = f"SELECT {', '.join(selected)} FROM {table}"
    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error:
        return
    for row in rows:
        for value in row:
            if isinstance(value, str) and value:
                ids.add(value)


def _add_json_array_values(
    conn: sqlite3.Connection,
    ids: set[str],
    table: str,
    columns: list[str],
) -> None:
    existing = _table_columns(conn, table)
    selected = [column for column in columns if column in existing]
    if not selected:
        return
    query = f"SELECT {', '.join(selected)} FROM {table}"
    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error:
        return
    for row in rows:
        for value in row:
            if isinstance(value, str):
                ids.update(_parse_json_array(value))


def collect_db_gold_ids(db_path: Path = DEFAULT_DB_PATH) -> set[str]:
    ids: set[str] = set()
    if not db_path.exists():
        return ids

    conn = sqlite3.connect(db_path)
    try:
        for table in [
            "records_chunks",
            "records_main_passages",
            "records_passages",
            "records_annotations",
            "risk_registry_ambiguous",
        ]:
            _add_column_values(
                conn,
                ids,
                table,
                [
                    "record_id",
                    "chunk_id",
                    "passage_id",
                    "annotation_id",
                    "source_record_id",
                    "linked_passage_id",
                ],
            )
            _add_json_array_values(
                conn,
                ids,
                table,
                ["source_passage_ids_json", "backref_target_ids_json"],
            )

        _add_column_values(
            conn,
            ids,
            "retrieval_ready_definition_view",
            [
                "concept_id",
                "primary_support_passage_id",
                "primary_source_record_id",
            ],
        )
        _add_json_array_values(
            conn,
            ids,
            "retrieval_ready_definition_view",
            [
                "definition_evidence_passage_ids_json",
                "explanation_evidence_passage_ids_json",
                "membership_evidence_passage_ids_json",
                "source_passage_ids_json",
            ],
        )

        for (concept_id,) in conn.execute(
            "SELECT concept_id FROM retrieval_ready_definition_view"
        ).fetchall():
            if concept_id:
                ids.add(f"safe:definition_terms:{concept_id}")

        _add_column_values(
            conn,
            ids,
            "retrieval_ready_formula_view",
            [
                "formula_id",
                "primary_formula_passage_id",
                "formula_span_start_passage_id",
                "formula_span_end_passage_id",
            ],
        )
        _add_json_array_values(
            conn,
            ids,
            "retrieval_ready_formula_view",
            ["source_passage_ids_json", "chapter_ids_json"],
        )
    finally:
        conn.close()

    return ids


def _collect_ids_from_json(value: Any, ids: set[str]) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _collect_ids_from_json(item, ids)
        return
    if isinstance(value, list):
        for item in value:
            _collect_ids_from_json(item, ids)
        return
    if isinstance(value, str) and GOLD_ID_RE.match(value):
        ids.add(value)


def collect_artifact_gold_ids(paths: list[Path] | None = None) -> set[str]:
    ids: set[str] = set()
    for path in paths or DEFAULT_ARTIFACT_PATHS:
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        _collect_ids_from_json(json.loads(line), ids)
                    except json.JSONDecodeError:
                        continue
            continue
        if path.suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            _collect_ids_from_json(data, ids)
    return ids


def read_dataset(dataset_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
        return rows, reader.fieldnames or []


def validate_dataset(
    dataset_path: Path,
    out_dir: Path,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "run_id": RUN_ID,
        "dataset_path": _display_path(dataset_path),
        "total_examples": 0,
        "category_counts": {},
        "should_answer_counts": {"true": 0, "false": 0},
        "expected_answer_mode_counts": {},
        "manual_audit_required_count": 0,
        "p2_residual_included": False,
        "missing_required_fields": [],
        "invalid_category_rows": [],
        "invalid_should_answer_rows": [],
        "missing_gold_rows": [],
        "unknown_gold_id_rows": [],
        "dataset_valid": False,
    }

    extra_errors: dict[str, Any] = {
        "dataset_exists": dataset_path.exists(),
        "duplicate_id_rows": [],
        "empty_question_rows": [],
        "invalid_expected_answer_mode_rows": [],
        "invalid_refuse_mode_rows": [],
        "invalid_manual_audit_required_rows": [],
        "manual_audit_note_rows": [],
        "invalid_gold_id_format_rows": [],
        "category_minimum_errors": [],
        "missing_p2_residual_queries": [],
        "pass_friendly_guard_errors": [],
    }

    if not dataset_path.exists():
        summary.update(extra_errors)
        return summary

    rows, fieldnames = read_dataset(dataset_path)
    summary["total_examples"] = len(rows)
    missing_fields = [field for field in REQUIRED_FIELDS if field not in fieldnames]
    summary["missing_required_fields"] = missing_fields

    category_counts = Counter(row.get("category", "") for row in rows)
    should_answer_counts = Counter(row.get("should_answer", "").lower() for row in rows)
    expected_mode_counts = Counter(row.get("expected_answer_mode", "") for row in rows)
    manual_audit_count = sum(
        1 for row in rows if row.get("manual_audit_required", "false").lower() == "true"
    )

    summary["category_counts"] = dict(sorted(category_counts.items()))
    summary["should_answer_counts"] = {
        "true": should_answer_counts.get("true", 0),
        "false": should_answer_counts.get("false", 0),
    }
    summary["expected_answer_mode_counts"] = dict(sorted(expected_mode_counts.items()))
    summary["manual_audit_required_count"] = manual_audit_count

    seen_ids: set[str] = set()
    known_gold_ids = collect_db_gold_ids(db_path) | collect_artifact_gold_ids()
    p2_seen = {row.get("question", "") for row in rows} & P2_RESIDUAL_QUERIES

    for index, row in enumerate(rows, start=2):
        row_id = row.get("id", f"row_{index}")
        category = row.get("category", "")
        should_answer = row.get("should_answer", "").lower()
        expected_mode = row.get("expected_answer_mode", "")
        manual_audit = row.get("manual_audit_required", "false").lower()
        notes = row.get("notes", "")
        gold_ids = _split_gold_ids(row.get("gold_chunk_ids", ""))

        if not row_id:
            row_id = f"row_{index}"
        if row_id in seen_ids:
            extra_errors["duplicate_id_rows"].append(row_id)
        seen_ids.add(row_id)

        if not row.get("question", ""):
            extra_errors["empty_question_rows"].append(row_id)

        if category not in ALLOWED_CATEGORIES:
            summary["invalid_category_rows"].append(row_id)

        if should_answer not in ALLOWED_BOOL:
            summary["invalid_should_answer_rows"].append(row_id)

        if expected_mode not in ALLOWED_ANSWER_MODES:
            extra_errors["invalid_expected_answer_mode_rows"].append(row_id)

        if should_answer == "false" and expected_mode not in {"", "refuse"}:
            extra_errors["invalid_refuse_mode_rows"].append(row_id)

        if manual_audit not in ALLOWED_BOOL:
            extra_errors["invalid_manual_audit_required_rows"].append(row_id)

        if should_answer == "true" and manual_audit != "true" and not gold_ids:
            summary["missing_gold_rows"].append(row_id)

        if manual_audit == "true":
            note_lower = notes.lower()
            if "manual audit" not in note_lower and "requires manual audit" not in note_lower:
                extra_errors["manual_audit_note_rows"].append(row_id)

        malformed = [gold_id for gold_id in gold_ids if not GOLD_ID_RE.match(gold_id)]
        if malformed or any(not gold_id for gold_id in gold_ids):
            extra_errors["invalid_gold_id_format_rows"].append(
                {"id": row_id, "invalid_ids": malformed or gold_ids}
            )

        unknown = [
            gold_id
            for gold_id in gold_ids
            if GOLD_ID_RE.match(gold_id) and gold_id not in known_gold_ids
        ]
        if unknown:
            summary["unknown_gold_id_rows"].append({"id": row_id, "unknown_ids": unknown})

    for category in sorted(ALLOWED_CATEGORIES):
        if category_counts.get(category, 0) < 5:
            extra_errors["category_minimum_errors"].append(
                {"category": category, "count": category_counts.get(category, 0)}
            )

    missing_p2 = sorted(P2_RESIDUAL_QUERIES - p2_seen)
    extra_errors["missing_p2_residual_queries"] = missing_p2
    summary["p2_residual_included"] = not missing_p2

    if summary["should_answer_counts"]["false"] < 5:
        extra_errors["pass_friendly_guard_errors"].append(
            "fewer than 5 refuse or negative-scope examples"
        )
    if expected_mode_counts.get("weak_with_review_notice", 0) < 1:
        extra_errors["pass_friendly_guard_errors"].append("no weak_with_review_notice examples")
    if manual_audit_count < len(P2_RESIDUAL_QUERIES):
        extra_errors["pass_friendly_guard_errors"].append(
            "manual audit count is lower than required P2 residual count"
        )

    summary.update(extra_errors)
    issue_keys = [
        "missing_required_fields",
        "invalid_category_rows",
        "invalid_should_answer_rows",
        "missing_gold_rows",
        "unknown_gold_id_rows",
        "duplicate_id_rows",
        "empty_question_rows",
        "invalid_expected_answer_mode_rows",
        "invalid_refuse_mode_rows",
        "invalid_manual_audit_required_rows",
        "manual_audit_note_rows",
        "invalid_gold_id_format_rows",
        "category_minimum_errors",
        "missing_p2_residual_queries",
        "pass_friendly_guard_errors",
    ]
    summary["dataset_valid"] = (
        summary["dataset_exists"]
        and summary["p2_residual_included"]
        and all(not summary[key] for key in issue_keys)
    )
    return summary


def write_summary(summary: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "eval_dataset_summary_v1.json"
    md_path = out_dir / "eval_dataset_summary_v1.md"

    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# eval_dataset_v1 Summary",
        "",
        f"- Dataset: `{summary['dataset_path']}`",
        f"- Total examples: {summary['total_examples']}",
        f"- Dataset valid: {str(summary['dataset_valid']).lower()}",
        f"- P2 residual included: {str(summary['p2_residual_included']).lower()}",
        f"- Manual audit required: {summary['manual_audit_required_count']}",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in summary["category_counts"].items():
        lines.append(f"- {category}: {count}")

    lines.extend(
        [
            "",
            "## Should Answer Counts",
            "",
            f"- true: {summary['should_answer_counts']['true']}",
            f"- false: {summary['should_answer_counts']['false']}",
            "",
            "## Expected Answer Mode Counts",
            "",
        ]
    )
    for mode, count in summary["expected_answer_mode_counts"].items():
        label = mode or "(empty)"
        lines.append(f"- {label}: {count}")

    lines.extend(
        [
            "",
            "## Validation Issues",
            "",
        ]
    )
    issue_keys = [
        "missing_required_fields",
        "invalid_category_rows",
        "invalid_should_answer_rows",
        "missing_gold_rows",
        "unknown_gold_id_rows",
        "duplicate_id_rows",
        "empty_question_rows",
        "invalid_expected_answer_mode_rows",
        "invalid_refuse_mode_rows",
        "invalid_manual_audit_required_rows",
        "manual_audit_note_rows",
        "invalid_gold_id_format_rows",
        "category_minimum_errors",
        "missing_p2_residual_queries",
        "pass_friendly_guard_errors",
    ]
    issue_found = False
    for key in issue_keys:
        value = summary.get(key, [])
        if value:
            issue_found = True
            lines.append(f"- {key}: `{json.dumps(value, ensure_ascii=False)}`")
    if not issue_found:
        lines.append("- none")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--db", default=DEFAULT_DB_PATH, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    dataset_path = args.dataset if args.dataset.is_absolute() else REPO_ROOT / args.dataset
    out_dir = args.out_dir if args.out_dir.is_absolute() else REPO_ROOT / args.out_dir
    db_path = args.db if args.db.is_absolute() else REPO_ROOT / args.db

    summary = validate_dataset(dataset_path=dataset_path, out_dir=out_dir, db_path=db_path)
    write_summary(summary, out_dir)
    return 0 if summary["dataset_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
