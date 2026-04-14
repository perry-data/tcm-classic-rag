from __future__ import annotations

import json
import re
from typing import Any


class LLMOutputValidationError(RuntimeError):
    pass


JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
NUMBERED_LINE_RE = re.compile(r"(?m)^\s*\d+\.\s+")
SINGLE_NUMBERED_LINE_RE = re.compile(r"^\s*\d+\.\s+")
EVIDENCE_REF_RE = re.compile(r"\[(E\d+)\]")
WEAK_MARKERS = (
    "需核对",
    "不应视为确定答案",
    "暂不能视为确定答案",
    "证据不足",
    "仅作参考",
    "待核对",
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
OVERLAP_STOPWORDS = {
    "根据",
    "当前",
    "证据",
    "依据",
    "主依据",
    "辅助材料",
    "核对材料",
    "结论",
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
    cleaned = re.sub(r"^\s*\d+\.\s*", "", cleaned)
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


def _ensure_line_has_grounding(line: str, refs: set[str], evidence_lookup: dict[str, str]) -> None:
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
) -> None:
    normalized = candidate_answer_text.strip()
    if not normalized:
        raise LLMOutputValidationError("Rendered answer_text is empty.")

    if len(normalized) < 40 or len(normalized) > 1600:
        raise LLMOutputValidationError("Rendered answer_text length is outside the accepted range.")

    for marker in FORBIDDEN_PATTERNS:
        if marker in normalized:
            raise LLMOutputValidationError(f"Rendered answer_text contains forbidden marker: {marker}")

    all_ids, primary_ids, evidence_lookup = _collect_evidence_lookup(evidence_pack)
    if not all_ids:
        raise LLMOutputValidationError("Evidence pack is empty.")

    if answer_mode == "weak_with_review_notice" and not any(marker in normalized for marker in WEAK_MARKERS):
        raise LLMOutputValidationError("Weak answer lost the required review / uncertainty cue.")

    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    if len(lines) < 3:
        raise LLMOutputValidationError("Rendered answer_text must contain one conclusion line plus at least two numbered points.")

    summary_line = lines[0]
    point_lines = lines[1:]
    if SINGLE_NUMBERED_LINE_RE.match(summary_line):
        raise LLMOutputValidationError("Rendered answer_text must start with a one-sentence conclusion before numbered points.")
    if len(point_lines) < 2 or len(point_lines) > 4:
        raise LLMOutputValidationError("Rendered answer_text must contain 2-4 numbered points.")
    if any(not SINGLE_NUMBERED_LINE_RE.match(line) for line in point_lines):
        raise LLMOutputValidationError("Rendered answer_text points must use numbered lines.")

    for line in lines:
        refs = set(EVIDENCE_REF_RE.findall(line))
        if not refs:
            raise LLMOutputValidationError("Each conclusion or numbered point must include at least one [E#] reference.")
        unknown_refs = refs - all_ids
        if unknown_refs:
            unknown_value = ",".join(sorted(unknown_refs))
            raise LLMOutputValidationError(f"Rendered answer_text referenced unknown evidence ids: {unknown_value}")
        if answer_mode == "strong" and any(ref not in primary_ids for ref in refs):
            raise LLMOutputValidationError("Strong answer cited non-primary evidence in answer_text.")
        _ensure_line_has_grounding(line, refs, evidence_lookup)
