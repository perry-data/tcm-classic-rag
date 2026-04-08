#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.strategies.general_question import (
    GeneralBranchMeta,
    GeneralQuestionPlan,
    analyze_general_branch,
    detect_general_question,
)
from backend.retrieval.hybrid import (
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_EXAMPLES,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    HybridRetrievalEngine,
    json_dumps,
    log,
)
from backend.retrieval.minimal import compact_text, extract_title_anchor


DEFAULT_ANSWER_EXAMPLES_OUT = "artifacts/hybrid_answer_examples.json"
DEFAULT_ANSWER_SMOKE_OUT = "artifacts/hybrid_answer_smoke_checks.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNIPPET_LIMIT = 120
COMPARISON_ENTITY_LIMIT = 2
COMPARISON_FORMULA_TITLE_LIMIT = 1
COMPARISON_SUPPORT_LIMIT = 1
COMPARISON_REVIEW_LIMIT = 2
GENERAL_BRANCH_LIMIT = 4
GENERAL_MANAGEMENT_BRANCH_LIMIT = 3
GENERAL_WEAK_BRANCH_LIMIT = 3
GENERAL_SECONDARY_LIMIT = 5
GENERAL_REVIEW_LIMIT = 3

FORMULA_VARIANT_REPLACEMENTS = (
    ("厚朴", "浓朴"),
    ("杏仁", "杏子"),
    ("杏人", "杏子"),
)

COMPARISON_KEYWORDS = (
    "区别",
    "不同",
    "异同",
    "比较",
    "相比",
    "何异",
    "差别",
    "多了什么",
    "少了什么",
)

UNSUPPORTED_COMPARISON_HINTS = (
    "哪个好",
    "哪个更好",
    "谁更好",
    "更适合",
    "优劣",
    "更强",
)

COMPARISON_CONTEXT_HINTS = (
    "证候",
    "主治",
    "语境",
    "适用",
    "症状",
    "条文语境",
)

PERSONAL_HEALTH_CONTEXT_HINTS = (
    "我的体重",
    "我的症状",
    "我的体质",
    "我现在",
    "我目前",
    "我血压",
    "我发烧",
    "我发热",
    "我咳嗽",
    "按我的",
    "适合我",
    "本人",
    "患者",
    "病人",
)

PERSONAL_TREATMENT_ACTION_HINTS = (
    "能不能",
    "可不可以",
    "可以不可以",
    "能用",
    "服用",
    "该用",
    "应该用",
    "用哪个方",
    "开处方",
    "用药",
)

DOSAGE_CONVERSION_HINTS = (
    "体重",
    "克数",
    "剂量",
    "换算",
    "折算",
    "用量",
)

MODERN_MEDICAL_TERMS = (
    "支气管炎",
    "高血压",
    "血压高",
    "糖尿病",
    "肺炎",
    "新冠",
    "疫苗",
    "癌",
    "肿瘤",
)

MODERN_MEDICAL_ACTION_HINTS = (
    "治疗",
    "疗效",
    "能不能",
    "能用",
    "适应症",
    "治",
)

PERSONAL_REGIMEN_HINTS = (
    "七天",
    "7天",
    "疗程",
    "方案",
    "用药方案",
    "适合我体质",
)

EXTERNAL_BOOK_HINTS = (
    "黄帝内经",
    "素问",
    "灵枢",
    "金匮要略",
    "温病条辨",
    "本草纲目",
)

VALUE_JUDGMENT_HINTS = (
    "哪个更准确",
    "哪一个更准确",
    "谁更准确",
    "哪个更好",
    "哪个好",
    "谁更好",
    "更适合",
    "优劣",
    "更强",
)

REFUSE_GUIDANCE_TEMPLATES = [
    "请改问具体条文，例如：某一条文的原文或含义是什么？",
    "请改问具体方名，例如：黄连汤方的组成或条文是什么？",
    "请改问书中某个明确术语或概念，例如：某句话出自哪一条？",
]

COMPARISON_REFUSE_GUIDANCE_TEMPLATES = [
    "请明确写出两个方名，例如：A 和 B 的区别是什么？",
    "若想比较证候或语境，请直接说明，例如：A 和 B 的条文语境有什么不同？",
    "若当前只确定一个方名，可先单独追问该方条文，再继续比较。",
]

NON_INGREDIENT_TOKENS = {
    "皮",
    "皮尖",
    "尖",
    "节",
    "穣",
    "根据前法",
    "前法",
    "馀根据前法",
    "馀根据",
    "根据",
    "煎服",
    "则愈",
    "右",
}


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble stable answer payloads from hybrid retrieval results.")
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
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    parser.add_argument("--query", help="Run a single query and print the assembled answer payload.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_ANSWER_EXAMPLES_OUT,
        help="Where to write the default answer examples JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_ANSWER_SMOKE_OUT,
        help="Where to write the answer smoke check markdown report.",
    )
    return parser.parse_args()


def compact_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def snippet_text(text: str | None, limit: int = SNIPPET_LIMIT) -> str:
    compact = compact_whitespace(text)
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def first_meaningful_line(text: str | None) -> str:
    if not text:
        return ""
    for line in str(text).splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def build_examples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
    }


def normalize_formula_lookup_text(text: str | None, *, keep_formula_suffix: bool = True) -> str:
    normalized = compact_text(text)
    for source, target in FORMULA_VARIANT_REPLACEMENTS:
        normalized = normalized.replace(compact_text(source), compact_text(target))
    if not keep_formula_suffix and normalized.endswith("方") and len(normalized) > 1:
        normalized = normalized[:-1]
    return normalized


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


@dataclass
class AnswerAssembler:
    db_path: Path
    policy_path: Path
    embed_model: str
    rerank_model: str
    cache_dir: Path
    dense_chunks_index: Path
    dense_chunks_meta: Path
    dense_main_index: Path
    dense_main_meta: Path

    def __post_init__(self) -> None:
        self.engine = HybridRetrievalEngine(
            db_path=self.db_path,
            policy_path=self.policy_path,
            embed_model=self.embed_model,
            rerank_model=self.rerank_model,
            cache_dir=self.cache_dir,
            dense_chunks_index=self.dense_chunks_index,
            dense_chunks_meta=self.dense_chunks_meta,
            dense_main_index=self.dense_main_index,
            dense_main_meta=self.dense_main_meta,
        )
        self._record_cache: dict[str, dict[str, Any]] = {}
        (
            self._formula_catalog,
            self._formula_aliases,
            self._formula_alias_lookup,
        ) = self._load_formula_catalog()
        self._last_comparison_debug: dict[str, Any] | None = None
        self._last_general_debug: dict[str, Any] | None = None

    def close(self) -> None:
        self.engine.close()

    def assemble(self, query_text: str) -> dict[str, Any]:
        self._last_comparison_debug = None
        self._last_general_debug = None
        policy_refusal = self._detect_policy_refusal(query_text)
        if policy_refusal is not None:
            return self._assemble_policy_refusal(query_text, policy_refusal)
        comparison_plan = self._detect_comparison_query(query_text)
        if comparison_plan is not None:
            return self._assemble_comparison(query_text, comparison_plan)
        general_plan = detect_general_question(query_text)
        if general_plan is not None:
            return self._assemble_general_question(query_text, general_plan)
        return self._assemble_standard(query_text)

    def get_last_comparison_debug(self) -> dict[str, Any] | None:
        return self._last_comparison_debug

    def _detect_policy_refusal(self, query_text: str) -> str | None:
        compact_query = compact_whitespace(query_text)
        if not compact_query:
            return None

        has_personal_context = self._has_any_hint(compact_query, PERSONAL_HEALTH_CONTEXT_HINTS)
        has_personal_action = self._has_any_hint(compact_query, PERSONAL_TREATMENT_ACTION_HINTS)

        if self._has_any_hint(compact_query, EXTERNAL_BOOK_HINTS) and self._has_any_hint(
            compact_query,
            VALUE_JUDGMENT_HINTS,
        ):
            return "跨书比较或价值判断超出《伤寒论》单书研读支持边界。"

        if has_personal_context and self._has_any_hint(compact_query, DOSAGE_CONVERSION_HINTS):
            return "按体重或个体情况换算剂量超出《伤寒论》研读支持边界。"

        if has_personal_context and self._has_any_hint(compact_query, PERSONAL_REGIMEN_HINTS):
            return "个体化处方或疗程方案超出《伤寒论》研读支持边界。"

        if self._has_any_hint(compact_query, MODERN_MEDICAL_TERMS) and self._has_any_hint(
            compact_query,
            MODERN_MEDICAL_ACTION_HINTS,
        ):
            return "现代病名疗效或用药判断超出《伤寒论》研读支持边界。"

        if has_personal_context and has_personal_action:
            return "个人诊疗、服药或处方建议超出《伤寒论》研读支持边界。"

        return None

    @staticmethod
    def _has_any_hint(text: str, hints: tuple[str, ...]) -> bool:
        return any(hint in text for hint in hints)

    def _assemble_policy_refusal(self, query_text: str, refuse_reason: str) -> dict[str, Any]:
        return self._compose_payload(
            query_text=query_text,
            answer_mode="refuse",
            answer_text="该问题超出《伤寒论》单书研读支持边界，暂不提供诊疗、剂量、现代病名疗效或跨书价值判断。",
            primary=[],
            secondary=[],
            review=[],
            review_notice=None,
            disclaimer=self._build_disclaimer("refuse", False, False),
            refuse_reason=refuse_reason,
            suggested_followup_questions=self._build_followups("refuse"),
            citations=[],
        )

    def _assemble_standard(self, query_text: str) -> dict[str, Any]:
        retrieval = self.engine.retrieve(query_text)
        primary = [self._build_evidence_item(row, display_role="primary") for row in retrieval["primary_evidence"]]
        secondary = [self._build_evidence_item(row, display_role="secondary") for row in retrieval["secondary_evidence"]]
        review = [self._build_evidence_item(row, display_role="review") for row in retrieval["risk_materials"]]

        answer_mode = retrieval["mode"]
        answer_text = self._build_answer_text(retrieval, primary, secondary, review)
        review_notice = self._build_review_notice(answer_mode)
        disclaimer = self._build_disclaimer(answer_mode, bool(secondary), bool(review))
        refuse_reason = self._build_refuse_reason(answer_mode)
        suggested_followup_questions = self._build_followups(answer_mode)
        citations = self._build_citations(answer_mode, primary, secondary, review)
        display_sections = self._build_display_sections(
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            citations=citations,
            review_notice=review_notice,
            suggested_followup_questions=suggested_followup_questions,
        )

        return {
            "query": query_text,
            "answer_mode": answer_mode,
            "answer_text": answer_text,
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "review_materials": review,
            "disclaimer": disclaimer,
            "review_notice": review_notice,
            "refuse_reason": refuse_reason,
            "suggested_followup_questions": suggested_followup_questions,
            "citations": citations,
            "display_sections": display_sections,
        }

    def _assemble_general_question(self, query_text: str, general_plan: GeneralQuestionPlan) -> dict[str, Any]:
        query_retrieval = self.engine.retrieve(query_text)
        topic_retrieval = (
            query_retrieval
            if compact_text(query_text) == general_plan.normalized_topic
            else self.engine.retrieve(general_plan.topic_text)
        )
        retrievals = [query_retrieval] if topic_retrieval is query_retrieval else [query_retrieval, topic_retrieval]

        seed_scores = self._build_general_seed_scores(retrievals)
        candidates = self._collect_general_branch_candidates(general_plan, seed_scores)
        strong_candidates = self._select_general_branches(candidates, general_plan, strong_only=True)
        fallback_secondary_rows = self._collect_general_slot_rows(retrievals, slot_name="secondary_evidence")
        fallback_review_rows = self._collect_general_slot_rows(retrievals, slot_name="risk_materials")

        self._last_general_debug = {
            "query": query_text,
            "general_question_detected": True,
            "general_kind": general_plan.general_kind,
            "topic_text": general_plan.topic_text,
            "candidate_count": len(candidates),
            "strong_candidate_count": sum(1 for candidate in candidates if candidate["strong_eligible"]),
            "selected_branch_count": len(strong_candidates),
        }

        if len(strong_candidates) >= 2:
            primary = [
                self._build_evidence_item(
                    candidate["row"],
                    display_role="primary",
                    title_override=candidate["branch_meta"].branch_label,
                )
                for candidate in strong_candidates
            ]
            selected_ids = {item["record_id"] for item in primary}
            secondary: list[dict[str, Any]] = []
            for candidate in candidates:
                record_id = candidate["row"]["record_id"]
                if record_id in selected_ids:
                    continue
                secondary.append(
                    self._build_evidence_item(
                        candidate["row"],
                        display_role="secondary",
                        title_override=candidate["branch_meta"].branch_label,
                    )
                )
                selected_ids.add(record_id)
                if len(secondary) >= GENERAL_SECONDARY_LIMIT:
                    break
            for row in fallback_secondary_rows:
                if row["record_id"] in selected_ids:
                    continue
                secondary.append(self._build_evidence_item(row, display_role="secondary"))
                selected_ids.add(row["record_id"])
                if len(secondary) >= GENERAL_SECONDARY_LIMIT:
                    break

            review: list[dict[str, Any]] = []
            for row in fallback_review_rows[:GENERAL_REVIEW_LIMIT]:
                review.append(self._build_evidence_item(row, display_role="review"))

            answer_text = self._build_general_answer_text(
                general_plan,
                strong_candidates,
                answer_mode="strong",
            )
            review_notice = self._build_review_notice("strong") if secondary or review else None
            disclaimer = self._build_disclaimer("strong", bool(secondary), bool(review))
            citations = self._build_citations("strong", primary, secondary, review)
            return self._compose_payload(
                query_text=query_text,
                answer_mode="strong",
                answer_text=answer_text,
                primary=primary,
                secondary=secondary,
                review=review,
                review_notice=review_notice,
                disclaimer=disclaimer,
                refuse_reason=None,
                suggested_followup_questions=[],
                citations=citations,
            )

        weak_candidates = self._select_general_branches(candidates, general_plan, strong_only=False)
        if weak_candidates or fallback_secondary_rows or fallback_review_rows:
            display_candidates = list(weak_candidates[:GENERAL_WEAK_BRANCH_LIMIT])
            if not display_candidates:
                display_candidates = self._build_general_fallback_display_candidates(
                    fallback_secondary_rows[:GENERAL_WEAK_BRANCH_LIMIT],
                    general_plan,
                )

            secondary: list[dict[str, Any]] = []
            seen_ids: set[str] = set()
            for candidate in weak_candidates[:GENERAL_WEAK_BRANCH_LIMIT]:
                risk_flags = dedupe_strings(candidate["row"]["risk_flag"] + ["general_branch_incomplete"])
                secondary.append(
                    self._build_evidence_item(
                        candidate["row"],
                        display_role="secondary",
                        title_override=candidate["branch_meta"].branch_label,
                        risk_flags_override=risk_flags,
                    )
                )
                seen_ids.add(candidate["row"]["record_id"])

            for row in fallback_secondary_rows:
                if row["record_id"] in seen_ids:
                    continue
                risk_flags = dedupe_strings(self._extract_risk_flags(row) + ["general_branch_incomplete"])
                secondary.append(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        risk_flags_override=risk_flags,
                    )
                )
                seen_ids.add(row["record_id"])
                if len(secondary) >= GENERAL_SECONDARY_LIMIT:
                    break

            review: list[dict[str, Any]] = []
            review_seen = set(seen_ids)
            for row in fallback_review_rows:
                if row["record_id"] in review_seen:
                    continue
                review.append(self._build_evidence_item(row, display_role="review"))
                review_seen.add(row["record_id"])
                if len(review) >= GENERAL_REVIEW_LIMIT:
                    break

            answer_text = self._build_general_answer_text(
                general_plan,
                display_candidates,
                answer_mode="weak_with_review_notice",
            )
            review_notice = "这是总括性问题，但当前只能整理出部分分支线索，以下内容需核对，不应视为完整答案。"
            disclaimer = "当前只输出部分分支整理与核对材料，不输出完整定案。"
            followups = self._build_general_followups(general_plan, display_candidates)
            citations = self._build_citations("weak_with_review_notice", [], secondary, review)
            return self._compose_payload(
                query_text=query_text,
                answer_mode="weak_with_review_notice",
                answer_text=answer_text,
                primary=[],
                secondary=secondary,
                review=review,
                review_notice=review_notice,
                disclaimer=disclaimer,
                refuse_reason=None,
                suggested_followup_questions=followups,
                citations=citations,
            )

        answer_text = (
            f"这是一个总括性问题，但当前无法把“{general_plan.topic_text}”稳定整理成分情况回答，"
            "因此暂不输出概括性结论。"
        )
        followups = self._build_general_followups(general_plan, [])
        return self._compose_payload(
            query_text=query_text,
            answer_mode="refuse",
            answer_text=answer_text,
            primary=[],
            secondary=[],
            review=[],
            review_notice=None,
            disclaimer="当前为总括类问题的拒答降级，不输出推测性概括。",
            refuse_reason=f"未能为“{general_plan.topic_text}”组织出至少两条可核对的可靠分支。",
            suggested_followup_questions=followups,
            citations=[],
        )

    def _build_general_seed_scores(self, retrievals: list[dict[str, Any]]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for retrieval in retrievals:
            for row in retrieval.get("raw_candidates", []):
                raw_score = min(float(row.get("combined_score", 0.0)) / 35.0, 28.0)
                if row.get("record_table") == "records_main_passages":
                    scores[row["record_id"]] = max(scores.get(row["record_id"], 0.0), raw_score)
                    continue
                if row.get("record_table") != "records_chunks":
                    continue
                for backref in self.engine._fetch_chunk_backrefs(row["record_id"]):
                    if backref["evidence_level"] not in {"A", "B"}:
                        continue
                    scores[backref["record_id"]] = max(scores.get(backref["record_id"], 0.0), raw_score)

            for slot_name in ("primary_evidence", "secondary_evidence"):
                for row in retrieval.get(slot_name, []):
                    slot_score = min(float(row.get("combined_score", 0.0)) / 40.0, 22.0)
                    scores[row["record_id"]] = max(scores.get(row["record_id"], 0.0), slot_score)
        return scores

    def _collect_general_branch_candidates(
        self,
        general_plan: GeneralQuestionPlan,
        seed_scores: dict[str, float],
    ) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for row in self.engine.unified_rows:
            if row["source_object"] != "main_passages":
                continue
            if row["evidence_level"] not in {"A", "B"}:
                continue
            if general_plan.normalized_topic not in compact_text(row["retrieval_text"]):
                continue

            branch_meta = analyze_general_branch(
                row["retrieval_text"],
                general_plan.topic_text,
                general_kind=general_plan.general_kind,
                chapter_matches_topic=general_plan.normalized_topic in compact_text(row["chapter_name"]),
            )
            if branch_meta is None:
                continue

            selection_score = branch_meta.heuristic_score + seed_scores.get(row["record_id"], 0.0)
            selection_score += 8.0 if row["evidence_level"] == "A" else -4.0
            if selection_score < 18.0:
                continue

            candidate = {
                "row": self._normalize_record_row(row),
                "branch_meta": branch_meta,
                "selection_score": selection_score,
                "strong_eligible": row["evidence_level"] == "A",
            }
            existing = deduped.get(branch_meta.branch_key)
            if existing is None or candidate["selection_score"] > existing["selection_score"]:
                deduped[branch_meta.branch_key] = candidate

        return sorted(
            deduped.values(),
            key=lambda item: (
                -item["selection_score"],
                item["row"]["chapter_id"],
                item["row"]["record_id"],
            ),
        )

    def _select_general_branches(
        self,
        candidates: list[dict[str, Any]],
        general_plan: GeneralQuestionPlan,
        *,
        strong_only: bool,
    ) -> list[dict[str, Any]]:
        eligible = [candidate for candidate in candidates if candidate["strong_eligible"] or not strong_only]
        if not eligible:
            return []
        branch_limit = GENERAL_MANAGEMENT_BRANCH_LIMIT if general_plan.general_kind == "management" else GENERAL_BRANCH_LIMIT

        classifications = [
            candidate for candidate in eligible if candidate["branch_meta"].branch_type == "classification"
        ]
        cautions = [candidate for candidate in eligible if candidate["branch_meta"].branch_type == "caution"]
        formulas = [candidate for candidate in eligible if candidate["branch_meta"].branch_type == "formula"]
        courses = [candidate for candidate in eligible if candidate["branch_meta"].branch_type == "course"]
        remainder = [candidate for candidate in eligible if candidate["branch_meta"].branch_type not in {"classification", "caution", "formula", "course"}]

        buckets = [sorted(bucket, key=lambda item: (-item["selection_score"], item["row"]["record_id"])) for bucket in [classifications, cautions, formulas, courses, remainder]]
        selected: list[dict[str, Any]] = []

        def add_from_bucket(bucket: list[dict[str, Any]], limit: int) -> None:
            for candidate in bucket:
                if candidate in selected:
                    continue
                selected.append(candidate)
                if len(selected) >= limit:
                    break

        if general_plan.general_kind == "overview":
            add_from_bucket(buckets[0], min(2, branch_limit))
            add_from_bucket(buckets[2], branch_limit)
            add_from_bucket(buckets[1], branch_limit)
            add_from_bucket(buckets[3], branch_limit)
        else:
            add_from_bucket(buckets[0], 1)
            add_from_bucket(buckets[2], branch_limit)
            add_from_bucket(buckets[1], branch_limit)
            add_from_bucket(buckets[3], branch_limit)

        if len(selected) < branch_limit:
            combined_remainder = sorted(
                [candidate for bucket in buckets for candidate in bucket if candidate not in selected],
                key=lambda item: (-item["selection_score"], item["row"]["record_id"]),
            )
            add_from_bucket(combined_remainder, branch_limit)

        return selected[:branch_limit]

    def _collect_general_slot_rows(
        self,
        retrievals: list[dict[str, Any]],
        *,
        slot_name: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for retrieval in retrievals:
            for row in retrieval.get(slot_name, []):
                if row["record_id"] in seen_ids:
                    continue
                rows.append(row)
                seen_ids.add(row["record_id"])
        return rows

    def _build_general_fallback_display_candidates(
        self,
        rows: list[dict[str, Any]],
        general_plan: GeneralQuestionPlan,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for index, row in enumerate(rows, start=1):
            full_text = self._fetch_record_meta(row["record_id"])["retrieval_text"]
            branch_label = f"待核对线索 {index}"
            candidates.append(
                {
                    "row": self._normalize_record_row(
                        {
                            "record_id": row["record_id"],
                            "source_object": row["source_object"],
                            "evidence_level": row["evidence_level"],
                            "chapter_id": row["chapter_id"],
                            "chapter_name": row["chapter_name"],
                            "retrieval_text": full_text or row.get("text_preview", ""),
                            "risk_flag": json_dumps(self._extract_risk_flags(row)),
                        }
                    ),
                    "branch_meta": GeneralBranchMeta(
                        branch_key=row["record_id"],
                        branch_type="fallback",
                        branch_label=branch_label,
                        branch_summary=f"当前只检索到与“{general_plan.topic_text}”相关的一条待核对线索，尚不足以独立成支。",
                        heuristic_score=0.0,
                    ),
                    "selection_score": 0.0,
                    "strong_eligible": False,
                }
            )
        return candidates

    def _build_general_answer_text(
        self,
        general_plan: GeneralQuestionPlan,
        selected_candidates: list[dict[str, Any]],
        *,
        answer_mode: str,
    ) -> str:
        if general_plan.general_kind == "management":
            lead = f"这是一个总括性问题，书中谈“{general_plan.topic_text}”并非只有一个固定治法，需要分情况看。"
        else:
            lead = f"这是一个总括性问题，书中谈“{general_plan.topic_text}”并非只有一条统一描述，需要分情况整理。"

        if answer_mode == "strong":
            lines = [lead, "以下先按当前能稳定抓到的典型分支整理："]
            for idx, candidate in enumerate(selected_candidates, start=1):
                branch_meta: GeneralBranchMeta = candidate["branch_meta"]
                lines.append(
                    f"{idx}. {branch_meta.branch_label}：{branch_meta.branch_summary} 依据：{candidate['row']['text_preview']}"
                )
            lines.append(f"当前回答只列若干典型分支，不等于穷尽全部“{general_plan.topic_text}”处理。")
            return "\n".join(lines)

        lines = [lead, "当前只能先整理出部分可核对的分支线索："]
        for idx, candidate in enumerate(selected_candidates, start=1):
            branch_meta = candidate["branch_meta"]
            lines.append(
                f"{idx}. {branch_meta.branch_label}：{branch_meta.branch_summary} 依据：{candidate['row']['text_preview']}"
            )
        lines.append("分支组织仍不完整，建议继续收窄到某一支再问。")
        return "\n".join(lines)

    def _build_general_followups(
        self,
        general_plan: GeneralQuestionPlan,
        selected_candidates: list[dict[str, Any]],
    ) -> list[str]:
        followups = [
            f"请改问更窄的一支，例如：{general_plan.topic_text}中某一支具体对应哪条？",
            f"请改问更窄的处理线索，例如：{general_plan.topic_text}里某种表现为什么用某方？",
        ]
        for candidate in selected_candidates[:2]:
            if candidate["branch_meta"].branch_label.startswith("待核对线索"):
                continue
            followups.append(
                f"可以继续追问：{general_plan.topic_text}里“{candidate['branch_meta'].branch_label}”具体怎么理解？"
            )
        return dedupe_strings(followups)[:3]

    def _build_comparison_refuse_reason(self, reason: str) -> str:
        if reason == "unsupported_comparison":
            return "当前只支持基于条文证据整理“区别 / 不同 / 异同 / 多了什么 / 少了什么”这类比较，不支持优劣判断。"
        if reason == "too_many_entities":
            return "当前一次只支持两个对象的 pairwise comparison，请把问题收缩到两个方名。"
        return "当前无法稳定识别两个待比较的方名，因此不能可靠组织比较答案。"

    def _build_comparison_entity_bundle(self, entity: dict[str, Any]) -> dict[str, Any]:
        retrieval = self.engine.retrieve(entity["canonical_name"])
        formula_row = self._find_formula_heading_row(entity["canonical_name"], retrieval)
        formula_rows = [formula_row] if formula_row else []
        support_rows = self._find_support_rows(
            entity["canonical_name"],
            excluded_record_ids={row["record_id"] for row in formula_rows},
        )
        context_row = support_rows[0] if support_rows else self._find_review_context_row(
            entity["canonical_name"],
            excluded_record_ids={row["record_id"] for row in formula_rows},
        )
        review_rows = self._lookup_review_rows(formula_rows + support_rows)
        if context_row and context_row["source_object"] != "main_passages":
            existing_review_ids = {row["record_id"] for row in review_rows}
            if context_row["record_id"] not in existing_review_ids:
                review_rows.append(context_row)
        facts = self._extract_formula_facts(
            entity["canonical_name"],
            formula_row=formula_rows[0] if formula_rows else None,
            context_row=context_row,
        )
        return {
            "group_label": entity["group_label"],
            "canonical_name": entity["canonical_name"],
            "formula_rows": formula_rows,
            "support_rows": support_rows,
            "review_rows": review_rows,
            "facts": facts,
            "context_source": context_row["source_object"] if context_row else None,
        }

    def _find_formula_heading_row(self, canonical_name: str, retrieval: dict[str, Any]) -> dict[str, Any] | None:
        for row in retrieval["primary_evidence"] + retrieval["secondary_evidence"]:
            if row["source_object"] != "main_passages":
                continue
            if self._row_is_formula_heading_for_entity(row, canonical_name):
                return row
        return None

    def _find_support_rows(self, canonical_name: str, excluded_record_ids: set[str]) -> list[dict[str, Any]]:
        return self._find_matching_rows(
            canonical_name,
            excluded_record_ids=excluded_record_ids,
            source_objects=("main_passages",),
            extra_risk_flags=["topic_mismatch_demoted"],
            limit=COMPARISON_SUPPORT_LIMIT,
        )

    def _find_review_context_row(self, canonical_name: str, excluded_record_ids: set[str]) -> dict[str, Any] | None:
        rows = self._find_matching_rows(
            canonical_name,
            excluded_record_ids=excluded_record_ids,
            source_objects=("passages", "ambiguous_passages"),
            extra_risk_flags=None,
            limit=1,
        )
        return rows[0] if rows else None

    def _find_matching_rows(
        self,
        canonical_name: str,
        *,
        excluded_record_ids: set[str],
        source_objects: tuple[str, ...],
        extra_risk_flags: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        query_key = normalize_formula_lookup_text(canonical_name, keep_formula_suffix=False)
        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for row in self.engine.unified_rows:
            if row["record_id"] in excluded_record_ids:
                continue
            if row["source_object"] not in source_objects:
                continue
            normalized_text = normalize_formula_lookup_text(row["retrieval_text"], keep_formula_suffix=True)
            if query_key not in normalized_text:
                continue
            if self._row_is_formula_heading_for_entity(row, canonical_name):
                continue
            score = 0
            if "主之" in row["retrieval_text"]:
                score += 30
            if row.get("chapter_id") != self._formula_catalog.get(canonical_name, {}).get("chapter_id"):
                score += 20
            compact_length = len(compact_whitespace(row["retrieval_text"]))
            if compact_length <= 96:
                score += 10
            if "详见" in row["retrieval_text"]:
                score += 5
            candidates.append(
                (
                    score,
                    compact_length,
                    self._normalize_record_row(row, extra_risk_flags=extra_risk_flags),
                )
            )

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]["record_id"]))
        return [candidate[2] for candidate in candidates[:limit]]

    def _lookup_review_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        review_rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in rows:
            record_id = row["record_id"]
            if not record_id.startswith("safe:main_passages:"):
                continue
            suffix = record_id.removeprefix("safe:main_passages:")
            candidate_ids = [f"full:passages:{suffix}", f"full:ambiguous_passages:{suffix}"]
            for candidate_id in candidate_ids:
                candidate_row = self.engine.record_by_id.get(candidate_id)
                if candidate_row is None or candidate_id in seen:
                    continue
                review_rows.append(self._normalize_record_row(candidate_row))
                seen.add(candidate_id)
        return review_rows

    def _normalize_record_row(
        self,
        row: dict[str, Any],
        *,
        extra_risk_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        risk_flags = dedupe_strings(self._extract_risk_flags(row) + (extra_risk_flags or []))
        return {
            "record_id": row["record_id"],
            "source_object": row["source_object"],
            "evidence_level": row["evidence_level"],
            "chapter_id": row["chapter_id"],
            "chapter_name": row["chapter_name"],
            "text_preview": snippet_text(row.get("retrieval_text") or row.get("text_preview")),
            "risk_flag": risk_flags,
            "topic_anchor": extract_title_anchor(row.get("retrieval_text") or row.get("text_preview")),
        }

    def _extract_risk_flags(self, row: dict[str, Any]) -> list[str]:
        risk_flags = row.get("risk_flag", [])
        if isinstance(risk_flags, str):
            try:
                parsed = json.loads(risk_flags)
            except json.JSONDecodeError:
                parsed = [risk_flags] if risk_flags else []
            risk_flags = parsed
        return [flag for flag in risk_flags if flag]

    def _row_is_formula_heading_for_entity(self, row: dict[str, Any], canonical_name: str) -> bool:
        text = row.get("retrieval_text") or row.get("text_preview", "")
        title = extract_title_anchor(text)
        if not title or not title.endswith("方"):
            return False
        return normalize_formula_lookup_text(title, keep_formula_suffix=False) == normalize_formula_lookup_text(
            canonical_name,
            keep_formula_suffix=False,
        )

    def _extract_formula_facts(
        self,
        canonical_name: str,
        *,
        formula_row: dict[str, Any] | None,
        context_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        facts = {
            "base_formula": "",
            "added_ingredients": [],
            "removed_ingredients": [],
            "context_clause": "",
            "formula_chapter_id": formula_row["chapter_id"] if formula_row else None,
            "formula_chapter_title": formula_row["chapter_name"] if formula_row else None,
            "support_chapter_id": context_row["chapter_id"] if context_row else None,
            "support_chapter_title": context_row["chapter_name"] if context_row else None,
        }
        if formula_row:
            formula_text = self._fetch_record_meta(formula_row["record_id"])["retrieval_text"]
            core_formula_text = formula_text.split("：", 1)[1] if "：" in formula_text else formula_text
            core_formula_text = core_formula_text.split("。", 1)[0]
            base_match = re.search(r"于(?:第[一二三四五六七八九十百千万0-9]+卷)?([^，。；:：]+?方)内", core_formula_text)
            if base_match:
                facts["base_formula"] = base_match.group(1).strip()
            facts["added_ingredients"] = self._extract_formula_delta_names(core_formula_text, marker="add")
            facts["removed_ingredients"] = self._extract_formula_delta_names(core_formula_text, marker="remove")

        if context_row:
            support_text = self._fetch_record_meta(context_row["record_id"])["retrieval_text"]
            facts["context_clause"] = self._extract_context_clause(support_text, canonical_name)
        return facts

    def _extract_formula_delta_names(self, formula_text: str, *, marker: str) -> list[str]:
        if marker == "add":
            segments = re.findall(r"(?:加|更加)([^。；]+)", formula_text)
        else:
            segments = re.findall(r"(?:^|，)去([^，。；]+)", formula_text)

        names: list[str] = []
        for segment in segments:
            if marker == "remove":
                segment = segment.split("加", 1)[0]
            for name in self._extract_phrase_names(segment):
                if name not in NON_INGREDIENT_TOKENS:
                    names.append(name)
        return dedupe_strings(names)

    def _extract_phrase_names(self, segment: str) -> list[str]:
        cleaned = compact_whitespace(segment)
        cleaned = re.sub(r"(根据前法|馀根据前法|馀根据|根据前|根据|煎服|前法).*$", "", cleaned)
        matches: list[str] = []
        for part in [piece.strip() for piece in re.split(r"[，]", cleaned) if piece.strip()]:
            if "、" in part and "各" in part:
                prefix = part.split("各", 1)[0]
                matches.extend(name.strip() for name in prefix.split("、") if name.strip())
                continue
            dosage_match = re.match(
                r"^([一-龥]{1,10}?)(?:各)?(?:半|[一二三四五六七八九十百千万\d]+)(?:两|枚|个|斤|升|合|钱|铢)",
                part,
            )
            if dosage_match:
                matches.append(dosage_match.group(1))
                continue
            matches.extend(piece.strip() for piece in part.split("、") if piece.strip())
        names: list[str] = []
        for match in matches:
            candidate = re.sub(r"(炮|炙|切|洗|擘|熬|去皮尖?|去节|破八片|绵裹|赵本.*|医统本.*)$", "", match).strip()
            candidate = candidate.strip("，、 ")
            if not candidate or candidate in NON_INGREDIENT_TOKENS or candidate.endswith("方"):
                continue
            names.append(candidate)
        return dedupe_strings(names)

    def _extract_context_clause(self, support_text: str, canonical_name: str) -> str:
        match_index = -1
        for variant in self._formula_text_variants(canonical_name):
            current_index = support_text.find(variant)
            if current_index >= 0 and (match_index < 0 or current_index < match_index):
                match_index = current_index
        if match_index < 0:
            return snippet_text(support_text, limit=64)
        context_text = support_text[:match_index].strip("，。；：: ")
        if "。" in context_text:
            context_text = context_text.split("。")[-1]
        if "；" in context_text:
            context_text = context_text.split("；")[-1]
        return compact_whitespace(context_text.strip("，。；：: "))

    def _formula_text_variants(self, canonical_name: str) -> list[str]:
        variants = {
            canonical_name,
            canonical_name[:-1] if canonical_name.endswith("方") else canonical_name,
        }
        replacement_pairs = [
            ("浓朴", "厚朴"),
            ("杏子", "杏人"),
            ("杏子", "杏仁"),
        ]
        expanded = set(variants)
        for source, target in replacement_pairs:
            current_variants = list(expanded)
            for variant in current_variants:
                if source in variant:
                    expanded.add(variant.replace(source, target))
        return sorted((variant for variant in expanded if variant), key=len, reverse=True)

    def _determine_comparison_mode(self, comparison_plan: dict[str, Any], entity_bundles: list[dict[str, Any]]) -> str:
        if any(not bundle["formula_rows"] for bundle in entity_bundles):
            return "refuse"

        composition_supported = any(
            bundle["facts"]["base_formula"] or bundle["facts"]["added_ingredients"] or bundle["facts"]["removed_ingredients"]
            for bundle in entity_bundles
        )
        context_supported = all(bundle["facts"]["context_clause"] for bundle in entity_bundles)
        context_main_supported = all(bundle["context_source"] == "main_passages" for bundle in entity_bundles)

        if comparison_plan["requested_context"] and (not context_supported or not context_main_supported):
            return "weak_with_review_notice"
        if not composition_supported and not context_supported:
            return "weak_with_review_notice"
        return "strong"

    def _build_comparison_lines(
        self,
        comparison_plan: dict[str, Any],
        entity_bundles: list[dict[str, Any]],
        answer_mode: str,
    ) -> list[str]:
        first, second = entity_bundles
        first_name = first["canonical_name"]
        second_name = second["canonical_name"]
        first_facts = first["facts"]
        second_facts = second["facts"]
        shared_base = (
            first_facts["base_formula"]
            if first_facts["base_formula"] and first_facts["base_formula"] == second_facts["base_formula"]
            else ""
        )
        first_added = [name for name in first_facts["added_ingredients"] if name not in second_facts["added_ingredients"]]
        second_added = [name for name in second_facts["added_ingredients"] if name not in first_facts["added_ingredients"]]
        first_removed = [name for name in first_facts["removed_ingredients"] if name not in second_facts["removed_ingredients"]]
        second_removed = [name for name in second_facts["removed_ingredients"] if name not in first_facts["removed_ingredients"]]

        if answer_mode == "strong":
            if shared_base:
                lines = [f"从现有方文与相关条文看，{first_name}与{second_name}都从{shared_base}加减而来，但显式加味和对应语境不同。"]
            else:
                lines = [f"从现有方文与相关条文看，{first_name}与{second_name}在显式组成和相关条文语境上并不相同。"]
        else:
            lines = [f"两方都已识别，但当前比较仍有证据缺口，以下只按现有方文做弱整理：{first_name} 与 {second_name} 的差异需要继续核对。"]

        if comparison_plan["query_kind"] == "same_and_diff" and shared_base:
            lines.append(f"1. 共同点：两方的方文都写明是在“{shared_base}”基础上加减。")

        delta_line = self._build_comparison_delta_line(
            comparison_plan["query_kind"],
            first_name,
            second_name,
            first_added,
            second_added,
            first_removed,
            second_removed,
        )
        if delta_line:
            lines.append(f"{len(lines)}. {delta_line}")

        if answer_mode == "strong" and first_facts["context_clause"] and second_facts["context_clause"]:
            first_context_prefix = "相关条文可见" if first["context_source"] == "main_passages" else "核对材料可见"
            second_context_prefix = "相关条文可见" if second["context_source"] == "main_passages" else "核对材料可见"
            lines.append(
                f"{len(lines)}. 条文语境：{first_name}{first_context_prefix}“{first_facts['context_clause']}”；"
                f"{second_name}{second_context_prefix}“{second_facts['context_clause']}”。"
            )
        elif comparison_plan["requested_context"]:
            missing_names = [
                bundle["canonical_name"]
                for bundle in entity_bundles
                if bundle["context_source"] != "main_passages"
            ]
            if missing_names:
                lines.append(
                    f"{len(lines)}. 语境证据缺口：当前未稳定找到 {self._join_formula_names(missing_names)} 的直接相关条文，"
                    "因此语境差异只能暂缓判断。"
                )

        source_line = self._build_comparison_source_line(first, second)
        if source_line:
            lines.append(f"{len(lines)}. {source_line}")

        lines.append("以上差异仅按当前可见条文与方文整理；若要逐字核对，请继续查看引用。")
        return lines

    def _build_comparison_delta_line(
        self,
        query_kind: str,
        first_name: str,
        second_name: str,
        first_added: list[str],
        second_added: list[str],
        first_removed: list[str],
        second_removed: list[str],
    ) -> str:
        pieces: list[str] = []
        if first_added:
            pieces.append(f"{first_name}明写加{ '、'.join(first_added) }")
        if second_added:
            pieces.append(f"{second_name}明写加{ '、'.join(second_added) }")
        if first_removed:
            pieces.append(f"{first_name}另去{ '、'.join(first_removed) }")
        if second_removed:
            pieces.append(f"{second_name}另去{ '、'.join(second_removed) }")

        if not pieces:
            return ""

        if query_kind == "delta":
            return "显式加减关系：" + "；".join(pieces) + "。"
        return "显式加减与药味差异：" + "；".join(pieces) + "。"

    def _build_comparison_source_line(self, first: dict[str, Any], second: dict[str, Any]) -> str:
        source_parts: list[str] = []
        first_facts = first["facts"]
        second_facts = second["facts"]
        if first_facts["formula_chapter_title"]:
            source_parts.append(
                f"{first['canonical_name']}的方文见“{self._format_comparison_source(first_facts['formula_chapter_title'])}”"
            )
        if second_facts["formula_chapter_title"]:
            source_parts.append(
                f"{second['canonical_name']}的方文见“{self._format_comparison_source(second_facts['formula_chapter_title'])}”"
            )
        if first_facts["support_chapter_title"]:
            source_parts.append(
                f"{first['canonical_name']}相关条文位于“{self._format_comparison_source(first_facts['support_chapter_title'])}”"
            )
        if second_facts["support_chapter_title"]:
            source_parts.append(
                f"{second['canonical_name']}相关条文位于“{self._format_comparison_source(second_facts['support_chapter_title'])}”"
            )
        if not source_parts:
            return ""
        return "出处线索：" + "；".join(source_parts) + "。"

    def _join_formula_names(self, names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        return "、".join(names[:-1]) + "和" + names[-1]

    def _format_comparison_source(self, source_title: str) -> str:
        if source_title == "《卷内音释，上卷已有。》":
            return "卷十附方位置"
        return source_title

    def _build_comparison_review_notice(
        self,
        answer_mode: str,
        comparison_plan: dict[str, Any],
        entity_bundles: list[dict[str, Any]],
    ) -> str | None:
        if answer_mode == "weak_with_review_notice":
            return "当前比较仍有证据缺口，以下内容只可视为待核对的弱整理，不应视为确定结论。"
        if answer_mode == "strong" and (
            any(bundle["support_rows"] for bundle in entity_bundles) or any(bundle["review_rows"] for bundle in entity_bundles)
        ):
            return "以下补充依据与核对材料仅用于比较佐证，不作为主结论。"
        return None

    def _build_comparison_disclaimer(self, answer_mode: str, has_secondary: bool, has_review: bool) -> str | None:
        if answer_mode == "strong":
            if has_secondary or has_review:
                return "比较结论优先依据两侧方文；补充依据与核对材料仅作佐证。"
            return "比较结论优先依据两侧方文整理。"
        if answer_mode == "weak_with_review_notice":
            return "当前只输出弱整理，不把证据不足的差异包装成确定结论。"
        return self._build_disclaimer(answer_mode, has_secondary, has_review)

    def _build_comparison_citations(
        self,
        answer_mode: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if answer_mode == "strong":
            citation_source = list(primary + secondary)
            covered_titles = {item["title"] for item in secondary}
            for item in review:
                if item["title"] not in covered_titles:
                    citation_source.append(item)
        elif answer_mode == "weak_with_review_notice":
            citation_source = secondary + review
        else:
            citation_source = []

        citations: list[dict[str, Any]] = []
        for index, item in enumerate(citation_source, start=1):
            citations.append(
                {
                    "citation_id": f"c{index}",
                    "record_id": item["record_id"],
                    "record_type": item["record_type"],
                    "title": item["title"],
                    "evidence_level": item["evidence_level"],
                    "snippet": item["snippet"],
                    "chapter_id": item["chapter_id"],
                    "chapter_title": item["chapter_title"],
                    "citation_role": item["display_role"],
                }
            )
        return citations

    def _load_formula_catalog(self) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
        rows = self.engine.conn.execute(
            """
            SELECT record_id, text, chapter_id, chapter_name
            FROM records_main_passages
            WHERE text LIKE '%方：%'
            """
        ).fetchall()
        catalog: dict[str, dict[str, Any]] = {}
        alias_lookup: dict[str, list[str]] = {}
        alias_records: list[dict[str, Any]] = []
        for row in rows:
            row_dict = dict(row)
            title = extract_title_anchor(row_dict["text"])
            if not title or not title.endswith("方"):
                continue
            if title not in catalog:
                catalog[title] = {
                    "canonical_name": title,
                    "record_id": row_dict["record_id"],
                    "chapter_id": row_dict["chapter_id"],
                    "chapter_name": row_dict["chapter_name"],
                }
            alias_keys = {
                normalize_formula_lookup_text(title, keep_formula_suffix=True),
                normalize_formula_lookup_text(title, keep_formula_suffix=False),
            }
            for alias_key in alias_keys:
                if not alias_key:
                    continue
                alias_lookup.setdefault(alias_key, [])
                if title not in alias_lookup[alias_key]:
                    alias_lookup[alias_key].append(title)
                alias_records.append({"alias_key": alias_key, "canonical_name": title})

        alias_records.sort(key=lambda item: (-len(item["alias_key"]), item["alias_key"], item["canonical_name"]))
        return catalog, alias_records, alias_lookup

    def _detect_comparison_query(self, query_text: str) -> dict[str, Any] | None:
        compact_query = compact_whitespace(query_text)
        has_supported_keyword = any(keyword in compact_query for keyword in COMPARISON_KEYWORDS)
        mentions = self._find_formula_mentions(compact_query)

        if len(mentions) >= COMPARISON_ENTITY_LIMIT and any(hint in compact_query for hint in UNSUPPORTED_COMPARISON_HINTS):
            return {
                "valid": False,
                "reason": "unsupported_comparison",
                "mentions": mentions,
            }

        if not has_supported_keyword:
            return None

        if len(mentions) != COMPARISON_ENTITY_LIMIT:
            return {
                "valid": False,
                "reason": "entity_resolution_failed" if len(mentions) < COMPARISON_ENTITY_LIMIT else "too_many_entities",
                "mentions": mentions,
            }

        entities: list[dict[str, Any]] = []
        for index, mention in enumerate(mentions, start=1):
            entity = dict(self._formula_catalog[mention["canonical_name"]])
            entity["group_label"] = "A" if index == 1 else "B"
            entity["mention_span"] = [mention["start"], mention["end"]]
            entities.append(entity)

        return {
            "valid": True,
            "reason": "comparison_detected",
            "mentions": mentions,
            "entities": entities,
            "query_kind": self._infer_comparison_query_kind(compact_query),
            "requested_context": any(hint in compact_query for hint in COMPARISON_CONTEXT_HINTS),
        }

    def _infer_comparison_query_kind(self, query_text: str) -> str:
        if "异同" in query_text:
            return "same_and_diff"
        if "多了什么" in query_text or "少了什么" in query_text:
            return "delta"
        return "difference"

    def _find_formula_mentions(self, query_text: str) -> list[dict[str, Any]]:
        normalized_query = normalize_formula_lookup_text(query_text, keep_formula_suffix=True)
        selected: list[dict[str, Any]] = []
        occupied_spans: list[tuple[int, int]] = []
        selected_formulas: set[str] = set()

        for alias in self._formula_aliases:
            alias_key = alias["alias_key"]
            search_from = 0
            while True:
                start = normalized_query.find(alias_key, search_from)
                if start < 0:
                    break
                end = start + len(alias_key)
                search_from = start + 1
                if alias["canonical_name"] in selected_formulas:
                    continue
                if any(max(start, left) < min(end, right) for left, right in occupied_spans):
                    continue
                selected.append(
                    {
                        "canonical_name": alias["canonical_name"],
                        "alias_key": alias_key,
                        "start": start,
                        "end": end,
                    }
                )
                occupied_spans.append((start, end))
                selected_formulas.add(alias["canonical_name"])
                break

        selected.sort(key=lambda item: item["start"])
        return selected

    def _assemble_comparison(self, query_text: str, comparison_plan: dict[str, Any]) -> dict[str, Any]:
        if not comparison_plan["valid"]:
            refuse_reason = self._build_comparison_refuse_reason(comparison_plan["reason"])
            self._last_comparison_debug = {
                "query": query_text,
                "comparison_detected": True,
                "comparison_valid": False,
                "reason": comparison_plan["reason"],
                "recognized_entities": [mention["canonical_name"] for mention in comparison_plan.get("mentions", [])],
                "structured_difference_count": 0,
            }
            return self._compose_payload(
                query_text=query_text,
                answer_mode="refuse",
                answer_text="当前无法基于稳定的双实体识别来组织比较答案，暂不直接作答。",
                primary=[],
                secondary=[],
                review=[],
                review_notice=None,
                disclaimer=self._build_disclaimer("refuse", False, False),
                refuse_reason=refuse_reason,
                suggested_followup_questions=list(COMPARISON_REFUSE_GUIDANCE_TEMPLATES),
                citations=[],
            )

        entity_bundles = [self._build_comparison_entity_bundle(entity) for entity in comparison_plan["entities"]]
        answer_mode = self._determine_comparison_mode(comparison_plan, entity_bundles)
        structured_lines = self._build_comparison_lines(comparison_plan, entity_bundles, answer_mode)

        if answer_mode == "strong":
            primary = []
            secondary = []
            review = []
            for bundle in entity_bundles:
                primary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="primary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["formula_rows"][:COMPARISON_FORMULA_TITLE_LIMIT]
                )
                secondary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["support_rows"][:COMPARISON_SUPPORT_LIMIT]
                )
                review.extend(
                    self._build_evidence_item(
                        row,
                        display_role="review",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["review_rows"][:COMPARISON_REVIEW_LIMIT]
                )
        else:
            primary = []
            secondary = []
            review = []
            for bundle in entity_bundles:
                secondary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                        risk_flags_override=dedupe_strings(self._extract_risk_flags(row) + ["comparison_mode_demoted"]),
                    )
                    for row in bundle["formula_rows"][:COMPARISON_FORMULA_TITLE_LIMIT]
                )
                secondary.extend(
                    self._build_evidence_item(
                        row,
                        display_role="secondary",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                        risk_flags_override=dedupe_strings(self._extract_risk_flags(row) + ["comparison_mode_demoted"]),
                    )
                    for row in bundle["support_rows"][:COMPARISON_SUPPORT_LIMIT]
                )
                review.extend(
                    self._build_evidence_item(
                        row,
                        display_role="review",
                        title_override=f"{bundle['group_label']} · {bundle['canonical_name']}",
                    )
                    for row in bundle["review_rows"][:COMPARISON_REVIEW_LIMIT]
                )

        answer_text = "\n".join(structured_lines)
        review_notice = self._build_comparison_review_notice(answer_mode, comparison_plan, entity_bundles)
        disclaimer = self._build_comparison_disclaimer(answer_mode, bool(secondary), bool(review))
        citations = self._build_comparison_citations(answer_mode, primary, secondary, review)
        refuse_reason = None
        followups: list[str] = []
        self._last_comparison_debug = {
            "query": query_text,
            "comparison_detected": True,
            "comparison_valid": True,
            "query_kind": comparison_plan["query_kind"],
            "requested_context": comparison_plan["requested_context"],
            "answer_mode": answer_mode,
            "recognized_entities": [
                {
                    "group_label": bundle["group_label"],
                    "canonical_name": bundle["canonical_name"],
                    "formula_row_found": bool(bundle["formula_rows"]),
                    "support_row_found": bool(bundle["support_rows"]),
                    "context_supported_by_main_passage": bundle["context_source"] == "main_passages",
                }
                for bundle in entity_bundles
            ],
            "structured_difference_count": max(len(structured_lines) - 1, 0),
        }
        return self._compose_payload(
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

    def _compose_payload(
        self,
        *,
        query_text: str,
        answer_mode: str,
        answer_text: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
        review_notice: str | None,
        disclaimer: str | None,
        refuse_reason: str | None,
        suggested_followup_questions: list[str],
        citations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        display_sections = self._build_display_sections(
            answer_text=answer_text,
            primary=primary,
            secondary=secondary,
            review=review,
            citations=citations,
            review_notice=review_notice,
            suggested_followup_questions=suggested_followup_questions,
        )
        return {
            "query": query_text,
            "answer_mode": answer_mode,
            "answer_text": answer_text,
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "review_materials": review,
            "disclaimer": disclaimer,
            "review_notice": review_notice,
            "refuse_reason": refuse_reason,
            "suggested_followup_questions": suggested_followup_questions,
            "citations": citations,
            "display_sections": display_sections,
        }

    def _fetch_record_meta(self, record_id: str) -> dict[str, Any]:
        cached = self._record_cache.get(record_id)
        if cached:
            return cached
        row = self.engine.conn.execute(
            """
            SELECT
                record_id,
                source_object,
                retrieval_text,
                chapter_id,
                chapter_name
            FROM vw_retrieval_records_unified
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            meta = {
                "record_id": record_id,
                "source_object": None,
                "retrieval_text": "",
                "chapter_id": None,
                "chapter_name": None,
            }
        else:
            meta = dict(row)
        self._record_cache[record_id] = meta
        return meta

    def _derive_title(self, row: dict[str, Any], full_text: str) -> str:
        topic_anchor = row.get("topic_anchor")
        if topic_anchor:
            return topic_anchor
        first_line = first_meaningful_line(full_text)
        if "：" in first_line:
            head = first_line.split("：", 1)[0].strip()
            if 1 <= len(head) <= 24:
                return head
        if ":" in first_line:
            head = first_line.split(":", 1)[0].strip()
            if 1 <= len(head) <= 24:
                return head
        if first_line:
            return snippet_text(first_line, limit=24)
        return row["record_id"]

    def _build_evidence_item(
        self,
        row: dict[str, Any],
        display_role: str,
        title_override: str | None = None,
        risk_flags_override: list[str] | None = None,
    ) -> dict[str, Any]:
        meta = self._fetch_record_meta(row["record_id"])
        full_text = meta["retrieval_text"] or row.get("text_preview", "")
        title = title_override or self._derive_title(row, full_text)
        risk_flags = risk_flags_override if risk_flags_override is not None else self._extract_risk_flags(row)
        return {
            "record_id": row["record_id"],
            "record_type": row["source_object"],
            "display_role": display_role,
            "title": title,
            "evidence_level": row["evidence_level"],
            "chapter_id": row["chapter_id"],
            "chapter_title": row["chapter_name"],
            "snippet": snippet_text(full_text),
            "risk_flags": list(risk_flags),
        }

    def _build_answer_text(
        self,
        retrieval: dict[str, Any],
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> str:
        mode = retrieval["mode"]
        query_theme = retrieval["query_request"].get("query_theme", {})
        query_anchor = query_theme.get("anchor") or retrieval["query_request"]["query_text_normalized"]

        if mode == "strong":
            if query_theme.get("type") == "formula_name":
                header = f"根据主依据，与“{query_anchor}”直接对应的条文主要有："
            else:
                header = "根据主依据，直接相关的主条如下："
            lines = [header]
            for idx, item in enumerate(primary[:3], start=1):
                lines.append(f"{idx}. {item['snippet']}")
            return "\n".join(lines)

        if mode == "weak_with_review_notice":
            lead = "正文强证据不足，以下内容需核对，暂不能视为确定答案。"
            if secondary:
                return f"{lead} 当前可先参考辅助材料：{secondary[0]['snippet']}"
            if review:
                return f"{lead} 当前仅检索到风险层材料：{review[0]['snippet']}"
            return lead

        return "当前未检索到足以支撑回答的依据，暂不提供答案。"

    def _build_review_notice(self, answer_mode: str) -> str | None:
        if answer_mode == "strong":
            return "以下补充依据与核对材料仅作说明，不作为主依据。"
        if answer_mode == "weak_with_review_notice":
            return "正文强证据不足，以下内容需核对，不应视为确定答案。"
        return None

    def _build_disclaimer(self, answer_mode: str, has_secondary: bool, has_review: bool) -> str | None:
        if answer_mode == "strong":
            if has_secondary or has_review:
                return "主证据优先；补充依据与核对材料不参与主结论判定。"
            return None
        if answer_mode == "weak_with_review_notice":
            return "当前只输出弱表述与核对材料，不输出确定性答案。"
        if answer_mode == "refuse":
            return "当前为统一拒答结构，不输出推测性答案。"
        return None

    def _build_refuse_reason(self, answer_mode: str) -> str | None:
        if answer_mode != "refuse":
            return None
        return "未检索到足以支撑回答的主证据、辅助证据或可供核对的风险材料。"

    def _build_followups(self, answer_mode: str) -> list[str]:
        if answer_mode == "refuse":
            return list(REFUSE_GUIDANCE_TEMPLATES)
        return []

    def _build_citations(
        self,
        answer_mode: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        citation_source: list[dict[str, Any]]
        if answer_mode == "strong":
            citation_source = primary
        elif answer_mode == "weak_with_review_notice":
            citation_source = secondary + review
        else:
            citation_source = []

        citations: list[dict[str, Any]] = []
        for index, item in enumerate(citation_source, start=1):
            citations.append(
                {
                    "citation_id": f"c{index}",
                    "record_id": item["record_id"],
                    "record_type": item["record_type"],
                    "title": item["title"],
                    "evidence_level": item["evidence_level"],
                    "snippet": item["snippet"],
                    "chapter_id": item["chapter_id"],
                    "chapter_title": item["chapter_title"],
                    "citation_role": item["display_role"],
                }
            )
        return citations

    def _build_display_sections(
        self,
        answer_text: str,
        primary: list[dict[str, Any]],
        secondary: list[dict[str, Any]],
        review: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        review_notice: str | None,
        suggested_followup_questions: list[str],
    ) -> list[dict[str, Any]]:
        return [
            {
                "section_id": "answer",
                "title": "回答",
                "section_type": "text",
                "visible": True,
                "field": "answer_text",
                "summary": snippet_text(answer_text, limit=48),
            },
            {
                "section_id": "review_notice",
                "title": "核对提示",
                "section_type": "notice",
                "visible": bool(review_notice),
                "field": "review_notice",
                "summary": review_notice or "",
            },
            {
                "section_id": "primary_evidence",
                "title": "主依据",
                "section_type": "slot_ref",
                "visible": bool(primary),
                "field": "primary_evidence",
                "item_count": len(primary),
            },
            {
                "section_id": "secondary_evidence",
                "title": "补充依据",
                "section_type": "slot_ref",
                "visible": bool(secondary),
                "field": "secondary_evidence",
                "item_count": len(secondary),
            },
            {
                "section_id": "review_materials",
                "title": "核对材料",
                "section_type": "slot_ref",
                "visible": bool(review),
                "field": "review_materials",
                "item_count": len(review),
            },
            {
                "section_id": "citations",
                "title": "引用",
                "section_type": "slot_ref",
                "visible": bool(citations),
                "field": "citations",
                "item_count": len(citations),
            },
            {
                "section_id": "refusal_guidance",
                "title": "改问建议",
                "section_type": "list",
                "visible": bool(suggested_followup_questions),
                "field": "suggested_followup_questions",
                "item_count": len(suggested_followup_questions),
            },
        ]


def build_smoke_markdown(command: str, results: list[dict[str, Any]]) -> str:
    strong_result = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    weak_result = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    refuse_result = next(result for result in results if result["example_id"] == "refuse_no_match")

    strong_primary_ids = [row["record_id"] for row in strong_result["primary_evidence"]]
    lines = [
        "# Hybrid Answer Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 结论",
        "",
        "- retrieval_backend: `hybrid_rrf_rerank`",
        "",
    ]

    for result in results:
        lines.append(
            f"- `{result['query']}` -> mode=`{result['answer_mode']}`, "
            f"primary={len(result['primary_evidence'])}, "
            f"secondary={len(result['secondary_evidence'])}, "
            f"review={len(result['review_materials'])}, "
            f"citations={len(result['citations'])}"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- strong_precision_patch_preserved: `{'ZJSHL-CH-009' not in ''.join(strong_primary_ids)}`",
            f"- weak_review_notice_present: `{bool(weak_result['review_notice'])}`",
            f"- refuse_guidance_present: `{bool(refuse_result['suggested_followup_questions'])}`",
        ]
    )

    for result in results:
        section_summary = [
            {
                "section_id": section["section_id"],
                "visible": section["visible"],
                "field": section["field"],
            }
            for section in result["display_sections"]
        ]
        lines.extend(
            [
                "",
                f"## Query: {result['query']}",
                "",
                f"- answer_mode: `{result['answer_mode']}`",
                f"- answer_text: {result['answer_text']}",
                f"- disclaimer: {result['disclaimer'] or 'None'}",
                f"- review_notice: {result['review_notice'] or 'None'}",
                f"- refuse_reason: {result['refuse_reason'] or 'None'}",
                f"- evidence_summary: primary={len(result['primary_evidence'])}, secondary={len(result['secondary_evidence'])}, review={len(result['review_materials'])}",
                f"- citations_summary: `{json_dumps([citation['record_id'] for citation in result['citations']])}`",
                f"- display_sections: `{json_dumps(section_summary)}`",
                "",
                "### Primary Evidence",
                "",
                json_dumps(result["primary_evidence"]) if result["primary_evidence"] else "_no rows_",
                "",
                "### Secondary Evidence",
                "",
                json_dumps(result["secondary_evidence"]) if result["secondary_evidence"] else "_no rows_",
                "",
                "### Review Materials",
                "",
                json_dumps(result["review_materials"]) if result["review_materials"] else "_no rows_",
                "",
                "### Suggested Follow-up Questions",
                "",
                json_dumps(result["suggested_followup_questions"]) if result["suggested_followup_questions"] else "_no rows_",
            ]
        )

    return "\n".join(lines) + "\n"


def run_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        payload = assembler.assemble(example["query_text"])
        payload["example_id"] = example["example_id"]
        payload["expected_mode"] = example["expected_mode"]
        results.append(payload)
    return results


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    examples = {result["example_id"]: result for result in results}

    strong = examples["strong_chunk_backref"]
    if strong["answer_mode"] != "strong":
        raise AssertionError("strong_chunk_backref mode regressed")
    if not strong["primary_evidence"]:
        raise AssertionError("strong_chunk_backref missing primary evidence")
    if any(item["record_type"] != "main_passages" for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence must contain only main_passages")
    if any("ZJSHL-CH-009" in item["chapter_id"] for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence reintroduced 葛根黄芩黄连汤方-related passages")
    if any(item["record_type"] in {"passages", "ambiguous_passages"} for item in strong["primary_evidence"]):
        raise AssertionError("strong primary_evidence must not include review materials")

    weak = examples["weak_with_review_notice"]
    if weak["answer_mode"] != "weak_with_review_notice":
        raise AssertionError("weak_with_review_notice mode regressed")
    if weak["primary_evidence"]:
        raise AssertionError("weak_with_review_notice should not contain primary evidence")
    if not weak["review_notice"]:
        raise AssertionError("weak_with_review_notice missing review_notice")
    if any(item["record_type"] == "annotation_links" for item in weak["secondary_evidence"] + weak["review_materials"]):
        raise AssertionError("annotation_links must remain disabled")

    refuse = examples["refuse_no_match"]
    if refuse["answer_mode"] != "refuse":
        raise AssertionError("refuse mode regressed")
    if refuse["answer_text"] == "":
        raise AssertionError("refuse answer_text should not be empty")
    if not refuse["refuse_reason"]:
        raise AssertionError("refuse missing refuse_reason")
    if len(refuse["suggested_followup_questions"]) < 3:
        raise AssertionError("refuse missing follow-up guidance")

    for result in results:
        if any(item["record_type"] == "annotation_links" for item in result["primary_evidence"]):
            raise AssertionError("annotation_links leaked into primary_evidence")
        if any(item["record_type"] == "annotation_links" for item in result["secondary_evidence"]):
            raise AssertionError("annotation_links leaked into secondary_evidence")
        if any(item["record_type"] == "annotation_links" for item in result["review_materials"]):
            raise AssertionError("annotation_links leaked into review_materials")


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    cache_dir = resolve_project_path(args.cache_dir)
    dense_chunks_index = resolve_project_path(args.dense_chunks_index)
    dense_chunks_meta = resolve_project_path(args.dense_chunks_meta)
    dense_main_index = resolve_project_path(args.dense_main_index)
    dense_main_meta = resolve_project_path(args.dense_main_meta)
    examples_out = resolve_project_path(args.examples_out)
    smoke_out = resolve_project_path(args.smoke_checks_out)

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)

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
        log(f"[1/4] Loaded policy from {policy_path}")
        log(f"[2/4] Loaded hybrid retrieval database and dense assets from {db_path}")

        if args.query:
            payload = assembler.assemble(args.query)
            print(json_dumps(payload))
            log("[3/4] Ran single-query hybrid answer assembly")
            log("[4/4] No artifact files updated in single-query mode")
            return 0

        results = run_examples(assembler)
        assert_smoke_expectations(results)
        examples_out.write_text(json_dumps(build_examples_payload(results)) + "\n", encoding="utf-8")

        command = f"{Path(sys.executable).name} -m backend.answers.assembler"
        smoke_out.write_text(build_smoke_markdown(command, results), encoding="utf-8")
        log("[3/4] Ran default answer examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        assembler.close()


if __name__ == "__main__":
    raise SystemExit(main())
