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
        "把证据整理成“先给结论、再解释条文意思、再交代依据”的可核验 answer_text。"
        "回答应像在辅助用户研读经典，而不是把检索片段原样堆出来。"
        "你只能使用提供的 query 和 Evidence Pack。"
        "你不能新增外部知识，不能给出诊疗、剂量、现代病名疗效判断，"
        "不能补造出处、章节、条号、citation、record_id，不能改变 strong / weak_with_review_notice 的边界。"
        "所有关键结论和解释都必须显式标注来自 Evidence Pack 的 [E#]。"
        "如果证据不足，必须承认不确定，不能补充书外常识或自作推断。"
    )
    if strict_retry:
        instruction += (
            "当前是严格重试模式："
            "请尽量沿用证据中的原词或近距离改写；"
            "不要使用没有证据支撑的抽象总结；"
            "不要写成 1. 2. 3. 的机械罗列；"
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
    body_allowed_ids = [item.get("evidence_id") for item in primary_rows] if answer_mode == "strong" else available_ids
    body_allowed_id_block = " ".join([item for item in body_allowed_ids if item]) if body_allowed_ids else "_none_"

    blocks = [
        "[answer_mode]",
        answer_mode,
        "[user_query]",
        query_text,
        "[available_evidence_ids]",
        available_id_block,
        "[body_allowed_evidence_ids]",
        body_allowed_id_block,
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
                "answer_text 必须是解释型、研读支持型回答，而不是证据拼贴。"
            ),
            (
                "[hard_constraints]\n"
                "1. 只能依据上述材料表达，不得补充书外知识。\n"
                "2. 不得输出诊疗建议、剂量建议、现代病名疗效判断。\n"
                "3. 不得新增或臆造 citation、record_id、条号、章节号、书名对比。\n"
                "4. strong 模式只能把 primary_evidence 用作关键观点依据；secondary/review 只能留在内部参考，不得进入正文证据标注。\n"
                "5. weak_with_review_notice 模式必须保留不确定性，明确写出“需核对”“证据不足”或等价提示。\n"
                "6. answer_text 默认采用 3-5 行短段结构，不要机械编号，推荐固定写法：\n"
                "   - 第 1 行：`结论：... [E#]`\n"
                "   - 中间 1-3 行：`解释：... [E#]`\n"
                "   - 最后 1 行：`依据：... [E#]`\n"
                "7. 每行以自然语言解释为主，每行 1-2 句；除非用户明确要求比较或分支枚举，否则不要写成 1. 2. 3. 条目清单。\n"
                "8. 解释重点是把条文意思说清楚，不要大段照抄原文，也不要只重复证据标题。\n"
                "9. 正文里只能使用 body_allowed_evidence_ids 中的 [E#]；不得引用其余证据编号。\n"
                "10. 不要复述系统元数据，尤其不要输出 record_id、chapter_id、ZJSHL-CH-*、source=、section= 这类内部标记。\n"
                "11. 若证据不足以支持完整解释，也要输出保守 answer_text，并明确说明不确定。\n"
                "12. 只输出 JSON，不要输出 markdown 代码块。JSON 至少包含："
                "{\"evidence_outline\": [{\"point\": \"...\", \"evidence_ids\": [\"E1\"]}], \"answer_text\": \"...\"}。"
            ),
        ]
    )
    user_prompt = "\n\n".join(blocks)

    return PromptEnvelope(
        system_instruction=_system_instruction(strict_retry=strict_retry),
        user_prompt=user_prompt,
    )
