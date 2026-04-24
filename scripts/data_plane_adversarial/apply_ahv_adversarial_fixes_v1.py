#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.answers.assembler import DEFAULT_DB_PATH, resolve_project_path  # noqa: E402


RUN_ID = "ahv_adversarial_regression_v1"
AHV_LAYER = "ambiguous_high_value_batch_safe_primary"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_adversarial"
DEFAULT_LEDGER_JSON = f"{DEFAULT_OUTPUT_DIR}/ahv_adversarial_fix_ledger_v1.json"
DEFAULT_LEDGER_MD = f"{DEFAULT_OUTPUT_DIR}/ahv_adversarial_fix_ledger_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply minimal AHV adversarial fixes v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger-json", default=DEFAULT_LEDGER_JSON)
    parser.add_argument("--ledger-md", default=DEFAULT_LEDGER_MD)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def table_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params)]


def append_note(existing: str, note: str) -> str:
    existing = str(existing or "").strip()
    if note in existing:
        return existing
    return f"{existing} {note}".strip()


def apply_match_mode_fix(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    before_rows = table_rows(
        conn,
        """
        SELECT lexicon_id, surface_form, target_term, target_id, match_mode, confidence, is_active, notes
        FROM learner_query_normalization_lexicon
        WHERE entry_type = 'term_surface'
          AND target_id IN (
              SELECT concept_id
              FROM definition_term_registry
              WHERE promotion_source_layer = ?
          )
        ORDER BY target_term, surface_form
        """,
        (AHV_LAYER,),
    )
    note = "ahv_adversarial_v1: active AHV learner surface uses exact matching; runtime blocks inactive alias primary."
    for row in before_rows:
        if int(row["is_active"]) != 1:
            continue
        conn.execute(
            """
            UPDATE learner_query_normalization_lexicon
            SET match_mode = 'exact',
                notes = ?
            WHERE lexicon_id = ?
            """,
            (append_note(row["notes"], note), row["lexicon_id"]),
        )
    after_rows = table_rows(
        conn,
        """
        SELECT lexicon_id, surface_form, target_term, target_id, match_mode, confidence, is_active, notes
        FROM learner_query_normalization_lexicon
        WHERE entry_type = 'term_surface'
          AND target_id IN (
              SELECT concept_id
              FROM definition_term_registry
              WHERE promotion_source_layer = ?
          )
        ORDER BY target_term, surface_form
        """,
        (AHV_LAYER,),
    )
    after_by_id = {row["lexicon_id"]: row for row in after_rows}
    changes: list[dict[str, Any]] = []
    for before in before_rows:
        after = after_by_id[before["lexicon_id"]]
        if before["match_mode"] != after["match_mode"] or before["notes"] != after["notes"]:
            changes.append(
                {
                    "lexicon_id": before["lexicon_id"],
                    "surface_form": before["surface_form"],
                    "target_term": before["target_term"],
                    "target_id": before["target_id"],
                    "is_active": before["is_active"],
                    "before": {
                        "match_mode": before["match_mode"],
                        "notes": before["notes"],
                    },
                    "after": {
                        "match_mode": after["match_mode"],
                        "notes": after["notes"],
                    },
                }
            )
    return changes


def write_snapshots(conn: sqlite3.Connection, output_dir: Path) -> dict[str, str]:
    snapshots = {
        "definition_term_registry": output_dir / "definition_term_registry_ahv_adversarial_v1_snapshot.json",
        "term_alias_registry": output_dir / "term_alias_registry_ahv_adversarial_v1_snapshot.json",
        "learner_query_normalization_lexicon": output_dir
        / "learner_query_normalization_ahv_adversarial_v1_snapshot.json",
    }
    write_json(
        snapshots["definition_term_registry"],
        table_rows(
            conn,
            """
            SELECT *
            FROM definition_term_registry
            WHERE promotion_source_layer = ?
            ORDER BY canonical_term, concept_id
            """,
            (AHV_LAYER,),
        ),
    )
    write_json(
        snapshots["term_alias_registry"],
        table_rows(
            conn,
            """
            SELECT *
            FROM term_alias_registry
            WHERE concept_id IN (
                SELECT concept_id
                FROM definition_term_registry
                WHERE promotion_source_layer = ?
            )
            ORDER BY canonical_term, alias
            """,
            (AHV_LAYER,),
        ),
    )
    write_json(
        snapshots["learner_query_normalization_lexicon"],
        table_rows(
            conn,
            """
            SELECT *
            FROM learner_query_normalization_lexicon
            WHERE target_id IN (
                SELECT concept_id
                FROM definition_term_registry
                WHERE promotion_source_layer = ?
            )
            ORDER BY target_term, surface_form
            """,
            (AHV_LAYER,),
        ),
    )
    return {key: str(path) for key, path in snapshots.items()}


def write_ledger(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    write_json(path_json, payload)
    lines = [
        "# AHV Adversarial Fix Ledger v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- db_path: `{payload['db_path']}`",
        f"- changed_learner_surface_count: `{payload['metrics']['changed_learner_surface_count']}`",
        f"- downgraded_object_count: `{payload['metrics']['downgraded_object_count']}`",
        f"- deactivated_alias_count: `{payload['metrics']['deactivated_alias_count']}`",
        "",
        "## Fixes",
        "",
        "- AHV active learner term surfaces are set to `match_mode=exact`.",
        "- Runtime support in `backend/retrieval/minimal.py` interprets AHV term aliases as exact-match only.",
        "- Runtime support blocks definition primary when a query exactly matches an inactive AHV alias.",
        "- No AHV object was added or downgraded in this fix pass.",
        "",
        "## Changed Learner Surfaces",
        "",
        "| target_term | surface_form | active | before | after |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["changes"]["learner_surface_match_mode"]:
        lines.append(
            f"| {row['target_term']} | {row['surface_form']} | {row['is_active']} | "
            f"{row['before']['match_mode']} | {row['after']['match_mode']} |"
        )
    lines.extend(
        [
            "",
            "## Snapshots",
            "",
        ]
    )
    for key, value in payload["snapshots"].items():
        lines.append(f"- {key}: `{value}`")
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    output_dir = resolve_project_path(args.output_dir)
    ledger_json = resolve_project_path(args.ledger_json)
    ledger_md = resolve_project_path(args.ledger_md)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        changes = apply_match_mode_fix(conn)
        conn.commit()
        snapshots = write_snapshots(conn, output_dir)
    finally:
        conn.close()
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "db_path": str(db_path),
        "metrics": {
            "changed_learner_surface_count": len(changes),
            "downgraded_object_count": 0,
            "deactivated_alias_count": 0,
            "new_ahv_object_count": 0,
        },
        "changes": {
            "learner_surface_match_mode": changes,
        },
        "runtime_fix": {
            "file": "backend/retrieval/minimal.py",
            "summary": "AHV aliases are exact-match only at runtime; inactive AHV aliases block definition primary.",
        },
        "snapshots": snapshots,
    }
    write_ledger(ledger_json, ledger_md, payload)
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
