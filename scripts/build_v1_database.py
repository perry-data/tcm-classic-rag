#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SAFE_REQUIRED_FILES = ("main_passages.json", "chunks.json")
FULL_REQUIRED_FILES = ("annotations.json", "passages.json", "ambiguous_passages.json")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPARSE_FTS_TABLE = "retrieval_sparse_fts"
SPARSE_FTS_TOKENIZER = "trigram"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the MVP SQLite database for the zjshl RAG project.")
    parser.add_argument("--safe-source", help="Path to safe dataset zip or directory.")
    parser.add_argument("--full-source", help="Path to full dataset zip or directory.")
    parser.add_argument(
        "--schema-draft",
        default="config/database_schema_draft.json",
        help="Path to database schema draft JSON.",
    )
    parser.add_argument(
        "--policy-json",
        default="config/layered_enablement_policy.json",
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument(
        "--db-path",
        default="artifacts/zjshl_v1.db",
        help="Output SQLite database path.",
    )
    parser.add_argument(
        "--report-path",
        default="artifacts/database_build_report.md",
        help="Output build report path.",
    )
    parser.add_argument(
        "--counts-path",
        default="artifacts/database_counts.json",
        help="Output counts JSON path.",
    )
    parser.add_argument(
        "--smoke-checks-path",
        default="artifacts/database_smoke_checks.md",
        help="Output smoke checks markdown path.",
    )
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def log(message: str) -> None:
    print(message, flush=True)


def bool_to_int(value: bool) -> int:
    return 1 if value else 0


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return text.strip()


def compact_text_for_fts(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def locate_source(explicit: str | None, candidates: list[Path], description: str) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"{description} not found: {path}")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{description} not found in candidates: {candidates}")


@dataclass
class JsonSource:
    path: Path

    def __post_init__(self) -> None:
        self.path = self.path.expanduser().resolve()
        if self.path.is_dir():
            self.kind = "directory"
            self._zipfile: zipfile.ZipFile | None = None
            self._zip_names: dict[str, str] = {}
            return
        if self.path.suffix.lower() == ".zip":
            self.kind = "zip"
            self._zipfile = zipfile.ZipFile(self.path)
            self._zip_names = {
                Path(info.filename).name: info.filename
                for info in self._zipfile.infolist()
                if not info.is_dir()
            }
            return
        raise ValueError(f"unsupported source type: {self.path}")

    def read_json(self, name: str) -> Any:
        if self.kind == "directory":
            target = self.path / name
            if not target.exists():
                raise FileNotFoundError(f"missing required file: {target}")
            return json.loads(target.read_text(encoding="utf-8"))
        if name not in self._zip_names:
            raise FileNotFoundError(f"missing required file in zip {self.path}: {name}")
        assert self._zipfile is not None
        return json.loads(self._zipfile.read(self._zip_names[name]).decode("utf-8"))

    def ensure_files(self, names: Iterable[str]) -> None:
        for name in names:
            self.read_json(name)

    def close(self) -> None:
        if self._zipfile is not None:
            self._zipfile.close()


def make_record_id(dataset_variant: str, source_object: str, source_record_id: str) -> str:
    return f"{dataset_variant}:{source_object}:{source_record_id}"


def make_link_id(chunk_id: str, ordinal: int) -> str:
    return f"safe:chunks:{chunk_id}:{ordinal}"


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE records_main_passages (
            record_id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL,
            passage_id TEXT NOT NULL UNIQUE,
            dataset_variant TEXT NOT NULL,
            source_object TEXT NOT NULL,
            source_type TEXT NOT NULL,
            book_id TEXT,
            chapter_id TEXT,
            chapter_name TEXT,
            chapter_type TEXT,
            passage_order_in_chapter INTEGER,
            source_file TEXT,
            source_item_no INTEGER,
            text TEXT NOT NULL,
            normalized_text TEXT NOT NULL,
            text_role TEXT,
            role_confidence TEXT,
            anchor_passage_id TEXT,
            retrieval_primary_raw INTEGER NOT NULL,
            retrieval_allowed INTEGER NOT NULL,
            evidence_level TEXT NOT NULL,
            display_allowed TEXT NOT NULL,
            risk_flag TEXT NOT NULL,
            requires_disclaimer INTEGER NOT NULL,
            default_weight_tier TEXT NOT NULL,
            policy_source_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            CHECK (dataset_variant = 'safe'),
            CHECK (source_object = 'main_passages'),
            CHECK (source_type = 'main_text'),
            CHECK (retrieval_allowed = 1),
            CHECK (
                (retrieval_primary_raw = 1 AND evidence_level = 'A' AND display_allowed = 'primary' AND default_weight_tier = 'high')
                OR
                (retrieval_primary_raw = 0 AND evidence_level = 'B' AND display_allowed = 'secondary' AND default_weight_tier = 'medium')
            )
        );

        CREATE TABLE records_chunks (
            record_id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL UNIQUE,
            dataset_variant TEXT NOT NULL,
            source_object TEXT NOT NULL,
            source_type TEXT NOT NULL,
            book_id TEXT,
            chapter_id TEXT,
            chapter_name TEXT,
            chunk_type TEXT,
            retrieval_tier_raw TEXT,
            chunk_text TEXT NOT NULL,
            normalized_text TEXT NOT NULL,
            source_passage_ids_json TEXT NOT NULL,
            source_passage_count INTEGER NOT NULL,
            retrieval_allowed INTEGER NOT NULL,
            evidence_level TEXT NOT NULL,
            display_allowed TEXT NOT NULL,
            risk_flag TEXT NOT NULL,
            requires_disclaimer INTEGER NOT NULL,
            default_weight_tier TEXT NOT NULL,
            policy_source_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            CHECK (dataset_variant = 'safe'),
            CHECK (source_object = 'chunks'),
            CHECK (source_type = 'chunk'),
            CHECK (retrieval_allowed = 1),
            CHECK (evidence_level = 'C'),
            CHECK (display_allowed = 'preview_only'),
            CHECK (requires_disclaimer = 0),
            CHECK (default_weight_tier = 'highest')
        );

        CREATE TABLE records_annotations (
            record_id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL,
            annotation_id TEXT NOT NULL UNIQUE,
            passage_id TEXT NOT NULL,
            dataset_variant TEXT NOT NULL,
            source_object TEXT NOT NULL,
            source_type TEXT NOT NULL,
            book_id TEXT,
            chapter_id TEXT,
            chapter_name TEXT,
            chapter_type TEXT,
            passage_order_in_chapter INTEGER,
            source_file TEXT,
            source_item_no INTEGER,
            text TEXT NOT NULL,
            normalized_text TEXT NOT NULL,
            text_role TEXT,
            role_confidence TEXT,
            source_anchor_passage_id TEXT,
            retrieval_primary_raw INTEGER NOT NULL,
            retrieval_allowed INTEGER NOT NULL,
            evidence_level TEXT NOT NULL,
            display_allowed TEXT NOT NULL,
            risk_flag TEXT NOT NULL,
            requires_disclaimer INTEGER NOT NULL,
            default_weight_tier TEXT NOT NULL,
            policy_source_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            linkage_enabled INTEGER NOT NULL,
            CHECK (dataset_variant = 'full'),
            CHECK (source_object = 'annotations'),
            CHECK (source_type = 'annotation'),
            CHECK (retrieval_allowed = 1),
            CHECK (evidence_level = 'B'),
            CHECK (display_allowed = 'secondary'),
            CHECK (requires_disclaimer = 1),
            CHECK (default_weight_tier = 'medium_low'),
            CHECK (linkage_enabled = 0)
        );

        CREATE TABLE records_passages (
            record_id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL,
            passage_id TEXT NOT NULL UNIQUE,
            dataset_variant TEXT NOT NULL,
            source_object TEXT NOT NULL,
            source_type TEXT NOT NULL,
            book_id TEXT,
            chapter_id TEXT,
            chapter_name TEXT,
            chapter_type TEXT,
            passage_order_in_chapter INTEGER,
            source_file TEXT,
            source_item_no INTEGER,
            text TEXT NOT NULL,
            normalized_text TEXT NOT NULL,
            text_role TEXT,
            role_confidence TEXT,
            source_anchor_passage_id TEXT,
            retrieval_primary_raw INTEGER NOT NULL,
            retrieval_allowed INTEGER NOT NULL,
            evidence_level TEXT NOT NULL,
            display_allowed TEXT NOT NULL,
            risk_flag TEXT NOT NULL,
            requires_disclaimer INTEGER NOT NULL,
            default_weight_tier TEXT NOT NULL,
            policy_source_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            ambiguous_registry_hit INTEGER NOT NULL,
            CHECK (dataset_variant = 'full'),
            CHECK (source_object = 'passages'),
            CHECK (source_type = 'ledger_text'),
            CHECK (retrieval_allowed = 1),
            CHECK (evidence_level = 'C'),
            CHECK (display_allowed = 'risk_only'),
            CHECK (requires_disclaimer = 1),
            CHECK (default_weight_tier = 'low')
        );

        CREATE TABLE risk_registry_ambiguous (
            record_id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL,
            passage_id TEXT NOT NULL UNIQUE,
            dataset_variant TEXT NOT NULL,
            source_object TEXT NOT NULL,
            source_type TEXT NOT NULL,
            chapter_id TEXT,
            source_file TEXT,
            source_item_no INTEGER,
            text TEXT NOT NULL,
            normalized_text TEXT NOT NULL,
            text_role TEXT,
            retrieval_allowed INTEGER NOT NULL,
            evidence_level TEXT NOT NULL,
            display_allowed TEXT NOT NULL,
            risk_flag TEXT NOT NULL,
            requires_disclaimer INTEGER NOT NULL,
            default_weight_tier TEXT NOT NULL,
            policy_source_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            linked_passage_record_id TEXT,
            linked_passage_id TEXT,
            CHECK (dataset_variant = 'full'),
            CHECK (source_object = 'ambiguous_passages'),
            CHECK (source_type = 'risk_registry'),
            CHECK (retrieval_allowed = 1),
            CHECK (evidence_level = 'C'),
            CHECK (display_allowed = 'risk_only'),
            CHECK (requires_disclaimer = 1),
            CHECK (default_weight_tier = 'lowest')
        );

        CREATE TABLE record_chunk_passage_links (
            link_id TEXT PRIMARY KEY,
            chunk_record_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            main_passage_record_id TEXT NOT NULL,
            main_passage_id TEXT NOT NULL,
            link_order INTEGER NOT NULL,
            backref_source TEXT NOT NULL,
            FOREIGN KEY (chunk_record_id) REFERENCES records_chunks(record_id),
            FOREIGN KEY (main_passage_record_id) REFERENCES records_main_passages(record_id)
        );

        CREATE INDEX idx_records_main_passages_evidence_level ON records_main_passages(evidence_level);
        CREATE INDEX idx_records_main_passages_chapter_id ON records_main_passages(chapter_id);
        CREATE INDEX idx_records_chunks_chapter_id ON records_chunks(chapter_id);
        CREATE INDEX idx_records_annotations_chapter_id ON records_annotations(chapter_id);
        CREATE INDEX idx_records_passages_chapter_id ON records_passages(chapter_id);
        CREATE INDEX idx_records_passages_ambiguous_hit ON records_passages(ambiguous_registry_hit);
        CREATE INDEX idx_risk_registry_ambiguous_chapter_id ON risk_registry_ambiguous(chapter_id);
        CREATE INDEX idx_record_chunk_passage_links_chunk_record_id ON record_chunk_passage_links(chunk_record_id);
        CREATE INDEX idx_record_chunk_passage_links_main_passage_record_id ON record_chunk_passage_links(main_passage_record_id);
        CREATE INDEX idx_record_chunk_passage_links_chunk_id ON record_chunk_passage_links(chunk_id);

        CREATE VIEW vw_retrieval_records_unified AS
        SELECT
            c.record_id AS retrieval_entry_id,
            'records_chunks' AS record_table,
            c.record_id,
            c.source_record_id,
            c.dataset_variant,
            c.source_object,
            c.source_type,
            c.chunk_text AS retrieval_text,
            c.normalized_text,
            c.book_id,
            c.chapter_id,
            c.chapter_name,
            c.evidence_level,
            c.display_allowed,
            c.risk_flag,
            c.requires_disclaimer,
            c.default_weight_tier,
            c.policy_source_id,
            'main_passages' AS backref_target_type,
            c.source_passage_ids_json AS backref_target_ids_json
        FROM records_chunks AS c
        WHERE c.retrieval_allowed = 1

        UNION ALL

        SELECT
            m.record_id AS retrieval_entry_id,
            'records_main_passages' AS record_table,
            m.record_id,
            m.source_record_id,
            m.dataset_variant,
            m.source_object,
            m.source_type,
            m.text AS retrieval_text,
            m.normalized_text,
            m.book_id,
            m.chapter_id,
            m.chapter_name,
            m.evidence_level,
            m.display_allowed,
            m.risk_flag,
            m.requires_disclaimer,
            m.default_weight_tier,
            m.policy_source_id,
            'none' AS backref_target_type,
            '[]' AS backref_target_ids_json
        FROM records_main_passages AS m
        WHERE m.retrieval_allowed = 1

        UNION ALL

        SELECT
            a.record_id AS retrieval_entry_id,
            'records_annotations' AS record_table,
            a.record_id,
            a.source_record_id,
            a.dataset_variant,
            a.source_object,
            a.source_type,
            a.text AS retrieval_text,
            a.normalized_text,
            a.book_id,
            a.chapter_id,
            a.chapter_name,
            a.evidence_level,
            a.display_allowed,
            a.risk_flag,
            a.requires_disclaimer,
            a.default_weight_tier,
            a.policy_source_id,
            'none' AS backref_target_type,
            '[]' AS backref_target_ids_json
        FROM records_annotations AS a
        WHERE a.retrieval_allowed = 1

        UNION ALL

        SELECT
            p.record_id AS retrieval_entry_id,
            'records_passages' AS record_table,
            p.record_id,
            p.source_record_id,
            p.dataset_variant,
            p.source_object,
            p.source_type,
            p.text AS retrieval_text,
            p.normalized_text,
            p.book_id,
            p.chapter_id,
            p.chapter_name,
            p.evidence_level,
            p.display_allowed,
            p.risk_flag,
            p.requires_disclaimer,
            p.default_weight_tier,
            p.policy_source_id,
            'none' AS backref_target_type,
            '[]' AS backref_target_ids_json
        FROM records_passages AS p
        WHERE p.retrieval_allowed = 1

        UNION ALL

        SELECT
            r.record_id AS retrieval_entry_id,
            'risk_registry_ambiguous' AS record_table,
            r.record_id,
            r.source_record_id,
            r.dataset_variant,
            r.source_object,
            r.source_type,
            r.text AS retrieval_text,
            r.normalized_text,
            p.book_id,
            r.chapter_id,
            p.chapter_name,
            r.evidence_level,
            r.display_allowed,
            r.risk_flag,
            r.requires_disclaimer,
            r.default_weight_tier,
            r.policy_source_id,
            'passages' AS backref_target_type,
            CASE
                WHEN r.linked_passage_id IS NOT NULL THEN '["' || r.linked_passage_id || '"]'
                ELSE '[]'
            END AS backref_target_ids_json
        FROM risk_registry_ambiguous AS r
        LEFT JOIN records_passages AS p
          ON p.passage_id = r.linked_passage_id
        WHERE r.retrieval_allowed = 1;

        CREATE VIRTUAL TABLE retrieval_sparse_fts USING fts5(
            record_id UNINDEXED,
            record_table UNINDEXED,
            source_object UNINDEXED,
            chapter_id UNINDEXED,
            policy_source_id UNINDEXED,
            default_weight_tier UNINDEXED,
            search_text,
            tokenize = 'trigram'
        );
        """
    )


def insert_records_main_passages(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    policy_version: str,
) -> dict[str, str]:
    payload = []
    record_ids: dict[str, str] = {}
    for row in rows:
        passage_id = row["passage_id"]
        record_id = make_record_id("safe", "main_passages", passage_id)
        record_ids[passage_id] = record_id
        retrieval_primary_raw = bool(row["retrieval_primary"])
        payload.append(
            (
                record_id,
                passage_id,
                passage_id,
                "safe",
                "main_passages",
                "main_text",
                row.get("book_id"),
                row.get("chapter_id"),
                row.get("chapter_name"),
                row.get("chapter_type"),
                row.get("passage_order_in_chapter"),
                row.get("source_file"),
                row.get("source_item_no"),
                row.get("text", ""),
                row.get("normalized_text") or normalize_text(row.get("text")),
                row.get("text_role"),
                row.get("role_confidence"),
                row.get("anchor_passage_id"),
                bool_to_int(retrieval_primary_raw),
                1,
                "A" if retrieval_primary_raw else "B",
                "primary" if retrieval_primary_raw else "secondary",
                json_text([] if retrieval_primary_raw else ["short_text_demoted"]),
                0,
                "high" if retrieval_primary_raw else "medium",
                "safe_main_passages_primary" if retrieval_primary_raw else "safe_main_passages_secondary",
                policy_version,
            )
        )
    conn.executemany(
        """
        INSERT INTO records_main_passages (
            record_id, source_record_id, passage_id, dataset_variant, source_object, source_type,
            book_id, chapter_id, chapter_name, chapter_type, passage_order_in_chapter, source_file,
            source_item_no, text, normalized_text, text_role, role_confidence, anchor_passage_id,
            retrieval_primary_raw, retrieval_allowed, evidence_level, display_allowed, risk_flag,
            requires_disclaimer, default_weight_tier, policy_source_id, policy_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    return record_ids


def insert_records_chunks(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    policy_version: str,
) -> dict[str, str]:
    payload = []
    record_ids: dict[str, str] = {}
    for row in rows:
        chunk_id = row["chunk_id"]
        record_id = make_record_id("safe", "chunks", chunk_id)
        record_ids[chunk_id] = record_id
        source_passage_ids = list(row.get("source_passage_ids") or [])
        payload.append(
            (
                record_id,
                chunk_id,
                chunk_id,
                "safe",
                "chunks",
                "chunk",
                row.get("book_id"),
                row.get("chapter_id"),
                row.get("chapter_name"),
                row.get("chunk_type"),
                row.get("retrieval_tier"),
                row.get("chunk_text", ""),
                row.get("normalized_text") or normalize_text(row.get("chunk_text")),
                json_text(source_passage_ids),
                len(source_passage_ids),
                1,
                "C",
                "preview_only",
                json_text([]),
                0,
                "highest",
                "safe_chunks",
                policy_version,
            )
        )
    conn.executemany(
        """
        INSERT INTO records_chunks (
            record_id, source_record_id, chunk_id, dataset_variant, source_object, source_type,
            book_id, chapter_id, chapter_name, chunk_type, retrieval_tier_raw, chunk_text,
            normalized_text, source_passage_ids_json, source_passage_count, retrieval_allowed,
            evidence_level, display_allowed, risk_flag, requires_disclaimer, default_weight_tier,
            policy_source_id, policy_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    return record_ids


def insert_records_annotations(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    policy_version: str,
) -> None:
    payload = []
    for row in rows:
        passage_id = row["passage_id"]
        record_id = make_record_id("full", "annotations", passage_id)
        payload.append(
            (
                record_id,
                passage_id,
                passage_id,
                passage_id,
                "full",
                "annotations",
                "annotation",
                row.get("book_id"),
                row.get("chapter_id"),
                row.get("chapter_name"),
                row.get("chapter_type"),
                row.get("passage_order_in_chapter"),
                row.get("source_file"),
                row.get("source_item_no"),
                row.get("text", ""),
                row.get("normalized_text") or normalize_text(row.get("text")),
                row.get("text_role"),
                row.get("role_confidence"),
                row.get("anchor_passage_id"),
                bool_to_int(bool(row.get("retrieval_primary", False))),
                1,
                "B",
                "secondary",
                json_text(["annotation_unlinked"]),
                1,
                "medium_low",
                "full_annotations_raw",
                policy_version,
                0,
            )
        )
    conn.executemany(
        """
        INSERT INTO records_annotations (
            record_id, source_record_id, annotation_id, passage_id, dataset_variant, source_object,
            source_type, book_id, chapter_id, chapter_name, chapter_type, passage_order_in_chapter,
            source_file, source_item_no, text, normalized_text, text_role, role_confidence,
            source_anchor_passage_id, retrieval_primary_raw, retrieval_allowed, evidence_level,
            display_allowed, risk_flag, requires_disclaimer, default_weight_tier, policy_source_id,
            policy_version, linkage_enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )


def insert_records_passages(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    ambiguous_ids: set[str],
    policy_version: str,
) -> dict[str, str]:
    payload = []
    record_ids: dict[str, str] = {}
    for row in rows:
        passage_id = row["passage_id"]
        record_id = make_record_id("full", "passages", passage_id)
        record_ids[passage_id] = record_id
        risk_flags = ["ledger_mixed_roles"]
        ambiguous_hit = passage_id in ambiguous_ids
        if ambiguous_hit:
            risk_flags.append("ambiguous_source")
        payload.append(
            (
                record_id,
                passage_id,
                passage_id,
                "full",
                "passages",
                "ledger_text",
                row.get("book_id"),
                row.get("chapter_id"),
                row.get("chapter_name"),
                row.get("chapter_type"),
                row.get("passage_order_in_chapter"),
                row.get("source_file"),
                row.get("source_item_no"),
                row.get("text", ""),
                row.get("normalized_text") or normalize_text(row.get("text")),
                row.get("text_role"),
                row.get("role_confidence"),
                row.get("anchor_passage_id"),
                bool_to_int(bool(row.get("retrieval_primary", False))),
                1,
                "C",
                "risk_only",
                json_text(risk_flags),
                1,
                "low",
                "full_passages_ledger",
                policy_version,
                bool_to_int(ambiguous_hit),
            )
        )
    conn.executemany(
        """
        INSERT INTO records_passages (
            record_id, source_record_id, passage_id, dataset_variant, source_object, source_type,
            book_id, chapter_id, chapter_name, chapter_type, passage_order_in_chapter, source_file,
            source_item_no, text, normalized_text, text_role, role_confidence, source_anchor_passage_id,
            retrieval_primary_raw, retrieval_allowed, evidence_level, display_allowed, risk_flag,
            requires_disclaimer, default_weight_tier, policy_source_id, policy_version, ambiguous_registry_hit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    return record_ids


def insert_risk_registry_ambiguous(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    passage_record_ids: dict[str, str],
    policy_version: str,
) -> None:
    payload = []
    for row in rows:
        passage_id = row["passage_id"]
        record_id = make_record_id("full", "ambiguous_passages", passage_id)
        linked_record_id = passage_record_ids.get(passage_id)
        payload.append(
            (
                record_id,
                passage_id,
                passage_id,
                "full",
                "ambiguous_passages",
                "risk_registry",
                row.get("chapter_id"),
                row.get("source_file"),
                row.get("source_item_no"),
                row.get("text", ""),
                normalize_text(row.get("text")),
                row.get("text_role"),
                1,
                "C",
                "risk_only",
                json_text(["ambiguous_source"]),
                1,
                "lowest",
                "ambiguous_related_material",
                policy_version,
                linked_record_id,
                passage_id if linked_record_id else None,
            )
        )
    conn.executemany(
        """
        INSERT INTO risk_registry_ambiguous (
            record_id, source_record_id, passage_id, dataset_variant, source_object, source_type,
            chapter_id, source_file, source_item_no, text, normalized_text, text_role,
            retrieval_allowed, evidence_level, display_allowed, risk_flag, requires_disclaimer,
            default_weight_tier, policy_source_id, policy_version, linked_passage_record_id, linked_passage_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )


def insert_record_chunk_passage_links(
    conn: sqlite3.Connection,
    chunk_rows: list[dict[str, Any]],
    chunk_record_ids: dict[str, str],
    main_passage_record_ids: dict[str, str],
) -> None:
    payload = []
    for row in chunk_rows:
        chunk_id = row["chunk_id"]
        chunk_record_id = chunk_record_ids[chunk_id]
        for ordinal, passage_id in enumerate(row.get("source_passage_ids") or [], start=1):
            if passage_id not in main_passage_record_ids:
                raise ValueError(
                    f"chunk {chunk_id} references passage {passage_id}, which is absent from records_main_passages"
                )
            payload.append(
                (
                    make_link_id(chunk_id, ordinal),
                    chunk_record_id,
                    chunk_id,
                    main_passage_record_ids[passage_id],
                    passage_id,
                    ordinal,
                    "source_passage_ids",
                )
            )
    conn.executemany(
        """
        INSERT INTO record_chunk_passage_links (
            link_id, chunk_record_id, chunk_id, main_passage_record_id, main_passage_id, link_order, backref_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )


def rebuild_sparse_fts(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT
            record_id,
            record_table,
            source_object,
            chapter_id,
            policy_source_id,
            default_weight_tier,
            retrieval_text
        FROM vw_retrieval_records_unified
        """
    ).fetchall()
    payload = [
        (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            compact_text_for_fts(row[6]),
        )
        for row in rows
    ]
    conn.execute(f"DELETE FROM {SPARSE_FTS_TABLE}")
    conn.executemany(
        f"""
        INSERT INTO {SPARSE_FTS_TABLE} (
            record_id,
            record_table,
            source_object,
            chapter_id,
            policy_source_id,
            default_weight_tier,
            search_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )


def fetch_counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = [
        "records_main_passages",
        "records_chunks",
        "records_annotations",
        "records_passages",
        "risk_registry_ambiguous",
        "record_chunk_passage_links",
        SPARSE_FTS_TABLE,
    ]
    counts: dict[str, int] = {}
    for name in tables:
        counts[name] = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    counts["vw_retrieval_records_unified"] = conn.execute(
        "SELECT COUNT(*) FROM vw_retrieval_records_unified"
    ).fetchone()[0]
    return counts


def fetch_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    stats["main_passages_by_level"] = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT evidence_level, COUNT(*) FROM records_main_passages GROUP BY evidence_level ORDER BY evidence_level"
        )
    }
    stats["unified_by_source_object"] = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT source_object, COUNT(*) FROM vw_retrieval_records_unified GROUP BY source_object ORDER BY source_object"
        )
    }
    stats["unified_by_weight_tier"] = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT default_weight_tier, COUNT(*) FROM vw_retrieval_records_unified GROUP BY default_weight_tier ORDER BY default_weight_tier"
        )
    }
    stats["multi_passage_chunks"] = conn.execute(
        "SELECT COUNT(*) FROM records_chunks WHERE source_passage_count > 1"
    ).fetchone()[0]
    stats["link_rows"] = conn.execute("SELECT COUNT(*) FROM record_chunk_passage_links").fetchone()[0]
    stats["fts_index_rows"] = conn.execute(f"SELECT COUNT(*) FROM {SPARSE_FTS_TABLE}").fetchone()[0]
    stats["annotation_links_in_unified_view"] = conn.execute(
        "SELECT COUNT(*) FROM vw_retrieval_records_unified WHERE source_object = 'annotation_links'"
    ).fetchone()[0]
    stats["chunk_primary_violations"] = conn.execute(
        "SELECT COUNT(*) FROM records_chunks WHERE evidence_level = 'A' OR display_allowed = 'primary'"
    ).fetchone()[0]
    stats["annotation_secondary_violations"] = conn.execute(
        "SELECT COUNT(*) FROM records_annotations WHERE evidence_level <> 'B' OR display_allowed <> 'secondary'"
    ).fetchone()[0]
    stats["passage_risk_violations"] = conn.execute(
        "SELECT COUNT(*) FROM records_passages WHERE evidence_level <> 'C' OR display_allowed <> 'risk_only'"
    ).fetchone()[0]
    stats["ambiguous_risk_violations"] = conn.execute(
        "SELECT COUNT(*) FROM risk_registry_ambiguous WHERE evidence_level <> 'C' OR display_allowed <> 'risk_only'"
    ).fetchone()[0]
    return stats


def fetch_smoke_samples(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    conn.row_factory = sqlite3.Row
    samples: dict[str, list[dict[str, Any]]] = {}
    queries = {
        "unified_view_priority_sample": """
            SELECT record_id, source_object, dataset_variant, evidence_level, display_allowed,
                   default_weight_tier, backref_target_type, backref_target_ids_json
            FROM vw_retrieval_records_unified
            ORDER BY CASE default_weight_tier
                WHEN 'highest' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'medium_low' THEN 4
                WHEN 'low' THEN 5
                WHEN 'lowest' THEN 6
                ELSE 7
            END, record_id
            LIMIT 6
        """,
        "chunk_backref_sample": """
            SELECT c.record_id AS chunk_record_id,
                   c.chunk_id,
                   c.source_passage_ids_json,
                   l.link_order,
                   l.main_passage_id,
                   m.evidence_level AS main_passage_evidence_level,
                   substr(m.text, 1, 60) AS main_passage_text_preview
            FROM records_chunks AS c
            JOIN record_chunk_passage_links AS l
              ON l.chunk_record_id = c.record_id
            JOIN records_main_passages AS m
              ON m.record_id = l.main_passage_record_id
            WHERE c.source_passage_count > 1
            ORDER BY c.source_passage_count DESC, c.record_id, l.link_order
            LIMIT 6
        """,
        "layering_sample": """
            SELECT * FROM (
                SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag
                FROM vw_retrieval_records_unified
                WHERE source_object = 'annotations'
                ORDER BY record_id
                LIMIT 3
            )
            UNION ALL
            SELECT * FROM (
                SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag
                FROM vw_retrieval_records_unified
                WHERE source_object = 'passages'
                ORDER BY record_id
                LIMIT 3
            )
            UNION ALL
            SELECT * FROM (
                SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag
                FROM vw_retrieval_records_unified
                WHERE source_object = 'ambiguous_passages'
                ORDER BY record_id
                LIMIT 3
            )
        """,
    }
    for name, query in queries.items():
        rows = conn.execute(query).fetchall()
        samples[name] = [dict(row) for row in rows]
    conn.row_factory = None
    return samples


def markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_no rows_"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header)
            if isinstance(value, str):
                values.append(value.replace("\n", " "))
            else:
                values.append(json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_counts_json(
    path: Path,
    safe_source: JsonSource,
    full_source: JsonSource,
    table_counts: dict[str, int],
    stats: dict[str, Any],
    policy_version: str,
) -> None:
    payload = {
        "build_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "policy_version": policy_version,
        "input_sources": {
            "safe": {"path": str(safe_source.path), "kind": safe_source.kind},
            "full": {"path": str(full_source.path), "kind": full_source.kind},
        },
        "table_counts": table_counts,
        "derived_stats": stats,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_build_report(
    path: Path,
    command: str,
    safe_source: JsonSource,
    full_source: JsonSource,
    db_path: Path,
    table_counts: dict[str, int],
    stats: dict[str, Any],
    policy_version: str,
    schema_version: str,
) -> None:
    source_notes = []
    if full_source.kind == "directory":
        source_notes.append(
            "- 当前工作区未检测到 `dist/zjshl_dataset_v2.zip`；本次构建使用目录输入 "
            f"`{full_source.path}` 作为 full 数据源。"
        )
    else:
        source_notes.append(f"- full 数据源来自 `{full_source.path}`。")
    report = "\n".join(
        [
            "# MVP 数据库构建报告",
            "",
            "## 运行命令",
            "",
            f"`{command}`",
            "",
            "## 输入源",
            "",
            f"- safe 数据源：`{safe_source.path}`（{safe_source.kind}）",
            f"- full 数据源：`{full_source.path}`（{full_source.kind}）",
            *source_notes,
            "",
            "## 输出",
            "",
            f"- 数据库文件：`{db_path}`",
            f"- policy version：`{policy_version}`",
            f"- schema draft version：`{schema_version}`",
            "",
            "## 必需对象检查",
            "",
            "- 已创建六张必需表：`records_main_passages`、`records_chunks`、`records_annotations`、`records_passages`、`risk_registry_ambiguous`、`record_chunk_passage_links`。",
            "- 已创建视图：`vw_retrieval_records_unified`。",
            f"- 已创建 FTS5 虚表：`{SPARSE_FTS_TABLE}`，tokenizer=`{SPARSE_FTS_TOKENIZER}`。",
            "- 未创建 `disabled_annotation_links` 运行时表。这是有意决策，原因是本轮要求默认不启用 `annotation_links`。",
            "",
            "## 表级统计",
            "",
            *(f"- `{name}`: {count}" for name, count in table_counts.items()),
            "",
            "## 关键校验",
            "",
            f"- `record_chunk_passage_links` 行数：{stats['link_rows']}",
            f"- 多 passage chunk 数：{stats['multi_passage_chunks']}",
            f"- FTS 索引行数：{stats['fts_index_rows']}",
            f"- `annotation_links` 出现在 unified view 的行数：{stats['annotation_links_in_unified_view']}",
            f"- chunk 主证据违规数：{stats['chunk_primary_violations']}",
            f"- annotation 辅助证据违规数：{stats['annotation_secondary_violations']}",
            f"- passages 风险层违规数：{stats['passage_risk_violations']}",
            f"- ambiguous 风险层违规数：{stats['ambiguous_risk_violations']}",
            "",
            "## 与文档/JSON 的实现决策说明",
            "",
            "- 字段与分层规则以冻结策略文件和 `config/database_schema_draft.json` 为准实现。",
            "- `policy_version` 使用 `config/layered_enablement_policy.json.version`，而不是 schema draft 文件自身版本号。",
            "- `risk_registry_ambiguous.normalized_text` 由原始 `text` 生成，因为源对象本身不带该字段。",
            "- unified view 中 chunk 的 `backref_target_ids_json` 直接使用 `records_chunks.source_passage_ids_json`；真实回指关系仍由 `record_chunk_passage_links` 承担并在 smoke check 中验证。",
            "- 未发现需要违背冻结策略的实现冲突。",
        ]
    )
    path.write_text(report + "\n", encoding="utf-8")


def write_smoke_checks(
    path: Path,
    samples: dict[str, list[dict[str, Any]]],
    stats: dict[str, Any],
) -> None:
    content = [
        "# 数据库 Smoke Checks",
        "",
        "## 结论",
        "",
        f"- unified view 可查询：`vw_retrieval_records_unified` 行数大于 0，当前为 {sum(len(rows) for rows in samples.values())} 条示例行已提取。",
        f"- FTS5 虚表已建：`{SPARSE_FTS_TABLE}` 当前行数为 {stats['fts_index_rows']}。",
        f"- chunk 回指关系已落地：`record_chunk_passage_links` 行数为 {stats['link_rows']}，大于多 passage chunk 数 {stats['multi_passage_chunks']}。",
        "- `annotations / passages / ambiguous_passages` 均按 B/C 层分开导入，未发生越级。",
        "",
        "## Query 1: unified view 基础查询",
        "",
        "```sql",
        "SELECT record_id, source_object, dataset_variant, evidence_level, display_allowed,",
        "       default_weight_tier, backref_target_type, backref_target_ids_json",
        "FROM vw_retrieval_records_unified",
        "ORDER BY CASE default_weight_tier",
        "    WHEN 'highest' THEN 1",
        "    WHEN 'high' THEN 2",
        "    WHEN 'medium' THEN 3",
        "    WHEN 'medium_low' THEN 4",
        "    WHEN 'low' THEN 5",
        "    WHEN 'lowest' THEN 6",
        "    ELSE 7 END, record_id",
        "LIMIT 6;",
        "```",
        "",
        markdown_table(samples["unified_view_priority_sample"]),
        "",
        "## Query 2: chunk 回指 main_passages",
        "",
        "```sql",
        "SELECT c.record_id AS chunk_record_id, c.chunk_id, c.source_passage_ids_json,",
        "       l.link_order, l.main_passage_id, m.evidence_level AS main_passage_evidence_level,",
        "       substr(m.text, 1, 60) AS main_passage_text_preview",
        "FROM records_chunks AS c",
        "JOIN record_chunk_passage_links AS l ON l.chunk_record_id = c.record_id",
        "JOIN records_main_passages AS m ON m.record_id = l.main_passage_record_id",
        "WHERE c.source_passage_count > 1",
        "ORDER BY c.source_passage_count DESC, c.record_id, l.link_order",
        "LIMIT 6;",
        "```",
        "",
        markdown_table(samples["chunk_backref_sample"]),
        "",
        "## Query 3: annotations / passages / ambiguous 分层检查",
        "",
        "```sql",
        "SELECT * FROM (",
        "    SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag",
        "    FROM vw_retrieval_records_unified",
        "    WHERE source_object = 'annotations'",
        "    ORDER BY record_id",
        "    LIMIT 3",
        ")",
        "UNION ALL",
        "SELECT * FROM (",
        "    SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag",
        "    FROM vw_retrieval_records_unified",
        "    WHERE source_object = 'passages'",
        "    ORDER BY record_id",
        "    LIMIT 3",
        ")",
        "UNION ALL",
        "SELECT * FROM (",
        "    SELECT record_table, source_object, record_id, evidence_level, display_allowed, risk_flag",
        "    FROM vw_retrieval_records_unified",
        "    WHERE source_object = 'ambiguous_passages'",
        "    ORDER BY record_id",
        "    LIMIT 3",
        ");",
        "```",
        "",
        markdown_table(samples["layering_sample"]),
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = PROJECT_ROOT
    schema_path = resolve_project_path(args.schema_draft)
    policy_path = resolve_project_path(args.policy_json)
    db_path = resolve_project_path(args.db_path)
    report_path = resolve_project_path(args.report_path)
    counts_path = resolve_project_path(args.counts_path)
    smoke_checks_path = resolve_project_path(args.smoke_checks_path)
    artifacts_dir = db_path.parent
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    smoke_checks_path.parent.mkdir(parents=True, exist_ok=True)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    schema_version = schema["version"]
    policy_version = policy["version"]

    safe_source = locate_source(
        args.safe_source,
        [root / schema["source_resolution"]["safe"]["artifact"]],
        "safe dataset source",
    )
    full_candidates = [root / schema["source_resolution"]["full"]["artifact_expected"]]
    audit_fallback = schema["source_resolution"]["full"].get("artifact_used_for_field_audit")
    if audit_fallback:
        full_candidates.append(root / audit_fallback)
    full_source = locate_source(args.full_source, full_candidates, "full dataset source")

    safe = JsonSource(safe_source)
    full = JsonSource(full_source)
    try:
        log(f"[1/6] Resolved safe source: {safe.path} ({safe.kind})")
        log(f"[2/6] Resolved full source: {full.path} ({full.kind})")
        safe.ensure_files(SAFE_REQUIRED_FILES)
        full.ensure_files(FULL_REQUIRED_FILES)

        safe_main_passages = safe.read_json("main_passages.json")
        safe_chunks = safe.read_json("chunks.json")
        full_annotations = full.read_json("annotations.json")
        full_passages = full.read_json("passages.json")
        full_ambiguous = full.read_json("ambiguous_passages.json")
        log(
            "[3/6] Loaded source objects: "
            f"safe.main_passages={len(safe_main_passages)}, "
            f"safe.chunks={len(safe_chunks)}, "
            f"full.annotations={len(full_annotations)}, "
            f"full.passages={len(full_passages)}, "
            f"full.ambiguous_passages={len(full_ambiguous)}"
        )

        if db_path.exists():
            db_path.unlink()

        conn = sqlite3.connect(db_path)
        try:
            create_schema(conn)
            ambiguous_ids = {row["passage_id"] for row in full_ambiguous}

            with conn:
                main_passage_record_ids = insert_records_main_passages(conn, safe_main_passages, policy_version)
                chunk_record_ids = insert_records_chunks(conn, safe_chunks, policy_version)
                insert_records_annotations(conn, full_annotations, policy_version)
                passage_record_ids = insert_records_passages(conn, full_passages, ambiguous_ids, policy_version)
                insert_risk_registry_ambiguous(conn, full_ambiguous, passage_record_ids, policy_version)
                insert_record_chunk_passage_links(conn, safe_chunks, chunk_record_ids, main_passage_record_ids)
                rebuild_sparse_fts(conn)
            log(f"[4/6] Built database schema and inserted data into {db_path}")

            table_counts = fetch_counts(conn)
            stats = fetch_stats(conn)
            samples = fetch_smoke_samples(conn)
        finally:
            conn.close()

        write_counts_json(counts_path, safe, full, table_counts, stats, policy_version)
        command = f"{Path(sys.executable).name} " + " ".join(sys.argv)
        write_build_report(
            report_path,
            command=command,
            safe_source=safe,
            full_source=full,
            db_path=db_path,
            table_counts=table_counts,
            stats=stats,
            policy_version=policy_version,
            schema_version=schema_version,
        )
        write_smoke_checks(smoke_checks_path, samples, stats)
        log(f"[5/6] Wrote report files under {artifacts_dir}")
        log(
            "[6/6] Counts summary: "
            + ", ".join(f"{name}={count}" for name, count in table_counts.items())
        )
        return 0
    finally:
        safe.close()
        full.close()


if __name__ == "__main__":
    raise SystemExit(main())
