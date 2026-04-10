from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import ModelStudioLLMConfig


@dataclass(frozen=True)
class PromptEnvelope:
    system_instruction: str
    user_prompt: str


def _format_evidence_block(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"[{title}]\n- _none_"

    lines = [f"[{title}]"]
    for item in rows:
        chapter_title = item.get("chapter_title") or "未知章节"
        lines.append(f"- {item.get('title') or '未命名证据'} | {chapter_title} | {item.get('snippet') or ''}")
    return "\n".join(lines)


def _system_instruction() -> str:
    return (
        "你是一个中医经典研读支持系统中的答案改写器。"
        "你的任务不是自由回答，而是在不改变既有证据边界、题型边界和回答模式的前提下，"
        "把给定的草稿答案整理成更自然、更清晰的中文表达。"
        "你只能使用提供的 query、draft answer 和 evidence。"
        "你不能新增外部知识，不能给出诊疗、剂量、现代病名疗效判断，"
        "不能补造出处、章节、条号、引用编号，不能改变 strong / weak_with_review_notice / refuse 的语气边界。"
    )


def build_answer_text_prompt(
    *,
    config: ModelStudioLLMConfig,
    query_text: str,
    answer_mode: str,
    baseline_answer_text: str,
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    review: list[dict[str, Any]],
) -> PromptEnvelope:
    primary_rows = primary[: config.max_primary_items]
    secondary_rows = secondary[: config.max_secondary_items]
    review_rows = review[: config.max_review_items]

    user_prompt = "\n\n".join(
        [
            "[answer_mode]",
            answer_mode,
            "[user_query]",
            query_text,
            "[draft_answer]",
            baseline_answer_text,
            _format_evidence_block("primary_evidence", primary_rows),
            _format_evidence_block("secondary_evidence", secondary_rows),
            _format_evidence_block("review_materials", review_rows),
            "[hard_constraints]\n"
            "1. 只能依据上述材料表达，不得补充书外知识。\n"
            "2. 不得输出诊疗建议、剂量建议、现代病名疗效判断。\n"
            "3. 不得新增或臆造 citation、record_id、条号、章节号、书名对比。\n"
            "4. strong 模式可做清晰归纳，但不得超出 primary evidence。\n"
            "5. weak_with_review_notice 模式必须保留不确定性，且明确“需核对”或等价提示。\n"
            "6. 如果 draft 已包含编号分支，输出时保留编号结构，不得压扁成一句话。\n"
            "7. 只输出 JSON，例如：{\"answer_text\": \"...\"}。",
        ]
    )

    return PromptEnvelope(system_instruction=_system_instruction(), user_prompt=user_prompt)
