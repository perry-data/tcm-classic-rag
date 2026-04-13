#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.answers.assembler import (
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    FORMULA_EFFECT_CONTEXT_BAD_PREFIX_HINTS,
    FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS,
    FORMULA_EFFECT_CONTEXT_NOISE_HINTS,
    FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS,
    FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG,
    AnswerAssembler,
    json_dumps,
)
from backend.retrieval.minimal import resolve_project_path


DEFAULT_AUDIT_JSON_OUT = "artifacts/experiments/formula_effect_bulk_audit_v1.json"
DEFAULT_SUMMARY_MD_OUT = "artifacts/experiments/formula_effect_bulk_audit_summary_v1.md"
DEFAULT_TAXONOMY_MD_OUT = "docs/design/formula_effect_failure_taxonomy_v2.md"
DEFAULT_DECISION_MD_OUT = "docs/patch_notes/formula_effect_bulk_audit_decision_v1.md"

DEFAULT_QUERY_TEMPLATES = (
    "{formula_name}有什么作用",
    "{formula_name}主治什么",
    "{formula_name}用于什么情况",
)

POSITIVE_PATTERN_LABELS = {"direct_context_main_selected", "stable_positive"}
SUSPICIOUS_STRONG_PATTERN_LABELS = {
    "short_tail_fragment_primary",
    "cross_chapter_bridge_primary",
    "formula_title_or_composition_over_primary",
    "false_strong_without_direct_context",
}
NON_FIXABLE_WITHIN_CURRENT_SCOPE = {
    "review_only_should_remain_weak",
    "raw_recall_missing_direct_context",
}


@dataclass(frozen=True)
class VariantSpec:
    label: str
    formula_effect_primary_v1_enabled: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a full-book formula_effect bulk audit.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta JSON.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta JSON.")
    parser.add_argument(
        "--audit-json-out",
        default=DEFAULT_AUDIT_JSON_OUT,
        help="Where to write the bulk audit JSON.",
    )
    parser.add_argument(
        "--summary-md-out",
        default=DEFAULT_SUMMARY_MD_OUT,
        help="Where to write the bulk audit summary markdown.",
    )
    parser.add_argument(
        "--taxonomy-md-out",
        default=DEFAULT_TAXONOMY_MD_OUT,
        help="Where to write the failure taxonomy markdown.",
    )
    parser.add_argument(
        "--decision-md-out",
        default=DEFAULT_DECISION_MD_OUT,
        help="Where to write the audit decision markdown.",
    )
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=("before", "after", "env"),
        default=("before", "after"),
        help="Audit variants to run. Use env to respect the current env flag state.",
    )
    parser.add_argument(
        "--limit-formulas",
        type=int,
        default=None,
        help="Optional cap for smoke runs.",
    )
    return parser.parse_args()


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def parse_risk_flags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value else []
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
    return []


def current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def render_variant_specs(variant_names: tuple[str, ...] | list[str]) -> list[VariantSpec]:
    variants: list[VariantSpec] = []
    for name in variant_names:
        if name == "before":
            variants.append(VariantSpec(label="before", formula_effect_primary_v1_enabled=False))
        elif name == "after":
            variants.append(VariantSpec(label="after", formula_effect_primary_v1_enabled=True))
        else:
            env_value = str(int(bool_flag_from_env())).strip()
            variants.append(
                VariantSpec(
                    label=f"env({env_value})",
                    formula_effect_primary_v1_enabled=bool_flag_from_env(),
                )
            )
    return variants


def bool_flag_from_env() -> bool:
    raw_value = str(os.environ.get(FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG, "")).strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def detect_route(assembler: AnswerAssembler, query_text: str) -> dict[str, Any]:
    if assembler._detect_policy_refusal(query_text) is not None:
        return {"route": "policy_refusal"}
    comparison_plan = assembler._detect_comparison_query(query_text)
    if comparison_plan is not None:
        return {
            "route": "comparison_query",
            "comparison_valid": bool(comparison_plan.get("valid")),
            "reason": comparison_plan.get("reason"),
        }
    if assembler._detect_formula_composition_query(query_text) is not None:
        return {"route": "formula_composition_query"}
    formula_effect_plan = assembler._detect_formula_effect_query(query_text)
    if formula_effect_plan is not None:
        return {
            "route": "formula_effect_query",
            "canonical_name": formula_effect_plan.get("canonical_name"),
        }
    if assembler._detect_definition_outline_query(query_text) is not None:
        return {"route": "definition_outline_query"}
    if assembler._detect_definition_priority_query(query_text) is not None:
        return {"route": "definition_priority_query"}
    if assembler.get_last_comparison_debug() is not None:
        return {"route": "comparison_debug_state"}
    if assembler.get_last_definition_priority_debug() is not None:
        return {"route": "definition_priority_debug_state"}
    from backend.strategies.general_question import detect_general_question

    if detect_general_question(query_text) is not None:
        return {"route": "general_question"}
    return {"route": "standard"}


def build_formula_effect_payload_from_bundle(
    assembler: AnswerAssembler,
    *,
    query_text: str,
    canonical_name: str,
    bundle: dict[str, Any],
) -> dict[str, Any]:
    answer_mode = assembler._determine_formula_effect_mode(bundle)
    if answer_mode == "strong":
        primary = [
            assembler._build_evidence_item(
                row,
                display_role="primary",
                title_override=f"{canonical_name} · 直接条文依据",
            )
            for row in bundle["support_rows"]
        ]
        secondary = [
            assembler._build_evidence_item(
                row,
                display_role="secondary",
                title_override=f"{canonical_name} · 方文",
            )
            for row in bundle["formula_rows"]
        ]
        review = [
            assembler._build_evidence_item(row, display_role="review")
            for row in bundle["review_rows"]
        ]
    elif answer_mode == "weak_with_review_notice":
        primary = []
        secondary = [
            assembler._build_evidence_item(
                row,
                display_role="secondary",
                title_override=f"{canonical_name} · 方文",
                risk_flags_override=ordered_unique(
                    parse_risk_flags(row.get("risk_flag")) + ["formula_effect_mode_demoted"]
                ),
            )
            for row in bundle["formula_rows"]
        ]
        review = [
            assembler._build_evidence_item(row, display_role="review")
            for row in bundle["review_rows"]
        ]
    else:
        primary = []
        secondary = []
        review = []

    answer_text = assembler._build_formula_effect_answer_text(
        canonical_name,
        bundle,
        answer_mode=answer_mode,
    )
    review_notice = assembler._build_review_notice(answer_mode)
    disclaimer = assembler._build_disclaimer(answer_mode, bool(secondary), bool(review))
    citations = assembler._build_formula_effect_citations(answer_mode, primary, secondary, review)
    refuse_reason = assembler._build_refuse_reason(answer_mode)
    followups = assembler._build_followups(answer_mode)
    return assembler._compose_payload(
        query_text=query_text,
        answer_mode=answer_mode,
        answer_text=answer_text,
        primary=primary,
        secondary=secondary,
        review=review,
        review_notice=review_notice,
        disclaimer=disclaimer,
        refuse_reason=refuse_reason,
        suggested_followup_questions=followups,
        citations=citations,
    )


def fetch_full_texts(assembler: AnswerAssembler, items: list[dict[str, Any]]) -> list[str]:
    texts: list[str] = []
    for item in items:
        texts.append(assembler._fetch_record_meta(item["record_id"]).get("retrieval_text", ""))
    return texts


def get_row_text(assembler: AnswerAssembler, row: dict[str, Any] | None) -> str:
    if not row:
        return ""
    return str(row.get("retrieval_text") or assembler._fetch_record_meta(row["record_id"]).get("retrieval_text") or "")


def classify_context_row(
    assembler: AnswerAssembler,
    *,
    canonical_name: str,
    formula_chapter_id: str | None,
    row: dict[str, Any] | None,
) -> dict[str, Any]:
    if not row:
        return {
            "record_id": None,
            "context_clause": "",
            "contains_direct_context": False,
            "is_formula_title_or_composition": False,
            "is_short_tail_fragment": False,
            "is_cross_chapter_bridge": False,
            "symptom_hits": 0,
            "context_length": 0,
            "score": None,
        }

    row_text = get_row_text(assembler, row)
    context_meta = assembler._analyze_formula_effect_context_row_v1(
        {
            **row,
            "retrieval_text": row_text,
        },
        canonical_name=canonical_name,
        formula_chapter_id=formula_chapter_id,
    )
    row_mentions = {mention["canonical_name"] for mention in assembler._find_formula_mentions(row_text)}
    score, _ = assembler._score_formula_effect_context_row_v1(
        {
            **row,
            "retrieval_text": row_text,
        },
        canonical_name=canonical_name,
        preferred_chapter_id=formula_chapter_id,
        row_mentions=row_mentions,
    )
    return {
        "record_id": row.get("record_id"),
        "context_clause": context_meta["context_clause"],
        "contains_direct_context": context_meta["contains_direct_context"],
        "is_formula_title_or_composition": context_meta["is_formula_title_or_composition"],
        "is_short_tail_fragment": context_meta["is_short_tail_fragment"],
        "is_cross_chapter_bridge": context_meta["is_cross_chapter_bridge"],
        "symptom_hits": context_meta["symptom_hits"],
        "context_length": context_meta["context_length"],
        "score": round(score, 3),
    }


def expand_raw_candidates(
    assembler: AnswerAssembler,
    raw_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for candidate in raw_candidates:
        record_id = candidate["record_id"]
        if record_id not in seen_ids:
            expanded.append(candidate)
            seen_ids.add(record_id)
        if candidate.get("record_table") != "records_chunks":
            continue
        for backref in assembler.engine._fetch_chunk_backrefs(record_id):
            if backref["record_id"] in seen_ids:
                continue
            expanded.append(
                {
                    **backref,
                    "source_object": "main_passages",
                    "record_table": "records_main_passages",
                    "retrieval_text": backref.get("text") or backref.get("retrieval_text") or "",
                }
            )
            seen_ids.add(backref["record_id"])
    return expanded


def determine_pattern_label(
    *,
    route: str,
    answer_mode: str,
    primary_meta: dict[str, Any],
    direct_context_exists_in_raw_candidates: bool,
    direct_context_main_exists_in_raw_candidates: bool,
    direct_context_exists_only_in_review: bool,
) -> str:
    if route != "formula_effect_query":
        return "route_miss_not_formula_effect"
    if answer_mode == "strong":
        if primary_meta["is_formula_title_or_composition"]:
            return "formula_title_or_composition_over_primary"
        if primary_meta["is_short_tail_fragment"]:
            return "short_tail_fragment_primary"
        if primary_meta["is_cross_chapter_bridge"]:
            return "cross_chapter_bridge_primary"
        if not primary_meta["contains_direct_context"]:
            return "false_strong_without_direct_context"
        return "direct_context_main_selected"
    if answer_mode == "weak_with_review_notice":
        if direct_context_main_exists_in_raw_candidates:
            return "weak_main_direct_context_not_lifted"
        if direct_context_exists_only_in_review:
            return "review_only_should_remain_weak"
        if not direct_context_exists_in_raw_candidates:
            return "raw_recall_missing_direct_context"
        return "weak_without_clear_bucket"
    if direct_context_main_exists_in_raw_candidates:
        return "refuse_despite_main_direct_context"
    if direct_context_exists_only_in_review:
        return "review_only_should_remain_weak"
    return "raw_recall_missing_direct_context"


def build_audit_row(
    assembler: AnswerAssembler,
    *,
    variant: VariantSpec,
    query_text: str,
    canonical_name: str,
    formula_meta: dict[str, Any],
    route_meta: dict[str, Any],
    bundle: dict[str, Any],
    payload: dict[str, Any],
    raw_query_retrieval: dict[str, Any],
) -> dict[str, Any]:
    formula_chapter_id = formula_meta.get("chapter_id")
    primary_items = payload["primary_evidence"]
    secondary_items = payload["secondary_evidence"]
    review_items = payload["review_materials"]

    primary_row = None
    if primary_items:
        primary_row = {
            **assembler.engine.record_by_id[primary_items[0]["record_id"]],
            "source_object": assembler.engine.record_by_id[primary_items[0]["record_id"]]["source_object"],
        }
    primary_meta = classify_context_row(
        assembler,
        canonical_name=canonical_name,
        formula_chapter_id=formula_chapter_id,
        row=primary_row,
    )

    expanded_raw_rows = expand_raw_candidates(assembler, raw_query_retrieval["raw_candidates"])
    direct_raw_rows: list[dict[str, Any]] = []
    for row in expanded_raw_rows:
        if row.get("source_object") not in {"main_passages", "passages", "ambiguous_passages"}:
            continue
        if canonical_name not in {mention["canonical_name"] for mention in assembler._find_formula_mentions(get_row_text(assembler, row))}:
            continue
        row_meta = classify_context_row(
            assembler,
            canonical_name=canonical_name,
            formula_chapter_id=formula_chapter_id,
            row=row,
        )
        if row_meta["contains_direct_context"]:
            direct_raw_rows.append(
                {
                    "record_id": row["record_id"],
                    "source_object": row.get("source_object"),
                    "chapter_id": row.get("chapter_id"),
                    "meta": row_meta,
                }
            )

    direct_context_exists_in_raw_candidates = bool(direct_raw_rows)
    direct_context_main_rows = [row for row in direct_raw_rows if row["source_object"] == "main_passages"]
    direct_context_review_rows = [
        row for row in direct_raw_rows if row["source_object"] in {"passages", "ambiguous_passages"}
    ]
    direct_context_main_exists_in_raw_candidates = bool(direct_context_main_rows)
    direct_context_exists_only_in_review = (not direct_context_main_exists_in_raw_candidates) and bool(
        direct_context_review_rows
    )
    pattern_label = determine_pattern_label(
        route=route_meta["route"],
        answer_mode=payload["answer_mode"],
        primary_meta=primary_meta,
        direct_context_exists_in_raw_candidates=direct_context_exists_in_raw_candidates,
        direct_context_main_exists_in_raw_candidates=direct_context_main_exists_in_raw_candidates,
        direct_context_exists_only_in_review=direct_context_exists_only_in_review,
    )
    primary_reasonable = payload["answer_mode"] == "strong" and pattern_label == "direct_context_main_selected"
    primary_suspicious = payload["answer_mode"] == "strong" and pattern_label in SUSPICIOUS_STRONG_PATTERN_LABELS
    weak_due_to_assembler_issue = payload["answer_mode"] == "weak_with_review_notice" and bool(
        direct_context_main_exists_in_raw_candidates
    )
    weak_reason_bucket = None
    if payload["answer_mode"] == "weak_with_review_notice":
        if weak_due_to_assembler_issue:
            weak_reason_bucket = "assembler_issue"
        elif direct_context_exists_only_in_review:
            weak_reason_bucket = "review_only"
        elif not direct_context_exists_in_raw_candidates:
            weak_reason_bucket = "raw_recall_missing"
        else:
            weak_reason_bucket = "other"

    primary_chapter_id = primary_items[0]["chapter_id"] if primary_items else None
    return {
        "variant": variant.label,
        "formula_effect_primary_rules_v1_enabled": variant.formula_effect_primary_v1_enabled,
        "formula_name": canonical_name,
        "query": query_text,
        "answer_mode": payload["answer_mode"],
        "route": route_meta["route"],
        "primary_evidence_ids": [item["record_id"] for item in primary_items],
        "primary_evidence_text": fetch_full_texts(assembler, primary_items),
        "primary_chapter_id": primary_chapter_id,
        "formula_chapter_id": formula_chapter_id,
        "secondary_evidence_ids": [item["record_id"] for item in secondary_items],
        "review_material_ids": [item["record_id"] for item in review_items],
        "answer_text": payload["answer_text"],
        "raw_top_candidate_ids": [row["record_id"] for row in raw_query_retrieval["raw_candidates"]],
        "whether_primary_contains_direct_context": primary_meta["contains_direct_context"],
        "whether_primary_is_formula_title_or_composition": primary_meta["is_formula_title_or_composition"],
        "whether_primary_looks_like_short_tail_fragment": primary_meta["is_short_tail_fragment"],
        "whether_primary_is_cross_chapter_bridge": primary_meta["is_cross_chapter_bridge"],
        "whether_direct_context_exists_in_raw_candidates": direct_context_exists_in_raw_candidates,
        "whether_direct_context_exists_only_in_review": direct_context_exists_only_in_review,
        "preliminary_pattern_label": pattern_label,
        "is_primary_reasonable": primary_reasonable,
        "is_primary_suspicious": primary_suspicious,
        "weak_reason_bucket": weak_reason_bucket,
        "weak_due_to_assembler_issue": weak_due_to_assembler_issue,
        "raw_direct_context_candidate_ids": [row["record_id"] for row in direct_raw_rows],
        "raw_direct_context_main_candidate_ids": [row["record_id"] for row in direct_context_main_rows],
        "raw_direct_context_review_candidate_ids": [row["record_id"] for row in direct_context_review_rows],
        "bundle_context_record_id": bundle["context_row"]["record_id"] if bundle.get("context_row") else None,
        "bundle_context_source": bundle.get("context_source"),
        "bundle_context_clause": bundle["facts"].get("context_clause"),
        "primary_context_clause": primary_meta["context_clause"],
    }


def build_formula_level_rows(query_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        grouped[row["formula_name"]].append(row)

    formula_rows: list[dict[str, Any]] = []
    for formula_name, rows in sorted(grouped.items()):
        rows_sorted = sorted(rows, key=lambda item: item["query"])
        mode_counts = Counter(row["answer_mode"] for row in rows_sorted)
        pattern_counts = Counter(row["preliminary_pattern_label"] for row in rows_sorted)
        weak_reason_counts = Counter(row["weak_reason_bucket"] for row in rows_sorted if row["weak_reason_bucket"])
        representative = rows_sorted[0]
        if len(mode_counts) == 1:
            formula_mode = representative["answer_mode"]
        else:
            formula_mode = "mixed"

        if formula_mode == "strong":
            if all(row["is_primary_reasonable"] for row in rows_sorted):
                formula_bucket = "strong_reasonable"
            elif any(row["is_primary_suspicious"] for row in rows_sorted):
                formula_bucket = "strong_suspicious"
            else:
                formula_bucket = "strong_other"
        elif formula_mode == "weak_with_review_notice":
            if all(row["weak_due_to_assembler_issue"] for row in rows_sorted):
                formula_bucket = "weak_assembler_issue"
            elif all(row["whether_direct_context_exists_only_in_review"] for row in rows_sorted):
                formula_bucket = "weak_review_only"
            elif all(not row["whether_direct_context_exists_in_raw_candidates"] for row in rows_sorted):
                formula_bucket = "weak_raw_recall_missing"
            else:
                formula_bucket = "weak_other"
        elif formula_mode == "refuse":
            if any(row["whether_direct_context_exists_only_in_review"] for row in rows_sorted):
                formula_bucket = "refuse_review_only"
            elif all(not row["whether_direct_context_exists_in_raw_candidates"] for row in rows_sorted):
                formula_bucket = "refuse_raw_recall_missing"
            else:
                formula_bucket = "refuse_other"
        else:
            formula_bucket = "mixed"

        formula_rows.append(
            {
                "formula_name": formula_name,
                "formula_mode": formula_mode,
                "formula_bucket": formula_bucket,
                "query_count": len(rows_sorted),
                "query_mode_counts": dict(mode_counts),
                "pattern_counts": dict(pattern_counts),
                "weak_reason_counts": dict(weak_reason_counts),
                "template_consistent": len(mode_counts) == 1 and len(pattern_counts) == 1,
                "representative_query": representative["query"],
                "representative_pattern_label": representative["preliminary_pattern_label"],
            }
        )
    return formula_rows


def sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key, _ in sorted(counter.items(), key=lambda item: (-item[1], item[0]))}


def build_variant_summary(
    *,
    variant: VariantSpec,
    query_rows: list[dict[str, Any]],
    formula_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    query_mode_counts = Counter(row["answer_mode"] for row in query_rows)
    formula_mode_counts = Counter(row["formula_mode"] for row in formula_rows)
    pattern_counts = Counter(row["preliminary_pattern_label"] for row in query_rows)
    formula_bucket_counts = Counter(row["formula_bucket"] for row in formula_rows)

    strong_reasonable_formulas = [
        row["formula_name"] for row in formula_rows if row["formula_bucket"] == "strong_reasonable"
    ]
    strong_suspicious_formulas = [
        row["formula_name"] for row in formula_rows if row["formula_bucket"] == "strong_suspicious"
    ]
    weak_assembler_formulas = [
        row["formula_name"] for row in formula_rows if row["formula_bucket"] == "weak_assembler_issue"
    ]
    weak_review_only_formulas = [
        row["formula_name"] for row in formula_rows if row["formula_bucket"] == "weak_review_only"
    ]
    weak_raw_recall_missing_formulas = [
        row["formula_name"] for row in formula_rows if row["formula_bucket"] in {"weak_raw_recall_missing", "refuse_raw_recall_missing"}
    ]
    weak_other_formulas = [
        row["formula_name"] for row in formula_rows if row["formula_bucket"] == "weak_other"
    ]

    failure_pattern_counts = Counter(
        row["preliminary_pattern_label"]
        for row in query_rows
        if row["preliminary_pattern_label"] not in POSITIVE_PATTERN_LABELS
    )
    top_failure_patterns = [
        {"pattern_label": label, "query_count": count}
        for label, count in failure_pattern_counts.most_common(5)
    ]
    fixable_pattern_counts = Counter(
        {
            label: count
            for label, count in failure_pattern_counts.items()
            if label not in NON_FIXABLE_WITHIN_CURRENT_SCOPE
        }
    )
    top_fixable_failure_patterns = [
        {"pattern_label": label, "query_count": count}
        for label, count in fixable_pattern_counts.most_common(5)
    ]
    return {
        "variant": variant.label,
        "formula_effect_primary_rules_v1_enabled": variant.formula_effect_primary_v1_enabled,
        "formula_count": len(formula_rows),
        "query_count": len(query_rows),
        "query_mode_counts": sorted_counter(query_mode_counts),
        "formula_mode_counts": sorted_counter(formula_mode_counts),
        "pattern_counts": sorted_counter(pattern_counts),
        "failure_pattern_counts": sorted_counter(failure_pattern_counts),
        "formula_bucket_counts": sorted_counter(formula_bucket_counts),
        "primary_reasonable_query_count": sum(1 for row in query_rows if row["is_primary_reasonable"]),
        "primary_suspicious_query_count": sum(1 for row in query_rows if row["is_primary_suspicious"]),
        "review_only_weak_query_count": sum(
            1 for row in query_rows if row["preliminary_pattern_label"] == "review_only_should_remain_weak"
        ),
        "raw_recall_missing_query_count": sum(
            1 for row in query_rows if row["preliminary_pattern_label"] == "raw_recall_missing_direct_context"
        ),
        "assembler_weak_query_count": sum(
            1 for row in query_rows if row["preliminary_pattern_label"] == "weak_main_direct_context_not_lifted"
        ),
        "strong_reasonable_formulas": strong_reasonable_formulas,
        "strong_suspicious_formulas": strong_suspicious_formulas,
        "weak_assembler_formulas": weak_assembler_formulas,
        "weak_review_only_formulas": weak_review_only_formulas,
        "weak_raw_recall_missing_formulas": weak_raw_recall_missing_formulas,
        "weak_other_formulas": weak_other_formulas,
        "top_failure_patterns": top_failure_patterns,
        "top_fixable_failure_patterns": top_fixable_failure_patterns,
    }


def build_before_after_delta(variant_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    by_label = {payload["summary"]["variant"]: payload for payload in variant_payloads}
    before = by_label.get("before")
    after = by_label.get("after")
    if before is None or after is None:
        return {}

    delta_keys = (
        "primary_reasonable_query_count",
        "primary_suspicious_query_count",
        "review_only_weak_query_count",
        "raw_recall_missing_query_count",
        "assembler_weak_query_count",
    )
    delta = {
        key: after["summary"][key] - before["summary"][key]
        for key in delta_keys
    }

    before_formula_map = {
        row["formula_name"]: row
        for row in before["formula_rows"]
    }
    after_formula_map = {
        row["formula_name"]: row
        for row in after["formula_rows"]
    }
    mode_transitions = Counter()
    suspicious_to_reasonable: list[str] = []
    reasonable_to_suspicious: list[str] = []
    for formula_name, after_row in after_formula_map.items():
        before_row = before_formula_map.get(formula_name)
        if before_row is None:
            continue
        mode_transitions[f"{before_row['formula_bucket']} -> {after_row['formula_bucket']}"] += 1
        if before_row["formula_bucket"] == "strong_suspicious" and after_row["formula_bucket"] == "strong_reasonable":
            suspicious_to_reasonable.append(formula_name)
        if before_row["formula_bucket"] == "strong_reasonable" and after_row["formula_bucket"] == "strong_suspicious":
            reasonable_to_suspicious.append(formula_name)
    return {
        "metric_delta": delta,
        "formula_bucket_transitions": sorted_counter(mode_transitions),
        "suspicious_to_reasonable_formulas": suspicious_to_reasonable,
        "reasonable_to_suspicious_formulas": reasonable_to_suspicious,
    }


def render_formula_list(formulas: list[str]) -> str:
    if not formulas:
        return "_none_"
    return "、".join(formulas)


def render_summary_markdown(
    *,
    audit_payload: dict[str, Any],
) -> str:
    variants = audit_payload["variants"]
    after_payload = next((variant for variant in variants if variant["summary"]["variant"] == "after"), variants[0])
    after_summary = after_payload["summary"]
    before_after_delta = audit_payload.get("before_after_delta") or {}

    lines = [
        "# formula_effect_bulk_audit_summary_v1",
        "",
        "## 扫描设置",
        "",
        f"- 支持的 query 模板数：`{audit_payload['query_template_count']}`",
        f"- 全书可识别方剂总数：`{audit_payload['formula_count']}`",
        f"- 生成 query 总数（全部 variant 合计）：`{audit_payload['total_query_count']}`",
        f"- 当前系统口径：`after`（`{FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG}=1`）",
        "",
        "## 当前系统全景（after）",
        "",
        f"- 批量覆盖的方剂总数：`{after_summary['formula_count']}`",
        f"- 批量 query 总数：`{after_summary['query_count']}`",
        f"- strong / weak / refuse（query 级）：`{after_summary['query_mode_counts'].get('strong', 0)}` / `{after_summary['query_mode_counts'].get('weak_with_review_notice', 0)}` / `{after_summary['query_mode_counts'].get('refuse', 0)}`",
        f"- strong / weak / refuse（formula 级）：`{after_summary['formula_mode_counts'].get('strong', 0)}` / `{after_summary['formula_mode_counts'].get('weak_with_review_notice', 0)}` / `{after_summary['formula_mode_counts'].get('refuse', 0)}`",
        f"- primary 合理的数量（query 级）：`{after_summary['primary_reasonable_query_count']}`",
        f"- primary 可疑的数量（query 级）：`{after_summary['primary_suspicious_query_count']}`",
        f"- review-only weak 的数量（query 级）：`{after_summary['review_only_weak_query_count']}`",
        f"- raw recall 缺失的数量（query 级）：`{after_summary['raw_recall_missing_query_count']}`",
        f"- weak 且更像 assembler 问题的数量（query 级）：`{after_summary['assembler_weak_query_count']}`",
        "",
        "## 方剂分组（after）",
        "",
        f"- 已经 strong 且 primary 合理：{render_formula_list(after_summary['strong_reasonable_formulas'])}",
        f"- strong 但 primary 可疑（假强）：{render_formula_list(after_summary['strong_suspicious_formulas'])}",
        f"- weak 且更像 assembler 问题：{render_formula_list(after_summary['weak_assembler_formulas'])}",
        f"- weak 且应视为 review-only：{render_formula_list(after_summary['weak_review_only_formulas'])}",
        f"- weak/refuse 且更像 raw recall 缺失：{render_formula_list(after_summary['weak_raw_recall_missing_formulas'])}",
        f"- weak 但模板间原因不完全一致：{render_formula_list(after_summary['weak_other_formulas'])}",
        "",
        "## Failure Pattern 统计（after，query 级）",
        "",
    ]

    for label, count in after_summary["failure_pattern_counts"].items():
        lines.append(f"- `{label}`：`{count}`")

    lines.extend(
        [
            "",
            "## 最值得优先修的前 3 类问题",
            "",
        ]
    )
    if not after_summary["top_fixable_failure_patterns"]:
        lines.append("- 当前没有明显落在 assembler 可修范围内的高频问题。")
    for item in after_summary["top_fixable_failure_patterns"][:3]:
        lines.append(f"- `{item['pattern_label']}`：`{item['query_count']}`")

    if before_after_delta:
        lines.extend(
            [
                "",
                "## Before / After 变化",
                "",
            ]
        )
        for key, value in before_after_delta["metric_delta"].items():
            lines.append(f"- `{key}` delta：`{value}`")
        if before_after_delta.get("suspicious_to_reasonable_formulas"):
            lines.append(
                f"- 从可疑 strong 转为合理 strong 的方剂：{render_formula_list(before_after_delta['suspicious_to_reasonable_formulas'])}"
            )
        if before_after_delta.get("reasonable_to_suspicious_formulas"):
            lines.append(
                f"- 从合理 strong 回退为可疑 strong 的方剂：{render_formula_list(before_after_delta['reasonable_to_suspicious_formulas'])}"
            )

    return "\n".join(lines) + "\n"


def render_taxonomy_markdown(*, audit_payload: dict[str, Any]) -> str:
    after_payload = next((variant for variant in audit_payload["variants"] if variant["summary"]["variant"] == "after"), audit_payload["variants"][0])
    pattern_counts = after_payload["summary"]["pattern_counts"]
    lines = [
        "# formula_effect_failure_taxonomy_v2",
        "",
        "本 taxonomy 面向《伤寒论》全书级 formula_effect 批量审计，而不是个案解释。",
        "",
        "## direct_context_main_selected",
        "",
        "- 定义：primary 直接落在能表达使用语境的 `main_passages` 条文上，且不是方题、组成或短残片。",
        "- 识别特征：`answer_mode=strong`，`whether_primary_contains_direct_context=true`，`whether_primary_is_formula_title_or_composition=false`，`whether_primary_looks_like_short_tail_fragment=false`，`whether_primary_is_cross_chapter_bridge=false`。",
        "- 是否主要是 assembler 问题：否，这是当前理想状态。",
        "- 是否主要是 raw recall 问题：否。",
        "- 后续是否值得修：不作为失败项修复，只作为正样本基线。",
        f"- 本轮 query 计数：`{pattern_counts.get('direct_context_main_selected', 0)}`",
        "",
        "## short_tail_fragment_primary",
        "",
        "- 定义：primary 虽然命中了提及该方的条文，但上下文只剩很短的承接片段，无法自然回答“有什么作用”。",
        "- 识别特征：`answer_mode=strong`，`whether_primary_looks_like_short_tail_fragment=true`；常见于 `宜`、`与`、`当`、`欲解外` 这类尾部动作词残留。",
        "- 是否主要是 assembler 问题：是，主要是 primary 选择和 context clause 抽取的问题。",
        "- 是否主要是 raw recall 问题：通常不是，raw 里往往已经有更完整候选。",
        "- 后续是否值得修：值得，高优先级。",
        f"- 本轮 query 计数：`{pattern_counts.get('short_tail_fragment_primary', 0)}`",
        "",
        "## cross_chapter_bridge_primary",
        "",
        "- 定义：primary 选到跨章承接或桥接条文，形式上可回答，但不是该方最自然的直接使用语境。",
        "- 识别特征：`answer_mode=strong` 且 `whether_primary_is_cross_chapter_bridge=true`。",
        "- 是否主要是 assembler 问题：是，属于 chapter 偏好和 primary ranking 问题。",
        "- 是否主要是 raw recall 问题：通常不是，raw/corpus 往往已经能找到同方正文语境。",
        "- 后续是否值得修：值得，高优先级。",
        f"- 本轮 query 计数：`{pattern_counts.get('cross_chapter_bridge_primary', 0)}`",
        "",
        "## formula_title_or_composition_over_primary",
        "",
        "- 定义：作用类 query 的 primary 被方题或组成条文抢占，答案退化成“方文/组成直出”。",
        "- 识别特征：`whether_primary_is_formula_title_or_composition=true`。",
        "- 是否主要是 assembler 问题：是，属于 evidence slot 选择错误。",
        "- 是否主要是 raw recall 问题：通常不是。",
        "- 后续是否值得修：值得，但优先级取决于出现频次。",
        f"- 本轮 query 计数：`{pattern_counts.get('formula_title_or_composition_over_primary', 0)}`",
        "",
        "## review_only_should_remain_weak",
        "",
        "- 定义：直接使用语境只稳定出现在 `passages` / `ambiguous_passages` 等 review 材料里，当前保持 weak 是正确保守行为。",
        "- 识别特征：`answer_mode=weak_with_review_notice` 且 `whether_direct_context_exists_only_in_review=true`。",
        "- 是否主要是 assembler 问题：不是，assembler 应保持保守，不应误抬成 strong。",
        "- 是否主要是 raw recall 问题：也不完全是，更多是当前证据层级限制。",
        "- 后续是否值得修：短期不建议在 assembler 层硬抬，除非未来允许更高等级证据来源。",
        f"- 本轮 query 计数：`{pattern_counts.get('review_only_should_remain_weak', 0)}`",
        "",
        "## raw_recall_missing_direct_context",
        "",
        "- 定义：query 级 raw candidates 中根本没有直接使用语境，因此 assembler 没有足够素材组织 strong。",
        "- 识别特征：`whether_direct_context_exists_in_raw_candidates=false`，对应 weak/refuse。",
        "- 是否主要是 assembler 问题：否。",
        "- 是否主要是 raw recall 问题：是，属于召回上限。",
        "- 后续是否值得修：值得，但前提是允许改 raw retrieval；本轮约束下不应继续深挖。",
        f"- 本轮 query 计数：`{pattern_counts.get('raw_recall_missing_direct_context', 0)}`",
        "",
        "## false_strong_without_direct_context",
        "",
        "- 定义：系统给出了 `strong`，但 primary 并不真正提供直接使用语境，因此属于“假 strong”。",
        "- 识别特征：`answer_mode=strong` 且 `whether_primary_contains_direct_context=false`，同时又不属于更具体的方题/短尾/跨章标签。",
        "- 是否主要是 assembler 问题：是。",
        "- 是否主要是 raw recall 问题：通常不是。",
        "- 后续是否值得修：值得，但应先看它是否能被更具体标签吸收。",
        f"- 本轮 query 计数：`{pattern_counts.get('false_strong_without_direct_context', 0)}`",
        "",
        "## stable_positive",
        "",
        "- 定义：formula 级多模板结果稳定为 strong，且 primary 一直合理，可视为当前 formula_effect 的稳定正样本。",
        "- 识别特征：formula 级 `strong_reasonable` 且模板结果一致。",
        "- 是否主要是 assembler 问题：否。",
        "- 是否主要是 raw recall 问题：否。",
        "- 后续是否值得修：不作为失败项修复，应纳入回归基线。",
        "",
        "## 补充模式：weak_main_direct_context_not_lifted",
        "",
        "- 定义：query raw candidates 里已经能看到 `main_passages` 直接语境，但最终仍落成 weak。",
        "- 识别特征：`answer_mode=weak_with_review_notice` 且 `raw_direct_context_main_candidate_ids` 非空。",
        "- 是否主要是 assembler 问题：是，这是 weak 中最值得单独抽出来看的 assembler 失配类。",
        "- 是否主要是 raw recall 问题：否，至少不是 query 级 raw recall 不足。",
        "- 后续是否值得修：若计数显著，值得优先修。",
        f"- 本轮 query 计数：`{pattern_counts.get('weak_main_direct_context_not_lifted', 0)}`",
    ]
    return "\n".join(lines) + "\n"


def render_decision_markdown(*, audit_payload: dict[str, Any]) -> str:
    after_payload = next((variant for variant in audit_payload["variants"] if variant["summary"]["variant"] == "after"), audit_payload["variants"][0])
    after_summary = after_payload["summary"]
    top_failure_patterns = after_summary["top_failure_patterns"]
    top_fixable_failure_patterns = after_summary["top_fixable_failure_patterns"]
    biggest_failure = top_failure_patterns[0]["pattern_label"] if top_failure_patterns else "none"
    biggest_fixable_failure = top_fixable_failure_patterns[0]["pattern_label"] if top_fixable_failure_patterns else "none"
    should_continue = biggest_fixable_failure != "none"
    if should_continue:
        recommendation = "继续 formula_effect"
        reason = "虽然全量失败里可能有大量 review-only / raw recall 限制，但仍存在可观的 assembler 级失配，继续修还有明确收益。"
    else:
        recommendation = "切换其他主线"
        reason = "当前失败主因已主要受 raw recall 或证据层级边界限制，继续在 formula_effect assembler 层深挖收益有限。"

    lines = [
        "# formula_effect_bulk_audit_decision_v1",
        "",
        "## 是否值得继续深挖",
        "",
        f"- 建议：`{recommendation}`",
        f"- 判断依据：{reason}",
        "",
        "## 若继续修，下一轮应只修哪个最大类问题",
        "",
    ]
    if top_failure_patterns:
        lines.append(
            f"- 下一轮只建议集中修：`{biggest_fixable_failure}`"
        )
    else:
        lines.append("- 当前没有显著失败模式，不建议继续在 formula_effect 上投入。")

    lines.extend(
        [
            "",
            "## 若不值得继续修，理由是什么",
            "",
            "- 当失败主因主要落在 `raw_recall_missing_direct_context` 或 `review_only_should_remain_weak` 时，本轮约束下无法通过 assembler 小修带来结构性收益。",
            "",
            "## 明确建议",
            "",
            f"- 当前建议：`{recommendation}`",
            f"- 当前最大 failure pattern（全量）：`{biggest_failure}`",
            f"- 当前最大可修 failure pattern：`{biggest_fixable_failure}`",
            f"- strong 但 primary 可疑（query 级）：`{after_summary['primary_suspicious_query_count']}`",
            f"- review-only weak（query 级）：`{after_summary['review_only_weak_query_count']}`",
            f"- raw recall 缺失（query 级）：`{after_summary['raw_recall_missing_query_count']}`",
            f"- assembler weak（query 级）：`{after_summary['assembler_weak_query_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    cache_dir = resolve_project_path(args.cache_dir)
    dense_chunks_index = resolve_project_path(args.dense_chunks_index)
    dense_chunks_meta = resolve_project_path(args.dense_chunks_meta)
    dense_main_index = resolve_project_path(args.dense_main_index)
    dense_main_meta = resolve_project_path(args.dense_main_meta)
    audit_json_out = resolve_project_path(args.audit_json_out)
    summary_md_out = resolve_project_path(args.summary_md_out)
    taxonomy_md_out = resolve_project_path(args.taxonomy_md_out)
    decision_md_out = resolve_project_path(args.decision_md_out)

    for output_path in (audit_json_out, summary_md_out, taxonomy_md_out, decision_md_out):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    assembler = AnswerAssembler(
        db_path=db_path,
        policy_path=policy_path,
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=cache_dir,
        dense_chunks_index=dense_chunks_index,
        dense_chunks_meta=dense_chunks_meta,
        dense_main_index=dense_main_index,
        dense_main_meta=dense_main_meta,
    )
    try:
        formula_names = sorted(assembler._formula_catalog)
        if args.limit_formulas is not None:
            formula_names = formula_names[: args.limit_formulas]

        variants = render_variant_specs(list(args.variants))
        route_cache: dict[str, dict[str, Any]] = {}
        raw_query_cache: dict[str, dict[str, Any]] = {}
        all_query_rows: list[dict[str, Any]] = []
        variant_payloads: list[dict[str, Any]] = []

        for variant in variants:
            assembler.formula_effect_primary_prioritization_enabled = variant.formula_effect_primary_v1_enabled
            variant_query_rows: list[dict[str, Any]] = []
            variant_formula_rows: list[dict[str, Any]] = []

            for formula_name in formula_names:
                formula_meta = assembler._formula_catalog[formula_name]
                bundle = assembler._build_formula_bundle(
                    formula_name,
                    formula_effect_primary_v1=variant.formula_effect_primary_v1_enabled,
                )
                for template in DEFAULT_QUERY_TEMPLATES:
                    query_text = template.format(formula_name=formula_name)
                    if query_text not in route_cache:
                        route_cache[query_text] = detect_route(assembler, query_text)
                    if query_text not in raw_query_cache:
                        raw_query_cache[query_text] = assembler.engine.retrieve(query_text)
                    route_meta = route_cache[query_text]
                    if route_meta["route"] == "formula_effect_query":
                        payload = build_formula_effect_payload_from_bundle(
                            assembler,
                            query_text=query_text,
                            canonical_name=formula_name,
                            bundle=bundle,
                        )
                    else:
                        payload = assembler.assemble(query_text)
                    variant_query_rows.append(
                        build_audit_row(
                            assembler,
                            variant=variant,
                            query_text=query_text,
                            canonical_name=formula_name,
                            formula_meta=formula_meta,
                            route_meta=route_meta,
                            bundle=bundle,
                            payload=payload,
                            raw_query_retrieval=raw_query_cache[query_text],
                        )
                    )

            variant_formula_rows = build_formula_level_rows(variant_query_rows)
            variant_summary = build_variant_summary(
                variant=variant,
                query_rows=variant_query_rows,
                formula_rows=variant_formula_rows,
            )
            variant_payloads.append(
                {
                    "summary": variant_summary,
                    "formula_rows": variant_formula_rows,
                    "query_rows": variant_query_rows,
                }
            )
            all_query_rows.extend(variant_query_rows)

        audit_payload = {
            "experiment_id": "formula_effect_bulk_audit_v1",
            "generated_at_utc": current_utc_timestamp(),
            "supported_env_flag": FORMULA_EFFECT_PRIMARY_RULES_ENV_FLAG,
            "query_templates": list(DEFAULT_QUERY_TEMPLATES),
            "query_template_count": len(DEFAULT_QUERY_TEMPLATES),
            "formula_count": len(formula_names),
            "total_query_count": len(all_query_rows),
            "variants": variant_payloads,
            "before_after_delta": build_before_after_delta(variant_payloads),
        }

        audit_json_out.write_text(json_dumps(audit_payload) + "\n", encoding="utf-8")
        summary_md_out.write_text(render_summary_markdown(audit_payload=audit_payload), encoding="utf-8")
        taxonomy_md_out.write_text(render_taxonomy_markdown(audit_payload=audit_payload), encoding="utf-8")
        decision_md_out.write_text(render_decision_markdown(audit_payload=audit_payload), encoding="utf-8")
        return 0
    finally:
        assembler.close()


if __name__ == "__main__":
    raise SystemExit(main())
