#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterator


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
from backend.llm import (  # noqa: E402
    DEFAULT_MODEL_STUDIO_BASE_URL,
    DEFAULT_MODEL_STUDIO_MODEL,
    LLMConfigError,
    ModelStudioLLMConfig,
    load_modelstudio_llm_config,
)
from backend.perf import (  # noqa: E402
    new_request_trace,
    reset_current_trace,
    set_current_trace,
)


RUN_ID = "full_chain_production_like_regression_v1"
OUTPUT_DIR = Path("artifacts/full_chain_regression")
DOC_DIR = Path("docs/full_chain_regression")

QUERY_SET_JSON = OUTPUT_DIR / "full_chain_query_set_v1.json"
QUERY_SET_MD = OUTPUT_DIR / "full_chain_query_set_v1.md"
RESULTS_JSON = OUTPUT_DIR / "full_chain_regression_results_v1.json"
RESULTS_MD = OUTPUT_DIR / "full_chain_regression_results_v1.md"
FAILURES_JSON = OUTPUT_DIR / "full_chain_failure_cases_v1.json"
FAILURES_MD = OUTPUT_DIR / "full_chain_failure_cases_v1.md"
REPAIR_QUEUE_JSON = OUTPUT_DIR / "data_layer_repair_queue_v1.json"
REPAIR_QUEUE_MD = OUTPUT_DIR / "data_layer_repair_queue_v1.md"
LATENCY_JSON = OUTPUT_DIR / "latency_snapshot_v1.json"
LATENCY_MD = OUTPUT_DIR / "latency_snapshot_v1.md"
REPORT_MD = DOC_DIR / "full_chain_production_like_regression_v1.md"

AHV_V1_LAYER = "ambiguous_high_value_batch_safe_primary"
AHV2_LAYER = "ambiguous_high_value_evidence_upgrade_v2_safe_primary"
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
DATA_LAYER_FAILURE_TYPES = {
    "data_layer_missing_object",
    "data_layer_bad_alias",
    "data_layer_bad_primary_sentence",
    "data_layer_bad_span",
    "review_only_boundary_error",
    "formula_comparison_primary_noise",
    "non_definition_intent_hijack",
}
FAILURE_TYPE_ORDER = (
    "review_only_boundary_error",
    "negative_query_false_positive",
    "formula_comparison_primary_noise",
    "data_layer_bad_alias",
    "data_layer_bad_span",
    "data_layer_missing_object",
    "retrieval_miss",
    "rerank_regression",
    "assembler_slot_error",
    "answer_mode_calibration_error",
    "llm_faithfulness_error",
    "citation_error",
    "data_layer_bad_primary_sentence",
    "non_definition_intent_hijack",
)
MODE_IDS = (
    "A_data_plane_baseline",
    "B_retrieval_rerank",
    "C_production_like_full_chain",
)


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    query: str
    query_category: str
    expected_terms: tuple[str, ...] = ()
    expected_formula_names: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class RunMode:
    run_mode: str
    label: str
    env: dict[str, str]
    llm_enabled: bool
    required: bool = False
    production_like: bool = False


class ModeUnavailable(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps(payload) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


@contextmanager
def patched_env(values: dict[str, str]) -> Iterator[None]:
    previous: dict[str, str | None] = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def compact_text(value: str | None) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def normalize_mode(answer_mode: str | None) -> str:
    if answer_mode == "strong":
        return "strong"
    if str(answer_mode or "").startswith("weak"):
        return "weak"
    return "refuse"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    position = (len(ordered) - 1) * pct
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 3)


def build_run_modes() -> list[RunMode]:
    return [
        RunMode(
            run_mode="A_data_plane_baseline",
            label="data-plane baseline",
            env={
                "PERF_DISABLE_LLM": "1",
                "PERF_DISABLE_RERANK": "1",
                "PERF_RETRIEVAL_MODE": "sparse",
            },
            llm_enabled=False,
            required=True,
        ),
        RunMode(
            run_mode="B_retrieval_rerank",
            label="retrieval + rerank",
            env={
                "PERF_DISABLE_LLM": "1",
                "PERF_DISABLE_RERANK": "0",
                "PERF_RETRIEVAL_MODE": "hybrid",
            },
            llm_enabled=False,
        ),
        RunMode(
            run_mode="C_production_like_full_chain",
            label="production-like full chain",
            env={
                "PERF_DISABLE_LLM": "0",
                "PERF_DISABLE_RERANK": "0",
                "PERF_RETRIEVAL_MODE": "hybrid",
            },
            llm_enabled=True,
            production_like=True,
        ),
    ]


def build_query_specs() -> list[QuerySpec]:
    specs: list[QuerySpec] = []

    ahv_v1 = (
        ("何谓太阳病", "太阳病"),
        ("伤寒是什么", "伤寒"),
        ("温病是什么意思", "温病"),
        ("结脉是什么", "结脉"),
        ("霍乱是什么", "霍乱"),
        ("劳复是什么意思", "劳复"),
        ("食复是什么意思", "食复"),
        ("促脉是什么", "促脉"),
        ("弦脉是什么意思", "弦脉"),
        ("滑脉是什么", "滑脉"),
        ("革脉是什么", "革脉"),
        ("血崩是什么", "血崩"),
        ("内虚是什么意思", "内虚"),
        ("痓病是什么", "痓病"),
        ("刚痓是什么", "刚痓"),
        ("柔痓是什么意思", "柔痓"),
    )
    specs.extend(
        QuerySpec(
            query_id=f"ahv_v1_canonical_{index:02d}",
            query=query,
            query_category="ahv_v1_canonical",
            expected_terms=(term,),
            notes="AHV v1 safe primary canonical definition.",
        )
        for index, (query, term) in enumerate(ahv_v1, start=1)
    )

    ahv2 = (
        ("阳明病是什么", "阳明病"),
        ("少阴病是什么意思", "少阴病"),
        ("结胸是什么", "结胸"),
        ("水逆是什么意思", "水逆"),
        ("半表半里证是什么", "半表半里证"),
        ("数脉是什么", "数脉"),
        ("太阴病是什么", "太阴病"),
        ("厥阴病是什么", "厥阴病"),
        ("风湿是什么意思", "风湿"),
        ("湿家是什么", "湿家"),
        ("过经是什么意思", "过经"),
        ("平脉是什么", "平脉"),
        ("毛脉是什么", "毛脉"),
        ("残贼是什么意思", "残贼"),
        ("八邪是什么", "八邪"),
        ("亡血是什么意思", "亡血"),
    )
    specs.extend(
        QuerySpec(
            query_id=f"ahv2_canonical_{index:02d}",
            query=query,
            query_category="ahv2_canonical",
            expected_terms=(term,),
            notes="AHV2 safe primary canonical definition.",
        )
        for index, (query, term) in enumerate(ahv2, start=1)
    )

    cross_batch = (
        ("太阳病和阳明病有什么区别", ("太阳病", "阳明病")),
        ("伤寒和温病有什么区别", ("伤寒", "温病")),
        ("结脉和促脉有什么区别", ("结脉", "促脉")),
        ("劳复和食复一样吗", ("劳复", "食复")),
        ("结胸和水逆有什么不同", ("结胸", "水逆")),
        ("少阴病和厥阴病有什么区别", ("少阴病", "厥阴病")),
        ("太阴病和阳明病有什么区别", ("太阴病", "阳明病")),
        ("数脉和结脉有什么区别", ("数脉", "结脉")),
        ("风湿和湿家一样吗", ("风湿", "湿家")),
        ("半表半里证和过经有什么不同", ("半表半里证", "过经")),
        ("亡血和阳气微一样吗", ("亡血", "阳气微")),
        ("荣气微和卫气衰有什么区别", ("荣气微", "卫气衰")),
        ("平脉和数脉有什么区别", ("平脉", "数脉")),
        ("八邪和残贼有什么区别", ("八邪", "残贼")),
        ("霍乱和伤寒有什么区别", ("霍乱", "伤寒")),
        ("内虚和血崩有什么关系", ("内虚", "血崩")),
        ("刚痓和柔痓有什么区别", ("刚痓", "柔痓")),
        ("痓病和太阳病有什么不同", ("痓病", "太阳病")),
        ("阳明病和少阴病一样吗", ("阳明病", "少阴病")),
        ("水逆和结胸一样吗", ("水逆", "结胸")),
        ("温病和暑病有什么区别", ("温病", "暑病")),
        ("冬温和温病有什么区别", ("冬温", "温病")),
        ("时行寒疫和伤寒有什么不同", ("时行寒疫", "伤寒")),
        ("弦脉和滑脉有什么区别", ("弦脉", "滑脉")),
        ("革脉和结脉有什么区别", ("革脉", "结脉")),
        ("食复和劳复有什么不同", ("食复", "劳复")),
    )
    specs.extend(
        QuerySpec(
            query_id=f"cross_batch_adversarial_{index:02d}",
            query=query,
            query_category="cross_batch_adversarial",
            expected_terms=terms,
            notes="Cross-batch comparison/relationship query must not be hijacked by one definition object.",
        )
        for index, (query, terms) in enumerate(cross_batch, start=1)
    )

    formulas = (
        ("乌梅丸方的条文是什么？", ("乌梅丸",)),
        ("茵陈蒿汤方的条文是什么？", ("茵陈蒿汤",)),
        ("桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？", ("桂枝去芍药汤", "桂枝去芍药加附子汤")),
        ("白虎汤方和白虎加人参汤方的区别是什么？", ("白虎汤", "白虎加人参汤")),
        ("桂枝加附子汤方的条文是什么？", ("桂枝加附子汤",)),
        ("桂枝加厚朴杏子汤方的条文是什么？", ("桂枝加浓朴杏子汤",)),
        ("桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？", ("桂枝加附子汤", "桂枝加浓朴杏子汤")),
        ("四逆加人参汤方的条文是什么？", ("四逆加人参汤",)),
        ("四逆加猪胆汁汤方的条文是什么？", ("四逆加猪胆汁汤",)),
        ("柴胡加芒硝汤方的条文是什么？", ("柴胡加芒硝汤",)),
        ("桂枝加芍药汤方的条文是什么？", ("桂枝加芍药汤",)),
        ("桂枝去桂加茯苓白术汤方的条文是什么？", ("桂枝去桂加茯苓白术汤",)),
        ("小柴胡汤方的条文是什么？", ("小柴胡汤",)),
        ("大承气汤方的条文是什么？", ("大承气汤",)),
        ("小承气汤方和大承气汤方有什么不同？", ("小承气汤", "大承气汤")),
        ("麻黄汤方的条文是什么？", ("麻黄汤",)),
        ("桂枝汤方的条文是什么？", ("桂枝汤",)),
        ("麻黄汤方和桂枝汤方的区别是什么？", ("麻黄汤", "桂枝汤")),
        ("白通汤方的条文是什么？", ("白通汤",)),
        ("白通加猪胆汁汤方和白通汤方有什么不同？", ("白通加猪胆汁汤", "白通汤")),
    )
    specs.extend(
        QuerySpec(
            query_id=f"formula_{index:02d}",
            query=query,
            query_category="formula",
            expected_formula_names=names,
            notes="Formula exact/comparison query.",
        )
        for index, (query, names) in enumerate(formulas, start=1)
    )

    learner_queries = (
        "睡着出汗是什么意思？",
        "四肢不温是什么？",
        "水饮结胸是什么意思？",
        "发汗药是干什么的？",
        "下药是什么意思？",
        "烧针益阳而损阴是什么意思？",
        "发汗后恶寒是什么意思？",
        "胸满是什么意思？",
        "心下悸是什么意思？",
        "小便不利是什么意思？",
        "口苦咽干目眩是什么意思？",
        "头项强痛是什么意思？",
        "不了了是什么意思？",
        "不得眠是什么意思？",
        "心烦是什么意思？",
        "身疼痛是什么意思？",
        "恶寒是什么意思？",
        "发热汗出是什么意思？",
        "脉浮是什么意思？",
        "下利是什么意思？",
        "干呕是什么意思？",
        "咽中痛是什么意思？",
    )
    specs.extend(
        QuerySpec(
            query_id=f"learner_short_{index:02d}",
            query=query,
            query_category="learner_short_normal",
            notes="Learner-facing short or normal user query.",
        )
        for index, query in enumerate(learner_queries, start=1)
    )

    review_only = (
        "神丹是什么意思？",
        "将军是什么意思？",
        "胆瘅是什么意思？",
        "两阳是什么意思？",
        "火劫发汗是什么意思？",
        "寒格是什么意思？",
        "肝乘脾是什么意思？",
        "清邪中上是什么意思？",
        "口苦病是什么意思？",
        "反是什么意思？",
    )
    specs.extend(
        QuerySpec(
            query_id=f"review_only_boundary_{index:02d}",
            query=query,
            query_category="review_only_support_boundary",
            notes="Review-only/support-only boundary query must not become clean primary.",
        )
        for index, query in enumerate(review_only, start=1)
    )

    negatives = (
        "太阳能是什么意思？",
        "复习是什么意思？",
        "劳动合同是什么？",
        "霍乱疫苗是什么？",
        "温度是什么意思？",
        "阳明山在哪里？",
        "少阴影是什么意思？",
        "结胸肌怎么练？",
        "白虎是什么意思？",
        "水逆星座是什么意思？",
    )
    specs.extend(
        QuerySpec(
            query_id=f"negative_modern_{index:02d}",
            query=query,
            query_category="negative_modern_unrelated",
            notes="Modern unrelated or false-friend negative query.",
        )
        for index, query in enumerate(negatives, start=1)
    )

    return specs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full-chain production-like regression v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    parser.add_argument(
        "--modes",
        default="A,B,C",
        help="Comma-separated mode short names to run: A,B,C. Defaults to all.",
    )
    parser.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=None,
        help="Optional timeout override for production-like LLM calls.",
    )
    parser.add_argument(
        "--llm-max-output-tokens",
        type=int,
        default=None,
        help="Optional max output token override for production-like LLM calls.",
    )
    parser.add_argument("--no-llm-preflight", action="store_true", help="Skip C-mode LLM preflight.")
    return parser.parse_args()


def resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "db_path": resolve_project_path(args.db_path),
        "policy_path": resolve_project_path(args.policy_json),
        "cache_dir": resolve_project_path(args.cache_dir),
        "dense_chunks_index": resolve_project_path(args.dense_chunks_index),
        "dense_chunks_meta": resolve_project_path(args.dense_chunks_meta),
        "dense_main_index": resolve_project_path(args.dense_main_index),
        "dense_main_meta": resolve_project_path(args.dense_main_meta),
    }


def make_assembler(
    args: argparse.Namespace,
    paths: dict[str, Path],
    *,
    llm_enabled: bool,
) -> AnswerAssembler:
    if llm_enabled:
        llm_config = load_modelstudio_llm_config(
            enabled_override=True,
            timeout_override=args.llm_timeout_seconds,
            max_output_tokens_override=args.llm_max_output_tokens,
        )
    else:
        llm_config = ModelStudioLLMConfig(
            enabled=False,
            api_key=None,
            model=DEFAULT_MODEL_STUDIO_MODEL,
            base_url=DEFAULT_MODEL_STUDIO_BASE_URL,
        )
    return AnswerAssembler(
        db_path=paths["db_path"],
        policy_path=paths["policy_path"],
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=paths["cache_dir"],
        dense_chunks_index=paths["dense_chunks_index"],
        dense_chunks_meta=paths["dense_chunks_meta"],
        dense_main_index=paths["dense_main_index"],
        dense_main_meta=paths["dense_main_meta"],
        llm_config=llm_config,
    )


def load_definition_registry(db_path: Path) -> dict[str, dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            str(row["concept_id"]): dict(row)
            for row in conn.execute(
                """
                SELECT concept_id, canonical_term, promotion_state, promotion_source_layer,
                       source_confidence, review_only_reason, is_safe_primary_candidate, is_active,
                       primary_evidence_type, primary_evidence_text
                FROM definition_term_registry
                """
            )
        }
    finally:
        conn.close()


def load_formula_registry(db_path: Path) -> dict[str, dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            str(row["formula_id"]): dict(row)
            for row in conn.execute(
                """
                SELECT formula_id, canonical_name, source_confidence, is_active,
                       formula_span_start_passage_id, formula_span_end_passage_id,
                       span_fix_status
                FROM formula_canonical_registry
                """
            )
        }
    finally:
        conn.close()


def canonical_term_to_id(registry: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {row["canonical_term"]: concept_id for concept_id, row in registry.items()}


def canonical_formula_to_id(registry: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {row["canonical_name"]: formula_id for formula_id, row in registry.items()}


def extract_definition_ids_from_items(items: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for item in items:
        record_id = str(item.get("record_id") or "")
        if record_id.startswith("safe:definition_terms:"):
            ids.append(record_id.rsplit(":", 1)[-1])
    return list(dict.fromkeys(ids))


def extract_formula_ids_from_candidates(candidates: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for row in candidates:
        if row.get("formula_id"):
            ids.append(str(row["formula_id"]))
        for formula_id in row.get("formula_candidate_ids") or []:
            ids.append(str(formula_id))
    return list(dict.fromkeys(ids))


def short_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "record_type": row.get("source_object"),
        "record_table": row.get("record_table"),
        "topic_consistency": row.get("topic_consistency"),
        "primary_allowed": row.get("primary_allowed"),
        "combined_score": row.get("combined_score"),
        "rerank_score": row.get("rerank_score"),
        "stage_sources": row.get("stage_sources") or [],
        "matched_terms": row.get("matched_terms") or [],
        "concept_id": row.get("concept_id"),
        "canonical_term": row.get("canonical_term"),
        "formula_id": row.get("formula_id"),
        "canonical_name": row.get("canonical_name"),
        "definition_candidate_ids": row.get("definition_candidate_ids") or [],
        "formula_candidate_ids": row.get("formula_candidate_ids") or [],
        "text_preview": row.get("text_preview") or row.get("retrieval_text", "")[:120],
    }


def short_rerank_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "record_type": row.get("source_object"),
        "topic_consistency": row.get("topic_consistency"),
        "rerank_score": row.get("rerank_score"),
        "combined_score": row.get("combined_score"),
    }


def forbidden_primary_items(primary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": item.get("record_id"),
            "record_type": item.get("record_type"),
            "risk_flags": item.get("risk_flags") or [],
            "title": item.get("title"),
        }
        for item in primary
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES
    ]


def detect_review_only_primary_conflicts(
    primary: list[dict[str, Any]],
    definition_registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for concept_id in extract_definition_ids_from_items(primary):
        row = definition_registry.get(concept_id) or {}
        if row.get("promotion_state") == "review_only" or row.get("source_confidence") == "review_only":
            conflicts.append(
                {
                    "record_id": f"safe:definition_terms:{concept_id}",
                    "concept_id": concept_id,
                    "canonical_term": row.get("canonical_term"),
                    "promotion_state": row.get("promotion_state"),
                }
            )
    return conflicts


def citation_judgement(payload: dict[str, Any]) -> tuple[str, str | None]:
    mode = payload.get("answer_mode")
    citations = payload.get("citations") or []
    primary_ids = {item.get("record_id") for item in payload.get("primary_evidence") or []}
    secondary_review_ids = {
        item.get("record_id")
        for item in (payload.get("secondary_evidence") or []) + (payload.get("review_materials") or [])
    }
    citation_ids = [item.get("record_id") for item in citations]
    if mode == "refuse":
        if citation_ids:
            return "fail: refuse answer emitted citations", "citation_error"
        return "pass: refuse has no citations", None
    if mode == "strong":
        if primary_ids and not citation_ids:
            return "fail: strong answer has primary evidence but no citations", "citation_error"
        if any(record_id not in primary_ids for record_id in citation_ids):
            return "fail: strong citations are not limited to primary evidence", "citation_error"
    elif str(mode or "").startswith("weak"):
        if any(record_id not in secondary_review_ids for record_id in citation_ids):
            return "fail: weak citations do not match secondary/review slots", "citation_error"
    if len(citation_ids) > 8:
        return "review: citation list is broad and should be manually checked for relevance", None
    return "pass: citation slots match answer mode", None


def faithfulness_judgement(payload: dict[str, Any], llm_debug: dict[str, Any]) -> tuple[str, str | None]:
    mode = payload.get("answer_mode")
    answer_text = payload.get("answer_text") or ""
    primary = payload.get("primary_evidence") or []
    secondary = payload.get("secondary_evidence") or []
    review = payload.get("review_materials") or []
    if mode == "strong" and not primary:
        return "fail: strong answer has no primary evidence", "assembler_slot_error"
    if str(mode or "").startswith("weak") and not (secondary or review):
        return "fail: weak answer has no supporting or review evidence", "answer_mode_calibration_error"
    if llm_debug.get("used_llm"):
        evidence_count = len(primary) + len(secondary) + len(review)
        refs = [int(match) for match in re.findall(r"\[E(\d+)\]", answer_text)]
        if refs and max(refs) > evidence_count:
            return "fail: LLM answer references an evidence id outside the evidence pack", "llm_faithfulness_error"
        if review and not primary and re.search(r"可以确定|直接说明|明确就是|足以说明", answer_text):
            return "fail: LLM answer states a review-only boundary too firmly", "llm_faithfulness_error"
    if mode == "refuse":
        return "pass: refuse answer does not assert a book conclusion", None
    return "pass: heuristic evidence-slot faithfulness checks passed", None


def choose_failure_type(existing: list[str | None]) -> str:
    present = {item for item in existing if item and item != "none"}
    for failure_type in FAILURE_TYPE_ORDER:
        if failure_type in present:
            return failure_type
    return "none"


def judge_record(
    spec: QuerySpec,
    payload: dict[str, Any],
    retrieval: dict[str, Any],
    llm_debug: dict[str, Any],
    definition_registry: dict[str, dict[str, Any]],
    formula_name_to_id: dict[str, str],
) -> dict[str, Any]:
    primary = payload.get("primary_evidence") or []
    secondary = payload.get("secondary_evidence") or []
    review = payload.get("review_materials") or []
    answer_mode = str(payload.get("answer_mode") or "")
    mode_family = normalize_mode(answer_mode)
    query_request = retrieval.get("query_request") or {}
    raw_candidates = retrieval.get("raw_candidates") or []
    term_normalization = query_request.get("term_normalization") or {}
    formula_normalization = query_request.get("formula_normalization") or {}
    matched_definition_ids = list(term_normalization.get("concept_ids") or [])
    primary_definition_ids = extract_definition_ids_from_items(primary)
    matched_formula_ids = list(formula_normalization.get("formula_ids") or [])
    raw_formula_ids = extract_formula_ids_from_candidates(raw_candidates[:8])
    expected_concept_ids = [
        concept_id
        for term in spec.expected_terms
        for concept_id, row in definition_registry.items()
        if row.get("canonical_term") == term
    ]
    expected_formula_ids = [formula_name_to_id[name] for name in spec.expected_formula_names if name in formula_name_to_id]
    primary_types = [item.get("record_type") for item in primary]
    forbidden_items = forbidden_primary_items(primary)
    review_conflicts = detect_review_only_primary_conflicts(primary, definition_registry)
    primary_text = compact_text(" ".join((item.get("title") or "") + " " + (item.get("snippet") or "") for item in primary))
    secondary_text = compact_text(" ".join((item.get("title") or "") + " " + (item.get("snippet") or "") for item in secondary))
    review_text = compact_text(" ".join((item.get("title") or "") + " " + (item.get("snippet") or "") for item in review))
    answer_text = compact_text(payload.get("answer_text") or "")
    failure_reasons: list[str] = []
    failure_types: list[str | None] = []

    if forbidden_items:
        failure_reasons.append("primary evidence contains forbidden raw/review source types")
        failure_types.append("assembler_slot_error")

    if review_conflicts:
        failure_reasons.append("review-only definition object entered primary evidence")
        failure_types.append("review_only_boundary_error")

    citation_status, citation_failure = citation_judgement(payload)
    if citation_failure:
        failure_reasons.append(citation_status)
        failure_types.append(citation_failure)

    faithfulness_status, faithfulness_failure = faithfulness_judgement(payload, llm_debug)
    if faithfulness_failure:
        failure_reasons.append(faithfulness_status)
        failure_types.append(faithfulness_failure)

    if spec.query_category in {"ahv_v1_canonical", "ahv2_canonical"}:
        expected_hit = bool(set(expected_concept_ids) & set(matched_definition_ids + primary_definition_ids))
        if not expected_hit:
            failure_reasons.append("canonical definition query did not hit expected definition object")
            failure_types.append("retrieval_miss")
        if mode_family != "strong":
            failure_reasons.append("canonical definition query did not produce strong answer")
            failure_types.append("answer_mode_calibration_error" if expected_hit else "retrieval_miss")
        if primary and expected_concept_ids and not set(expected_concept_ids) & set(primary_definition_ids):
            failure_reasons.append("canonical definition primary does not contain expected concept")
            failure_types.append("assembler_slot_error")

    elif spec.query_category == "cross_batch_adversarial":
        expected_primary_terms = [term for term in spec.expected_terms if compact_text(term) in primary_text]
        singleton_definition_primary = len(primary_definition_ids) == 1 and bool(set(primary_definition_ids) & set(expected_concept_ids))
        if mode_family == "strong" and len(expected_primary_terms) < 2:
            failure_reasons.append("strong comparison/relationship answer lacks primary coverage for both sides")
            failure_types.append("non_definition_intent_hijack" if singleton_definition_primary else "answer_mode_calibration_error")
        if singleton_definition_primary and len(spec.expected_terms) >= 2:
            failure_reasons.append("cross-batch relationship query was hijacked by one definition object")
            failure_types.append("non_definition_intent_hijack")

    elif spec.query_category == "formula":
        expected_count = len(expected_formula_ids)
        matched_expected = set(expected_formula_ids) & set(matched_formula_ids + raw_formula_ids)
        primary_expected_names = [name for name in spec.expected_formula_names if compact_text(name) in primary_text]
        if expected_count and len(matched_expected) < expected_count:
            failure_reasons.append("formula normalization/raw candidates missed one or more expected formulas")
            failure_types.append("data_layer_bad_alias")
        if mode_family != "strong":
            failure_reasons.append("formula exact/comparison query did not produce strong answer")
            failure_types.append("answer_mode_calibration_error" if matched_expected else "retrieval_miss")
        if expected_count > 1 and mode_family == "strong" and len(primary_expected_names) < expected_count:
            failure_reasons.append("formula comparison strong answer lacks primary coverage for both formula names")
            failure_types.append("formula_comparison_primary_noise")
        bad_formula_candidates = [
            short_candidate(row)
            for row in raw_candidates[:8]
            if row.get("topic_consistency") in BAD_FORMULA_TOPICS and row.get("primary_allowed")
        ]
        if bad_formula_candidates:
            failure_reasons.append("bad formula anchor remained primary-allowed in top candidates")
            failure_types.append("formula_comparison_primary_noise")

    elif spec.query_category == "learner_short_normal":
        if mode_family == "refuse":
            failure_reasons.append("normal learner query refused instead of offering a conservative book-grounded answer")
            failure_types.append("retrieval_miss")
        if answer_mode == "strong" and not primary:
            failure_reasons.append("strong learner answer has no primary evidence")
            failure_types.append("answer_mode_calibration_error")

    elif spec.query_category == "review_only_support_boundary":
        if mode_family == "strong":
            failure_reasons.append("review-only/support-only boundary query produced strong answer")
            failure_types.append("review_only_boundary_error")
        review_terms = [term for term in ("神丹", "将军", "胆瘅", "两阳", "火劫发汗", "寒格", "肝乘脾", "清邪中上", "口苦病", "反") if term in spec.query]
        if review_terms and any(compact_text(term) in primary_text for term in review_terms):
            failure_reasons.append("review-only/support-only surface appears in primary evidence")
            failure_types.append("review_only_boundary_error")

    elif spec.query_category == "negative_modern_unrelated":
        if mode_family == "strong":
            failure_reasons.append("negative/modern unrelated query produced strong answer")
            failure_types.append("negative_query_false_positive")
        if primary:
            failure_reasons.append("negative/modern unrelated query has primary evidence")
            failure_types.append("negative_query_false_positive")

    if answer_mode == "strong" and review and not primary:
        failure_reasons.append("strong answer uses review material without primary support")
        failure_types.append("answer_mode_calibration_error")

    pass_record = not failure_reasons
    failure_type = choose_failure_type(failure_types)
    if not pass_record and failure_type == "none":
        failure_type = "answer_mode_calibration_error"

    return {
        "pass": pass_record,
        "faithfulness_judgement": faithfulness_status,
        "mode_judgement": "pass: answer_mode is consistent with query category" if not any("answer" in reason or "strong" in reason or "refused" in reason for reason in failure_reasons) else "fail: " + "; ".join(failure_reasons),
        "citation_judgement": citation_status,
        "failure_type": failure_type,
        "failure_reasons": failure_reasons,
        "expected_concept_ids": expected_concept_ids,
        "expected_formula_ids": expected_formula_ids,
        "primary_definition_ids": primary_definition_ids,
        "review_only_primary_conflicts": review_conflicts,
    }


def run_single_query(
    assembler: AnswerAssembler,
    spec: QuerySpec,
    mode: RunMode,
    definition_registry: dict[str, dict[str, Any]],
    formula_name_to_id: dict[str, str],
) -> dict[str, Any]:
    captured_retrievals: list[dict[str, Any]] = []
    original_retrieve: Callable[..., dict[str, Any]] = assembler.engine.retrieve

    def capture_retrieve(query_text: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original_retrieve(query_text, *args, **kwargs)
        captured_retrievals.append(result)
        return result

    assembler.engine.retrieve = capture_retrieve  # type: ignore[method-assign]
    trace = new_request_trace(request_path=f"/regression/{RUN_ID}/{mode.run_mode}", query=spec.query)
    token = set_current_trace(trace)
    payload: dict[str, Any] | None = None
    query_error: str | None = None
    try:
        payload = assembler.assemble(spec.query)
        trace.status_code = 200
    except Exception as exc:  # pragma: no cover - runtime artifact captures the error
        trace.status_code = 500
        query_error = f"{type(exc).__name__}: {exc}"
    finally:
        latency_ms = trace.total_ms()
        stage_durations_ms = dict(trace.stage_durations_ms)
        reset_current_trace(token)
        assembler.engine.retrieve = original_retrieve  # type: ignore[method-assign]

    diagnostic_retrieval_used = False
    retrieval = next(
        (
            item
            for item in captured_retrievals
            if (item.get("query_request") or {}).get("query_text") == spec.query
        ),
        None,
    )
    if retrieval is None:
        retrieval = original_retrieve(spec.query)
        diagnostic_retrieval_used = True

    llm_debug = dict(assembler.get_last_llm_debug() or {})
    if payload is None:
        payload = {
            "query": spec.query,
            "answer_mode": "error",
            "answer_text": "",
            "primary_evidence": [],
            "secondary_evidence": [],
            "review_materials": [],
            "citations": [],
        }

    judgement = judge_record(spec, payload, retrieval, llm_debug, definition_registry, formula_name_to_id)
    raw_top5 = [short_candidate(row) for row in (retrieval.get("raw_candidates") or [])[:5]]
    trace_rerank = ((retrieval.get("retrieval_trace") or {}).get("rerank_top_candidates") or [])[:5]
    rerank_top5 = [short_rerank_candidate(row) for row in trace_rerank]
    query_request = retrieval.get("query_request") or {}
    term_normalization = query_request.get("term_normalization") or {}
    formula_normalization = query_request.get("formula_normalization") or {}
    primary = payload.get("primary_evidence") or []
    secondary = payload.get("secondary_evidence") or []
    review = payload.get("review_materials") or []

    if query_error:
        judgement["pass"] = False
        judgement["failure_type"] = "assembler_slot_error"
        judgement.setdefault("failure_reasons", []).append(query_error)

    return {
        "query_id": spec.query_id,
        "query": spec.query,
        "query_category": spec.query_category,
        "run_mode": mode.run_mode,
        "answer_mode": payload.get("answer_mode"),
        "answer_text": payload.get("answer_text") or "",
        "primary_ids": [item.get("record_id") for item in primary],
        "secondary_ids": [item.get("record_id") for item in secondary],
        "review_ids": [item.get("record_id") for item in review],
        "primary_record_types": [item.get("record_type") for item in primary],
        "forbidden_primary_items": forbidden_primary_items(primary),
        "matched_formula_ids": list(formula_normalization.get("formula_ids") or []),
        "matched_definition_concept_ids": list(term_normalization.get("concept_ids") or []),
        "query_focus_source": query_request.get("query_focus_source"),
        "term_normalization": term_normalization,
        "formula_normalization": formula_normalization,
        "raw_top5_candidates": raw_top5,
        "rerank_top5_candidates": rerank_top5,
        "llm_used": bool(llm_debug.get("used_llm")),
        "llm_debug": {
            key: value
            for key, value in llm_debug.items()
            if key not in {"base_url"} and key != "api_key"
        },
        "latency_ms": round(latency_ms, 3),
        "stage_durations_ms": stage_durations_ms,
        "faithfulness_judgement": judgement["faithfulness_judgement"],
        "mode_judgement": judgement["mode_judgement"],
        "citation_judgement": judgement["citation_judgement"],
        "failure_type": judgement["failure_type"],
        "failure_reasons": judgement["failure_reasons"],
        "pass": bool(judgement["pass"]),
        "expected_concept_ids": judgement["expected_concept_ids"],
        "expected_formula_ids": judgement["expected_formula_ids"],
        "primary_definition_ids": judgement["primary_definition_ids"],
        "review_only_primary_conflicts": judgement["review_only_primary_conflicts"],
        "diagnostic_retrieval_used": diagnostic_retrieval_used,
    }


def preflight_llm(assembler: AnswerAssembler) -> tuple[bool, dict[str, Any]]:
    payload = assembler.assemble("何谓太阳病")
    debug = dict(assembler.get_last_llm_debug() or {})
    return bool(payload.get("answer_mode") != "refuse" and debug.get("used_llm")), {
        "answer_mode": payload.get("answer_mode"),
        "llm_attempted": bool(debug.get("attempted")),
        "llm_used": bool(debug.get("used_llm")),
        "fallback_used": bool(debug.get("fallback_used")),
        "skipped_reason": debug.get("skipped_reason"),
        "fallback_reason": debug.get("fallback_reason"),
    }


def run_mode(
    args: argparse.Namespace,
    paths: dict[str, Path],
    mode: RunMode,
    specs: list[QuerySpec],
    definition_registry: dict[str, dict[str, Any]],
    formula_name_to_id: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    started_at = now_utc()
    status: dict[str, Any] = {
        "run_mode": mode.run_mode,
        "label": mode.label,
        "required": mode.required,
        "production_like": mode.production_like,
        "env": mode.env,
        "started_at_utc": started_at,
        "completed_at_utc": None,
        "status": "started",
        "unavailable_reason": None,
        "llm_preflight": None,
    }

    with patched_env(mode.env):
        try:
            assembler = make_assembler(args, paths, llm_enabled=mode.llm_enabled)
        except (LLMConfigError, SystemExit, Exception) as exc:
            status["status"] = "unavailable"
            status["unavailable_reason"] = f"{type(exc).__name__}: {exc}"
            status["completed_at_utc"] = now_utc()
            if mode.required:
                raise ModeUnavailable(status["unavailable_reason"]) from exc
            return records, status

        try:
            if mode.production_like and not args.no_llm_preflight:
                try:
                    preflight_ok, preflight = preflight_llm(assembler)
                except Exception as exc:  # pragma: no cover - runtime artifact captures the error
                    preflight_ok = False
                    preflight = {"error": f"{type(exc).__name__}: {exc}"}
                status["llm_preflight"] = preflight
                if not preflight_ok:
                    status["status"] = "unavailable"
                    status["unavailable_reason"] = "LLM preflight did not produce used_llm=true for a non-refuse query."
                    status["completed_at_utc"] = now_utc()
                    return records, status

            for index, spec in enumerate(specs, start=1):
                print(f"[{mode.run_mode}] {index:03d}/{len(specs)} {spec.query_id}: {spec.query}", flush=True)
                record = run_single_query(
                    assembler=assembler,
                    spec=spec,
                    mode=mode,
                    definition_registry=definition_registry,
                    formula_name_to_id=formula_name_to_id,
                )
                records.append(record)
        finally:
            assembler.close()

    status["completed_at_utc"] = now_utc()
    if mode.production_like:
        non_refuse = [record for record in records if record.get("answer_mode") != "refuse"]
        if non_refuse and not any(record.get("llm_used") for record in non_refuse):
            status["status"] = "completed_without_successful_llm"
            status["unavailable_reason"] = "No non-refuse production-like record had llm_used=true."
        else:
            status["status"] = "completed"
    else:
        status["status"] = "completed"
    return records, status


def mark_cross_mode_rerank_regressions(records: list[dict[str, Any]]) -> None:
    by_query: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        by_query[record["query_id"]][record["run_mode"]] = record

    for modes in by_query.values():
        baseline = modes.get("A_data_plane_baseline")
        rerank = modes.get("B_retrieval_rerank")
        if not baseline or not rerank:
            continue
        if baseline.get("pass") and not rerank.get("pass"):
            rerank["failure_type"] = "rerank_regression"
            reasons = rerank.setdefault("failure_reasons", [])
            if "B mode failed while A mode passed for the same query" not in reasons:
                reasons.append("B mode failed while A mode passed for the same query")


def summarize_metrics(
    specs: list[QuerySpec],
    records: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
    repair_queue: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    completed_modes = [status["run_mode"] for status in statuses if str(status.get("status", "")).startswith("completed")]
    records_by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        records_by_mode[record["run_mode"]].append(record)

    latency_p50 = {
        mode: round(median([record["latency_ms"] for record in mode_records]), 3) if mode_records else 0.0
        for mode, mode_records in records_by_mode.items()
    }
    latency_p95 = {
        mode: percentile([record["latency_ms"] for record in mode_records], 0.95)
        for mode, mode_records in records_by_mode.items()
    }
    fail_records = [record for record in records if not record.get("pass")]
    failure_type_counts = Counter(record["failure_type"] for record in fail_records)
    failure_type_count_total = sum(failure_type_counts.values())
    missing_failure_type_count = sum(
        1
        for record in fail_records
        if not record.get("failure_type") or record.get("failure_type") == "none"
    )
    wrong_definition_primary_total = sum(
        1
        for record in records
        if record["failure_type"] in {"non_definition_intent_hijack", "assembler_slot_error"}
        and record.get("primary_definition_ids")
    )
    formula_bad_anchor_total = sum(
        1
        for record in records
        if record["query_category"] == "formula"
        and any(
            candidate.get("topic_consistency") in BAD_FORMULA_TOPICS
            for candidate in record.get("raw_top5_candidates") or []
        )
    )
    return {
        "query_count": len(specs),
        "run_mode_count": len(completed_modes),
        "completed_modes": completed_modes,
        "status_by_mode": {status["run_mode"]: status["status"] for status in statuses},
        "pass_count_by_mode": {
            mode: sum(1 for record in mode_records if record.get("pass")) for mode, mode_records in records_by_mode.items()
        },
        "fail_count_by_mode": {
            mode: sum(1 for record in mode_records if not record.get("pass"))
            for mode, mode_records in records_by_mode.items()
        },
        "forbidden_primary_total": sum(len(record.get("forbidden_primary_items") or []) for record in records),
        "formula_bad_anchor_total": formula_bad_anchor_total,
        "review_only_primary_conflict_total": sum(
            len(record.get("review_only_primary_conflicts") or []) for record in records
        ),
        "wrong_definition_primary_total": wrong_definition_primary_total,
        "non_definition_intent_hijack_total": failure_type_counts["non_definition_intent_hijack"],
        "rerank_regression_count": failure_type_counts["rerank_regression"],
        "llm_faithfulness_error_count": failure_type_counts["llm_faithfulness_error"],
        "answer_mode_calibration_error_count": failure_type_counts["answer_mode_calibration_error"],
        "citation_error_count": failure_type_counts["citation_error"],
        "failure_record_count": len(fail_records),
        "failure_type_count_total": failure_type_count_total,
        "missing_failure_type_count": missing_failure_type_count,
        "failure_metrics_consistent": len(fail_records) == failure_type_count_total
        and missing_failure_type_count == 0,
        "failure_type_counts": dict(sorted(failure_type_counts.items())),
        "p0_repair_count": len(repair_queue["P0"]),
        "p1_repair_count": len(repair_queue["P1"]),
        "p2_observation_count": len(repair_queue["P2"]),
        "latency_p50_by_mode": latency_p50,
        "latency_p95_by_mode": latency_p95,
    }


def build_repair_queue(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    failures = [record for record in records if not record.get("pass")]
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for record in failures:
        key = (record["query_id"], record["failure_type"])
        existing = deduped.get(key)
        if existing is None or record["run_mode"] == "C_production_like_full_chain":
            deduped[key] = record

    p0: list[dict[str, Any]] = []
    p1: list[dict[str, Any]] = []
    p2: list[dict[str, Any]] = []

    for record in deduped.values():
        entry = {
            "query_id": record["query_id"],
            "query": record["query"],
            "query_category": record["query_category"],
            "run_mode": record["run_mode"],
            "failure_type": record["failure_type"],
            "primary_ids": record.get("primary_ids") or [],
            "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
            "matched_formula_ids": record.get("matched_formula_ids") or [],
            "failure_reasons": record.get("failure_reasons") or [],
            "recommended_next_action": recommend_next_action(record),
        }
        if record["failure_type"] in {
            "review_only_boundary_error",
            "negative_query_false_positive",
            "formula_comparison_primary_noise",
        } and len(p0) < 10:
            p0.append(entry)
        elif record["failure_type"] in DATA_LAYER_FAILURE_TYPES | {"retrieval_miss"} and len(p1) < 30:
            p1.append(entry)
        else:
            p2.append(entry)

    if len(p0) > 10:
        p2.extend(p0[10:])
        p0 = p0[:10]
    return {"P0": p0, "P1": p1, "P2": p2}


def recommend_next_action(record: dict[str, Any]) -> str:
    failure_type = record.get("failure_type")
    category = record.get("query_category")
    if failure_type == "review_only_boundary_error":
        return "Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view."
    if failure_type == "negative_query_false_positive":
        return "Add or tighten alias/intent guard so modern false-friend query does not select book primary evidence."
    if failure_type == "formula_comparison_primary_noise":
        return "Audit formula registry aliases/spans and comparison primary bundle for both formula anchors."
    if failure_type == "data_layer_bad_alias":
        return "Audit exact alias coverage for the expected formula/definition object without adding broad contains surfaces."
    if failure_type == "retrieval_miss" and category == "learner_short_normal":
        return "Check whether a learner-safe definition/explanation object exists; if not, queue object/span audit rather than reopening raw full passages."
    if failure_type == "rerank_regression":
        return "Compare A/B raw and rerank top candidates; preserve safe object priority through rerank or assembler slot selection."
    if failure_type == "llm_faithfulness_error":
        return "Keep data fixed; inspect LLM answer_text against evidence pack and validator/fallback behavior in a separate prompt/validator round."
    if failure_type == "citation_error":
        return "Inspect citation slot normalization for this branch; do not change evidence eligibility until citation mismatch is localized."
    return "Manual audit: inspect primary/secondary/review slots and decide whether this is data-layer, rerank, assembler, or LLM work."


def build_query_set_payload(specs: list[QuerySpec]) -> dict[str, Any]:
    counts = Counter(spec.query_category for spec in specs)
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "query_count": len(specs),
        "query_category_counts": dict(sorted(counts.items())),
        "queries": [asdict(spec) for spec in specs],
    }


def build_latency_payload(records: list[dict[str, Any]], statuses: list[dict[str, Any]]) -> dict[str, Any]:
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_mode[record["run_mode"]].append(record)
    modes: dict[str, Any] = {}
    for mode, mode_records in sorted(by_mode.items()):
        latencies = [record["latency_ms"] for record in mode_records]
        stage_totals: dict[str, list[float]] = defaultdict(list)
        for record in mode_records:
            for stage, value in (record.get("stage_durations_ms") or {}).items():
                stage_totals[stage].append(float(value))
        modes[mode] = {
            "count": len(mode_records),
            "latency_p50_ms": round(median(latencies), 3) if latencies else 0.0,
            "latency_p95_ms": percentile(latencies, 0.95),
            "latency_max_ms": round(max(latencies), 3) if latencies else 0.0,
            "stage_p50_ms": {
                stage: round(median(values), 3)
                for stage, values in sorted(stage_totals.items())
                if values
            },
            "stage_p95_ms": {
                stage: percentile(values, 0.95)
                for stage, values in sorted(stage_totals.items())
                if values
            },
        }
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "mode_statuses": statuses,
        "modes": modes,
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["_none_"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", "<br>") for cell in row) + " |")
    return lines


def render_query_set_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Full Chain Query Set v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- query_count: `{payload['query_count']}`",
        "",
        "## Category Counts",
        "",
    ]
    lines.extend(md_table(["category", "count"], [[key, value] for key, value in payload["query_category_counts"].items()]))
    lines.extend(["", "## Queries", ""])
    lines.extend(
        md_table(
            ["query_id", "category", "query", "expected_terms", "expected_formula_names"],
            [
                [
                    item["query_id"],
                    item["query_category"],
                    item["query"],
                    ", ".join(item["expected_terms"]),
                    ", ".join(item["expected_formula_names"]),
                ]
                for item in payload["queries"]
            ],
        )
    )
    return lines


def render_results_md(payload: dict[str, Any]) -> list[str]:
    metrics = payload["metrics"]
    status_rows = [
        [
            status["run_mode"],
            status["status"],
            status.get("unavailable_reason") or "",
        ]
        for status in payload["mode_statuses"]
    ]
    lines = [
        "# Full Chain Regression Results v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- query_count: `{metrics['query_count']}`",
        f"- run_mode_count: `{metrics['run_mode_count']}`",
        "",
        "## Mode Status",
        "",
    ]
    lines.extend(md_table(["mode", "status", "reason"], status_rows))
    lines.extend(["", "## Metrics", ""])
    metric_rows = [[key, json.dumps(value, ensure_ascii=False)] for key, value in metrics.items() if key != "status_by_mode"]
    lines.extend(md_table(["metric", "value"], metric_rows))
    lines.extend(["", "## Failed Records", ""])
    failures = [record for record in payload["records"] if not record.get("pass")]
    lines.extend(
        md_table(
            ["mode", "query_id", "category", "answer_mode", "failure_type", "reasons"],
            [
                [
                    record["run_mode"],
                    record["query_id"],
                    record["query_category"],
                    record["answer_mode"],
                    record["failure_type"],
                    "; ".join(record.get("failure_reasons") or [])[:220],
                ]
                for record in failures[:80]
            ],
        )
    )
    return lines


def render_failures_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Full Chain Failure Cases v1",
        "",
        f"- failure_count: `{payload['failure_count']}`",
        "",
    ]
    by_type = Counter(item["failure_type"] for item in payload["failures"])
    lines.extend(md_table(["failure_type", "count"], [[key, value] for key, value in sorted(by_type.items())]))
    lines.extend(["", "## Cases", ""])
    lines.extend(
        md_table(
            ["mode", "query_id", "query", "category", "failure_type", "primary_ids", "reasons"],
            [
                [
                    item["run_mode"],
                    item["query_id"],
                    item["query"],
                    item["query_category"],
                    item["failure_type"],
                    ", ".join(item.get("primary_ids") or []),
                    "; ".join(item.get("failure_reasons") or [])[:260],
                ]
                for item in payload["failures"]
            ],
        )
    )
    return lines


def render_repair_queue_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Data Layer Repair Queue v1",
        "",
        f"- p0_repair_count: `{len(payload['P0'])}`",
        f"- p1_repair_count: `{len(payload['P1'])}`",
        f"- p2_observation_count: `{len(payload['P2'])}`",
    ]
    for priority in ("P0", "P1", "P2"):
        lines.extend(["", f"## {priority}", ""])
        lines.extend(
            md_table(
                ["query_id", "mode", "failure_type", "query", "next_action"],
                [
                    [
                        item["query_id"],
                        item["run_mode"],
                        item["failure_type"],
                        item["query"],
                        item["recommended_next_action"],
                    ]
                    for item in payload[priority]
                ],
            )
        )
    return lines


def render_latency_md(payload: dict[str, Any]) -> list[str]:
    rows = []
    for mode, data in payload["modes"].items():
        rows.append([mode, data["count"], data["latency_p50_ms"], data["latency_p95_ms"], data["latency_max_ms"]])
    lines = ["# Latency Snapshot v1", ""]
    lines.extend(md_table(["mode", "count", "p50_ms", "p95_ms", "max_ms"], rows))
    lines.extend(["", "## Stage P50", ""])
    for mode, data in payload["modes"].items():
        lines.extend([f"### {mode}", ""])
        lines.extend(md_table(["stage", "p50_ms"], [[stage, value] for stage, value in data["stage_p50_ms"].items()]))
        lines.append("")
    return lines


def render_report_md(
    results_payload: dict[str, Any],
    failures_payload: dict[str, Any],
    repair_queue: dict[str, list[dict[str, Any]]],
) -> list[str]:
    metrics = results_payload["metrics"]
    lines = [
        "# Full Chain Production-like Regression v1",
        "",
        "## Scope",
        "",
        "This run evaluates whether prior data-plane upgrades still hold after rerank, assembler slotting, citations, and LLM answer_text rendering. It does not add AHV3 objects, change prompts, change frontend code, change API payload contract, or reopen raw full passages into primary evidence.",
        "",
        "## Mode Completion",
        "",
    ]
    lines.extend(
        md_table(
            ["mode", "status", "reason"],
            [
                [status["run_mode"], status["status"], status.get("unavailable_reason") or ""]
                for status in results_payload["mode_statuses"]
            ],
        )
    )
    lines.extend(["", "## Quantitative Metrics", ""])
    lines.extend(
        md_table(
            ["metric", "value"],
            [
                ["query_count", metrics["query_count"]],
                ["run_mode_count", metrics["run_mode_count"]],
                ["pass_count_by_mode", json.dumps(metrics["pass_count_by_mode"], ensure_ascii=False)],
                ["fail_count_by_mode", json.dumps(metrics["fail_count_by_mode"], ensure_ascii=False)],
                ["forbidden_primary_total", metrics["forbidden_primary_total"]],
                ["formula_bad_anchor_total", metrics["formula_bad_anchor_total"]],
                ["review_only_primary_conflict_total", metrics["review_only_primary_conflict_total"]],
                ["wrong_definition_primary_total", metrics["wrong_definition_primary_total"]],
                ["non_definition_intent_hijack_total", metrics["non_definition_intent_hijack_total"]],
                ["rerank_regression_count", metrics["rerank_regression_count"]],
                ["llm_faithfulness_error_count", metrics["llm_faithfulness_error_count"]],
                ["answer_mode_calibration_error_count", metrics["answer_mode_calibration_error_count"]],
                ["citation_error_count", metrics["citation_error_count"]],
                ["failure_record_count", metrics["failure_record_count"]],
                ["failure_type_count_total", metrics["failure_type_count_total"]],
                ["missing_failure_type_count", metrics["missing_failure_type_count"]],
                ["failure_metrics_consistent", metrics["failure_metrics_consistent"]],
                ["p0_repair_count", metrics["p0_repair_count"]],
                ["p1_repair_count", metrics["p1_repair_count"]],
                ["latency_p50_by_mode", json.dumps(metrics["latency_p50_by_mode"], ensure_ascii=False)],
                ["latency_p95_by_mode", json.dumps(metrics["latency_p95_by_mode"], ensure_ascii=False)],
            ],
        )
    )
    lines.extend(["", "## Major Failure Types", ""])
    lines.extend(md_table(["failure_type", "count"], [[key, value] for key, value in metrics["failure_type_counts"].items()]))
    for priority, title in (("P0", "P0 Immediate Data-layer Repairs"), ("P1", "P1 Next Batch Data-layer Repairs"), ("P2", "P2 Observations")):
        lines.extend(["", f"## {title}", ""])
        lines.extend(
            md_table(
                ["query_id", "mode", "failure_type", "query", "next_action"],
                [
                    [item["query_id"], item["run_mode"], item["failure_type"], item["query"], item["recommended_next_action"]]
                    for item in repair_queue[priority][:30]
                ],
            )
        )
    lines.extend(
        [
            "",
            "## Artifact Index",
            "",
            "- `artifacts/full_chain_regression/full_chain_query_set_v1.json`",
            "- `artifacts/full_chain_regression/full_chain_regression_results_v1.json`",
            "- `artifacts/full_chain_regression/full_chain_failure_cases_v1.json`",
            "- `artifacts/full_chain_regression/data_layer_repair_queue_v1.json`",
            "- `artifacts/full_chain_regression/latency_snapshot_v1.json`",
        ]
    )
    return lines


def selected_modes(args: argparse.Namespace) -> list[RunMode]:
    requested = {part.strip().upper() for part in args.modes.split(",") if part.strip()}
    short_to_mode = {"A": "A_data_plane_baseline", "B": "B_retrieval_rerank", "C": "C_production_like_full_chain"}
    requested_ids = {short_to_mode.get(item, item) for item in requested}
    return [mode for mode in build_run_modes() if mode.run_mode in requested_ids]


def main() -> int:
    args = parse_args()
    paths = resolve_paths(args)
    specs = build_query_specs()
    definition_registry = load_definition_registry(paths["db_path"])
    formula_registry = load_formula_registry(paths["db_path"])
    formula_name_to_id = canonical_formula_to_id(formula_registry)
    modes = selected_modes(args)

    query_set_payload = build_query_set_payload(specs)
    write_json(QUERY_SET_JSON, query_set_payload)
    write_md(QUERY_SET_MD, render_query_set_md(query_set_payload))

    all_records: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    for mode in modes:
        print(f"[mode:start] {mode.run_mode}", flush=True)
        records, status = run_mode(
            args=args,
            paths=paths,
            mode=mode,
            specs=specs,
            definition_registry=definition_registry,
            formula_name_to_id=formula_name_to_id,
        )
        all_records.extend(records)
        statuses.append(status)
        print(f"[mode:done] {mode.run_mode} status={status['status']} records={len(records)}", flush=True)

    mark_cross_mode_rerank_regressions(all_records)
    repair_queue = build_repair_queue(all_records)
    metrics = summarize_metrics(specs, all_records, statuses, repair_queue)
    results_payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "query_count": len(specs),
        "mode_statuses": statuses,
        "metrics": metrics,
        "records": all_records,
    }
    failures_payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "failure_count": sum(1 for record in all_records if not record.get("pass")),
        "failures": [record for record in all_records if not record.get("pass")],
    }
    repair_payload = {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        **repair_queue,
    }
    latency_payload = build_latency_payload(all_records, statuses)

    write_json(RESULTS_JSON, results_payload)
    write_md(RESULTS_MD, render_results_md(results_payload))
    write_json(FAILURES_JSON, failures_payload)
    write_md(FAILURES_MD, render_failures_md(failures_payload))
    write_json(REPAIR_QUEUE_JSON, repair_payload)
    write_md(REPAIR_QUEUE_MD, render_repair_queue_md(repair_payload))
    write_json(LATENCY_JSON, latency_payload)
    write_md(LATENCY_MD, render_latency_md(latency_payload))
    write_md(REPORT_MD, render_report_md(results_payload, failures_payload, repair_queue))

    if metrics["query_count"] < 100:
        raise SystemExit("query_count below required minimum")
    if "A_data_plane_baseline" not in metrics["completed_modes"]:
        raise SystemExit("required mode A did not complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
