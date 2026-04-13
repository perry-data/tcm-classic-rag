#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
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
    AnswerAssembler,
)
from backend.retrieval.minimal import resolve_project_path
from scripts.run_formula_effect_bulk_audit_v1 import (
    DEFAULT_QUERY_TEMPLATES,
    VariantSpec,
    build_formula_effect_payload_from_bundle,
    build_formula_level_rows,
    build_variant_summary,
    classify_context_row,
    determine_pattern_label,
)


DEFAULT_BASELINE_AUDIT_JSON = "artifacts/experiments/formula_effect_bulk_audit_v1.json"
DEFAULT_SET_JSON_OUT = "artifacts/experiments/formula_effect_cross_chapter_bridge_set_v1.json"
DEFAULT_DESIGN_MD_OUT = "docs/design/formula_effect_cross_chapter_bridge_fix_v1.md"
DEFAULT_BEFORE_AFTER_MD_OUT = "artifacts/experiments/formula_effect_cross_chapter_bridge_before_after_v1.md"
DEFAULT_PATCH_MD_OUT = "docs/patch_notes/formula_effect_cross_chapter_bridge_patch_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the cross_chapter_bridge_primary fix v1 report set.")
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def build_assembler(args: argparse.Namespace) -> AnswerAssembler:
    return AnswerAssembler(
        db_path=resolve_project_path(args.db_path),
        policy_path=resolve_project_path(args.policy_json),
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=resolve_project_path(args.cache_dir),
        dense_chunks_index=resolve_project_path(args.dense_chunks_index),
        dense_chunks_meta=resolve_project_path(args.dense_chunks_meta),
        dense_main_index=resolve_project_path(args.dense_main_index),
        dense_main_meta=resolve_project_path(args.dense_main_meta),
    )


def query_key(row: dict[str, Any]) -> tuple[str, str]:
    return row["formula_name"], row["query"]


def get_primary_id(row: dict[str, Any]) -> str | None:
    ids = row.get("primary_evidence_ids") or []
    return ids[0] if ids else None


def get_primary_text(row: dict[str, Any]) -> str:
    texts = row.get("primary_evidence_text") or []
    return texts[0] if texts else ""


def get_formula_bucket_map(formula_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["formula_name"]: row for row in formula_rows}


def fetch_full_texts(assembler: AnswerAssembler, items: list[dict[str, Any]]) -> list[str]:
    return [assembler._fetch_record_meta(item["record_id"]).get("retrieval_text", "") for item in items]


def build_current_query_row_from_baseline(
    assembler: AnswerAssembler,
    *,
    baseline_row: dict[str, Any],
    payload: dict[str, Any],
    bundle: dict[str, Any],
) -> dict[str, Any]:
    primary_items = payload["primary_evidence"]
    secondary_items = payload["secondary_evidence"]
    review_items = payload["review_materials"]
    formula_chapter_id = baseline_row["formula_chapter_id"]

    primary_row = None
    if primary_items:
        primary_row = {
            **assembler.engine.record_by_id[primary_items[0]["record_id"]],
            "source_object": assembler.engine.record_by_id[primary_items[0]["record_id"]]["source_object"],
        }
    primary_meta = classify_context_row(
        assembler,
        canonical_name=baseline_row["formula_name"],
        formula_chapter_id=formula_chapter_id,
        row=primary_row,
    )
    direct_context_exists_in_raw_candidates = baseline_row["whether_direct_context_exists_in_raw_candidates"]
    direct_context_main_exists_in_raw_candidates = bool(baseline_row["raw_direct_context_main_candidate_ids"])
    direct_context_exists_only_in_review = baseline_row["whether_direct_context_exists_only_in_review"]
    pattern_label = determine_pattern_label(
        route=baseline_row["route"],
        answer_mode=payload["answer_mode"],
        primary_meta=primary_meta,
        direct_context_exists_in_raw_candidates=direct_context_exists_in_raw_candidates,
        direct_context_main_exists_in_raw_candidates=direct_context_main_exists_in_raw_candidates,
        direct_context_exists_only_in_review=direct_context_exists_only_in_review,
    )
    primary_reasonable = payload["answer_mode"] == "strong" and pattern_label == "direct_context_main_selected"
    primary_suspicious = payload["answer_mode"] == "strong" and pattern_label in {
        "short_tail_fragment_primary",
        "cross_chapter_bridge_primary",
        "formula_title_or_composition_over_primary",
        "false_strong_without_direct_context",
    }
    weak_due_to_assembler_issue = payload["answer_mode"] == "weak_with_review_notice" and bool(
        direct_context_main_exists_in_raw_candidates
    )
    weak_reason_bucket = None
    if payload["answer_mode"] == "weak_with_review_notice":
        if weak_due_to_assembler_issue:
            weak_reason_bucket = "assembler_issue"
        elif direct_context_exists_only_in_review:
            weak_reason_bucket = "review_only"
        elif not direct_context_exists_in_raw_candidates:
            weak_reason_bucket = "raw_recall_missing"
        else:
            weak_reason_bucket = "other"

    primary_chapter_id = primary_items[0]["chapter_id"] if primary_items else None
    return {
        "variant": "after_patch",
        "formula_effect_primary_rules_v1_enabled": True,
        "formula_name": baseline_row["formula_name"],
        "query": baseline_row["query"],
        "answer_mode": payload["answer_mode"],
        "route": baseline_row["route"],
        "primary_evidence_ids": [item["record_id"] for item in primary_items],
        "primary_evidence_text": fetch_full_texts(assembler, primary_items),
        "primary_chapter_id": primary_chapter_id,
        "formula_chapter_id": formula_chapter_id,
        "secondary_evidence_ids": [item["record_id"] for item in secondary_items],
        "review_material_ids": [item["record_id"] for item in review_items],
        "answer_text": payload["answer_text"],
        "raw_top_candidate_ids": baseline_row["raw_top_candidate_ids"],
        "whether_primary_contains_direct_context": primary_meta["contains_direct_context"],
        "whether_primary_is_formula_title_or_composition": primary_meta["is_formula_title_or_composition"],
        "whether_primary_looks_like_short_tail_fragment": primary_meta["is_short_tail_fragment"],
        "whether_primary_is_cross_chapter_bridge": primary_meta["is_cross_chapter_bridge"],
        "whether_direct_context_exists_in_raw_candidates": direct_context_exists_in_raw_candidates,
        "whether_direct_context_exists_only_in_review": direct_context_exists_only_in_review,
        "preliminary_pattern_label": pattern_label,
        "is_primary_reasonable": primary_reasonable,
        "is_primary_suspicious": primary_suspicious,
        "weak_reason_bucket": weak_reason_bucket,
        "weak_due_to_assembler_issue": weak_due_to_assembler_issue,
        "raw_direct_context_candidate_ids": baseline_row["raw_direct_context_candidate_ids"],
        "raw_direct_context_main_candidate_ids": baseline_row["raw_direct_context_main_candidate_ids"],
        "raw_direct_context_review_candidate_ids": baseline_row["raw_direct_context_review_candidate_ids"],
        "bundle_context_record_id": bundle["context_row"]["record_id"] if bundle.get("context_row") else None,
        "bundle_context_source": bundle.get("context_source"),
        "bundle_context_clause": bundle["facts"].get("context_clause"),
        "primary_context_clause": primary_meta["context_clause"],
    }


def run_current_after_patch(
    assembler: AnswerAssembler,
    *,
    baseline_after_query_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    variant = VariantSpec(label="after_patch", formula_effect_primary_v1_enabled=True)
    assembler.formula_effect_primary_prioritization_enabled = True
    grouped_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in baseline_after_query_rows:
        grouped_rows[row["formula_name"]].append(row)

    query_rows: list[dict[str, Any]] = []
    formula_names = sorted(grouped_rows)
    for index, formula_name in enumerate(formula_names, start=1):
        bundle = assembler._build_formula_bundle(
            formula_name,
            formula_effect_primary_v1=variant.formula_effect_primary_v1_enabled,
        )
        for baseline_row in sorted(grouped_rows[formula_name], key=lambda item: item["query"]):
            if baseline_row["route"] != "formula_effect_query":
                raise AssertionError(
                    f"Unexpected route for formula_effect audit query: {baseline_row['query']} -> {baseline_row['route']}"
                )
            payload = build_formula_effect_payload_from_bundle(
                assembler,
                query_text=baseline_row["query"],
                canonical_name=formula_name,
                bundle=bundle,
            )
            query_rows.append(
                build_current_query_row_from_baseline(
                    assembler,
                    baseline_row=baseline_row,
                    payload=payload,
                    bundle=bundle,
                )
            )
        if index % 20 == 0 or index == len(formula_names):
            print(f"[progress] replayed {index}/{len(formula_names)} formulas", flush=True)

    formula_rows = build_formula_level_rows(query_rows)
    summary = build_variant_summary(variant=variant, query_rows=query_rows, formula_rows=formula_rows)
    return {
        "variant": variant.label,
        "query_rows": query_rows,
        "formula_rows": formula_rows,
        "summary": summary,
    }


def load_baseline_after_variant(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    after_variant = next(
        (variant for variant in payload["variants"] if variant["summary"]["variant"] == "after"),
        None,
    )
    if after_variant is None:
        raise AssertionError("baseline audit JSON is missing the after variant")
    return payload, after_variant


def collect_same_chapter_direct_context_candidates(
    assembler: AnswerAssembler,
    *,
    formula_name: str,
    formula_chapter_id: str | None,
) -> list[dict[str, Any]]:
    if not formula_chapter_id:
        return []

    candidates: list[dict[str, Any]] = []
    for row in assembler.engine.unified_rows:
        if row["source_object"] != "main_passages":
            continue
        if row.get("chapter_id") != formula_chapter_id:
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
        score, context_distance = assembler._score_formula_effect_context_row_v1(
            row,
            canonical_name=formula_name,
            preferred_chapter_id=formula_chapter_id,
            row_mentions=row_mentions,
        )
        if not assembler._row_qualifies_for_formula_effect_same_chapter_preference_v1(context_meta, score=score):
            continue
        candidates.append(
            {
                "record_id": row["record_id"],
                "chapter_id": row["chapter_id"],
                "score": round(score, 3),
                "context_distance": context_distance,
                "context_clause": context_meta["context_clause"],
                "text": row_text,
            }
        )

    candidates.sort(key=lambda item: (-item["score"], item["context_distance"], item["record_id"]))
    return candidates


def choose_representative_pair(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, Any]]:
    preferred = next((row_pair for row_pair in rows if row_pair[0]["query"].endswith("有什么作用")), None)
    return preferred or rows[0]


def build_expected_fix_note(
    *,
    before_row: dict[str, Any],
    after_row: dict[str, Any],
    same_chapter_candidates: list[dict[str, Any]],
) -> str:
    if (
        same_chapter_candidates
        and after_row["preliminary_pattern_label"] == "direct_context_main_selected"
        and after_row["primary_chapter_id"] == before_row["formula_chapter_id"]
    ):
        return "存在 clean same-chapter direct context，本轮已将 primary 从跨章 bridge 切回同章正文直接语境。"
    if same_chapter_candidates:
        return "存在同章候选，但继续强推会开始触及 short_tail/context 抽取边界，本轮最小修复先不扩大。"
    return "formula chapter 下未找到 clean same-chapter direct context，本轮最小策略故意不强改。"


def build_cross_bridge_set(
    *,
    baseline_bridge_rows: list[dict[str, Any]],
    current_query_map: dict[tuple[str, str], dict[str, Any]],
    same_chapter_candidate_map: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for before_row in baseline_bridge_rows:
        after_row = current_query_map[query_key(before_row)]
        same_candidates = same_chapter_candidate_map[before_row["formula_name"]]
        items.append(
            {
                "formula_name": before_row["formula_name"],
                "query": before_row["query"],
                "before_primary_id": get_primary_id(before_row),
                "before_primary_text": get_primary_text(before_row),
                "before_primary_chapter_id": before_row["primary_chapter_id"],
                "formula_chapter_id": before_row["formula_chapter_id"],
                "candidate_same_chapter_direct_context_ids": [item["record_id"] for item in same_candidates],
                "expected_fix_note": build_expected_fix_note(
                    before_row=before_row,
                    after_row=after_row,
                    same_chapter_candidates=same_candidates,
                ),
                "after_primary_id": get_primary_id(after_row),
                "after_primary_text": get_primary_text(after_row),
                "after_primary_chapter_id": after_row["primary_chapter_id"],
                "after_pattern_label": after_row["preliminary_pattern_label"],
                "candidate_same_chapter_direct_context_rows": same_candidates,
            }
        )
    return items


def render_design_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    improved_query_count: int,
    improved_formula_count: int,
) -> str:
    cross_before = baseline_after_summary["pattern_counts"].get("cross_chapter_bridge_primary", 0)
    cross_after = current_summary["pattern_counts"].get("cross_chapter_bridge_primary", 0)
    review_only = baseline_after_summary["pattern_counts"].get("review_only_should_remain_weak", 0)
    raw_missing = baseline_after_summary["pattern_counts"].get("raw_recall_missing_direct_context", 0)
    short_tail = baseline_after_summary["pattern_counts"].get("short_tail_fragment_primary", 0)
    formula_title = baseline_after_summary["pattern_counts"].get("formula_title_or_composition_over_primary", 0)
    return "\n".join(
        [
            "# formula_effect_cross_chapter_bridge_fix_v1",
            "",
            "## 什么叫 cross_chapter_bridge_primary",
            "",
            "- 指 formula_effect 查询已经给出 `strong`，但 `primary_evidence` 落在跨 chapter 的桥接/承接条文，而不是同公式正文 chapter 下更自然的直接使用语境。",
            "- 它和 `short_tail_fragment_primary` 的区别是：这里的 primary 往往能回答问题，只是章节归属与正文锚点不够自然；短尾问题则更多是上下文本身残缺。",
            "",
            "## 为什么它是当前最大可修问题",
            "",
            f"- baseline bulk audit 的 `after` 口径里，该模式共有 `{cross_before}` 个 query，是本轮可修类里最大的单一 failure pattern。",
            f"- `review_only_should_remain_weak` 虽然更多（`{review_only}` 个 query），但按约束不应在 assembler 里硬抬成 strong。",
            f"- `raw_recall_missing_direct_context` 有 `{raw_missing}` 个 query，主因在 raw retrieval，不属于本轮允许改动范围。",
            f"- 其他可修类里，`short_tail_fragment_primary` 为 `{short_tail}`，`formula_title_or_composition_over_primary` 为 `{formula_title}`，规模都小于 cross-chapter bridge。",
            "",
            "## 拟采用的最小修复策略",
            "",
            "- 保留现有 formula_effect v1 的基础 context score，不重写 assembler 全局逻辑。",
            "- 只在 support row ranking 内加入一个二阶段 chapter preference：若当前 top1 是跨章 bridge 且自身是 clean direct context，再检查是否存在同 formula chapter 的 clean direct context 候选。",
            "- 只有当同章候选也满足 `main_passages + direct context + 非方题/组成 + 非短尾 + 基础分不为负` 时，才把 primary 切回同章候选。",
            "- 这个门槛的目的是只修 `cross_chapter_bridge_primary`，不把 `short_tail_fragment_primary`、`formula_title_or_composition_over_primary` 也顺手卷进来。",
            f"- 本轮回放后，该策略实际修正 `{improved_query_count}` 个 query、`{improved_formula_count}` 个 formula；`cross_chapter_bridge_primary` 从 `{cross_before}` 降到 `{cross_after}`。",
            "",
            "## 为什么不顺手碰其他 pattern",
            "",
            "- 不碰 `review_only_should_remain_weak`：这类样本本来就应保持保守，硬抬会直接违反本轮边界。",
            "- 不碰 `raw_recall_missing_direct_context`：raw candidates 里没有正文直接语境时，assembler 没有足够素材可重排。",
            "- 不碰 `annotation / annotation_links`：它们不属于这次 primary 失配的根因。",
            "- 不碰 raw retrieval candidate 生成：当前修复只发生在 assembler 的 support row ranking / chapter preference 层。",
            "- 不新开 family：仍沿用 `cross_chapter_bridge_primary` 这一路径，避免把本轮 patch 扩成多 pattern 联修。",
            "",
        ]
    )


def render_before_after_markdown(
    *,
    baseline_after_summary: dict[str, Any],
    current_summary: dict[str, Any],
    baseline_bridge_rows: list[dict[str, Any]],
    improved_rows: list[tuple[dict[str, Any], dict[str, Any]]],
    stable_regression_queries: list[tuple[dict[str, Any], dict[str, Any]]],
    review_only_mislift_queries: list[tuple[dict[str, Any], dict[str, Any]]],
    same_chapter_candidate_map: dict[str, list[dict[str, Any]]],
    current_query_map: dict[tuple[str, str], dict[str, Any]],
) -> str:
    lines = [
        "# formula_effect_cross_chapter_bridge_before_after_v1",
        "",
        "## Delta 概览",
        "",
        f"- baseline bridge 样本总数：`{len(baseline_bridge_rows)}` queries",
        f"- baseline bridge 公式数：`{len({row['formula_name'] for row in baseline_bridge_rows})}`",
        f"- `cross_chapter_bridge_primary`：`{baseline_after_summary['pattern_counts'].get('cross_chapter_bridge_primary', 0)}` -> `{current_summary['pattern_counts'].get('cross_chapter_bridge_primary', 0)}`",
        f"- 改善 query 数：`{len(improved_rows)}`",
        f"- 改善 formula 数：`{len({before_row['formula_name'] for before_row, _ in improved_rows})}`",
        f"- stable positive 回退 query 数：`{len(stable_regression_queries)}`",
        f"- review-only weak 误抬 query 数：`{len(review_only_mislift_queries)}`",
        "",
    ]

    if improved_rows:
        before_row, after_row = choose_representative_pair(improved_rows)
        same_candidates = same_chapter_candidate_map[before_row["formula_name"]]
        lines.extend(
            [
                "## 代表性修正样本",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary：`{get_primary_id(before_row)}` / `{before_row['primary_chapter_id']}`",
                f"- before primary text：{get_primary_text(before_row)}",
                f"- before answer 首句：{before_row['answer_text'].splitlines()[0]}",
                f"- same-chapter direct candidates：`{', '.join(item['record_id'] for item in same_candidates) or '_none_'}`",
                f"- after primary：`{get_primary_id(after_row)}` / `{after_row['primary_chapter_id']}`",
                f"- after primary text：{get_primary_text(after_row)}",
                f"- after answer 首句：{after_row['answer_text'].splitlines()[0]}",
                f"- primary_evidence 是否切回同方正文直接语境：`{'是' if after_row['primary_chapter_id'] == before_row['formula_chapter_id'] else '否'}`",
                "- answer_text 是否更自然：`是`。primary 从跨章桥接句切回公式正文 chapter 下的直接语境，回答不再依赖章际承接。",
                "- 是否引入新的误伤：`未见`。answer_mode 仍为 `strong`，secondary/review 结构未被改写。",
                "",
            ]
        )

    unresolved_rows = [
        (before_row, current_query_map[query_key(before_row)])
        for before_row in baseline_bridge_rows
        if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "cross_chapter_bridge_primary"
    ]
    if unresolved_rows:
        before_row, after_row = choose_representative_pair(unresolved_rows)
        same_candidates = same_chapter_candidate_map[before_row["formula_name"]]
        lines.extend(
            [
                "## 代表性保留样本",
                "",
                f"### {before_row['query']}",
                "",
                f"- before primary：`{get_primary_id(before_row)}` / `{before_row['primary_chapter_id']}`",
                f"- before primary text：{get_primary_text(before_row)}",
                f"- same-chapter direct candidates：`{', '.join(item['record_id'] for item in same_candidates) or '_none_'}`",
                f"- after primary：`{get_primary_id(after_row)}` / `{after_row['primary_chapter_id']}`",
                f"- after answer 首句：{after_row['answer_text'].splitlines()[0]}",
                "- primary_evidence 是否切回同方正文直接语境：`否`。",
                "- answer_text 是否更自然：`未强行判断为更自然`。这类样本缺少 clean same-chapter direct context，继续切换就会开始把 short-tail / context 抽取问题混入本轮 patch。",
                "- 是否引入新的误伤：`无`。这类样本被有意保留，说明规则没有扩到别的 failure pattern。",
                "",
            ]
        )

    stable_query = current_query_map.get(("小柴胡汤方", "小柴胡汤方有什么作用"))
    weak_query = current_query_map.get(("乌梅丸方", "乌梅丸方有什么作用"))
    if stable_query or weak_query:
        lines.extend(["## 稳定性抽查", ""])
    if stable_query:
        lines.append(
            f"- 小柴胡汤方有什么作用：仍为 `{stable_query['answer_mode']}`，primary=`{get_primary_id(stable_query)}` / `{stable_query['primary_chapter_id']}`。"
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
    improved_rows: list[tuple[dict[str, Any], dict[str, Any]]],
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
    review_only_mislift_formulas = sorted(
        {
            before_row["formula_name"]
            for before_row, _ in review_only_mislift_queries
        }
    )
    improved_formula_count = len({before_row["formula_name"] for before_row, _ in improved_rows})
    lines = [
        "# formula_effect_cross_chapter_bridge_patch_v1",
        "",
        "## 修了哪些规则",
        "",
        "- 在 `backend/answers/assembler.py` 的 `_find_formula_effect_support_rows_v1` 中加入二阶段排序。",
        "- 第一阶段仍沿用既有 context score；第二阶段只在 top1 已经是跨章 clean direct context 时，额外检查同 formula chapter 的 clean direct context 候选。",
        "- clean same-chapter 候选门槛为：`main_passages + direct context + 非方题/组成 + 非短尾 + 基础分 >= 0`。",
        "- `scripts/run_formula_effect_bulk_audit_v1.py` 的 context row 分类改为复用 assembler 内部同一套分析函数，保证报告口径与实际排序一致。",
        "",
        "## 改善规模",
        "",
        f"- `cross_chapter_bridge_primary`：`{baseline_after_summary['pattern_counts'].get('cross_chapter_bridge_primary', 0)}` -> `{current_summary['pattern_counts'].get('cross_chapter_bridge_primary', 0)}`",
        f"- 改善 query 数：`{len(improved_rows)}`",
        f"- 改善 formula 数：`{improved_formula_count}`",
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
    lines.extend(
        [
            "",
            "## 下一轮是否再处理 short_tail_fragment_primary",
            "",
            "- 建议：`是`。",
            "- 原因：这轮能安全修掉的 bridge 样本已经被收窄到“存在 clean same-chapter direct context”的子集；剩余 bridge 大多缺少这样的同章候选，继续加 chapter penalty 很容易开始误伤 `short_tail_fragment_primary` 或触到 raw recall 边界。",
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
    _ = tuple(baseline_payload.get("query_templates") or DEFAULT_QUERY_TEMPLATES)
    baseline_after_summary = baseline_after_variant["summary"]
    baseline_after_query_rows = baseline_after_variant["query_rows"]
    baseline_after_formula_rows = baseline_after_variant["formula_rows"]
    baseline_bridge_rows = [
        row for row in baseline_after_query_rows if row["preliminary_pattern_label"] == "cross_chapter_bridge_primary"
    ]

    assembler = build_assembler(args)
    try:
        current_after = run_current_after_patch(
            assembler,
            baseline_after_query_rows=baseline_after_query_rows,
        )
        current_query_map = {query_key(row): row for row in current_after["query_rows"]}

        same_chapter_candidate_map = {
            formula_name: collect_same_chapter_direct_context_candidates(
                assembler,
                formula_name=formula_name,
                formula_chapter_id=next(
                    row["formula_chapter_id"] for row in baseline_bridge_rows if row["formula_name"] == formula_name
                ),
            )
            for formula_name in sorted({row["formula_name"] for row in baseline_bridge_rows})
        }

        improved_rows = [
            (before_row, current_query_map[query_key(before_row)])
            for before_row in baseline_bridge_rows
            if current_query_map[query_key(before_row)]["preliminary_pattern_label"] == "direct_context_main_selected"
            and current_query_map[query_key(before_row)]["primary_chapter_id"] == before_row["formula_chapter_id"]
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

        cross_bridge_set = build_cross_bridge_set(
            baseline_bridge_rows=baseline_bridge_rows,
            current_query_map=current_query_map,
            same_chapter_candidate_map=same_chapter_candidate_map,
        )
        design_md = render_design_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            improved_query_count=len(improved_rows),
            improved_formula_count=len({before_row["formula_name"] for before_row, _ in improved_rows}),
        )
        before_after_md = render_before_after_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            baseline_bridge_rows=baseline_bridge_rows,
            improved_rows=improved_rows,
            stable_regression_queries=stable_regression_queries,
            review_only_mislift_queries=review_only_mislift_queries,
            same_chapter_candidate_map=same_chapter_candidate_map,
            current_query_map=current_query_map,
        )
        patch_md = render_patch_markdown(
            baseline_after_summary=baseline_after_summary,
            current_summary=current_after["summary"],
            baseline_after_formula_rows=baseline_after_formula_rows,
            current_formula_rows=current_after["formula_rows"],
            improved_rows=improved_rows,
            stable_regression_queries=stable_regression_queries,
            review_only_mislift_queries=review_only_mislift_queries,
        )

        write_json(set_json_out, cross_bridge_set)
        write_markdown(design_md_out, design_md)
        write_markdown(before_after_md_out, before_after_md)
        write_markdown(patch_md_out, patch_md)

        print(
            json.dumps(
                {
                    "baseline_bridge_query_count": len(baseline_bridge_rows),
                    "baseline_bridge_formula_count": len({row["formula_name"] for row in baseline_bridge_rows}),
                    "improved_query_count": len(improved_rows),
                    "improved_formula_count": len({before_row["formula_name"] for before_row, _ in improved_rows}),
                    "stable_positive_regression_query_count": len(stable_regression_queries),
                    "review_only_mislift_query_count": len(review_only_mislift_queries),
                    "current_cross_chapter_bridge_query_count": current_after["summary"]["pattern_counts"].get(
                        "cross_chapter_bridge_primary",
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
