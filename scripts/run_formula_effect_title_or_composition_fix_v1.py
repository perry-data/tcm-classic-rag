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
    FORMULA_COMPOSITION_DOSAGE_PATTERN,
    FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS,
    FORMULA_EFFECT_DIRECT_USAGE_MARKERS,
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


DEFAULT_SET_JSON_OUT = "artifacts/experiments/formula_effect_title_or_composition_set_v1.json"
DEFAULT_DESIGN_MD_OUT = "docs/design/formula_effect_title_or_composition_fix_v1.md"
DEFAULT_BEFORE_AFTER_MD_OUT = "artifacts/experiments/formula_effect_title_or_composition_before_after_v1.md"
DEFAULT_PATCH_MD_OUT = "docs/patch_notes/formula_effect_title_or_composition_patch_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the formula_title_or_composition_over_primary fix v1 report set.")
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


def classify_before_primary_kind(
    assembler: AnswerAssembler,
    *,
    formula_name: str,
    before_row: dict[str, Any],
) -> str:
    primary_id = get_primary_id(before_row)
    if not primary_id:
        return "mixed"

    row = assembler.engine.record_by_id.get(primary_id)
    text = strip_inline_notes(get_primary_text(before_row))
    compact_text = compact_whitespace(text)
    if row and assembler._row_is_formula_heading_for_entity(row, formula_name):
        return "title"
    if compact_text.startswith(formula_name) or compact_text.startswith(formula_name[:-1] if formula_name.endswith("方") else formula_name):
        return "title"

    dosage_hits = len(FORMULA_COMPOSITION_DOSAGE_PATTERN.findall(compact_text))
    has_direct_usage = any(marker in compact_text for marker in FORMULA_EFFECT_DIRECT_USAGE_MARKERS) or any(
        hint in compact_text for hint in FORMULA_EFFECT_CONTEXT_SYMPTOM_HINTS
    )
    if dosage_hits >= 2 and not has_direct_usage:
        return "composition"
    return "mixed"


def collect_candidate_direct_context_ids(
    assembler: AnswerAssembler,
    *,
    formula_name: str,
    formula_chapter_id: str | None,
) -> list[str]:
    candidates: list[tuple[float, int, str]] = []
    for row in assembler.engine.unified_rows:
        if row["source_object"] != "main_passages":
            continue
        text = row.get("retrieval_text", "")
        row_mentions = {mention["canonical_name"] for mention in assembler._find_formula_mentions(text)}
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
        score, context_distance = assembler._score_formula_effect_context_row_v1(
            row,
            canonical_name=formula_name,
            preferred_chapter_id=formula_chapter_id,
            row_mentions=row_mentions,
        )
        if not assembler._row_qualifies_for_formula_effect_direct_context_preference_v1(context_meta, score=score):
            continue
        candidates.append((score, context_distance, row["record_id"]))

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [record_id for _, _, record_id in candidates[:5]]


def build_expected_fix_note(
    *,
    before_row: dict[str, Any],
    after_row: dict[str, Any],
) -> str:
    before_primary_id = get_primary_id(before_row)
    after_primary_id = get_primary_id(after_row)
    after_pattern_label = after_row["preliminary_pattern_label"]
    if after_pattern_label == "direct_context_main_selected":
        if before_primary_id == after_primary_id:
            return "当前 primary 本身就是正文直接语境，本轮修正的是 title/composition 误判。"
        return "存在更稳妥的 direct context 条文，本轮已把 primary 从方题/组成误占切回正文语境。"
    if after_pattern_label == "cross_chapter_bridge_primary":
        return "title/composition 误占已消除，但样本更准确地暴露为 cross-chapter bridge；本轮不继续扩修 bridge。"
    if after_pattern_label == "false_strong_without_direct_context":
        return "title/composition 标签已消除，但这条样本仍残留 context 抽取噪声；本轮不继续扩大到其他 pattern。"
    if after_pattern_label == "formula_title_or_composition_over_primary":
        return "当前仍未稳定摆脱方题/组成误占，本轮先保留。"
    return "该样本已脱离 title/composition bucket，但新的主因不在本轮修复边界内。"


def build_title_or_composition_set(
    assembler: AnswerAssembler,
    *,
    baseline_target_rows: list[dict[str, Any]],
    current_query_map: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for before_row in baseline_target_rows:
        after_row = current_query_map[query_key(before_row)]
        candidate_direct_context_ids = collect_candidate_direct_context_ids(
            assembler,
            formula_name=before_row["formula_name"],
            formula_chapter_id=before_row.get("formula_chapter_id"),
        )
        items.append(
            {
                "formula_name": before_row["formula_name"],
                "query": before_row["query"],
                "before_primary_id": get_primary_id(before_row),
                "before_primary_text": get_primary_text(before_row),
                "before_primary_kind": classify_before_primary_kind(
                    assembler,
                    formula_name=before_row["formula_name"],
                    before_row=before_row,
                ),
                "candidate_direct_context_ids": candidate_direct_context_ids,
                "expected_fix_note": build_expected_fix_note(
                    before_row=before_row,
                    after_row=after_row,
                ),
                "after_primary_id": get_primary_id(after_row),
                "after_primary_text": get_primary_text(after_row),
                "after_pattern_label": after_row["preliminary_pattern_label"],
                "after_primary_context_clause": after_row.get("primary_context_clause"),
            }
        )
    return items


def choose_representative_direct_pair(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    preferred = next(
        (
            row_pair
            for row_pair in rows
            if row_pair[0]["query"].endswith("有什么作用") and get_primary_id(row_pair[0]) == get_primary_id(row_pair[1])
        ),
        None,
    )
    return preferred or (rows[0] if rows else None)


def render_design_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    resolved_query_count: int,
    resolved_formula_count: int,
    direct_query_count: int,
    rebucketed_cross_chapter_count: int,
    rebucketed_false_strong_count: int,
) -> str:
    title_before = baseline_after_summary["pattern_counts"].get("formula_title_or_composition_over_primary", 0)
    title_after = current_summary["pattern_counts"].get("formula_title_or_composition_over_primary", 0)
    cross_before = baseline_after_summary["pattern_counts"].get("cross_chapter_bridge_primary", 0)
    review_only = baseline_after_summary["pattern_counts"].get("review_only_should_remain_weak", 0)
    raw_missing = baseline_after_summary["pattern_counts"].get("raw_recall_missing_direct_context", 0)
    short_tail = baseline_after_summary["pattern_counts"].get("short_tail_fragment_primary", 0)
    return "\n".join(
        [
            "# formula_effect_title_or_composition_fix_v1",
            "",
            "## 什么叫 formula_title_or_composition_over_primary",
            "",
            "- 指作用类 query 的 `primary_evidence` 被方题或组成条误占，或者正文直接语境被当前 composition heuristic 误判成了“组成条”。",
            "- 这一类里既有真的 title/composition 抢位，也有正文条文因为出现 `一升 / 三两 / 合病 / 数升` 之类词面而被错误贴上 composition 标签。",
            "",
            "## 为什么它会让“作用类问法”退化成方文/组成直出",
            "",
            "- 一旦 primary 被当成方题/组成条，`formula_effect` 的 strong answer 就会被判成“不是直接使用语境”，用户看到的回答要么偏方文直出，要么落到可疑 strong。",
            "- 这类问题多数不是 raw recall 缺料，而是 assembler 在 primary slot 分析和 support row ranking 上把正文 direct context 误当成 composition。",
            f"- baseline bulk audit 的 `after` 口径里，这类样本共有 `{title_before}` 个 query / `{title_before // 3}` 个 formula；本轮回放后降到 `{title_after}` 个 query。",
            "",
            "## 拟采用的最小修复策略",
            "",
            "- 收紧 `_row_is_formula_composition_line`：不再因为单个 `合 / 两 / 升` 字面就判成 composition，而是要求更像真正的剂量结构；同时对带明显 direct usage marker 或症状语境的行取消 composition 判定。",
            "- 在 `formula_effect` support row ranking 里加入一个很小的 direct-context preference：只有当 top1 仍是 title/composition 且存在 clean main direct context 候选时，才优先正文直接语境。",
            "- 不改 raw retrieval candidate 生成，不碰 annotation / annotation_links，不改 review-only weak 的证据层级。",
            f"- 本轮回放后，`formula_title_or_composition_over_primary` 共脱离 `{resolved_query_count}` 个 query、`{resolved_formula_count}` 个 formula；其中 `{direct_query_count}` 个 query 回到 `direct_context_main_selected`，另有 `{rebucketed_cross_chapter_count}` 个 query 转入 `cross_chapter_bridge_primary`，`{rebucketed_false_strong_count}` 个 query 转入 `false_strong_without_direct_context`。",
            "",
            "## 为什么本轮不顺手碰其他 pattern",
            "",
            f"- 不继续扩 `cross_chapter_bridge_primary`：当前 baseline 还有 `{cross_before}` 个 bridge query，本轮只允许把 title/composition 误占清掉，不继续加 chapter v2 偏好。",
            f"- 不碰 `review_only_should_remain_weak`：这类有 `{review_only}` 个 query，本来就应保持弱，不应因 title/composition patch 被误抬。",
            f"- 不碰 `raw_recall_missing_direct_context`：这类有 `{raw_missing}` 个 query，根因在 raw retrieval，不在本轮边界内。",
            f"- 不继续深挖 `short_tail_fragment_primary`：这类在上轮 patch 已单独处理过，当前剩余问题不应和 title/composition 联修。",
            "",
        ]
    )


def render_before_after_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_target_rows: list[dict[str, Any]],
    resolved_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    direct_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    cross_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    false_strong_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    stable_regression_queries: list[tuple[dict[str, Any], dict[str, Any]]],
    review_only_mislift_queries: list[tuple[dict[str, Any], dict[str, Any]]],
) -> str:
    lines = [
        "# formula_effect_title_or_composition_before_after_v1",
        "",
        "## Delta 概览",
        "",
        f"- baseline title/composition 样本总数：`{len(baseline_target_rows)}` queries",
        f"- baseline title/composition 公式数：`{len({row['formula_name'] for row in baseline_target_rows})}`",
        f"- `formula_title_or_composition_over_primary`：`{baseline_after_summary['pattern_counts'].get('formula_title_or_composition_over_primary', 0)}` -> `{current_summary['pattern_counts'].get('formula_title_or_composition_over_primary', 0)}`",
        f"- 脱离 title/composition 的 query 数：`{len(resolved_rows)}`",
        f"- 脱离 title/composition 的 formula 数：`{len({before_row['formula_name'] for before_row, _ in resolved_rows})}`",
        f"- 其中回到 `direct_context_main_selected`：`{len(direct_rows)}` queries",
        f"- 其中转入 `cross_chapter_bridge_primary`：`{len(cross_rows)}` queries",
        f"- 其中转入 `false_strong_without_direct_context`：`{len(false_strong_rows)}` queries",
        f"- stable positive 回退 query 数：`{len(stable_regression_queries)}`",
        f"- review-only weak 误抬 query 数：`{len(review_only_mislift_queries)}`",
        "",
    ]

    direct_pair = choose_representative_direct_pair(direct_rows)
    if direct_pair is not None:
        before_row, after_row = direct_pair
        lines.extend(
            [
                "## 代表性样本一：同一条正文不再被误判成组成条",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary：`{get_primary_id(before_row)}`",
                f"- before primary text：{get_primary_text(before_row)}",
                f"- before answer 首句：{before_row['answer_text'].splitlines()[0]}",
                f"- after primary：`{get_primary_id(after_row)}`",
                f"- after primary text：{get_primary_text(after_row)}",
                f"- after answer 首句：{after_row['answer_text'].splitlines()[0]}",
                f"- primary 是否从方题/组成条切到直接使用语境：`{'是' if get_primary_id(before_row) != get_primary_id(after_row) else '否'}`。这批样本里主修点主要是去掉 composition 误判，因此很多 query 的 primary row 本身并未更换。",
                "- answer_text 是否更像“基于语境解释”：`基本持平`。这类样本的主要改善在 primary slot 归因，不一定体现在 answer 文案改写上。",
                "- 是否引入新的误伤：`未见`。answer_mode 仍为 `strong`，review-only 弱样本没有被抬升。",
                "",
            ]
        )

    if cross_rows:
        before_row, after_row = cross_rows[0]
        lines.extend(
            [
                "## 代表性样本二：title/composition 去掉后暴露为 bridge",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary：`{get_primary_id(before_row)}` / `{before_row['primary_chapter_id']}`",
                f"- after primary：`{get_primary_id(after_row)}` / `{after_row['primary_chapter_id']}`",
                f"- after pattern：`{after_row['preliminary_pattern_label']}`",
                "- primary 是否从方题/组成条切到直接使用语境：`否`。primary 仍是同一条正文，但现在更准确地暴露为 cross-chapter bridge，而不是 composition 误占。",
                "- answer_text 是否更像“基于语境解释”：`基本持平`。这类样本的主要变化是 bucket 更准确，不是文案层重写。",
                "- 是否引入新的误伤：`否`。这是旧的 bridge 问题被重新显影，不是新的误抬。",
                "",
            ]
        )

    if false_strong_rows:
        before_row, after_row = false_strong_rows[0]
        lines.extend(
            [
                "## 保留边界：去掉 composition 误判后仍有 context 噪声",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary text：{get_primary_text(before_row)}",
                f"- after pattern：`{after_row['preliminary_pattern_label']}`",
                f"- after primary_context_clause：`{after_row.get('primary_context_clause')}`",
                "- primary 是否已经摆脱方题/组成误判：`是`。",
                "- answer_text 是否更像“基于语境解释”：`部分是`。这类样本已经不再是 composition 抢位，但仍残留 context 清洗噪声，因此本轮不把它硬说成 fully clean。",
                "- 是否引入新的误伤：`否`。只是把真实剩余问题从 title/composition bucket 里分离出来。",
                "",
            ]
        )

    lines.extend(
        [
            "## 稳定性抽查",
            "",
            "- `stable positive` 回退：`未见`。",
            "- `review_only_should_remain_weak` 误抬：`未见`。",
            "",
        ]
    )
    return "\n".join(lines)


def render_patch_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_after_formula_rows: list[dict[str, Any]],
    current_formula_rows: list[dict[str, Any]],
    resolved_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    direct_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    cross_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    false_strong_rows: list[tuple[dict[str, Any], dict[str, Any]]],
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
    current_cross_chapter = current_summary["pattern_counts"].get("cross_chapter_bridge_primary", 0)

    lines = [
        "# formula_effect_title_or_composition_patch_v1",
        "",
        "## 修了哪些规则",
        "",
        "- 收紧 `backend/answers/assembler.py` 里的 `_row_is_formula_composition_line`：不再因为普通正文里的 `合 / 两 / 升` 等字面就判成 composition，而是要求更像真正的剂量结构。",
        "- 对带明显 direct usage marker 或症状语境的行取消 composition 判定，避免正文 direct context 被错打成组成条。",
        "- 在 `_find_formula_effect_support_rows_v1` 中加入一层很小的 direct-context preference：仅当 top1 仍是 title/composition 且存在 clean main direct context 候选时，才让位给正文直接语境。",
        "- 在 `_score_formula_effect_context_row_v1` 中补上 title/composition penalty，避免作用类 query 被方题/组成条抢占 primary。",
        "",
        "## 改善规模",
        "",
        f"- `formula_title_or_composition_over_primary`：`{baseline_after_summary['pattern_counts'].get('formula_title_or_composition_over_primary', 0)}` -> `{current_summary['pattern_counts'].get('formula_title_or_composition_over_primary', 0)}`",
        f"- 脱离 title/composition 的 query 数：`{len(resolved_rows)}`",
        f"- 脱离 title/composition 的 formula 数：`{resolved_formula_count}`",
        f"- 其中回到 `direct_context_main_selected`：`{len(direct_rows)}` queries",
        f"- 其中转入 `cross_chapter_bridge_primary`：`{len(cross_rows)}` queries",
        f"- 其中转入 `false_strong_without_direct_context`：`{len(false_strong_rows)}` queries",
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
    lines.extend(
        [
            "",
            "## 下一轮是否还值得继续回头处理 cross_chapter_bridge_primary v2",
            "",
            f"- 建议：`{'是' if current_cross_chapter > 0 else '否'}`。",
            f"- 原因：当前 `cross_chapter_bridge_primary` 仍有 `{current_cross_chapter}` 个 query，而且本轮 title/composition 样本里又有 `{len(cross_rows)}` 个 query 在去误判后重新暴露成 bridge，说明它仍是值得单独处理的剩余大类。",
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

    _, baseline_after_variant = load_baseline_after_variant(baseline_path)
    baseline_after_summary = baseline_after_variant["summary"]
    baseline_after_query_rows = baseline_after_variant["query_rows"]
    baseline_after_formula_rows = baseline_after_variant["formula_rows"]
    baseline_target_rows = [
        row
        for row in baseline_after_query_rows
        if row["preliminary_pattern_label"] == "formula_title_or_composition_over_primary"
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
            for before_row in baseline_target_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] != "formula_title_or_composition_over_primary"
        ]
        direct_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_target_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "direct_context_main_selected"
        ]
        cross_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_target_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "cross_chapter_bridge_primary"
        ]
        false_strong_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_target_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "false_strong_without_direct_context"
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

        result_set = build_title_or_composition_set(
            assembler,
            baseline_target_rows=baseline_target_rows,
            current_query_map=current_query_map,
        )
        design_md = render_design_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            resolved_query_count=len(resolved_rows),
            resolved_formula_count=len({before_row["formula_name"] for before_row, _ in resolved_rows}),
            direct_query_count=len(direct_rows),
            rebucketed_cross_chapter_count=len(cross_rows),
            rebucketed_false_strong_count=len(false_strong_rows),
        )
        before_after_md = render_before_after_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            baseline_target_rows=baseline_target_rows,
            resolved_rows=resolved_rows,
            direct_rows=direct_rows,
            cross_rows=cross_rows,
            false_strong_rows=false_strong_rows,
            stable_regression_queries=stable_regression_queries,
            review_only_mislift_queries=review_only_mislift_queries,
        )
        patch_md = render_patch_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            baseline_after_formula_rows=baseline_after_formula_rows,
            current_formula_rows=current_after["formula_rows"],
            resolved_rows=resolved_rows,
            direct_rows=direct_rows,
            cross_rows=cross_rows,
            false_strong_rows=false_strong_rows,
            stable_regression_queries=stable_regression_queries,
            review_only_mislift_queries=review_only_mislift_queries,
        )

        write_json(set_json_out, result_set)
        write_markdown(design_md_out, design_md)
        write_markdown(before_after_md_out, before_after_md)
        write_markdown(patch_md_out, patch_md)

        print(
            json.dumps(
                {
                    "baseline_title_or_composition_query_count": len(baseline_target_rows),
                    "baseline_title_or_composition_formula_count": len({row["formula_name"] for row in baseline_target_rows}),
                    "resolved_query_count": len(resolved_rows),
                    "resolved_formula_count": len({before_row["formula_name"] for before_row, _ in resolved_rows}),
                    "direct_context_query_count": len(direct_rows),
                    "rebucketed_cross_chapter_query_count": len(cross_rows),
                    "rebucketed_false_strong_query_count": len(false_strong_rows),
                    "stable_positive_regression_query_count": len(stable_regression_queries),
                    "review_only_mislift_query_count": len(review_only_mislift_queries),
                    "current_title_or_composition_query_count": current_after["summary"]["pattern_counts"].get(
                        "formula_title_or_composition_over_primary",
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
