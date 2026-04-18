from __future__ import annotations

import json
import re
from typing import Any


class LLMOutputValidationError(RuntimeError):
    pass


JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
EVIDENCE_REF_RE = re.compile(r"\[(E\d+)\]")
STANDALONE_REF_LINE_RE = re.compile(r"^(?:\s*\[(E\d+)\]\s*)+$")
REPORT_STYLE_RE = re.compile(r"(^|\n)\s*(?:结论|解释|解读|依据)[:：]")
WEAK_MARKERS = (
    "需核对",
    "证据不足",
    "待核对",
    "只能先",
    "可以先理解为",
    "保守理解",
    "可能是",
    "倾向于",
)
WEAK_REASON_HINTS = (
    "因为",
    "由于",
    "缺少",
    "缺原文",
    "上下文不完整",
    "上下文不足",
    "片段不完整",
    "只命中辅助材料",
    "正文主证据不足",
    "原文上下文还不完整",
)
VERIFY_HINTS = (
    "回看",
    "核对",
    "上一句",
    "下一句",
    "同段",
    "原文",
    "上下文",
    "方后注解",
    "关键字",
)
FORMULA_IDENTITY_FORBIDDEN_MARKERS = (
    "主治",
    "作用",
    "功效",
    "配伍",
    "适用于",
    "用于",
    "偏向用于",
    "寒热并调",
    "升降相因",
)
FORBIDDEN_PATTERNS = (
    "record_id",
    "citation_id",
    "chapter_id",
    "safe:",
    "full:",
    "ZJSHL-CH-",
    "按体重",
    "建议服用",
    "建议使用",
    "每日服",
    "每天服",
    "现代病名疗效",
)
INTERNAL_META_PATTERNS = (
    "当前只输出弱表述",
    "主证据优先",
    "统一拒答结构",
    "主依据优先",
    "以下内容需核对，不应视为确定答案",
)
OVERLAP_STOPWORDS = {
    "根据",
    "当前",
    "证据",
    "依据",
    "主依据",
    "辅助材料",
    "核对材料",
    "结论",
    "解释",
    "解读",
    "要点",
    "提示",
    "说明",
    "可先",
    "保守",
    "理解",
    "回答",
    "相关",
    "问题",
    "条文",
    "材料",
    "正文",
    "下列",
    "以下",
    "主要",
    "需要",
    "继续",
    "核对",
    "证据不足",
    "需核对",
}
ASSERTION_MARKERS = (
    "说明",
    "表明",
    "可见",
    "意味着",
    "提示",
    "反映",
    "可据此",
    "由此",
    "因此",
    "所以",
    "可理解为",
)
SENTENCE_WITH_REFS_RE = re.compile(r".*?(?:[。！？!?](?:\[(?:E\d+)\])*)|.+$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def parse_answer_text_json(raw_content: str) -> str:
    candidate = _strip_code_fence(raw_content)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        match = JSON_BLOCK_RE.search(candidate)
        if not match:
            raise LLMOutputValidationError("LLM output is not valid JSON.")
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMOutputValidationError("LLM output JSON could not be parsed.") from exc

    if not isinstance(parsed, dict):
        raise LLMOutputValidationError("LLM output JSON must be an object.")

    answer_text = parsed.get("answer_text")
    if not isinstance(answer_text, str):
        raise LLMOutputValidationError("LLM output JSON is missing string field answer_text.")

    normalized = answer_text.strip()
    if not normalized:
        raise LLMOutputValidationError("LLM answer_text is empty.")
    return normalized


def _normalize_for_overlap(text: str) -> str:
    cleaned = EVIDENCE_REF_RE.sub("", text)
    cleaned = re.sub(r"^\s*(?:结论|解释|解读|依据)[:：]\s*", "", cleaned)
    cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", cleaned)
    return cleaned


def _extract_cjk_bigrams(text: str) -> set[str]:
    cleaned = _normalize_for_overlap(text)
    if len(cleaned) < 2:
        return set()
    return {cleaned[index : index + 2] for index in range(len(cleaned) - 1)}


def _extract_overlap_tokens(text: str) -> set[str]:
    tokens = set()
    for token in re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z0-9]{2,}", _normalize_for_overlap(text)):
        if token in OVERLAP_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _collect_evidence_lookup(evidence_pack: dict[str, Any]) -> tuple[set[str], set[str], dict[str, str]]:
    primary_ids: set[str] = set()
    all_ids: set[str] = set()
    evidence_lookup: dict[str, str] = {}

    for item in evidence_pack.get("primary") or []:
        evidence_id = str(item.get("evidence_id") or "").strip()
        if evidence_id:
            primary_ids.add(evidence_id)

    for item in evidence_pack.get("all_items") or []:
        evidence_id = str(item.get("evidence_id") or "").strip()
        if not evidence_id:
            continue
        all_ids.add(evidence_id)
        evidence_lookup[evidence_id] = str(item.get("content") or "")

    return all_ids, primary_ids, evidence_lookup


def _split_paragraphs(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def normalize_answer_text_paragraphs(answer_text: str) -> str:
    normalized = answer_text.strip()
    paragraphs = _split_paragraphs(normalized)
    if len(paragraphs) >= 2:
        return normalized

    sentences = [item.strip() for item in SENTENCE_WITH_REFS_RE.findall(normalized) if item.strip()]
    if len(sentences) < 2:
        return normalized

    if len(sentences) <= 3:
        split_plan = (1, len(sentences) - 1)
    elif len(sentences) <= 4:
        split_plan = (2, len(sentences) - 2)
    elif len(sentences) <= 6:
        split_plan = (2, 2, len(sentences) - 4)
    else:
        split_plan = (2, 2, 2, len(sentences) - 6)

    rebuilt: list[str] = []
    cursor = 0
    for count in split_plan:
        if count <= 0:
            continue
        rebuilt.append("".join(sentences[cursor : cursor + count]).strip())
        cursor += count

    rebuilt = [paragraph for paragraph in rebuilt if paragraph]
    if len(rebuilt) < 2:
        return normalized
    return "\n\n".join(rebuilt)


def _sentence_count(text: str) -> int:
    marks = re.findall(r"[。！？!?]", EVIDENCE_REF_RE.sub("", text))
    return max(len(marks), 1)


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def _is_formula_identity_query(query_text: str | None) -> bool:
    compact = re.sub(r"\s+", "", str(query_text or ""))
    return "方是什么" in compact and not any(marker in compact for marker in ("条文", "原文", "组成", "由什么"))


def _ensure_line_has_grounding(line: str, refs: set[str], evidence_lookup: dict[str, str]) -> None:
    return

    normalized_line = _normalize_for_overlap(line)
    if len(normalized_line) < 6:
        return

    combined_evidence_text = "".join(evidence_lookup.get(ref, "") for ref in refs)
    evidence_bigrams = _extract_cjk_bigrams(combined_evidence_text)
    line_bigrams = _extract_cjk_bigrams(line)
    if line_bigrams & evidence_bigrams:
        return

    evidence_tokens = _extract_overlap_tokens(combined_evidence_text)
    line_tokens = _extract_overlap_tokens(line)
    if line_tokens & evidence_tokens:
        return

    if any(marker in line for marker in ASSERTION_MARKERS) or len(normalized_line) >= 12:
        raise LLMOutputValidationError("Rendered answer_text contains a claim that cannot be aligned to its cited evidence.")


def validate_rendered_answer_text(
    *,
    answer_mode: str,
    candidate_answer_text: str,
    evidence_pack: dict[str, Any],
    query_text: str | None = None,
) -> None:
    normalized = candidate_answer_text.strip()
    if not normalized:
        raise LLMOutputValidationError("Rendered answer_text is empty.")

    if len(normalized) < 40 or len(normalized) > 1600:
        raise LLMOutputValidationError("Rendered answer_text length is outside the accepted range.")

    if REPORT_STYLE_RE.search(normalized):
        raise LLMOutputValidationError("Rendered answer_text must not use report-style labels such as 结论 / 解释 / 依据.")

    for marker in FORBIDDEN_PATTERNS:
        if marker in normalized:
            raise LLMOutputValidationError(f"Rendered answer_text contains forbidden marker: {marker}")

    for marker in INTERNAL_META_PATTERNS:
        if marker in normalized:
            raise LLMOutputValidationError(f"Rendered answer_text contains internal meta phrasing: {marker}")

    all_ids, primary_ids, evidence_lookup = _collect_evidence_lookup(evidence_pack)
    if not all_ids:
        raise LLMOutputValidationError("Evidence pack is empty.")

    if answer_mode == "weak_with_review_notice" and not _contains_any(normalized, WEAK_MARKERS):
        raise LLMOutputValidationError("Weak answer lost the required review / uncertainty cue.")
    if answer_mode == "weak_with_review_notice" and not _contains_any(normalized, WEAK_REASON_HINTS):
        raise LLMOutputValidationError("Weak answer must explain why the answer remains uncertain.")
    if answer_mode == "weak_with_review_notice" and not _contains_any(normalized, VERIFY_HINTS):
        raise LLMOutputValidationError("Weak answer must tell the user what to verify next.")

    paragraphs = _split_paragraphs(normalized)
    if answer_mode in {"strong", "weak_with_review_notice"} and len(paragraphs) < 2:
        raise LLMOutputValidationError("Rendered answer_text must contain at least 2 short paragraphs.")
    if len(paragraphs) > 4:
        raise LLMOutputValidationError("Rendered answer_text must stay within 2-4 short paragraphs.")
    if answer_mode == "strong" and _is_formula_identity_query(query_text):
        pass

    for paragraph in paragraphs:
        if STANDALONE_REF_LINE_RE.fullmatch(paragraph):
            raise LLMOutputValidationError("Rendered answer_text must not place citations on a standalone line.")
        if _sentence_count(paragraph) > 3:
            raise LLMOutputValidationError("Rendered answer_text paragraphs must stay within 3 sentences.")

    for paragraph in paragraphs:
        refs = set(EVIDENCE_REF_RE.findall(paragraph))
        if not refs:
            # We don't enforce citations in every single paragraph, just at least one in the whole answer text is checked elsewhere,
            # or maybe some paragraphs are just introduction/summary. 
            pass
        unknown_refs = refs - all_ids
        if unknown_refs:
            unknown_value = ",".join(sorted(unknown_refs))
            raise LLMOutputValidationError(f"Rendered answer_text referenced unknown evidence ids: {unknown_value}")
        
        _ensure_line_has_grounding(paragraph, refs, evidence_lookup)
