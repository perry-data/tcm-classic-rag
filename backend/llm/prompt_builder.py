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
        lines.append(
            "\n".join(
                [
                    (
                        f"- {item.get('evidence_id') or 'E?'}"
                        f" | source={item.get('source_type') or 'unknown'}"
                        f" | section={item.get('section_label') or '未标明章节'}"
                        f" | title={item.get('title') or '未命名证据'}"
                    ),
                    f"  content={item.get('content') or ''}",
                ]
            )
        )
    return "\n".join(lines)


def _system_instruction(*, strict_retry: bool) -> str:
    instruction = (
        "你是一个中医经典研读支持系统中的证据约束型回答生成器。"
        "你的职责不是自由发挥，也不是只润色草稿，而是读取给定证据后，"
        "先提炼证据要点，再基于证据组织出可核验的解释型 answer_text。"
        "你只能使用提供的 query 和 Evidence Pack。"
        "你不能新增外部知识，不能给出诊疗、剂量、现代病名疗效判断，"
        "不能补造出处、章节、条号、citation、record_id，不能改变 strong / weak_with_review_notice 的边界。"
        "所有关键结论和每个编号要点都必须显式标注来自 Evidence Pack 的 [E#]。"
        "如果证据不足，必须承认不确定，不能补充书外常识或自作推断。"
    )
    if strict_retry:
        instruction += (
            "当前是严格重试模式："
            "请尽量沿用证据中的原词或近距离改写；"
            "不要使用没有证据支撑的抽象总结；"
            "如果某个说法无法直接对应证据，请删掉或改成不确定提示。"
        )
    return instruction


def build_answer_text_prompt(
    *,
    config: ModelStudioLLMConfig,
    query_text: str,
    answer_mode: str,
    evidence_pack: dict[str, Any],
    strict_retry: bool = False,
    retry_reason: str | None = None,
) -> PromptEnvelope:
    primary_rows = list(evidence_pack.get("primary") or [])[: config.max_primary_items]
    secondary_rows = list(evidence_pack.get("secondary") or [])[: config.max_secondary_items]
    review_rows = list(evidence_pack.get("review") or [])[: config.max_review_items]
    available_ids = list(evidence_pack.get("all_evidence_ids") or [])
    available_id_block = " ".join(available_ids) if available_ids else "_none_"

    blocks = [
        "[answer_mode]",
        answer_mode,
        "[user_query]",
        query_text,
        "[available_evidence_ids]",
        available_id_block,
        _format_evidence_block("primary_evidence", primary_rows),
        _format_evidence_block("secondary_evidence", secondary_rows),
        _format_evidence_block("review_materials", review_rows),
    ]
    if retry_reason:
        blocks.extend(
            [
                "[retry_reason]",
                retry_reason,
            ]
        )
    blocks.extend(
        [
            (
                "[task]\n"
                "先阅读 Evidence Pack，提炼 2-4 个证据要点，再写 answer_text。"
                "answer_text 必须是解释型回答，而不是证据拼贴。"
            ),
            (
                "[hard_constraints]\n"
                "1. 只能依据上述材料表达，不得补充书外知识。\n"
                "2. 不得输出诊疗建议、剂量建议、现代病名疗效判断。\n"
                "3. 不得新增或臆造 citation、record_id、条号、章节号、书名对比。\n"
                "4. strong 模式只能把 primary_evidence 用作关键观点依据；secondary/review 只能留在内部参考，不得进入正文证据标注。\n"
                "5. weak_with_review_notice 模式必须保留不确定性，明确写出“需核对”“证据不足”或等价提示。\n"
                "6. answer_text 必须采用固定结构：\n"
                "   - 第 1 行：一句话结论，且带 [E#]。\n"
                "   - 第 2 行起：2-4 条编号要点，每条都要有 [E#]。\n"
                "   - 每条要点尽量只写 1 句，避免过长复述。\n"
                "7. [E#] 只能使用 available_evidence_ids 中存在的编号，不得编造。\n"
                "8. 若证据不足以支持完整解释，也要输出保守 answer_text，并明确说明不确定。\n"
                "9. 只输出 JSON，不要输出 markdown 代码块。JSON 至少包含："
                "{\"evidence_outline\": [{\"point\": \"...\", \"evidence_ids\": [\"E1\"]}], \"answer_text\": \"...\"}。"
            ),
        ]
    )
    user_prompt = "\n\n".join(blocks)

    return PromptEnvelope(
        system_instruction=_system_instruction(strict_retry=strict_retry),
        user_prompt=user_prompt,
    )
