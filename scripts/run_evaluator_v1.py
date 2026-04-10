#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.answers.assembler import (  # noqa: E402
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


DEFAULT_GOLDSET_PATH = "artifacts/evaluation/goldset_v1_seed.json"
DEFAULT_REPORT_JSON_PATH = "artifacts/evaluation/evaluator_v1_report.json"
DEFAULT_REPORT_MD_PATH = "artifacts/evaluation/evaluator_v1_report.md"
DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1/answers"
RUNNER_VERSION = "evaluator_runner_v1"
PASSAGE_ID_RE = re.compile(r"ZJSHL-CH-\d{3}-P-\d{4}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay goldset_v1_seed.json against the current formal answer chain.",
    )
    parser.add_argument("--goldset", default=DEFAULT_GOLDSET_PATH, help="Path to goldset_v1 seed JSON.")
    parser.add_argument("--report-json", default=DEFAULT_REPORT_JSON_PATH, help="Output evaluator JSON report path.")
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD_PATH, help="Output evaluator Markdown report path.")
    parser.add_argument(
        "--runner-backend",
        choices=("local_assembler", "api"),
        default="local_assembler",
        help="Replay through local AnswerAssembler by default, or an already-running formal API endpoint.",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="POST endpoint used when --runner-backend=api.")
    parser.add_argument(
        "--fail-on-evaluation-failure",
        action="store_true",
        help="Return a non-zero exit code when any evaluator check fails.",
    )
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH, help="Path to layered enablement policy JSON.")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def log(message: str) -> None:
    print(message, flush=True)


def command_line() -> str:
    return " ".join(shlex.quote(part) for part in [Path(sys.executable).name, *sys.argv])


def load_goldset(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "goldset_schema_v1":
        raise ValueError(f"Unsupported goldset schema_version: {data.get('schema_version')}")
    if not isinstance(data.get("items"), list) or not data["items"]:
        raise ValueError("Goldset must contain a non-empty items array.")
    return data


def passage_id_from_record_id(record_id: str | None) -> str | None:
    if not record_id:
        return None
    match = PASSAGE_ID_RE.search(record_id)
    return match.group(0) if match else None


def compact_whitespace(text: str | None, limit: int = 160) -> str:
    if not text:
        return ""
    compacted = " ".join(str(text).split())
    if len(compacted) <= limit:
        return compacted
    return compacted[:limit] + "..."


def record_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["record_id"] for row in rows if isinstance(row, dict) and row.get("record_id")]


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


class LocalAssemblerRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.assembler = AnswerAssembler(
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

    def answer(self, query: str) -> dict[str, Any]:
        return self.assembler.assemble(query)

    def close(self) -> None:
        self.assembler.close()


class ApiRunner:
    def __init__(self, api_url: str) -> None:
        self.api_url = api_url

    def answer(self, query: str) -> dict[str, Any]:
        body = json.dumps({"query": query}, ensure_ascii=False).encode("utf-8")
        request = urllib_request.Request(
            self.api_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            response_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API request failed with HTTP {exc.code}: {response_text}") from exc

    def close(self) -> None:
        return None


def build_runner(args: argparse.Namespace) -> LocalAssemblerRunner | ApiRunner:
    if args.runner_backend == "api":
        return ApiRunner(args.api_url)
    return LocalAssemblerRunner(args)


def evaluate_gold_citation(item: dict[str, Any], citations: list[dict[str, Any]]) -> dict[str, Any]:
    assertions = item.get("answer_assertions", {})
    required = bool(item.get("citation_check_required") or assertions.get("must_include_gold_citation"))
    gold_record_ids = set(item.get("gold_record_ids", []))
    gold_passage_ids = set(item.get("gold_passage_ids", []))
    matched: list[dict[str, Any]] = []

    for citation in citations:
        record_id = citation.get("record_id")
        passage_id = passage_id_from_record_id(record_id)
        matched_by: list[str] = []
        if record_id in gold_record_ids:
            matched_by.append("record_id")
        if passage_id in gold_passage_ids:
            matched_by.append("passage_id")
        if matched_by:
            matched.append(
                {
                    "citation_id": citation.get("citation_id"),
                    "record_id": record_id,
                    "passage_id": passage_id,
                    "matched_by": matched_by,
                    "citation_role": citation.get("citation_role"),
                }
            )

    return {
        "required": required,
        "passed": (not required) or bool(matched),
        "matched_count": len(matched),
        "matched_citations": matched,
    }


def build_condition_check(required: bool, observed_count: int, expected_zero: bool) -> dict[str, Any]:
    return {
        "required": required,
        "observed_count": observed_count,
        "passed": (not required) or ((observed_count == 0) if expected_zero else (observed_count > 0)),
    }


def evaluate_unsupported_assertion(
    item: dict[str, Any],
    payload: dict[str, Any],
    citation_check: dict[str, Any],
    evidence_count: int,
    citation_count: int,
    primary_count: int,
) -> dict[str, Any]:
    assertions = item.get("answer_assertions", {})
    required = bool(assertions.get("must_avoid_unsupported_assertion"))
    actual_mode = payload.get("answer_mode")
    expected_mode = item.get("expected_mode")
    reasons: list[str] = []

    if required:
        has_gold_evidence = bool(item.get("gold_record_ids") or item.get("gold_passage_ids"))
        if assertions.get("must_refuse") and actual_mode != "refuse":
            reasons.append("must_refuse_but_actual_mode_not_refuse")
        if expected_mode == "refuse" and actual_mode != "refuse":
            reasons.append("expected_refuse_but_actual_mode_not_refuse")
        if expected_mode == "weak_with_review_notice" and actual_mode == "strong":
            reasons.append("expected_weak_but_actual_mode_strong")
        if assertions.get("must_keep_primary_empty") and primary_count > 0:
            reasons.append("primary_evidence_should_be_empty")
        if assertions.get("must_have_zero_evidence") and evidence_count > 0:
            reasons.append("evidence_should_be_zero")
        if assertions.get("must_have_zero_citations") and citation_count > 0:
            reasons.append("citations_should_be_zero")
        if actual_mode == "strong":
            if not has_gold_evidence:
                reasons.append("strong_without_gold_evidence")
            if evidence_count == 0:
                reasons.append("strong_without_evidence")
            if primary_count == 0:
                reasons.append("strong_without_primary_evidence")
            if citation_count == 0:
                reasons.append("strong_without_citations")
            if citation_check["required"] and not citation_check["passed"]:
                reasons.append("strong_without_gold_citation")

    return {
        "required": required,
        "passed": not reasons,
        "rule_version": "minimal_v1",
        "failure_reasons": unique_preserve_order(reasons),
    }


def evaluate_item(item: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    assertions = item.get("answer_assertions", {})
    expected_mode = item["expected_mode"]
    actual_mode = payload.get("answer_mode")
    primary = payload.get("primary_evidence") or []
    secondary = payload.get("secondary_evidence") or []
    review = payload.get("review_materials") or []
    citations = payload.get("citations") or []
    evidence_count = len(primary) + len(secondary) + len(review)
    citation_count = len(citations)

    citation_check = evaluate_gold_citation(item, citations)
    primary_empty_check = build_condition_check(
        bool(assertions.get("must_keep_primary_empty")),
        len(primary),
        expected_zero=True,
    )
    zero_evidence_check = build_condition_check(
        bool(assertions.get("must_have_zero_evidence")),
        evidence_count,
        expected_zero=True,
    )
    zero_citations_check = build_condition_check(
        bool(assertions.get("must_have_zero_citations")),
        citation_count,
        expected_zero=True,
    )
    unsupported_assertion_check = evaluate_unsupported_assertion(
        item=item,
        payload=payload,
        citation_check=citation_check,
        evidence_count=evidence_count,
        citation_count=citation_count,
        primary_count=len(primary),
    )
    mode_match = actual_mode == expected_mode

    failed_checks: list[str] = []
    if assertions.get("mode_match_required", True) and not mode_match:
        failed_checks.append("mode_match")
    if not citation_check["passed"]:
        failed_checks.append("gold_citation_check")
    if not primary_empty_check["passed"]:
        failed_checks.append("primary_empty_check")
    if not zero_evidence_check["passed"]:
        failed_checks.append("zero_evidence_check")
    if not zero_citations_check["passed"]:
        failed_checks.append("zero_citations_check")
    if not unsupported_assertion_check["passed"]:
        failed_checks.append("unsupported_assertion_check")

    return {
        "question_id": item["question_id"],
        "query": item["query"],
        "question_type": item["question_type"],
        "question_type_label": item.get("question_type_label"),
        "expected_mode": expected_mode,
        "actual_mode": actual_mode,
        "mode_match": mode_match,
        "citation_check_required": bool(item.get("citation_check_required")),
        "citations_present": citation_count > 0,
        "primary_empty_check": primary_empty_check,
        "zero_evidence_check": zero_evidence_check,
        "zero_citations_check": zero_citations_check,
        "gold_citation_check": citation_check,
        "unsupported_assertion_check": unsupported_assertion_check,
        "actual_counts": {
            "primary_evidence": len(primary),
            "secondary_evidence": len(secondary),
            "review_materials": len(review),
            "total_evidence": evidence_count,
            "citations": citation_count,
        },
        "actual_record_ids": {
            "primary_evidence": record_ids(primary),
            "secondary_evidence": record_ids(secondary),
            "review_materials": record_ids(review),
            "citations": record_ids(citations),
        },
        "answer_text_excerpt": compact_whitespace(payload.get("answer_text")),
        "review_notice": payload.get("review_notice"),
        "refuse_reason": payload.get("refuse_reason"),
        "failed_checks": failed_checks,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts = Counter(result["question_type"] for result in results)
    expected_mode_counts = Counter(result["expected_mode"] for result in results)
    actual_mode_counts = Counter(result["actual_mode"] for result in results)
    mode_match_count = sum(1 for result in results if result["mode_match"])
    citation_required = [result for result in results if result["citation_check_required"]]
    citation_required_pass = [
        result for result in citation_required if result["gold_citation_check"]["passed"]
    ]

    by_type: dict[str, dict[str, Any]] = {}
    for question_type in sorted(type_counts):
        typed = [result for result in results if result["question_type"] == question_type]
        typed_citation_required = [result for result in typed if result["citation_check_required"]]
        by_type[question_type] = {
            "total": len(typed),
            "mode_match_count": sum(1 for result in typed if result["mode_match"]),
            "citation_check_required_count": len(typed_citation_required),
            "citation_basic_pass_count": sum(
                1 for result in typed_citation_required if result["gold_citation_check"]["passed"]
            ),
            "failure_count": sum(1 for result in typed if result["failed_checks"]),
        }

    failure_samples = [
        {
            "question_id": result["question_id"],
            "query": result["query"],
            "question_type": result["question_type"],
            "expected_mode": result["expected_mode"],
            "actual_mode": result["actual_mode"],
            "failed_checks": result["failed_checks"],
            "unsupported_assertion_failure_reasons": result["unsupported_assertion_check"]["failure_reasons"],
        }
        for result in results
        if result["failed_checks"]
    ]

    return {
        "total_questions": len(results),
        "mode_match_count": mode_match_count,
        "mode_match_rate": round(mode_match_count / len(results), 4) if results else 0.0,
        "type_counts": dict(sorted(type_counts.items())),
        "expected_mode_counts": dict(sorted(expected_mode_counts.items())),
        "actual_mode_counts": dict(sorted(actual_mode_counts.items())),
        "by_question_type": by_type,
        "citation_check_required": {
            "total": len(citation_required),
            "basic_pass_count": len(citation_required_pass),
            "basic_pass_rate": round(len(citation_required_pass) / len(citation_required), 4)
            if citation_required
            else 0.0,
            "failed_question_ids": [
                result["question_id"]
                for result in citation_required
                if not result["gold_citation_check"]["passed"]
            ],
        },
        "failure_count": len(failure_samples),
        "failure_samples": failure_samples,
        "all_checks_passed": not failure_samples,
    }


def build_report(
    goldset: dict[str, Any],
    results: list[dict[str, Any]],
    args: argparse.Namespace,
    started_at_utc: str,
    finished_at_utc: str,
) -> dict[str, Any]:
    return {
        "runner_version": RUNNER_VERSION,
        "generated_at_utc": finished_at_utc,
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "command": command_line(),
        "goldset": {
            "path": str(resolve_project_path(args.goldset)),
            "schema_version": goldset.get("schema_version"),
            "dataset_name": goldset.get("dataset_name"),
            "dataset_stage": goldset.get("dataset_stage"),
        },
        "runner_backend": {
            "name": args.runner_backend,
            "entrypoint": "backend.answers.assembler.AnswerAssembler"
            if args.runner_backend == "local_assembler"
            else args.api_url,
            "note": (
                "Default v1 path uses the local AnswerAssembler to run query -> hybrid retrieval -> "
                "evidence gating -> answer assembler without starting the HTTP transport adapter."
                if args.runner_backend == "local_assembler"
                else "API mode posts each query to the formal POST /api/v1/answers endpoint."
            ),
        },
        "summary": summarize_results(results),
        "items": results,
    }


def bool_mark(value: bool) -> str:
    return "PASS" if value else "FAIL"


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    backend = report["runner_backend"]
    lines = [
        "# Evaluator v1 Report",
        "",
        "## 运行信息",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- runner_version: `{report['runner_version']}`",
        f"- runner_backend: `{backend['name']}`",
        f"- entrypoint: `{backend['entrypoint']}`",
        f"- goldset: `{report['goldset']['path']}`",
        f"- command: `{report['command']}`",
        f"- replay_note: {backend['note']}",
        "",
        "## 汇总",
        "",
        f"- total_questions: `{summary['total_questions']}`",
        f"- mode_match_count: `{summary['mode_match_count']}/{summary['total_questions']}`",
        f"- mode_match_rate: `{summary['mode_match_rate']}`",
        f"- citation_check_required_basic_pass: `{summary['citation_check_required']['basic_pass_count']}/{summary['citation_check_required']['total']}`",
        f"- failure_count: `{summary['failure_count']}`",
        f"- all_checks_passed: `{summary['all_checks_passed']}`",
        f"- type_counts: `{json.dumps(summary['type_counts'], ensure_ascii=False)}`",
        f"- expected_mode_counts: `{json.dumps(summary['expected_mode_counts'], ensure_ascii=False)}`",
        f"- actual_mode_counts: `{json.dumps(summary['actual_mode_counts'], ensure_ascii=False)}`",
        "",
        "## 题型统计",
        "",
        "| question_type | total | mode_match | citation_required | citation_basic_pass | failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for question_type, stats in summary["by_question_type"].items():
        lines.append(
            f"| `{question_type}` | {stats['total']} | {stats['mode_match_count']} | "
            f"{stats['citation_check_required_count']} | {stats['citation_basic_pass_count']} | "
            f"{stats['failure_count']} |"
        )

    lines.extend(
        [
            "",
            "## 逐题结果",
            "",
            "| question_id | type | expected | actual | mode | citations | gold citation | primary empty | zero evidence | zero citations | unsupported |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )

    for result in report["items"]:
        lines.append(
            f"| `{result['question_id']}` | `{result['question_type']}` | `{result['expected_mode']}` | "
            f"`{result['actual_mode']}` | {bool_mark(result['mode_match'])} | "
            f"{result['actual_counts']['citations']} | "
            f"{bool_mark(result['gold_citation_check']['passed'])} | "
            f"{bool_mark(result['primary_empty_check']['passed'])} | "
            f"{bool_mark(result['zero_evidence_check']['passed'])} | "
            f"{bool_mark(result['zero_citations_check']['passed'])} | "
            f"{bool_mark(result['unsupported_assertion_check']['passed'])} |"
        )

    lines.extend(["", "## 失败样本", ""])
    if not summary["failure_samples"]:
        lines.append("_No failed samples._")
    else:
        for sample in summary["failure_samples"]:
            reasons = ", ".join(sample["failed_checks"])
            unsupported = ", ".join(sample["unsupported_assertion_failure_reasons"]) or "None"
            lines.extend(
                [
                    f"### {sample['question_id']}",
                    "",
                    f"- query: {sample['query']}",
                    f"- question_type: `{sample['question_type']}`",
                    f"- expected_mode: `{sample['expected_mode']}`",
                    f"- actual_mode: `{sample['actual_mode']}`",
                    f"- failed_checks: `{reasons}`",
                    f"- unsupported_assertion_failure_reasons: `{unsupported}`",
                    "",
                ]
            )

    lines.extend(["", "## Citation Required 明细", ""])
    for result in report["items"]:
        if not result["citation_check_required"]:
            continue
        matched_ids = [
            match["record_id"]
            for match in result["gold_citation_check"]["matched_citations"]
            if match.get("record_id")
        ]
        lines.append(
            f"- `{result['question_id']}`: {bool_mark(result['gold_citation_check']['passed'])}; "
            f"matched={json.dumps(matched_ids, ensure_ascii=False)}"
        )

    return "\n".join(lines) + "\n"


def run_evaluator(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    goldset_path = resolve_project_path(args.goldset)
    goldset = load_goldset(goldset_path)
    started_at_utc = datetime.now(timezone.utc).isoformat()
    runner = build_runner(args)
    results: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(goldset["items"], start=1):
            log(f"[evaluator:v1] replay {index}/{len(goldset['items'])}: {item['question_id']}")
            payload = runner.answer(item["query"])
            results.append(evaluate_item(item, payload))
    finally:
        runner.close()

    finished_at_utc = datetime.now(timezone.utc).isoformat()
    report = build_report(goldset, results, args, started_at_utc, finished_at_utc)
    return report, build_markdown(report)


def main() -> int:
    args = parse_args()
    report_json_path = resolve_project_path(args.report_json)
    report_md_path = resolve_project_path(args.report_md)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)

    report, markdown = run_evaluator(args)
    report_json_path.write_text(json_dumps(report) + "\n", encoding="utf-8")
    report_md_path.write_text(markdown, encoding="utf-8")
    log(f"[evaluator:v1] wrote {report_json_path}")
    log(f"[evaluator:v1] wrote {report_md_path}")

    if args.fail_on_evaluation_failure and not report["summary"]["all_checks_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
