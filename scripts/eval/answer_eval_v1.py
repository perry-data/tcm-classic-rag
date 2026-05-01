#!/usr/bin/env python3
"""Run rules-only answer evaluation for eval_dataset_v1.

This evaluator runs the current AnswerAssembler once for each dataset row,
with retrieval + rerank enabled and LLM generation disabled. It then scores the
resulting trace records with deterministic rules only. It does not call an LLM
judge and does not change retrieval, prompt, dataset, or runtime evidence rules.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
from backend.diagnostics.qa_trace import ENV_QA_TRACE_DIR, ENV_QA_TRACE_ENABLED  # noqa: E402
from scripts.eval.retrieval_eval_v1 import (  # noqa: E402
    IdEquivalenceIndex,
    add_id_variants,
    display_path,
    resolve_project_path,
)


RUN_ID = "answer_eval_v1"
DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_RETRIEVAL_JSON = REPO_ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID
TRACE_FILENAME = "qa_trace_answer_eval_v1.jsonl"

RUN_MODE_ENV = {
    "B": {
        "run_mode": "B_retrieval_rerank_no_llm",
        "PERF_DISABLE_LLM": "1",
        "PERF_DISABLE_RERANK": "0",
        "PERF_RETRIEVAL_MODE": "hybrid",
    },
}

SCOPE_QUALIFIERS = (
    "根据《注解伤寒论》",
    "据《注解伤寒论》",
    "从《注解伤寒论》",
    "《注解伤寒论》",
    "本书",
    "书中",
    "原文",
    "条文",
)

REFUSAL_HINTS = (
    "范围外",
    "超出",
    "不能回答",
    "不能根据《注解伤寒论》回答",
    "无法根据《注解伤寒论》回答",
    "不属于《注解伤寒论》",
    "不属于本书",
    "没有检索到足以支撑回答",
    "先不硬答",
    "不输出推测性答案",
)


@dataclass(frozen=True)
class EvalExample:
    id: str
    category: str
    question: str
    gold_chunk_ids: list[str]
    gold_answer_keywords: list[str]
    should_answer: bool
    expected_answer_mode: str
    manual_audit_required: bool
    notes: str
    subtype: str


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def split_pipe(value: str | None) -> list[str]:
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_dataset(dataset_path: Path) -> list[EvalExample]:
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[EvalExample] = []
        for row in reader:
            rows.append(
                EvalExample(
                    id=(row.get("id") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    question=(row.get("question") or "").strip(),
                    gold_chunk_ids=split_pipe(row.get("gold_chunk_ids")),
                    gold_answer_keywords=split_pipe(row.get("gold_answer_keywords")),
                    should_answer=parse_bool(row.get("should_answer")),
                    expected_answer_mode=(row.get("expected_answer_mode") or "").strip(),
                    manual_audit_required=parse_bool(row.get("manual_audit_required")),
                    notes=(row.get("notes") or "").strip(),
                    subtype=(row.get("subtype") or "").strip(),
                )
            )
    return rows


def classify_example(example: EvalExample) -> str:
    if example.manual_audit_required:
        return "diagnostic_only"
    if not example.should_answer:
        return "unanswerable"
    if example.gold_chunk_ids:
        return "answerable_metric"
    return "diagnostic_only"


def apply_run_mode(run_mode: str) -> dict[str, str]:
    mode = run_mode.upper()
    if mode not in RUN_MODE_ENV:
        raise ValueError(f"unsupported run mode: {run_mode}")
    config = RUN_MODE_ENV[mode]
    for key, value in config.items():
        if key.startswith("PERF_"):
            os.environ[key] = value
    return config


def restore_env(snapshot: dict[str, str | None]) -> None:
    for key, value in snapshot.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def compact_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def excerpt(value: Any, *, limit: int = 180) -> str:
    text = compact_text(value)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def prepare_trace_paths(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / TRACE_FILENAME
    if trace_path.exists():
        trace_path.unlink()
    trace_tmp_dir = out_dir / "_trace_tmp"
    if trace_tmp_dir.exists():
        shutil.rmtree(trace_tmp_dir)
    trace_tmp_dir.mkdir(parents=True, exist_ok=True)
    return trace_path, trace_tmp_dir


def read_tmp_trace_records(trace_tmp_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(trace_tmp_dir.glob("qa_trace_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def order_trace_records(
    examples: list[EvalExample],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records_by_query: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for record in records:
        records_by_query[str(record.get("query") or "")].append(record)

    ordered: list[dict[str, Any]] = []
    missing: list[str] = []
    for example in examples:
        queue = records_by_query.get(example.question)
        if not queue:
            missing.append(f"{example.id}:{example.question}")
            continue
        ordered.append(queue.popleft())
    if missing:
        raise RuntimeError("missing qa trace rows for examples: " + "; ".join(missing))
    return ordered


def write_canonical_trace(trace_path: Path, records: list[dict[str, Any]]) -> None:
    with trace_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def add_trace_item_ids(ids: set[str], item: dict[str, Any]) -> None:
    for key in ("chunk_id", "record_id"):
        value = item.get(key)
        if value:
            add_id_variants(ids, str(value))


def equivalent_ids(values: Iterable[str], equivalence: IdEquivalenceIndex) -> set[str]:
    base: set[str] = set()
    for value in values:
        add_id_variants(base, value)
    return equivalence.equivalents_for_values(base)


def trace_top5_matchable_ids(record: dict[str, Any], equivalence: IdEquivalenceIndex) -> list[list[str]]:
    result: list[list[str]] = []
    for item in (record.get("top_k_chunks") or [])[:5]:
        ids: set[str] = set()
        if isinstance(item, dict):
            add_trace_item_ids(ids, item)
        result.append(sorted(equivalent_ids(ids, equivalence)))
    return result


def trace_top5_id_union(record: dict[str, Any], equivalence: IdEquivalenceIndex) -> set[str]:
    ids: set[str] = set()
    for item in (record.get("top_k_chunks") or [])[:5]:
        if isinstance(item, dict):
            add_trace_item_ids(ids, item)
    return equivalent_ids(ids, equivalence)


def trace_evidence_id_union(record: dict[str, Any], equivalence: IdEquivalenceIndex) -> set[str]:
    values: list[str] = []
    for key in ("primary_evidence_ids", "secondary_evidence_ids", "review_material_ids"):
        values.extend(str(item) for item in (record.get(key) or []) if item)
    for citation in record.get("citations") or []:
        if isinstance(citation, dict):
            value = citation.get("chunk_id") or citation.get("record_id")
            if value:
                values.append(str(value))
    return equivalent_ids(values, equivalence)


def citation_ids_from_trace(record: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for citation in record.get("citations") or []:
        if not isinstance(citation, dict):
            continue
        value = citation.get("chunk_id") or citation.get("record_id")
        if value:
            ids.append(str(value))
    return ids


def citation_source_slots(record: dict[str, Any]) -> list[str]:
    slots: list[str] = []
    for citation in record.get("citations") or []:
        if isinstance(citation, dict):
            slots.append(str(citation.get("source_slot") or "unknown"))
    return slots


def citation_ids_visible_in_trace(
    citation_ids: list[str],
    record: dict[str, Any],
    equivalence: IdEquivalenceIndex,
) -> bool:
    if not citation_ids:
        return False
    visible_ids = trace_evidence_id_union(record, equivalence)
    return all(equivalent_ids([citation_id], equivalence) & visible_ids for citation_id in citation_ids)


def citations_from_top_k(
    citation_ids: list[str],
    record: dict[str, Any],
    equivalence: IdEquivalenceIndex,
) -> bool:
    if not citation_ids:
        return False
    top5_ids = trace_top5_id_union(record, equivalence)
    return all(equivalent_ids([citation_id], equivalence) & top5_ids for citation_id in citation_ids)


def any_gold_cited(
    citation_ids: list[str],
    gold_chunk_ids: list[str],
    equivalence: IdEquivalenceIndex,
) -> bool:
    if not citation_ids or not gold_chunk_ids:
        return False
    citation_equiv = equivalent_ids(citation_ids, equivalence)
    for gold_id in gold_chunk_ids:
        if equivalent_ids([gold_id], equivalence) & citation_equiv:
            return True
    return False


def answer_has_scope_qualifier(final_answer: str) -> bool:
    return any(keyword in final_answer for keyword in SCOPE_QUALIFIERS)


def answer_refuses(final_answer: str, answer_mode: str) -> bool:
    if answer_mode == "refuse":
        return True
    return any(keyword in final_answer for keyword in REFUSAL_HINTS)


def keyword_hit(final_answer: str, keywords: list[str]) -> bool | None:
    if not keywords:
        return None
    return any(keyword and keyword in final_answer for keyword in keywords)


def score_example(
    example: EvalExample,
    record: dict[str, Any],
    equivalence: IdEquivalenceIndex,
) -> dict[str, Any]:
    example_class = classify_example(example)
    included_in_answer_metrics = example_class == "answerable_metric"
    diagnostic_only = example_class == "diagnostic_only"
    actual_answer_mode = str(record.get("answer_mode") or "unknown")
    final_answer = str(record.get("final_answer") or "")
    citation_ids = citation_ids_from_trace(record)
    citation_slots = citation_source_slots(record)
    notes: list[str] = []

    has_citation: bool | None = None
    citation_from_top_k: bool | None = None
    gold_cited: bool | None = None
    refuse_when_should_not_answer: bool | None = None
    scope_qualified: bool | None = None
    answer_keyword_hit: bool | None = None
    expected_answer_mode_match: bool | None = None

    if example.should_answer:
        if actual_answer_mode == "refuse":
            has_citation = False
            citation_from_top_k = False
            if included_in_answer_metrics:
                gold_cited = False
            notes.append("answer_mode=refuse for should_answer=true")
        else:
            has_citation = bool(citation_ids) and citation_ids_visible_in_trace(
                citation_ids,
                record,
                equivalence,
            )
            citation_from_top_k = citations_from_top_k(citation_ids, record, equivalence)
            if citation_ids and not has_citation:
                notes.append("citation id not visible in trace evidence slots")
            if citation_ids and not citation_from_top_k:
                notes.append("at least one citation was not found in trace top_k_chunks")
            if included_in_answer_metrics:
                gold_cited = any_gold_cited(citation_ids, example.gold_chunk_ids, equivalence)
                if not gold_cited:
                    notes.append("no citation matched gold_chunk_ids under evaluator equivalence")
        if included_in_answer_metrics:
            answer_keyword_hit = keyword_hit(final_answer, example.gold_answer_keywords)
    else:
        refuse_when_should_not_answer = answer_refuses(final_answer, actual_answer_mode)

    if not diagnostic_only:
        scope_qualified = answer_has_scope_qualifier(final_answer)
        if example.expected_answer_mode:
            expected_answer_mode_match = actual_answer_mode == example.expected_answer_mode
    else:
        if example.expected_answer_mode:
            expected_answer_mode_match = actual_answer_mode == example.expected_answer_mode

    return {
        "id": example.id,
        "category": example.category,
        "question": example.question,
        "should_answer": example.should_answer,
        "manual_audit_required": example.manual_audit_required,
        "included_in_answer_metrics": included_in_answer_metrics,
        "diagnostic_only": diagnostic_only,
        "example_class": example_class,
        "expected_answer_mode": example.expected_answer_mode,
        "actual_answer_mode": actual_answer_mode,
        "gold_chunk_ids": example.gold_chunk_ids,
        "gold_answer_keywords": example.gold_answer_keywords,
        "top5_record_ids": [
            str(item.get("record_id") or "") for item in (record.get("top_k_chunks") or [])[:5] if isinstance(item, dict)
        ],
        "top5_chunk_ids": [
            str(item.get("chunk_id") or "") for item in (record.get("top_k_chunks") or [])[:5] if isinstance(item, dict)
        ],
        "top5_matchable_ids": trace_top5_matchable_ids(record, equivalence),
        "citation_ids": citation_ids,
        "citation_source_slots": citation_slots,
        "has_citation": has_citation,
        "citation_from_top_k": citation_from_top_k,
        "gold_cited": gold_cited,
        "refuse_when_should_not_answer": refuse_when_should_not_answer,
        "scope_qualified": scope_qualified,
        "answer_keyword_hit": answer_keyword_hit,
        "expected_answer_mode_match": expected_answer_mode_match,
        "final_answer_excerpt": excerpt(final_answer),
        "notes": "; ".join(notes),
        "subtype": example.subtype,
        "dataset_notes": example.notes,
    }


def rate(rows: list[dict[str, Any]], field: str) -> float:
    values = [row[field] for row in rows if row.get(field) is not None]
    if not values:
        return 0.0
    return round(sum(1 for value in values if value is True) / len(values), 6)


def metric_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int | float]:
    values = [row[field] for row in rows if row.get(field) is not None]
    passed = sum(1 for value in values if value is True)
    denominator = len(values)
    return {
        "passed": passed,
        "denominator": denominator,
        "rate": round(passed / denominator, 6) if denominator else 0.0,
    }


def aggregate_payload(
    *,
    dataset_path: Path,
    retrieval_json: Path,
    trace_path: Path,
    run_mode_config: dict[str, str],
    per_example: list[dict[str, Any]],
    trace_records: list[dict[str, Any]],
) -> dict[str, Any]:
    class_counts = Counter(row["example_class"] for row in per_example)
    answer_metric_rows = [row for row in per_example if row["included_in_answer_metrics"]]
    diagnostic_rows = [row for row in per_example if row["diagnostic_only"]]
    unanswerable_rows = [row for row in per_example if row["example_class"] == "unanswerable"]
    non_diagnostic_rows = [row for row in per_example if not row["diagnostic_only"]]
    keyword_rows = [row for row in answer_metric_rows if row["answer_keyword_hit"] is not None]
    expected_mode_rows = [
        row for row in non_diagnostic_rows if row.get("expected_answer_mode") and row["expected_answer_mode_match"] is not None
    ]

    per_category: dict[str, dict[str, Any]] = {}
    for category in sorted({row["category"] for row in per_example}):
        category_rows = [row for row in per_example if row["category"] == category]
        category_answer_rows = [row for row in category_rows if row["included_in_answer_metrics"]]
        category_unanswerable_rows = [row for row in category_rows if row["example_class"] == "unanswerable"]
        category_non_diagnostic_rows = [row for row in category_rows if not row["diagnostic_only"]]
        category_keyword_rows = [row for row in category_answer_rows if row["answer_keyword_hit"] is not None]
        category_expected_rows = [
            row
            for row in category_non_diagnostic_rows
            if row.get("expected_answer_mode") and row["expected_answer_mode_match"] is not None
        ]
        per_category[category] = {
            "examples": len(category_rows),
            "answerable_metric_examples": len(category_answer_rows),
            "diagnostic_only_examples": sum(1 for row in category_rows if row["diagnostic_only"]),
            "unanswerable_examples": len(category_unanswerable_rows),
            "has_citation_rate": rate(category_answer_rows, "has_citation"),
            "citation_from_top_k_rate": rate(category_answer_rows, "citation_from_top_k"),
            "gold_cited_rate": rate(category_answer_rows, "gold_cited"),
            "refuse_when_should_not_answer_rate": rate(category_unanswerable_rows, "refuse_when_should_not_answer"),
            "scope_qualified_rate": rate(category_non_diagnostic_rows, "scope_qualified"),
            "answer_keyword_hit_rate": rate(category_keyword_rows, "answer_keyword_hit"),
            "expected_answer_mode_match_rate": rate(category_expected_rows, "expected_answer_mode_match"),
        }

    metric_denominators = {
        "has_citation": len(answer_metric_rows),
        "citation_from_top_k": len(answer_metric_rows),
        "gold_cited": len(answer_metric_rows),
        "refuse_when_should_not_answer": len(unanswerable_rows),
        "scope_qualified": len(non_diagnostic_rows),
        "answer_keyword_hit": len(keyword_rows),
        "expected_answer_mode_match": len(expected_mode_rows),
    }
    metric_pass_counts = {
        "has_citation": metric_counts(answer_metric_rows, "has_citation")["passed"],
        "citation_from_top_k": metric_counts(answer_metric_rows, "citation_from_top_k")["passed"],
        "gold_cited": metric_counts(answer_metric_rows, "gold_cited")["passed"],
        "refuse_when_should_not_answer": metric_counts(unanswerable_rows, "refuse_when_should_not_answer")["passed"],
        "scope_qualified": metric_counts(non_diagnostic_rows, "scope_qualified")["passed"],
        "answer_keyword_hit": metric_counts(keyword_rows, "answer_keyword_hit")["passed"],
        "expected_answer_mode_match": metric_counts(expected_mode_rows, "expected_answer_mode_match")["passed"],
    }

    return {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": display_path(dataset_path),
        "retrieval_eval_source": display_path(retrieval_json),
        "trace_log": display_path(trace_path),
        "run_mode": run_mode_config["run_mode"],
        "env_flags": {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
            "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
        },
        "judge": {
            "type": "rules_only",
            "llm_judge": False,
        },
        "llm_used": any(bool(record.get("llm_used")) for record in trace_records),
        "total_examples": len(per_example),
        "answerable_metric_examples": class_counts.get("answerable_metric", 0),
        "diagnostic_only_examples": class_counts.get("diagnostic_only", 0),
        "unanswerable_examples": class_counts.get("unanswerable", 0),
        "has_citation_rate": rate(answer_metric_rows, "has_citation"),
        "citation_from_top_k_rate": rate(answer_metric_rows, "citation_from_top_k"),
        "gold_cited_rate": rate(answer_metric_rows, "gold_cited"),
        "refuse_when_should_not_answer_rate": rate(unanswerable_rows, "refuse_when_should_not_answer"),
        "scope_qualified_rate": rate(non_diagnostic_rows, "scope_qualified"),
        "answer_keyword_hit_rate": rate(keyword_rows, "answer_keyword_hit"),
        "expected_answer_mode_match_rate": rate(expected_mode_rows, "expected_answer_mode_match"),
        "metric_denominators": metric_denominators,
        "metric_pass_counts": metric_pass_counts,
        "per_category": per_category,
        "per_example": per_example,
    }


def format_rule_list(rows: list[dict[str, Any]], *, empty: str = "- none") -> list[str]:
    if not rows:
        return [empty]
    lines: list[str] = []
    for row in rows:
        lines.append(
            "- `{id}` ({category}) {question} | mode={mode} | citations={citations} | notes={notes}".format(
                id=row["id"],
                category=row["category"],
                question=row["question"],
                mode=row["actual_answer_mode"],
                citations=json.dumps(row["citation_ids"], ensure_ascii=False),
                notes=row["notes"] or "",
            )
        )
    return lines


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# answer_eval_v1",
        "",
        "## Summary",
        "",
        f"- Dataset: `{payload['dataset_path']}`",
        f"- Retrieval eval source: `{payload['retrieval_eval_source']}`",
        f"- Trace log: `{payload['trace_log']}`",
        f"- Run mode: `{payload['run_mode']}`",
        f"- LLM used: `{str(payload['llm_used']).lower()}`",
        f"- Total examples: {payload['total_examples']}",
        f"- Answerable metric examples: {payload['answerable_metric_examples']}",
        f"- Diagnostic-only examples: {payload['diagnostic_only_examples']}",
        f"- Unanswerable examples: {payload['unanswerable_examples']}",
        f"- has_citation_rate: {payload['has_citation_rate']:.6f}",
        f"- citation_from_top_k_rate: {payload['citation_from_top_k_rate']:.6f}",
        f"- gold_cited_rate: {payload['gold_cited_rate']:.6f}",
        f"- refuse_when_should_not_answer_rate: {payload['refuse_when_should_not_answer_rate']:.6f}",
        f"- scope_qualified_rate: {payload['scope_qualified_rate']:.6f}",
        f"- answer_keyword_hit_rate: {payload['answer_keyword_hit_rate']:.6f}",
        f"- expected_answer_mode_match_rate: {payload['expected_answer_mode_match_rate']:.6f}",
        "",
        "## Per Category",
        "",
        "| category | examples | answerable | diagnostic | unanswerable | has citation | citation in top-k | gold cited | refuse ok | scope qualified | keyword hit | mode match |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for category, metrics in payload["per_category"].items():
        lines.append(
            "| {category} | {examples} | {answerable} | {diagnostic} | {unanswerable} | "
            "{has:.6f} | {topk:.6f} | {gold:.6f} | {refuse:.6f} | {scope:.6f} | {keyword:.6f} | {mode:.6f} |".format(
                category=category,
                examples=metrics["examples"],
                answerable=metrics["answerable_metric_examples"],
                diagnostic=metrics["diagnostic_only_examples"],
                unanswerable=metrics["unanswerable_examples"],
                has=metrics["has_citation_rate"],
                topk=metrics["citation_from_top_k_rate"],
                gold=metrics["gold_cited_rate"],
                refuse=metrics["refuse_when_should_not_answer_rate"],
                scope=metrics["scope_qualified_rate"],
                keyword=metrics["answer_keyword_hit_rate"],
                mode=metrics["expected_answer_mode_match_rate"],
            )
        )

    answer_rows = [row for row in payload["per_example"] if row["included_in_answer_metrics"]]
    unanswerable_rows = [row for row in payload["per_example"] if row["example_class"] == "unanswerable"]
    non_diagnostic_rows = [row for row in payload["per_example"] if not row["diagnostic_only"]]
    citation_missing = [row for row in answer_rows if row["has_citation"] is False]
    citation_not_topk = [row for row in answer_rows if row["citation_from_top_k"] is False]
    unrefused = [row for row in unanswerable_rows if row["refuse_when_should_not_answer"] is False]
    mode_mismatch = [row for row in non_diagnostic_rows if row["expected_answer_mode_match"] is False]
    diagnostics = [row for row in payload["per_example"] if row["diagnostic_only"]]

    lines.extend(["", "## Citation Missing", ""])
    lines.extend(format_rule_list(citation_missing))
    lines.extend(["", "## Citation Not From Top-K", ""])
    lines.extend(format_rule_list(citation_not_topk))
    lines.extend(["", "## Should Answer False But Not Refused", ""])
    lines.extend(format_rule_list(unrefused))
    lines.extend(["", "## Expected Answer Mode Mismatch", ""])
    lines.extend(format_rule_list(mode_mismatch))

    lines.extend(["", "## P2 Residual Diagnostics", ""])
    lines.append("These rows are diagnostic-only and are not included in gold_cited or keyword-hit aggregate denominators.")
    lines.append("")
    lines.append("| id | question | answer_mode | citations | final_answer_excerpt |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in diagnostics:
        lines.append(
            "| {id} | {question} | {mode} | `{citations}` | {excerpt} |".format(
                id=row["id"],
                question=row["question"],
                mode=row["actual_answer_mode"],
                citations=json.dumps(row["citation_ids"], ensure_ascii=False),
                excerpt=row["final_answer_excerpt"].replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def run_answer_chain(
    *,
    examples: list[EvalExample],
    trace_tmp_dir: Path,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    os.environ[ENV_QA_TRACE_DIR] = str(trace_tmp_dir)
    os.environ[ENV_QA_TRACE_ENABLED] = "1"
    assembler = AnswerAssembler(
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
    try:
        for index, example in enumerate(examples, start=1):
            print(f"[{index}/{len(examples)}] answer_eval: {example.id} {example.question}", flush=True)
            assembler.assemble(example.question)
    finally:
        assembler.close()
    return read_tmp_trace_records(trace_tmp_dir)


def run_eval(args: argparse.Namespace) -> dict[str, Any]:
    dataset_path = resolve_project_path(args.dataset)
    retrieval_json = resolve_project_path(args.retrieval_json)
    out_dir = resolve_project_path(args.out_dir)
    trace_path, trace_tmp_dir = prepare_trace_paths(out_dir)
    db_path = resolve_project_path(args.db_path)

    env_keys = [
        "PERF_DISABLE_LLM",
        "PERF_DISABLE_RERANK",
        "PERF_RETRIEVAL_MODE",
        ENV_QA_TRACE_DIR,
        ENV_QA_TRACE_ENABLED,
    ]
    old_env = {key: os.environ.get(key) for key in env_keys}
    try:
        run_mode_config = apply_run_mode(args.run_mode)
        examples = load_dataset(dataset_path)
        raw_trace_records = run_answer_chain(examples=examples, trace_tmp_dir=trace_tmp_dir, args=args)
        ordered_trace_records = order_trace_records(examples, raw_trace_records)
        write_canonical_trace(trace_path, ordered_trace_records)

        equivalence = IdEquivalenceIndex(db_path)
        per_example = [
            score_example(example, record, equivalence)
            for example, record in zip(examples, ordered_trace_records, strict=True)
        ]
        payload = aggregate_payload(
            dataset_path=dataset_path,
            retrieval_json=retrieval_json,
            trace_path=trace_path,
            run_mode_config=run_mode_config,
            per_example=per_example,
            trace_records=ordered_trace_records,
        )

        json_path = out_dir / f"{RUN_ID}.json"
        md_path = out_dir / f"{RUN_ID}.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(build_report(payload), encoding="utf-8")
        print(f"Wrote {display_path(trace_path)}", flush=True)
        print(f"Wrote {display_path(json_path)}", flush=True)
        print(f"Wrote {display_path(md_path)}", flush=True)
        return payload
    finally:
        if trace_tmp_dir.exists():
            shutil.rmtree(trace_tmp_dir)
        restore_env(old_env)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET, type=Path)
    parser.add_argument("--retrieval-json", default=DEFAULT_RETRIEVAL_JSON, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--run-mode", default="B", choices=sorted(RUN_MODE_ENV))
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX)
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META)
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX)
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    run_eval(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
