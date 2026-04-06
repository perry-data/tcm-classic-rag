#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    json_dumps,
    log,
)
from backend.retrieval.minimal import DEFAULT_EXAMPLES


DEFAULT_COMPARISON_EXAMPLES_OUT = "artifacts/comparison_examples.json"
DEFAULT_COMPARISON_SMOKE_OUT = "artifacts/comparison_smoke_checks.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

COMPARISON_EXAMPLES = [
    {
        "example_id": "comparison_formula_delta_strong",
        "description": "比较成功且证据充分，直接回答显式加减差异。",
        "query": "桂枝加附子汤方比桂枝加厚朴杏子汤方少了什么？",
        "expected_mode": "strong",
    },
    {
        "example_id": "comparison_context_weak",
        "description": "比较成功，但用户追问条文语境时只能 weak。",
        "query": "桂枝去芍药汤方和桂枝去芍药加附子汤方的条文语境有什么不同？",
        "expected_mode": "weak_with_review_notice",
    },
    {
        "example_id": "comparison_entity_unstable",
        "description": "比较意图存在，但第二个方名识别不充分。",
        "query": "桂枝加附子汤方和桂枝加厚朴那个方的区别是什么？",
        "expected_mode": "refuse",
    },
    {
        "example_id": "comparison_invalid_question",
        "description": "无效比较问题，超出本轮支持的优劣判断。",
        "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方哪个好？",
        "expected_mode": "refuse",
    },
    {
        "example_id": "comparison_demo_scene",
        "description": "最接近答辩演示场景的方剂辨析问题。",
        "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
        "expected_mode": "strong",
    },
]


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate comparison-answer examples and smoke checks.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH, help="Path to layered policy JSON.")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_COMPARISON_EXAMPLES_OUT,
        help="Where to write comparison example JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_COMPARISON_SMOKE_OUT,
        help="Where to write comparison smoke checks markdown.",
    )
    return parser.parse_args()


def build_examples_payload(results: list[dict[str, Any]], frozen_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "comparison_examples": results,
        "frozen_examples_validation": frozen_results,
    }


def run_comparison_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in COMPARISON_EXAMPLES:
        payload = assembler.assemble(example["query"])
        debug = assembler.get_last_comparison_debug()
        results.append(
            {
                **example,
                "payload": payload,
                "comparison_debug": debug,
            }
        )
    return results


def run_frozen_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        payload = assembler.assemble(example["query_text"])
        results.append(
            {
                "example_id": example["example_id"],
                "query": example["query_text"],
                "expected_mode": example["expected_mode"],
                "answer_mode": payload["answer_mode"],
                "pass": payload["answer_mode"] == example["expected_mode"],
            }
        )
    return results


def assert_expectations(results: list[dict[str, Any]], frozen_results: list[dict[str, Any]]) -> None:
    for result in results:
        if result["payload"]["answer_mode"] != result["expected_mode"]:
            raise AssertionError(f"{result['example_id']} mode regressed")
    if not all(result["pass"] for result in frozen_results):
        raise AssertionError("frozen examples regressed")


def build_smoke_markdown(
    command: str,
    comparison_results: list[dict[str, Any]],
    frozen_results: list[dict[str, Any]],
) -> str:
    lines = [
        "# Comparison Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 比较样例结论",
        "",
    ]

    for result in comparison_results:
        payload = result["payload"]
        debug = result["comparison_debug"] or {}
        recognized = bool(debug.get("comparison_valid")) and len(debug.get("recognized_entities", [])) == 2
        structured_diff = (debug.get("structured_difference_count") or 0) >= 2
        lines.extend(
            [
                f"### {result['example_id']}",
                "",
                f"- query: `{result['query']}`",
                f"- answer_mode: `{payload['answer_mode']}`",
                f"- 两个对象是否识别成功: `{recognized}`",
                f"- 是否形成结构化差异: `{structured_diff}`",
                f"- 是否保留 citations: `{bool(payload['citations'])}`",
                f"- primary={len(payload['primary_evidence'])}, secondary={len(payload['secondary_evidence'])}, review={len(payload['review_materials'])}",
                f"- answer_text: {payload['answer_text']}",
                "",
            ]
        )

    lines.extend(
        [
            "## 冻结样例回归",
            "",
        ]
    )
    for result in frozen_results:
        lines.append(
            f"- `{result['query']}` -> expected=`{result['expected_mode']}`, actual=`{result['answer_mode']}`, pass=`{result['pass']}`"
        )
    lines.append("")
    lines.append(f"- 是否破坏原三条冻结样例: `{not all(result['pass'] for result in frozen_results)}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    cache_dir = resolve_project_path(args.cache_dir)
    dense_chunks_index = resolve_project_path(args.dense_chunks_index)
    dense_chunks_meta = resolve_project_path(args.dense_chunks_meta)
    dense_main_index = resolve_project_path(args.dense_main_index)
    dense_main_meta = resolve_project_path(args.dense_main_meta)
    examples_out = resolve_project_path(args.examples_out)
    smoke_out = resolve_project_path(args.smoke_checks_out)

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)

    assembler = AnswerAssembler(
        db_path=db_path,
        policy_path=policy_path,
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=cache_dir,
        dense_chunks_index=dense_chunks_index,
        dense_chunks_meta=dense_chunks_meta,
        dense_main_index=dense_main_index,
        dense_main_meta=dense_main_meta,
    )
    try:
        log(f"[1/4] Loaded policy from {policy_path}")
        log(f"[2/4] Loaded hybrid retrieval database and dense assets from {db_path}")
        comparison_results = run_comparison_examples(assembler)
        frozen_results = run_frozen_examples(assembler)
        assert_expectations(comparison_results, frozen_results)
        examples_out.write_text(
            json_dumps(build_examples_payload(comparison_results, frozen_results)) + "\n",
            encoding="utf-8",
        )
        command = f"{Path(sys.executable).name} -m backend.checks.comparison_checks"
        smoke_out.write_text(
            build_smoke_markdown(command, comparison_results, frozen_results),
            encoding="utf-8",
        )
        log("[3/4] Ran comparison examples and validated frozen regressions")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        assembler.close()


if __name__ == "__main__":
    raise SystemExit(main())
