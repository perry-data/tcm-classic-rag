#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_POLICY_PATH = "config/layered_enablement_policy.json"
DEFAULT_EXAMPLES_OUT = "artifacts/retrieval_examples.json"
DEFAULT_SMOKE_OUT = "artifacts/retrieval_smoke_checks.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_EXAMPLES = [
    {
        "example_id": "strong_chunk_backref",
        "query_text": "黄连汤方的条文是什么？",
        "expected_mode": "strong",
    },
    {
        "example_id": "weak_with_review_notice",
        "query_text": "烧针益阳而损阴是什么意思？",
        "expected_mode": "weak_with_review_notice",
    },
    {
        "example_id": "refuse_no_match",
        "query_text": "书中有没有提到量子纠缠？",
        "expected_mode": "refuse",
    },
]

SOURCE_BUDGETS = {
    "definition_term_object_view": 4,
    "formula_object_view": 4,
    "safe_chunks": 8,
    "safe_main_passages_primary": 6,
    "safe_main_passages_secondary": 4,
    "controlled_replay_main_passages": 2,
    "full_annotations_raw": 3,
    "full_passages_ledger": 2,
    "ambiguous_related_material": 1,
}

DEFAULT_TOTAL_LIMIT = 24
PRIMARY_LIMIT = 3
SECONDARY_LIMIT = 5
RISK_LIMIT = 5

WEIGHT_BONUS = {
    "highest": 6.0,
    "high": 5.0,
    "medium": 4.0,
    "medium_low": 3.0,
    "low": 2.0,
    "lowest": 1.0,
    "off": 0.0,
}

QUESTION_NOISE_PHRASES = [
    "请问",
    "书中",
    "文中",
    "伤寒论里",
    "伤寒论中",
    "有没有",
    "有无",
    "是否",
    "怎么",
    "如何",
    "是什么意思",
    "是什么",
    "什么意思",
    "条文",
    "原文",
    "提到",
    "讲到",
    "说到",
    "关于",
    "的吗",
    "吗",
    "呢",
    "么",
]

FORMULA_QUERY_SUFFIXES = (
    "汤方",
    "散方",
    "丸方",
    "饮方",
    "方",
    "汤",
    "散",
    "丸",
    "饮",
)

FORMULA_ANCHOR_VARIANT_REPLACEMENTS = (
    ("厚朴", "浓朴"),
    ("杏仁", "杏子"),
    ("杏人", "杏子"),
)
FORMULA_OBJECT_DISABLE_ENV = "TCM_DISABLE_FORMULA_OBJECT_RETRIEVAL"
FORMULA_OBJECT_SOURCE_ID = "formula_object_view"
DEFINITION_OBJECT_DISABLE_ENV = "TCM_DISABLE_DEFINITION_OBJECT_RETRIEVAL"
DEFINITION_OBJECT_SOURCE_ID = "definition_term_object_view"
FORMULA_RUNTIME_TABLES = (
    "formula_canonical_registry",
    "formula_alias_registry",
    "retrieval_ready_formula_view",
)
DEFINITION_RUNTIME_TABLES = (
    "definition_term_registry",
    "retrieval_ready_definition_view",
)
DEFINITION_RUNTIME_OPTIONAL_TABLES = (
    "term_alias_registry",
    "learner_query_normalization_lexicon",
)
FORMULA_COMPARISON_HINTS = ("区别", "不同", "比较", "对比", "异同", "有什么不一样", "和", "与")


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal retrieval on zjshl_v1.db.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--query", help="Run a single query and print JSON to stdout.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_EXAMPLES_OUT,
        help="Where to write the default example results JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_SMOKE_OUT,
        help="Where to write the smoke check markdown report.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=DEFAULT_TOTAL_LIMIT,
        help="Maximum number of raw candidates kept after ranking.",
    )
    return parser.parse_args()


def log(message: str) -> None:
    print(message, flush=True)


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = text.lower()
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized)
    return normalized


def extract_focus_text(query_text: str) -> str:
    focus = compact_text(query_text)
    for phrase in sorted(QUESTION_NOISE_PHRASES, key=len, reverse=True):
        focus = focus.replace(compact_text(phrase), "")
    focus = re.sub(r"[的是呢吗么]+$", "", focus)
    return focus or compact_text(query_text)


def build_query_terms(focus_text: str) -> list[str]:
    if not focus_text:
        return []
    terms: set[str] = {focus_text}
    if 2 <= len(focus_text) <= 24:
        for n in range(min(4, len(focus_text)), 1, -1):
            for idx in range(0, len(focus_text) - n + 1):
                terms.add(focus_text[idx : idx + n])
    return sorted(terms, key=lambda item: (-len(item), item))


def extract_title_anchor(text: str | None) -> str:
    if not text:
        return ""
    first_line = next((line.strip() for line in str(text).splitlines() if line.strip()), "")
    if not first_line:
        return ""
    first_segment = re.split(r"[：:]", first_line, maxsplit=1)[0].strip()
    return compact_text(first_segment)


def extract_raw_title_anchor(text: str | None) -> str:
    if not text:
        return ""
    first_line = next((line.strip() for line in str(text).splitlines() if line.strip()), "")
    if not first_line:
        return ""
    return re.split(r"[：:]", first_line, maxsplit=1)[0].strip()


def clean_formula_title_anchor(text: str | None) -> str:
    raw_title = " ".join(str(text).split()) if text else ""
    if not raw_title:
        return ""
    cleaned = re.sub(r"(?:赵本|医统本)+有「([^」]+)」字", r"\1", raw_title)
    cleaned = re.sub(r"(?:赵本|医统本)+并有「([^」]+)」字", r"\1", cleaned)
    cleaned = re.sub(r"(?:赵本|医统本)+(?:作|无)「[^」]+」字?", "", cleaned)
    return compact_text(cleaned)


def normalize_formula_anchor(text: str | None) -> str:
    anchor = clean_formula_title_anchor(text)
    if not anchor:
        anchor = compact_text(text)
    for source, target in FORMULA_ANCHOR_VARIANT_REPLACEMENTS:
        anchor = anchor.replace(compact_text(source), compact_text(target))
    if anchor.endswith("方") and len(anchor) > 1:
        return anchor[:-1]
    return anchor


def normalize_formula_runtime_text(text: str | None) -> str:
    normalized = compact_text(text)
    for source, target in FORMULA_ANCHOR_VARIANT_REPLACEMENTS:
        normalized = normalized.replace(compact_text(source), compact_text(target))
    return normalized


def runtime_env_flag_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


class FormulaRuntimeIndex:
    def __init__(
        self,
        *,
        enabled: bool,
        formulas_by_id: dict[str, dict[str, Any]] | None = None,
        aliases: list[dict[str, Any]] | None = None,
        formula_rows: list[dict[str, Any]] | None = None,
        passage_to_formula_ids: dict[str, list[str]] | None = None,
        disabled_reason: str | None = None,
    ) -> None:
        self.enabled = enabled
        self.formulas_by_id = formulas_by_id or {}
        self.aliases = aliases or []
        self.formula_rows = formula_rows or []
        self.formula_row_by_formula_id = {row["formula_id"]: row for row in self.formula_rows}
        self.passage_to_formula_ids = passage_to_formula_ids or {}
        self.disabled_reason = disabled_reason

    @classmethod
    def disabled(cls, reason: str) -> "FormulaRuntimeIndex":
        return cls(enabled=False, disabled_reason=reason)

    @classmethod
    def from_db(cls, conn: sqlite3.Connection) -> "FormulaRuntimeIndex":
        if runtime_env_flag_enabled(os.getenv(FORMULA_OBJECT_DISABLE_ENV)):
            return cls.disabled(f"{FORMULA_OBJECT_DISABLE_ENV}=1")

        existing = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE name IN ({})".format(
                    ",".join("?" for _ in FORMULA_RUNTIME_TABLES)
                ),
                FORMULA_RUNTIME_TABLES,
            )
        }
        missing = [name for name in FORMULA_RUNTIME_TABLES if name not in existing]
        if missing:
            return cls.disabled("missing:" + ",".join(missing))

        formulas_by_id = {
            row["formula_id"]: dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM formula_canonical_registry
                WHERE is_active = 1
                """
            )
        }
        if not formulas_by_id:
            return cls.disabled("empty formula_canonical_registry")

        alias_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    alias,
                    normalized_alias,
                    formula_id,
                    alias_type,
                    confidence,
                    is_auto_generated,
                    needs_manual_review
                FROM formula_alias_registry
                WHERE is_active = 1
                  AND formula_id IN (
                      SELECT formula_id FROM formula_canonical_registry WHERE is_active = 1
                  )
                """
            )
        ]
        alias_formula_ids: dict[str, set[str]] = {}
        for row in alias_rows:
            alias_formula_ids.setdefault(row["normalized_alias"], set()).add(row["formula_id"])
        aliases = []
        for row in alias_rows:
            normalized_alias = normalize_formula_runtime_text(row.get("normalized_alias") or row.get("alias"))
            if len(normalized_alias) < 3:
                continue
            if len(alias_formula_ids.get(row["normalized_alias"], set())) > 1:
                continue
            confidence = float(row.get("confidence") or 0.0)
            if confidence < 0.72:
                continue
            if int(row.get("needs_manual_review") or 0) and confidence < 0.95:
                continue
            row["normalized_alias"] = normalized_alias
            row["confidence"] = confidence
            aliases.append(row)
        aliases.sort(key=lambda row: (-len(row["normalized_alias"]), -float(row["confidence"]), row["normalized_alias"]))

        formula_rows: list[dict[str, Any]] = []
        passage_to_formula_ids: dict[str, list[str]] = {}
        view_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    v.*,
                    COALESCE(m.chapter_name, '') AS chapter_name
                FROM retrieval_ready_formula_view AS v
                LEFT JOIN records_main_passages AS m
                  ON m.passage_id = v.primary_formula_passage_id
                """
            )
        ]
        for row in view_rows:
            formula_id = row["formula_id"]
            if formula_id not in formulas_by_id:
                continue
            source_ids = safe_json_list(row.get("source_passage_ids_json"))
            for passage_id in source_ids:
                passage_to_formula_ids.setdefault(passage_id, [])
                if formula_id not in passage_to_formula_ids[passage_id]:
                    passage_to_formula_ids[passage_id].append(formula_id)
            record_id = f"formula:{formula_id}"
            formula_rows.append(
                {
                    "retrieval_entry_id": record_id,
                    "record_table": "retrieval_ready_formula_view",
                    "record_id": record_id,
                    "source_record_id": formula_id,
                    "dataset_variant": "safe",
                    "source_object": "formulas",
                    "source_type": "formula_object",
                    "retrieval_text": row.get("retrieval_text") or "",
                    "normalized_text": normalize_formula_runtime_text(row.get("retrieval_text") or ""),
                    "book_id": "ZJSHL",
                    "chapter_id": first_json_value(row.get("chapter_ids_json")) or row.get("chapter_id"),
                    "chapter_name": row.get("chapter_name") or "",
                    "evidence_level": row.get("allowed_evidence_level") or "A",
                    "display_allowed": "primary",
                    "risk_flag": "[]",
                    "requires_disclaimer": 0,
                    "default_weight_tier": "highest",
                    "policy_source_id": FORMULA_OBJECT_SOURCE_ID,
                    "backref_target_type": "formula_span",
                    "backref_target_ids_json": row.get("source_passage_ids_json") or "[]",
                    "formula_id": formula_id,
                    "canonical_name": row.get("canonical_name") or formulas_by_id[formula_id].get("canonical_name"),
                    "primary_formula_passage_id": row.get("primary_formula_passage_id"),
                    "source_passage_ids_json": row.get("source_passage_ids_json") or "[]",
                    "source_confidence": row.get("source_confidence") or formulas_by_id[formula_id].get("source_confidence"),
                }
            )

        return cls(
            enabled=bool(formula_rows and aliases),
            formulas_by_id=formulas_by_id,
            aliases=aliases,
            formula_rows=formula_rows,
            passage_to_formula_ids=passage_to_formula_ids,
            disabled_reason=None if formula_rows and aliases else "empty formula runtime rows or aliases",
        )

    def resolve(self, query_text: str) -> dict[str, Any]:
        empty = {
            "enabled": self.enabled,
            "type": "none",
            "formula_ids": [],
            "matches": [],
            "disabled_reason": self.disabled_reason,
        }
        if not self.enabled:
            return empty

        normalized_query = normalize_formula_runtime_text(query_text)
        if not normalized_query:
            return empty

        occupied: list[tuple[int, int]] = []
        matches: list[dict[str, Any]] = []
        for alias in self.aliases:
            normalized_alias = alias["normalized_alias"]
            start = normalized_query.find(normalized_alias)
            while start >= 0:
                end = start + len(normalized_alias)
                overlaps = any(not (end <= used_start or start >= used_end) for used_start, used_end in occupied)
                if not overlaps:
                    occupied.append((start, end))
                    formula = self.formulas_by_id.get(alias["formula_id"], {})
                    matches.append(
                        {
                            "formula_id": alias["formula_id"],
                            "canonical_name": formula.get("canonical_name"),
                            "alias": alias.get("alias"),
                            "normalized_alias": normalized_alias,
                            "alias_type": alias.get("alias_type"),
                            "confidence": alias.get("confidence"),
                            "span": [start, end],
                        }
                    )
                    break
                start = normalized_query.find(normalized_alias, start + 1)

        if not matches:
            return empty

        matches.sort(key=lambda item: (item["span"][0], -(item["span"][1] - item["span"][0])))
        formula_ids = unique_preserve_order(match["formula_id"] for match in matches)
        query_has_comparison_hint = any(compact_text(hint) in normalized_query for hint in FORMULA_COMPARISON_HINTS)
        if len(formula_ids) >= 2:
            return {
                "enabled": True,
                "type": "comparison",
                "formula_ids": formula_ids,
                "left_formula_id": formula_ids[0],
                "right_formula_id": formula_ids[1],
                "matches": matches,
                "disabled_reason": None,
            }
        if query_has_comparison_hint and len(matches) >= 2:
            return {
                "enabled": True,
                "type": "comparison",
                "formula_ids": formula_ids,
                "left_formula_id": formula_ids[0],
                "right_formula_id": formula_ids[0],
                "matches": matches,
                "disabled_reason": None,
            }
        return {
            "enabled": True,
            "type": "exact",
            "formula_ids": formula_ids,
            "target_formula_id": formula_ids[0],
            "matches": matches,
            "disabled_reason": None,
        }

    def formula_ids_for_row(self, row: dict[str, Any]) -> list[str]:
        formula_id = row.get("formula_id")
        if formula_id:
            return [str(formula_id)]

        passage_ids: list[str] = []
        source_record_id = str(row.get("source_record_id") or "")
        if source_record_id:
            passage_ids.append(source_record_id)
        passage_ids.extend(safe_json_list(row.get("backref_target_ids_json")))

        formula_ids: list[str] = []
        for passage_id in unique_preserve_order(passage_ids):
            formula_ids.extend(self.passage_to_formula_ids.get(passage_id) or [])
        return unique_preserve_order(formula_ids)


class DefinitionRuntimeIndex:
    def __init__(
        self,
        *,
        enabled: bool,
        definition_rows: list[dict[str, Any]] | None = None,
        concepts_by_id: dict[str, dict[str, Any]] | None = None,
        alias_rows: list[dict[str, Any]] | None = None,
        query_family_rows: list[dict[str, Any]] | None = None,
        passage_to_concept_ids: dict[str, list[str]] | None = None,
        disabled_reason: str | None = None,
    ) -> None:
        self.enabled = enabled
        self.definition_rows = definition_rows or []
        self.definition_row_by_concept_id = {
            row["concept_id"]: row for row in self.definition_rows if row.get("concept_id")
        }
        self.concepts_by_id = concepts_by_id or {}
        self.alias_rows = alias_rows or []
        self.query_family_rows = query_family_rows or []
        self.passage_to_concept_ids = passage_to_concept_ids or {}
        self.disabled_reason = disabled_reason

    @classmethod
    def disabled(cls, reason: str) -> "DefinitionRuntimeIndex":
        return cls(enabled=False, disabled_reason=reason)

    def empty_resolution(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "type": "none",
            "concept_ids": [],
            "matches": [],
            "matched_query_family": None,
            "normalized_target_term": None,
            "canonical_target_term": None,
            "canonical_query": None,
            "disabled_reason": self.disabled_reason,
        }

    @classmethod
    def from_db(cls, conn: sqlite3.Connection) -> "DefinitionRuntimeIndex":
        if runtime_env_flag_enabled(os.getenv(DEFINITION_OBJECT_DISABLE_ENV)):
            return cls.disabled(f"{DEFINITION_OBJECT_DISABLE_ENV}=1")

        existing = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE name IN ({})".format(
                    ",".join("?" for _ in DEFINITION_RUNTIME_TABLES)
                ),
                DEFINITION_RUNTIME_TABLES,
            )
        }
        missing = [name for name in DEFINITION_RUNTIME_TABLES if name not in existing]
        if missing:
            return cls.disabled("missing:" + ",".join(missing))

        optional_existing = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE name IN ({})".format(
                    ",".join("?" for _ in DEFINITION_RUNTIME_OPTIONAL_TABLES)
                ),
                DEFINITION_RUNTIME_OPTIONAL_TABLES,
            )
        }

        concepts_by_id = {
            row["concept_id"]: dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM definition_term_registry
                WHERE is_active = 1
                """
            )
        }
        view_rows = [dict(row) for row in conn.execute("SELECT * FROM retrieval_ready_definition_view")]
        definition_rows: list[dict[str, Any]] = []
        passage_to_concept_ids: dict[str, list[str]] = {}
        for row in view_rows:
            concept_id = row["concept_id"]
            record_id = f"safe:definition_terms:{concept_id}"
            for passage_id in safe_json_list(row.get("source_passage_ids_json")):
                passage_to_concept_ids.setdefault(passage_id, [])
                if concept_id not in passage_to_concept_ids[passage_id]:
                    passage_to_concept_ids[passage_id].append(concept_id)
            definition_rows.append(
                {
                    "retrieval_entry_id": record_id,
                    "record_table": "retrieval_ready_definition_view",
                    "record_id": record_id,
                    "source_record_id": concept_id,
                    "dataset_variant": "safe",
                    "source_object": "definition_terms",
                    "source_type": "definition_evidence_object",
                    "retrieval_text": row.get("retrieval_text") or row.get("primary_evidence_text") or "",
                    "normalized_text": compact_text(row.get("retrieval_text") or row.get("primary_evidence_text")),
                    "book_id": "ZJSHL",
                    "chapter_id": first_json_value(row.get("chapter_ids_json")),
                    "chapter_name": "",
                    "evidence_level": row.get("allowed_evidence_level") or "A",
                    "display_allowed": "primary",
                    "risk_flag": "[]",
                    "requires_disclaimer": 0,
                    "default_weight_tier": "highest",
                    "policy_source_id": DEFINITION_OBJECT_SOURCE_ID,
                    "backref_target_type": "definition_source_passages",
                    "backref_target_ids_json": row.get("source_passage_ids_json") or "[]",
                    "concept_id": concept_id,
                    "canonical_term": row.get("canonical_term"),
                    "normalized_term": row.get("normalized_term"),
                    "concept_type": row.get("concept_type"),
                    "query_aliases_json": row.get("query_aliases_json") or "[]",
                    "primary_evidence_type": row.get("primary_evidence_type"),
                    "primary_evidence_text": row.get("primary_evidence_text"),
                    "primary_support_passage_id": row.get("primary_support_passage_id"),
                    "source_passage_ids_json": row.get("source_passage_ids_json") or "[]",
                    "source_confidence": row.get("source_confidence"),
                    "primary_source_table": row.get("primary_source_table") or "",
                    "promotion_state": row.get("promotion_state") or "",
                    "promotion_source_layer": row.get("promotion_source_layer") or "",
                    "promotion_reason": row.get("promotion_reason") or "",
                    "review_only_reason": row.get("review_only_reason") or "",
                    "notes": row.get("notes") or "",
                }
            )

        alias_rows: list[dict[str, Any]] = []
        if "term_alias_registry" in optional_existing:
            raw_alias_rows = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT
                        alias,
                        normalized_alias,
                        concept_id,
                        canonical_term,
                        alias_type,
                        confidence,
                        source
                    FROM term_alias_registry
                    WHERE is_active = 1
                    """
                )
            ]
            for row in raw_alias_rows:
                if row["concept_id"] not in {item["concept_id"] for item in definition_rows}:
                    continue
                normalized_alias = compact_text(row.get("normalized_alias") or row.get("alias"))
                if len(normalized_alias) < 2:
                    continue
                row["normalized_alias"] = normalized_alias
                row["confidence"] = float(row.get("confidence") or 0.0)
                alias_rows.append(row)

        if "learner_query_normalization_lexicon" in optional_existing:
            lexicon_rows = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT
                        entry_type,
                        match_mode,
                        surface_form,
                        normalized_surface_form,
                        target_type,
                        target_id,
                        target_term,
                        intent_hint,
                        canonical_query_template,
                        confidence,
                        source,
                        notes
                    FROM learner_query_normalization_lexicon
                    WHERE is_active = 1
                    """
                )
            ]
        else:
            lexicon_rows = []

        query_family_rows = [
            {
                **row,
                "normalized_surface_form": compact_text(row.get("normalized_surface_form") or row.get("surface_form")),
                "confidence": float(row.get("confidence") or 0.0),
            }
            for row in lexicon_rows
            if row.get("entry_type") == "query_family"
        ]
        query_family_rows.sort(
            key=lambda row: (-len(row["normalized_surface_form"]), -row["confidence"], row["surface_form"])
        )

        for row in lexicon_rows:
            if row.get("entry_type") != "term_surface":
                continue
            concept_id = str(row.get("target_id") or "")
            if concept_id not in {item["concept_id"] for item in definition_rows}:
                continue
            normalized_alias = compact_text(row.get("normalized_surface_form") or row.get("surface_form"))
            if len(normalized_alias) < 2:
                continue
            alias_rows.append(
                {
                    "alias": row.get("surface_form") or row.get("target_term") or "",
                    "normalized_alias": normalized_alias,
                    "concept_id": concept_id,
                    "canonical_term": row.get("target_term") or "",
                    "alias_type": "learner_term_surface",
                    "confidence": float(row.get("confidence") or 0.0),
                    "source": row.get("source") or "learner_query_normalization_lexicon",
                }
            )

        deduped_aliases: dict[tuple[str, str], dict[str, Any]] = {}
        for row in alias_rows:
            key = (row["concept_id"], row["normalized_alias"])
            existing = deduped_aliases.get(key)
            if existing is None or float(row["confidence"]) > float(existing["confidence"]):
                deduped_aliases[key] = row
        alias_rows = sorted(
            deduped_aliases.values(),
            key=lambda row: (-len(row["normalized_alias"]), -float(row["confidence"]), row["normalized_alias"]),
        )

        return cls(
            enabled=bool(definition_rows),
            definition_rows=definition_rows,
            concepts_by_id=concepts_by_id,
            alias_rows=alias_rows,
            query_family_rows=query_family_rows,
            passage_to_concept_ids=passage_to_concept_ids,
            disabled_reason=None if definition_rows else "empty definition runtime rows",
        )

    def _match_aliases(self, normalized_query: str) -> list[dict[str, Any]]:
        occupied: list[tuple[int, int]] = []
        matches: list[dict[str, Any]] = []
        for alias in self.alias_rows:
            normalized_alias = alias["normalized_alias"]
            start = normalized_query.find(normalized_alias)
            while start >= 0:
                end = start + len(normalized_alias)
                overlaps = any(not (end <= used_start or start >= used_end) for used_start, used_end in occupied)
                if not overlaps:
                    occupied.append((start, end))
                    matches.append(
                        {
                            "concept_id": alias["concept_id"],
                            "canonical_term": alias.get("canonical_term"),
                            "alias": alias.get("alias"),
                            "normalized_alias": normalized_alias,
                            "alias_type": alias.get("alias_type"),
                            "confidence": alias.get("confidence"),
                            "source": alias.get("source"),
                            "span": [start, end],
                        }
                    )
                    break
                start = normalized_query.find(normalized_alias, start + 1)
        matches.sort(key=lambda item: (item["span"][0], -(item["span"][1] - item["span"][0])))
        return matches

    def resolve(self, query_text: str) -> dict[str, Any]:
        empty = self.empty_resolution()
        if not self.enabled:
            return empty

        normalized_query = compact_text(query_text)
        if not normalized_query:
            return empty

        matched_family: dict[str, Any] | None = None
        stripped_query = normalized_query
        for row in self.query_family_rows:
            surface = row["normalized_surface_form"]
            if not surface:
                continue
            residual = None
            if row["match_mode"] == "prefix" and normalized_query.startswith(surface):
                residual = normalized_query[len(surface) :]
            elif row["match_mode"] == "suffix" and normalized_query.endswith(surface):
                residual = normalized_query[: -len(surface)]
            elif row["match_mode"] == "exact" and normalized_query == surface:
                residual = ""
            if residual is None:
                continue
            residual = residual.strip()
            if row["match_mode"] != "exact" and not residual:
                continue
            matched_family = row
            stripped_query = residual or normalized_query
            break

        matches = self._match_aliases(stripped_query) if stripped_query else []
        if not matches and stripped_query != normalized_query:
            matches = self._match_aliases(normalized_query)
        if matched_family and stripped_query:
            exact_topic_matches = [
                match
                for match in matches
                if match.get("span") == [0, len(stripped_query)]
            ]
            if exact_topic_matches:
                matches = exact_topic_matches
            else:
                return empty
        if not matches:
            return empty

        concept_ids = unique_preserve_order(match["concept_id"] for match in matches)
        canonical_target_term = matches[0].get("canonical_term") or self.concepts_by_id.get(
            concept_ids[0], {}
        ).get("canonical_term")
        canonical_query = None
        if matched_family and canonical_target_term:
            canonical_query = str(matched_family.get("canonical_query_template") or "").replace(
                "{topic}",
                canonical_target_term,
            )

        return {
            "enabled": True,
            "type": "normalized_query" if matched_family else "exact_term",
            "concept_ids": concept_ids,
            "matches": matches,
            "matched_query_family": None
            if matched_family is None
            else {
                "surface_form": matched_family.get("surface_form"),
                "match_mode": matched_family.get("match_mode"),
                "intent_hint": matched_family.get("intent_hint"),
                "canonical_query_template": matched_family.get("canonical_query_template"),
            },
            "normalized_target_term": compact_text(canonical_target_term),
            "canonical_target_term": canonical_target_term,
            "canonical_query": canonical_query,
            "disabled_reason": None,
        }

    def concept_ids_for_row(self, row: dict[str, Any]) -> list[str]:
        concept_id = row.get("concept_id")
        if concept_id:
            return [str(concept_id)]

        passage_ids: list[str] = []
        source_record_id = str(row.get("source_record_id") or "")
        if source_record_id:
            passage_ids.append(source_record_id)
        passage_ids.extend(safe_json_list(row.get("backref_target_ids_json")))

        concept_ids: list[str] = []
        for passage_id in unique_preserve_order(passage_ids):
            concept_ids.extend(self.passage_to_concept_ids.get(passage_id) or [])
        return unique_preserve_order(concept_ids)


def safe_json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    try:
        loaded = json.loads(str(value))
    except Exception:
        return []
    if not isinstance(loaded, list):
        return []
    return [str(item) for item in loaded if item]


def first_json_value(value: Any) -> str | None:
    values = safe_json_list(value)
    return values[0] if values else None


def infer_query_theme(query_focus: str) -> dict[str, Any]:
    anchor = extract_title_anchor(query_focus) or compact_text(query_focus)
    normalized_anchor = normalize_formula_anchor(anchor)
    if anchor and any(anchor.endswith(suffix) for suffix in FORMULA_QUERY_SUFFIXES) and len(normalized_anchor) >= 2:
        return {
            "type": "formula_name",
            "anchor": anchor,
            "normalized_anchor": normalized_anchor,
        }
    return {
        "type": "generic",
        "anchor": anchor or compact_text(query_focus),
        "normalized_anchor": compact_text(query_focus),
    }


def evaluate_topic_consistency(query_theme: dict[str, Any], candidate_text: str | None) -> dict[str, Any]:
    candidate_anchor = clean_formula_title_anchor(extract_raw_title_anchor(candidate_text))
    candidate_anchor_normalized = normalize_formula_anchor(candidate_anchor)
    query_anchor = query_theme.get("anchor", "")
    query_anchor_normalized = query_theme.get("normalized_anchor", "")

    if query_theme.get("type") != "formula_name":
        return {
            "topic_anchor": candidate_anchor,
            "topic_consistency": "neutral",
            "precision_adjustment": 0.0,
            "primary_allowed": True,
        }

    if candidate_anchor_normalized and candidate_anchor_normalized == query_anchor_normalized:
        return {
            "topic_anchor": candidate_anchor,
            "topic_consistency": "exact_formula_anchor",
            "precision_adjustment": 24.0,
            "primary_allowed": True,
        }

    if candidate_anchor_normalized and query_anchor_normalized and query_anchor_normalized in candidate_anchor_normalized:
        return {
            "topic_anchor": candidate_anchor,
            "topic_consistency": "expanded_formula_anchor",
            "precision_adjustment": -18.0,
            "primary_allowed": False,
        }

    if candidate_anchor_normalized and any(candidate_anchor.endswith(suffix) for suffix in FORMULA_QUERY_SUFFIXES):
        return {
            "topic_anchor": candidate_anchor,
            "topic_consistency": "different_formula_anchor",
            "precision_adjustment": -28.0,
            "primary_allowed": False,
        }

    candidate_compact = compact_text(candidate_text)
    if query_anchor and query_anchor in candidate_compact:
        return {
            "topic_anchor": candidate_anchor,
            "topic_consistency": "phrase_only_match",
            "precision_adjustment": -8.0,
            "primary_allowed": False,
        }

    return {
        "topic_anchor": candidate_anchor,
        "topic_consistency": "formula_query_off_topic",
        "precision_adjustment": -14.0,
        "primary_allowed": False,
    }


def baseline_topic_consistency(candidate_text: str | None) -> dict[str, Any]:
    return {
        "topic_anchor": extract_title_anchor(candidate_text),
        "topic_consistency": "baseline_unchecked",
        "precision_adjustment": 0.0,
        "primary_allowed": True,
    }


def compute_text_match_score(query_focus: str, query_terms: list[str], candidate_text: str) -> tuple[float, list[str]]:
    candidate_compact = compact_text(candidate_text)
    if not candidate_compact:
        return 0.0, []

    score = 0.0
    matched_terms: list[str] = []

    if query_focus and query_focus in candidate_compact:
        score += 100.0 + min(len(query_focus) * 4.0, 40.0)
        matched_terms.append(query_focus)

    for term in query_terms:
        if term == query_focus:
            continue
        if term in candidate_compact:
            if len(term) >= 4:
                score += 8.0
            elif len(term) == 3:
                score += 4.0
            else:
                score += 1.5
            if term not in matched_terms and len(matched_terms) < 12:
                matched_terms.append(term)

    return score, matched_terms


def preview_text(text: str | None, limit: int = 80) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[:limit] + "..."


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


@dataclass
class RetrievalEngine:
    db_path: Path
    policy_path: Path
    candidate_limit: int = DEFAULT_TOTAL_LIMIT

    def __post_init__(self) -> None:
        self.policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._assert_policy_guards()
        self.definition_runtime = DefinitionRuntimeIndex.from_db(self.conn)
        self.formula_runtime = FormulaRuntimeIndex.from_db(self.conn)
        base_rows = [dict(row) for row in self.conn.execute("SELECT * FROM vw_retrieval_records_unified")]
        self.unified_rows = self.definition_runtime.definition_rows + self.formula_runtime.formula_rows + base_rows
        self.record_by_id = {row["record_id"]: row for row in self.unified_rows}

    def close(self) -> None:
        self.conn.close()

    def _assert_policy_guards(self) -> None:
        annotation_link_count = self.conn.execute(
            "SELECT COUNT(*) FROM vw_retrieval_records_unified WHERE source_object = 'annotation_links'"
        ).fetchone()[0]
        if annotation_link_count != 0:
            raise ValueError("annotation_links leaked into vw_retrieval_records_unified")

    def build_request(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        query_focus = extract_focus_text(query_text)
        formula_normalization = self.formula_runtime.resolve(query_text)
        term_normalization = (
            self.definition_runtime.resolve(query_text)
            if formula_normalization.get("type") == "none"
            else self.definition_runtime.empty_resolution()
        )
        query_focus_source = "noise_stripped_query"
        normalized_target_term = term_normalization.get("normalized_target_term")
        if normalized_target_term and formula_normalization.get("type") == "none":
            query_focus = normalized_target_term
            query_focus_source = "term_normalization"
        query_theme = infer_query_theme(query_focus)
        if formula_normalization["type"] == "exact":
            formula_id = formula_normalization["formula_ids"][0]
            formula = self.formula_runtime.formulas_by_id.get(formula_id) or {}
            query_theme = {
                "type": "formula_name",
                "anchor": formula.get("canonical_name") or query_theme.get("anchor"),
                "normalized_anchor": formula.get("normalized_name") or query_theme.get("normalized_anchor"),
                "formula_id": formula_id,
                "formula_object_normalized": True,
            }
        elif formula_normalization["type"] == "comparison":
            query_theme = {
                **query_theme,
                "type": "formula_comparison",
                "formula_ids": formula_normalization["formula_ids"],
                "formula_object_normalized": True,
            }
        return {
            "query_text": query_text,
            "query_text_normalized": query_focus,
            "query_focus_source": query_focus_source,
            "query_theme": query_theme,
            "formula_normalization": formula_normalization,
            "term_normalization": term_normalization,
            "target_mode": "strong_first",
            "precision_profile": "tight_primary" if tight_primary_precision else "baseline",
            "allow_levels": ["A", "B", "C"],
            "blocked_sources": ["annotation_links"],
            "source_priority": self.policy["stage_policy"]["retrieval_stage"]["priority_order"],
            "candidate_budget": {
                "total_limit": self.candidate_limit,
                "per_source_soft_limit": SOURCE_BUDGETS,
            },
            "scope_filters": {"book_id": "ZJSHL", "chapter_id": None},
        }

    def retrieve(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        request = self.build_request(query_text, tight_primary_precision=tight_primary_precision)
        raw_candidates = self._collect_raw_candidates(request)
        resolved = self._resolve_candidates(raw_candidates, request)
        slots = self._assemble_slots(resolved)
        mode_info = self._determine_mode(slots)
        return {
            "query_request": request,
            "raw_candidates": raw_candidates,
            "primary_evidence": slots["primary_evidence"],
            "secondary_evidence": slots["secondary_evidence"],
            "risk_materials": slots["risk_materials"],
            "retrieval_trace": resolved["retrieval_trace"],
            "mode": mode_info["mode"],
            "mode_reason": mode_info["mode_reason"],
            "runtime_risk_flags": mode_info["runtime_risk_flags"],
            "annotation_links_enabled": False,
        }

    def _collect_raw_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query_focus = request["query_text_normalized"]
        query_theme = request["query_theme"]
        query_terms = build_query_terms(query_focus)
        scored: list[dict[str, Any]] = (
            self._collect_definition_object_candidates(request) + self._collect_formula_object_candidates(request)
        )
        tight_primary_precision = request["precision_profile"] == "tight_primary"

        for row in self.unified_rows:
            if row["source_object"] == "annotation_links":
                continue
            text_score, matched_terms = compute_text_match_score(query_focus, query_terms, row["normalized_text"])
            if text_score <= 0:
                continue
            if tight_primary_precision:
                topic_meta = self._row_topic_meta(request, row)
            else:
                topic_meta = baseline_topic_consistency(row["retrieval_text"])
            weight_bonus = WEIGHT_BONUS.get(row["default_weight_tier"], 0.0)
            combined_score = text_score + weight_bonus + topic_meta["precision_adjustment"]
            candidate = dict(row)
            candidate.update(
                {
                    "text_match_score": round(text_score, 3),
                    "weight_bonus": weight_bonus,
                    "precision_adjustment": topic_meta["precision_adjustment"],
                    "combined_score": round(combined_score, 3),
                    "matched_terms": matched_terms,
                    "topic_anchor": topic_meta["topic_anchor"],
                    "topic_consistency": topic_meta["topic_consistency"],
                    "primary_allowed": topic_meta["primary_allowed"],
                    "formula_candidate_ids": topic_meta.get("formula_candidate_ids", []),
                    "formula_scope": topic_meta.get("formula_scope"),
                }
            )
            if not self._passes_formula_scope_gate(request, candidate):
                continue
            scored.append(candidate)

        if not scored:
            return []

        max_text_score = max(candidate["text_match_score"] for candidate in scored)
        minimum_text_score = max(2.0, max_text_score * 0.2)
        scored = [candidate for candidate in scored if candidate["text_match_score"] >= minimum_text_score]

        scored.sort(
            key=lambda row: (
                -row["combined_score"],
                -row["text_match_score"],
                -WEIGHT_BONUS.get(row["default_weight_tier"], 0.0),
                row["record_id"],
            )
        )

        selected: list[dict[str, Any]] = []
        per_source_counts: Counter[str] = Counter()
        for candidate in scored:
            policy_source_id = candidate["policy_source_id"]
            limit = SOURCE_BUDGETS.get(policy_source_id, self.candidate_limit)
            if per_source_counts[policy_source_id] >= limit:
                continue
            selected.append(candidate)
            per_source_counts[policy_source_id] += 1
            if len(selected) >= self.candidate_limit:
                break

        return self._dedupe_semantic_candidates(selected)

    def _collect_formula_object_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        normalization = request.get("formula_normalization") or {}
        formula_ids = normalization.get("formula_ids") or []
        if not self.formula_runtime.enabled or normalization.get("type") not in {"exact", "comparison"}:
            return []

        candidates: list[dict[str, Any]] = []
        for rank, formula_id in enumerate(formula_ids[:4], start=1):
            row = self.formula_runtime.formula_row_by_formula_id.get(formula_id)
            if not row:
                continue
            matched_aliases = [
                match.get("alias") or match.get("normalized_alias")
                for match in normalization.get("matches") or []
                if match.get("formula_id") == formula_id
            ]
            alias_lengths = [
                len(str(match.get("normalized_alias") or ""))
                for match in normalization.get("matches") or []
                if match.get("formula_id") == formula_id
            ]
            text_score = 180.0 + (max(alias_lengths) * 6.0 if alias_lengths else 0.0)
            topic_meta = self._row_topic_meta(request, row)
            weight_bonus = WEIGHT_BONUS.get(row["default_weight_tier"], 0.0)
            combined_score = text_score + weight_bonus + topic_meta["precision_adjustment"] + (8.0 / rank)
            candidate = dict(row)
            candidate.update(
                {
                    "text_match_score": round(text_score, 6),
                    "weight_bonus": weight_bonus,
                    "precision_adjustment": topic_meta["precision_adjustment"],
                    "combined_score": round(combined_score, 6),
                    "matched_terms": unique_preserve_order([term for term in matched_aliases if term]),
                    "topic_anchor": topic_meta["topic_anchor"],
                    "topic_consistency": topic_meta["topic_consistency"],
                    "primary_allowed": topic_meta["primary_allowed"],
                    "formula_candidate_ids": topic_meta.get("formula_candidate_ids", []),
                    "formula_scope": topic_meta.get("formula_scope"),
                    "primary_block_reason": None if topic_meta["primary_allowed"] else topic_meta["topic_consistency"],
                    "sparse_score": round(combined_score, 6),
                    "sparse_bm25_raw": None,
                    "sparse_bm25_score": None,
                    "dense_score": 0.0,
                    "dense_rank_score": 0.0,
                    "rrf_score": 0.0,
                    "rerank_raw_score": None,
                    "rerank_score": None,
                    "stage_sources": ["formula_object"],
                    "stage_ranks": {"formula_object": rank},
                }
            )
            if self._passes_formula_scope_gate(request, candidate):
                candidates.append(candidate)
        return candidates

    def _collect_definition_object_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        normalization = request.get("term_normalization") or {}
        concept_ids = normalization.get("concept_ids") or []
        if not self.definition_runtime.enabled or normalization.get("type") not in {"exact_term", "normalized_query"}:
            return []

        candidates: list[dict[str, Any]] = []
        for rank, concept_id in enumerate(concept_ids[:4], start=1):
            row = self.definition_runtime.definition_row_by_concept_id.get(concept_id)
            if not row:
                continue
            matched_aliases = [
                match.get("alias") or match.get("normalized_alias")
                for match in normalization.get("matches") or []
                if match.get("concept_id") == concept_id
            ]
            alias_lengths = [
                len(str(match.get("normalized_alias") or ""))
                for match in normalization.get("matches") or []
                if match.get("concept_id") == concept_id
            ]
            text_score = 170.0 + (max(alias_lengths) * 7.0 if alias_lengths else 0.0)
            topic_meta = self._row_topic_meta(request, row)
            weight_bonus = WEIGHT_BONUS.get(row["default_weight_tier"], 0.0)
            combined_score = text_score + weight_bonus + topic_meta["precision_adjustment"] + (8.0 / rank)
            candidate = dict(row)
            candidate.update(
                {
                    "text_match_score": round(text_score, 6),
                    "weight_bonus": weight_bonus,
                    "precision_adjustment": topic_meta["precision_adjustment"],
                    "combined_score": round(combined_score, 6),
                    "matched_terms": unique_preserve_order([term for term in matched_aliases if term]),
                    "topic_anchor": topic_meta["topic_anchor"],
                    "topic_consistency": topic_meta["topic_consistency"],
                    "primary_allowed": topic_meta["primary_allowed"],
                    "definition_candidate_ids": topic_meta.get("definition_candidate_ids", []),
                    "definition_scope": topic_meta.get("definition_scope"),
                    "primary_block_reason": None if topic_meta["primary_allowed"] else topic_meta["topic_consistency"],
                    "sparse_score": round(combined_score, 6),
                    "sparse_bm25_raw": None,
                    "sparse_bm25_score": None,
                    "dense_score": 0.0,
                    "dense_rank_score": 0.0,
                    "rrf_score": 0.0,
                    "rerank_raw_score": None,
                    "rerank_score": None,
                    "stage_sources": ["definition_object"],
                    "stage_ranks": {"definition_object": rank},
                }
            )
            candidates.append(candidate)
        return candidates

    def _row_topic_meta(self, request: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
        base_meta = evaluate_topic_consistency(request["query_theme"], row["retrieval_text"])
        formula_meta = self._formula_topic_meta(request, row)
        if formula_meta:
            return {**base_meta, **formula_meta}
        definition_meta = self._definition_topic_meta(request, row)
        if definition_meta:
            return {**base_meta, **definition_meta}
        return base_meta

    def _formula_topic_meta(self, request: dict[str, Any], row: dict[str, Any]) -> dict[str, Any] | None:
        normalization = request.get("formula_normalization") or {}
        query_type = normalization.get("type")
        target_formula_ids = set(normalization.get("formula_ids") or [])
        if query_type not in {"exact", "comparison"} or not target_formula_ids or not self.formula_runtime.enabled:
            return None

        candidate_formula_ids = self.formula_runtime.formula_ids_for_row(row)
        if not candidate_formula_ids:
            return None

        matching_formula_ids = [formula_id for formula_id in candidate_formula_ids if formula_id in target_formula_ids]
        is_formula_object = row.get("record_table") == "retrieval_ready_formula_view"
        if matching_formula_ids:
            formula_id = matching_formula_ids[0]
            formula = self.formula_runtime.formulas_by_id.get(formula_id) or {}
            if is_formula_object:
                topic_consistency = "formula_object_exact" if query_type == "exact" else "comparison_formula_object"
                precision_adjustment = 72.0 if query_type == "exact" else 56.0
                formula_scope = "target_formula_object"
            else:
                topic_consistency = "same_formula_span" if query_type == "exact" else "comparison_formula_span"
                precision_adjustment = 36.0 if query_type == "exact" else 30.0
                formula_scope = "target_formula_span"
            return {
                "topic_anchor": formula.get("canonical_name") or row.get("topic_anchor") or "",
                "topic_consistency": topic_consistency,
                "precision_adjustment": precision_adjustment,
                "primary_allowed": True,
                "formula_candidate_ids": candidate_formula_ids,
                "formula_scope": formula_scope,
            }

        first_formula = self.formula_runtime.formulas_by_id.get(candidate_formula_ids[0]) or {}
        return {
            "topic_anchor": first_formula.get("canonical_name") or row.get("topic_anchor") or "",
            "topic_consistency": "different_formula_anchor"
            if query_type == "exact"
            else "comparison_out_of_scope_formula_anchor",
            "precision_adjustment": -72.0 if is_formula_object else -52.0,
            "primary_allowed": False,
            "formula_candidate_ids": candidate_formula_ids,
            "formula_scope": "different_formula_object" if is_formula_object else "different_formula_span",
        }

    def _definition_topic_meta(self, request: dict[str, Any], row: dict[str, Any]) -> dict[str, Any] | None:
        normalization = request.get("term_normalization") or {}
        target_concept_ids = set(normalization.get("concept_ids") or [])
        if normalization.get("type") not in {"exact_term", "normalized_query"} or not target_concept_ids:
            return None

        candidate_concept_ids = self.definition_runtime.concept_ids_for_row(row)
        if not candidate_concept_ids:
            return None

        matching_concept_ids = [concept_id for concept_id in candidate_concept_ids if concept_id in target_concept_ids]
        is_definition_object = row.get("record_table") == "retrieval_ready_definition_view"
        if matching_concept_ids:
            concept_id = matching_concept_ids[0]
            concept = self.definition_runtime.concepts_by_id.get(concept_id) or {}
            return {
                "topic_anchor": concept.get("canonical_term") or row.get("canonical_term") or "",
                "topic_consistency": "definition_object_exact" if is_definition_object else "definition_source_span",
                "precision_adjustment": 64.0 if is_definition_object else 28.0,
                "primary_allowed": True,
                "definition_candidate_ids": candidate_concept_ids,
                "definition_scope": "target_definition_object" if is_definition_object else "target_definition_span",
            }

        if not is_definition_object:
            return None

        concept = self.definition_runtime.concepts_by_id.get(candidate_concept_ids[0]) or {}
        return {
            "topic_anchor": concept.get("canonical_term") or row.get("canonical_term") or "",
            "topic_consistency": "different_definition_object",
            "precision_adjustment": -24.0,
            "primary_allowed": False,
            "definition_candidate_ids": candidate_concept_ids,
            "definition_scope": "different_definition_object",
        }

    def _passes_formula_scope_gate(self, request: dict[str, Any], candidate: dict[str, Any]) -> bool:
        normalization = request.get("formula_normalization") or {}
        if normalization.get("type") not in {"exact", "comparison"}:
            return True
        if candidate.get("formula_scope") in {"target_formula_object", "target_formula_span"}:
            return True
        if candidate.get("formula_scope") in {"different_formula_object", "different_formula_span"}:
            return False
        return candidate.get("topic_consistency") not in {
            "different_formula_anchor",
            "expanded_formula_anchor",
            "comparison_out_of_scope_formula_anchor",
            "formula_query_off_topic",
        }

    def _semantic_candidate_key(self, candidate: dict[str, Any]) -> str:
        record_table = candidate.get("record_table")
        if record_table in {"records_passages", "risk_registry_ambiguous"}:
            dataset_variant = str(candidate.get("dataset_variant") or "").strip()
            source_record_id = str(candidate.get("source_record_id") or "").strip()
            if dataset_variant and source_record_id:
                return f"{dataset_variant}:risk_passage:{source_record_id}"
        return str(candidate.get("record_id") or "")

    def _semantic_candidate_preference(self, candidate: dict[str, Any]) -> tuple[int, float, float, str]:
        source_object = candidate.get("source_object")
        source_preference = 0
        if source_object == "passages":
            source_preference = 2
        elif source_object == "ambiguous_passages":
            source_preference = 1
        return (
            source_preference,
            float(candidate.get("combined_score") or 0.0),
            float(candidate.get("text_match_score") or 0.0),
            str(candidate.get("record_id") or ""),
        )

    def _dedupe_semantic_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        index_by_key: dict[str, int] = {}
        for candidate in candidates:
            semantic_key = self._semantic_candidate_key(candidate)
            existing_index = index_by_key.get(semantic_key)
            if existing_index is None:
                index_by_key[semantic_key] = len(deduped)
                deduped.append(candidate)
                continue
            existing = deduped[existing_index]
            if self._semantic_candidate_preference(candidate) > self._semantic_candidate_preference(existing):
                deduped[existing_index] = candidate
        return deduped

    def _fetch_chunk_backrefs(self, chunk_record_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                l.link_order,
                l.main_passage_record_id,
                l.main_passage_id,
                m.record_id,
                m.passage_id,
                m.chapter_id,
                m.chapter_name,
                m.text,
                m.normalized_text,
                m.evidence_level,
                m.display_allowed,
                m.risk_flag,
                m.default_weight_tier,
                m.policy_source_id,
                m.requires_disclaimer
            FROM record_chunk_passage_links AS l
            JOIN records_main_passages AS m
              ON m.record_id = l.main_passage_record_id
            WHERE l.chunk_record_id = ?
            ORDER BY l.link_order
        """
        return [dict(row) for row in self.conn.execute(query, (chunk_record_id,))]

    def _resolve_candidates(self, raw_candidates: list[dict[str, Any]], request: dict[str, Any]) -> dict[str, Any]:
        primary_pool: dict[str, dict[str, Any]] = {}
        secondary_pool: dict[str, dict[str, Any]] = {}
        risk_pool: dict[str, dict[str, Any]] = {}
        chunk_hits: list[dict[str, Any]] = []
        used_sources: list[str] = []

        for candidate in raw_candidates:
            used_sources.append(candidate["record_table"])
            if candidate["record_table"] == "retrieval_ready_formula_view":
                formula_entries = self._build_formula_object_entries(candidate, request)
                for index, entry in enumerate(formula_entries):
                    if index == 0 and candidate["primary_allowed"] and entry["evidence_level"] == "A":
                        self._merge_evidence_entry(primary_pool, entry)
                    else:
                        self._merge_evidence_entry(secondary_pool, entry)
                continue

            if candidate["record_table"] == "records_chunks":
                backrefs = self._fetch_chunk_backrefs(candidate["record_id"])
                chunk_hit = {
                    "chunk_record_id": candidate["record_id"],
                    "chunk_score": candidate["combined_score"],
                    "matched_terms": candidate["matched_terms"],
                    "topic_consistency": candidate["topic_consistency"],
                    "topic_anchor": candidate["topic_anchor"],
                    "linked_main_passages": [],
                }
                for backref in backrefs:
                    main_entry = self._build_main_passage_entry_from_chunk(candidate, backref)
                    chunk_hit["linked_main_passages"].append(
                        {
                            "main_passage_record_id": backref["record_id"],
                            "passage_id": backref["passage_id"],
                            "evidence_level": backref["evidence_level"],
                            "display_allowed": backref["display_allowed"],
                        }
                    )
                    if backref["evidence_level"] == "A" and candidate["primary_allowed"]:
                        self._merge_evidence_entry(primary_pool, main_entry)
                    else:
                        if backref["evidence_level"] == "A" and not candidate["primary_allowed"]:
                            main_entry["risk_flag"] = unique_preserve_order(
                                main_entry["risk_flag"] + ["topic_mismatch_demoted"]
                            )
                        self._merge_evidence_entry(secondary_pool, main_entry)
                chunk_hits.append(chunk_hit)
                continue

            if candidate["record_table"] == "records_main_passages":
                entry = self._build_direct_entry(candidate, retrieval_path="direct")
                if candidate["evidence_level"] == "A" and candidate["primary_allowed"]:
                    self._merge_evidence_entry(primary_pool, entry)
                else:
                    if candidate["evidence_level"] == "A" and not candidate["primary_allowed"]:
                        entry["risk_flag"] = unique_preserve_order(entry["risk_flag"] + ["topic_mismatch_demoted"])
                    self._merge_evidence_entry(secondary_pool, entry)
                continue

            if candidate["record_table"] == "controlled_replay_main_passages":
                entry = self._build_direct_entry(candidate, retrieval_path="controlled_replay_allowlist")
                self._merge_evidence_entry(secondary_pool, entry)
                continue

            if candidate["record_table"] == "records_annotations":
                entry = self._build_direct_entry(candidate, retrieval_path="direct")
                self._merge_evidence_entry(secondary_pool, entry)
                continue

            if candidate["record_table"] in {"records_passages", "risk_registry_ambiguous"}:
                entry = self._build_direct_entry(candidate, retrieval_path="direct")
                self._merge_evidence_entry(risk_pool, entry)
                continue

        return {
            "primary_pool": primary_pool,
            "secondary_pool": secondary_pool,
            "risk_pool": risk_pool,
            "retrieval_trace": {
                "chunk_hits": chunk_hits,
                "blocked_sources": ["annotation_links"],
                "used_sources": unique_preserve_order(used_sources),
                "raw_candidate_count": len(raw_candidates),
                "precision_profile": request["precision_profile"],
                "query_theme": request["query_theme"],
            },
        }

    def _build_main_passage_entry_from_chunk(self, chunk_candidate: dict[str, Any], main_row: dict[str, Any]) -> dict[str, Any]:
        return {
            "record_id": main_row["record_id"],
            "source_object": "main_passages",
            "evidence_level": main_row["evidence_level"],
            "display_allowed": main_row["display_allowed"],
            "risk_flag": json.loads(main_row["risk_flag"]),
            "default_weight_tier": main_row["default_weight_tier"],
            "combined_score": round(chunk_candidate["combined_score"] + 0.5, 3),
            "text_match_score": chunk_candidate["text_match_score"],
            "matched_terms": list(chunk_candidate["matched_terms"]),
            "text_preview": preview_text(main_row["text"]),
            "chapter_id": main_row["chapter_id"],
            "chapter_name": main_row["chapter_name"],
            "requires_disclaimer": bool(main_row["requires_disclaimer"]),
            "policy_source_id": main_row["policy_source_id"],
            "topic_anchor": chunk_candidate["topic_anchor"],
            "topic_consistency": chunk_candidate["topic_consistency"],
            "retrieval_paths": [
                {
                    "type": "chunk_backref",
                    "chunk_record_id": chunk_candidate["record_id"],
                    "chunk_score": chunk_candidate["combined_score"],
                }
            ],
        }

    def _build_formula_object_entries(
        self,
        formula_candidate: dict[str, Any],
        request: dict[str, Any],
    ) -> list[dict[str, Any]]:
        passage_ids = safe_json_list(formula_candidate.get("source_passage_ids_json"))
        primary_passage_id = formula_candidate.get("primary_formula_passage_id")
        ordered_passage_ids = unique_preserve_order(
            [str(primary_passage_id)] if primary_passage_id else [] + passage_ids
        )
        if primary_passage_id:
            ordered_passage_ids = unique_preserve_order([str(primary_passage_id)] + passage_ids)
        if not ordered_passage_ids:
            return []

        placeholders = ",".join("?" for _ in ordered_passage_ids)
        rows = [
            dict(row)
            for row in self.conn.execute(
                f"""
                SELECT
                    record_id,
                    passage_id,
                    chapter_id,
                    chapter_name,
                    text,
                    normalized_text,
                    evidence_level,
                    display_allowed,
                    risk_flag,
                    default_weight_tier,
                    policy_source_id,
                    requires_disclaimer
                FROM records_main_passages
                WHERE passage_id IN ({placeholders})
                """,
                ordered_passage_ids,
            )
        ]
        row_by_passage_id = {row["passage_id"]: row for row in rows}
        entries: list[dict[str, Any]] = []
        for index, passage_id in enumerate(ordered_passage_ids):
            main_row = row_by_passage_id.get(passage_id)
            if not main_row:
                continue
            score_adjustment = 1.25 if passage_id == primary_passage_id else max(0.1, 0.75 - index * 0.1)
            entries.append(
                {
                    "record_id": main_row["record_id"],
                    "source_object": "main_passages",
                    "evidence_level": main_row["evidence_level"],
                    "display_allowed": main_row["display_allowed"],
                    "risk_flag": json.loads(main_row["risk_flag"]),
                    "default_weight_tier": main_row["default_weight_tier"],
                    "combined_score": round(float(formula_candidate["combined_score"]) + score_adjustment, 3),
                    "text_match_score": formula_candidate["text_match_score"],
                    "matched_terms": list(formula_candidate["matched_terms"]),
                    "text_preview": preview_text(main_row["text"]),
                    "chapter_id": main_row["chapter_id"],
                    "chapter_name": main_row["chapter_name"],
                    "requires_disclaimer": bool(main_row["requires_disclaimer"]),
                    "policy_source_id": main_row["policy_source_id"],
                    "topic_anchor": formula_candidate["topic_anchor"],
                    "topic_consistency": formula_candidate["topic_consistency"],
                    "formula_candidate_ids": formula_candidate.get("formula_candidate_ids", []),
                    "formula_scope": formula_candidate.get("formula_scope"),
                    "retrieval_paths": [
                        {
                            "type": "formula_object_backref",
                            "formula_record_id": formula_candidate["record_id"],
                            "formula_id": formula_candidate.get("formula_id"),
                            "formula_score": formula_candidate["combined_score"],
                            "source_passage_role": "primary_formula_passage"
                            if passage_id == primary_passage_id
                            else "formula_support_passage",
                        }
                    ],
                }
            )
        return entries

    def _build_direct_entry(self, candidate: dict[str, Any], retrieval_path: str) -> dict[str, Any]:
        return {
            "record_id": candidate["record_id"],
            "source_object": candidate["source_object"],
            "evidence_level": candidate["evidence_level"],
            "display_allowed": candidate["display_allowed"],
            "risk_flag": json.loads(candidate["risk_flag"]),
            "default_weight_tier": candidate["default_weight_tier"],
            "combined_score": candidate["combined_score"],
            "text_match_score": candidate["text_match_score"],
            "matched_terms": list(candidate["matched_terms"]),
            "text_preview": preview_text(candidate["retrieval_text"]),
            "chapter_id": candidate["chapter_id"],
            "chapter_name": candidate["chapter_name"],
            "requires_disclaimer": bool(candidate["requires_disclaimer"]),
            "policy_source_id": candidate["policy_source_id"],
            "topic_anchor": candidate["topic_anchor"],
            "topic_consistency": candidate["topic_consistency"],
            "retrieval_paths": [{"type": retrieval_path}],
        }

    def _merge_evidence_entry(self, pool: dict[str, dict[str, Any]], entry: dict[str, Any]) -> None:
        existing = pool.get(entry["record_id"])
        if not existing:
            pool[entry["record_id"]] = entry
            return
        existing["combined_score"] = max(existing["combined_score"], entry["combined_score"])
        existing["text_match_score"] = max(existing["text_match_score"], entry["text_match_score"])
        existing["matched_terms"] = unique_preserve_order(existing["matched_terms"] + entry["matched_terms"])
        existing["retrieval_paths"] = existing["retrieval_paths"] + entry["retrieval_paths"]
        existing["risk_flag"] = unique_preserve_order(existing["risk_flag"] + entry["risk_flag"])

    def _assemble_slots(self, resolved: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        primary = self._sort_and_trim(resolved["primary_pool"].values(), PRIMARY_LIMIT)
        secondary = self._sort_and_trim(resolved["secondary_pool"].values(), SECONDARY_LIMIT)
        risk = self._sort_and_trim(resolved["risk_pool"].values(), RISK_LIMIT)
        return {
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "risk_materials": risk,
        }

    def _sort_and_trim(self, entries: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        ordered = sorted(
            entries,
            key=lambda row: (
                -row["combined_score"],
                -row["text_match_score"],
                -WEIGHT_BONUS.get(row["default_weight_tier"], 0.0),
                row["record_id"],
            ),
        )
        return ordered[:limit]

    def _determine_mode(self, slots: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        primary = slots["primary_evidence"]
        secondary = slots["secondary_evidence"]
        risk = slots["risk_materials"]

        if primary:
            if secondary:
                reason = self.policy["answer_modes"]["strong_with_auxiliary"]["default_user_message"]
            else:
                reason = self.policy["answer_modes"]["strong"]["default_user_message"]
            return {
                "mode": "strong",
                "mode_reason": reason,
                "runtime_risk_flags": [],
            }

        if secondary or risk:
            runtime_risk_flags = list(
                self.policy["answer_modes"]["weak_with_review_notice"]["must_add_risk_labels"]
            )
            for entry in secondary + risk:
                runtime_risk_flags.extend(entry["risk_flag"])
            return {
                "mode": "weak_with_review_notice",
                "mode_reason": self.policy["answer_modes"]["weak_with_review_notice"]["default_user_message"],
                "runtime_risk_flags": unique_preserve_order(runtime_risk_flags),
            }

        return {
            "mode": "refuse",
            "mode_reason": self.policy["answer_modes"]["refuse"]["default_user_message"],
            "runtime_risk_flags": [],
        }


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
            if isinstance(value, (dict, list)):
                values.append(json.dumps(value, ensure_ascii=False))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_examples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
    }


def build_precision_patch_section(before_result: dict[str, Any], after_result: dict[str, Any]) -> list[str]:
    before_primary_ids = [row["record_id"] for row in before_result["primary_evidence"]]
    after_primary_ids = [row["record_id"] for row in after_result["primary_evidence"]]
    removed_ids = [record_id for record_id in before_primary_ids if record_id not in after_primary_ids]
    added_ids = [record_id for record_id in after_primary_ids if record_id not in before_primary_ids]

    lines = [
        "## Strong Precision Patch",
        "",
        f"- query: `{after_result['query_request']['query_text']}`",
        f"- before_profile: `{before_result['query_request']['precision_profile']}`",
        f"- after_profile: `{after_result['query_request']['precision_profile']}`",
        "",
        "### Primary Evidence Before Tight Filter",
        "",
        markdown_table(
            [
                {
                    "record_id": row["record_id"],
                    "chapter_id": row["chapter_id"],
                    "topic_consistency": row["topic_consistency"],
                    "text_preview": row["text_preview"],
                }
                for row in before_result["primary_evidence"]
            ]
        ),
        "",
        "### Primary Evidence After Tight Filter",
        "",
        markdown_table(
            [
                {
                    "record_id": row["record_id"],
                    "chapter_id": row["chapter_id"],
                    "topic_consistency": row["topic_consistency"],
                    "text_preview": row["text_preview"],
                }
                for row in after_result["primary_evidence"]
            ]
        ),
        "",
        "### Primary Evidence Diff",
        "",
        f"- removed_from_primary: `{json.dumps(removed_ids, ensure_ascii=False)}`",
        f"- added_to_primary: `{json.dumps(added_ids, ensure_ascii=False)}`",
    ]
    return lines


def build_smoke_markdown(
    command: str,
    results: list[dict[str, Any]],
    precision_patch: dict[str, dict[str, Any]] | None = None,
) -> str:
    lines = [
        "# Retrieval Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 结论",
        "",
    ]

    for result in results:
        lines.append(
            f"- `{result['example_id']}`: mode=`{result['mode']}`, "
            f"primary={len(result['primary_evidence'])}, "
            f"secondary={len(result['secondary_evidence'])}, "
            f"risk={len(result['risk_materials'])}, "
            f"chunk_hits={len(result['retrieval_trace']['chunk_hits'])}"
        )

    if precision_patch:
        lines.extend(
            [
                "",
                *build_precision_patch_section(
                    precision_patch["before_strong_result"],
                    precision_patch["after_strong_result"],
                ),
            ]
        )

    for result in results:
        lines.extend(
            [
                "",
                f"## Example: {result['example_id']}",
                "",
                f"- query: `{result['query_request']['query_text']}`",
                f"- mode: `{result['mode']}`",
                f"- mode_reason: {result['mode_reason']}",
                f"- runtime_risk_flags: `{json.dumps(result['runtime_risk_flags'], ensure_ascii=False)}`",
                "",
                "### Raw Candidates",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "evidence_level": row["evidence_level"],
                            "combined_score": row["combined_score"],
                            "matched_terms": json.dumps(row["matched_terms"], ensure_ascii=False),
                            "topic_consistency": row["topic_consistency"],
                            "backref_target_type": row["backref_target_type"],
                        }
                        for row in result["raw_candidates"][:6]
                    ]
                ),
                "",
                "### Primary Evidence",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "combined_score": row["combined_score"],
                            "topic_consistency": row["topic_consistency"],
                            "retrieval_paths": json.dumps(row["retrieval_paths"], ensure_ascii=False),
                        }
                        for row in result["primary_evidence"]
                    ]
                ),
                "",
                "### Secondary Evidence",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "combined_score": row["combined_score"],
                            "topic_consistency": row["topic_consistency"],
                            "risk_flag": json.dumps(row["risk_flag"], ensure_ascii=False),
                        }
                        for row in result["secondary_evidence"]
                    ]
                ),
                "",
                "### Risk Materials",
                "",
                markdown_table(
                    [
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "combined_score": row["combined_score"],
                            "risk_flag": json.dumps(row["risk_flag"], ensure_ascii=False),
                        }
                        for row in result["risk_materials"]
                    ]
                ),
                "",
                "### Chunk Hits",
                "",
                markdown_table(
                    [
                        {
                            "chunk_record_id": row["chunk_record_id"],
                            "chunk_score": row["chunk_score"],
                            "topic_consistency": row["topic_consistency"],
                            "linked_main_passages": json.dumps(row["linked_main_passages"], ensure_ascii=False),
                        }
                        for row in result["retrieval_trace"]["chunk_hits"]
                    ]
                ),
            ]
        )

    return "\n".join(lines) + "\n"


def run_examples(engine: RetrievalEngine) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        result = engine.retrieve(example["query_text"])
        result["example_id"] = example["example_id"]
        result["expected_mode"] = example["expected_mode"]
        results.append(result)
    return results


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    mode_counts = Counter(result["mode"] for result in results)
    if mode_counts["strong"] < 1:
        raise AssertionError("expected at least one strong example")
    if mode_counts["weak_with_review_notice"] < 1:
        raise AssertionError("expected at least one weak_with_review_notice example")
    if mode_counts["refuse"] < 1:
        raise AssertionError("expected at least one refuse example")

    if not any(result["retrieval_trace"]["chunk_hits"] for result in results):
        raise AssertionError("expected at least one example with chunk backrefs")

    if any(result["annotation_links_enabled"] for result in results):
        raise AssertionError("annotation_links should remain disabled")

    for result in results:
        if result["mode"] == "strong" and not result["primary_evidence"]:
            raise AssertionError("strong result missing primary_evidence")
        if result["mode"] == "weak_with_review_notice" and result["primary_evidence"]:
            raise AssertionError("weak_with_review_notice must not include primary_evidence")

    strong_result = next((result for result in results if result["example_id"] == "strong_chunk_backref"), None)
    if not strong_result:
        raise AssertionError("missing strong_chunk_backref example")
    if any("葛根黄芩黄连汤方" in row["text_preview"] or "ZJSHL-CH-009" in row["chapter_id"] for row in strong_result["primary_evidence"]):
        raise AssertionError("strong_chunk_backref primary_evidence still contains expanded formula matches")

    weak_result = next((result for result in results if result["example_id"] == "weak_with_review_notice"), None)
    if not weak_result or weak_result["mode"] != "weak_with_review_notice":
        raise AssertionError("weak_with_review_notice example regressed")

    refuse_result = next((result for result in results if result["example_id"] == "refuse_no_match"), None)
    if not refuse_result or refuse_result["mode"] != "refuse":
        raise AssertionError("refuse example regressed")


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    examples_out = resolve_project_path(args.examples_out)
    smoke_out = resolve_project_path(args.smoke_checks_out)

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)

    engine = RetrievalEngine(db_path=db_path, policy_path=policy_path, candidate_limit=args.candidate_limit)
    try:
        log(f"[1/4] Loaded policy from {policy_path}")
        log(f"[2/4] Loaded retrieval database from {db_path} with {len(engine.unified_rows)} unified rows")

        if args.query:
            result = engine.retrieve(args.query)
            print(json_dumps(result))
            log("[3/4] Ran single-query retrieval")
            log("[4/4] No artifact files updated in single-query mode")
            return 0

        results = run_examples(engine)
        assert_smoke_expectations(results)
        strong_example = next(example for example in DEFAULT_EXAMPLES if example["example_id"] == "strong_chunk_backref")
        precision_patch = {
            "before_strong_result": engine.retrieve(strong_example["query_text"], tight_primary_precision=False),
            "after_strong_result": next(result for result in results if result["example_id"] == "strong_chunk_backref"),
        }
        examples_payload = build_examples_payload(results)
        examples_out.write_text(json_dumps(examples_payload) + "\n", encoding="utf-8")

        command = f"{Path(sys.executable).name} " + " ".join(sys.argv)
        smoke_out.write_text(build_smoke_markdown(command, results, precision_patch=precision_patch), encoding="utf-8")
        log("[3/4] Ran default retrieval examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
