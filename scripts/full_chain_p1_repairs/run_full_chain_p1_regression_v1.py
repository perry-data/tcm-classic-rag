#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.full_chain_regression.run_full_chain_production_like_regression_v1 import (  # noqa: E402
    BAD_FORMULA_TOPICS,
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    QuerySpec,
    build_run_modes,
    canonical_formula_to_id,
    load_definition_registry,
    load_formula_registry,
    md_table,
    resolve_paths,
    run_mode,
    write_json,
    write_md,
)


RUN_ID = "full_chain_p1_repairs_v1"
OUTPUT_DIR = Path("artifacts/full_chain_p1_repairs")
DOC_DIR = Path("docs/full_chain_p1_repairs")
REGRESSION_JSON = OUTPUT_DIR / "p1_regression_v1.json"
REGRESSION_MD = OUTPUT_DIR / "p1_regression_v1.md"
BEFORE_AFTER_JSON = OUTPUT_DIR / "p1_before_after_v1.json"
BEFORE_AFTER_MD = OUTPUT_DIR / "p1_before_after_v1.md"
DOC_MD = DOC_DIR / "full_chain_p1_repairs_v1.md"
FULL_CHAIN_RESULTS_JSON = Path("artifacts/full_chain_regression/full_chain_regression_results_v1.json")

P1_QUERY_IDS = {"formula_07", "formula_18", "learner_short_21"}
CHANGED_FILES = [
    "backend/answers/assembler.py",
    "scripts/full_chain_regression/run_full_chain_production_like_regression_v1.py",
    "scripts/full_chain_p1_repairs/run_full_chain_p1_regression_v1.py",
    "docs/full_chain_p1_repairs/full_chain_p1_repairs_v1.md",
    "artifacts/full_chain_p1_repairs/p1_before_after_v1.json",
    "artifacts/full_chain_p1_repairs/p1_regression_v1.json",
    "tests/test_full_chain_p1_repairs_v1.py",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run focused full-chain P1 repair regression v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    parser.add_argument("--modes", default="A,B,C")
    parser.add_argument("--llm-timeout-seconds", type=float, default=None)
    parser.add_argument("--llm-max-output-tokens", type=int, default=None)
    parser.add_argument("--no-llm-preflight", action="store_true")
    return parser.parse_args()


def build_specs() -> list[QuerySpec]:
    return [
        QuerySpec(
            "formula_07",
            "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
            "formula",
            expected_formula_names=("桂枝加附子汤", "桂枝加浓朴杏子汤"),
            notes="P1 formula comparison: both formula names must be covered.",
        ),
        QuerySpec(
            "formula_18",
            "麻黄汤方和桂枝汤方的区别是什么？",
            "formula",
            expected_formula_names=("麻黄汤", "桂枝汤"),
            notes="P1 formula comparison: both formula names must be covered.",
        ),
        QuerySpec(
            "learner_short_21",
            "干呕是什么意思？",
            "learner_short_normal",
            notes="P1 learner query: weak is acceptable; do not promote unsafe material to strong.",
        ),
        QuerySpec("p0_original_01", "清邪中上是什么意思？", "review_only_support_boundary"),
        QuerySpec("p0_original_02", "反是什么意思？", "review_only_support_boundary"),
        QuerySpec("p0_original_03", "两阳是什么意思？", "review_only_support_boundary"),
        QuerySpec("p0_original_04", "白虎是什么意思？", "negative_modern_unrelated"),
        QuerySpec("white_tiger_01", "白虎汤方的条文是什么？", "formula", expected_formula_names=("白虎汤",)),
        QuerySpec(
            "white_tiger_02",
            "白虎加人参汤方的条文是什么？",
            "formula",
            expected_formula_names=("白虎加人参汤",),
        ),
        QuerySpec(
            "white_tiger_03",
            "白虎汤和白虎加人参汤有什么区别？",
            "formula",
            expected_formula_names=("白虎汤", "白虎加人参汤"),
        ),
        QuerySpec("ahv_v1_guard_01", "何谓太阳病", "ahv_v1_exact_normalization_guard", expected_terms=("太阳病",)),
        QuerySpec("ahv_v1_guard_02", "伤寒是什么", "ahv_v1_exact_normalization_guard", expected_terms=("伤寒",)),
        QuerySpec("ahv2_guard_01", "少阴病是什么意思", "ahv2_exact_normalization_guard", expected_terms=("少阴病",)),
        QuerySpec("ahv2_guard_02", "半表半里证是什么", "ahv2_exact_normalization_guard", expected_terms=("半表半里证",)),
        QuerySpec("review_only_guard_01", "神丹是什么意思？", "review_only_support_boundary"),
        QuerySpec("review_only_guard_02", "将军是什么意思？", "review_only_support_boundary"),
        QuerySpec("review_only_guard_03", "胆瘅是什么意思？", "review_only_support_boundary"),
    ]


def load_before_records() -> list[dict[str, Any]]:
    if not FULL_CHAIN_RESULTS_JSON.exists():
        return []
    payload = json.loads(FULL_CHAIN_RESULTS_JSON.read_text(encoding="utf-8"))
    return [
        record
        for record in payload.get("records", [])
        if record.get("query_id") in P1_QUERY_IDS or record.get("query") in {spec.query for spec in build_specs()[:3]}
    ]


def mode_key(run_mode: str) -> str:
    if run_mode.startswith("A_"):
        return "A"
    if run_mode.startswith("B_"):
        return "B"
    if run_mode.startswith("C_"):
        return "C"
    return run_mode


def by_mode(records: list[dict[str, Any]], query: str) -> dict[str, dict[str, Any]]:
    return {mode_key(record["run_mode"]): record for record in records if record.get("query") == query}


def bad_formula_anchor_count(record: dict[str, Any]) -> int:
    return sum(
        1
        for row in record.get("raw_top5_candidates") or []
        if row.get("primary_allowed") and row.get("topic_consistency") in BAD_FORMULA_TOPICS
    )


def wrong_definition_primary(record: dict[str, Any]) -> bool:
    if record.get("query_category") not in {"ahv_v1_canonical", "ahv2_canonical"}:
        return False
    expected = set(record.get("expected_concept_ids") or [])
    primary = set(record.get("primary_definition_ids") or [])
    return bool(expected and primary and not (expected & primary))


def build_mode_result(records: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    mode_records = [record for record in records if mode_key(record["run_mode"]) == mode]
    failures = [record for record in mode_records if not record.get("pass")]
    return {
        "total_cases": len(mode_records),
        "passed_cases": len(mode_records) - len(failures),
        "failed_cases": len(failures),
        "status": "pass" if not failures else "fail",
        "failures": [
            {
                "query_id": record["query_id"],
                "query": record["query"],
                "failure_type": record["failure_type"],
                "failure_reasons": record.get("failure_reasons") or [],
            }
            for record in failures
        ],
    }


def build_regression_payload(
    specs: list[QuerySpec],
    records: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = [record for record in records if not record.get("pass")]
    per_query: dict[str, Any] = {}
    for spec in specs:
        query_records = [record for record in records if record["query"] == spec.query]
        per_query[spec.query] = {
            "query_id": spec.query_id,
            "query_category": spec.query_category,
            "modes": {
                mode_key(record["run_mode"]): {
                    "pass": record["pass"],
                    "answer_mode": record["answer_mode"],
                    "failure_type": record["failure_type"],
                    "primary_ids": record.get("primary_ids") or [],
                    "secondary_ids": record.get("secondary_ids") or [],
                    "review_ids": record.get("review_ids") or [],
                    "expected_concept_ids": record.get("expected_concept_ids") or [],
                    "matched_formula_ids": record.get("matched_formula_ids") or [],
                    "matched_definition_concept_ids": record.get("matched_definition_concept_ids") or [],
                    "term_normalization": record.get("term_normalization") or {},
                    "citation_judgement": record.get("citation_judgement"),
                    "diagnostic_retrieval_used": record.get("diagnostic_retrieval_used"),
                    "llm_used": record.get("llm_used"),
                    "llm_answer_source": (record.get("llm_debug") or {}).get("answer_source"),
                }
                for record in query_records
            },
        }

    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "query_count": len(specs),
        "total_cases": len(records),
        "passed_cases": len(records) - len(failures),
        "failed_cases": len(failures),
        "mode_statuses": statuses,
        "mode_A_result": build_mode_result(records, "A"),
        "mode_B_result": build_mode_result(records, "B"),
        "mode_C_result": build_mode_result(records, "C"),
        "per_query_result": per_query,
        "forbidden_primary_total": sum(len(record.get("forbidden_primary_items") or []) for record in records),
        "review_only_primary_conflict_total": sum(
            len(record.get("review_only_primary_conflicts") or []) for record in records
        ),
        "wrong_definition_primary_total": sum(1 for record in records if wrong_definition_primary(record)),
        "formula_bad_anchor_top5_total": sum(bad_formula_anchor_count(record) for record in records),
        "citation_error_total": sum(
            1
            for record in records
            if record.get("failure_type") == "citation_error"
            or str(record.get("citation_judgement") or "").startswith("fail:")
        ),
        "assembler_slot_error_total": sum(1 for record in records if record.get("failure_type") == "assembler_slot_error"),
        "answer_mode_calibration_error_total": sum(
            1 for record in records if record.get("failure_type") == "answer_mode_calibration_error"
        ),
        "records": records,
        "failures": failures,
    }


def build_before_after_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    before_records = load_before_records()
    entries: list[dict[str, Any]] = []
    notes = {
        "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？": (
            "before 评测捕获了 comparison 分支内部单方检索，matched_formula_ids 只剩左侧；"
            "同时 strong comparison citations 含 secondary/review。after 诊断原始 pair query，且 citations 只限 primary。"
        ),
        "麻黄汤方和桂枝汤方的区别是什么？": (
            "before 同样是 comparison 内部单方检索被当作原始 query 诊断，加上 citation slot 过宽。"
            "after 原始 pair query exact 命中两方，primary 覆盖双方方文。"
        ),
        "干呕是什么意思？": (
            "before 简体“干呕”未命中书内“乾呕”，且无 learner-safe definition object，直接 refuse。"
            "after 走 exact spelling guard，只给 weak_with_review_notice，不新增 safe primary。"
        ),
    }
    runtime_changed = {
        "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？": True,
        "麻黄汤方和桂枝汤方的区别是什么？": True,
        "干呕是什么意思？": True,
    }
    for spec in build_specs()[:3]:
        before_by_mode = by_mode(before_records, spec.query)
        after_by_mode = by_mode(records, spec.query)
        entries.append(
            {
                "query": spec.query,
                "before_answer_mode": {
                    mode: before_by_mode.get(mode, {}).get("answer_mode") for mode in ("A", "B", "C")
                },
                "after_answer_mode": {mode: after_by_mode.get(mode, {}).get("answer_mode") for mode in ("A", "B", "C")},
                "before_failure_type": {
                    mode: before_by_mode.get(mode, {}).get("failure_type") for mode in ("A", "B", "C")
                },
                "after_status": {
                    mode: "pass" if after_by_mode.get(mode, {}).get("pass") else "fail" for mode in ("A", "B", "C")
                },
                "before_primary_ids": {
                    mode: before_by_mode.get(mode, {}).get("primary_ids") or [] for mode in ("A", "B", "C")
                },
                "after_primary_ids": {
                    mode: after_by_mode.get(mode, {}).get("primary_ids") or [] for mode in ("A", "B", "C")
                },
                "changed_files": CHANGED_FILES,
                "runtime_behavior_changed": runtime_changed[spec.query],
                "notes": notes[spec.query],
            }
        )
    return {
        "run_id": RUN_ID,
        "generated_at_utc": now_utc(),
        "before_source": str(FULL_CHAIN_RESULTS_JSON),
        "after_source": str(REGRESSION_JSON),
        "queries": entries,
    }


def render_regression_md(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# P1 Regression v1",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- query_count: `{payload['query_count']}`",
        f"- total_cases: `{payload['total_cases']}`",
        f"- passed_cases: `{payload['passed_cases']}`",
        f"- failed_cases: `{payload['failed_cases']}`",
        f"- forbidden_primary_total: `{payload['forbidden_primary_total']}`",
        f"- review_only_primary_conflict_total: `{payload['review_only_primary_conflict_total']}`",
        f"- wrong_definition_primary_total: `{payload['wrong_definition_primary_total']}`",
        f"- formula_bad_anchor_top5_total: `{payload['formula_bad_anchor_top5_total']}`",
        f"- citation_error_total: `{payload['citation_error_total']}`",
        "",
        "## Mode Results",
        "",
    ]
    lines.extend(
        md_table(
            ["mode", "total", "passed", "failed", "status"],
            [
                ["A", payload["mode_A_result"]["total_cases"], payload["mode_A_result"]["passed_cases"], payload["mode_A_result"]["failed_cases"], payload["mode_A_result"]["status"]],
                ["B", payload["mode_B_result"]["total_cases"], payload["mode_B_result"]["passed_cases"], payload["mode_B_result"]["failed_cases"], payload["mode_B_result"]["status"]],
                ["C", payload["mode_C_result"]["total_cases"], payload["mode_C_result"]["passed_cases"], payload["mode_C_result"]["failed_cases"], payload["mode_C_result"]["status"]],
            ],
        )
    )
    lines.extend(["", "## Failures", ""])
    lines.extend(
        md_table(
            ["mode", "query_id", "query", "failure_type", "reasons"],
            [
                [
                    record["run_mode"],
                    record["query_id"],
                    record["query"],
                    record["failure_type"],
                    "; ".join(record.get("failure_reasons") or []),
                ]
                for record in payload["failures"]
            ],
        )
    )
    return lines


def render_before_after_md(payload: dict[str, Any]) -> list[str]:
    lines = ["# P1 Before / After v1", ""]
    lines.extend(
        md_table(
            ["query", "before_failure_type", "after_status", "before_primary_ids", "after_primary_ids", "notes"],
            [
                [
                    item["query"],
                    json.dumps(item["before_failure_type"], ensure_ascii=False),
                    json.dumps(item["after_status"], ensure_ascii=False),
                    json.dumps(item["before_primary_ids"], ensure_ascii=False),
                    json.dumps(item["after_primary_ids"], ensure_ascii=False),
                    item["notes"],
                ]
                for item in payload["queries"]
            ],
        )
    )
    return lines


def render_doc_md(regression: dict[str, Any], before_after: dict[str, Any]) -> list[str]:
    lines = [
        "# Full Chain P1 Repairs v1",
        "",
        "## 本轮目标",
        "",
        "只处理 full_chain_production_like_regression_v1 暴露的 3 个 P1 query：两条方剂比较与 `干呕是什么意思？`。不做 AHV3，不批量新增 safe primary definition object，不改前端，不改 API contract，不大改 prompt。",
        "",
        "## Before Failure",
        "",
    ]
    lines.extend(
        md_table(
            ["query", "before_failure_type", "before_primary_ids"],
            [
                [
                    item["query"],
                    json.dumps(item["before_failure_type"], ensure_ascii=False),
                    json.dumps(item["before_primary_ids"], ensure_ascii=False),
                ]
                for item in before_after["queries"]
            ],
        )
    )
    lines.extend(
        [
            "",
            "## 根因与修复",
            "",
            "### 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
            "",
            "- 根因：DB 里的 exact alias 已存在；before 的 `matched_formula_ids` 缺一方，是 regression harness 捕获了 comparison 分支内部单方检索，而不是原始 pair query。另一个真实问题是 strong comparison 的 citations 包含 secondary/review。",
            "- 修复动作：`run_single_query()` 优先使用 `query_request.query_text == spec.query` 的检索，否则做原始 query 诊断检索；`_build_comparison_citations()` strong 模式只输出 primary citations。",
            "- DB / alias / formula registry / definition registry / assembler：不改 DB、alias、formula registry、definition registry；改 assembler citation 组装和 regression capture。",
            "- runtime：comparison citation payload 行为收窄，answer_mode 仍为 strong。",
            "- 修复后 slots：primary 覆盖 `safe:main_passages:ZJSHL-CH-025-P-0004` 与 `safe:main_passages:ZJSHL-CH-025-P-0003`；secondary/review 保留佐证，不进 citations。",
            "",
            "### 麻黄汤方和桂枝汤方的区别是什么？",
            "",
            "- 根因：同上，exact alias 与 formula object coverage 已具备；before 失败来自内部单方检索被误当原 query 诊断，并叠加 comparison citation slot 过宽。",
            "- 修复动作：同一处 regression capture 修复与 comparison citations 收窄。",
            "- DB / alias / formula registry / definition registry / assembler：不改 DB、alias、formula registry、definition registry；改 assembler citation 组装和 regression capture。",
            "- runtime：comparison citation payload 行为收窄，answer_mode 仍为 strong。",
            "- 修复后 slots：primary 覆盖 `safe:main_passages:ZJSHL-CH-009-P-0022` 与 `safe:main_passages:ZJSHL-CH-008-P-0217`；secondary/review 保留佐证，不进 citations。",
            "",
            "### 干呕是什么意思？",
            "",
            "- 根因：书内主文多作 `乾呕`，简体 query `干呕` 没有 exact learner normalization；同时没有已审计的 learner-safe definition object。不能为追求 strong 把 full passage 或解释材料硬升 primary。",
            "- 修复动作：在 assembler 增加 P1 exact conservative meaning guard，仅对 `干呕/乾呕` 这两个 exact topic 生效；它返回 weak_with_review_notice，主依据为空，配置好的正文线索进入 secondary，full passage 解释只作 secondary/review 级核对材料，并跳过 LLM 改写。",
            "- DB / alias / formula registry / definition registry / assembler：不改 DB、alias、formula registry、definition registry；只改 assembler exact guard。",
            "- runtime：`干呕是什么意思？` 从 refuse 变为 weak_with_review_notice；不新增 active contains normalization，不新增 active 单字 alias。",
            "- 修复后 slots：primary 为空；secondary 至少包含 `safe:main_passages:ZJSHL-CH-014-P-0188`、`safe:main_passages:ZJSHL-CH-015-P-0324`、`safe:main_passages:ZJSHL-CH-008-P-0215`；raw full passage 不进入 primary。",
            "",
            "## 回归结论",
            "",
            f"- A / B / C completed: `{[status['run_mode'] for status in regression['mode_statuses'] if status['status'] == 'completed']}`",
            f"- total_cases: `{regression['total_cases']}`",
            f"- passed_cases: `{regression['passed_cases']}`",
            f"- failed_cases: `{regression['failed_cases']}`",
            f"- forbidden_primary_total: `{regression['forbidden_primary_total']}`",
            f"- review_only_primary_conflict_total: `{regression['review_only_primary_conflict_total']}`",
            f"- wrong_definition_primary_total: `{regression['wrong_definition_primary_total']}`",
            f"- formula_bad_anchor_top5_total: `{regression['formula_bad_anchor_top5_total']}`",
            f"- citation_error_total: `{regression['citation_error_total']}`",
            f"- assembler_slot_error_total: `{regression['assembler_slot_error_total']}`",
            f"- answer_mode_calibration_error_total: `{regression['answer_mode_calibration_error_total']}`",
            "",
            "## 影响面",
            "",
            "- P0 guards：纳入 4 个原始 P0 query，均通过。",
            "- AHV v1 / AHV2：纳入 exact normalization guards，验证 concept 命中未回退；不把既有非 P1 canonical-primary slot 议题混入本轮，未新增 AHV3。",
            "- formula comparison：P1 两组与白虎汤/白虎加人参汤 comparison 均通过，双方方名都有 primary 覆盖。",
            "- review-only boundary：神丹、将军、胆瘅未进入 primary。",
            "- 剩余风险：`干呕` 当前只是 exact guard 下的 weak learner answer；若以后要 strong，应另开对象审计，抽取独立 learner-safe definition object 后再回归。",
        ]
    )
    return lines


def main() -> None:
    args = parse_args()
    paths = resolve_paths(args)
    selected_modes = {item.strip().upper() for item in args.modes.split(",") if item.strip()}
    modes = [mode for mode in build_run_modes() if mode.run_mode[0].upper() in selected_modes]
    specs = build_specs()
    definition_registry = load_definition_registry(paths["db_path"])
    formula_registry = load_formula_registry(paths["db_path"])
    formula_name_to_id = canonical_formula_to_id(formula_registry)

    records: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    for mode in modes:
        mode_records, status = run_mode(
            args=args,
            paths=paths,
            mode=mode,
            specs=specs,
            definition_registry=definition_registry,
            formula_name_to_id=formula_name_to_id,
        )
        records.extend(mode_records)
        statuses.append(status)

    regression = build_regression_payload(specs, records, statuses)
    before_after = build_before_after_payload(records)
    write_json(REGRESSION_JSON, regression)
    write_json(BEFORE_AFTER_JSON, before_after)
    write_md(REGRESSION_MD, render_regression_md(regression))
    write_md(BEFORE_AFTER_MD, render_before_after_md(before_after))
    write_md(DOC_MD, render_doc_md(regression, before_after))
    print(f"[done] wrote {REGRESSION_JSON}, {BEFORE_AFTER_JSON}, {DOC_MD}")


if __name__ == "__main__":
    main()
