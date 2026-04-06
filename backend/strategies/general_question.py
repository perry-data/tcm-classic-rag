#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass

from backend.retrieval.minimal import compact_text, extract_focus_text, infer_query_theme


GENERAL_TRIGGER_SPECS = [
    ("应该怎么办", "management"),
    ("该怎么办", "management"),
    ("怎么办", "management"),
    ("怎么处理", "management"),
    ("如何处理", "management"),
    ("如何应对", "management"),
    ("如何治疗", "management"),
    ("如何治", "management"),
    ("有哪些情况", "overview"),
    ("有什么情况", "overview"),
    ("有什么分类", "overview"),
    ("有哪些分类", "overview"),
    ("有什么分支", "overview"),
    ("有哪些分支", "overview"),
    ("分情况", "overview"),
    ("处理思路", "overview"),
]

GENERAL_PREFIXES = (
    "请问",
    "关于",
    "对于",
    "书中",
    "文中",
    "伤寒论里",
    "伤寒论中",
    "如果问",
    "像",
    "这一类",
    "这类",
    "这种",
    "这个",
)

GENERAL_SUFFIX_NOISE = (
    "总的",
    "总体",
    "一般",
    "大体",
    "应该",
    "可以",
    "需要",
)

GENERAL_BLOCK_HINTS = (
    "条文",
    "原文",
    "出处",
    "出自",
    "是什么意思",
    "什么意思",
    "有没有提到",
    "有无提到",
    "量子纠缠",
)

FORMULA_BRANCH_PATTERNS = (
    re.compile(r"([一-龥0-9]{1,16}(?:汤|散|丸|饮|方))主之"),
    re.compile(r"宜([一-龥0-9]{1,16}(?:汤|散|丸|饮|方))"),
)

NOTE_PATTERNS = (
    re.compile(r"赵本(?:有|无|作)「[^」]*」(?:字)?"),
    re.compile(r"赵本注：?「[^」]*」"),
)


@dataclass(frozen=True)
class GeneralQuestionPlan:
    query_text: str
    topic_text: str
    normalized_topic: str
    general_kind: str
    matched_trigger: str


@dataclass(frozen=True)
class GeneralBranchMeta:
    branch_key: str
    branch_type: str
    branch_label: str
    branch_summary: str
    heuristic_score: float
    formula_name: str | None = None


def detect_general_question(query_text: str) -> GeneralQuestionPlan | None:
    stripped_query = query_text.strip()
    if not stripped_query:
        return None

    query_focus = extract_focus_text(stripped_query)
    query_theme = infer_query_theme(query_focus)
    if query_theme.get("type") == "formula_name":
        return None

    if any(hint in stripped_query for hint in GENERAL_BLOCK_HINTS):
        return None

    matched_trigger = ""
    general_kind = ""
    for trigger, kind in GENERAL_TRIGGER_SPECS:
        if trigger in stripped_query:
            matched_trigger = trigger
            general_kind = kind
            break

    if not matched_trigger:
        return None

    topic_text = _extract_topic_text(stripped_query, matched_trigger)
    normalized_topic = compact_text(topic_text)
    if len(normalized_topic) < 2:
        return None

    topic_theme = infer_query_theme(extract_focus_text(topic_text))
    if topic_theme.get("type") == "formula_name":
        return None

    if normalized_topic in {compact_text(trigger) for trigger, _ in GENERAL_TRIGGER_SPECS}:
        return None

    return GeneralQuestionPlan(
        query_text=stripped_query,
        topic_text=topic_text,
        normalized_topic=normalized_topic,
        general_kind=general_kind,
        matched_trigger=matched_trigger,
    )


def analyze_general_branch(
    text: str,
    topic_text: str,
    *,
    general_kind: str,
    chapter_matches_topic: bool,
) -> GeneralBranchMeta | None:
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        return None

    condition = _extract_condition_clause(cleaned_text, topic_text)
    formula_name = _extract_formula_name(cleaned_text)
    if formula_name and condition.endswith(formula_name):
        condition = condition[: -len(formula_name)].rstrip("，,")
    text_length = len(compact_text(cleaned_text))
    chapter_bonus = 10.0 if chapter_matches_topic else 0.0
    brevity_bonus = 6.0 if text_length <= 40 else 3.0 if text_length <= 80 else -4.0

    if formula_name:
        branch_label = f"{formula_name}这一支"
        branch_summary = f"若见{condition or topic_text}，条文多归到“{formula_name}”这一支。"
        return GeneralBranchMeta(
            branch_key=formula_name,
            branch_type="formula",
            branch_label=branch_label,
            branch_summary=branch_summary,
            heuristic_score=42.0 + chapter_bonus + brevity_bonus,
            formula_name=formula_name,
        )

    if "不可" in cleaned_text:
        caution_phrase = _extract_caution_phrase(cleaned_text)
        branch_label = caution_phrase or "禁误治这一支"
        branch_summary = f"若见{condition or topic_text}，条文强调“{caution_phrase or '不可误治'}”，提示不能按单一路径处理。"
        return GeneralBranchMeta(
            branch_key=branch_label,
            branch_type="caution",
            branch_label=branch_label,
            branch_summary=branch_summary,
            heuristic_score=24.0 + chapter_bonus + brevity_bonus,
        )

    if "名曰" in cleaned_text or "名为" in cleaned_text:
        branch_label = _extract_diagnostic_label(cleaned_text)
        branch_summary = f"先看{condition or topic_text}，书中把它单列成一个分支，提示“{topic_text}”并非只有一种证候。"
        base_score = 26.0 if general_kind == "overview" else 22.0
        return GeneralBranchMeta(
            branch_key=branch_label,
            branch_type="classification",
            branch_label=branch_label,
            branch_summary=branch_summary,
            heuristic_score=base_score + chapter_bonus + brevity_bonus,
        )

    if "自愈" in cleaned_text or "则愈" in cleaned_text or "当须" in cleaned_text:
        branch_label = "病程变化这一支"
        branch_summary = f"若见{condition or topic_text}，条文还给出病程或处置变化线索，不能只按单条定法理解。"
        return GeneralBranchMeta(
            branch_key=branch_label,
            branch_type="course",
            branch_label=branch_label,
            branch_summary=branch_summary,
            heuristic_score=18.0 + chapter_bonus + brevity_bonus,
        )

    return None


def _extract_topic_text(query_text: str, matched_trigger: str) -> str:
    topic = query_text.replace(matched_trigger, "")
    topic = topic.strip().strip("？?！!。；;，,：:")
    for prefix in GENERAL_PREFIXES:
        if topic.startswith(prefix):
            topic = topic[len(prefix) :].strip()
    for suffix in GENERAL_SUFFIX_NOISE:
        if topic.endswith(suffix):
            topic = topic[: -len(suffix)].strip()
    topic = topic.strip("？?！!。；;，,：:")
    focus = extract_focus_text(topic)
    return topic if len(compact_text(topic)) >= len(focus) and topic else focus


def _clean_text(text: str) -> str:
    cleaned = text or ""
    for pattern in NOTE_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    return cleaned.strip("，,")


def _extract_formula_name(text: str) -> str | None:
    for pattern in FORMULA_BRANCH_PATTERNS:
        matched = pattern.search(text)
        if matched:
            return matched.group(1)
    return None


def _extract_condition_clause(text: str, topic_text: str) -> str:
    sentence = re.split(r"[。；]", text, maxsplit=1)[0]
    if topic_text and topic_text in sentence:
        sentence = sentence.split(topic_text, 1)[1]
    sentence = sentence.lstrip("，,：: ")
    for marker in ("不可", "宜", "主之", "名曰", "名为", "则愈", "自愈", "当须"):
        if marker in sentence:
            sentence = sentence.split(marker, 1)[0]
            break
    sentence = sentence.rstrip("，,")
    if "者" in sentence and sentence.index("者") <= 28:
        sentence = sentence[: sentence.index("者") + 1]
    return sentence[:28].rstrip("，,")


def _extract_caution_phrase(text: str) -> str | None:
    matched = re.search(r"(不可[^，。；]{1,14})", text)
    if matched:
        return matched.group(1)
    if "不可" in text:
        return "不可误治"
    return None


def _extract_diagnostic_label(text: str) -> str:
    if "中风" in text:
        return "先辨中风"
    if "伤寒" in text:
        return "先辨伤寒"
    return "先辨证候"
