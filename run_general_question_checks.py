#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from general_question_strategy import detect_general_question
from run_answer_assembler import (
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_EXAMPLES,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    AnswerAssembler,
    json_dumps,
    log,
)


DEFAULT_GENERAL_EXAMPLES_OUT = "artifacts/general_question_examples.json"
DEFAULT_GENERAL_SMOKE_OUT = "artifacts/general_question_smoke_checks.md"
DEFAULT_GENERAL_EXAMPLES = [
    {
        "example_id": "taiyang_management_strong",
        "query_text": "太阳病应该怎么办？",
        "expected_mode": "strong",
        "expected_general_detected": True,
    },
    {
        "example_id": "taiyang_overview_strong",
        "query_text": "太阳病有哪些情况？",
        "expected_mode": "strong",
        "expected_general_detected": True,
    },
    {
        "example_id": "shaoyin_management_strong",
        "query_text": "少阴病应该怎么办？",
        "expected_mode": "strong",
        "expected_general_detected": True,
    },
    {
        "example_id": "liujing_management_weak",
        "query_text": "六经病应该怎么办？",
        "expected_mode": "weak_with_review_notice",
        "expected_general_detected": True,
    },
    {
        "example_id": "formula_pseudo_general",
        "query_text": "黄连汤方应该怎么办？",
        "expected_mode": "strong",
        "expected_general_detected": False,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run smoke checks for minimal general-question handling.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    parser.add_argument(
        "--examples-out",
        default=DEFAULT_GENERAL_EXAMPLES_OUT,
        help="Where to write general-question examples JSON.",
    )
    parser.add_argument(
        "--smoke-checks-out",
        default=DEFAULT_GENERAL_SMOKE_OUT,
        help="Where to write general-question smoke checks markdown.",
    )
    return parser.parse_args()


def run_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_GENERAL_EXAMPLES:
        payload = assembler.assemble(example["query_text"])
        general_detected = detect_general_question(example["query_text"]) is not None
        uses_structured_branching = "总括性问题" in payload["answer_text"] and "\n1." in payload["answer_text"]
        citations_preserved = bool(payload["citations"])
        results.append(
            {
                "example_id": example["example_id"],
                "query": example["query_text"],
                "expected_mode": example["expected_mode"],
                "answer_mode": payload["answer_mode"],
                "expected_general_detected": example["expected_general_detected"],
                "general_detected": general_detected,
                "uses_structured_branching": uses_structured_branching,
                "citations_preserved": citations_preserved,
                "payload": payload,
            }
        )
    return results


def run_frozen_examples(assembler: AnswerAssembler) -> list[dict[str, Any]]:
    frozen: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        payload = assembler.assemble(example["query_text"])
        frozen.append(
            {
                "example_id": example["example_id"],
                "query": example["query_text"],
                "expected_mode": example["expected_mode"],
                "answer_mode": payload["answer_mode"],
            }
        )
    return frozen


def assert_expectations(results: list[dict[str, Any]], frozen_results: list[dict[str, Any]]) -> None:
    for result in results:
        if result["answer_mode"] != result["expected_mode"]:
            raise AssertionError(f"{result['example_id']} mode regressed")
        if result["general_detected"] != result["expected_general_detected"]:
            raise AssertionError(f"{result['example_id']} general-question detection regressed")
        if result["general_detected"] and not result["uses_structured_branching"]:
            raise AssertionError(f"{result['example_id']} should use structured branching")
        if result["answer_mode"] != "refuse" and not result["citations_preserved"]:
            raise AssertionError(f"{result['example_id']} should preserve citations")
        if result["answer_mode"] == "weak_with_review_notice" and result["payload"]["primary_evidence"]:
            raise AssertionError(f"{result['example_id']} weak mode must not expose primary_evidence")

    for frozen in frozen_results:
        if frozen["answer_mode"] != frozen["expected_mode"]:
            raise AssertionError(f"{frozen['example_id']} frozen example regressed")


def build_examples_payload(results: list[dict[str, Any]], frozen_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
        "frozen_examples": frozen_results,
    }


def build_smoke_markdown(results: list[dict[str, Any]], frozen_results: list[dict[str, Any]]) -> str:
    frozen_ok = all(item["answer_mode"] == item["expected_mode"] for item in frozen_results)
    lines = [
        "# General Question Smoke Checks",
        "",
        "## 结论",
        "",
        f"- original_frozen_examples_preserved: `{frozen_ok}`",
        "",
    ]

    for result in results:
        payload = result["payload"]
        lines.extend(
            [
                f"## Query: {result['query']}",
                "",
                f"- answer_mode: `{result['answer_mode']}`",
                f"- 是否识别为总括类问题: `{result['general_detected']}`",
                f"- 是否采用分情况整理: `{result['uses_structured_branching']}`",
                f"- citations 是否保留: `{result['citations_preserved']}`",
                f"- 是否破坏原三条冻结样例: `{not frozen_ok}`",
                f"- primary_count: `{len(payload['primary_evidence'])}`",
                f"- secondary_count: `{len(payload['secondary_evidence'])}`",
                "",
                "### Answer Text",
                "",
                payload["answer_text"],
                "",
                "### Citation IDs",
                "",
                json_dumps([citation["record_id"] for citation in payload["citations"]]) if payload["citations"] else "_no rows_",
                "",
            ]
        )

    lines.extend(
        [
            "## Frozen Examples",
            "",
        ]
    )
    for item in frozen_results:
        lines.append(
            f"- `{item['query']}` -> expected=`{item['expected_mode']}`, actual=`{item['answer_mode']}`"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    db_path = (repo_root / args.db_path).resolve()
    policy_path = (repo_root / args.policy_json).resolve()
    cache_dir = (repo_root / args.cache_dir).resolve()
    dense_chunks_index = (repo_root / args.dense_chunks_index).resolve()
    dense_chunks_meta = (repo_root / args.dense_chunks_meta).resolve()
    dense_main_index = (repo_root / args.dense_main_index).resolve()
    dense_main_meta = (repo_root / args.dense_main_meta).resolve()
    examples_out = (repo_root / args.examples_out).resolve()
    smoke_out = (repo_root / args.smoke_checks_out).resolve()

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
        log(f"[2/4] Loaded answer assembler assets from {db_path}")
        results = run_examples(assembler)
        frozen_results = run_frozen_examples(assembler)
        assert_expectations(results, frozen_results)
        examples_out.write_text(json_dumps(build_examples_payload(results, frozen_results)) + "\n", encoding="utf-8")
        smoke_out.write_text(build_smoke_markdown(results, frozen_results), encoding="utf-8")
        log("[3/4] Ran general-question examples and verified frozen examples")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        assembler.close()


if __name__ == "__main__":
    raise SystemExit(main())
