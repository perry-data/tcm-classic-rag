#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
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


RUN_ID = "cross_batch_ahv_consistency_audit_v1"
AHV_V1_LAYER = "ambiguous_high_value_batch_safe_primary"
AHV2_LAYER = "ambiguous_high_value_evidence_upgrade_v2_safe_primary"
AHV_SAFE_LAYERS = (AHV_V1_LAYER, AHV2_LAYER)
AHV_SUPPORT_LAYERS = (
    "ambiguous_high_value_batch_support_only",
    "ambiguous_high_value_evidence_upgrade_v2_support_only",
)

DEFAULT_OUTPUT_DIR = "artifacts/data_plane_cross_batch"
DEFAULT_DOC_DIR = "docs/data_plane_cross_batch"
DEFAULT_INVENTORY_JSON = f"{DEFAULT_OUTPUT_DIR}/cross_batch_ahv_object_inventory_v1.json"
DEFAULT_INVENTORY_MD = f"{DEFAULT_OUTPUT_DIR}/cross_batch_ahv_object_inventory_v1.md"
DEFAULT_LEDGER_JSON = f"{DEFAULT_OUTPUT_DIR}/cross_batch_consistency_ledger_v1.json"
DEFAULT_LEDGER_MD = f"{DEFAULT_OUTPUT_DIR}/cross_batch_consistency_ledger_v1.md"
DEFAULT_AUDIT_DOC = f"{DEFAULT_DOC_DIR}/cross_batch_ahv_consistency_audit_v1.md"
DEFAULT_POLICY_DOC = f"{DEFAULT_DOC_DIR}/cross_batch_consistency_policy_v1.md"

FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}

CONCEPT_GROUPS = {
    "convulsion_terms": ("痓病", "刚痓", "柔痓"),
    "pulse_terms": ("结脉", "促脉", "数脉", "滑脉", "弦脉", "革脉", "毛脉", "纯弦脉"),
    "six_channel_outline_terms": ("太阳病", "阳明病", "太阴病", "少阴病", "厥阴病"),
    "seasonal_disease_terms": ("伤寒", "温病", "暑病", "冬温", "时行寒疫"),
    "post_recovery_terms": ("劳复", "食复", "过经"),
    "chest_and_location_terms": ("结胸", "水结胸", "半表半里证", "水逆"),
}

EXPECTED_PRIMARY_TYPE_BY_CONCEPT_TYPE = {
    "six_channel_disease_term": "exact_term_definition",
    "pulse_pattern_term": "exact_term_definition",
    "pulse_qi_state_term": "exact_term_definition",
    "pulse_pathology_term": "exact_term_definition",
    "qi_blood_state_term": "exact_term_definition",
    "disease_state_term": "exact_term_definition",
    "disease_person_state_term": "exact_term_definition",
    "disease_location_term": "exact_term_definition",
    "disease_course_term": "exact_term_definition",
    "seasonal_disease_term": "exact_term_definition",
    "post_recovery_term": "exact_term_definition",
    "pathogen_category_term": "exact_term_definition",
}

CROSS_BATCH_SCOPE_BY_CONCEPT_TYPE = {
    "six_channel_disease_term": "channel_disease_outline",
    "pulse_pattern_term": "pulse_pattern_definition",
    "pulse_qi_state_term": "pulse_state_definition",
    "pulse_pathology_term": "pulse_pathology_definition",
    "qi_blood_state_term": "body_state_definition",
    "disease_state_term": "named_condition_definition",
    "disease_person_state_term": "named_condition_definition",
    "disease_location_term": "named_condition_definition",
    "disease_course_term": "named_condition_definition",
    "seasonal_disease_term": "seasonal_disease_definition",
    "post_recovery_term": "post_recovery_definition",
    "pathogen_category_term": "pathogen_category_definition",
}

PRIMARY_TYPE_POLICY_NOTES = {
    "channel_disease_outline": "cross_batch_ahv_consistency_audit_v1: 六经病对象统一标为 channel_disease_outline，仅表示提纲句/总纲句，不代表该篇全部证治。",
    "pulse_pattern_definition": "cross_batch_ahv_consistency_audit_v1: 脉象对象统一标为 pulse_pattern_definition，仅表示命名脉象句或短定义句。",
    "pulse_state_definition": "cross_batch_ahv_consistency_audit_v1: 脉象所见气血状态对象统一标为 pulse_state_definition，限定为原句判断义。",
    "pulse_pathology_definition": "cross_batch_ahv_consistency_audit_v1: 脉病理分类对象统一标为 pulse_pathology_definition，后文解释只作 supporting evidence。",
    "body_state_definition": "cross_batch_ahv_consistency_audit_v1: 气血/身体状态对象统一标为 body_state_definition，限定为原句命名或判断义。",
    "named_condition_definition": "cross_batch_ahv_consistency_audit_v1: 病证/状态对象统一标为 named_condition_definition，不外扩到治疗、病机或整段材料。",
    "seasonal_disease_definition": "cross_batch_ahv_consistency_audit_v1: 时病/外感病名对象统一标为 seasonal_disease_definition，仅保留闭合命名/定义句。",
    "post_recovery_definition": "cross_batch_ahv_consistency_audit_v1: 瘥后复病对象统一标为 post_recovery_definition，劳复、食复、过经互不归一。",
    "pathogen_category_definition": "cross_batch_ahv_consistency_audit_v1: 分类枚举对象统一标为 pathogen_category_definition，只保留自足枚举句。",
}


@dataclass(frozen=True)
class ObjectRow:
    concept_id: str
    canonical_term: str
    concept_type: str
    source_confidence: str
    primary_evidence_type: str
    promotion_state: str
    promotion_source_layer: str
    primary_source_table: str
    primary_source_evidence_level: str
    is_safe_primary_candidate: int
    is_active: int
    primary_support_passage_id: str
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit AHV v1 + AHV2 safe primary consistency.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--inventory-json", default=DEFAULT_INVENTORY_JSON)
    parser.add_argument("--inventory-md", default=DEFAULT_INVENTORY_MD)
    parser.add_argument("--ledger-json", default=DEFAULT_LEDGER_JSON)
    parser.add_argument("--ledger-md", default=DEFAULT_LEDGER_MD)
    parser.add_argument("--audit-doc", default=DEFAULT_AUDIT_DOC)
    parser.add_argument("--policy-doc", default=DEFAULT_POLICY_DOC)
    parser.add_argument("--skip-runtime-probes", action="store_true")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_text(text: str | None) -> str:
    if not text:
        return ""
    import re

    return re.sub(r"[^\w\u4e00-\u9fff]+", "", str(text).lower())


def json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    try:
        loaded = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    if isinstance(loaded, list):
        return [str(item) for item in loaded if item]
    return []


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def table_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params)]


def expected_primary_evidence_type(row: dict[str, Any]) -> str:
    concept_type = str(row.get("concept_type") or "")
    try:
        return EXPECTED_PRIMARY_TYPE_BY_CONCEPT_TYPE[concept_type]
    except KeyError as exc:
        raise ValueError(f"Unhandled concept_type for cross-batch AHV policy: {concept_type}") from exc


def expected_primary_type_note(row: dict[str, Any]) -> str:
    scope_type = CROSS_BATCH_SCOPE_BY_CONCEPT_TYPE[str(row.get("concept_type") or "")]
    return PRIMARY_TYPE_POLICY_NOTES[scope_type]


def load_safe_objects(conn: sqlite3.Connection) -> list[dict[str, Any]]:
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


def load_alias_rows(conn: sqlite3.Connection, concept_ids: list[str]) -> list[dict[str, Any]]:
    if not concept_ids:
        return []
    placeholders = ",".join("?" for _ in concept_ids)
    return table_rows(
        conn,
        f"""
        SELECT *
        FROM term_alias_registry
        WHERE concept_id IN ({placeholders})
        ORDER BY canonical_term, alias, alias_id
        """,
        tuple(concept_ids),
    )


def load_learner_rows(conn: sqlite3.Connection, concept_ids: list[str]) -> list[dict[str, Any]]:
    if not concept_ids:
        return []
    placeholders = ",".join("?" for _ in concept_ids)
    return table_rows(
        conn,
        f"""
        SELECT *
        FROM learner_query_normalization_lexicon
        WHERE target_id IN ({placeholders})
        ORDER BY target_term, surface_form, lexicon_id
        """,
        tuple(concept_ids),
    )


def load_review_boundary_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    layers = (*AHV_SUPPORT_LAYERS, "promoted_from_full_risk_layer")
    placeholders = ",".join("?" for _ in layers)
    return table_rows(
        conn,
        f"""
        SELECT *
        FROM definition_term_registry
        WHERE promotion_state != 'safe_primary'
           OR is_safe_primary_candidate = 0
           OR promotion_source_layer IN ({placeholders})
        ORDER BY promotion_source_layer, canonical_term
        """,
        layers,
    )


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
        if (
            item.get("record_type") in FORBIDDEN_PRIMARY_TYPES
            or record_id.startswith("full:passages:")
            or record_id.startswith("full:ambiguous_passages:")
        ):
            forbidden.append({"record_id": item.get("record_id"), "record_type": item.get("record_type")})
    return forbidden


def run_inactive_alias_primary_backdoor_probe(
    db_path: Path,
    inactive_alias_rows: list[dict[str, Any]],
    ahv_concept_ids: set[str],
) -> dict[str, Any]:
    probe_aliases = []
    seen: set[tuple[str, str]] = set()
    for row in inactive_alias_rows:
        alias = str(row.get("alias") or "").strip()
        if not alias:
            continue
        key = (str(row.get("concept_id") or ""), compact_text(alias))
        if key in seen:
            continue
        seen.add(key)
        probe_aliases.append(row)

    backdoor_hits: list[dict[str, Any]] = []
    assembler = make_assembler(db_path)
    try:
        for row in probe_aliases:
            query = f"{row['alias']}是什么意思"
            retrieval = assembler.engine.retrieve(query)
            payload = assembler.assemble(query)
            term_normalization = retrieval.get("query_request", {}).get("term_normalization") or {}
            matched_ahv_ids = [
                concept_id
                for concept_id in (term_normalization.get("concept_ids") or [])
                if str(concept_id) in ahv_concept_ids
            ]
            primary_ids = [str(item.get("record_id") or "") for item in payload.get("primary_evidence") or []]
            primary_ahv_ids = [
                record_id.rsplit(":", 1)[-1]
                for record_id in primary_ids
                if record_id.startswith("safe:definition_terms:")
                and record_id.rsplit(":", 1)[-1] in ahv_concept_ids
            ]
            if matched_ahv_ids or primary_ahv_ids:
                backdoor_hits.append(
                    {
                        "alias": row.get("alias"),
                        "canonical_term": row.get("canonical_term"),
                        "concept_id": row.get("concept_id"),
                        "query": query,
                        "matched_ahv_ids": matched_ahv_ids,
                        "primary_ahv_ids": primary_ahv_ids,
                        "primary_ids": primary_ids,
                        "forbidden_primary_items": primary_forbidden_items(payload),
                    }
                )
    finally:
        assembler.close()
    return {
        "probe_count": len(probe_aliases),
        "inactive_alias_primary_backdoor_count": len(backdoor_hits),
        "backdoor_hits": backdoor_hits,
    }


def build_inventory_payload(
    *,
    db_path: Path,
    safe_objects: list[dict[str, Any]],
    alias_rows: list[dict[str, Any]],
    learner_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    aliases_by_concept: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in alias_rows:
        aliases_by_concept[str(row["concept_id"])].append(row)

    learners_by_concept: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in learner_rows:
        learners_by_concept[str(row["target_id"])].append(row)

    objects: list[dict[str, Any]] = []
    for row in safe_objects:
        item = {
            key: row.get(key)
            for key in (
                "concept_id",
                "canonical_term",
                "normalized_term",
                "concept_type",
                "primary_support_passage_id",
                "primary_source_table",
                "primary_source_evidence_level",
                "source_confidence",
                "primary_evidence_type",
                "promotion_state",
                "promotion_source_layer",
                "promotion_reason",
                "review_only_reason",
                "notes",
                "is_safe_primary_candidate",
                "is_active",
            )
        }
        item["expected_primary_evidence_type"] = expected_primary_evidence_type(row)
        item["cross_batch_scope_type"] = CROSS_BATCH_SCOPE_BY_CONCEPT_TYPE[str(row.get("concept_type") or "")]
        item["primary_type_policy_note"] = expected_primary_type_note(row)
        item["query_aliases"] = json_list(row.get("query_aliases_json"))
        item["learner_surface_forms"] = json_list(row.get("learner_surface_forms_json"))
        item["source_passage_ids"] = json_list(row.get("source_passage_ids_json"))
        item["aliases"] = aliases_by_concept.get(str(row["concept_id"]), [])
        item["learner_normalization"] = learners_by_concept.get(str(row["concept_id"]), [])
        objects.append(item)

    layer_counts = Counter(row["promotion_source_layer"] for row in safe_objects)
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "db_path": str(db_path),
        "audited_object_count": len(safe_objects),
        "ahv_v1_object_count": layer_counts.get(AHV_V1_LAYER, 0),
        "ahv2_object_count": layer_counts.get(AHV2_LAYER, 0),
        "layers": {
            "ahv_v1": AHV_V1_LAYER,
            "ahv2": AHV2_LAYER,
        },
        "objects": objects,
    }


def concept_group_findings(safe_objects: list[dict[str, Any]], alias_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    term_to_rows = {row["canonical_term"]: row for row in safe_objects}
    active_alias_targets: dict[str, set[str]] = defaultdict(set)
    inactive_aliases: dict[str, list[str]] = defaultdict(list)
    for row in alias_rows:
        normalized = compact_text(row.get("normalized_alias") or row.get("alias"))
        if not normalized:
            continue
        if int(row.get("is_active") or 0):
            active_alias_targets[normalized].add(str(row["canonical_term"]))
        else:
            inactive_aliases[str(row["canonical_term"])].append(str(row.get("alias") or ""))

    findings: list[dict[str, Any]] = []
    for group_id, terms in CONCEPT_GROUPS.items():
        present_terms = [term for term in terms if term in term_to_rows]
        missing_terms = [term for term in terms if term not in term_to_rows]
        active_conflicts = [
            {"alias": alias, "terms": sorted(targets)}
            for alias, targets in sorted(active_alias_targets.items())
            if len(targets) > 1 and any(term in targets for term in present_terms)
        ]
        conclusion = "no_cross_batch_conflict"
        rationale = "对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。"
        if active_conflicts:
            conclusion = "conflict"
            rationale = "存在 active alias 指向多个概念。"
        findings.append(
            {
                "group_id": group_id,
                "requested_terms": list(terms),
                "present_terms": present_terms,
                "missing_terms": missing_terms,
                "active_alias_conflicts": active_conflicts,
                "inactive_aliases_by_term": {term: inactive_aliases.get(term, []) for term in present_terms},
                "conclusion": conclusion,
                "rationale": rationale,
            }
        )
    return findings


def build_consistency_ledger(
    *,
    db_path: Path,
    safe_objects: list[dict[str, Any]],
    alias_rows: list[dict[str, Any]],
    learner_rows: list[dict[str, Any]],
    review_boundary_rows: list[dict[str, Any]],
    runtime_probes: dict[str, Any],
) -> dict[str, Any]:
    concept_ids = {str(row["concept_id"]) for row in safe_objects}
    layer_counts = Counter(row["promotion_source_layer"] for row in safe_objects)
    canonical_counts = Counter(compact_text(row["canonical_term"]) for row in safe_objects)
    duplicate_terms = [
        {
            "normalized_term": normalized,
            "objects": [
                {
                    "concept_id": row["concept_id"],
                    "canonical_term": row["canonical_term"],
                    "promotion_source_layer": row["promotion_source_layer"],
                }
                for row in safe_objects
                if compact_text(row["canonical_term"]) == normalized
            ],
        }
        for normalized, count in canonical_counts.items()
        if count > 1
    ]

    active_learner_rows = [row for row in learner_rows if int(row.get("is_active") or 0)]
    active_alias_rows = [row for row in alias_rows if int(row.get("is_active") or 0)]
    active_contains = [
        row
        for row in active_learner_rows
        if str(row.get("entry_type") or "") == "term_surface" and str(row.get("match_mode") or "") != "exact"
    ]
    active_single_char_aliases = [
        row
        for row in active_alias_rows
        if len(compact_text(row.get("normalized_alias") or row.get("alias"))) == 1
    ]
    active_single_char_learner = [
        row
        for row in active_learner_rows
        if str(row.get("entry_type") or "") == "term_surface"
        and len(compact_text(row.get("normalized_surface_form") or row.get("surface_form"))) == 1
    ]

    active_alias_targets: dict[str, set[str]] = defaultdict(set)
    for row in active_alias_rows:
        active_alias_targets[compact_text(row.get("normalized_alias") or row.get("alias"))].add(str(row["concept_id"]))
    for row in active_learner_rows:
        if str(row.get("entry_type") or "") == "term_surface":
            active_alias_targets[compact_text(row.get("normalized_surface_form") or row.get("surface_form"))].add(
                str(row["target_id"])
            )
    duplicate_active_aliases = [
        {"normalized_alias": alias, "concept_ids": sorted(targets)}
        for alias, targets in sorted(active_alias_targets.items())
        if alias and len(targets) > 1
    ]

    review_ids = {str(row["concept_id"]) for row in review_boundary_rows}
    review_only_learner_safe_conflicts = [
        row
        for row in active_learner_rows
        if str(row.get("target_id") or "") in review_ids
        or (
            str(row.get("entry_type") or "") == "term_surface"
            and str(row.get("target_id") or "") not in concept_ids
            and str(row.get("target_type") or "") == "definition_term"
        )
    ]
    review_only_active_alias_conflicts = [
        row
        for row in table_review_alias_conflicts(alias_rows=[], review_boundary_rows=[])
    ]

    confidence_inconsistencies = [
        {
            "concept_id": row["concept_id"],
            "canonical_term": row["canonical_term"],
            "source_confidence": row["source_confidence"],
            "expected_source_confidence": "medium",
            "reason": "AHV v1/v2 safe primary from full/risk/ambiguous or batch safe main extraction remains medium.",
        }
        for row in safe_objects
        if row.get("source_confidence") != "medium"
    ]
    evidence_type_inconsistencies = [
        {
            "concept_id": row["concept_id"],
            "canonical_term": row["canonical_term"],
            "concept_type": row["concept_type"],
            "primary_evidence_type": row["primary_evidence_type"],
            "expected_primary_evidence_type": expected_primary_evidence_type(row),
        }
        for row in safe_objects
        if row.get("primary_evidence_type") != expected_primary_evidence_type(row)
    ]

    group_findings = concept_group_findings(safe_objects, alias_rows)
    duplicate_concept_count = len(duplicate_terms) + sum(
        1 for finding in group_findings if finding["conclusion"] == "conflict"
    )

    metrics = {
        "audited_object_count": len(safe_objects),
        "ahv_v1_object_count": layer_counts.get(AHV_V1_LAYER, 0),
        "ahv2_object_count": layer_counts.get(AHV2_LAYER, 0),
        "duplicate_concept_count": duplicate_concept_count,
        "active_contains_count": len(active_contains),
        "active_single_char_alias_count": len(active_single_char_aliases) + len(active_single_char_learner),
        "duplicate_active_alias_count": len(duplicate_active_aliases),
        "inactive_alias_primary_backdoor_count": runtime_probes.get("inactive_alias_primary_backdoor_count", 0),
        "review_only_learner_safe_conflict_count": len(review_only_learner_safe_conflicts)
        + len(review_only_active_alias_conflicts),
        "confidence_consistent_count": len(safe_objects) - len(confidence_inconsistencies),
        "confidence_inconsistent_count": len(confidence_inconsistencies),
        "evidence_type_consistent_count": len(safe_objects) - len(evidence_type_inconsistencies),
        "evidence_type_inconsistent_count": len(evidence_type_inconsistencies),
    }
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "db_path": str(db_path),
        "layers": {"ahv_v1": AHV_V1_LAYER, "ahv2": AHV2_LAYER},
        "metrics": metrics,
        "duplicate_terms": duplicate_terms,
        "concept_group_findings": group_findings,
        "confidence_inconsistencies": confidence_inconsistencies,
        "evidence_type_inconsistencies": evidence_type_inconsistencies,
        "alias_findings": {
            "active_contains": active_contains,
            "active_single_char_aliases": active_single_char_aliases,
            "active_single_char_learner_surfaces": active_single_char_learner,
            "duplicate_active_aliases": duplicate_active_aliases,
            "inactive_alias_runtime_probe": runtime_probes,
            "review_only_learner_safe_conflicts": review_only_learner_safe_conflicts,
            "review_only_active_alias_conflicts": review_only_active_alias_conflicts,
        },
    }


def table_review_alias_conflicts(
    *, alias_rows: list[dict[str, Any]], review_boundary_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return []


def load_review_only_active_alias_conflicts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return table_rows(
        conn,
        """
        SELECT a.*, d.promotion_state, d.promotion_source_layer, d.is_safe_primary_candidate
        FROM term_alias_registry AS a
        JOIN definition_term_registry AS d
          ON d.concept_id = a.concept_id
        WHERE a.is_active = 1
          AND (
              d.promotion_state != 'safe_primary'
              OR d.is_safe_primary_candidate = 0
              OR a.alias_type IN ('review_only_support', 'learner_risky', 'ambiguous')
          )
        ORDER BY d.promotion_source_layer, a.canonical_term, a.alias
        """,
    )


def load_review_only_active_learner_conflicts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return table_rows(
        conn,
        """
        SELECT l.*, d.promotion_state, d.promotion_source_layer, d.is_safe_primary_candidate
        FROM learner_query_normalization_lexicon AS l
        JOIN definition_term_registry AS d
          ON d.concept_id = l.target_id
        WHERE l.is_active = 1
          AND l.entry_type = 'term_surface'
          AND (
              d.promotion_state != 'safe_primary'
              OR d.is_safe_primary_candidate = 0
          )
        ORDER BY d.promotion_source_layer, l.target_term, l.surface_form
        """,
    )


def inventory_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Cross-Batch AHV Object Inventory v1",
        "",
        f"- audited_object_count: `{payload['audited_object_count']}`",
        f"- ahv_v1_object_count: `{payload['ahv_v1_object_count']}`",
        f"- ahv2_object_count: `{payload['ahv2_object_count']}`",
        "",
        "| batch | canonical_term | concept_type | source_confidence | primary_evidence_type | scope_type | primary_source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["objects"]:
        batch = "AHV v1" if row["promotion_source_layer"] == AHV_V1_LAYER else "AHV2"
        lines.append(
            "| "
            + " | ".join(
                [
                    batch,
                    row["canonical_term"],
                    row["concept_type"],
                    row["source_confidence"],
                    row["primary_evidence_type"],
                    row["cross_batch_scope_type"],
                    f"{row['primary_source_table']}:{row['primary_support_passage_id']}",
                ]
            )
            + " |"
        )
    return lines


def ledger_md(payload: dict[str, Any]) -> list[str]:
    metrics = payload["metrics"]
    lines = [
        "# Cross-Batch AHV Consistency Ledger v1",
        "",
        f"- audited_object_count: `{metrics['audited_object_count']}`",
        f"- ahv_v1_object_count: `{metrics['ahv_v1_object_count']}`",
        f"- ahv2_object_count: `{metrics['ahv2_object_count']}`",
        f"- duplicate_concept_count: `{metrics['duplicate_concept_count']}`",
        f"- active_contains_count: `{metrics['active_contains_count']}`",
        f"- active_single_char_alias_count: `{metrics['active_single_char_alias_count']}`",
        f"- duplicate_active_alias_count: `{metrics['duplicate_active_alias_count']}`",
        f"- inactive_alias_primary_backdoor_count: `{metrics['inactive_alias_primary_backdoor_count']}`",
        f"- review_only_learner_safe_conflict_count: `{metrics['review_only_learner_safe_conflict_count']}`",
        f"- confidence_consistent_count: `{metrics['confidence_consistent_count']}`",
        f"- confidence_inconsistent_count: `{metrics['confidence_inconsistent_count']}`",
        f"- evidence_type_consistent_count: `{metrics['evidence_type_consistent_count']}`",
        f"- evidence_type_inconsistent_count: `{metrics['evidence_type_inconsistent_count']}`",
        "",
        "## Concept Groups",
        "",
        "| group | present_terms | missing_terms | conclusion | rationale |",
        "| --- | --- | --- | --- | --- |",
    ]
    for finding in payload["concept_group_findings"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    finding["group_id"],
                    ", ".join(finding["present_terms"]) or "-",
                    ", ".join(finding["missing_terms"]) or "-",
                    finding["conclusion"],
                    finding["rationale"],
                ]
            )
            + " |"
        )
    lines.extend(["", "## Evidence Type Inconsistencies", ""])
    if payload["evidence_type_inconsistencies"]:
        lines.extend(
            [
                "| canonical_term | concept_type | current | expected |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in payload["evidence_type_inconsistencies"]:
            lines.append(
                f"| {row['canonical_term']} | {row['concept_type']} | {row['primary_evidence_type']} | {row['expected_primary_evidence_type']} |"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Confidence Inconsistencies", ""])
    if payload["confidence_inconsistencies"]:
        lines.extend(["| canonical_term | current | expected |", "| --- | --- | --- |"])
        for row in payload["confidence_inconsistencies"]:
            lines.append(f"| {row['canonical_term']} | {row['source_confidence']} | {row['expected_source_confidence']} |")
    else:
        lines.append("- none")
    return lines


def audit_doc_md(ledger: dict[str, Any]) -> list[str]:
    metrics = ledger["metrics"]
    return [
        "# Cross-Batch AHV Consistency Audit v1",
        "",
        "本轮审计只覆盖 AHV v1 与 AHV2 已存在的 safe primary definition/concept objects，不新增 AHV3 对象，不改 prompt、前端、API payload、answer_mode 或 commentarial 主逻辑。",
        "",
        "## Scope",
        "",
        f"- AHV v1 layer: `{AHV_V1_LAYER}`",
        f"- AHV2 layer: `{AHV2_LAYER}`",
        f"- audited_object_count: `{metrics['audited_object_count']}`",
        "",
        "## Summary",
        "",
        f"- duplicate_concept_count: `{metrics['duplicate_concept_count']}`",
        f"- confidence_inconsistent_count: `{metrics['confidence_inconsistent_count']}`",
        f"- evidence_type_inconsistent_count: `{metrics['evidence_type_inconsistent_count']}`",
        f"- active_contains_count: `{metrics['active_contains_count']}`",
        f"- active_single_char_alias_count: `{metrics['active_single_char_alias_count']}`",
        f"- duplicate_active_alias_count: `{metrics['duplicate_active_alias_count']}`",
        f"- inactive_alias_primary_backdoor_count: `{metrics['inactive_alias_primary_backdoor_count']}`",
        "",
        "## Conclusion",
        "",
        "跨批次对象层以 exact learner normalization 为共同边界；review-only/support-only 对象不进入 retrieval_ready_definition_view；raw full/ambiguous 不恢复为 primary。若 ledger 中 evidence_type_inconsistent_count 为 0，则两批对象已经按统一 metadata policy 对齐。",
    ]


def policy_doc_md() -> list[str]:
    lines = [
        "# Cross-Batch AHV Consistency Policy v1",
        "",
        "## Non-Expansion Rule",
        "",
        "- 本 policy 只约束 AHV v1/AHV2 已有 safe primary 对象。",
        "- 不新增第三批对象，不恢复 raw full/ambiguous passage 到 primary。",
        "",
        "## Confidence Rule",
        "",
        "- AHV v1/AHV2 safe primary 统一保留 `source_confidence=medium`。",
        "- support/review-only 对象保持 `source_confidence=review_only`，不得拥有 active learner-safe normalization。",
        "",
        "## Primary Evidence Type Rule",
        "",
        "| concept_type | primary_evidence_type | cross_batch_scope_type | scope |",
        "| --- | --- | --- | --- |",
    ]
    type_rows = sorted(EXPECTED_PRIMARY_TYPE_BY_CONCEPT_TYPE.items())
    for concept_type, evidence_type in type_rows:
        scope_type = CROSS_BATCH_SCOPE_BY_CONCEPT_TYPE[concept_type]
        scope = PRIMARY_TYPE_POLICY_NOTES[scope_type].split(": ", 1)[-1]
        lines.append(f"| {concept_type} | {evidence_type} | {scope_type} | {scope} |")
    lines.extend(
        [
            "",
            "## Alias And Normalization Rule",
            "",
            "- AHV v1/AHV2 active learner term surfaces must use `match_mode=exact`.",
            "- active single-character alias is forbidden.",
            "- active alias pointing to multiple concepts is forbidden.",
            "- inactive risky/ambiguous aliases may stay registered for audit, but must not route into AHV primary.",
            "",
            "## Intent Guard Rule",
            "",
            "- `X 是什么 / X 是什么意思 / 何谓 X` may use the matching AHV definition object.",
            "- treatment, formula, mechanism, source-passage, and comparison questions must not be hijacked by a single AHV definition object.",
        ]
    )
    return lines


def run_audit(
    *,
    db_path: Path,
    inventory_json: Path,
    inventory_md_path: Path,
    ledger_json: Path,
    ledger_md_path: Path,
    audit_doc: Path,
    policy_doc: Path,
    skip_runtime_probes: bool = False,
) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        safe_objects = load_safe_objects(conn)
        concept_ids = [str(row["concept_id"]) for row in safe_objects]
        alias_rows = load_alias_rows(conn, concept_ids)
        learner_rows = load_learner_rows(conn, concept_ids)
        review_boundary_rows = load_review_boundary_rows(conn)
        review_only_active_alias_conflicts = load_review_only_active_alias_conflicts(conn)
        review_only_active_learner_conflicts = load_review_only_active_learner_conflicts(conn)
    finally:
        conn.close()

    inactive_alias_rows = [row for row in alias_rows if not int(row.get("is_active") or 0)]
    runtime_probes = (
        {"probe_count": 0, "inactive_alias_primary_backdoor_count": 0, "backdoor_hits": []}
        if skip_runtime_probes
        else run_inactive_alias_primary_backdoor_probe(db_path, inactive_alias_rows, set(concept_ids))
    )

    inventory = build_inventory_payload(
        db_path=db_path,
        safe_objects=safe_objects,
        alias_rows=alias_rows,
        learner_rows=learner_rows,
    )
    ledger = build_consistency_ledger(
        db_path=db_path,
        safe_objects=safe_objects,
        alias_rows=alias_rows,
        learner_rows=learner_rows,
        review_boundary_rows=review_boundary_rows,
        runtime_probes=runtime_probes,
    )
    ledger["alias_findings"]["review_only_active_alias_conflicts"] = review_only_active_alias_conflicts
    ledger["alias_findings"]["review_only_active_learner_conflicts"] = review_only_active_learner_conflicts
    ledger["metrics"]["review_only_learner_safe_conflict_count"] += len(review_only_active_alias_conflicts) + len(
        review_only_active_learner_conflicts
    )

    write_json(inventory_json, inventory)
    write_md(inventory_md_path, inventory_md(inventory))
    write_json(ledger_json, ledger)
    write_md(ledger_md_path, ledger_md(ledger))
    write_md(audit_doc, audit_doc_md(ledger))
    write_md(policy_doc, policy_doc_md())
    return {"inventory": inventory, "ledger": ledger}


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    result = run_audit(
        db_path=db_path,
        inventory_json=resolve_project_path(args.inventory_json),
        inventory_md_path=resolve_project_path(args.inventory_md),
        ledger_json=resolve_project_path(args.ledger_json),
        ledger_md_path=resolve_project_path(args.ledger_md),
        audit_doc=resolve_project_path(args.audit_doc),
        policy_doc=resolve_project_path(args.policy_doc),
        skip_runtime_probes=args.skip_runtime_probes,
    )
    print(json.dumps(result["ledger"]["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
