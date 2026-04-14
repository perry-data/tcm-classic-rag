#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
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
)
from backend.api.minimal_api import EXPECTED_PAYLOAD_FIELDS, MinimalApiService
from backend.chat_history import DEFAULT_CONVERSATIONS_DB_PATH
from backend.llm import load_modelstudio_llm_config
from backend.retrieval.hybrid import json_dumps, log


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_OUT = "artifacts/generation_alignment_v1/generation_alignment_v1_report.md"
DEFAULT_EXAMPLES_OUT = "artifacts/generation_alignment_v1/generation_alignment_v1_examples.json"
EVIDENCE_REF_RE = re.compile(r"\[(E\d+)\]")
NUMBERED_LINE_RE = re.compile(r"^\s*\d+\.\s+")
PROPOSAL_ALIGNMENT_POINTS = [
    "开题要求生成式回答充分利用检索证据，并给出可核验的出处依据。",
    "开题要求通过 Prompt 约束与结果校验降低幻觉，避免杜撰出处。",
    "开题创新点明确提出“证据释义 / 要点抽取 -> 基于证据生成 -> 条文依据输出”的分步生成路径。",
]
ALIGNMENT_CASES = [
    {
        "case_id": "required_strong_huanglian_tang",
        "label": "required",
        "query_text": "黄连汤方的条文是什么？",
        "expected_mode": "strong",
    },
    {
        "case_id": "required_weak_shaozhen",
        "label": "required",
        "query_text": "烧针益阳而损阴是什么意思？",
        "expected_mode": "weak_with_review_notice",
    },
    {
        "case_id": "required_refuse_quantum",
        "label": "required",
        "query_text": "书中有没有提到量子纠缠？",
        "expected_mode": "refuse",
    },
    {
        "case_id": "explainer_taiyang_management",
        "label": "explainer",
        "query_text": "太阳病应该怎么办？",
        "expected_mode": "strong",
    },
    {
        "case_id": "explainer_huanglian_composition",
        "label": "explainer",
        "query_text": "黄连汤方由什么组成？",
        "expected_mode": "strong",
    },
    {
        "case_id": "explainer_guizhi_plus_fuzi_composition",
        "label": "explainer",
        "query_text": "桂枝加附子汤方由什么组成？",
        "expected_mode": "strong",
    },
]


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path_value).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate regression artifacts for generation alignment v1.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH, help="Path to layered enablement policy JSON.")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks metadata.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main metadata.")
    parser.add_argument(
        "--conversations-db-path",
        default=DEFAULT_CONVERSATIONS_DB_PATH,
        help="Path to the decoupled conversation history sqlite database.",
    )
    parser.add_argument("--report-out", default=DEFAULT_REPORT_OUT, help="Markdown report output path.")
    parser.add_argument("--examples-out", default=DEFAULT_EXAMPLES_OUT, help="JSON examples output path.")
    return parser.parse_args()


def _slot_record_ids(payload: dict[str, Any], slot_name: str) -> list[str]:
    return [str(item.get("record_id")) for item in payload.get(slot_name, [])]


def _citation_pairs(payload: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (str(item.get("record_id")), str(item.get("citation_role")))
        for item in payload.get("citations", [])
    ]


def _analyze_answer_text(answer_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in answer_text.splitlines() if line.strip()]
    point_lines = lines[1:] if len(lines) > 1 else []
    refs_by_line = [EVIDENCE_REF_RE.findall(line) for line in lines]
    return {
        "line_count": len(lines),
        "summary_line": lines[0] if lines else "",
        "point_count": len(point_lines),
        "point_lines": point_lines,
        "conclusion_has_refs": bool(refs_by_line and refs_by_line[0]),
        "all_lines_have_refs": bool(lines) and all(bool(refs) for refs in refs_by_line),
        "numbered_points_valid": all(NUMBERED_LINE_RE.match(line) for line in point_lines),
        "evidence_refs": sorted({ref for refs in refs_by_line for ref in refs}),
    }


def _build_service(args: argparse.Namespace, *, llm_enabled: bool) -> MinimalApiService:
    return MinimalApiService(
        db_path=resolve_project_path(args.db_path),
        policy_path=resolve_project_path(args.policy_json),
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=resolve_project_path(args.cache_dir),
        dense_chunks_index=resolve_project_path(args.dense_chunks_index),
        dense_chunks_meta=resolve_project_path(args.dense_chunks_meta),
        dense_main_index=resolve_project_path(args.dense_main_index),
        dense_main_meta=resolve_project_path(args.dense_main_meta),
        llm_config=load_modelstudio_llm_config(enabled_override=llm_enabled),
        conversations_db_path=resolve_project_path(args.conversations_db_path),
    )


def run_cases(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    baseline_service = _build_service(args, llm_enabled=False)
    llm_service = _build_service(args, llm_enabled=True)
    command = " ".join(
        shlex.quote(part)
        for part in [Path(sys.executable).name, "-m", "backend.checks.generation_alignment_v1_checks"]
    )
    try:
        llm_summary = llm_service.llm_config.public_summary()
        cases: list[dict[str, Any]] = []
        for case in ALIGNMENT_CASES:
            request_body = {"query": case["query_text"]}
            baseline_payload = baseline_service.answer(request_body)
            llm_payload = llm_service.answer(request_body)
            llm_debug = dict(llm_service.last_llm_debug or {})
            answer_analysis = _analyze_answer_text(llm_payload["answer_text"])
            case_result = {
                "case_id": case["case_id"],
                "label": case["label"],
                "query": case["query_text"],
                "expected_mode": case["expected_mode"],
                "baseline_response_body": baseline_payload,
                "llm_response_body": llm_payload,
                "llm_debug": llm_debug,
                "answer_text_analysis": answer_analysis,
                "checks": {
                    "payload_contract_kept": list(llm_payload.keys()) == EXPECTED_PAYLOAD_FIELDS,
                    "mode_kept": baseline_payload["answer_mode"] == llm_payload["answer_mode"] == case["expected_mode"],
                    "primary_unchanged": _slot_record_ids(baseline_payload, "primary_evidence")
                    == _slot_record_ids(llm_payload, "primary_evidence"),
                    "secondary_unchanged": _slot_record_ids(baseline_payload, "secondary_evidence")
                    == _slot_record_ids(llm_payload, "secondary_evidence"),
                    "review_unchanged": _slot_record_ids(baseline_payload, "review_materials")
                    == _slot_record_ids(llm_payload, "review_materials"),
                    "citations_unchanged": _citation_pairs(baseline_payload) == _citation_pairs(llm_payload),
                    "answer_text_changed": baseline_payload["answer_text"] != llm_payload["answer_text"],
                    "all_lines_have_refs": answer_analysis["all_lines_have_refs"],
                    "point_count_ok": 2 <= answer_analysis["point_count"] <= 4 if case["expected_mode"] != "refuse" else True,
                    "numbered_points_valid": answer_analysis["numbered_points_valid"] if case["expected_mode"] != "refuse" else True,
                    "llm_attempted_when_expected": (
                        llm_debug.get("attempted") if case["expected_mode"] != "refuse" else llm_debug.get("skipped_reason") == "refuse_mode"
                    ),
                },
            }
            cases.append(case_result)

        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "llm_config": llm_summary,
            "proposal_alignment_context": PROPOSAL_ALIGNMENT_POINTS,
            "cases": cases,
        }
        return payload, command
    finally:
        baseline_service.close()
        llm_service.close()


def build_report_markdown(command: str, payload: dict[str, Any]) -> str:
    cases = payload["cases"]
    llm_config = payload["llm_config"]
    lines = [
        "# Generation Alignment v1 Report",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 开题对齐口径",
        "",
        f"- 开题原件：`docs/proposal/221030147张前_开题报告.docx`",
    ]
    for point in PROPOSAL_ALIGNMENT_POINTS:
        lines.append(f"- {point}")

    lines.extend(
        [
            "",
            "## LLM Config",
            "",
            f"- provider: `{llm_config['provider']}`",
            f"- model: `{llm_config['model']}`",
            f"- base_url: `{llm_config['base_url']}`",
            f"- timeout_seconds: `{llm_config['timeout_seconds']}`",
            f"- max_output_tokens: `{llm_config['max_output_tokens']}`",
            "",
            "## 总结",
            "",
            f"- total_cases: `{len(cases)}`",
            f"- required_cases: `{sum(1 for case in cases if case['label'] == 'required')}`",
            f"- explainer_cases: `{sum(1 for case in cases if case['label'] == 'explainer')}`",
            f"- mode_kept_all: `{all(case['checks']['mode_kept'] for case in cases)}`",
            f"- evidence_slots_kept_all: `{all(case['checks']['primary_unchanged'] and case['checks']['secondary_unchanged'] and case['checks']['review_unchanged'] for case in cases)}`",
            f"- citations_kept_all: `{all(case['checks']['citations_unchanged'] for case in cases)}`",
            f"- llm_used_all_non_refuse: `{all(case['llm_debug'].get('used_llm') for case in cases if case['expected_mode'] != 'refuse')}`",
            f"- evidence_ref_alignment_all_non_refuse: `{all(case['checks']['all_lines_have_refs'] and case['checks']['point_count_ok'] and case['checks']['numbered_points_valid'] for case in cases if case['expected_mode'] != 'refuse')}`",
            f"- refuse_skips_llm: `{all(case['llm_debug'].get('skipped_reason') == 'refuse_mode' for case in cases if case['expected_mode'] == 'refuse')}`",
        ]
    )

    for case in cases:
        llm_payload = case["llm_response_body"]
        llm_debug = case["llm_debug"]
        analysis = case["answer_text_analysis"]
        checks = case["checks"]
        lines.extend(
            [
                "",
                f"## Case: {case['case_id']}",
                "",
                f"- label: `{case['label']}`",
                f"- query: `{case['query']}`",
                f"- expected_mode: `{case['expected_mode']}`",
                f"- actual_mode: `{llm_payload['answer_mode']}`",
                f"- answer_source: `{llm_debug.get('answer_source')}`",
                f"- attempted: `{llm_debug.get('attempted')}`",
                f"- used_llm: `{llm_debug.get('used_llm')}`",
                f"- fallback_used: `{llm_debug.get('fallback_used')}`",
                f"- payload_contract_kept: `{checks['payload_contract_kept']}`",
                f"- evidence_slots_kept: `{checks['primary_unchanged'] and checks['secondary_unchanged'] and checks['review_unchanged']}`",
                f"- citations_kept: `{checks['citations_unchanged']}`",
                f"- refs_on_all_lines: `{checks['all_lines_have_refs']}`",
                f"- point_count: `{analysis['point_count']}`",
                f"- numbered_points_valid: `{checks['numbered_points_valid']}`",
                f"- llm_attempted_when_expected: `{checks['llm_attempted_when_expected']}`",
                "",
                "### Answer Text",
                "",
                "```text",
                llm_payload["answer_text"],
                "```",
                "",
                "### LLM Debug",
                "",
                f"`{json_dumps(llm_debug)}`",
            ]
        )

    return "\n".join(lines) + "\n"


def assert_results(payload: dict[str, Any]) -> None:
    for case in payload["cases"]:
        checks = case["checks"]
        if not checks["payload_contract_kept"]:
            raise AssertionError(f"payload contract drift detected for {case['case_id']}")
        if not checks["mode_kept"]:
            raise AssertionError(f"mode drift detected for {case['case_id']}")
        if not checks["primary_unchanged"] or not checks["secondary_unchanged"] or not checks["review_unchanged"]:
            raise AssertionError(f"evidence slots changed for {case['case_id']}")
        if not checks["citations_unchanged"]:
            raise AssertionError(f"citations changed for {case['case_id']}")
        if case["expected_mode"] != "refuse":
            if not checks["all_lines_have_refs"]:
                raise AssertionError(f"answer_text lost evidence refs for {case['case_id']}")
            if not checks["point_count_ok"] or not checks["numbered_points_valid"]:
                raise AssertionError(f"answer_text structure regressed for {case['case_id']}")
            if not checks["llm_attempted_when_expected"]:
                raise AssertionError(f"LLM was not attempted for {case['case_id']}")
        else:
            if case["llm_debug"].get("skipped_reason") != "refuse_mode":
                raise AssertionError("refuse mode should skip LLM rendering")


def main() -> int:
    args = parse_args()
    report_out = resolve_project_path(args.report_out)
    examples_out = resolve_project_path(args.examples_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    examples_out.parent.mkdir(parents=True, exist_ok=True)

    log("[1/4] Loaded baseline + LLM services for generation alignment v1")
    payload, command = run_cases(args)
    log("[2/4] Ran required strong / weak / refuse and 3 explainer cases")
    assert_results(payload)
    examples_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_out.write_text(build_report_markdown(command, payload), encoding="utf-8")
    log(f"[3/4] Assertions passed for {len(payload['cases'])} cases")
    log(f"[4/4] Wrote {examples_out} and {report_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
