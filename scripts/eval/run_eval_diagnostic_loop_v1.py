#!/usr/bin/env python3
"""Run the eval diagnostic loop and write an aggregate summary.

This is an orchestration entrypoint only. It reruns the existing eval scripts,
captures each step's process result, then summarizes their artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "eval_diagnostic_loop_v1"

DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

EVAL_ROOT = REPO_ROOT / "artifacts" / "eval"
DATASET_OUT_DIR = EVAL_ROOT / "eval_dataset_v1"
RETRIEVAL_OUT_DIR = EVAL_ROOT / "retrieval_eval_v1"
ANSWER_OUT_DIR = EVAL_ROOT / "answer_eval_v1"
FAILURE_OUT_DIR = EVAL_ROOT / "failure_report_v1"
CITATION_AUDIT_OUT_DIR = EVAL_ROOT / "citation_topk_mismatch_audit_v1"
RECLASSIFIED_OUT_DIR = EVAL_ROOT / "failure_report_reclassified_after_citation_audit_v1"

DATASET_SUMMARY_JSON = DATASET_OUT_DIR / "eval_dataset_summary_v1.json"
RETRIEVAL_JSON = RETRIEVAL_OUT_DIR / "retrieval_eval_v1.json"
ANSWER_JSON = ANSWER_OUT_DIR / "answer_eval_v1.json"
TRACE_LOG = ANSWER_OUT_DIR / "qa_trace_answer_eval_v1.jsonl"
FAILURE_JSON = FAILURE_OUT_DIR / "failure_cases_v1.json"
CITATION_AUDIT_JSON = CITATION_AUDIT_OUT_DIR / "citation_topk_mismatch_audit_v1.json"
RECLASSIFIED_JSON = RECLASSIFIED_OUT_DIR / "failure_cases_reclassified_v1.json"
NEXT_QUEUE_JSON = RECLASSIFIED_OUT_DIR / "next_repair_queue_after_citation_audit_v1.json"

SUMMARY_JSON_NAME = "eval_diagnostic_loop_summary_v1.json"
SUMMARY_MD_NAME = "eval_diagnostic_loop_summary_v1.md"

RUN_MODE_ENV = {
    "B": {
        "run_mode": "B_retrieval_rerank_no_llm",
        "PERF_DISABLE_LLM": "1",
        "PERF_DISABLE_RERANK": "0",
        "PERF_RETRIEVAL_MODE": "hybrid",
    },
}

DATASET_FIELDS = [
    "total_examples",
    "category_counts",
    "dataset_valid",
]
RETRIEVAL_FIELDS = [
    "answerable_metric_examples",
    "diagnostic_only_examples",
    "unanswerable_examples",
    "hit_at_1",
    "hit_at_3",
    "hit_at_5",
    "mrr",
    "recall_at_5",
]
ANSWER_FIELDS = [
    "has_citation_rate",
    "citation_from_top_k_rate",
    "gold_cited_rate",
    "refuse_when_should_not_answer_rate",
    "scope_qualified_rate",
    "answer_keyword_hit_rate",
    "expected_answer_mode_match_rate",
]
FAILURE_FIELDS = [
    "formal_fail_count",
    "warning_count",
    "diagnostic_count",
    "ok_count",
    "failure_type_counts",
]
CITATION_AUDIT_FIELDS = [
    "total_citation_not_from_topk",
    "runtime_bug_count",
    "evaluator_or_trace_issue_count",
    "manual_audit_required_count",
    "root_cause_counts",
]
RECLASSIFIED_FIELDS = [
    "original_formal_fail_count",
    "reclassified_formal_fail_count",
    "runtime_bug_count",
    "tooling_count",
    "policy_warning_count",
    "diagnostic_count",
    "ok_count",
]
NEXT_QUEUE_FIELDS = [
    "runtime_citation_scope_repairs",
    "trace_or_evaluator_repairs",
    "secondary_review_policy_decisions",
    "retrieval_or_chunking_repairs",
    "p2_manual_audit",
]


@dataclass(frozen=True)
class StepSpec:
    name: str
    command: list[str]


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def excerpt_text(value: str, *, max_lines: int = 40, max_chars: int = 4000) -> str:
    text = value.strip()
    if not text:
        return ""
    lines = text.splitlines()
    omitted = max(0, len(lines) - max_lines)
    selected = lines[-max_lines:]
    if omitted:
        selected.insert(0, f"[omitted {omitted} earlier lines]")
    excerpt = "\n".join(selected)
    if len(excerpt) > max_chars:
        excerpt = "[truncated]\n" + excerpt[-max_chars:]
    return excerpt


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(item) for item in command)


def mode_config(run_mode: str) -> dict[str, str]:
    mode = run_mode.upper()
    if mode not in RUN_MODE_ENV:
        raise ValueError(f"unsupported run mode: {run_mode}")
    return RUN_MODE_ENV[mode]


def run_env(run_mode: str) -> dict[str, str]:
    config = mode_config(run_mode)
    env = os.environ.copy()
    for key, value in config.items():
        if key.startswith("PERF_"):
            env[key] = value
    env["PYTHONUNBUFFERED"] = "1"
    return env


def build_steps(dataset_path: Path, run_mode: str) -> list[StepSpec]:
    python = sys.executable
    dataset_arg = display_path(dataset_path)
    return [
        StepSpec(
            "validate_eval_dataset_v1",
            [
                python,
                "scripts/eval/validate_eval_dataset_v1.py",
                "--dataset",
                dataset_arg,
                "--out-dir",
                display_path(DATASET_OUT_DIR),
            ],
        ),
        StepSpec(
            "retrieval_eval_v1",
            [
                python,
                "scripts/eval/retrieval_eval_v1.py",
                "--dataset",
                dataset_arg,
                "--out-dir",
                display_path(RETRIEVAL_OUT_DIR),
                "--run-mode",
                run_mode,
            ],
        ),
        StepSpec(
            "answer_eval_v1",
            [
                python,
                "scripts/eval/answer_eval_v1.py",
                "--dataset",
                dataset_arg,
                "--retrieval-json",
                display_path(RETRIEVAL_JSON),
                "--out-dir",
                display_path(ANSWER_OUT_DIR),
                "--run-mode",
                run_mode,
            ],
        ),
        StepSpec(
            "failure_report_v1",
            [
                python,
                "scripts/eval/build_failure_report_v1.py",
                "--dataset",
                dataset_arg,
                "--retrieval-json",
                display_path(RETRIEVAL_JSON),
                "--answer-json",
                display_path(ANSWER_JSON),
                "--trace-log",
                display_path(TRACE_LOG),
                "--out-dir",
                display_path(FAILURE_OUT_DIR),
            ],
        ),
        StepSpec(
            "citation_topk_mismatch_audit_v1",
            [
                python,
                "scripts/eval/audit_citation_topk_mismatch_v1.py",
                "--dataset",
                dataset_arg,
                "--retrieval-json",
                display_path(RETRIEVAL_JSON),
                "--answer-json",
                display_path(ANSWER_JSON),
                "--trace-log",
                display_path(TRACE_LOG),
                "--failure-json",
                display_path(FAILURE_JSON),
                "--out-dir",
                display_path(CITATION_AUDIT_OUT_DIR),
            ],
        ),
        StepSpec(
            "failure_report_reclassified_after_citation_audit_v1",
            [
                python,
                "scripts/eval/reclassify_failure_report_after_citation_audit_v1.py",
                "--dataset",
                dataset_arg,
                "--retrieval-json",
                display_path(RETRIEVAL_JSON),
                "--answer-json",
                display_path(ANSWER_JSON),
                "--failure-json",
                display_path(FAILURE_JSON),
                "--citation-audit-json",
                display_path(CITATION_AUDIT_JSON),
                "--out-dir",
                display_path(RECLASSIFIED_OUT_DIR),
            ],
        ),
    ]


def run_step(step: StepSpec, *, env: dict[str, str]) -> dict[str, Any]:
    print(f"[{RUN_ID}] running {step.name}", flush=True)
    completed = subprocess.run(
        step.command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    status = "pass" if completed.returncode == 0 else "fail"
    print(f"[{RUN_ID}] {step.name}: {status} ({completed.returncode})", flush=True)
    return {
        "name": step.name,
        "command": shell_join(step.command),
        "returncode": completed.returncode,
        "status": status,
        "stdout_excerpt": excerpt_text(completed.stdout),
        "stderr_excerpt": excerpt_text(completed.stderr),
        "stdout_line_count": len(completed.stdout.splitlines()),
        "stderr_line_count": len(completed.stderr.splitlines()),
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def pick_fields(payload: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: payload.get(field) for field in fields}


def source_artifacts() -> dict[str, str]:
    return {
        "eval_dataset_v1": display_path(DATASET_SUMMARY_JSON),
        "retrieval_eval_v1": display_path(RETRIEVAL_JSON),
        "answer_eval_v1": display_path(ANSWER_JSON),
        "qa_trace_answer_eval_v1": display_path(TRACE_LOG),
        "failure_report_v1": display_path(FAILURE_JSON),
        "citation_topk_mismatch_audit_v1": display_path(CITATION_AUDIT_JSON),
        "failure_report_reclassified_after_citation_audit_v1": display_path(RECLASSIFIED_JSON),
        "next_repair_queue_after_citation_audit_v1": display_path(NEXT_QUEUE_JSON),
    }


def build_summary(*, dataset_path: Path, run_mode: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    config = mode_config(run_mode)
    dataset_payload = load_json(DATASET_SUMMARY_JSON)
    retrieval_payload = load_json(RETRIEVAL_JSON)
    answer_payload = load_json(ANSWER_JSON)
    failure_payload = load_json(FAILURE_JSON)
    citation_payload = load_json(CITATION_AUDIT_JSON)
    reclassified_payload = load_json(RECLASSIFIED_JSON)
    next_queue_payload = load_json(NEXT_QUEUE_JSON)

    answer_summary = pick_fields(answer_payload, ANSWER_FIELDS)
    answer_summary["llm_used"] = answer_payload.get("llm_used")
    answer_summary["judge"] = answer_payload.get("judge")
    answer_summary["env_flags"] = answer_payload.get("env_flags")

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": display_path(dataset_path),
        "run_mode": config["run_mode"],
        "env_flags": {
            key: value for key, value in config.items() if key.startswith("PERF_")
        },
        "no_llm": config["PERF_DISABLE_LLM"] == "1",
        "judge": {"type": "rules_only_orchestration", "llm_judge": False},
        "steps": steps,
        "all_steps_passed": all(step["returncode"] == 0 for step in steps)
        and len(steps) == len(build_steps(dataset_path, run_mode)),
        "source_artifacts": source_artifacts(),
        "dataset": pick_fields(dataset_payload, DATASET_FIELDS),
        "retrieval": pick_fields(retrieval_payload, RETRIEVAL_FIELDS),
        "answer": answer_summary,
        "failure_report": pick_fields(failure_payload, FAILURE_FIELDS),
        "citation_audit": pick_fields(citation_payload, CITATION_AUDIT_FIELDS),
        "reclassified": pick_fields(reclassified_payload, RECLASSIFIED_FIELDS),
        "next_repair_queue": {
            field: next_queue_payload.get(field, []) for field in NEXT_QUEUE_FIELDS
        },
    }


def md_escape(value: Any) -> str:
    text = " ".join(str(value if value is not None else "").split())
    return text.replace("|", "\\|")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(item) for item in row) + " |")
    return "\n".join(lines)


def count_table(counter: dict[str, Any] | None) -> str:
    if not counter:
        return "_None._"
    return md_table(["key", "count"], [[key, value] for key, value in sorted(counter.items())])


def metric_table(metrics: dict[str, Any], fields: list[str]) -> str:
    return md_table(["metric", "value"], [[field, metrics.get(field)] for field in fields])


def queue_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("id") or "") for row in rows if row.get("id")]


def render_markdown(summary: dict[str, Any]) -> str:
    dataset = summary["dataset"]
    retrieval = summary["retrieval"]
    answer = summary["answer"]
    failure = summary["failure_report"]
    citation = summary["citation_audit"]
    reclassified = summary["reclassified"]
    queue = summary["next_repair_queue"]

    step_rows = [
        [
            step["name"],
            step["status"],
            step["returncode"],
            step["stdout_excerpt"],
            step["stderr_excerpt"],
        ]
        for step in summary["steps"]
    ]
    queue_rows = [
        [
            "runtime_citation_scope_repairs",
            len(queue["runtime_citation_scope_repairs"]),
            ", ".join(queue_ids(queue["runtime_citation_scope_repairs"])),
        ],
        [
            "trace_or_evaluator_repairs",
            len(queue["trace_or_evaluator_repairs"]),
            ", ".join(queue_ids(queue["trace_or_evaluator_repairs"])),
        ],
        [
            "secondary_review_policy_decisions",
            len(queue["secondary_review_policy_decisions"]),
            ", ".join(queue_ids(queue["secondary_review_policy_decisions"])),
        ],
        [
            "retrieval_or_chunking_repairs",
            len(queue["retrieval_or_chunking_repairs"]),
            ", ".join(queue_ids(queue["retrieval_or_chunking_repairs"])),
        ],
        [
            "p2_manual_audit",
            len(queue["p2_manual_audit"]),
            ", ".join(queue_ids(queue["p2_manual_audit"])),
        ],
    ]

    return "\n\n".join(
        [
            "# eval_diagnostic_loop_summary_v1",
            "## 本轮目标\n"
            "这是诊断闭环总览；这不是系统全通过。"
            "本轮只一键复跑既有诊断链路并汇总产物，不修系统、不改规则、不隐藏失败。",
            "## 运行配置\n"
            + md_table(
                ["field", "value"],
                [
                    ["dataset_path", summary["dataset_path"]],
                    ["run_mode", summary["run_mode"]],
                    ["PERF_DISABLE_LLM", summary["env_flags"].get("PERF_DISABLE_LLM")],
                    ["PERF_DISABLE_RERANK", summary["env_flags"].get("PERF_DISABLE_RERANK")],
                    ["PERF_RETRIEVAL_MODE", summary["env_flags"].get("PERF_RETRIEVAL_MODE")],
                    ["all_steps_passed", summary["all_steps_passed"]],
                    ["llm_judge", summary["judge"]["llm_judge"]],
                ],
            ),
            "## 各步骤运行状态\n"
            + md_table(
                ["step", "status", "returncode", "stdout excerpt", "stderr excerpt"],
                step_rows,
            ),
            "## dataset 概况\n"
            + metric_table(dataset, DATASET_FIELDS)
            + "\n\n### category_counts\n"
            + count_table(dataset.get("category_counts") or {}),
            "## retrieval 指标\n" + metric_table(retrieval, RETRIEVAL_FIELDS),
            "## answer 指标\n"
            + metric_table(answer, [*ANSWER_FIELDS, "llm_used"])
            + "\n\nanswer_eval_v1 使用 rules-only 评估；summary 记录 no_llm=true，且 answer.llm_used=false。",
            "## failure_report 原始归因\n"
            + metric_table(failure, FAILURE_FIELDS[:-1])
            + "\n\n### failure_type_counts\n"
            + count_table(failure.get("failure_type_counts") or {}),
            "## citation audit 结论\n"
            + metric_table(citation, CITATION_AUDIT_FIELDS[:-1])
            + "\n\n### root_cause_counts\n"
            + count_table(citation.get("root_cause_counts") or {}),
            "## reclassified 归因\n" + metric_table(reclassified, RECLASSIFIED_FIELDS),
            "## next repair queue\n"
            + md_table(["queue", "count", "ids"], queue_rows),
            "## 下一步建议\n"
            f"- reclassified formal fail 仍为 {reclassified.get('reclassified_formal_fail_count')}。\n"
            f"- {reclassified.get('runtime_bug_count')} 条是真 runtime citation bug："
            + ", ".join(queue_ids(queue["runtime_citation_scope_repairs"]))
            + "。\n"
            f"- {reclassified.get('tooling_count')} 条是 trace/evaluator 工具问题："
            + ", ".join(queue_ids(queue["trace_or_evaluator_repairs"]))
            + "。\n"
            f"- {reclassified.get('policy_warning_count')} 条是 secondary/review citation policy decision："
            + ", ".join(queue_ids(queue["secondary_review_policy_decisions"]))
            + "。\n"
            f"- {reclassified.get('diagnostic_count')} 条 P2 仍是 diagnostic："
            + ", ".join(queue_ids(queue["p2_manual_audit"]))
            + "。\n"
            "- 下一轮若进入修复，应先按 queue 分流；policy warning 先定政策，不作为 runtime bug 直接修。",
        ]
    ) + "\n"


def write_summary(summary: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / SUMMARY_JSON_NAME
    md_path = out_dir / SUMMARY_MD_NAME
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    return json_path, md_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-mode", default="B", choices=sorted(RUN_MODE_ENV))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dataset_path = resolve_project_path(args.dataset)
    out_dir = resolve_project_path(args.out_dir)
    env = run_env(args.run_mode)

    steps: list[dict[str, Any]] = []
    for step in build_steps(dataset_path, args.run_mode):
        result = run_step(step, env=env)
        steps.append(result)
        if result["returncode"] != 0:
            break

    summary = build_summary(dataset_path=dataset_path, run_mode=args.run_mode, steps=steps)
    json_path, md_path = write_summary(summary, out_dir)
    print(f"[{RUN_ID}] wrote {display_path(json_path)}", flush=True)
    print(f"[{RUN_ID}] wrote {display_path(md_path)}", flush=True)
    return 0 if summary["all_steps_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
