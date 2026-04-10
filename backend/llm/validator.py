from __future__ import annotations

import json
import re


class LLMOutputValidationError(RuntimeError):
    pass


JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
NUMBERED_LINE_RE = re.compile(r"(?m)^\s*\d+\.\s+")
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


def validate_rendered_answer_text(
    *,
    answer_mode: str,
    baseline_answer_text: str,
    candidate_answer_text: str,
) -> None:
    normalized = candidate_answer_text.strip()
    if not normalized:
        raise LLMOutputValidationError("Rendered answer_text is empty.")

    if len(normalized) < 20 or len(normalized) > 1200:
        raise LLMOutputValidationError("Rendered answer_text length is outside the accepted range.")

    for marker in FORBIDDEN_PATTERNS:
        if marker in normalized:
            raise LLMOutputValidationError(f"Rendered answer_text contains forbidden marker: {marker}")

    if answer_mode == "weak_with_review_notice" and not any(marker in normalized for marker in WEAK_MARKERS):
        raise LLMOutputValidationError("Weak answer lost the required review / uncertainty cue.")

    baseline_has_numbering = bool(NUMBERED_LINE_RE.search(baseline_answer_text))
    candidate_has_numbering = bool(NUMBERED_LINE_RE.search(normalized))
    if baseline_has_numbering and not candidate_has_numbering:
        raise LLMOutputValidationError("Rendered answer_text broke the numbered structure required by the baseline.")
