#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_OUTPUT_JSON = "artifacts/data_implementation/definition_term_registry_v1.json"
DEFAULT_CANDIDATES_MD = "artifacts/data_implementation/definition_safe_evidence_candidates_v1.md"
DEFAULT_BASELINE_JSON = "artifacts/assembler_boundary_fix/definition_primary_regression_v1.json"


SEED_CONCEPTS: list[dict[str, Any]] = [
    {
        "concept_id": "DEF-FAHAN-YAO",
        "canonical_term": "发汗药",
        "concept_type": "therapeutic_category",
        "definition_evidence_passage_ids": ["ZJSHL-CH-006-P-0120"],
        "explanation_evidence_passage_ids": ["ZJSHL-CH-006-P-0127"],
        "membership_evidence_passage_ids": ["ZJSHL-CH-006-P-0120"],
        "primary_support_passage_id": "ZJSHL-CH-006-P-0127",
        "primary_evidence_type": "exact_term_explanation",
        "primary_evidence_text": "发汗药，须温暖服者，易为发散也。",
        "retrieval_sentences": [
            "发汗药，须温暖服者，易为发散也。",
            "桂枝汤者，发汗药也。",
        ],
        "query_aliases": ["发汗药"],
        "source_confidence": "high",
        "is_safe_primary_candidate": True,
        "notes": "从 full:passages 中抽出定义/解释句与归类句；原 full passage 仍不进入 primary。",
    },
    {
        "concept_id": "DEF-XIA-YAO",
        "canonical_term": "下药",
        "concept_type": "therapeutic_category",
        "definition_evidence_passage_ids": [],
        "explanation_evidence_passage_ids": [],
        "membership_evidence_passage_ids": ["ZJSHL-CH-006-P-0120"],
        "primary_support_passage_id": "ZJSHL-CH-006-P-0120",
        "primary_evidence_type": "term_membership_sentence",
        "primary_evidence_text": "承气汤者，下药也。",
        "retrieval_sentences": [
            "承气汤者，下药也。",
            "甘遂者，下药也。",
        ],
        "query_aliases": ["下药"],
        "source_confidence": "medium",
        "is_safe_primary_candidate": True,
        "notes": "仅提升直接归类句；泛化解释仍需下一轮补充。",
    },
    {
        "concept_id": "DEF-HUAI-BING",
        "canonical_term": "坏病",
        "concept_type": "disease_state_term",
        "definition_evidence_passage_ids": ["ZJSHL-CH-008-P-0227", "ZJSHL-CH-008-P-0226"],
        "explanation_evidence_passage_ids": ["ZJSHL-CH-008-P-0227"],
        "membership_evidence_passage_ids": [],
        "primary_support_passage_id": "ZJSHL-CH-008-P-0227",
        "primary_evidence_type": "exact_term_definition",
        "primary_evidence_text": "太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。",
        "retrieval_sentences": [
            "太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。",
            "太阳病三日，已发汗，若吐，若下，若温针，仍不解者，此为坏病。",
        ],
        "query_aliases": ["坏病"],
        "source_confidence": "high",
        "is_safe_primary_candidate": True,
        "notes": "抽出“谓之坏病/此为坏病”的定义句，避免整段 full passage 越权。",
    },
    {
        "concept_id": "DEF-YANG-JIE",
        "canonical_term": "阳结",
        "concept_type": "pulse_pattern_term",
        "definition_evidence_passage_ids": ["ZJSHL-CH-003-P-0004", "ZJSHL-CH-003-P-0017"],
        "explanation_evidence_passage_ids": ["ZJSHL-CH-003-P-0018"],
        "membership_evidence_passage_ids": ["ZJSHL-CH-003-P-0004", "ZJSHL-CH-003-P-0017"],
        "primary_support_passage_id": "ZJSHL-CH-003-P-0004",
        "primary_evidence_type": "exact_term_definition",
        "primary_evidence_text": "其脉浮而数，能食，不大便者，此为实，名曰阳结也。",
        "retrieval_sentences": [
            "其脉浮而数，能食，不大便者，此为实，名曰阳结也。",
            "脉蔼蔼，如车盖者，名曰阳结也。",
        ],
        "query_aliases": ["阳结"],
        "source_confidence": "high",
        "is_safe_primary_candidate": True,
        "notes": "已有 safe main 主证据；纳入 registry 作为概念对象对照。",
    },
    {
        "concept_id": "DEF-YIN-JIE",
        "canonical_term": "阴结",
        "concept_type": "pulse_pattern_term",
        "definition_evidence_passage_ids": ["ZJSHL-CH-003-P-0004", "ZJSHL-CH-003-P-0019"],
        "explanation_evidence_passage_ids": [],
        "membership_evidence_passage_ids": ["ZJSHL-CH-003-P-0004", "ZJSHL-CH-003-P-0019"],
        "primary_support_passage_id": "ZJSHL-CH-003-P-0004",
        "primary_evidence_type": "exact_term_definition",
        "primary_evidence_text": "其脉沉而迟，不能食，身体重，大便反硬，名曰阴结也。",
        "retrieval_sentences": [
            "其脉沉而迟，不能食，身体重，大便反硬，名曰阴结也。",
            "脉如循长竿者，名曰阴结也。",
        ],
        "query_aliases": ["阴结"],
        "source_confidence": "high",
        "is_safe_primary_candidate": True,
        "notes": "已有 safe main 主证据；纳入 registry 作为概念对象对照。",
    },
    {
        "concept_id": "DEF-SHEN-DAN",
        "canonical_term": "神丹",
        "concept_type": "drug_name_term",
        "definition_evidence_passage_ids": [],
        "explanation_evidence_passage_ids": [],
        "membership_evidence_passage_ids": ["ZJSHL-CH-006-P-0118"],
        "primary_support_passage_id": "ZJSHL-CH-006-P-0118",
        "primary_evidence_type": "term_membership_sentence",
        "primary_evidence_text": "神丹者，发汗之药也。",
        "retrieval_sentences": ["神丹者，发汗之药也。"],
        "query_aliases": ["神丹"],
        "source_confidence": "review_only",
        "is_safe_primary_candidate": False,
        "notes": "当前依据主要来自 annotation/full passage 对照层；本轮登记但不提升。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build definition/term safe evidence registry v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--candidates-md", default=DEFAULT_CANDIDATES_MD)
    parser.add_argument("--baseline-json", default=DEFAULT_BASELINE_JSON)
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def fetch_passage(conn: sqlite3.Connection, passage_id: str) -> dict[str, Any]:
    for table in ("records_main_passages", "records_passages", "records_annotations", "risk_registry_ambiguous"):
        row = conn.execute(
            f"""
            SELECT
                record_id,
                source_object,
                evidence_level,
                display_allowed,
                risk_flag,
                chapter_id,
                chapter_name,
                text
            FROM {table}
            WHERE passage_id = ?
            """,
            (passage_id,),
        ).fetchone()
        if row:
            payload = dict(row)
            payload["source_table"] = table
            return payload
    raise ValueError(f"missing passage id in runtime DB: {passage_id}")


def build_records(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed in SEED_CONCEPTS:
        evidence_ids = unique(
            seed["definition_evidence_passage_ids"]
            + seed["explanation_evidence_passage_ids"]
            + seed["membership_evidence_passage_ids"]
        )
        source_rows = [fetch_passage(conn, passage_id) for passage_id in evidence_ids]
        primary_row = fetch_passage(conn, seed["primary_support_passage_id"])
        chapter_ids = unique([row.get("chapter_id") for row in source_rows if row.get("chapter_id")])
        retrieval_text = "\n".join(unique(seed["retrieval_sentences"] + [seed["canonical_term"]] + seed["query_aliases"]))
        records.append(
            {
                "concept_id": seed["concept_id"],
                "canonical_term": seed["canonical_term"],
                "normalized_term": compact_text(seed["canonical_term"]),
                "concept_type": seed["concept_type"],
                "definition_evidence_passage_ids_json": json_text(seed["definition_evidence_passage_ids"]),
                "explanation_evidence_passage_ids_json": json_text(seed["explanation_evidence_passage_ids"]),
                "membership_evidence_passage_ids_json": json_text(seed["membership_evidence_passage_ids"]),
                "primary_support_passage_id": seed["primary_support_passage_id"],
                "source_passage_ids_json": json_text(evidence_ids),
                "chapter_ids_json": json_text(chapter_ids),
                "query_aliases_json": json_text(seed["query_aliases"]),
                "primary_evidence_type": seed["primary_evidence_type"],
                "primary_evidence_text": seed["primary_evidence_text"],
                "retrieval_text": retrieval_text,
                "normalized_retrieval_text": compact_text(retrieval_text),
                "primary_source_object": primary_row["source_object"],
                "primary_source_record_id": primary_row["record_id"],
                "primary_source_evidence_level": primary_row["evidence_level"],
                "source_confidence": seed["source_confidence"],
                "is_safe_primary_candidate": 1 if seed["is_safe_primary_candidate"] else 0,
                "notes": seed["notes"],
                "is_active": 1,
            }
        )
    return records


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS retrieval_ready_definition_view;
        DROP TABLE IF EXISTS definition_term_registry;

        CREATE TABLE definition_term_registry (
            concept_id TEXT PRIMARY KEY,
            canonical_term TEXT NOT NULL,
            normalized_term TEXT NOT NULL UNIQUE,
            concept_type TEXT NOT NULL,
            definition_evidence_passage_ids_json TEXT NOT NULL,
            explanation_evidence_passage_ids_json TEXT NOT NULL,
            membership_evidence_passage_ids_json TEXT NOT NULL,
            primary_support_passage_id TEXT NOT NULL,
            source_passage_ids_json TEXT NOT NULL,
            chapter_ids_json TEXT NOT NULL,
            query_aliases_json TEXT NOT NULL,
            primary_evidence_type TEXT NOT NULL,
            primary_evidence_text TEXT NOT NULL,
            retrieval_text TEXT NOT NULL,
            normalized_retrieval_text TEXT NOT NULL,
            primary_source_object TEXT NOT NULL,
            primary_source_record_id TEXT NOT NULL,
            primary_source_evidence_level TEXT NOT NULL,
            source_confidence TEXT NOT NULL,
            is_safe_primary_candidate INTEGER NOT NULL,
            notes TEXT NOT NULL,
            is_active INTEGER NOT NULL
        );

        CREATE INDEX idx_definition_term_registry_normalized
            ON definition_term_registry(normalized_term);

        CREATE VIEW retrieval_ready_definition_view AS
        SELECT
            concept_id,
            canonical_term,
            normalized_term,
            concept_type,
            definition_evidence_passage_ids_json,
            explanation_evidence_passage_ids_json,
            membership_evidence_passage_ids_json,
            primary_support_passage_id,
            source_passage_ids_json,
            chapter_ids_json,
            query_aliases_json,
            primary_evidence_type,
            primary_evidence_text,
            retrieval_text,
            normalized_retrieval_text,
            primary_source_object,
            primary_source_record_id,
            primary_source_evidence_level,
            source_confidence,
            notes,
            'A' AS allowed_evidence_level
        FROM definition_term_registry
        WHERE is_active = 1
          AND is_safe_primary_candidate = 1;
        """
    )


def insert_records(conn: sqlite3.Connection, records: list[dict[str, Any]]) -> None:
    with conn:
        conn.executemany(
            """
            INSERT INTO definition_term_registry (
                concept_id,
                canonical_term,
                normalized_term,
                concept_type,
                definition_evidence_passage_ids_json,
                explanation_evidence_passage_ids_json,
                membership_evidence_passage_ids_json,
                primary_support_passage_id,
                source_passage_ids_json,
                chapter_ids_json,
                query_aliases_json,
                primary_evidence_type,
                primary_evidence_text,
                retrieval_text,
                normalized_retrieval_text,
                primary_source_object,
                primary_source_record_id,
                primary_source_evidence_level,
                source_confidence,
                is_safe_primary_candidate,
                notes,
                is_active
            ) VALUES (
                :concept_id,
                :canonical_term,
                :normalized_term,
                :concept_type,
                :definition_evidence_passage_ids_json,
                :explanation_evidence_passage_ids_json,
                :membership_evidence_passage_ids_json,
                :primary_support_passage_id,
                :source_passage_ids_json,
                :chapter_ids_json,
                :query_aliases_json,
                :primary_evidence_type,
                :primary_evidence_text,
                :retrieval_text,
                :normalized_retrieval_text,
                :primary_source_object,
                :primary_source_record_id,
                :primary_source_evidence_level,
                :source_confidence,
                :is_safe_primary_candidate,
                :notes,
                :is_active
            )
            """,
            records,
        )


def load_baseline(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row.get("query"): row for row in payload.get("definition_results") or [] if row.get("query")}


def write_json(path: Path, records: list[dict[str, Any]], conn: sqlite3.Connection) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    confidence_counts = Counter(row["source_confidence"] for row in records)
    payload = {
        "generated_at_utc": now_utc(),
        "registry_id": "definition_term_registry_v1",
        "concept_count": len(records),
        "safe_primary_candidate_count": sum(1 for row in records if row["is_safe_primary_candidate"]),
        "source_confidence_counts": dict(sorted(confidence_counts.items())),
        "concepts": records,
        "retrieval_ready_definition_view_sample": [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM retrieval_ready_definition_view ORDER BY concept_id"
            ).fetchall()
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_candidates_md(path: Path, records: list[dict[str, Any]], baseline: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    support_queries = ["什么是发汗药", "发汗药是什么意思", "坏病是什么", "坏病是什么意思"]
    lines = [
        "# Definition Safe Evidence Candidates v1",
        "",
        "## Current Support-Only Failure Surface",
        "",
        "| query | previous mode | why weak | full passage support ids | candidate definition / explanation sentence |",
        "| --- | --- | --- | --- | --- |",
    ]
    sentence_by_term = {row["canonical_term"]: row["primary_evidence_text"] for row in records}
    for query in support_queries:
        row = baseline.get(query) or {}
        support_ids = [
            item.get("record_id")
            for item in row.get("support_full_passages") or []
            if item.get("record_id")
        ]
        term = "发汗药" if "发汗药" in query else "坏病"
        lines.append(
            "| {query} | {mode} | {why} | {ids} | {sentence} |".format(
                query=query,
                mode=row.get("payload_mode") or "unknown",
                why="primary_eligible 为空，关键句只在 support/review 的 full:passages 中",
                ids="<br>".join(support_ids) if support_ids else "-",
                sentence=sentence_by_term.get(term, "-"),
            )
        )

    lines.extend(
        [
            "",
            "## Promotion Registry",
            "",
            "| concept_id | term | type | primary support passage | source layer | safe primary | primary sentence | notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in records:
        lines.append(
            "| {concept_id} | {term} | {concept_type} | {pid} | {source} | {safe} | {sentence} | {notes} |".format(
                concept_id=row["concept_id"],
                term=row["canonical_term"],
                concept_type=row["concept_type"],
                pid=row["primary_support_passage_id"],
                source=f"{row['primary_source_object']} / {row['primary_source_evidence_level']}",
                safe="yes" if row["is_safe_primary_candidate"] else "no",
                sentence=row["primary_evidence_text"],
                notes=row["notes"],
            )
        )

    lines.extend(
        [
            "",
            "## Non-Promotion Rule",
            "",
            "- `full:passages:*` remains risk/support-only in the original runtime tables.",
            "- Only rows with `is_safe_primary_candidate=1` are exposed through `retrieval_ready_definition_view`.",
            "- `DEF-SHEN-DAN` is deliberately registered but not exposed as primary because the current source is still review-only.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    output_json = resolve_project_path(args.output_json)
    candidates_md = resolve_project_path(args.candidates_md)
    baseline_json = resolve_project_path(args.baseline_json)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        records = build_records(conn)
        create_schema(conn)
        insert_records(conn, records)
        write_json(output_json, records, conn)
        write_candidates_md(candidates_md, records, load_baseline(baseline_json))
    finally:
        conn.close()

    print(f"wrote {output_json}")
    print(f"wrote {candidates_md}")
    print(f"updated {db_path} with definition_term_registry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
