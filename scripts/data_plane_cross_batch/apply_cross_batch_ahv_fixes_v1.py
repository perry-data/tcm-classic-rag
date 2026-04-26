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
from scripts.data_plane_cross_batch.run_cross_batch_ahv_consistency_audit_v1 import (  # noqa: E402
    AHV_SAFE_LAYERS,
    CROSS_BATCH_SCOPE_BY_CONCEPT_TYPE,
    EXPECTED_PRIMARY_TYPE_BY_CONCEPT_TYPE,
    expected_primary_evidence_type,
    expected_primary_type_note,
)


RUN_ID = "cross_batch_ahv_fixes_v1"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_cross_batch"
DEFAULT_LEDGER_JSON = f"{DEFAULT_OUTPUT_DIR}/cross_batch_fix_ledger_v1.json"
DEFAULT_LEDGER_MD = f"{DEFAULT_OUTPUT_DIR}/cross_batch_fix_ledger_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply minimal cross-batch AHV metadata and guard fixes.")
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


def count_safe_objects(conn: sqlite3.Connection) -> int:
    placeholders = ",".join("?" for _ in AHV_SAFE_LAYERS)
    return int(
        conn.execute(
            f"""
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE promotion_source_layer IN ({placeholders})
              AND promotion_state = 'safe_primary'
              AND is_active = 1
            """,
            AHV_SAFE_LAYERS,
        ).fetchone()[0]
    )


def load_safe_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in AHV_SAFE_LAYERS)
    return table_rows(
        conn,
        f"""
        SELECT *
        FROM definition_term_registry
        WHERE promotion_source_layer IN ({placeholders})
          AND promotion_state = 'safe_primary'
          AND is_active = 1
        ORDER BY promotion_source_layer, canonical_term
        """,
        AHV_SAFE_LAYERS,
    )


def fix_primary_evidence_types(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for row in load_safe_rows(conn):
        expected = expected_primary_evidence_type(row)
        current = str(row.get("primary_evidence_type") or "")
        if current == expected:
            continue
        note = expected_primary_type_note(row)
        conn.execute(
            """
            UPDATE definition_term_registry
            SET primary_evidence_type = ?,
                notes = ?
            WHERE concept_id = ?
            """,
            (expected, append_note(row.get("notes") or "", note), row["concept_id"]),
        )
        changes.append(
            {
                "concept_id": row["concept_id"],
                "canonical_term": row["canonical_term"],
                "concept_type": row["concept_type"],
                "before_primary_evidence_type": current,
                "after_primary_evidence_type": expected,
                "note_added": note,
            }
        )
    return changes


def collect_previously_deactivated_by_run(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return table_rows(
        conn,
        """
        SELECT a.*, d.promotion_source_layer
        FROM term_alias_registry AS a
        JOIN definition_term_registry AS d
          ON d.concept_id = a.concept_id
        WHERE a.is_active = 0
          AND a.notes LIKE '%cross_batch_ahv_consistency_audit_v1:%alias deactivated%'
        ORDER BY d.promotion_source_layer, a.canonical_term, a.alias
        """,
    )


def fix_source_confidence(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for row in load_safe_rows(conn):
        if row.get("source_confidence") == "medium":
            continue
        note = "cross_batch_ahv_consistency_audit_v1: AHV v1/AHV2 safe primary confidence unified to medium."
        conn.execute(
            """
            UPDATE definition_term_registry
            SET source_confidence = 'medium',
                notes = ?
            WHERE concept_id = ?
            """,
            (append_note(row.get("notes") or "", note), row["concept_id"]),
        )
        changes.append(
            {
                "concept_id": row["concept_id"],
                "canonical_term": row["canonical_term"],
                "before_source_confidence": row.get("source_confidence"),
                "after_source_confidence": "medium",
            }
        )
    return changes


def fix_active_contains(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in AHV_SAFE_LAYERS)
    rows = table_rows(
        conn,
        f"""
        SELECT l.*
        FROM learner_query_normalization_lexicon AS l
        JOIN definition_term_registry AS d
          ON d.concept_id = l.target_id
        WHERE l.entry_type = 'term_surface'
          AND l.is_active = 1
          AND l.match_mode != 'exact'
          AND d.promotion_source_layer IN ({placeholders})
        ORDER BY l.target_term, l.surface_form
        """,
        AHV_SAFE_LAYERS,
    )
    changes: list[dict[str, Any]] = []
    note = "cross_batch_ahv_consistency_audit_v1: active AHV learner surface forced to exact."
    for row in rows:
        conn.execute(
            """
            UPDATE learner_query_normalization_lexicon
            SET match_mode = 'exact',
                notes = ?
            WHERE lexicon_id = ?
            """,
            (append_note(row.get("notes") or "", note), row["lexicon_id"]),
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
    placeholders = ",".join("?" for _ in AHV_SAFE_LAYERS)
    rows = table_rows(
        conn,
        f"""
        SELECT a.*
        FROM term_alias_registry AS a
        JOIN definition_term_registry AS d
          ON d.concept_id = a.concept_id
        WHERE a.is_active = 1
          AND d.promotion_source_layer IN ({placeholders})
          AND (
              LENGTH(a.normalized_alias) = 1
              OR a.alias_type IN ('learner_risky', 'ambiguous', 'review_only_support')
          )
        ORDER BY a.canonical_term, a.alias
        """,
        AHV_SAFE_LAYERS,
    )
    changes: list[dict[str, Any]] = []
    note = "cross_batch_ahv_consistency_audit_v1: unsafe active alias deactivated."
    for row in rows:
        conn.execute(
            """
            UPDATE term_alias_registry
            SET is_active = 0,
                notes = ?
            WHERE alias_id = ?
            """,
            (append_note(row.get("notes") or "", note), row["alias_id"]),
        )
        changes.append(
            {
                "alias_id": row["alias_id"],
                "alias": row["alias"],
                "canonical_term": row["canonical_term"],
                "before_is_active": row["is_active"],
                "after_is_active": 0,
            }
        )
    return changes


def deactivate_review_only_active_aliases(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = table_rows(
        conn,
        """
        SELECT a.*, d.promotion_state, d.is_safe_primary_candidate, d.promotion_source_layer
        FROM term_alias_registry AS a
        JOIN definition_term_registry AS d
          ON d.concept_id = a.concept_id
        WHERE a.is_active = 1
          AND (
              d.promotion_state != 'safe_primary'
              OR d.is_safe_primary_candidate = 0
          )
        ORDER BY d.promotion_source_layer, a.canonical_term, a.alias
        """,
    )
    changes: list[dict[str, Any]] = []
    note = "cross_batch_ahv_consistency_audit_v1: review/risky alias deactivated."
    for row in rows:
        conn.execute(
            """
            UPDATE term_alias_registry
            SET is_active = 0,
                notes = ?
            WHERE alias_id = ?
            """,
            (append_note(row.get("notes") or "", note), row["alias_id"]),
        )
        changes.append(
            {
                "alias_id": row["alias_id"],
                "alias": row["alias"],
                "canonical_term": row["canonical_term"],
                "promotion_source_layer": row["promotion_source_layer"],
                "before_is_active": row["is_active"],
                "after_is_active": 0,
            }
        )
    return changes


def write_snapshots(conn: sqlite3.Connection, output_dir: Path) -> dict[str, str]:
    snapshots = {
        "definition_term_registry": output_dir / "definition_term_registry_cross_batch_v1_snapshot.json",
        "term_alias_registry": output_dir / "term_alias_registry_cross_batch_v1_snapshot.json",
        "learner_query_normalization_lexicon": output_dir / "learner_query_normalization_cross_batch_v1_snapshot.json",
    }
    write_json(
        snapshots["definition_term_registry"],
        table_rows(conn, "SELECT * FROM definition_term_registry ORDER BY promotion_source_layer, canonical_term, concept_id"),
    )
    write_json(
        snapshots["term_alias_registry"],
        table_rows(conn, "SELECT * FROM term_alias_registry ORDER BY canonical_term, alias, alias_id"),
    )
    write_json(
        snapshots["learner_query_normalization_lexicon"],
        table_rows(
            conn,
            "SELECT * FROM learner_query_normalization_lexicon ORDER BY entry_type, target_term, surface_form, lexicon_id",
        ),
    )
    return {key: str(path) for key, path in snapshots.items()}


def write_ledger(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    write_json(path_json, payload)
    metrics = payload["metrics"]
    lines = [
        "# Cross-Batch AHV Fix Ledger v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- before_safe_object_count: `{metrics['before_safe_object_count']}`",
        f"- after_safe_object_count: `{metrics['after_safe_object_count']}`",
        f"- changed_primary_evidence_type_count: `{metrics['changed_primary_evidence_type_count']}`",
        f"- changed_source_confidence_count: `{metrics['changed_source_confidence_count']}`",
        f"- changed_learner_surface_count: `{metrics['changed_learner_surface_count']}`",
        f"- deactivated_alias_count: `{metrics['deactivated_alias_count']}`",
        f"- downgraded_object_count: `{metrics['downgraded_object_count']}`",
        f"- new_safe_object_count_delta: `{metrics['new_safe_object_count_delta']}`",
        "",
        "## Primary Evidence Type Fixes",
        "",
    ]
    if payload["changes"]["primary_evidence_type"]:
        lines.extend(["| term | concept_type | before | after |", "| --- | --- | --- | --- |"])
        for row in payload["changes"]["primary_evidence_type"]:
            lines.append(
                f"| {row['canonical_term']} | {row['concept_type']} | {row['before_primary_evidence_type']} | {row['after_primary_evidence_type']} |"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Alias / Normalization Fixes", ""])
    if payload["changes"]["learner_surface_match_mode"] or payload["changes"]["deactivated_aliases"]:
        for row in payload["changes"]["learner_surface_match_mode"]:
            lines.append(f"- learner `{row['target_term']}` / `{row['surface_form']}`: {row['before_match_mode']} -> exact")
        for row in payload["changes"]["deactivated_aliases"]:
            lines.append(f"- alias `{row['canonical_term']}` / `{row['alias']}`: active -> inactive")
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
        before_safe_count = count_safe_objects(conn)
        with conn:
            primary_type_changes = fix_primary_evidence_types(conn)
            confidence_changes = fix_source_confidence(conn)
            learner_changes = fix_active_contains(conn)
            unsafe_alias_changes = deactivate_unsafe_aliases(conn)
            review_alias_changes = deactivate_review_only_active_aliases(conn)
        previously_deactivated = collect_previously_deactivated_by_run(conn)
        after_safe_count = count_safe_objects(conn)
        snapshots = write_snapshots(conn, output_dir)
    finally:
        conn.close()

    alias_changes = unsafe_alias_changes + review_alias_changes
    alias_changes_for_ledger = alias_changes + [
        {
            "alias_id": row["alias_id"],
            "alias": row["alias"],
            "canonical_term": row["canonical_term"],
            "promotion_source_layer": row.get("promotion_source_layer"),
            "before_is_active": 1,
            "after_is_active": 0,
            "already_applied": True,
        }
        for row in previously_deactivated
        if row["alias_id"] not in {change["alias_id"] for change in alias_changes}
    ]
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "db_path": str(db_path),
        "policy": {
            "expected_primary_type_by_concept_type": EXPECTED_PRIMARY_TYPE_BY_CONCEPT_TYPE,
            "cross_batch_scope_by_concept_type": CROSS_BATCH_SCOPE_BY_CONCEPT_TYPE,
        },
        "metrics": {
            "before_safe_object_count": before_safe_count,
            "after_safe_object_count": after_safe_count,
            "changed_primary_evidence_type_count": len(primary_type_changes),
            "changed_source_confidence_count": len(confidence_changes),
            "changed_learner_surface_count": len(learner_changes),
            "deactivated_alias_count": len(alias_changes_for_ledger),
            "downgraded_object_count": 0,
            "new_safe_object_count_delta": after_safe_count - before_safe_count,
        },
        "changes": {
            "primary_evidence_type": primary_type_changes,
            "source_confidence": confidence_changes,
            "learner_surface_match_mode": learner_changes,
            "deactivated_aliases": alias_changes_for_ledger,
        },
        "snapshots": snapshots,
    }
    write_ledger(ledger_json, ledger_md, payload)
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
