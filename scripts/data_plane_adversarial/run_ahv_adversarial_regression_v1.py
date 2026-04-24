#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
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


RUN_ID = "ahv_adversarial_regression_v1"
AHV_LAYER = "ambiguous_high_value_batch_safe_primary"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_adversarial"
DEFAULT_OUTPUT_JSON = f"{DEFAULT_OUTPUT_DIR}/ahv_adversarial_regression_after_fix_v1.json"
DEFAULT_OUTPUT_MD = f"{DEFAULT_OUTPUT_DIR}/ahv_adversarial_regression_after_fix_v1.md"
DEFAULT_QUERY_SET_JSON = f"{DEFAULT_OUTPUT_DIR}/ahv_adversarial_query_set_v1.json"
DEFAULT_QUERY_SET_MD = f"{DEFAULT_OUTPUT_DIR}/ahv_adversarial_query_set_v1.md"

FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
AHV_TERMS = (
    "太阳病",
    "伤寒",
    "温病",
    "暑病",
    "冬温",
    "时行寒疫",
    "刚痓",
    "柔痓",
    "痓病",
    "结脉",
    "促脉",
    "弦脉",
    "滑脉",
    "革脉",
    "行尸",
    "内虚",
    "血崩",
    "霍乱",
    "劳复",
    "食复",
)
REVIEW_ONLY_TERMS = {"神丹", "将军", "口苦病", "胆瘅病", "高", "章", "卑", "惵", "损", "纲", "缓", "迟"}


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    query: str
    query_type: str
    expected_behavior: str
    expected_ahv_terms: tuple[str, ...] = ()
    forbidden_ahv_terms: tuple[str, ...] = ()
    require_no_ahv_primary: bool = False
    require_no_ahv_normalization: bool = False
    require_no_definition_primary: bool = False
    require_strong: bool = False
    require_not_strong: bool = False
    require_formula_guard: bool = False
    allow_ahv_normalization_terms: tuple[str, ...] = field(default_factory=tuple)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AHV adversarial regression v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--query-set-json", default=DEFAULT_QUERY_SET_JSON)
    parser.add_argument("--query-set-md", default=DEFAULT_QUERY_SET_MD)
    parser.add_argument("--run-label", default="after_fix")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def normalize_mode(answer_mode: str | None) -> str:
    if answer_mode == "strong":
        return "strong"
    if answer_mode and str(answer_mode).startswith("weak"):
        return "weak"
    return "refuse"


def ahv_record_id(concept_id: str) -> str:
    return f"safe:definition_terms:{concept_id}"


def load_definition_registry(db_path: Path) -> dict[str, dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = {
            str(row["concept_id"]): dict(row)
            for row in conn.execute(
                """
                SELECT concept_id, canonical_term, promotion_state, promotion_source_layer,
                       source_confidence, review_only_reason, is_safe_primary_candidate, is_active
                FROM definition_term_registry
                """
            )
        }
        return rows
    finally:
        conn.close()


def ahv_term_to_id(registry: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {
        row["canonical_term"]: concept_id
        for concept_id, row in registry.items()
        if row.get("promotion_source_layer") == AHV_LAYER
    }


def build_query_specs() -> list[QuerySpec]:
    canonical_queries = (
        ("ahv_canonical_01", "何谓太阳病", "太阳病"),
        ("ahv_canonical_02", "伤寒是什么", "伤寒"),
        ("ahv_canonical_03", "温病是什么意思", "温病"),
        ("ahv_canonical_04", "暑病是什么意思", "暑病"),
        ("ahv_canonical_05", "冬温是什么", "冬温"),
        ("ahv_canonical_06", "时行寒疫是什么", "时行寒疫"),
        ("ahv_canonical_07", "刚痓是什么", "刚痓"),
        ("ahv_canonical_08", "柔痓是什么意思", "柔痓"),
        ("ahv_canonical_09", "痓病是什么", "痓病"),
        ("ahv_canonical_10", "结脉是什么", "结脉"),
        ("ahv_canonical_11", "促脉是什么", "促脉"),
        ("ahv_canonical_12", "弦脉是什么", "弦脉"),
        ("ahv_canonical_13", "滑脉是什么意思", "滑脉"),
        ("ahv_canonical_14", "革脉是什么", "革脉"),
        ("ahv_canonical_15", "行尸是什么意思", "行尸"),
        ("ahv_canonical_16", "内虚是什么意思", "内虚"),
        ("ahv_canonical_17", "血崩是什么", "血崩"),
        ("ahv_canonical_18", "霍乱是什么", "霍乱"),
        ("ahv_canonical_19", "劳复是什么意思", "劳复"),
        ("ahv_canonical_20", "食复是什么意思", "食复"),
    )
    specs: list[QuerySpec] = [
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="ahv_canonical_guard",
            expected_behavior=f"必须命中 {term} 的 AHV safe definition primary，且不得混入其他 AHV primary。",
            expected_ahv_terms=(term,),
            allow_ahv_normalization_terms=(term,),
            require_strong=True,
        )
        for query_id, query, term in canonical_queries
    ]

    similar_queries = (
        ("similar_01", "春温病是什么意思", "春温/温病相近词不得因包含“温病”而命中温病 AHV。"),
        ("similar_02", "寒疫病是什么意思", "寒疫/时行寒疫相近词不得命中时行寒疫 AHV。"),
        ("similar_03", "痉是什么意思", "单字异体痉不得命中刚痓、柔痓或痓病 AHV。"),
        ("similar_04", "痓是什么意思", "单字痓不得命中痓病 AHV。"),
        ("similar_05", "刚痓和柔痓有什么不同", "刚痓/柔痓比较意图不得被单个 AHV definition primary 抢占。"),
        ("similar_06", "柔痓和痓病是一回事吗", "柔痓/痓病关系问法不得被单个 AHV definition primary 抢占。"),
        ("similar_07", "痉病和痓病是同一个词吗", "痉病/痓病关系问法不得被单个 AHV definition primary 抢占。"),
        ("similar_08", "结是什么意思", "单字结不得命中结脉 AHV。"),
        ("similar_09", "结脉和促脉有什么区别", "结脉/促脉比较意图不得被 AHV definition primary 抢占。"),
        ("similar_10", "促是什么意思", "单字促不得命中促脉 AHV。"),
        ("similar_11", "滑脉和革脉有什么不同", "滑脉/革脉比较意图不得被 AHV definition primary 抢占。"),
        ("similar_12", "滑象是什么意思", "滑象不得因字面相近命中滑脉 AHV。"),
        ("similar_13", "革象是什么意思", "革象不得因字面相近命中革脉 AHV。"),
        ("similar_14", "劳复和食复一样吗", "劳复/食复关系问法不得被单个 AHV definition primary 抢占。"),
        ("similar_15", "劳病是什么意思", "劳病不得命中劳复 AHV。"),
        ("similar_16", "食病是什么意思", "食病不得命中食复 AHV。"),
        ("similar_17", "伤寒和温病有什么区别", "伤寒/温病比较意图不得被 AHV definition primary 抢占。"),
        ("similar_18", "伤寒和暑病有什么区别", "伤寒/暑病比较意图不得被 AHV definition primary 抢占。"),
        ("similar_19", "伤寒和冬温有什么区别", "伤寒/冬温比较意图不得被 AHV definition primary 抢占。"),
        ("similar_20", "太阳病和伤寒是一回事吗", "太阳病/伤寒关系问法不得被单个 AHV definition primary 抢占。"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="similar_concept_false_trigger",
            expected_behavior=expected,
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for query_id, query, expected in similar_queries
    )

    disabled_alias_queries = (
        ("disabled_alias_01", "春温是什么意思", "停用 alias 春温不得重新命中温病 AHV。"),
        ("disabled_alias_02", "暑病者是什么意思", "停用 alias 暑病者不得重新命中暑病 AHV。"),
        ("disabled_alias_03", "寒疫是什么意思", "停用 alias 寒疫不得重新命中时行寒疫 AHV。"),
        ("disabled_alias_04", "劳动病是什么", "停用 alias 劳动病不得重新命中劳复 AHV。"),
        ("disabled_alias_05", "强食复病是什么意思", "停用 alias 强食复病不得重新命中食复 AHV。"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="disabled_alias_recheck",
            expected_behavior=expected,
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for query_id, query, expected in disabled_alias_queries
    )

    partial_queries = (
        "太阳是什么意思",
        "寒是什么意思",
        "温是什么意思",
        "暑是什么意思",
        "弦是什么意思",
        "滑是什么意思",
        "革是什么意思",
        "劳是什么意思",
        "食是什么意思",
        "复是什么意思",
    )
    specs.extend(
        QuerySpec(
            query_id=f"partial_word_{index:02d}",
            query=query,
            query_type="partial_word_literal_similarity",
            expected_behavior="单字或普通部分词不得触发 AHV term normalization 或 AHV primary。",
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for index, query in enumerate(partial_queries, start=1)
    )

    non_definition_queries = (
        ("non_definition_01", "太阳病有哪些方？"),
        ("non_definition_02", "伤寒怎么治疗？"),
        ("non_definition_03", "温病与伤寒如何区分？"),
        ("non_definition_04", "霍乱用什么方？"),
        ("non_definition_05", "劳复应该怎么处理？"),
        ("non_definition_06", "食复怎么治？"),
        ("non_definition_07", "结脉有什么方？"),
        ("non_definition_08", "革脉预后如何？"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="non_definition_intent",
            expected_behavior="非 definition/meaning 意图不得被 AHV definition object 抢占 primary；若系统不能正确路由，应记录为 routing/intent 债务。",
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for query_id, query in non_definition_queries
    )

    negative_queries = (
        "太阳能是什么意思",
        "食物中毒是什么意思",
        "劳动合同是什么",
        "皮革是什么",
        "滑雪是什么意思",
        "内虚拟机是什么",
        "霍乱疫苗是什么",
        "暑假是什么",
        "温度是什么意思",
        "复习是什么意思",
    )
    specs.extend(
        QuerySpec(
            query_id=f"negative_{index:02d}",
            query=query,
            query_type="negative_unrelated",
            expected_behavior="明显非中医/非本书术语样本不得命中 AHV primary，不得 AHV normalization，不得错误 strong。",
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
            require_not_strong=True,
        )
        for index, query in enumerate(negative_queries, start=1)
    )

    formula_queries = (
        "桂枝去芍药汤方的条文是什么？",
        "桂枝去芍药加附子汤方的条文是什么？",
        "四逆加人参汤方的条文是什么？",
        "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
        "桂枝去桂加茯苓白术汤方的条文是什么？",
    )
    specs.extend(
        QuerySpec(
            query_id=f"formula_guard_{index:02d}",
            query=query,
            query_type="formula_guard",
            expected_behavior="formula guard 不得出现 bad anchor，且不得被 AHV definition primary 抢占。",
            require_no_ahv_primary=True,
            require_formula_guard=True,
            require_strong=True,
        )
        for index, query in enumerate(formula_queries, start=1)
    )

    gold_queries = (
        "下药是什么意思",
        "四逆是什么意思",
        "盗汗是什么意思",
        "水结胸是什么",
        "坏病是什么",
    )
    specs.extend(
        QuerySpec(
            query_id=f"gold_safe_definition_{index:02d}",
            query=query,
            query_type="gold_safe_definition_guard",
            expected_behavior="既有 gold-safe definition guard 必须保持 strong，且不得被 AHV primary 抢占。",
            require_no_ahv_primary=True,
            require_strong=True,
        )
        for index, query in enumerate(gold_queries, start=1)
    )

    review_queries = (
        "神丹是什么意思",
        "将军是什么意思",
        "口苦病是什么意思",
        "胆瘅病是什么意思",
    )
    specs.extend(
        QuerySpec(
            query_id=f"review_only_boundary_{index:02d}",
            query=query,
            query_type="review_only_boundary_guard",
            expected_behavior="review-only boundary 不得进入 definition primary。",
            require_no_definition_primary=True,
        )
        for index, query in enumerate(review_queries, start=1)
    )
    return specs


def spec_to_artifact(spec: QuerySpec) -> dict[str, Any]:
    return {
        "query_id": spec.query_id,
        "query": spec.query,
        "query_type": spec.query_type,
        "expected_behavior": spec.expected_behavior,
        "expected_ahv_terms": list(spec.expected_ahv_terms),
        "forbidden_ahv_terms": list(spec.forbidden_ahv_terms),
        "require_no_ahv_primary": spec.require_no_ahv_primary,
        "require_no_ahv_normalization": spec.require_no_ahv_normalization,
        "require_no_definition_primary": spec.require_no_definition_primary,
        "require_strong": spec.require_strong,
        "require_not_strong": spec.require_not_strong,
        "require_formula_guard": spec.require_formula_guard,
        "allow_ahv_normalization_terms": list(spec.allow_ahv_normalization_terms),
    }


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


def result_for_spec(
    assembler: AnswerAssembler,
    registry: dict[str, dict[str, Any]],
    ahv_ids_by_term: dict[str, str],
    spec: QuerySpec,
) -> dict[str, Any]:
    expected_ids = {ahv_ids_by_term[term] for term in spec.expected_ahv_terms if term in ahv_ids_by_term}
    allowed_norm_ids = {
        ahv_ids_by_term[term]
        for term in (*spec.expected_ahv_terms, *spec.allow_ahv_normalization_terms)
        if term in ahv_ids_by_term
    }
    ahv_id_to_term = {concept_id: term for term, concept_id in ahv_ids_by_term.items()}
    try:
        retrieval = assembler.engine.retrieve(spec.query)
        payload = assembler.assemble(spec.query)
    except Exception as exc:
        return {
            **spec_to_artifact(spec),
            "actual_answer_mode": "error",
            "mode_bucket": "refuse",
            "term_normalization_enabled": False,
            "matched_concept_ids": [],
            "matched_terms": [],
            "primary_ids": [],
            "primary_record_types": [],
            "is_ahv_primary_hit": False,
            "ahv_primary_terms": [],
            "wrong_ahv_primary_hit": False,
            "wrong_term_normalization": False,
            "forbidden_primary_items": [],
            "review_only_primary_conflict": False,
            "formula_bad_anchor_count": 0,
            "pass": False,
            "fail_reason": f"exception: {type(exc).__name__}: {exc}",
        }

    raw_top = retrieval.get("raw_candidates") or []
    term_normalization = retrieval.get("query_request", {}).get("term_normalization") or {}
    matched_concept_ids = [str(item) for item in term_normalization.get("concept_ids") or []]
    matched_terms = [
        str(match.get("alias") or match.get("canonical_term") or match.get("normalized_alias") or "")
        for match in term_normalization.get("matches") or []
    ]
    primary = payload.get("primary_evidence") or []
    primary_ids = [str(item.get("record_id") or "") for item in primary]
    primary_record_types = [str(item.get("record_type") or "") for item in primary]
    primary_concept_ids = [
        record_id.rsplit(":", 1)[-1]
        for record_id in primary_ids
        if record_id.startswith("safe:definition_terms:")
    ]
    ahv_primary_ids = [concept_id for concept_id in primary_concept_ids if concept_id in ahv_id_to_term]
    ahv_primary_terms = [ahv_id_to_term[concept_id] for concept_id in ahv_primary_ids]
    wrong_ahv_primary_ids = [concept_id for concept_id in ahv_primary_ids if concept_id not in expected_ids]
    if spec.require_no_ahv_primary:
        wrong_ahv_primary_ids = ahv_primary_ids

    ahv_normalized_ids = [concept_id for concept_id in matched_concept_ids if concept_id in ahv_id_to_term]
    wrong_normalized_ids = [concept_id for concept_id in ahv_normalized_ids if concept_id not in allowed_norm_ids]
    wrong_term_normalization = bool(wrong_normalized_ids)
    if spec.require_no_ahv_normalization and ahv_normalized_ids:
        wrong_term_normalization = True

    forbidden_items = primary_forbidden_items(payload)
    review_conflicts: list[dict[str, Any]] = []
    for concept_id in primary_concept_ids:
        row = registry.get(concept_id)
        if not row:
            continue
        if (
            row.get("promotion_state") == "review_only"
            or int(row.get("is_safe_primary_candidate") or 0) == 0
            or row.get("canonical_term") in REVIEW_ONLY_TERMS
        ):
            review_conflicts.append(
                {
                    "concept_id": concept_id,
                    "canonical_term": row.get("canonical_term"),
                    "promotion_state": row.get("promotion_state"),
                }
            )

    formula_bad_anchor_count = sum(
        1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS
    )

    fail_reasons: list[str] = []
    if forbidden_items:
        fail_reasons.append("forbidden primary evidence")
    if spec.expected_ahv_terms:
        missing_terms = [term for term in spec.expected_ahv_terms if ahv_ids_by_term.get(term) not in ahv_primary_ids]
        if missing_terms:
            fail_reasons.append("expected AHV primary missing: " + ",".join(missing_terms))
    if wrong_ahv_primary_ids:
        fail_reasons.append(
            "wrong AHV primary hit: " + ",".join(ahv_id_to_term[concept_id] for concept_id in wrong_ahv_primary_ids)
        )
    if wrong_term_normalization:
        fail_reasons.append(
            "wrong AHV term normalization: "
            + ",".join(ahv_id_to_term[concept_id] for concept_id in wrong_normalized_ids or ahv_normalized_ids)
        )
    if spec.require_no_definition_primary and any(record_type == "definition_terms" for record_type in primary_record_types):
        fail_reasons.append("definition primary present for review-only boundary")
    if review_conflicts:
        fail_reasons.append("review-only definition object entered primary")
    if spec.require_formula_guard and formula_bad_anchor_count:
        fail_reasons.append("formula bad anchor in raw top5")
    if spec.require_strong and normalize_mode(payload.get("answer_mode")) != "strong":
        fail_reasons.append("expected strong answer_mode")
    if spec.require_not_strong and normalize_mode(payload.get("answer_mode")) == "strong":
        fail_reasons.append("unexpected strong answer_mode")

    return {
        **spec_to_artifact(spec),
        "actual_answer_mode": payload.get("answer_mode"),
        "mode_bucket": normalize_mode(payload.get("answer_mode")),
        "term_normalization_enabled": bool(matched_concept_ids),
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "matched_concept_ids": matched_concept_ids,
        "matched_terms": [term for term in matched_terms if term],
        "matched_ahv_terms": [ahv_id_to_term[concept_id] for concept_id in ahv_normalized_ids],
        "primary_ids": primary_ids,
        "primary_record_types": primary_record_types,
        "is_ahv_primary_hit": bool(ahv_primary_ids),
        "ahv_primary_terms": ahv_primary_terms,
        "wrong_ahv_primary_hit": bool(wrong_ahv_primary_ids),
        "wrong_term_normalization": wrong_term_normalization,
        "forbidden_primary_items": forbidden_items,
        "review_only_primary_conflict": bool(review_conflicts),
        "review_only_primary_conflict_items": review_conflicts,
        "formula_bad_anchor_count": formula_bad_anchor_count,
        "definition_primary_count": sum(1 for record_type in primary_record_types if record_type == "definition_terms"),
        "pass": not fail_reasons,
        "fail_reason": "; ".join(fail_reasons),
    }


def summarize(rows: list[dict[str, Any]], run_label: str) -> dict[str, Any]:
    query_type_counts = Counter(row["query_type"] for row in rows)
    fail_rows = [row for row in rows if not row["pass"]]
    canonical_rows = [row for row in rows if row["query_type"] == "ahv_canonical_guard"]
    return {
        "run_label": run_label,
        "total_query_count": len(rows),
        "pass_count": len(rows) - len(fail_rows),
        "fail_count": len(fail_rows),
        "query_type_counts": dict(sorted(query_type_counts.items())),
        "wrong_ahv_primary_hit_count": sum(1 for row in rows if row["wrong_ahv_primary_hit"]),
        "wrong_term_normalization_count": sum(1 for row in rows if row["wrong_term_normalization"]),
        "disabled_alias_still_hit_count": sum(
            1
            for row in rows
            if row["query_type"] == "disabled_alias_recheck"
            and (row["is_ahv_primary_hit"] or row["matched_ahv_terms"])
        ),
        "partial_word_false_positive_count": sum(
            1
            for row in rows
            if row["query_type"] == "partial_word_literal_similarity"
            and (row["is_ahv_primary_hit"] or row["matched_ahv_terms"])
        ),
        "non_definition_intent_hijack_count": sum(
            1
            for row in rows
            if row["query_type"] == "non_definition_intent"
            and (row["is_ahv_primary_hit"] or row["matched_ahv_terms"])
        ),
        "negative_sample_false_positive_count": sum(
            1
            for row in rows
            if row["query_type"] == "negative_unrelated"
            and (row["is_ahv_primary_hit"] or row["matched_ahv_terms"] or row["mode_bucket"] == "strong")
        ),
        "forbidden_primary_total": sum(len(row["forbidden_primary_items"]) for row in rows),
        "review_only_primary_conflict_count": sum(1 for row in rows if row["review_only_primary_conflict"]),
        "formula_bad_anchor_top5_total": sum(
            row["formula_bad_anchor_count"] for row in rows if row["query_type"] == "formula_guard"
        ),
        "ahv_canonical_guard_pass_count": sum(1 for row in canonical_rows if row["pass"]),
        "ahv_canonical_guard_total": len(canonical_rows),
        "failure_query_ids": [row["query_id"] for row in fail_rows],
    }


def write_query_set(paths: tuple[Path, Path], specs: list[QuerySpec]) -> None:
    path_json, path_md = paths
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "query_count": len(specs),
        "query_type_counts": dict(sorted(Counter(spec.query_type for spec in specs).items())),
        "queries": [spec_to_artifact(spec) for spec in specs],
    }
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# AHV Adversarial Query Set v1",
        "",
        f"- query_count: `{len(specs)}`",
        f"- query_type_counts: `{json.dumps(payload['query_type_counts'], ensure_ascii=False)}`",
        "",
        "| query_id | query_type | query | expected_behavior |",
        "| --- | --- | --- | --- |",
    ]
    for spec in specs:
        lines.append(
            f"| {spec.query_id} | {spec.query_type} | {spec.query} | {spec.expected_behavior} |"
        )
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_regression(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = payload["metrics"]
    lines = [
        "# AHV Adversarial Regression v1",
        "",
        f"- run_label: `{payload['run_label']}`",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- db_path: `{payload['db_path']}`",
        f"- total_query_count: `{metrics['total_query_count']}`",
        f"- pass_count / fail_count: `{metrics['pass_count']} / {metrics['fail_count']}`",
        f"- wrong_ahv_primary_hit_count: `{metrics['wrong_ahv_primary_hit_count']}`",
        f"- wrong_term_normalization_count: `{metrics['wrong_term_normalization_count']}`",
        f"- disabled_alias_still_hit_count: `{metrics['disabled_alias_still_hit_count']}`",
        f"- partial_word_false_positive_count: `{metrics['partial_word_false_positive_count']}`",
        f"- non_definition_intent_hijack_count: `{metrics['non_definition_intent_hijack_count']}`",
        f"- negative_sample_false_positive_count: `{metrics['negative_sample_false_positive_count']}`",
        f"- forbidden_primary_total: `{metrics['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_count: `{metrics['review_only_primary_conflict_count']}`",
        f"- formula_bad_anchor_top5_total: `{metrics['formula_bad_anchor_top5_total']}`",
        f"- ahv_canonical_guard_pass_count: `{metrics['ahv_canonical_guard_pass_count']}`",
        "",
        "## Failures",
        "",
    ]
    failures = payload["failures"]
    if failures:
        lines.extend(
            [
                "| query_id | query_type | query | answer_mode | matched_ahv_terms | ahv_primary_terms | fail_reason |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in failures:
            lines.append(
                "| "
                + " | ".join(
                    [
                        row["query_id"],
                        row["query_type"],
                        row["query"],
                        str(row["actual_answer_mode"]),
                        ",".join(row["matched_ahv_terms"]) or "-",
                        ",".join(row["ahv_primary_terms"]) or "-",
                        row["fail_reason"],
                    ]
                )
                + " |"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Query Results",
            "",
            "| query_id | query_type | query | answer_mode | focus | primary_ids | pass |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["query_id"],
                    row["query_type"],
                    row["query"],
                    str(row["actual_answer_mode"]),
                    str(row.get("query_focus_source")),
                    "<br>".join(row["primary_ids"]) or "-",
                    str(row["pass"]),
                ]
            )
            + " |"
        )
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    query_set_json = resolve_project_path(args.query_set_json)
    query_set_md = resolve_project_path(args.query_set_md)
    specs = build_query_specs()
    if len(specs) < 80:
        raise SystemExit(f"query set too small: {len(specs)}")
    write_query_set((query_set_json, query_set_md), specs)

    registry = load_definition_registry(db_path)
    ahv_ids_by_term = ahv_term_to_id(registry)
    missing_terms = [term for term in AHV_TERMS if term not in ahv_ids_by_term]
    if missing_terms:
        raise SystemExit("Missing AHV terms in registry: " + ",".join(missing_terms))

    assembler = make_assembler(db_path)
    try:
        rows = [result_for_spec(assembler, registry, ahv_ids_by_term, spec) for spec in specs]
    finally:
        assembler.close()

    metrics = summarize(rows, args.run_label)
    payload = {
        "run_id": RUN_ID,
        "run_label": args.run_label,
        "generated_at_utc": now_utc(),
        "db_path": str(db_path),
        "query_set_json": str(query_set_json),
        "query_count": len(specs),
        "metrics": metrics,
        "rows": rows,
        "failures": [row for row in rows if not row["pass"]],
    }
    write_regression(output_json, output_md, payload)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
