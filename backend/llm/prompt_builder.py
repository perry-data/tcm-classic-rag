from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .client import ModelStudioLLMConfig


@dataclass(frozen=True)
class PromptEnvelope:
    system_instruction: str
    user_prompt: str


def _detect_query_style(query_text: str) -> str:
    normalized = str(query_text or "").strip()
    compact = re.sub(r"\s+", "", normalized)
    meaning_markers = ["是什么意思", "什么意思", "怎么理解", "含义", "为何", "为什么", "指什么", "如何理解", "这句话", "这段话", "此言", "何谓", "何解", "提醒什么"]
    if any(marker in compact for marker in meaning_markers):
        return "meaning_explanation"
    if "方是什么" in compact and not any(marker in compact for marker in ("条文", "原文", "组成", "由什么")):
        return "formula_identity"
    return "generic"


def _build_mode_style_block(answer_mode: str, query_style: str) -> str:
    if answer_mode == "strong":
        lines = [
            "strong 模式固定结构（请用自然流畅的段落，绝对禁止输出“结论：”、“解释：”、“依据：”等标题）：",
            "1. 首段（一句话回答）：先用一句人话清晰自然地回答“它是什么 / 这句话怎么理解”。",
            "2. 中段（解释段落）：用 1 段话通俗转述，说明关键字词、关系或上下文。不要逐条堆砌证据原句。",
            "3. 尾段（交代依据）：末尾用 1 句话说明“依据主要来自哪些条文或片段”，并把引用放在句末。",
        ]
        if query_style == "formula_identity":
            lines.extend(
                [
                    "",
                    "【高频问法特化：问“XX方是什么？”】",
                    "请按以下顺序自然作答：",
                    "1. 先说：这是书中的一个方名或方剂条目。",
                    "2. 再说：当前检索到的组成片段包含哪些药味或剂量（把引用放在这句末尾）。如果片段不完整，要明确提示“目前只检索到这些”。",
                    "3. 如果未检索到主治或证候，绝对不要硬补；用一句话提示“需要回到条文/方后注解处核对主治语境”。",
                ]
            )
        elif query_style == "meaning_explanation":
            lines.extend(
                [
                    "",
                    "【高频问法特化：问古文或术语“是什么意思”】",
                    "请按以下顺序自然作答：",
                    "1. 第 1 段（一句话白话解释）：用自然中文，把“它在说什么/提醒什么”讲明白。禁止先讲系统规则。必须直接回答，用肯定语气。",
                    "2. 第 2 段（解释关键词）：解释 1~2 个关键术语（如“益阳/损阴”“卫阳/荣阴”），只基于证据包，不引入书外医学常识。",
                    "3. 第 3 段（如有必要说明核对）：若证据有缺口（缺上下文等），给用户建议回看同段条文/上下句，并在句末附引用。若证据已充分，可省略此段。",
                ]
            )
        return "\n".join(lines)

    if answer_mode == "weak_with_review_notice":
        lines = [
            "weak_with_review_notice 模式固定结构（请用自然流畅的段落，绝对禁止输出标题）：",
            "1. 保守解释：先给一个可用的保守解释，必须使用“可能 / 倾向 / 可以先理解为”这类弱化表达，给用户一个初步认知。",
            "2. 不确定原因：接着用一句话解释为什么现在只能弱答（例如：只命中辅助材料、缺原文上下文、片段不完整等）。",
            "3. 核对路径：告诉用户该去核对哪里，点明要回看哪一句、关注哪个词、需要补哪段上下文；并在句末附上引用。",
            "4. weak 模式不能只说“需核对”或罗列材料，必须给出对用户有用的保守解释。",
        ]
        if query_style == "meaning_explanation":
            lines.extend(
                [
                    "",
                    "【高频问法特化：问古文或术语“是什么意思”】",
                    "请按以下顺序自然作答：",
                    "1. 第 1 段（一句话白话解释）：用自然中文，把“它在说什么/提醒什么”讲明白。禁止先讲系统规则。用“可能/倾向/可先理解为”弱化语气直接回答。",
                    "2. 第 2 段（解释关键词）：解释 1~2 个关键术语（如“益阳/损阴”“卫阳/荣阴”），只基于证据包，不引入书外医学常识。",
                    "3. 第 3 段（说明不确定点 + 给核对路径）：用一句话说明不确定的原因（建议使用“因为/由于/缺少”等词，例如：因为目前主要命中的是辅助材料，或者缺少完整正文上下文），并建议用户回看上一句、下一句或同段条文，并在句末附上引用。",
                ]
            )
        return "\n".join(lines)

    return "\n".join(
        [
            "refuse 模式固定结构（请用自然流畅的段落，绝对禁止输出标题）：",
            "1. 用 1-2 句话简洁说明目前无法直接回答。",
            "2. 再用 1 句话给出与书中语料相关的改问建议（例如建议改问更具体的条文或方名）。",
            "3. 绝对不罗列证据，不加任何内部规则说明。",
        ]
    )


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
        "你的职责是读取给定证据后，写出像老师在带着学生读书那样的自然中文 answer_text。"
        "回答要先把意思讲明白，再交代证据来自哪里，而不是把检索片段原样堆砌出来。"
        "你只能使用提供的 query 和 Evidence Pack。"
        "你不能新增外部知识，不能给出诊疗、剂量、现代病名疗效判断，"
        "不能补造出处、章节、条号、citation、record_id，不能改变 strong / weak_with_review_notice 的边界。"
        "必须将引用严格内联在相关句子的句末（例如：……。[E1]）。绝对禁止出现单独一行的 E1 或 [E1] 引用。"
        "绝对禁止在输出中使用任何标题（如“结论：”、“解释：”、“依据：”）。"
        "绝对禁止写成 1. 2. 3. 的机械罗列或证据列表体。"
        "如果证据不足，必须承认不确定，不能补充书外常识或自作推断。"
    )
    if strict_retry:
        instruction += (
            "当前是严格重试模式："
            "请尽量沿用证据中的原词或近距离改写；"
            "不要使用没有证据支撑的抽象总结；"
            "不要写成 1. 2. 3. 的机械罗列；"
            "绝对禁止输出“结论：”、“解释：”、“依据：”等标题，禁止输出“当前只输出弱表述”、“为避免越界”、“为主证据补充”之类内部话术；"
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
    query_style = _detect_query_style(query_text)
    available_ids = list(evidence_pack.get("all_evidence_ids") or [])
    available_id_block = " ".join(available_ids) if available_ids else "_none_"
    body_allowed_ids = [item.get("evidence_id") for item in primary_rows] if answer_mode == "strong" else available_ids
    body_allowed_id_block = " ".join([item for item in body_allowed_ids if item]) if body_allowed_ids else "_none_"

    blocks = [
        "[answer_mode]",
        answer_mode,
        "[user_query]",
        query_text,
        "[query_style]",
        query_style,
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
                "先阅读 Evidence Pack，提炼最重要的 2-4 个证据要点，再写 answer_text。"
                "answer_text 必须是自然流畅的解释型、研读支持型回答，绝对不能是证据拼贴或日志报告。"
            ),
            (
                "[hard_constraints]\n"
                "1. 只能依据上述材料表达，不得补充书外知识。\n"
                "2. 不得输出诊疗建议、剂量建议、现代病名疗效判断。\n"
                "3. 不得新增或臆造 citation、record_id、条号、章节号、书名对比。\n"
                "4. strong 模式只能把 primary_evidence 用作关键观点依据；secondary/review 只能留在内部参考，不得进入正文证据标注。\n"
                "5. weak_with_review_notice 模式必须保留不确定性，明确说明为什么只能保守解释，并给出核对路径。\n"
                "6. answer_text 默认写成 2-4 段自然段落；每段单独成行，每段不超过 3 句，绝对不要机械编号。\n"
                "7. 绝对禁止使用“结论：”、“解释：”、“依据：”这种报告体标题。\n"
                "8. 绝对禁止输出“当前只输出弱表述”、“主证据优先”、“为避免越界”、“为避免越出证据边界”、“先按现有主依据作保守整理”、“比较结论优先依据”、“主证据优先…补充依据不参与”这类系统内部设定或日志话术。\n"
                "9. 引用绝对不能单独占一行，绝对不能把 E1/E2 拆成独立行；必须写成“……。[E1][E2]”这种句末内联格式。只在“承载信息的关键句”（结论句、解释句、组成片段句）句末标注引用，不需要每句话都标。\n"
                "10. 解释重点是把条文意思用自然的人话转述清楚，不要大段照抄原文，也不要只重复证据标题。\n"                "11. 正文里只能使用 body_allowed_evidence_ids 中的 [E#]；不得引用其余证据编号。\n"
                "12. 不要复述系统元数据，尤其不要输出 record_id、chapter_id、ZJSHL-CH-*、source=、section= 这类内部标记。\n"
                "13. 若证据不足以支持完整解释，也要输出可理解的保守 answer_text，绝对不能只简单罗列材料或只说一句“需核对”。\n"
                "14. 绝对禁止出现“1. 主依据写到...”、“2. 主依据写到...”这种逐条列证据原文的结构，或者“证据罗列体”。必须用自然段落讲述。\n"
                "15. 第一段必须直接回答用户的问句（如“是什么/什么意思/怎么理解”），绝对不允许第一段先解释系统规则或输出免责声明。\n"
                "16. 只输出 JSON，不要输出 markdown 代码块。JSON 至少包含："
                "{\"evidence_outline\": [{\"point\": \"...\", \"evidence_ids\": [\"E1\"]}], \"answer_text\": \"...\"}。"
            ),
            "[mode_style]\n" + _build_mode_style_block(answer_mode, query_style),
        ]
    )
    user_prompt = "\n\n".join(blocks)

    return PromptEnvelope(
        system_instruction=_system_instruction(strict_retry=strict_retry),
        user_prompt=user_prompt,
    )
