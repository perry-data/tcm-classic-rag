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

from backend.retrieval.minimal import DEFAULT_DB_PATH, resolve_project_path  # noqa: E402
from scripts.data_plane_batch_upgrade_v2.run_ambiguous_high_value_evidence_upgrade_v2 import (  # noqa: E402
    AHV2_SAFE_LAYER,
    AHV2_SUPPORT_LAYER,
)


RUN_ID = "ahv2_adversarial_fixes_v1"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_batch_upgrade_v2"
DEFAULT_LEDGER_JSON = f"{DEFAULT_OUTPUT_DIR}/ahv2_fix_ledger_v1.json"
DEFAULT_LEDGER_MD = f"{DEFAULT_OUTPUT_DIR}/ahv2_fix_ledger_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply minimal AHV2 adversarial fixes.")
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


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def table_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params)]


def append_note(existing: str, note: str) -> str:
    existing = str(existing or "").strip()
    if note in existing:
        return existing
    return f"{existing} {note}".strip()


def fix_active_contains(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = table_rows(
        conn,
        """
        SELECT lexicon_id, surface_form, target_term, target_id, match_mode, notes
        FROM learner_query_normalization_lexicon
        WHERE is_active = 1
          AND match_mode != 'exact'
          AND target_id IN (
              SELECT concept_id
              FROM definition_term_registry
              WHERE promotion_source_layer = ?
          )
        ORDER BY target_term, surface_form
        """,
        (AHV2_SAFE_LAYER,),
    )
    changes: list[dict[str, Any]] = []
    note = "ahv2_adversarial_fixes_v1: active AHV2 learner surface forced to exact."
    for row in rows:
        conn.execute(
            """
            UPDATE learner_query_normalization_lexicon
            SET match_mode = 'exact',
                notes = ?
            WHERE lexicon_id = ?
            """,
            (append_note(row["notes"], note), row["lexicon_id"]),
        )
        changes.append(
            {
                "lexicon_id": row["lexicon_id"],
                "surface_form": row["surface_form"],
                "target_term": row["target_term"],
                "before_match_mode": row["match_mode"],
                "after_match_mode": "exact",
            }
        )
    return changes


def deactivate_unsafe_aliases(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = table_rows(
        conn,
        """
        SELECT alias_id, alias, normalized_alias, canonical_term, concept_id, alias_type, is_active, notes
        FROM term_alias_registry
        WHERE source = 'ambiguous_high_value_evidence_upgrade_v2'
          AND is_active = 1
          AND (
              LENGTH(normalized_alias) < 2
              OR alias_type IN ('learner_risky', 'ambiguous', 'review_only_support')
              OR concept_id IN (
                  SELECT concept_id
                  FROM definition_term_registry
                  WHERE promotion_source_layer = ?
              )
          )
        ORDER BY canonical_term, alias
        """,
        (AHV2_SUPPORT_LAYER,),
    )
    changes: list[dict[str, Any]] = []
    note = "ahv2_adversarial_fixes_v1: unsafe/review alias deactivated."
    for row in rows:
        conn.execute(
            """
            UPDATE term_alias_registry
            SET is_active = 0,
                notes = ?
            WHERE alias_id = ?
            """,
            (append_note(row["notes"], note), row["alias_id"]),
        )
        changes.append(
            {
                "alias_id": row["alias_id"],
                "alias": row["alias"],
                "canonical_term": row["canonical_term"],
                "alias_type": row["alias_type"],
                "before_is_active": row["is_active"],
                "after_is_active": 0,
            }
        )
    return changes


def write_snapshots(conn: sqlite3.Connection, output_dir: Path) -> dict[str, str]:
    snapshots = {
        "definition_term_registry": output_dir / "definition_term_registry_ahv2_snapshot.json",
        "term_alias_registry": output_dir / "term_alias_registry_ahv2_snapshot.json",
        "learner_query_normalization_lexicon": output_dir / "learner_query_normalization_ahv2_snapshot.json",
        "sentence_role_registry": output_dir / "sentence_role_registry_ahv2_snapshot.json",
    }
    write_json(
        snapshots["definition_term_registry"],
        table_rows(conn, "SELECT * FROM definition_term_registry ORDER BY canonical_term, concept_id"),
    )
    write_json(
        snapshots["term_alias_registry"],
        table_rows(conn, "SELECT * FROM term_alias_registry ORDER BY canonical_term, alias, alias_id"),
    )
    write_json(
        snapshots["learner_query_normalization_lexicon"],
        table_rows(
            conn,
            "SELECT * FROM learner_query_normalization_lexicon ORDER BY entry_type, surface_form, target_term",
        ),
    )
    write_json(
        snapshots["sentence_role_registry"],
        table_rows(conn, "SELECT * FROM sentence_role_registry ORDER BY source_table, passage_id, sentence_index"),
    )
    return {key: str(path) for key, path in snapshots.items()}


def write_ledger(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    write_json(path_json, payload)
    lines = [
        "# AHV2 Fix Ledger v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- changed_learner_surface_count: `{payload['metrics']['changed_learner_surface_count']}`",
        f"- deactivated_alias_count: `{payload['metrics']['deactivated_alias_count']}`",
        f"- downgraded_object_count: `{payload['metrics']['downgraded_object_count']}`",
        "",
        "## Runtime Safety",
        "",
        "- `backend/retrieval/minimal.py` treats AHV v1 and AHV2 promotion layers as exact-match layers.",
        "- AHV definition objects are skipped from raw text-match collection unless exact term normalization already selected that concept.",
        "- `backend/answers/assembler.py` keeps definition-outline payload metadata intact and prefers the exact definition object when one was selected by term normalization.",
        "",
        "## Learner Surface Fixes",
        "",
    ]
    if payload["changes"]["learner_surface_match_mode"]:
        for row in payload["changes"]["learner_surface_match_mode"]:
            lines.append(f"- `{row['target_term']}` / `{row['surface_form']}`: {row['before_match_mode']} -> exact")
    else:
        lines.append("- none")
    lines.extend(["", "## Alias Fixes", ""])
    if payload["changes"]["deactivated_aliases"]:
        for row in payload["changes"]["deactivated_aliases"]:
            lines.append(f"- `{row['canonical_term']}` / `{row['alias']}`: active -> inactive")
    else:
        lines.append("- none")
    write_md(path_md, lines)


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    output_dir = resolve_project_path(args.output_dir)
    ledger_json = resolve_project_path(args.ledger_json)
    ledger_md = resolve_project_path(args.ledger_md)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            learner_changes = fix_active_contains(conn)
            alias_changes = deactivate_unsafe_aliases(conn)
        snapshots = write_snapshots(conn, output_dir)
    finally:
        conn.close()

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "db_path": str(db_path),
        "metrics": {
            "changed_learner_surface_count": len(learner_changes),
            "deactivated_alias_count": len(alias_changes),
            "downgraded_object_count": 0,
            "new_ahv2_object_count": 0,
        },
        "changes": {
            "learner_surface_match_mode": learner_changes,
            "deactivated_aliases": alias_changes,
        },
        "runtime_fixes": [
            {
                "file": "backend/retrieval/minimal.py",
                "summary": "AHV v1/v2 layers use exact alias matching and are not collected as raw text-match definition candidates without exact normalization.",
            },
            {
                "file": "backend/answers/assembler.py",
                "summary": "Definition-outline assembly carries query_request metadata and uses an exact definition object as primary when term normalization selected it.",
            },
        ],
        "snapshots": snapshots,
    }
    write_ledger(ledger_json, ledger_md, payload)
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
