#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_ALIASES_PATH = "data/processed/zjshl_dataset_v2/aliases.json"
DEFAULT_REGISTRY_JSON = "artifacts/data_implementation/formula_registry_v1.json"
DEFAULT_ALIAS_JSON = "artifacts/data_implementation/formula_alias_registry_v1.json"
DEFAULT_REPORT_PATH = "artifacts/data_implementation/formula_registry_build_report_v1.md"

FORMULA_SUFFIXES = ("汤", "散", "丸", "饮")
TITLE_SUFFIXES = tuple(suffix + "方" for suffix in FORMULA_SUFFIXES) + FORMULA_SUFFIXES
DECOCTION_HINTS = ("上", "右", "以水", "煑", "煮", "去滓", "温服", "分温", "服方寸匕", "作丸", "为末")
USAGE_HINTS = ("主之", "宜", "与", "可与", "更作", "详见", "方")
ORTHOGRAPHIC_VARIANTS = (
    ("浓朴", "厚朴"),
    ("杏人", "杏仁"),
    ("杏子", "杏仁"),
    ("乾", "干"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build persistent formula registries and retrieval view.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--aliases-path", default=DEFAULT_ALIASES_PATH)
    parser.add_argument("--registry-json", default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--alias-json", default=DEFAULT_ALIAS_JSON)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def normalize_formula_name(text: str | None) -> str:
    normalized = compact_text(clean_formula_name(text))
    normalized = normalized.replace("厚朴", "浓朴").replace("杏仁", "杏子").replace("杏人", "杏子")
    if normalized.endswith("方"):
        normalized = normalized[:-1]
    return normalized


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_formula_id(normalized_name: str) -> str:
    digest = hashlib.sha1(normalized_name.encode("utf-8")).hexdigest()[:12]
    return f"FML-{digest}"


def clean_formula_name(text: str | None) -> str:
    if not text:
        return ""
    name = str(text).strip()
    name = re.sub(r"[：:].*$", "", name)
    name = re.sub(r"([一-龥])赵本[^有]{0,6}有「([^」]+)」二字", r"\2\1", name)
    name = re.sub(r"([一-龥])赵本有「([^」]+)」字?", r"\1\2", name)
    name = re.sub(r"([一-龥])医统本有「([^」]+)」字?", r"\1\2", name)
    name = re.sub(r"赵本无「[^」]+」字?", "", name)
    name = re.sub(r"医统本无「[^」]+」字?", "", name)
    name = re.sub(r"赵本作「[^」]+」", "", name)
    name = re.sub(r"医统本作「[^」]+」", "", name)
    name = re.sub(r"赵本(?:医统本)?(?:并)?作「[^」]+」", "", name)
    name = re.sub(r"赵本(?:医统本)?(?:并)?有「([^」]+)」字?", r"\1", name)
    name = re.sub(r"医统本(?:并)?有「([^」]+)」字?", r"\1", name)
    name = re.sub(r"[，,。；;、\\s]+", "", name)
    if name.endswith("方") and len(name) > 1:
        name = name[:-1]
    return name


def title_formula_name(text: str) -> str | None:
    first = next((line.strip() for line in str(text).splitlines() if line.strip()), "")
    if "：" not in first and ":" not in first:
        return None
    head = re.split(r"[：:]", first, maxsplit=1)[0].strip()
    if not head or len(head) > 48:
        return None
    if any(head.endswith(suffix) for suffix in TITLE_SUFFIXES):
        cleaned = clean_formula_name(head)
        if len(cleaned) >= 3 and any(cleaned.endswith(suffix) for suffix in FORMULA_SUFFIXES):
            return cleaned
    return None


def row_compact(row: dict[str, Any]) -> str:
    return compact_text(row.get("normalized_text") or row.get("text") or "")


def is_decoction_row(text: str) -> bool:
    compact = compact_text(text)
    if not compact:
        return False
    if compact.startswith(("上", "右")) and any(hint in compact for hint in ("味", "水", "服", "煮", "煑", "滓")):
        return True
    return any(compact.startswith(compact_text(hint)) for hint in DECOCTION_HINTS) or any(
        compact_text(hint) in compact for hint in ("去滓", "温服", "分温", "方寸匕")
    )


def source_confidence_for(
    *,
    has_title: bool,
    composition_ids: list[str],
    usage_ids: list[str],
    decoction_ids: list[str],
) -> str:
    if has_title and composition_ids and (usage_ids or decoction_ids):
        return "high"
    if has_title and composition_ids:
        return "medium"
    return "low"


def load_main_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT
                record_id,
                source_record_id,
                passage_id,
                chapter_id,
                chapter_name,
                passage_order_in_chapter,
                text,
                normalized_text
            FROM records_main_passages
            ORDER BY chapter_id, passage_order_in_chapter
            """
        )
    ]


def build_formula_records(main_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_passage_id = {row["passage_id"]: row for row in main_rows}
    by_chapter: dict[str, list[dict[str, Any]]] = {}
    title_by_passage_id: dict[str, str] = {}
    for row in main_rows:
        by_chapter.setdefault(row["chapter_id"], []).append(row)
        formula_name = title_formula_name(row["text"])
        if formula_name:
            title_by_passage_id[row["passage_id"]] = formula_name

    candidates: dict[str, dict[str, Any]] = {}
    for row in main_rows:
        formula_name = title_by_passage_id.get(row["passage_id"])
        if not formula_name:
            continue
        normalized_name = normalize_formula_name(formula_name)
        if not normalized_name:
            continue
        formula_id = stable_formula_id(normalized_name)
        existing = candidates.get(formula_id)
        if existing and existing["primary_formula_passage_id"] <= row["passage_id"]:
            continue
        candidates[formula_id] = {
            "formula_id": formula_id,
            "canonical_name": clean_formula_name(formula_name),
            "normalized_name": normalized_name,
            "primary_formula_passage_id": row["passage_id"],
            "chapter_id": row["chapter_id"],
            "chapter_name": row["chapter_name"],
            "passage_order_in_chapter": row["passage_order_in_chapter"],
        }

    segment_rows: list[dict[str, Any]] = []
    formula_records: list[dict[str, Any]] = []
    for formula in sorted(candidates.values(), key=lambda item: (item["chapter_id"], item["passage_order_in_chapter"])):
        formula_id = formula["formula_id"]
        canonical_name = formula["canonical_name"]
        normalized_name = formula["normalized_name"]
        primary_id = formula["primary_formula_passage_id"]
        primary_row = rows_by_passage_id[primary_id]
        chapter_rows = by_chapter[primary_row["chapter_id"]]
        primary_index = next(index for index, row in enumerate(chapter_rows) if row["passage_id"] == primary_id)

        composition_ids = [primary_id]
        decoction_ids: list[str] = []
        for next_row in chapter_rows[primary_index + 1 : primary_index + 5]:
            if next_row["passage_id"] in title_by_passage_id:
                break
            if is_decoction_row(next_row["text"]):
                decoction_ids.append(next_row["passage_id"])
                continue
            if decoction_ids:
                break

        variants = {
            compact_text(canonical_name),
            compact_text(canonical_name + "方"),
            normalize_formula_name(canonical_name),
            normalize_formula_name(canonical_name + "方"),
        }
        usage_candidates: list[dict[str, Any]] = []
        for row in main_rows:
            if row["passage_id"] == primary_id:
                continue
            compact = row_compact(row)
            if not compact or not any(variant and variant in compact for variant in variants):
                continue
            if not any(compact_text(hint) in compact for hint in USAGE_HINTS):
                continue
            distance = abs(int(row["passage_order_in_chapter"]) - int(primary_row["passage_order_in_chapter"]))
            same_chapter = row["chapter_id"] == primary_row["chapter_id"]
            usage_candidates.append(
                {
                    "row": row,
                    "rank": (0 if same_chapter else 1, distance, row["chapter_id"], row["passage_order_in_chapter"]),
                }
            )
        usage_candidates.sort(key=lambda item: item["rank"])
        usage_ids = [item["row"]["passage_id"] for item in usage_candidates[:8]]

        same_chapter_usage_before = [
            passage_id
            for passage_id in usage_ids
            if rows_by_passage_id[passage_id]["chapter_id"] == primary_row["chapter_id"]
            and rows_by_passage_id[passage_id]["passage_order_in_chapter"] <= primary_row["passage_order_in_chapter"]
        ]
        formula_span_start = same_chapter_usage_before[0] if same_chapter_usage_before else primary_id
        formula_span_end = decoction_ids[-1] if decoction_ids else primary_id
        source_ids = list(dict.fromkeys([primary_id] + composition_ids + decoction_ids + usage_ids))
        chapter_ids = list(dict.fromkeys(rows_by_passage_id[pid]["chapter_id"] for pid in source_ids))
        confidence = source_confidence_for(
            has_title=True,
            composition_ids=composition_ids,
            usage_ids=usage_ids,
            decoction_ids=decoction_ids,
        )
        formula_record = {
            "formula_id": formula_id,
            "canonical_name": canonical_name,
            "normalized_name": normalized_name,
            "primary_formula_passage_id": primary_id,
            "chapter_id": primary_row["chapter_id"],
            "formula_span_start_passage_id": formula_span_start,
            "formula_span_end_passage_id": formula_span_end,
            "composition_passage_ids_json": json_text(composition_ids),
            "decoction_passage_ids_json": json_text(decoction_ids),
            "usage_context_passage_ids_json": json_text(usage_ids),
            "source_passage_ids_json": json_text(source_ids),
            "chapter_ids_json": json_text(chapter_ids),
            "source_confidence": confidence,
            "is_active": 1,
        }
        formula_records.append(formula_record)

        for segment_type, passage_ids in (
            ("composition", composition_ids),
            ("decoction", decoction_ids),
            ("usage_context", usage_ids),
        ):
            for segment_order, passage_id in enumerate(passage_ids, start=1):
                row = rows_by_passage_id[passage_id]
                segment_rows.append(
                    {
                        "formula_id": formula_id,
                        "segment_type": segment_type,
                        "passage_id": passage_id,
                        "segment_order": segment_order,
                        "text": row["text"],
                    }
                )

        neighbor_ids = [
            passage_id
            for passage_id in usage_ids
            if rows_by_passage_id[passage_id]["chapter_id"] == primary_row["chapter_id"]
        ][:2]
        for segment_order, passage_id in enumerate(neighbor_ids, start=1):
            row = rows_by_passage_id[passage_id]
            segment_rows.append(
                {
                    "formula_id": formula_id,
                    "segment_type": "neighbor_context",
                    "passage_id": passage_id,
                    "segment_order": segment_order,
                    "text": row["text"],
                }
            )

    return formula_records, segment_rows


def alias_record(
    *,
    alias: str,
    formula_id: str,
    alias_type: str,
    confidence: float,
    source: str,
    is_auto_generated: bool,
    needs_manual_review: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "alias": alias,
        "normalized_alias": normalize_formula_name(alias) if alias.endswith("方") else normalize_formula_name(alias),
        "formula_id": formula_id,
        "alias_type": alias_type,
        "confidence": round(confidence, 3),
        "source": source,
        "is_auto_generated": 1 if is_auto_generated else 0,
        "needs_manual_review": 1 if needs_manual_review else 0,
        "notes": notes,
        "is_active": 1,
    }


def build_alias_records(formula_records: list[dict[str, Any]], aliases_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    formula_by_normalized = {row["normalized_name"]: row for row in formula_records}
    records: list[dict[str, Any]] = []
    skipped_source_aliases = 0

    for formula in formula_records:
        canonical = formula["canonical_name"]
        formula_id = formula["formula_id"]
        records.append(
            alias_record(
                alias=canonical,
                formula_id=formula_id,
                alias_type="canonical",
                confidence=1.0,
                source="formula_canonical_registry",
                is_auto_generated=False,
                needs_manual_review=False,
                notes="canonical formula name extracted into persistent registry",
            )
        )
        records.append(
            alias_record(
                alias=canonical + "方",
                formula_id=formula_id,
                alias_type="suffix_variant",
                confidence=0.98,
                source="auto:fang_suffix",
                is_auto_generated=True,
                needs_manual_review=False,
                notes="汤/汤方、散/散方、丸/丸方 suffix normalization",
            )
        )
        for source, target in ORTHOGRAPHIC_VARIANTS:
            if source in canonical:
                variant = canonical.replace(source, target)
                records.append(
                    alias_record(
                        alias=variant,
                        formula_id=formula_id,
                        alias_type="orthographic_variant",
                        confidence=0.9,
                        source="auto:orthographic_variant",
                        is_auto_generated=True,
                        needs_manual_review=False,
                        notes=f"known orthographic variant {source}->{target}",
                    )
                )
                records.append(
                    alias_record(
                        alias=variant + "方",
                        formula_id=formula_id,
                        alias_type="orthographic_suffix_variant",
                        confidence=0.88,
                        source="auto:orthographic_variant",
                        is_auto_generated=True,
                        needs_manual_review=False,
                        notes=f"known orthographic variant with 方 suffix {source}->{target}",
                    )
                )

    source_aliases = json.loads(aliases_path.read_text(encoding="utf-8")) if aliases_path.exists() else []
    for item in source_aliases:
        canonical = item.get("canonical_term")
        alias = item.get("alias")
        normalized = normalize_formula_name(canonical)
        formula = formula_by_normalized.get(normalized)
        if not formula:
            skipped_source_aliases += 1
            continue
        records.append(
            alias_record(
                alias=alias,
                formula_id=formula["formula_id"],
                alias_type=f"source:{item.get('alias_type') or 'alias'}",
                confidence=0.99,
                source=f"aliases.json:{item.get('alias_id')}",
                is_auto_generated=False,
                needs_manual_review=False,
                notes=item.get("note") or "existing aliases.json formula alias",
            )
        )

    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        key = (record["alias"], record["normalized_alias"], record["formula_id"])
        existing = deduped.get(key)
        if not existing or (record["confidence"], -record["is_auto_generated"]) > (
            existing["confidence"],
            -existing["is_auto_generated"],
        ):
            deduped[key] = record

    alias_targets: dict[str, set[str]] = {}
    for record in deduped.values():
        alias_targets.setdefault(record["normalized_alias"], set()).add(record["formula_id"])
    final_records: list[dict[str, Any]] = []
    for record in deduped.values():
        if len(alias_targets.get(record["normalized_alias"], set())) > 1:
            record = dict(record)
            record["needs_manual_review"] = 1
            record["confidence"] = min(float(record["confidence"]), 0.69)
            record["notes"] = (record.get("notes") or "") + "; normalized alias maps to multiple formula ids"
        final_records.append(record)

    final_records.sort(key=lambda row: (row["formula_id"], row["alias_type"], row["alias"]))
    return final_records, {"skipped_source_aliases": skipped_source_aliases}


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS retrieval_ready_formula_view;
        DROP TABLE IF EXISTS formula_retrieval_segments;
        DROP TABLE IF EXISTS formula_alias_registry;
        DROP TABLE IF EXISTS formula_canonical_registry;

        CREATE TABLE formula_canonical_registry (
            formula_id TEXT PRIMARY KEY,
            canonical_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            primary_formula_passage_id TEXT NOT NULL,
            chapter_id TEXT NOT NULL,
            formula_span_start_passage_id TEXT NOT NULL,
            formula_span_end_passage_id TEXT NOT NULL,
            composition_passage_ids_json TEXT NOT NULL,
            decoction_passage_ids_json TEXT NOT NULL,
            usage_context_passage_ids_json TEXT NOT NULL,
            source_passage_ids_json TEXT NOT NULL,
            chapter_ids_json TEXT NOT NULL,
            source_confidence TEXT NOT NULL,
            is_active INTEGER NOT NULL
        );

        CREATE TABLE formula_alias_registry (
            alias TEXT NOT NULL,
            normalized_alias TEXT NOT NULL,
            formula_id TEXT NOT NULL,
            alias_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            source TEXT NOT NULL,
            is_auto_generated INTEGER NOT NULL,
            needs_manual_review INTEGER NOT NULL,
            notes TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formula_canonical_registry(formula_id)
        );

        CREATE TABLE formula_retrieval_segments (
            formula_id TEXT NOT NULL,
            segment_type TEXT NOT NULL,
            passage_id TEXT NOT NULL,
            segment_order INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formula_canonical_registry(formula_id)
        );

        CREATE INDEX idx_formula_alias_registry_normalized
            ON formula_alias_registry(normalized_alias);
        CREATE INDEX idx_formula_retrieval_segments_formula
            ON formula_retrieval_segments(formula_id, segment_type, segment_order);

        CREATE VIEW retrieval_ready_formula_view AS
        SELECT
            c.formula_id,
            c.canonical_name,
            c.normalized_name,
            COALESCE((
                SELECT group_concat(alias, '；')
                FROM (
                    SELECT alias
                    FROM formula_alias_registry AS a
                    WHERE a.formula_id = c.formula_id
                      AND a.is_active = 1
                      AND a.needs_manual_review = 0
                    ORDER BY a.confidence DESC, length(a.alias) DESC, a.alias
                )
            ), '') AS alias_text,
            c.canonical_name || '；' || c.canonical_name || '方' AS formula_name_text,
            COALESCE((
                SELECT group_concat(text, char(10))
                FROM (
                    SELECT text
                    FROM formula_retrieval_segments AS s
                    WHERE s.formula_id = c.formula_id
                      AND s.segment_type = 'composition'
                    ORDER BY s.segment_order
                )
            ), '') AS composition_text,
            COALESCE((
                SELECT group_concat(text, char(10))
                FROM (
                    SELECT text
                    FROM formula_retrieval_segments AS s
                    WHERE s.formula_id = c.formula_id
                      AND s.segment_type = 'decoction'
                    ORDER BY s.segment_order
                )
            ), '') AS decoction_text,
            COALESCE((
                SELECT group_concat(text, char(10))
                FROM (
                    SELECT text
                    FROM formula_retrieval_segments AS s
                    WHERE s.formula_id = c.formula_id
                      AND s.segment_type = 'usage_context'
                    ORDER BY s.segment_order
                )
            ), '') AS usage_context_text,
            COALESCE((
                SELECT group_concat(text, char(10))
                FROM (
                    SELECT text
                    FROM formula_retrieval_segments AS s
                    WHERE s.formula_id = c.formula_id
                      AND s.segment_type = 'neighbor_context'
                    ORDER BY s.segment_order
                )
            ), '') AS neighbor_context_text,
            '方剂：' || c.canonical_name
                || char(10) || '别名：' || COALESCE((
                    SELECT group_concat(alias, '；')
                    FROM (
                        SELECT alias
                        FROM formula_alias_registry AS a
                        WHERE a.formula_id = c.formula_id
                          AND a.is_active = 1
                          AND a.needs_manual_review = 0
                        ORDER BY a.confidence DESC, length(a.alias) DESC, a.alias
                    )
                ), '')
                || char(10) || '方名：' || c.canonical_name || '；' || c.canonical_name || '方'
                || char(10) || '组成：' || COALESCE((
                    SELECT group_concat(text, char(10))
                    FROM (
                        SELECT text
                        FROM formula_retrieval_segments AS s
                        WHERE s.formula_id = c.formula_id
                          AND s.segment_type = 'composition'
                        ORDER BY s.segment_order
                    )
                ), '')
                || char(10) || '煎服法：' || COALESCE((
                    SELECT group_concat(text, char(10))
                    FROM (
                        SELECT text
                        FROM formula_retrieval_segments AS s
                        WHERE s.formula_id = c.formula_id
                          AND s.segment_type = 'decoction'
                        ORDER BY s.segment_order
                    )
                ), '')
                || char(10) || '使用语境：' || COALESCE((
                    SELECT group_concat(text, char(10))
                    FROM (
                        SELECT text
                        FROM formula_retrieval_segments AS s
                        WHERE s.formula_id = c.formula_id
                          AND s.segment_type = 'usage_context'
                        ORDER BY s.segment_order
                    )
                ), '')
                || char(10) || '邻接上下文：' || COALESCE((
                    SELECT group_concat(text, char(10))
                    FROM (
                        SELECT text
                        FROM formula_retrieval_segments AS s
                        WHERE s.formula_id = c.formula_id
                          AND s.segment_type = 'neighbor_context'
                        ORDER BY s.segment_order
                    )
                ), '') AS retrieval_text,
            c.primary_formula_passage_id,
            c.formula_span_start_passage_id,
            c.formula_span_end_passage_id,
            c.source_passage_ids_json,
            c.chapter_ids_json,
            'A' AS allowed_evidence_level,
            c.source_confidence
        FROM formula_canonical_registry AS c
        WHERE c.is_active = 1;
        """
    )


def insert_records(
    conn: sqlite3.Connection,
    formula_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    segment_records: list[dict[str, Any]],
) -> None:
    with conn:
        conn.executemany(
            """
            INSERT INTO formula_canonical_registry (
                formula_id,
                canonical_name,
                normalized_name,
                primary_formula_passage_id,
                chapter_id,
                formula_span_start_passage_id,
                formula_span_end_passage_id,
                composition_passage_ids_json,
                decoction_passage_ids_json,
                usage_context_passage_ids_json,
                source_passage_ids_json,
                chapter_ids_json,
                source_confidence,
                is_active
            ) VALUES (
                :formula_id,
                :canonical_name,
                :normalized_name,
                :primary_formula_passage_id,
                :chapter_id,
                :formula_span_start_passage_id,
                :formula_span_end_passage_id,
                :composition_passage_ids_json,
                :decoction_passage_ids_json,
                :usage_context_passage_ids_json,
                :source_passage_ids_json,
                :chapter_ids_json,
                :source_confidence,
                :is_active
            )
            """,
            formula_records,
        )
        conn.executemany(
            """
            INSERT INTO formula_alias_registry (
                alias,
                normalized_alias,
                formula_id,
                alias_type,
                confidence,
                source,
                is_auto_generated,
                needs_manual_review,
                notes,
                is_active
            ) VALUES (
                :alias,
                :normalized_alias,
                :formula_id,
                :alias_type,
                :confidence,
                :source,
                :is_auto_generated,
                :needs_manual_review,
                :notes,
                :is_active
            )
            """,
            alias_records,
        )
        conn.executemany(
            """
            INSERT INTO formula_retrieval_segments (
                formula_id,
                segment_type,
                passage_id,
                segment_order,
                text
            ) VALUES (
                :formula_id,
                :segment_type,
                :passage_id,
                :segment_order,
                :text
            )
            """,
            segment_records,
        )


def write_outputs(
    *,
    conn: sqlite3.Connection,
    formula_records: list[dict[str, Any]],
    alias_records: list[dict[str, Any]],
    alias_stats: dict[str, Any],
    registry_json: Path,
    alias_json: Path,
    report_path: Path,
) -> None:
    registry_json.parent.mkdir(parents=True, exist_ok=True)
    alias_json.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    formula_view_rows = [dict(row) for row in conn.execute("SELECT * FROM retrieval_ready_formula_view ORDER BY formula_id")]
    registry_payload = {
        "generated_at_utc": now_utc(),
        "formula_count": len(formula_records),
        "formulas": formula_records,
        "retrieval_ready_formula_view_sample": formula_view_rows[:12],
    }
    alias_payload = {
        "generated_at_utc": now_utc(),
        "alias_count": len(alias_records),
        "aliases": alias_records,
    }
    registry_json.write_text(json.dumps(registry_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    alias_json.write_text(json.dumps(alias_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    confidence_counts = Counter(record["source_confidence"] for record in formula_records)
    alias_type_counts = Counter(record["alias_type"] for record in alias_records)
    review_alias_count = sum(1 for record in alias_records if record["needs_manual_review"])
    auto_alias_count = sum(1 for record in alias_records if record["is_auto_generated"])
    empty_decoction = sum(1 for record in formula_records if not json.loads(record["decoction_passage_ids_json"]))
    empty_usage = sum(1 for record in formula_records if not json.loads(record["usage_context_passage_ids_json"]))

    lines = [
        "# Formula Registry Build Report v1",
        "",
        f"- generated_at_utc: `{now_utc()}`",
        f"- formula_canonical_registry rows: `{len(formula_records)}`",
        f"- formula_alias_registry rows: `{len(alias_records)}`",
        f"- retrieval_ready_formula_view rows: `{len(formula_view_rows)}`",
        f"- auto_generated_aliases: `{auto_alias_count}`",
        f"- manual_review_aliases: `{review_alias_count}`",
        f"- skipped aliases.json non-formula rows: `{alias_stats.get('skipped_source_aliases')}`",
        f"- formulas_without_decoction_segment: `{empty_decoction}`",
        f"- formulas_without_usage_context_segment: `{empty_usage}`",
        "",
        "## Source Confidence",
        "",
        *[f"- {key}: `{value}`" for key, value in sorted(confidence_counts.items())],
        "",
        "## Alias Types",
        "",
        *[f"- {key}: `{value}`" for key, value in sorted(alias_type_counts.items())],
        "",
        "## Notes",
        "",
        "- Registry rows are persisted in SQLite and mirrored to JSON artifacts.",
        "- `retrieval_ready_formula_view` is a runtime view with one row per formula_id.",
        "- Core formula text is built from safe `records_main_passages`; risk-only full passages are not used as formula view body text.",
        "- Ambiguous normalized aliases are kept in the alias registry with `needs_manual_review=1` and confidence below runtime threshold.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    aliases_path = resolve_project_path(args.aliases_path)
    registry_json = resolve_project_path(args.registry_json)
    alias_json = resolve_project_path(args.alias_json)
    report_path = resolve_project_path(args.report_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        main_rows = load_main_rows(conn)
        formula_records, segment_records = build_formula_records(main_rows)
        alias_records, alias_stats = build_alias_records(formula_records, aliases_path)
        create_schema(conn)
        insert_records(conn, formula_records, alias_records, segment_records)
        write_outputs(
            conn=conn,
            formula_records=formula_records,
            alias_records=alias_records,
            alias_stats=alias_stats,
            registry_json=registry_json,
            alias_json=alias_json,
            report_path=report_path,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
