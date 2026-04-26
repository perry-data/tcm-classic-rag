#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


os.environ.setdefault("PERF_DISABLE_LLM", "1")
os.environ.setdefault("PERF_DISABLE_RERANK", "1")
os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.answers.assembler import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    AnswerAssembler,
    resolve_project_path,
)


DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_formula_medium_span_fix_v1.db"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_formula_fix"
DEFAULT_DOC_PATH = "docs/data_plane_formula_fix/formula_medium_span_fix_v1.md"

TARGET_FORMULAS = (
    "乌梅丸",
    "旋复代赭石汤",
    "栀子浓朴汤",
    "桂枝甘草龙骨牡蛎汤",
    "茵陈蒿汤",
    "麻黄附子甘草汤",
)
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}


FORMULA_FIXES: dict[str, dict[str, Any]] = {
    "乌梅丸": {
        "issue_categories": [
            "composition span incomplete",
            "decoction/preparation span missing",
            "usage_context span missing",
            "composition display variant contaminated",
        ],
        "formula_span_start_passage_id": "ZJSHL-CH-015-P-0219",
        "formula_span_end_passage_id": "ZJSHL-CH-015-P-0225",
        "composition_passage_ids": ["ZJSHL-CH-015-P-0221", "ZJSHL-CH-015-P-0222", "ZJSHL-CH-015-P-0223"],
        "decoction_passage_ids": ["ZJSHL-CH-015-P-0225"],
        "usage_context_passage_ids": ["ZJSHL-CH-015-P-0219", "ZJSHL-CH-015-P-0220"],
        "source_confidence": "high",
        "formula_display_name": "乌梅丸",
        "composition_display_text": (
            "乌梅丸方：乌梅三百个；细辛六两；乾姜十两；黄连一斤；当归四两；"
            "附子六两，炮；蜀椒四两，去子；桂枝六两；人参六两；黄柏六两"
        ),
        "span_fix_reason": (
            "补入 ZJSHL-CH-015-P-0222/ZJSHL-CH-015-P-0223 作为连续组成，"
            "并登记 ZJSHL-CH-015-P-0225 为丸法/服法，ZJSHL-CH-015-P-0219/0220 为使用语境。"
        ),
        "confidence_reason": (
            "完整组成、丸法/服法和蛔厥使用语境均已定位；展示层去除赵本异文噪声，"
            "primary 回指仍只会落到 safe main passages。"
        ),
        "post_fix_classification": "high",
    },
    "旋复代赭石汤": {
        "issue_categories": [
            "title / canonical display variant contaminated",
            "composition display variant contaminated",
            "usage_context span missing",
            "decoction span still absent in available source",
        ],
        "formula_span_start_passage_id": "ZJSHL-CH-010-P-0104",
        "formula_span_end_passage_id": "ZJSHL-CH-010-P-0106",
        "composition_passage_ids": ["ZJSHL-CH-010-P-0106"],
        "decoction_passage_ids": [],
        "usage_context_passage_ids": ["ZJSHL-CH-010-P-0104", "ZJSHL-CH-010-P-0105"],
        "source_confidence": "medium",
        "formula_display_name": "旋复代赭石汤",
        "composition_display_text": (
            "旋复代赭石汤方：旋复花三两；人参二两；生姜五两，切；半夏半升，洗；"
            "代赭石一两；大枣十二枚，擘；甘草三两，炙"
        ),
        "span_fix_reason": (
            "补入 ZJSHL-CH-010-P-0104/0105 为使用语境，并对标题和代赭石药味做 variant-stripped display。"
        ),
        "confidence_reason": "组成和使用语境可审计，但当前可用数据中未找到独立煎服法 span，故不升 high。",
        "post_fix_classification": "medium",
    },
    "栀子浓朴汤": {
        "issue_categories": [
            "usage_context span missing",
            "composition display variant contaminated",
            "decoction span still absent in available source",
        ],
        "formula_span_start_passage_id": "ZJSHL-CH-009-P-0168",
        "formula_span_end_passage_id": "ZJSHL-CH-009-P-0170",
        "composition_passage_ids": ["ZJSHL-CH-009-P-0170"],
        "decoction_passage_ids": [],
        "usage_context_passage_ids": ["ZJSHL-CH-009-P-0168", "ZJSHL-CH-009-P-0169"],
        "source_confidence": "medium",
        "formula_display_name": "栀子浓朴汤",
        "composition_display_text": "栀子浓朴汤方：栀子十四枚，擘；浓朴四两，姜炙，去皮；枳实四枚，水浸，去穣，炒",
        "span_fix_reason": "补入 ZJSHL-CH-009-P-0168/0169 为使用语境，并清理组成展示中的赵本异文噪声。",
        "confidence_reason": "使用语境已补齐，但没有独立煎服法 span，组成行仍来自 variant-heavy 行，故保持 medium。",
        "post_fix_classification": "medium",
    },
    "桂枝甘草龙骨牡蛎汤": {
        "issue_categories": [
            "usage_context span missing",
            "composition display variant contaminated",
            "composition-only object",
        ],
        "formula_span_start_passage_id": "ZJSHL-CH-009-P-0296",
        "formula_span_end_passage_id": "ZJSHL-CH-009-P-0298",
        "composition_passage_ids": ["ZJSHL-CH-009-P-0298"],
        "decoction_passage_ids": [],
        "usage_context_passage_ids": ["ZJSHL-CH-009-P-0296", "ZJSHL-CH-009-P-0297"],
        "source_confidence": "high",
        "formula_display_name": "桂枝甘草龙骨牡蛎汤",
        "composition_display_text": "桂枝甘草龙骨牡蛎汤方：桂枝一两；甘草二两；牡蛎二两，熬；龙骨二两",
        "span_fix_reason": "补入 ZJSHL-CH-009-P-0296/0297 为使用语境，并清理桂枝去皮、甘草炙等异文展示噪声。",
        "confidence_reason": "方名、组成和使用语境连续且边界稳定；无相邻方串入，故可按 composition+usage 对象升 high。",
        "post_fix_classification": "high",
    },
    "茵陈蒿汤": {
        "issue_categories": ["decoction span missing", "usage_context span missing"],
        "formula_span_start_passage_id": "ZJSHL-CH-011-P-0141",
        "formula_span_end_passage_id": "ZJSHL-CH-011-P-0143",
        "composition_passage_ids": ["ZJSHL-CH-011-P-0141"],
        "decoction_passage_ids": ["ZJSHL-CH-011-P-0143"],
        "usage_context_passage_ids": ["ZJSHL-CH-011-P-0200"],
        "source_confidence": "high",
        "formula_display_name": "茵陈蒿汤",
        "composition_display_text": "茵陈蒿汤方：茵陈蒿六两；栀子十四枚，擘；大黄二两，去皮",
        "span_fix_reason": "补入 ZJSHL-CH-011-P-0143 为煎服法，补入 ZJSHL-CH-011-P-0200 为精确方名使用语境。",
        "confidence_reason": "组成、煎服法和精确使用语境均已定位，且 composition display 无显著异文污染，故可升 high。",
        "post_fix_classification": "high",
    },
    "麻黄附子甘草汤": {
        "issue_categories": ["usage_context span missing", "decoction span missing", "composition display variant contaminated"],
        "formula_span_start_passage_id": "ZJSHL-CH-014-P-0067",
        "formula_span_end_passage_id": "ZJSHL-CH-014-P-0071",
        "composition_passage_ids": ["ZJSHL-CH-014-P-0069"],
        "decoction_passage_ids": ["ZJSHL-CH-014-P-0071"],
        "usage_context_passage_ids": ["ZJSHL-CH-014-P-0067", "ZJSHL-CH-014-P-0068"],
        "source_confidence": "high",
        "formula_display_name": "麻黄附子甘草汤",
        "composition_display_text": "麻黄附子甘草汤方：麻黄二两，去节；甘草二两，炙；附子一枚，炮，去皮",
        "span_fix_reason": "补入 ZJSHL-CH-014-P-0067/0068 为使用语境，ZJSHL-CH-014-P-0071 为煎服法，并去除附子破八片异文展示噪声。",
        "confidence_reason": "组成、使用语境和煎服法连续且与相邻麻黄附子细辛汤边界清楚，故可升 high。",
        "post_fix_classification": "high",
    },
}

REGRESSION_QUERIES: tuple[dict[str, str], ...] = (
    {"category": "formula_exact", "query": "乌梅丸方的条文是什么？", "target": "乌梅丸"},
    {"category": "formula_exact", "query": "旋复代赭石汤方的条文是什么？", "target": "旋复代赭石汤"},
    {"category": "formula_exact", "query": "栀子浓朴汤方的条文是什么？", "target": "栀子浓朴汤"},
    {"category": "formula_exact", "query": "桂枝甘草龙骨牡蛎汤方的条文是什么？", "target": "桂枝甘草龙骨牡蛎汤"},
    {"category": "formula_exact", "query": "茵陈蒿汤方的条文是什么？", "target": "茵陈蒿汤"},
    {"category": "formula_exact", "query": "麻黄附子甘草汤方的条文是什么？", "target": "麻黄附子甘草汤"},
    {"category": "formula_comparison", "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？", "target": ""},
    {"category": "formula_comparison", "query": "桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？", "target": ""},
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply formula medium span fixes v1 and run regression.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def safe_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def safe_cell(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return text.replace("|", "／").replace("\n", "<br>")


def unique(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")}


def ensure_formula_fix_columns(conn: sqlite3.Connection) -> None:
    columns = table_columns(conn, "formula_canonical_registry")
    wanted = {
        "formula_display_name": "TEXT NOT NULL DEFAULT ''",
        "composition_display_text": "TEXT NOT NULL DEFAULT ''",
        "span_fix_reason": "TEXT NOT NULL DEFAULT ''",
        "confidence_reason": "TEXT NOT NULL DEFAULT ''",
        "span_fix_status": "TEXT NOT NULL DEFAULT ''",
    }
    with conn:
        for column, ddl in wanted.items():
            if column not in columns:
                conn.execute(f"ALTER TABLE formula_canonical_registry ADD COLUMN {column} {ddl}")
        conn.execute(
            """
            UPDATE formula_canonical_registry
            SET formula_display_name = canonical_name
            WHERE formula_display_name = ''
            """
        )


def recreate_formula_view(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS retrieval_ready_formula_view;
        CREATE VIEW retrieval_ready_formula_view AS
        SELECT
            c.formula_id,
            c.canonical_name,
            c.normalized_name,
            COALESCE(NULLIF(c.formula_display_name, ''), c.canonical_name) AS formula_display_name,
            c.composition_display_text,
            c.span_fix_reason,
            c.confidence_reason,
            c.span_fix_status,
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
            COALESCE(NULLIF(c.formula_display_name, ''), c.canonical_name)
                || '；' || c.canonical_name
                || '；' || c.canonical_name || '方' AS formula_name_text,
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
            '方剂：' || COALESCE(NULLIF(c.formula_display_name, ''), c.canonical_name)
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
                || char(10) || '展示组成：' || COALESCE(NULLIF(c.composition_display_text, ''), '')
                || char(10) || '原文组成：' || COALESCE((
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
                || char(10) || '置信说明：' || COALESCE(NULLIF(c.confidence_reason, ''), '') AS retrieval_text,
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


def fetch_source_row(conn: sqlite3.Connection, passage_id: str) -> dict[str, Any]:
    for table_name in ("records_main_passages", "records_passages", "records_annotations"):
        row = conn.execute(
            f"""
            SELECT
                '{table_name}' AS source_table,
                passage_id,
                chapter_id,
                chapter_name,
                passage_order_in_chapter,
                text
            FROM {table_name}
            WHERE passage_id = ?
            LIMIT 1
            """,
            (passage_id,),
        ).fetchone()
        if row:
            return dict(row)
    raise RuntimeError(f"missing passage_id: {passage_id}")


def fetch_formula_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    optional = [
        "formula_display_name",
        "composition_display_text",
        "span_fix_reason",
        "confidence_reason",
        "span_fix_status",
    ]
    columns = table_columns(conn, "formula_canonical_registry")
    select_optional = ", ".join(column if column in columns else f"'' AS {column}" for column in optional)
    rows = [
        dict(row)
        for row in conn.execute(
            f"""
            SELECT
                *,
                {select_optional}
            FROM formula_canonical_registry
            WHERE canonical_name IN ({",".join("?" for _ in TARGET_FORMULAS)})
            ORDER BY canonical_name
            """,
            TARGET_FORMULAS,
        )
    ]
    for row in rows:
        for field in (
            "composition_passage_ids_json",
            "decoction_passage_ids_json",
            "usage_context_passage_ids_json",
            "source_passage_ids_json",
            "chapter_ids_json",
        ):
            row[field.removesuffix("_json")] = safe_json_list(row.get(field))
    return rows


def fetch_view_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    columns = table_columns(conn, "formula_canonical_registry")
    has_fix_columns = "span_fix_status" in columns
    if has_fix_columns:
        select_sql = """
            SELECT
                formula_id,
                canonical_name,
                formula_display_name,
                formula_name_text,
                composition_display_text,
                composition_text,
                decoction_text,
                usage_context_text,
                source_passage_ids_json,
                source_confidence,
                span_fix_status,
                confidence_reason
            FROM retrieval_ready_formula_view
            WHERE canonical_name IN ({})
            ORDER BY canonical_name
        """.format(",".join("?" for _ in TARGET_FORMULAS))
    else:
        select_sql = """
            SELECT
                formula_id,
                canonical_name,
                '' AS formula_display_name,
                formula_name_text,
                '' AS composition_display_text,
                composition_text,
                decoction_text,
                usage_context_text,
                source_passage_ids_json,
                source_confidence,
                '' AS span_fix_status,
                '' AS confidence_reason
            FROM retrieval_ready_formula_view
            WHERE canonical_name IN ({})
            ORDER BY canonical_name
        """.format(",".join("?" for _ in TARGET_FORMULAS))
    return [dict(row) for row in conn.execute(select_sql, TARGET_FORMULAS)]


def fetch_segment_rows(conn: sqlite3.Connection, formula_ids: list[str]) -> list[dict[str, Any]]:
    if not formula_ids:
        return []
    placeholders = ",".join("?" for _ in formula_ids)
    rows = [
        dict(row)
        for row in conn.execute(
            f"""
            SELECT formula_id, segment_type, passage_id, segment_order, text
            FROM formula_retrieval_segments
            WHERE formula_id IN ({placeholders})
            ORDER BY formula_id, segment_type, segment_order
            """,
            formula_ids,
        )
    ]
    for row in rows:
        source = fetch_source_row(conn, row["passage_id"])
        row["source_table"] = source["source_table"]
    return rows


def registry_snapshot(db_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        formula_rows = fetch_formula_rows(conn)
        formula_ids = [row["formula_id"] for row in formula_rows]
        return {
            "formula_rows": formula_rows,
            "view_rows": fetch_view_rows(conn),
            "segment_rows": fetch_segment_rows(conn, formula_ids),
            "confidence_counts": dict(
                Counter(row["source_confidence"] for row in formula_rows).most_common()
            ),
        }
    finally:
        conn.close()


def apply_formula_fixes(conn: sqlite3.Connection) -> None:
    ensure_formula_fix_columns(conn)
    formula_by_name = {
        row["canonical_name"]: dict(row)
        for row in conn.execute(
            "SELECT formula_id, canonical_name FROM formula_canonical_registry WHERE canonical_name IN ({})".format(
                ",".join("?" for _ in TARGET_FORMULAS)
            ),
            TARGET_FORMULAS,
        )
    }
    missing = sorted(set(TARGET_FORMULAS) - set(formula_by_name))
    if missing:
        raise RuntimeError(f"missing target formulas: {missing}")

    with conn:
        for canonical_name, fix in FORMULA_FIXES.items():
            formula_id = formula_by_name[canonical_name]["formula_id"]
            source_ids = unique(
                fix["usage_context_passage_ids"]
                + fix["composition_passage_ids"]
                + fix["decoction_passage_ids"]
            )
            chapter_ids = unique([fetch_source_row(conn, passage_id)["chapter_id"] for passage_id in source_ids])
            conn.execute(
                """
                UPDATE formula_canonical_registry
                SET
                    formula_span_start_passage_id = ?,
                    formula_span_end_passage_id = ?,
                    composition_passage_ids_json = ?,
                    decoction_passage_ids_json = ?,
                    usage_context_passage_ids_json = ?,
                    source_passage_ids_json = ?,
                    chapter_ids_json = ?,
                    source_confidence = ?,
                    formula_display_name = ?,
                    composition_display_text = ?,
                    span_fix_reason = ?,
                    confidence_reason = ?,
                    span_fix_status = ?
                WHERE formula_id = ?
                """,
                (
                    fix["formula_span_start_passage_id"],
                    fix["formula_span_end_passage_id"],
                    json_text(fix["composition_passage_ids"]),
                    json_text(fix["decoction_passage_ids"]),
                    json_text(fix["usage_context_passage_ids"]),
                    json_text(source_ids),
                    json_text(chapter_ids),
                    fix["source_confidence"],
                    fix["formula_display_name"],
                    fix["composition_display_text"],
                    fix["span_fix_reason"],
                    fix["confidence_reason"],
                    fix["post_fix_classification"],
                    formula_id,
                ),
            )
            conn.execute("DELETE FROM formula_retrieval_segments WHERE formula_id = ?", (formula_id,))
            segment_records: list[dict[str, Any]] = []
            for segment_type, passage_ids in (
                ("composition", fix["composition_passage_ids"]),
                ("decoction", fix["decoction_passage_ids"]),
                ("usage_context", fix["usage_context_passage_ids"]),
            ):
                for order, passage_id in enumerate(passage_ids, start=1):
                    source = fetch_source_row(conn, passage_id)
                    segment_records.append(
                        {
                            "formula_id": formula_id,
                            "segment_type": segment_type,
                            "passage_id": passage_id,
                            "segment_order": order,
                            "text": source["text"],
                        }
                    )
            conn.executemany(
                """
                INSERT INTO formula_retrieval_segments (
                    formula_id, segment_type, passage_id, segment_order, text
                ) VALUES (
                    :formula_id, :segment_type, :passage_id, :segment_order, :text
                )
                """,
                segment_records,
            )
    recreate_formula_view(conn)


def make_assembler(db_path: Path) -> AnswerAssembler:
    return AnswerAssembler(
        db_path=db_path,
        policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
        embed_model=DEFAULT_EMBED_MODEL,
        rerank_model=DEFAULT_RERANK_MODEL,
        cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
        dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
        dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
        dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
        dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
    )


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    forbidden: list[dict[str, Any]] = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            forbidden.append({"record_id": item.get("record_id"), "record_type": item.get("record_type")})
    return forbidden


def summarize_query(assembler: AnswerAssembler, query: str, category: str, target: str) -> dict[str, Any]:
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    raw_top = retrieval.get("raw_candidates") or []
    formula_normalization = retrieval.get("query_request", {}).get("formula_normalization") or {}
    primary = payload.get("primary_evidence") or []
    return {
        "category": category,
        "query": query,
        "target": target,
        "answer_mode": payload.get("answer_mode"),
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "formula_normalization": formula_normalization,
        "primary_ids": [item.get("record_id") for item in primary],
        "primary_record_types": [item.get("record_type") for item in primary],
        "primary_forbidden_items": primary_forbidden_items(payload),
        "primary_all_safe_main": bool(primary) and all(item.get("record_type") == "main_passages" for item in primary),
        "formula_bad_anchor_top5_count": sum(
            1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS
        ),
    }


def run_regression(db_path: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    confidence_by_name = {
        row["canonical_name"]: row["source_confidence"] for row in snapshot["formula_rows"]
    }
    assembler = make_assembler(db_path)
    try:
        rows = [
            {
                **summarize_query(assembler, item["query"], item["category"], item["target"]),
                "target_source_confidence": confidence_by_name.get(item["target"], ""),
            }
            for item in REGRESSION_QUERIES
        ]
    finally:
        assembler.close()
    category_counts: dict[str, dict[str, int]] = {}
    for category in sorted({row["category"] for row in rows}):
        category_counts[category] = dict(
            sorted(Counter(row["answer_mode"] for row in rows if row["category"] == category).items())
        )
    return {
        "rows": rows,
        "summary": {
            "query_count": len(rows),
            "mode_counts": dict(sorted(Counter(row["answer_mode"] for row in rows).items())),
            "category_mode_counts": category_counts,
            "forbidden_primary_total": sum(len(row["primary_forbidden_items"]) for row in rows),
            "exact_formula_query_count": sum(1 for row in rows if row["category"] == "formula_exact"),
            "exact_formula_strong_count": sum(
                1 for row in rows if row["category"] == "formula_exact" and row["answer_mode"] == "strong"
            ),
            "comparison_query_count": sum(1 for row in rows if row["category"] == "formula_comparison"),
            "comparison_strong_count": sum(
                1 for row in rows if row["category"] == "formula_comparison" and row["answer_mode"] == "strong"
            ),
            "formula_bad_anchor_top5_total": sum(row["formula_bad_anchor_top5_count"] for row in rows),
            "primary_non_safe_main_total": sum(
                1 for row in rows if row["primary_ids"] and not row["primary_all_safe_main"]
            ),
            "target_high_count": sum(
                1 for row in snapshot["formula_rows"] if row["source_confidence"] == "high"
            ),
            "target_medium_count": sum(
                1 for row in snapshot["formula_rows"] if row["source_confidence"] == "medium"
            ),
        },
    }


def pair_query_results(before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before_by_query = {row["query"]: row for row in before_rows}
    return [
        {
            "category": after["category"],
            "query": after["query"],
            "target": after["target"],
            "before": before_by_query[after["query"]],
            "after": after,
            "delta": {
                "mode_changed": before_by_query[after["query"]]["answer_mode"] != after["answer_mode"],
                "primary_changed": before_by_query[after["query"]]["primary_ids"] != after["primary_ids"],
            },
        }
        for after in after_rows
    ]


def build_before_after_records(before_snapshot: dict[str, Any], after_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    before_by_name = {row["canonical_name"]: row for row in before_snapshot["formula_rows"]}
    after_by_name = {row["canonical_name"]: row for row in after_snapshot["formula_rows"]}
    records: list[dict[str, Any]] = []
    for name in TARGET_FORMULAS:
        before = before_by_name[name]
        after = after_by_name[name]
        fix = FORMULA_FIXES[name]
        records.append(
            {
                "canonical_name": name,
                "issue_categories": fix["issue_categories"],
                "before": before,
                "after": after,
                "span_fix_reason": fix["span_fix_reason"],
                "confidence_reason": fix["confidence_reason"],
                "upgraded_to_high": before["source_confidence"] != "high" and after["source_confidence"] == "high",
                "post_fix_classification": fix["post_fix_classification"],
            }
        )
    return records


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def before_after_table(records: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| formula | before_span | after_span | before_comp | after_comp | before_decoction | after_decoction | before_usage | after_usage | confidence | conclusion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        before = record["before"]
        after = record["after"]
        lines.append(
            "| "
            + " | ".join(
                [
                    safe_cell(record["canonical_name"]),
                    safe_cell([before["formula_span_start_passage_id"], before["formula_span_end_passage_id"]]),
                    safe_cell([after["formula_span_start_passage_id"], after["formula_span_end_passage_id"]]),
                    safe_cell(before["composition_passage_ids"]),
                    safe_cell(after["composition_passage_ids"]),
                    safe_cell(before["decoction_passage_ids"]),
                    safe_cell(after["decoction_passage_ids"]),
                    safe_cell(before["usage_context_passage_ids"]),
                    safe_cell(after["usage_context_passage_ids"]),
                    safe_cell(f"{before['source_confidence']} -> {after['source_confidence']}"),
                    safe_cell(record["confidence_reason"]),
                ]
            )
            + " |"
        )
    return lines


def regression_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| category | query | before_mode | after_mode | primary_after | safe_main_after | bad_anchor_after |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        before = row["before"]
        after = row["after"]
        lines.append(
            "| "
            + " | ".join(
                [
                    safe_cell(row["category"]),
                    safe_cell(row["query"]),
                    safe_cell(before["answer_mode"]),
                    safe_cell(after["answer_mode"]),
                    safe_cell(after["primary_ids"] or "-"),
                    safe_cell(after["primary_all_safe_main"]),
                    safe_cell(after["formula_bad_anchor_top5_count"]),
                ]
            )
            + " |"
        )
    return lines


def write_before_after_md(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [
        "# Formula Medium Span Fix Before/After v1",
        "",
        "## Summary",
        "",
        *before_after_table(records),
        "",
        "## Per Formula Notes",
        "",
    ]
    for record in records:
        after = record["after"]
        lines.extend(
            [
                f"### {record['canonical_name']}",
                "",
                f"- issue_categories: `{json.dumps(record['issue_categories'], ensure_ascii=False)}`",
                f"- composition_display_text: `{after['composition_display_text']}`",
                f"- span_fix_reason: {record['span_fix_reason']}",
                f"- confidence_reason: {record['confidence_reason']}",
                f"- post_fix_classification: `{record['post_fix_classification']}`",
                "",
            ]
        )
    if lines and lines[-1] == "":
        lines.pop()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_regression_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Formula Medium Span Fix Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- before_db: `{payload['before_db']}`",
        f"- after_db: `{payload['after_db']}`",
        "",
        "## Summary",
        "",
        f"- exact formula strong before -> after: `{payload['before_summary']['exact_formula_strong_count']}/{payload['before_summary']['exact_formula_query_count']} -> {payload['after_summary']['exact_formula_strong_count']}/{payload['after_summary']['exact_formula_query_count']}`",
        f"- comparison strong before -> after: `{payload['before_summary']['comparison_strong_count']}/{payload['before_summary']['comparison_query_count']} -> {payload['after_summary']['comparison_strong_count']}/{payload['after_summary']['comparison_query_count']}`",
        f"- forbidden primary before -> after: `{payload['before_summary']['forbidden_primary_total']} -> {payload['after_summary']['forbidden_primary_total']}`",
        f"- primary non-safe-main before -> after: `{payload['before_summary']['primary_non_safe_main_total']} -> {payload['after_summary']['primary_non_safe_main_total']}`",
        f"- bad anchors top5 before -> after: `{payload['before_summary']['formula_bad_anchor_top5_total']} -> {payload['after_summary']['formula_bad_anchor_top5_total']}`",
        f"- target high count before -> after: `{payload['before_summary']['target_high_count']} -> {payload['after_summary']['target_high_count']}`",
        "",
        "## Query Table",
        "",
        *regression_table(payload["paired_results"]),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_doc(path: Path, before_after_records: list[dict[str, Any]], regression_payload: dict[str, Any]) -> None:
    high = [row["canonical_name"] for row in before_after_records if row["after"]["source_confidence"] == "high"]
    medium = [row["canonical_name"] for row in before_after_records if row["after"]["source_confidence"] == "medium"]
    lines = [
        "# Formula Medium Span Fix v1",
        "",
        "## Scope",
        "",
        "- 本轮只处理 small gold audit v1 中 6 个 `gold_needs_span_fix` formula medium。",
        "- 不改 prompt、前端、API payload、answer_mode、commentarial 或 definition/concept 主线。",
        "- raw full/passages 可作为 formula span 的可审计 support，但回归确认 primary evidence 仍只来自 `safe:main_passages:*`。",
        "",
        "## Classification",
        "",
        f"- 类别1 已可升 high: `{json.dumps(high, ensure_ascii=False)}`",
        f"- 类别2 已修但仍保持 medium: `{json.dumps(medium, ensure_ascii=False)}`",
        "- 类别3 当前不建议继续投入: `[]`",
        "",
        "## Before/After",
        "",
        *before_after_table(before_after_records),
        "",
        "## Regression",
        "",
        f"- exact formula strong after: `{regression_payload['after_summary']['exact_formula_strong_count']}/{regression_payload['after_summary']['exact_formula_query_count']}`",
        f"- comparison strong after: `{regression_payload['after_summary']['comparison_strong_count']}/{regression_payload['after_summary']['comparison_query_count']}`",
        f"- forbidden primary after: `{regression_payload['after_summary']['forbidden_primary_total']}`",
        f"- primary non-safe-main after: `{regression_payload['after_summary']['primary_non_safe_main_total']}`",
        f"- bad anchors top5 after: `{regression_payload['after_summary']['formula_bad_anchor_top5_total']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db)
    before_db = Path(args.before_db)
    output_dir = resolve_project_path(args.output_dir)
    doc_path = resolve_project_path(args.doc_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not before_db.exists():
        shutil.copy2(db_path, before_db)

    before_snapshot = registry_snapshot(before_db)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        apply_formula_fixes(conn)
    finally:
        conn.close()

    after_snapshot = registry_snapshot(db_path)
    before_after_records = build_before_after_records(before_snapshot, after_snapshot)
    before_regression = run_regression(before_db, before_snapshot)
    after_regression = run_regression(db_path, after_snapshot)
    regression_payload = {
        "generated_at_utc": now_utc(),
        "before_db": str(before_db),
        "after_db": str(db_path),
        "before_summary": before_regression["summary"],
        "after_summary": after_regression["summary"],
        "before_rows": before_regression["rows"],
        "after_rows": after_regression["rows"],
        "paired_results": pair_query_results(before_regression["rows"], after_regression["rows"]),
    }

    before_after_payload = {
        "generated_at_utc": now_utc(),
        "records": before_after_records,
        "before_snapshot": before_snapshot,
        "after_snapshot": after_snapshot,
    }
    write_json(output_dir / "formula_medium_span_fix_before_after_v1.json", before_after_payload)
    write_before_after_md(output_dir / "formula_medium_span_fix_before_after_v1.md", before_after_records)
    write_json(output_dir / "formula_medium_span_fix_regression_v1.json", regression_payload)
    write_regression_md(output_dir / "formula_medium_span_fix_regression_v1.md", regression_payload)
    write_json(
        output_dir / "formula_canonical_registry_span_fix_v1_snapshot.json",
        {"generated_at_utc": now_utc(), "records": after_snapshot["formula_rows"]},
    )
    write_json(
        output_dir / "retrieval_ready_formula_view_span_fix_v1_snapshot.json",
        {"generated_at_utc": now_utc(), "records": after_snapshot["view_rows"]},
    )
    write_doc(doc_path, before_after_records, regression_payload)

    print(f"wrote {output_dir / 'formula_medium_span_fix_before_after_v1.json'}")
    print(f"wrote {output_dir / 'formula_medium_span_fix_before_after_v1.md'}")
    print(f"wrote {output_dir / 'formula_medium_span_fix_regression_v1.json'}")
    print(f"wrote {output_dir / 'formula_medium_span_fix_regression_v1.md'}")
    print(f"wrote {output_dir / 'formula_canonical_registry_span_fix_v1_snapshot.json'}")
    print(f"wrote {output_dir / 'retrieval_ready_formula_view_span_fix_v1_snapshot.json'}")
    print(f"wrote {doc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
