#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.minimal import DEFAULT_DB_PATH, resolve_project_path  # noqa: E402
from scripts.data_plane_batch_upgrade_v2.run_ambiguous_high_value_evidence_upgrade_v2 import (  # noqa: E402
    AHV2_SAFE_LAYER,
    CANDIDATES,
    compact_text,
    json_text,
)


RUN_ID = "ahv2_quality_audit_v1"
DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_ahv2_quality_audit_v1.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_batch_upgrade_v2"
DEFAULT_DOC_DIR = "docs/data_plane_batch_upgrade_v2"
ALLOWED_VERDICTS = {
    "keep_safe_primary",
    "keep_safe_primary_but_medium",
    "adjust_alias_before_release",
    "support_only_instead",
    "reject_instead",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AHV2 built-in quality audit.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-dir", default=DEFAULT_DOC_DIR)
    parser.add_argument("--refresh-before", action="store_true")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_before_db(db_path: Path, before_db: Path, refresh: bool) -> None:
    before_db.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not before_db.exists():
        shutil.copy2(db_path, before_db)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def fetch_source_text(conn: sqlite3.Connection, row: dict[str, Any]) -> str:
    table = row["primary_source_table"]
    passage_id = row["primary_support_passage_id"]
    try:
        source = conn.execute(f"SELECT text FROM {table} WHERE passage_id = ?", (passage_id,)).fetchone()
    except sqlite3.Error:
        source = None
    if source is None and table == "risk_registry_ambiguous":
        source = conn.execute("SELECT text FROM records_passages WHERE passage_id = ?", (passage_id,)).fetchone()
    return str(source["text"]) if source else ""


def load_rows(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM definition_term_registry
        WHERE promotion_source_layer = ?
        ORDER BY canonical_term, concept_id
        """,
        (AHV2_SAFE_LAYER,),
    ).fetchall()
    return {str(row["canonical_term"]): dict(row) for row in rows}


def load_alias_rows(conn: sqlite3.Connection, concept_id: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT alias, normalized_alias, alias_type, confidence, source, notes, is_active
            FROM term_alias_registry
            WHERE concept_id = ?
            ORDER BY alias, alias_type
            """,
            (concept_id,),
        )
    ]


def load_learner_rows(conn: sqlite3.Connection, concept_id: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT entry_type, match_mode, surface_form, normalized_surface_form,
                   target_term, intent_hint, confidence, source, notes, is_active
            FROM learner_query_normalization_lexicon
            WHERE target_id = ?
            ORDER BY surface_form
            """,
            (concept_id,),
        )
    ]


def audit_object(conn: sqlite3.Connection, row: dict[str, Any]) -> dict[str, Any]:
    alias_rows = load_alias_rows(conn, row["concept_id"])
    learner_rows = load_learner_rows(conn, row["concept_id"])
    active_aliases = [item for item in alias_rows if int(item["is_active"]) == 1]
    active_learner = [item for item in learner_rows if int(item["is_active"]) == 1]

    primary_text = str(row["primary_evidence_text"] or "")
    context_dependency = "bounded" if row["primary_source_object"] in {"passages", "ambiguous_passages"} else "low"
    variant_pollution = any(marker in primary_text for marker in ("赵本", "医统本", "汪本", "熊校记", "旧钞"))
    single_active_alias = any(len(compact_text(item["normalized_alias"] or item["alias"])) < 2 for item in active_aliases)
    risky_active_alias = any(item["alias_type"] in {"learner_risky", "ambiguous", "review_only_support"} for item in active_aliases)
    non_exact_learner = any(item["match_mode"] != "exact" for item in active_learner)
    term_stable = bool(row["canonical_term"]) and len(compact_text(row["canonical_term"])) >= 2
    independent = bool(primary_text) and compact_text(row["canonical_term"]) in compact_text(row["retrieval_text"])
    alias_overbroad = single_active_alias or risky_active_alias
    normalization_safe = bool(active_learner) and not non_exact_learner and not alias_overbroad

    if variant_pollution or not term_stable or not independent:
        verdict = "support_only_instead"
    elif alias_overbroad or non_exact_learner:
        verdict = "adjust_alias_before_release"
    elif row["source_confidence"] == "medium":
        verdict = "keep_safe_primary_but_medium"
    else:
        verdict = "keep_safe_primary"
    if verdict not in ALLOWED_VERDICTS:
        raise RuntimeError(f"bad verdict: {verdict}")

    return {
        "concept_id": row["concept_id"],
        "canonical_term": row["canonical_term"],
        "primary_support_passage_id": row["primary_support_passage_id"],
        "primary_source_table": row["primary_source_table"],
        "primary_source_object": row["primary_source_object"],
        "primary_source_record_id": row["primary_source_record_id"],
        "primary_source_evidence_level": row["primary_source_evidence_level"],
        "source_confidence": row["source_confidence"],
        "promotion_state": row["promotion_state"],
        "primary_evidence_text": primary_text,
        "checks": {
            "primary_sentence_independent": independent,
            "context_dependency": context_dependency,
            "variant_or_collation_pollution": variant_pollution,
            "term_identity_stable": term_stable,
            "alias_overbroad": alias_overbroad,
            "normalization_safe": normalization_safe,
        },
        "alias_registry_rows": alias_rows,
        "learner_normalization_rows": learner_rows,
        "source_text_excerpt": fetch_source_text(conn, row),
        "verdict": verdict,
        "audit_reason": (
            "medium-confidence object kept with exact-match normalization"
            if verdict == "keep_safe_primary_but_medium"
            else "needs demotion or alias adjustment before release"
            if verdict != "keep_safe_primary"
            else "safe primary object kept"
        ),
    }


def validate_rows(rows_by_term: dict[str, dict[str, Any]]) -> None:
    expected_terms = {item.canonical_term for item in CANDIDATES if item.category == "A"}
    actual_terms = set(rows_by_term)
    if expected_terms != actual_terms:
        raise RuntimeError(
            "AHV2 audit term mismatch; missing="
            + ",".join(sorted(expected_terms - actual_terms))
            + " extra="
            + ",".join(sorted(actual_terms - expected_terms))
        )


def append_audit_notes(conn: sqlite3.Connection, audited_objects: list[dict[str, Any]]) -> int:
    changed = 0
    for item in audited_objects:
        note = f"ahv2_quality_audit_v1: verdict={item['verdict']}; normalization_exact=true."
        row = conn.execute(
            "SELECT notes FROM definition_term_registry WHERE concept_id = ?",
            (item["concept_id"],),
        ).fetchone()
        existing = str(row["notes"] or "") if row else ""
        if note in existing:
            continue
        conn.execute(
            "UPDATE definition_term_registry SET notes = ? WHERE concept_id = ?",
            (f"{existing} {note}".strip(), item["concept_id"]),
        )
        changed += 1
    return changed


def write_ledger(output_dir: Path, audited_objects: list[dict[str, Any]], notes_changed_count: int) -> dict[str, Any]:
    verdict_counts = dict(sorted(Counter(item["verdict"] for item in audited_objects).items()))
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "metrics": {
            "quality_audited_A_count": len(audited_objects),
            "notes_changed_count": notes_changed_count,
            "keep_safe_primary_count": sum(item["verdict"] == "keep_safe_primary" for item in audited_objects),
            "keep_safe_primary_but_medium_count": sum(
                item["verdict"] == "keep_safe_primary_but_medium" for item in audited_objects
            ),
            "adjust_alias_before_release_count": sum(
                item["verdict"] == "adjust_alias_before_release" for item in audited_objects
            ),
            "support_only_instead_count": sum(item["verdict"] == "support_only_instead" for item in audited_objects),
            "reject_instead_count": sum(item["verdict"] == "reject_instead" for item in audited_objects),
        },
        "verdict_counts": verdict_counts,
        "audited_objects": audited_objects,
    }
    write_json(output_dir / "ahv2_quality_audit_ledger_v1.json", payload)
    lines = [
        "# AHV2 Quality Audit Ledger v1",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- quality_audited_A_count: `{payload['metrics']['quality_audited_A_count']}`",
        f"- verdict_counts: `{json.dumps(verdict_counts, ensure_ascii=False)}`",
        "",
        "| term | verdict | independent | context_dependency | variant_pollution | alias_overbroad | normalization_safe |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in audited_objects:
        checks = item["checks"]
        lines.append(
            f"| {item['canonical_term']} | {item['verdict']} | "
            f"{checks['primary_sentence_independent']} | {checks['context_dependency']} | "
            f"{checks['variant_or_collation_pollution']} | {checks['alias_overbroad']} | "
            f"{checks['normalization_safe']} |"
        )
    write_md(output_dir / "ahv2_quality_audit_ledger_v1.md", lines)
    return payload


def write_doc(doc_dir: Path, ledger: dict[str, Any]) -> None:
    lines = [
        "# AHV2 Built-in Quality Audit v1",
        "",
        "本审计只覆盖 AHV2 本轮新增 A 类 safe primary objects，不新增对象，不改 prompt、前端、API payload、answer_mode 或 commentarial 主逻辑。",
        "",
        f"- quality_audited_A_count: `{ledger['metrics']['quality_audited_A_count']}`",
        f"- keep_safe_primary_but_medium_count: `{ledger['metrics']['keep_safe_primary_but_medium_count']}`",
        f"- adjust_alias_before_release_count: `{ledger['metrics']['adjust_alias_before_release_count']}`",
        f"- support_only_instead_count: `{ledger['metrics']['support_only_instead_count']}`",
        "",
        "## Audit Fields",
        "",
        "- primary sentence independence",
        "- context dependency",
        "- variant/collation pollution",
        "- term identity stability",
        "- alias breadth",
        "- normalization safety",
        "- final verdict",
    ]
    write_md(doc_dir / "ahv2_quality_audit_v1.md", lines)


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    before_db = resolve_project_path(args.before_db)
    output_dir = resolve_project_path(args.output_dir)
    doc_dir = resolve_project_path(args.doc_dir)
    ensure_before_db(db_path, before_db, args.refresh_before)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows_by_term = load_rows(conn)
        validate_rows(rows_by_term)
        audited_objects = [audit_object(conn, rows_by_term[item.canonical_term]) for item in CANDIDATES if item.category == "A"]
        with conn:
            notes_changed_count = append_audit_notes(conn, audited_objects)
        ledger = write_ledger(output_dir, audited_objects, notes_changed_count)
        write_doc(doc_dir, ledger)
    finally:
        conn.close()

    print(json.dumps({"run_id": RUN_ID, "metrics": ledger["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
