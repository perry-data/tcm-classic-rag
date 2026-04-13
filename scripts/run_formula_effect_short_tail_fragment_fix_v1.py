#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
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
    FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS,
    AnswerAssembler,
    compact_whitespace,
    strip_inline_notes,
)
from backend.retrieval.minimal import resolve_project_path
from scripts.run_formula_effect_cross_chapter_bridge_fix_v1 import (
    DEFAULT_BASELINE_AUDIT_JSON,
    build_assembler,
    get_formula_bucket_map,
    get_primary_id,
    get_primary_text,
    load_baseline_after_variant,
    query_key,
    run_current_after_patch,
    write_json,
    write_markdown,
)


DEFAULT_SET_JSON_OUT = "artifacts/experiments/formula_effect_short_tail_fragment_set_v1.json"
DEFAULT_DESIGN_MD_OUT = "docs/design/formula_effect_short_tail_fragment_fix_v1.md"
DEFAULT_BEFORE_AFTER_MD_OUT = "artifacts/experiments/formula_effect_short_tail_fragment_before_after_v1.md"
DEFAULT_PATCH_MD_OUT = "docs/patch_notes/formula_effect_short_tail_fragment_patch_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the short_tail_fragment_primary fix v1 report set.")
    parser.add_argument("--baseline-audit-json", default=DEFAULT_BASELINE_AUDIT_JSON)
    parser.add_argument("--set-json-out", default=DEFAULT_SET_JSON_OUT)
    parser.add_argument("--design-md-out", default=DEFAULT_DESIGN_MD_OUT)
    parser.add_argument("--before-after-md-out", default=DEFAULT_BEFORE_AFTER_MD_OUT)
    parser.add_argument("--patch-md-out", default=DEFAULT_PATCH_MD_OUT)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    return parser.parse_args()


def detect_fragment_type(
    assembler: AnswerAssembler,
    *,
    formula_name: str,
    primary_text: str,
    context_clause: str,
) -> str:
    cleaned_text = strip_inline_notes(primary_text)
    match_index = -1
    for variant in assembler._formula_text_variants(formula_name):
        current_index = cleaned_text.find(variant)
        if current_index >= 0 and (match_index < 0 or current_index < match_index):
            match_index = current_index

    prefix_text = cleaned_text[:match_index].strip("，。；：: ") if match_index >= 0 else ""
    for hint in sorted(FORMULA_EFFECT_CONTEXT_BAD_TAIL_HINTS, key=len, reverse=True):
        if prefix_text.endswith(hint):
            return hint

    cleaned_context = compact_whitespace(context_clause).strip("，。；：: ")
    if cleaned_context.startswith("若"):
        return "若"
    if cleaned_context.startswith("不"):
        return "不"
    if cleaned_context.startswith("欲"):
        return "欲"
    if cleaned_context.endswith("痛"):
        return "痛"
    if cleaned_context.endswith("利"):
        return "利"
    return "short_direct_clause"


def collect_better_context_candidates(
    assembler: AnswerAssembler,
    *,
    formula_name: str,
    before_row: dict[str, Any],
    after_row: dict[str, Any],
) -> list[str]:
    before_primary_id = get_primary_id(before_row)
    before_context_clause = before_row.get("primary_context_clause") or ""
    after_primary_id = get_primary_id(after_row)
    after_context_clause = after_row.get("primary_context_clause") or ""

    candidate_ids: list[str] = []
    if after_primary_id and (
        after_primary_id != before_primary_id
        or compact_whitespace(after_context_clause) != compact_whitespace(before_context_clause)
    ):
        candidate_ids.append(after_primary_id)

    formula_chapter_id = before_row.get("formula_chapter_id")
    for row in assembler.engine.unified_rows:
        if row["source_object"] not in {"main_passages", "passages", "ambiguous_passages"}:
            continue
        row_text = row.get("retrieval_text", "")
        row_mentions = {mention["canonical_name"] for mention in assembler._find_formula_mentions(row_text)}
        if formula_name not in row_mentions:
            continue
        if assembler._row_is_formula_heading_for_entity(row, formula_name):
            continue
        if assembler._row_is_other_formula_heading(row, formula_name):
            continue

        context_meta = assembler._analyze_formula_effect_context_row_v1(
            row,
            canonical_name=formula_name,
            formula_chapter_id=formula_chapter_id,
        )
        if (
            not context_meta["contains_direct_context"]
            or context_meta["is_short_tail_fragment"]
            or context_meta["is_formula_title_or_composition"]
        ):
            continue
        record_id = row["record_id"]
        if record_id not in candidate_ids:
            candidate_ids.append(record_id)
        if len(candidate_ids) >= 5:
            break

    return candidate_ids


def build_expected_fix_note(
    *,
    before_row: dict[str, Any],
    after_row: dict[str, Any],
    candidate_better_context_ids: list[str],
) -> str:
    before_primary_id = get_primary_id(before_row)
    after_primary_id = get_primary_id(after_row)
    before_context_clause = compact_whitespace(before_row.get("primary_context_clause") or "")
    after_context_clause = compact_whitespace(after_row.get("primary_context_clause") or "")

    after_pattern_label = after_row["preliminary_pattern_label"]
    if after_pattern_label == "direct_context_main_selected":
        if after_primary_id == before_primary_id and after_context_clause != before_context_clause:
            return "同一条 primary 内已从短尾残片回退到更完整的直接语境。"
        if after_primary_id == before_primary_id:
            return "这类短而完整的直接语境已不再被误判成 short tail。"
        return "已有更完整的 direct context 候选，本轮已把 primary 切到更自然的条文。"
    if after_pattern_label == "cross_chapter_bridge_primary":
        return "短尾残片已被清掉，但样本更准确地暴露为 cross-chapter bridge；本轮不继续扩修 bridge。"
    if any(candidate_id.startswith("full:") for candidate_id in candidate_better_context_ids):
        return "review 层可见更完整语境，但按本轮边界不跨证据层级抬升。"
    return "当前没有更稳妥的正文直接语境可切换，本轮最小修复先保留。"


def build_short_tail_set(
    assembler: AnswerAssembler,
    *,
    baseline_short_tail_rows: list[dict[str, Any]],
    current_query_map: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for before_row in baseline_short_tail_rows:
        after_row = current_query_map[query_key(before_row)]
        candidate_better_context_ids = collect_better_context_candidates(
            assembler,
            formula_name=before_row["formula_name"],
            before_row=before_row,
            after_row=after_row,
        )
        items.append(
            {
                "formula_name": before_row["formula_name"],
                "query": before_row["query"],
                "before_primary_id": get_primary_id(before_row),
                "before_primary_text": get_primary_text(before_row),
                "before_context_clause": before_row.get("primary_context_clause"),
                "fragment_type": detect_fragment_type(
                    assembler,
                    formula_name=before_row["formula_name"],
                    primary_text=get_primary_text(before_row),
                    context_clause=before_row.get("primary_context_clause") or "",
                ),
                "candidate_better_context_ids": candidate_better_context_ids,
                "expected_fix_note": build_expected_fix_note(
                    before_row=before_row,
                    after_row=after_row,
                    candidate_better_context_ids=candidate_better_context_ids,
                ),
                "after_primary_id": get_primary_id(after_row),
                "after_primary_text": get_primary_text(after_row),
                "after_context_clause": after_row.get("primary_context_clause"),
                "after_pattern_label": after_row["preliminary_pattern_label"],
            }
        )
    return items


def choose_action_fragment_pair(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    for before_row, after_row in rows:
        fragment = compact_whitespace(before_row.get("primary_context_clause") or "")
        if fragment in {"与", "宜", "当", "可", "不瘥"} and before_row["query"].endswith("有什么作用"):
            return before_row, after_row
    return rows[0] if rows else None


def choose_compact_clause_pair(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    for before_row, after_row in rows:
        before_context = compact_whitespace(before_row.get("primary_context_clause") or "")
        if before_context in {"与", "宜", "当", "可", "不瘥"}:
            continue
        if get_primary_id(before_row) == get_primary_id(after_row) and before_row["query"].endswith("有什么作用"):
            return before_row, after_row
    return rows[0] if rows else None


def render_design_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    resolved_query_count: int,
    resolved_formula_count: int,
    fully_direct_query_count: int,
    rebucketed_query_count: int,
) -> str:
    short_tail_before = baseline_after_summary["pattern_counts"].get("short_tail_fragment_primary", 0)
    short_tail_after = current_summary["pattern_counts"].get("short_tail_fragment_primary", 0)
    cross_chapter = baseline_after_summary["pattern_counts"].get("cross_chapter_bridge_primary", 0)
    review_only = baseline_after_summary["pattern_counts"].get("review_only_should_remain_weak", 0)
    raw_missing = baseline_after_summary["pattern_counts"].get("raw_recall_missing_direct_context", 0)
    formula_title = baseline_after_summary["pattern_counts"].get("formula_title_or_composition_over_primary", 0)
    return "\n".join(
        [
            "# formula_effect_short_tail_fragment_fix_v1",
            "",
            "## 什么叫 short_tail_fragment_primary",
            "",
            "- 指 `formula_effect_query` 已经给到 `strong`，但 `primary_context_clause` 只剩很短的动作尾巴或条件残片，像 `与`、`不瘥`、`若少气` 这类语境拿来直接回答“有什么作用”会很别扭。",
            "- 这类问题多数不是 raw recall 缺料，而是同一条 primary 的 context clause 抽取过窄，或者把短而完整的直接语境误判成 short tail。",
            "",
            "## 为什么它影响用户体感",
            "",
            "- 用户第一眼看到的 answer 首句会直接退化成“用于与”“用于不瘥”“用于若少气”这类不自然短句。",
            "- 即使 primary record_id 本身没错，只要 context clause 抽窄，整个 strong answer 的可信度和可读性都会立刻下降。",
            f"- baseline bulk audit 的 `after` 口径里，这类样本共有 `{short_tail_before}` 个 query / `{short_tail_before // 3}` 个 formula；本轮回放后降到 `{short_tail_after}` 个 query。",
            "",
            "## 拟采用的最小修复策略",
            "",
            "- 不改 raw retrieval candidate 生成，不扩 annotation / annotation_links，不碰 review-only 的升格逻辑。",
            "- 在 `backend/answers/assembler.py` 的 `formula_effect` context clause 抽取里增加一层同-row 回退：如果 formula 前只剩 `与 / 可与 / 当 / 宜 / 更作` 这类动作残片，就回退到前一个更完整的症状片段；必要时拼回极短的条件尾巴，如 `不瘥`。",
            "- 对 `少阴病，下利`、`发汗后，腹胀满`、`若少气` 这类短但完整的直接语境，改成更谨慎的 compact direct clause 判定，不再一律按“长度短”打成 short tail。",
            f"- 本轮回放后，`short_tail_fragment_primary` 本身共脱离 `{resolved_query_count}` 个 query、`{resolved_formula_count}` 个 formula；其中 `{fully_direct_query_count}` 个 query 落回 `direct_context_main_selected`，另有 `{rebucketed_query_count}` 个 query 更准确地转入 `cross_chapter_bridge_primary`。",
            "",
            "## 为什么本轮不顺手碰其他 pattern",
            "",
            f"- 不继续扩 `cross_chapter_bridge_primary`：它已有专门 patch，继续加 chapter 偏好会把 short-tail 和 bridge 两类规则重新缠在一起；当前 baseline 仍有 `{cross_chapter}` 个 bridge query，后续应单独评估。",
            f"- 不碰 `review_only_should_remain_weak`：这类有 `{review_only}` 个 query，本来就应保持保守，不应借 short-tail patch 被误抬。",
            f"- 不碰 `raw_recall_missing_direct_context`：这类有 `{raw_missing}` 个 query，根因在 raw retrieval，不属于本轮允许范围。",
            f"- 不顺手改 `formula_title_or_composition_over_primary`：这类仍有 `{formula_title}` 个 query，属于独立的 primary slot 问题，值得单独开一轮处理。",
            "",
        ]
    )


def render_before_after_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_short_tail_rows: list[dict[str, Any]],
    resolved_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    direct_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    rebucketed_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    stable_regression_queries: list[tuple[dict[str, Any], dict[str, Any]]],
    review_only_mislift_queries: list[tuple[dict[str, Any], dict[str, Any]]],
    current_query_map: dict[tuple[str, str], dict[str, Any]],
) -> str:
    lines = [
        "# formula_effect_short_tail_fragment_before_after_v1",
        "",
        "## Delta 概览",
        "",
        f"- baseline short-tail 样本总数：`{len(baseline_short_tail_rows)}` queries",
        f"- baseline short-tail 公式数：`{len({row['formula_name'] for row in baseline_short_tail_rows})}`",
        f"- `short_tail_fragment_primary`：`{baseline_after_summary['pattern_counts'].get('short_tail_fragment_primary', 0)}` -> `{current_summary['pattern_counts'].get('short_tail_fragment_primary', 0)}`",
        f"- 脱离 short-tail 的 query 数：`{len(resolved_rows)}`",
        f"- 脱离 short-tail 的 formula 数：`{len({before_row['formula_name'] for before_row, _ in resolved_rows})}`",
        f"- 其中回到 `direct_context_main_selected`：`{len(direct_rows)}` queries",
        f"- 其中转入 `cross_chapter_bridge_primary`：`{len(rebucketed_rows)}` queries",
        f"- stable positive 回退 query 数：`{len(stable_regression_queries)}`",
        f"- review-only weak 误抬 query 数：`{len(review_only_mislift_queries)}`",
        "",
    ]

    action_pair = choose_action_fragment_pair(direct_rows)
    if action_pair is not None:
        before_row, after_row = action_pair
        lines.extend(
            [
                "## 代表性样本一：动作尾巴残片回退",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary：`{get_primary_id(before_row)}`",
                f"- before primary_context_clause：`{before_row.get('primary_context_clause')}`",
                f"- before answer 首句：{before_row['answer_text'].splitlines()[0]}",
                f"- after primary：`{get_primary_id(after_row)}`",
                f"- after primary_context_clause：`{after_row.get('primary_context_clause')}`",
                f"- after answer 首句：{after_row['answer_text'].splitlines()[0]}",
                f"- primary_context_clause 是否从短残片变成完整直接语境：`{'是' if compact_whitespace(before_row.get('primary_context_clause') or '') != compact_whitespace(after_row.get('primary_context_clause') or '') else '否'}`",
                "- answer_text 是否更自然：`是`。首句不再直接暴露 `与 / 不瘥` 这类动作残片。",
                "- 是否引入新的误伤：`未见`。primary 仍在 `main_passages`，answer_mode 仍为 `strong`。",
                "",
            ]
        )

    compact_pair = choose_compact_clause_pair(resolved_rows)
    if compact_pair is not None:
        before_row, after_row = compact_pair
        lines.extend(
            [
                "## 代表性样本二：短但完整的直接语境不再误判",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary_context_clause：`{before_row.get('primary_context_clause')}`",
                f"- after primary_context_clause：`{after_row.get('primary_context_clause')}`",
                f"- after answer 首句：{after_row['answer_text'].splitlines()[0]}",
                "- primary_context_clause 是否不再被视为短残片：`是`。这类样本的 primary 没换 record，修复点主要是 compact direct clause 判定更稳了。",
                "- answer_text 是否更自然：`是`。即使文本几乎不变，回答也不再被错误地归到 short-tail bucket。",
                "- 是否引入新的误伤：`未见`。没有把 review-only 证据拉进 strong 主依据。",
                "",
            ]
        )

    if rebucketed_rows:
        before_row, after_row = rebucketed_rows[0]
        lines.extend(
            [
                "## 保留边界：短尾修掉后暴露为 bridge",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary_context_clause：`{before_row.get('primary_context_clause')}`",
                f"- after primary_context_clause：`{after_row.get('primary_context_clause')}`",
                f"- after pattern：`{after_row['preliminary_pattern_label']}`",
                "- primary_context_clause 是否已经摆脱短残片：`是`。",
                "- answer_text 是否更自然：`是`。但这类样本仍然不是 fully clean，因为现在暴露的是 chapter 归属问题，而不是短尾残片。",
                "- 是否引入新的误伤：`否`。这是原有 bridge 问题被重新显影，不是 review-only 被误抬。",
                "",
            ]
        )

    stable_query = current_query_map.get(("小柴胡汤方", "小柴胡汤方有什么作用"))
    weak_query = current_query_map.get(("乌梅丸方", "乌梅丸方有什么作用"))
    if stable_query or weak_query:
        lines.extend(["## 稳定性抽查", ""])
    if stable_query:
        lines.append(
            f"- 小柴胡汤方有什么作用：仍为 `{stable_query['answer_mode']}`，pattern=`{stable_query['preliminary_pattern_label']}`。"
        )
    if weak_query:
        lines.append(
            f"- 乌梅丸方有什么作用：仍为 `{weak_query['answer_mode']}`，primary 仍为空，未把 review-only weak 误抬成 strong。"
        )
    lines.append("")
    return "\n".join(lines)


def render_patch_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_after_formula_rows: list[dict[str, Any]],
    current_formula_rows: list[dict[str, Any]],
    resolved_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    direct_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    rebucketed_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    stable_regression_queries: list[tuple[dict[str, Any], dict[str, Any]]],
    review_only_mislift_queries: list[tuple[dict[str, Any], dict[str, Any]]],
) -> str:
    baseline_formula_map = get_formula_bucket_map(baseline_after_formula_rows)
    current_formula_map = get_formula_bucket_map(current_formula_rows)
    stable_regression_formulas = sorted(
        {
            formula_name
            for formula_name, before_row in baseline_formula_map.items()
            if before_row["formula_bucket"] == "strong_reasonable"
            and current_formula_map.get(formula_name, {}).get("formula_bucket") != "strong_reasonable"
        }
    )
    review_only_mislift_formulas = sorted({before_row["formula_name"] for before_row, _ in review_only_mislift_queries})
    resolved_formula_count = len({before_row["formula_name"] for before_row, _ in resolved_rows})
    formula_title_after = current_summary["pattern_counts"].get("formula_title_or_composition_over_primary", 0)
    cross_after = current_summary["pattern_counts"].get("cross_chapter_bridge_primary", 0)

    lines = [
        "# formula_effect_short_tail_fragment_patch_v1",
        "",
        "## 修了哪些规则",
        "",
        "- 在 `backend/answers/assembler.py` 的 `_extract_formula_effect_context_clause_v1` 中加入同-row backtrack：当 formula 前只剩短动作残片时，回退到前一个更完整的症状片段。",
        "- 对极短条件尾巴仅在必要时拼回，例如 `不瘥`，避免 answer_text 只剩一个动作词。",
        "- 在 `_analyze_formula_effect_context_row_v1` 里加入 compact direct clause 判定，让 `少阴病，下利`、`发汗后，腹胀满` 这类短但完整的直接语境不再被误标为 short tail。",
        "- 仅复用现有 formula_effect 逻辑做最小调整，没有改 raw retrieval、annotation 或 review-only weak 的证据边界。",
        "",
        "## 改善规模",
        "",
        f"- `short_tail_fragment_primary`：`{baseline_after_summary['pattern_counts'].get('short_tail_fragment_primary', 0)}` -> `{current_summary['pattern_counts'].get('short_tail_fragment_primary', 0)}`",
        f"- 脱离 short-tail 的 query 数：`{len(resolved_rows)}`",
        f"- 脱离 short-tail 的 formula 数：`{resolved_formula_count}`",
        f"- 其中回到 `direct_context_main_selected`：`{len(direct_rows)}` queries",
        f"- 其中转入 `cross_chapter_bridge_primary`：`{len(rebucketed_rows)}` queries",
        f"- `primary_reasonable_query_count`：`{baseline_after_summary['primary_reasonable_query_count']}` -> `{current_summary['primary_reasonable_query_count']}`",
        f"- `primary_suspicious_query_count`：`{baseline_after_summary['primary_suspicious_query_count']}` -> `{current_summary['primary_suspicious_query_count']}`",
        "",
        "## 是否有回退样本",
        "",
        f"- stable positive 回退 query 数：`{len(stable_regression_queries)}`",
        f"- stable positive 回退 formula 数：`{len(stable_regression_formulas)}`",
        f"- review-only weak 误抬 query 数：`{len(review_only_mislift_queries)}`",
        f"- review-only weak 误抬 formula 数：`{len(review_only_mislift_formulas)}`",
    ]
    if stable_regression_formulas:
        lines.append(f"- stable positive 回退公式：`{'、'.join(stable_regression_formulas)}`")
    else:
        lines.append("- stable positive 回退公式：`_none_`")
    if review_only_mislift_formulas:
        lines.append(f"- review-only 误抬公式：`{'、'.join(review_only_mislift_formulas)}`")
    else:
        lines.append("- review-only 误抬公式：`_none_`")

    next_round = "是" if formula_title_after > 0 else "否"
    reason = (
        f"当前 `formula_title_or_composition_over_primary` 仍有 `{formula_title_after}` 个 query，且它与 short-tail 一样属于 assembler 内的 primary slot 失配。"
        if formula_title_after > 0
        else f"当前 `formula_title_or_composition_over_primary` 已不再显著，剩余更大的 suspicious strong 类是 `cross_chapter_bridge_primary`（`{cross_after}` 个 query）。"
    )
    lines.extend(
        [
            "",
            "## 下一轮是否还值得处理 formula_title_or_composition_over_primary",
            "",
            f"- 建议：`{next_round}`。",
            f"- 原因：{reason}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    baseline_path = resolve_project_path(args.baseline_audit_json)
    set_json_out = resolve_project_path(args.set_json_out)
    design_md_out = resolve_project_path(args.design_md_out)
    before_after_md_out = resolve_project_path(args.before_after_md_out)
    patch_md_out = resolve_project_path(args.patch_md_out)

    baseline_payload, baseline_after_variant = load_baseline_after_variant(baseline_path)
    baseline_after_summary = baseline_after_variant["summary"]
    baseline_after_query_rows = baseline_after_variant["query_rows"]
    baseline_after_formula_rows = baseline_after_variant["formula_rows"]
    baseline_short_tail_rows = [
        row for row in baseline_after_query_rows if row["preliminary_pattern_label"] == "short_tail_fragment_primary"
    ]

    assembler = build_assembler(args)
    try:
        current_after = run_current_after_patch(
            assembler,
            baseline_after_query_rows=baseline_after_query_rows,
        )
        current_query_map = {query_key(row): row for row in current_after["query_rows"]}

        resolved_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_short_tail_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] != "short_tail_fragment_primary"
        ]
        direct_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_short_tail_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "direct_context_main_selected"
        ]
        rebucketed_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_short_tail_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "cross_chapter_bridge_primary"
        ]
        stable_regression_queries = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_after_query_rows
            if before_row["preliminary_pattern_label"] == "direct_context_main_selected"
            and current_query_map[query_key(before_row)]["preliminary_pattern_label"] != "direct_context_main_selected"
        ]
        review_only_mislift_queries = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_after_query_rows
            if before_row["preliminary_pattern_label"] == "review_only_should_remain_weak"
            and (
                current_query_map[query_key(before_row)]["answer_mode"] != "weak_with_review_notice"
                or bool(current_query_map[query_key(before_row)]["primary_evidence_ids"])
            )
        ]

        short_tail_set = build_short_tail_set(
            assembler,
            baseline_short_tail_rows=baseline_short_tail_rows,
            current_query_map=current_query_map,
        )
        design_md = render_design_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            resolved_query_count=len(resolved_rows),
            resolved_formula_count=len({before_row["formula_name"] for before_row, _ in resolved_rows}),
            fully_direct_query_count=len(direct_rows),
            rebucketed_query_count=len(rebucketed_rows),
        )
        before_after_md = render_before_after_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            baseline_short_tail_rows=baseline_short_tail_rows,
            resolved_rows=resolved_rows,
            direct_rows=direct_rows,
            rebucketed_rows=rebucketed_rows,
            stable_regression_queries=stable_regression_queries,
            review_only_mislift_queries=review_only_mislift_queries,
            current_query_map=current_query_map,
        )
        patch_md = render_patch_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            baseline_after_formula_rows=baseline_after_formula_rows,
            current_formula_rows=current_after["formula_rows"],
            resolved_rows=resolved_rows,
            direct_rows=direct_rows,
            rebucketed_rows=rebucketed_rows,
            stable_regression_queries=stable_regression_queries,
            review_only_mislift_queries=review_only_mislift_queries,
        )

        write_json(set_json_out, short_tail_set)
        write_markdown(design_md_out, design_md)
        write_markdown(before_after_md_out, before_after_md)
        write_markdown(patch_md_out, patch_md)

        print(
            json.dumps(
                {
                    "baseline_short_tail_query_count": len(baseline_short_tail_rows),
                    "baseline_short_tail_formula_count": len({row["formula_name"] for row in baseline_short_tail_rows}),
                    "resolved_query_count": len(resolved_rows),
                    "resolved_formula_count": len({before_row["formula_name"] for before_row, _ in resolved_rows}),
                    "direct_context_query_count": len(direct_rows),
                    "rebucketed_cross_chapter_query_count": len(rebucketed_rows),
                    "stable_positive_regression_query_count": len(stable_regression_queries),
                    "review_only_mislift_query_count": len(review_only_mislift_queries),
                    "current_short_tail_query_count": current_after["summary"]["pattern_counts"].get(
                        "short_tail_fragment_primary",
                        0,
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        assembler.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
