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
from scripts.data_plane_batch_upgrade_v2.run_ambiguous_high_value_evidence_upgrade_v2 import (  # noqa: E402
    AHV2_SAFE_LAYER,
    CANDIDATES,
)


RUN_ID = "ahv2_adversarial_regression_v1"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_batch_upgrade_v2"
DEFAULT_OUTPUT_JSON = f"{DEFAULT_OUTPUT_DIR}/ahv2_adversarial_after_fix_v1.json"
DEFAULT_OUTPUT_MD = f"{DEFAULT_OUTPUT_DIR}/ahv2_adversarial_after_fix_v1.md"
DEFAULT_QUERY_SET_JSON = f"{DEFAULT_OUTPUT_DIR}/ahv2_adversarial_query_set_v1.json"
DEFAULT_QUERY_SET_MD = f"{DEFAULT_OUTPUT_DIR}/ahv2_adversarial_query_set_v1.md"
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
AHV1_LAYER = "ambiguous_high_value_batch_safe_primary"
REVIEW_ONLY_TERMS = {"神丹", "将军", "口苦病", "胆瘅病", "高", "章", "卑", "惵", "损", "纲", "缓", "迟"}


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    query: str
    query_type: str
    expected_behavior: str
    expected_ahv2_terms: tuple[str, ...] = ()
    require_no_ahv2_primary: bool = False
    require_no_ahv2_normalization: bool = False
    require_no_definition_primary: bool = False
    require_formula_guard: bool = False
    require_strong: bool = False
    allow_ahv2_normalization_terms: tuple[str, ...] = field(default_factory=tuple)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AHV2 adversarial regression.")
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


def load_definition_registry(db_path: Path) -> dict[str, dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            str(row["concept_id"]): dict(row)
            for row in conn.execute(
                """
                SELECT concept_id, canonical_term, promotion_state, promotion_source_layer,
                       source_confidence, review_only_reason, is_safe_primary_candidate, is_active
                FROM definition_term_registry
                """
            )
        }
    finally:
        conn.close()


def term_to_id(registry: dict[str, dict[str, Any]], layer: str) -> dict[str, str]:
    return {
        row["canonical_term"]: concept_id
        for concept_id, row in registry.items()
        if row.get("promotion_source_layer") == layer
    }


def build_query_specs() -> list[QuerySpec]:
    a_items = [item for item in CANDIDATES if item.category == "A"]
    specs = [
        QuerySpec(
            query_id=f"ahv2_canonical_{index:02d}",
            query=item.query,
            query_type="ahv2_canonical_guard",
            expected_behavior=f"必须命中 {item.canonical_term} 的 AHV2 safe definition primary。",
            expected_ahv2_terms=(item.canonical_term,),
            allow_ahv2_normalization_terms=(item.canonical_term,),
            require_strong=True,
        )
        for index, item in enumerate(a_items, start=1)
    ]

    similar_queries = (
        ("similar_01", "荣气微弱是什么意思", "相近词不得命中荣气微 AHV2。"),
        ("similar_02", "卫气虚是什么意思", "相近概念不得命中卫气衰 AHV2。"),
        ("similar_03", "阳气不足是什么意思", "既有阳不足对象不得误归阳气微 AHV2。"),
        ("similar_04", "亡阳是什么意思", "亡阳不得误归亡血 AHV2。"),
        ("similar_05", "平是什么意思", "单字平不得命中平脉 AHV2。"),
        ("similar_06", "平脉和数脉有什么区别", "比较意图不得被单个 AHV2 definition object 抢占。"),
        ("similar_07", "数是什么意思", "单字数不得命中数脉 AHV2。"),
        ("similar_08", "毛是什么意思", "单字毛不得命中毛脉 AHV2。"),
        ("similar_09", "纯弦是什么意思", "inactive 短 alias 不得命中纯弦脉 AHV2。"),
        ("similar_10", "残是什么意思", "单字残不得命中残贼 AHV2。"),
        ("similar_11", "八邪和残贼有什么区别", "相近概念比较不得被单个 AHV2 primary 抢占。"),
        ("similar_12", "湿病是什么", "湿病不得误命中湿家 AHV2。"),
        ("similar_13", "风湿病是什么", "现代/宽泛风湿病不得命中风湿 AHV2。"),
        ("similar_14", "水逆反应是什么", "现代水逆反应不得命中水逆 AHV2。"),
        ("similar_15", "半表半里和表里之间一样吗", "关系问法不得命中半表半里证 AHV2 primary。"),
        ("similar_16", "过经方是什么意思", "相近组合词不得命中过经 AHV2。"),
        ("similar_17", "结胸证和水结胸有什么区别", "比较问法不得被结胸 AHV2 抢占。"),
        ("similar_18", "阳明是什么意思", "短概念阳明不得命中阳明病 AHV2。"),
        ("similar_19", "太阴是什么意思", "短概念太阴不得命中太阴病 AHV2。"),
        ("similar_20", "少阴和厥阴有什么区别", "六经比较不得被单个 AHV2 primary 抢占。"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="similar_concept_false_trigger",
            expected_behavior=expected,
            require_no_ahv2_primary=True,
            require_no_ahv2_normalization=True,
        )
        for query_id, query, expected in similar_queries
    )

    disabled_alias_queries = (
        ("disabled_alias_01", "平是什么意思", "inactive 单字 alias 平不得命中平脉 AHV2。"),
        ("disabled_alias_02", "数是什么意思", "inactive 单字 alias 数不得命中数脉 AHV2。"),
        ("disabled_alias_03", "毛是什么意思", "inactive 单字 alias 毛不得命中毛脉 AHV2。"),
        ("disabled_alias_04", "纯弦是什么意思", "inactive risky alias 纯弦不得命中纯弦脉 AHV2。"),
        ("disabled_alias_05", "风湿病是什么", "inactive risky alias 风湿病不得命中风湿 AHV2。"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="disabled_alias_recheck",
            expected_behavior=expected,
            require_no_ahv2_primary=True,
            require_no_ahv2_normalization=True,
        )
        for query_id, query, expected in disabled_alias_queries
    )

    partial_queries = ("荣是什么意思", "卫是什么意思", "阳是什么意思", "血是什么意思", "平是什么意思", "数是什么意思", "毛是什么意思", "湿是什么意思", "水是什么意思", "胸是什么意思")
    specs.extend(
        QuerySpec(
            query_id=f"partial_word_{index:02d}",
            query=query,
            query_type="partial_word_literal_similarity",
            expected_behavior="部分词或单字不得触发 AHV2 normalization/primary。",
            require_no_ahv2_primary=True,
            require_no_ahv2_normalization=True,
        )
        for index, query in enumerate(partial_queries, start=1)
    )

    non_definition_queries = (
        ("non_definition_01", "荣气微怎么治？"),
        ("non_definition_02", "卫气衰用什么方？"),
        ("non_definition_03", "水逆怎么治？"),
        ("non_definition_04", "结胸用什么方？"),
        ("non_definition_05", "半表半里证有哪些方？"),
        ("non_definition_06", "阳明病怎么治疗？"),
        ("non_definition_07", "太阴病的病机是什么？"),
        ("non_definition_08", "风湿和湿家有什么区别？"),
        ("non_definition_09", "少阴病有哪些方？"),
        ("non_definition_10", "厥阴病怎么治？"),
    )
    specs.extend(
        QuerySpec(
            query_id=query_id,
            query=query,
            query_type="non_definition_intent",
            expected_behavior="治疗、方药、病机或比较意图不得被 AHV2 definition primary 抢占。",
            require_no_ahv2_primary=True,
            require_no_ahv2_normalization=True,
        )
        for query_id, query in non_definition_queries
    )

    negative_queries = (
        "平板电脑是什么",
        "数学是什么意思",
        "毛衣是什么",
        "风湿免疫科是什么",
        "水逆网络用语是什么意思",
        "胸口健身动作是什么",
        "太阴历是什么",
        "阳明山在哪里",
        "过经纪人是什么意思",
        "八邪游戏是什么",
    )
    specs.extend(
        QuerySpec(
            query_id=f"negative_{index:02d}",
            query=query,
            query_type="negative_unrelated",
            expected_behavior="现代词、普通词、生活词不得命中 AHV2 primary 或 AHV2 normalization。",
            require_no_ahv2_primary=True,
            require_no_ahv2_normalization=True,
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
            expected_behavior="formula guard 不得出现 bad anchor，且不得被 AHV2 definition primary 抢占。",
            require_no_ahv2_primary=True,
            require_formula_guard=True,
            require_strong=True,
        )
        for index, query in enumerate(formula_queries, start=1)
    )

    gold_queries = ("下药是什么意思", "四逆是什么意思", "盗汗是什么意思", "水结胸是什么", "坏病是什么")
    specs.extend(
        QuerySpec(
            query_id=f"gold_safe_definition_{index:02d}",
            query=query,
            query_type="gold_safe_definition_guard",
            expected_behavior="既有 gold-safe definition guard 必须保持 strong，且不得被 AHV2 primary 抢占。",
            require_no_ahv2_primary=True,
            require_strong=True,
        )
        for index, query in enumerate(gold_queries, start=1)
    )

    ahv1_queries = ("伤寒是什么", "霍乱是什么", "劳复是什么意思", "食复是什么意思", "结脉是什么")
    specs.extend(
        QuerySpec(
            query_id=f"ahv_v1_guard_{index:02d}",
            query=query,
            query_type="ahv_v1_guard",
            expected_behavior="AHV v1 guard 必须保持可用，不得被 AHV2 primary 抢占。",
            require_no_ahv2_primary=True,
            require_strong=True,
        )
        for index, query in enumerate(ahv1_queries, start=1)
    )

    review_queries = ("神丹是什么意思", "将军是什么意思", "高是什么意思", "顺是什么意思")
    specs.extend(
        QuerySpec(
            query_id=f"review_only_boundary_{index:02d}",
            query=query,
            query_type="review_only_boundary_guard",
            expected_behavior="review-only boundary 不得进入 definition primary。",
            require_no_definition_primary=True,
            require_no_ahv2_primary=True,
            require_no_ahv2_normalization=True,
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
        "expected_ahv2_terms": list(spec.expected_ahv2_terms),
        "require_no_ahv2_primary": spec.require_no_ahv2_primary,
        "require_no_ahv2_normalization": spec.require_no_ahv2_normalization,
        "require_no_definition_primary": spec.require_no_definition_primary,
        "require_formula_guard": spec.require_formula_guard,
        "require_strong": spec.require_strong,
        "allow_ahv2_normalization_terms": list(spec.allow_ahv2_normalization_terms),
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
    ahv2_ids_by_term: dict[str, str],
    spec: QuerySpec,
) -> dict[str, Any]:
    expected_ids = {ahv2_ids_by_term[term] for term in spec.expected_ahv2_terms if term in ahv2_ids_by_term}
    allowed_norm_ids = {
        ahv2_ids_by_term[term]
        for term in (*spec.expected_ahv2_terms, *spec.allow_ahv2_normalization_terms)
        if term in ahv2_ids_by_term
    }
    ahv2_id_to_term = {concept_id: term for term, concept_id in ahv2_ids_by_term.items()}
    try:
        retrieval = assembler.engine.retrieve(spec.query)
        payload = assembler.assemble(spec.query)
    except Exception as exc:
        return {
            **spec_to_artifact(spec),
            "actual_answer_mode": "error",
            "mode_bucket": "refuse",
            "matched_concept_ids": [],
            "matched_terms": [],
            "matched_ahv2_terms": [],
            "primary_ids": [],
            "primary_record_types": [],
            "is_ahv2_primary_hit": False,
            "ahv2_primary_terms": [],
            "wrong_ahv2_primary_hit": False,
            "wrong_term_normalization": False,
            "forbidden_primary_items": [],
            "review_only_primary_conflict": False,
            "formula_bad_anchor_count": 0,
            "pass": False,
            "fail_reason": f"exception: {type(exc).__name__}: {exc}",
        }

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
    ahv2_primary_ids = [concept_id for concept_id in primary_concept_ids if concept_id in ahv2_id_to_term]
    ahv2_primary_terms = [ahv2_id_to_term[concept_id] for concept_id in ahv2_primary_ids]
    wrong_ahv2_primary_ids = [concept_id for concept_id in ahv2_primary_ids if concept_id not in expected_ids]
    if spec.require_no_ahv2_primary:
        wrong_ahv2_primary_ids = ahv2_primary_ids

    ahv2_normalized_ids = [concept_id for concept_id in matched_concept_ids if concept_id in ahv2_id_to_term]
    wrong_normalized_ids = [concept_id for concept_id in ahv2_normalized_ids if concept_id not in allowed_norm_ids]
    wrong_term_normalization = bool(wrong_normalized_ids)
    if spec.require_no_ahv2_normalization and ahv2_normalized_ids:
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
        1
        for row in (retrieval.get("raw_candidates") or [])[:5]
        if row.get("topic_consistency") in BAD_FORMULA_TOPICS
    )

    fail_reasons: list[str] = []
    if forbidden_items:
        fail_reasons.append("forbidden primary evidence")
    if spec.expected_ahv2_terms:
        missing = [term for term in spec.expected_ahv2_terms if ahv2_ids_by_term.get(term) not in ahv2_primary_ids]
        if missing:
            fail_reasons.append("expected AHV2 primary missing: " + ",".join(missing))
    if wrong_ahv2_primary_ids:
        fail_reasons.append(
            "wrong AHV2 primary hit: " + ",".join(ahv2_id_to_term[concept_id] for concept_id in wrong_ahv2_primary_ids)
        )
    if wrong_term_normalization:
        fail_reasons.append(
            "wrong AHV2 term normalization: "
            + ",".join(ahv2_id_to_term[concept_id] for concept_id in wrong_normalized_ids or ahv2_normalized_ids)
        )
    if spec.require_no_definition_primary and any(record_type == "definition_terms" for record_type in primary_record_types):
        fail_reasons.append("definition primary present for review-only boundary")
    if review_conflicts:
        fail_reasons.append("review-only definition object entered primary")
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
        "matched_terms": [term for term in matched_terms if term],
        "matched_ahv2_terms": [ahv2_id_to_term[concept_id] for concept_id in ahv2_normalized_ids],
        "primary_ids": primary_ids,
        "primary_record_types": primary_record_types,
        "is_ahv2_primary_hit": bool(ahv2_primary_ids),
        "ahv2_primary_terms": ahv2_primary_terms,
        "wrong_ahv2_primary_hit": bool(wrong_ahv2_primary_ids),
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
    mode_counts = Counter(row["mode_bucket"] for row in rows)
    fail_rows = [row for row in rows if not row["pass"]]
    canonical_rows = [row for row in rows if row["query_type"] == "ahv2_canonical_guard"]
    ahv1_rows = [row for row in rows if row["query_type"] == "ahv_v1_guard"]
    return {
        "run_label": run_label,
        "total_query_count": len(rows),
        "strong_count": mode_counts.get("strong", 0),
        "weak_count": mode_counts.get("weak", 0),
        "refuse_count": mode_counts.get("refuse", 0),
        "pass_count": len(rows) - len(fail_rows),
        "fail_count": len(fail_rows),
        "query_type_counts": dict(sorted(query_type_counts.items())),
        "new_safe_object_primary_hit_count": sum(1 for row in canonical_rows if row["is_ahv2_primary_hit"]),
        "wrong_ahv2_primary_hit_count": sum(1 for row in rows if row["wrong_ahv2_primary_hit"]),
        "wrong_term_normalization_count": sum(1 for row in rows if row["wrong_term_normalization"]),
        "disabled_alias_still_hit_count": sum(
            1
            for row in rows
            if row["query_type"] == "disabled_alias_recheck"
            and (row["is_ahv2_primary_hit"] or row["matched_ahv2_terms"])
        ),
        "partial_word_false_positive_count": sum(
            1
            for row in rows
            if row["query_type"] == "partial_word_literal_similarity"
            and (row["is_ahv2_primary_hit"] or row["matched_ahv2_terms"])
        ),
        "non_definition_intent_hijack_count": sum(
            1
            for row in rows
            if row["query_type"] == "non_definition_intent"
            and (row["is_ahv2_primary_hit"] or row["matched_ahv2_terms"])
        ),
        "negative_sample_false_positive_count": sum(
            1
            for row in rows
            if row["query_type"] == "negative_unrelated"
            and (row["is_ahv2_primary_hit"] or row["matched_ahv2_terms"])
        ),
        "forbidden_primary_total": sum(len(row["forbidden_primary_items"]) for row in rows),
        "review_only_primary_conflict_count": sum(1 for row in rows if row["review_only_primary_conflict"]),
        "formula_bad_anchor_top5_total": sum(
            row["formula_bad_anchor_count"] for row in rows if row["query_type"] == "formula_guard"
        ),
        "ahv_v1_guard_pass_count": sum(1 for row in ahv1_rows if row["pass"]),
        "ahv_v1_guard_total": len(ahv1_rows),
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
        "# AHV2 Adversarial Query Set v1",
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_regression(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    write_json(path_json, payload)
    metrics = payload["metrics"]
    lines = [
        "# AHV2 Adversarial Regression v1",
        "",
        f"- run_label: `{payload['run_label']}`",
        f"- total_query_count: `{metrics['total_query_count']}`",
        f"- strong / weak / refuse: `{metrics['strong_count']} / {metrics['weak_count']} / {metrics['refuse_count']}`",
        f"- pass_count / fail_count: `{metrics['pass_count']} / {metrics['fail_count']}`",
        f"- new_safe_object_primary_hit_count: `{metrics['new_safe_object_primary_hit_count']}`",
        f"- wrong_ahv2_primary_hit_count: `{metrics['wrong_ahv2_primary_hit_count']}`",
        f"- wrong_term_normalization_count: `{metrics['wrong_term_normalization_count']}`",
        f"- disabled_alias_still_hit_count: `{metrics['disabled_alias_still_hit_count']}`",
        f"- partial_word_false_positive_count: `{metrics['partial_word_false_positive_count']}`",
        f"- non_definition_intent_hijack_count: `{metrics['non_definition_intent_hijack_count']}`",
        f"- negative_sample_false_positive_count: `{metrics['negative_sample_false_positive_count']}`",
        f"- forbidden_primary_total: `{metrics['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_count: `{metrics['review_only_primary_conflict_count']}`",
        f"- formula_bad_anchor_top5_total: `{metrics['formula_bad_anchor_top5_total']}`",
        f"- ahv_v1_guard_pass_count: `{metrics['ahv_v1_guard_pass_count']}`",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines.extend(
            [
                "| query_id | query_type | query | mode | matched_ahv2_terms | ahv2_primary_terms | fail_reason |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in payload["failures"]:
            lines.append(
                f"| {row['query_id']} | {row['query_type']} | {row['query']} | {row['actual_answer_mode']} | "
                f"{','.join(row['matched_ahv2_terms']) or '-'} | {','.join(row['ahv2_primary_terms']) or '-'} | {row['fail_reason']} |"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Query Results", "", "| query_id | query_type | query | mode | primary_ids | pass |", "| --- | --- | --- | --- | --- | --- |"])
    for row in payload["rows"]:
        lines.append(
            f"| {row['query_id']} | {row['query_type']} | {row['query']} | {row['actual_answer_mode']} | "
            f"{'<br>'.join(row['primary_ids']) or '-'} | {row['pass']} |"
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
    if len(specs) < 80:
        raise SystemExit(f"query set too small: {len(specs)}")
    write_query_set(query_set_json, query_set_md, specs)

    registry = load_definition_registry(db_path)
    ahv2_ids_by_term = term_to_id(registry, AHV2_SAFE_LAYER)
    expected_terms = {item.canonical_term for item in CANDIDATES if item.category == "A"}
    missing_terms = sorted(expected_terms - set(ahv2_ids_by_term))
    if missing_terms:
        raise SystemExit("Missing AHV2 terms in registry: " + ",".join(missing_terms))

    assembler = make_assembler(db_path)
    try:
        rows = [result_for_spec(assembler, registry, ahv2_ids_by_term, spec) for spec in specs]
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
