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
from scripts.data_plane_cross_batch.run_cross_batch_ahv_consistency_audit_v1 import (  # noqa: E402
    AHV2_LAYER,
    AHV_SAFE_LAYERS,
    AHV_V1_LAYER,
)


RUN_ID = "cross_batch_adversarial_regression_v1"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_cross_batch"
DEFAULT_OUTPUT_JSON = f"{DEFAULT_OUTPUT_DIR}/cross_batch_adversarial_after_fix_v1.json"
DEFAULT_OUTPUT_MD = f"{DEFAULT_OUTPUT_DIR}/cross_batch_adversarial_after_fix_v1.md"
DEFAULT_QUERY_SET_JSON = f"{DEFAULT_OUTPUT_DIR}/cross_batch_adversarial_query_set_v1.json"
DEFAULT_QUERY_SET_MD = f"{DEFAULT_OUTPUT_DIR}/cross_batch_adversarial_query_set_v1.md"

FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}

AHV_V1_CANONICAL_TERMS = (
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

AHV2_CANONICAL_TERMS = (
    "荣气微",
    "卫气衰",
    "阳气微",
    "亡血",
    "平脉",
    "数脉",
    "毛脉",
    "纯弦脉",
    "残贼",
    "八邪",
    "湿家",
    "风湿",
    "水逆",
    "半表半里证",
    "过经",
    "结胸",
    "阳明病",
    "太阴病",
    "少阴病",
    "厥阴病",
)

REVIEW_ONLY_TERMS = {
    "神丹",
    "将军",
    "两阳",
    "胆瘅",
    "胆瘅病",
    "火劫发汗",
    "肝乘脾",
    "反",
    "复",
    "寒格",
    "清邪中上",
}


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    query: str
    query_type: str
    expected_behavior: str
    expected_terms: tuple[str, ...] = ()
    expected_batch: str | None = None
    require_no_ahv_primary: bool = False
    require_no_ahv_normalization: bool = False
    require_no_definition_primary: bool = False
    require_formula_guard: bool = False
    require_strong: bool = False
    allow_normalization_terms: tuple[str, ...] = field(default_factory=tuple)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run cross-batch AHV adversarial regression.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--query-set-json", default=DEFAULT_QUERY_SET_JSON)
    parser.add_argument("--query-set-md", default=DEFAULT_QUERY_SET_MD)
    parser.add_argument("--run-label", default="after_fix")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def normalize_mode(answer_mode: str | None) -> str:
    if answer_mode == "strong":
        return "strong"
    if answer_mode and str(answer_mode).startswith("weak"):
        return "weak"
    return "refuse"


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


def load_definition_registry(db_path: Path) -> dict[str, dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            str(row["concept_id"]): dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM definition_term_registry
                """
            )
        }
    finally:
        conn.close()


def ahv_term_to_id(registry: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {
        str(row["canonical_term"]): concept_id
        for concept_id, row in registry.items()
        if row.get("promotion_source_layer") in AHV_SAFE_LAYERS
        and row.get("promotion_state") == "safe_primary"
        and int(row.get("is_active") or 0) == 1
    }


def ahv_id_to_batch(registry: dict[str, dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for concept_id, row in registry.items():
        if row.get("promotion_source_layer") == AHV_V1_LAYER:
            result[concept_id] = "ahv_v1"
        elif row.get("promotion_source_layer") == AHV2_LAYER:
            result[concept_id] = "ahv2"
    return result


def build_query_specs() -> list[QuerySpec]:
    specs: list[QuerySpec] = []

    v1_queries = (
        ("ahv_v1_canonical_01", "何谓太阳病", "太阳病"),
        ("ahv_v1_canonical_02", "伤寒是什么", "伤寒"),
        ("ahv_v1_canonical_03", "温病是什么意思", "温病"),
        ("ahv_v1_canonical_04", "暑病是什么意思", "暑病"),
        ("ahv_v1_canonical_05", "冬温是什么", "冬温"),
        ("ahv_v1_canonical_06", "时行寒疫是什么", "时行寒疫"),
        ("ahv_v1_canonical_07", "刚痓是什么", "刚痓"),
        ("ahv_v1_canonical_08", "柔痓是什么意思", "柔痓"),
        ("ahv_v1_canonical_09", "痓病是什么", "痓病"),
        ("ahv_v1_canonical_10", "结脉是什么", "结脉"),
        ("ahv_v1_canonical_11", "促脉是什么", "促脉"),
        ("ahv_v1_canonical_12", "弦脉是什么", "弦脉"),
        ("ahv_v1_canonical_13", "滑脉是什么意思", "滑脉"),
        ("ahv_v1_canonical_14", "革脉是什么", "革脉"),
        ("ahv_v1_canonical_15", "行尸是什么意思", "行尸"),
        ("ahv_v1_canonical_16", "内虚是什么意思", "内虚"),
        ("ahv_v1_canonical_17", "血崩是什么", "血崩"),
        ("ahv_v1_canonical_18", "霍乱是什么", "霍乱"),
        ("ahv_v1_canonical_19", "劳复是什么意思", "劳复"),
        ("ahv_v1_canonical_20", "食复是什么意思", "食复"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="ahv_v1_canonical_guard",
            expected_behavior=f"必须命中 AHV v1 `{term}` safe primary。",
            expected_terms=(term,),
            expected_batch="ahv_v1",
            allow_normalization_terms=(term,),
            require_strong=True,
        )
        for query_id, query, term in v1_queries
    )

    v2_queries = tuple(
        (f"ahv2_canonical_{index:02d}", f"{term}是什么意思" if index <= 16 else f"{term}是什么", term)
        for index, term in enumerate(AHV2_CANONICAL_TERMS, start=1)
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="ahv2_canonical_guard",
            expected_behavior=f"必须命中 AHV2 `{term}` safe primary。",
            expected_terms=(term,),
            expected_batch="ahv2",
            allow_normalization_terms=(term,),
            require_strong=True,
        )
        for query_id, query, term in v2_queries
    )

    conflict_queries = (
        ("conflict_01", "太阳病和阳明病有什么区别", "六经比较不得被单个 AHV 对象抢 primary。"),
        ("conflict_02", "伤寒和温病有什么区别", "伤寒/温病比较不得被单个 AHV 对象抢 primary。"),
        ("conflict_03", "伤寒和暑病是一回事吗", "近义/关系问法不得单点归一。"),
        ("conflict_04", "刚痓和柔痓有什么不同", "刚痓/柔痓比较不得单点归一。"),
        ("conflict_05", "痓病和刚痓是什么关系", "宽窄关系问法不得被单个对象抢 primary。"),
        ("conflict_06", "结脉和促脉有什么区别", "脉象比较不得单点归一。"),
        ("conflict_07", "弦脉和纯弦脉有什么区别", "相近脉象比较不得单点归一。"),
        ("conflict_08", "滑脉和数脉有什么区别", "脉象比较不得单点归一。"),
        ("conflict_09", "劳复和食复一样吗", "瘥后复病关系问法不得单点归一。"),
        ("conflict_10", "结胸和水逆有什么不同", "病证比较不得单点归一。"),
        ("conflict_11", "半表半里证和结胸有什么关系", "关系问法不得单点归一。"),
        ("conflict_12", "水逆和水结胸是一回事吗", "近词比较不得单点归一。"),
        ("conflict_13", "少阴病和厥阴病有什么区别", "六经比较不得单点归一。"),
        ("conflict_14", "太阴病和阳明病有什么区别", "六经比较不得单点归一。"),
        ("conflict_15", "温病和暑病有什么关系", "时病关系问法不得单点归一。"),
        ("conflict_16", "冬温和温病是一回事吗", "宽窄关系不得误归一。"),
        ("conflict_17", "时行寒疫和伤寒有什么不同", "相近外感病名不得误归一。"),
        ("conflict_18", "平脉和数脉有什么区别", "脉象比较不得单点归一。"),
        ("conflict_19", "毛脉和革脉有什么区别", "脉象比较不得单点归一。"),
        ("conflict_20", "残贼和八邪有什么关系", "分类/病理关系不得单点归一。"),
        ("conflict_21", "湿家和风湿有什么区别", "湿病相关概念不得互抢。"),
        ("conflict_22", "阳气微和内虚有什么关系", "跨批次状态概念不得误归一。"),
        ("conflict_23", "亡血和血崩是一回事吗", "气血状态/病名不得误归一。"),
        ("conflict_24", "过经和劳复有什么不同", "病程/复病概念不得误归一。"),
        ("conflict_25", "太阳病和少阴病怎样区分", "六经区分问法不得单点归一。"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="cross_batch_concept_conflict",
            expected_behavior=expected,
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for query_id, query, expected in conflict_queries
    )

    non_definition_queries = (
        "阳明病用什么方",
        "少阴病怎么治",
        "厥阴病有哪些方",
        "霍乱用什么方",
        "结胸怎么治",
        "水逆用什么方",
        "伤寒怎么治疗",
        "温病怎么治",
        "劳复应该怎么处理",
        "食复应该怎么处理",
        "弦脉预后如何",
        "革脉说明什么",
        "结脉有什么方",
        "太阳病的条文是什么",
        "阳明病的条文是什么",
        "太阴病的病机是什么",
        "半表半里证用什么方",
        "风湿如何治疗",
        "亡血怎么处理",
        "过经之后用什么方",
    )
    specs.extend(
        QuerySpec(
            query_id=f"non_definition_{index:02d}",
            query=query,
            query_type="non_definition_intent",
            expected_behavior="治疗、方药、病机、预后、条文意图不得被 AHV definition primary 抢占。",
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for index, query in enumerate(non_definition_queries, start=1)
    )

    negative_queries = (
        "温是什么意思",
        "寒是什么意思",
        "阳是什么意思",
        "阴是什么意思",
        "数是什么意思",
        "毛是什么意思",
        "纯是什么意思",
        "弦是什么意思",
        "水是什么意思",
        "过是什么意思",
        "半表是什么意思",
        "复习是什么意思",
        "劳动是什么意思",
        "食物是什么意思",
        "太阳能是什么意思",
        "阳明山是什么",
        "少阴影是什么意思",
        "太阴历是什么",
        "厥是什么意思",
        "八邪游戏是什么",
    )
    specs.extend(
        QuerySpec(
            query_id=f"negative_alias_{index:02d}",
            query=query,
            query_type="alias_partial_negative",
            expected_behavior="单字、部分词、现代词、生活词不得触发 AHV primary 或 AHV normalization。",
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
        )
        for index, query in enumerate(negative_queries, start=1)
    )

    review_queries = (
        "神丹是什么意思",
        "将军是什么意思",
        "两阳是什么意思",
        "胆瘅是什么意思",
        "火劫发汗是什么意思",
        "肝乘脾是什么意思",
        "反是什么意思",
        "复是什么意思",
        "寒格是什么意思",
        "清邪中上是什么意思",
    )
    specs.extend(
        QuerySpec(
            query_id=f"review_only_{index:02d}",
            query=query,
            query_type="review_only_rejected_guard",
            expected_behavior="review-only/rejected 边界对象不得进入 definition primary，也不得触发 AHV normalization。",
            require_no_ahv_primary=True,
            require_no_ahv_normalization=True,
            require_no_definition_primary=True,
        )
        for index, query in enumerate(review_queries, start=1)
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
            require_no_ahv_normalization=True,
            require_formula_guard=True,
            require_strong=True,
        )
        for index, query in enumerate(formula_queries, start=1)
    )
    return specs


def spec_to_artifact(spec: QuerySpec) -> dict[str, Any]:
    return {
        "query_id": spec.query_id,
        "query": spec.query,
        "query_type": spec.query_type,
        "expected_behavior": spec.expected_behavior,
        "expected_terms": list(spec.expected_terms),
        "expected_batch": spec.expected_batch,
        "require_no_ahv_primary": spec.require_no_ahv_primary,
        "require_no_ahv_normalization": spec.require_no_ahv_normalization,
        "require_no_definition_primary": spec.require_no_definition_primary,
        "require_formula_guard": spec.require_formula_guard,
        "require_strong": spec.require_strong,
        "allow_normalization_terms": list(spec.allow_normalization_terms),
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
    batch_by_id: dict[str, str],
    spec: QuerySpec,
) -> dict[str, Any]:
    expected_ids = {ahv_ids_by_term[term] for term in spec.expected_terms if term in ahv_ids_by_term}
    allowed_norm_ids = {
        ahv_ids_by_term[term]
        for term in (*spec.expected_terms, *spec.allow_normalization_terms)
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
            "matched_concept_ids": [],
            "matched_ahv_terms": [],
            "primary_ids": [],
            "primary_record_types": [],
            "ahv_primary_terms": [],
            "wrong_ahv_primary_hit": False,
            "wrong_term_normalization": False,
            "non_definition_intent_hijack": False,
            "comparison_primary_hijack": False,
            "forbidden_primary_items": [],
            "review_only_primary_conflict": False,
            "formula_bad_anchor_count": 0,
            "pass": False,
            "fail_reason": f"exception: {type(exc).__name__}: {exc}",
        }

    term_normalization = retrieval.get("query_request", {}).get("term_normalization") or {}
    matched_concept_ids = [str(item) for item in term_normalization.get("concept_ids") or []]
    matched_ahv_ids = [concept_id for concept_id in matched_concept_ids if concept_id in ahv_id_to_term]
    matched_ahv_terms = [ahv_id_to_term[concept_id] for concept_id in matched_ahv_ids]
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
    wrong_normalized_ids = [concept_id for concept_id in matched_ahv_ids if concept_id not in allowed_norm_ids]
    wrong_term_normalization = bool(wrong_normalized_ids)
    if spec.require_no_ahv_normalization and matched_ahv_ids:
        wrong_term_normalization = True

    forbidden_items = primary_forbidden_items(payload)
    review_conflicts: list[dict[str, Any]] = []
    for concept_id in primary_concept_ids:
        row = registry.get(concept_id)
        if not row:
            continue
        if (
            row.get("promotion_state") != "safe_primary"
            or int(row.get("is_safe_primary_candidate") or 0) == 0
            or row.get("canonical_term") in REVIEW_ONLY_TERMS
        ):
            review_conflicts.append(
                {
                    "concept_id": concept_id,
                    "canonical_term": row.get("canonical_term"),
                    "promotion_state": row.get("promotion_state"),
                    "promotion_source_layer": row.get("promotion_source_layer"),
                }
            )

    formula_bad_anchor_count = sum(
        1
        for row in (retrieval.get("raw_candidates") or [])[:5]
        if row.get("topic_consistency") in BAD_FORMULA_TOPICS
    )
    non_definition_hijack = spec.query_type == "non_definition_intent" and (
        bool(ahv_primary_ids) or bool(matched_ahv_ids)
    )
    comparison_hijack = spec.query_type == "cross_batch_concept_conflict" and (
        bool(ahv_primary_ids) or bool(matched_ahv_ids)
    )

    fail_reasons: list[str] = []
    if forbidden_items:
        fail_reasons.append("forbidden primary evidence")
    if spec.expected_terms:
        missing = [term for term in spec.expected_terms if ahv_ids_by_term.get(term) not in ahv_primary_ids]
        if missing:
            fail_reasons.append("expected AHV primary missing: " + ",".join(missing))
        if spec.expected_batch:
            wrong_batch = [
                concept_id
                for concept_id in ahv_primary_ids
                if concept_id in expected_ids and batch_by_id.get(concept_id) != spec.expected_batch
            ]
            if wrong_batch:
                fail_reasons.append("expected batch mismatch")
    if wrong_ahv_primary_ids:
        fail_reasons.append(
            "wrong AHV primary hit: " + ",".join(ahv_id_to_term[concept_id] for concept_id in wrong_ahv_primary_ids)
        )
    if wrong_term_normalization:
        fail_reasons.append(
            "wrong AHV term normalization: "
            + ",".join(ahv_id_to_term[concept_id] for concept_id in wrong_normalized_ids or matched_ahv_ids)
        )
    if spec.require_no_definition_primary and any(record_type == "definition_terms" for record_type in primary_record_types):
        fail_reasons.append("definition primary present for review-only/rejected guard")
    if review_conflicts:
        fail_reasons.append("review-only/rejected definition object entered primary")
    if spec.require_formula_guard and formula_bad_anchor_count:
        fail_reasons.append("formula bad anchor in raw top5")
    if spec.require_strong and normalize_mode(payload.get("answer_mode")) != "strong":
        fail_reasons.append("expected strong answer_mode")

    return {
        **spec_to_artifact(spec),
        "actual_answer_mode": payload.get("answer_mode"),
        "mode_bucket": normalize_mode(payload.get("answer_mode")),
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "matched_concept_ids": matched_concept_ids,
        "matched_ahv_terms": matched_ahv_terms,
        "matched_ahv_batches": [batch_by_id.get(concept_id) for concept_id in matched_ahv_ids],
        "primary_ids": primary_ids,
        "primary_record_types": primary_record_types,
        "ahv_primary_terms": ahv_primary_terms,
        "ahv_primary_batches": [batch_by_id.get(concept_id) for concept_id in ahv_primary_ids],
        "wrong_ahv_primary_hit": bool(wrong_ahv_primary_ids),
        "wrong_term_normalization": wrong_term_normalization,
        "non_definition_intent_hijack": non_definition_hijack,
        "comparison_primary_hijack": comparison_hijack,
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
    mode_counts = Counter(row["mode_bucket"] for row in rows)
    fail_rows = [row for row in rows if not row["pass"]]
    v1_rows = [row for row in rows if row["query_type"] == "ahv_v1_canonical_guard"]
    v2_rows = [row for row in rows if row["query_type"] == "ahv2_canonical_guard"]
    return {
        "run_label": run_label,
        "total_query_count": len(rows),
        "strong_count": mode_counts.get("strong", 0),
        "weak_count": mode_counts.get("weak", 0),
        "refuse_count": mode_counts.get("refuse", 0),
        "query_type_counts": dict(sorted(query_type_counts.items())),
        "wrong_ahv_primary_hit_count": sum(1 for row in rows if row["wrong_ahv_primary_hit"]),
        "wrong_term_normalization_count": sum(1 for row in rows if row["wrong_term_normalization"]),
        "non_definition_intent_hijack_count": sum(1 for row in rows if row["non_definition_intent_hijack"]),
        "comparison_primary_hijack_count": sum(1 for row in rows if row["comparison_primary_hijack"]),
        "forbidden_primary_total": sum(len(row["forbidden_primary_items"]) for row in rows),
        "review_only_primary_conflict_count": sum(1 for row in rows if row["review_only_primary_conflict"]),
        "formula_bad_anchor_top5_total": sum(
            row["formula_bad_anchor_count"] for row in rows if row["query_type"] == "formula_guard"
        ),
        "ahv_v1_guard_pass_count": sum(1 for row in v1_rows if row["pass"]),
        "ahv_v1_guard_total": len(v1_rows),
        "ahv2_guard_pass_count": sum(1 for row in v2_rows if row["pass"]),
        "ahv2_guard_total": len(v2_rows),
        "regression_pass_count": len(rows) - len(fail_rows),
        "regression_fail_count": len(fail_rows),
        "failure_query_ids": [row["query_id"] for row in fail_rows],
    }


def write_query_set(path_json: Path, path_md: Path, specs: list[QuerySpec]) -> None:
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "query_count": len(specs),
        "query_type_counts": dict(sorted(Counter(spec.query_type for spec in specs).items())),
        "queries": [spec_to_artifact(spec) for spec in specs],
    }
    write_json(path_json, payload)
    lines = [
        "# Cross-Batch AHV Adversarial Query Set v1",
        "",
        f"- query_count: `{payload['query_count']}`",
        f"- query_type_counts: `{json.dumps(payload['query_type_counts'], ensure_ascii=False)}`",
        "",
        "| query_id | query_type | query | expected_behavior |",
        "| --- | --- | --- | --- |",
    ]
    for spec in specs:
        lines.append(f"| {spec.query_id} | {spec.query_type} | {spec.query} | {spec.expected_behavior} |")
    write_md(path_md, lines)


def write_regression(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    write_json(path_json, payload)
    metrics = payload["metrics"]
    lines = [
        "# Cross-Batch AHV Adversarial Regression v1",
        "",
        f"- run_label: `{payload['run_label']}`",
        f"- total_query_count: `{metrics['total_query_count']}`",
        f"- strong / weak / refuse: `{metrics['strong_count']} / {metrics['weak_count']} / {metrics['refuse_count']}`",
        f"- regression_pass_count / regression_fail_count: `{metrics['regression_pass_count']} / {metrics['regression_fail_count']}`",
        f"- wrong_ahv_primary_hit_count: `{metrics['wrong_ahv_primary_hit_count']}`",
        f"- wrong_term_normalization_count: `{metrics['wrong_term_normalization_count']}`",
        f"- non_definition_intent_hijack_count: `{metrics['non_definition_intent_hijack_count']}`",
        f"- comparison_primary_hijack_count: `{metrics['comparison_primary_hijack_count']}`",
        f"- forbidden_primary_total: `{metrics['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_count: `{metrics['review_only_primary_conflict_count']}`",
        f"- formula_bad_anchor_top5_total: `{metrics['formula_bad_anchor_top5_total']}`",
        f"- ahv_v1_guard_pass_count: `{metrics['ahv_v1_guard_pass_count']}` / `{metrics['ahv_v1_guard_total']}`",
        f"- ahv2_guard_pass_count: `{metrics['ahv2_guard_pass_count']}` / `{metrics['ahv2_guard_total']}`",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines.extend(
            [
                "| query_id | query_type | query | mode | matched_ahv_terms | ahv_primary_terms | fail_reason |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in payload["failures"]:
            lines.append(
                f"| {row['query_id']} | {row['query_type']} | {row['query']} | {row['actual_answer_mode']} | "
                f"{','.join(row['matched_ahv_terms']) or '-'} | {','.join(row['ahv_primary_terms']) or '-'} | {row['fail_reason']} |"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Query Results",
            "",
            "| query_id | query_type | query | mode | matched_ahv_terms | primary_ids | pass |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['query_id']} | {row['query_type']} | {row['query']} | {row['actual_answer_mode']} | "
            f"{','.join(row['matched_ahv_terms']) or '-'} | {'<br>'.join(row['primary_ids']) or '-'} | {row['pass']} |"
        )
    write_md(path_md, lines)


def main() -> None:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    query_set_json = resolve_project_path(args.query_set_json)
    query_set_md = resolve_project_path(args.query_set_md)

    specs = build_query_specs()
    if len(specs) < 100:
        raise SystemExit(f"query set too small: {len(specs)}")
    write_query_set(query_set_json, query_set_md, specs)

    registry = load_definition_registry(db_path)
    ahv_ids_by_term = ahv_term_to_id(registry)
    expected_terms = set(AHV_V1_CANONICAL_TERMS) | set(AHV2_CANONICAL_TERMS)
    missing_terms = sorted(expected_terms - set(ahv_ids_by_term))
    if missing_terms:
        raise SystemExit("Missing AHV terms in registry: " + ",".join(missing_terms))

    assembler = make_assembler(db_path)
    try:
        rows = [
            result_for_spec(assembler, registry, ahv_ids_by_term, ahv_id_to_batch(registry), spec)
            for spec in specs
        ]
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
