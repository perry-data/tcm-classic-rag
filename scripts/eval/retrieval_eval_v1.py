#!/usr/bin/env python3
"""Evaluate retrieval top-k evidence hits for eval_dataset_v1.

This evaluator only runs retrieval plus optional rerank. It does not assemble
answers and does not call any LLM path.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.retrieval.hybrid import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_RERANK_MODEL,
    HybridRetrievalEngine,
)
from backend.retrieval.minimal import DEFAULT_DB_PATH, DEFAULT_POLICY_PATH, preview_text  # noqa: E402


RUN_ID = "retrieval_eval_v1"
DEFAULT_DATASET = REPO_ROOT / "data" / "eval" / "eval_dataset_v1.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "eval" / RUN_ID

RUN_MODE_ENV = {
    "A": {
        "run_mode": "A_sparse_no_rerank",
        "PERF_DISABLE_LLM": "1",
        "PERF_DISABLE_RERANK": "1",
        "PERF_RETRIEVAL_MODE": "sparse",
    },
    "B": {
        "run_mode": "B_retrieval_rerank",
        "PERF_DISABLE_LLM": "1",
        "PERF_DISABLE_RERANK": "0",
        "PERF_RETRIEVAL_MODE": "hybrid",
    },
}

ID_FIELD_NAMES = {
    "record_id",
    "retrieval_entry_id",
    "source_record_id",
    "chunk_id",
    "passage_id",
    "annotation_id",
    "formula_id",
    "concept_id",
    "primary_formula_passage_id",
    "primary_support_passage_id",
    "primary_source_record_id",
    "formula_span_start_passage_id",
    "formula_span_end_passage_id",
    "main_passage_record_id",
    "main_passage_id",
    "chunk_record_id",
    "formula_record_id",
}

JSON_LIST_FIELD_NAMES = {
    "source_passage_ids_json",
    "backref_target_ids_json",
    "definition_evidence_passage_ids_json",
    "explanation_evidence_passage_ids_json",
    "membership_evidence_passage_ids_json",
    "primary_ids",
    "secondary_ids",
    "review_ids",
}


@dataclass(frozen=True)
class EvalExample:
    id: str
    category: str
    question: str
    should_answer: bool
    manual_audit_required: bool
    gold_chunk_ids: list[str]
    notes: str
    subtype: str


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


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def split_gold_ids(value: str | None) -> list[str]:
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_dataset(dataset_path: Path) -> list[EvalExample]:
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                EvalExample(
                    id=(row.get("id") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    question=(row.get("question") or "").strip(),
                    should_answer=parse_bool(row.get("should_answer")),
                    manual_audit_required=parse_bool(row.get("manual_audit_required")),
                    gold_chunk_ids=split_gold_ids(row.get("gold_chunk_ids")),
                    notes=(row.get("notes") or "").strip(),
                    subtype=(row.get("subtype") or "").strip(),
                )
            )
    return rows


def parse_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if item]


def add_id_variants(ids: set[str], value: str | None, *, kind: str | None = None) -> None:
    if not value:
        return
    raw = str(value).strip()
    if not raw:
        return

    ids.add(raw)
    if kind == "formula" or raw.startswith("formula:"):
        formula_id = raw.split(":", 1)[1] if raw.startswith("formula:") else raw
        ids.add(formula_id)
        ids.add(f"formula:{formula_id}")
        return
    if kind == "concept" or raw.startswith("safe:definition_terms:"):
        concept_id = raw.rsplit(":", 1)[-1] if raw.startswith("safe:definition_terms:") else raw
        ids.add(concept_id)
        ids.add(f"safe:definition_terms:{concept_id}")
        return
    if kind == "passage":
        ids.add(f"safe:main_passages:{raw}")
        ids.add(f"full:passages:{raw}")
        return
    if kind == "annotation":
        ids.add(f"full:annotations:{raw}")
        return
    if kind == "chunk":
        ids.add(f"safe:chunks:{raw}")
        return

    if raw.startswith(("safe:", "full:", "risk:")):
        bare = raw.rsplit(":", 1)[-1]
        if raw.startswith("safe:main_passages:"):
            ids.add(bare)
            ids.add(f"full:passages:{bare}")
        elif raw.startswith("full:passages:"):
            ids.add(bare)
            ids.add(f"safe:main_passages:{bare}")
        elif raw.startswith("safe:chunks:"):
            ids.add(bare)
        elif raw.startswith("full:annotations:"):
            return
        return

    if raw.startswith("FML-"):
        ids.add(f"formula:{raw}")
        return
    if raw.startswith(("DPO-", "AHV-")):
        ids.add(f"safe:definition_terms:{raw}")
        return
    if "-CK-" in raw:
        ids.add(f"safe:chunks:{raw}")
        return
    if "-P-" in raw:
        ids.add(f"safe:main_passages:{raw}")
        ids.add(f"full:passages:{raw}")


def expanded_id_set(values: Iterable[str]) -> set[str]:
    ids: set[str] = set()
    for value in values:
        add_id_variants(ids, value)
    return ids


class IdEquivalenceIndex:
    def __init__(self, db_path: Path) -> None:
        self.object_sources_by_id: dict[str, set[str]] = defaultdict(set)
        self._load(db_path)

    def equivalents_for_values(self, values: Iterable[str]) -> set[str]:
        expanded = expanded_id_set(values)
        for value in list(expanded):
            expanded.update(self.object_sources_by_id.get(value, set()))
        return expanded

    def _link_object_sources(self, object_values: Iterable[str], source_values: Iterable[str]) -> None:
        objects = expanded_id_set(value for value in object_values if value)
        sources = expanded_id_set(value for value in source_values if value)
        if not objects or not sources:
            return
        for value in objects:
            self.object_sources_by_id[value].update(sources)

    def _load(self, db_path: Path) -> None:
        if not db_path.exists():
            return
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            self._load_formula_equivalences(conn)
            self._load_definition_equivalences(conn)
        finally:
            conn.close()

    def _load_formula_equivalences(self, conn: sqlite3.Connection) -> None:
        if not self._table_exists(conn, "retrieval_ready_formula_view"):
            return
        rows = conn.execute(
            """
            SELECT
                formula_id,
                primary_formula_passage_id,
                formula_span_start_passage_id,
                formula_span_end_passage_id,
                source_passage_ids_json
            FROM retrieval_ready_formula_view
            """
        ).fetchall()
        for row in rows:
            formula_id = row["formula_id"]
            source_values = [
                row["primary_formula_passage_id"],
                row["formula_span_start_passage_id"],
                row["formula_span_end_passage_id"],
                *parse_json_list(row["source_passage_ids_json"]),
            ]
            self._link_object_sources([formula_id, f"formula:{formula_id}"], source_values)

    def _load_definition_equivalences(self, conn: sqlite3.Connection) -> None:
        if not self._table_exists(conn, "retrieval_ready_definition_view"):
            return
        rows = conn.execute(
            """
            SELECT
                concept_id,
                primary_support_passage_id,
                primary_source_record_id,
                definition_evidence_passage_ids_json,
                explanation_evidence_passage_ids_json,
                membership_evidence_passage_ids_json,
                source_passage_ids_json
            FROM retrieval_ready_definition_view
            """
        ).fetchall()
        for row in rows:
            concept_id = row["concept_id"]
            source_values = [
                row["primary_support_passage_id"],
                row["primary_source_record_id"],
                *parse_json_list(row["definition_evidence_passage_ids_json"]),
                *parse_json_list(row["explanation_evidence_passage_ids_json"]),
                *parse_json_list(row["membership_evidence_passage_ids_json"]),
                *parse_json_list(row["source_passage_ids_json"]),
            ]
            self._link_object_sources(
                [concept_id, f"safe:definition_terms:{concept_id}"],
                source_values,
            )

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
            (table,),
        ).fetchone()
        return row is not None


def extract_ids_from_payload(value: Any, ids: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ID_FIELD_NAMES and isinstance(item, str):
                add_id_variants(ids, item)
            elif key in JSON_LIST_FIELD_NAMES:
                for parsed_item in parse_json_list(item):
                    add_id_variants(ids, parsed_item)
            elif key in {"retrieval_paths", "linked_main_passages"}:
                extract_ids_from_payload(item, ids)
        return
    if isinstance(value, list):
        for item in value:
            extract_ids_from_payload(item, ids)


def extract_candidate_matchable_ids(candidate: dict[str, Any], equivalence: IdEquivalenceIndex) -> list[str]:
    ids: set[str] = set()
    record_table = str(candidate.get("record_table") or "")
    record_id = candidate.get("record_id")
    add_id_variants(ids, record_id)

    if record_table == "records_chunks":
        add_id_variants(ids, candidate.get("source_record_id"), kind="chunk")
        for passage_id in parse_json_list(candidate.get("source_passage_ids_json")):
            add_id_variants(ids, passage_id, kind="passage")
        for passage_id in parse_json_list(candidate.get("backref_target_ids_json")):
            add_id_variants(ids, passage_id, kind="passage")
    elif record_table in {"records_main_passages", "records_passages", "controlled_replay_main_passages"}:
        add_id_variants(ids, candidate.get("source_record_id"), kind="passage")
        add_id_variants(ids, candidate.get("passage_id"), kind="passage")
    elif record_table == "records_annotations":
        add_id_variants(ids, candidate.get("source_record_id"), kind="annotation")
        add_id_variants(ids, candidate.get("annotation_id"), kind="annotation")
    elif record_table == "retrieval_ready_formula_view":
        add_id_variants(ids, candidate.get("source_record_id"), kind="formula")
        add_id_variants(ids, candidate.get("formula_id"), kind="formula")
        add_id_variants(ids, candidate.get("primary_formula_passage_id"), kind="passage")
        for passage_id in parse_json_list(candidate.get("source_passage_ids_json")):
            add_id_variants(ids, passage_id, kind="passage")
        for passage_id in parse_json_list(candidate.get("backref_target_ids_json")):
            add_id_variants(ids, passage_id, kind="passage")
    elif record_table == "retrieval_ready_definition_view":
        add_id_variants(ids, candidate.get("source_record_id"), kind="concept")
        add_id_variants(ids, candidate.get("concept_id"), kind="concept")
        add_id_variants(ids, candidate.get("primary_support_passage_id"), kind="passage")
        for passage_id in parse_json_list(candidate.get("source_passage_ids_json")):
            add_id_variants(ids, passage_id, kind="passage")
        for passage_id in parse_json_list(candidate.get("backref_target_ids_json")):
            add_id_variants(ids, passage_id, kind="passage")
    else:
        extract_ids_from_payload(candidate, ids)

    extract_ids_from_payload(
        {
            "retrieval_paths": candidate.get("retrieval_paths") or [],
            "linked_main_passages": candidate.get("linked_main_passages") or [],
        },
        ids,
    )
    return sorted(equivalence.equivalents_for_values(ids))


def candidate_summary(candidate: dict[str, Any], matchable_ids: list[str]) -> dict[str, Any]:
    return {
        "record_id": candidate.get("record_id"),
        "record_table": candidate.get("record_table"),
        "source_object": candidate.get("source_object"),
        "source_record_id": candidate.get("source_record_id"),
        "combined_score": candidate.get("combined_score"),
        "rerank_score": candidate.get("rerank_score"),
        "stage_sources": candidate.get("stage_sources") or [],
        "topic_consistency": candidate.get("topic_consistency"),
        "matchable_ids": matchable_ids,
        "text_preview": preview_text(candidate.get("retrieval_text", "")),
    }


def classify_example(example: EvalExample) -> str:
    if example.manual_audit_required:
        return "diagnostic_only"
    if not example.should_answer:
        return "unanswerable"
    if example.gold_chunk_ids:
        return "answerable_metric"
    return "diagnostic_only"


def score_example(
    example: EvalExample,
    raw_candidates: list[dict[str, Any]],
    equivalence: IdEquivalenceIndex,
) -> dict[str, Any]:
    top5_candidates = raw_candidates[:5]
    all_candidate_matchable_ids = [
        extract_candidate_matchable_ids(candidate, equivalence) for candidate in raw_candidates
    ]
    top5_matchable_ids = all_candidate_matchable_ids[:5]

    gold_equivalence = {
        gold_id: equivalence.equivalents_for_values([gold_id]) for gold_id in example.gold_chunk_ids
    }
    first_hit_rank: int | None = None
    for rank, matchable_ids in enumerate(all_candidate_matchable_ids, start=1):
        matchable_set = set(matchable_ids)
        if any(matchable_set & equivalent_ids for equivalent_ids in gold_equivalence.values()):
            first_hit_rank = rank
            break

    top1_union = set().union(*(set(ids) for ids in top5_matchable_ids[:1])) if top5_matchable_ids[:1] else set()
    top3_union = set().union(*(set(ids) for ids in top5_matchable_ids[:3])) if top5_matchable_ids[:3] else set()
    top5_union = set().union(*(set(ids) for ids in top5_matchable_ids)) if top5_matchable_ids else set()

    hit_at_1 = any(top1_union & equivalent_ids for equivalent_ids in gold_equivalence.values())
    hit_at_3 = any(top3_union & equivalent_ids for equivalent_ids in gold_equivalence.values())
    hit_at_5 = any(top5_union & equivalent_ids for equivalent_ids in gold_equivalence.values())
    matched_gold_count = sum(
        1 for equivalent_ids in gold_equivalence.values() if top5_union & equivalent_ids
    )
    recall_at_5 = matched_gold_count / len(example.gold_chunk_ids) if example.gold_chunk_ids else 0.0
    mrr = 1.0 / first_hit_rank if first_hit_rank is not None and first_hit_rank <= 5 else 0.0
    example_class = classify_example(example)
    included_in_metrics = example_class == "answerable_metric"

    return {
        "id": example.id,
        "category": example.category,
        "question": example.question,
        "should_answer": example.should_answer,
        "manual_audit_required": example.manual_audit_required,
        "gold_chunk_ids": example.gold_chunk_ids,
        "top5_record_ids": [str(candidate.get("record_id") or "") for candidate in top5_candidates],
        "top5_matchable_ids": top5_matchable_ids,
        "top5_candidates": [
            candidate_summary(candidate, matchable_ids)
            for candidate, matchable_ids in zip(top5_candidates, top5_matchable_ids, strict=False)
        ],
        "first_hit_rank": first_hit_rank,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "recall_at_5": round(recall_at_5, 6),
        "mrr": round(mrr, 6),
        "included_in_metrics": included_in_metrics,
        "diagnostic_only": example_class == "diagnostic_only",
        "example_class": example_class,
        "subtype": example.subtype,
        "notes": example.notes,
    }


def aggregate_metric_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "hit_at_1": 0.0,
            "hit_at_3": 0.0,
            "hit_at_5": 0.0,
            "mrr": 0.0,
            "recall_at_5": 0.0,
        }
    denominator = float(len(rows))
    return {
        "hit_at_1": round(sum(1 for row in rows if row["hit_at_1"]) / denominator, 6),
        "hit_at_3": round(sum(1 for row in rows if row["hit_at_3"]) / denominator, 6),
        "hit_at_5": round(sum(1 for row in rows if row["hit_at_5"]) / denominator, 6),
        "mrr": round(sum(float(row["mrr"]) for row in rows) / denominator, 6),
        "recall_at_5": round(sum(float(row["recall_at_5"]) for row in rows) / denominator, 6),
    }


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# retrieval_eval_v1",
        "",
        "## Summary",
        "",
        f"- Dataset: `{payload['dataset_path']}`",
        f"- Run mode: `{payload['run_mode']}`",
        f"- Total examples: {payload['total_examples']}",
        f"- Answerable metric examples: {payload['answerable_metric_examples']}",
        f"- Diagnostic-only examples: {payload['diagnostic_only_examples']}",
        f"- Unanswerable examples: {payload['unanswerable_examples']}",
        f"- Hit@1: {payload['hit_at_1']:.6f}",
        f"- Hit@3: {payload['hit_at_3']:.6f}",
        f"- Hit@5: {payload['hit_at_5']:.6f}",
        f"- MRR: {payload['mrr']:.6f}",
        f"- Recall@5: {payload['recall_at_5']:.6f}",
        "",
        "## Per Category",
        "",
        "| category | examples | Hit@1 | Hit@3 | Hit@5 | MRR | Recall@5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for category, metrics in payload["per_category"].items():
        lines.append(
            "| {category} | {count} | {hit_at_1:.6f} | {hit_at_3:.6f} | "
            "{hit_at_5:.6f} | {mrr:.6f} | {recall_at_5:.6f} |".format(
                category=category,
                count=metrics["examples"],
                hit_at_1=metrics["hit_at_1"],
                hit_at_3=metrics["hit_at_3"],
                hit_at_5=metrics["hit_at_5"],
                mrr=metrics["mrr"],
                recall_at_5=metrics["recall_at_5"],
            )
        )

    metric_examples = [row for row in payload["per_example"] if row["included_in_metrics"]]
    misses = [row for row in metric_examples if not row["hit_at_5"]]
    low_ranked = [
        row
        for row in metric_examples
        if row["first_hit_rank"] is not None and row["first_hit_rank"] > 5
    ]

    lines.extend(["", "## Top5 Misses", ""])
    if not misses:
        lines.append("- none")
    else:
        for row in misses:
            lines.append(
                "- `{id}` ({category}) {question} | gold={gold} | top5={top5}".format(
                    id=row["id"],
                    category=row["category"],
                    question=row["question"],
                    gold=json.dumps(row["gold_chunk_ids"], ensure_ascii=False),
                    top5=json.dumps(row["top5_record_ids"], ensure_ascii=False),
                )
            )

    lines.extend(["", "## Gold Appears Below Top5", ""])
    if not low_ranked:
        lines.append("- none")
    else:
        for row in low_ranked:
            lines.append(
                "- `{id}` rank={rank} {question} | gold={gold} | top5={top5}".format(
                    id=row["id"],
                    rank=row["first_hit_rank"],
                    question=row["question"],
                    gold=json.dumps(row["gold_chunk_ids"], ensure_ascii=False),
                    top5=json.dumps(row["top5_record_ids"], ensure_ascii=False),
                )
            )

    diagnostics = [row for row in payload["per_example"] if row["diagnostic_only"]]
    lines.extend(["", "## P2 Residual Diagnostic Top5", ""])
    for row in diagnostics:
        lines.append(
            "- `{id}` {question} | included_in_metrics=false | top5={top5}".format(
                id=row["id"],
                question=row["question"],
                top5=json.dumps(row["top5_record_ids"], ensure_ascii=False),
            )
        )

    unanswerable = [row for row in payload["per_example"] if row["example_class"] == "unanswerable"]
    lines.extend(["", "## Unanswerable Top5", ""])
    for row in unanswerable:
        lines.append(
            "- `{id}` {question} | included_in_metrics=false | top5={top5}".format(
                id=row["id"],
                question=row["question"],
                top5=json.dumps(row["top5_record_ids"], ensure_ascii=False),
            )
        )

    return "\n".join(lines) + "\n"


def apply_run_mode(run_mode: str) -> dict[str, str]:
    mode = run_mode.upper()
    if mode not in RUN_MODE_ENV:
        raise ValueError(f"unsupported run mode: {run_mode}")
    config = RUN_MODE_ENV[mode]
    for key, value in config.items():
        if key.startswith("PERF_"):
            os.environ[key] = value
    return config


def run_eval(args: argparse.Namespace) -> dict[str, Any]:
    dataset_path = resolve_project_path(args.dataset)
    out_dir = resolve_project_path(args.out_dir)
    db_path = resolve_project_path(args.db_path)
    policy_path = resolve_project_path(args.policy_json)
    run_mode_config = apply_run_mode(args.run_mode)

    examples = load_dataset(dataset_path)
    equivalence = IdEquivalenceIndex(db_path)
    engine = HybridRetrievalEngine(
        db_path=db_path,
        policy_path=policy_path,
        candidate_limit=args.candidate_limit,
        embed_model=args.embed_model,
        rerank_model=args.rerank_model,
        cache_dir=resolve_project_path(args.cache_dir),
        dense_chunks_index=resolve_project_path(args.dense_chunks_index),
        dense_chunks_meta=resolve_project_path(args.dense_chunks_meta),
        dense_main_index=resolve_project_path(args.dense_main_index),
        dense_main_meta=resolve_project_path(args.dense_main_meta),
    )
    try:
        per_example: list[dict[str, Any]] = []
        for index, example in enumerate(examples, start=1):
            print(f"[{index}/{len(examples)}] retrieval: {example.id} {example.question}", flush=True)
            retrieval = engine.retrieve(example.question)
            per_example.append(score_example(example, retrieval["raw_candidates"], equivalence))
    finally:
        engine.close()

    metric_rows = [row for row in per_example if row["included_in_metrics"]]
    top_metrics = aggregate_metric_rows(metric_rows)
    per_category: dict[str, dict[str, Any]] = {}
    for category in sorted({row["category"] for row in metric_rows}):
        rows = [row for row in metric_rows if row["category"] == category]
        per_category[category] = {"examples": len(rows), **aggregate_metric_rows(rows)}

    class_counts = Counter(row["example_class"] for row in per_example)
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": display_path(dataset_path),
        "run_mode": run_mode_config["run_mode"],
        "env_flags": {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
            "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
        },
        "llm_used": False,
        "total_examples": len(per_example),
        "answerable_metric_examples": class_counts.get("answerable_metric", 0),
        "diagnostic_only_examples": class_counts.get("diagnostic_only", 0),
        "unanswerable_examples": class_counts.get("unanswerable", 0),
        **top_metrics,
        "per_category": per_category,
        "per_example": per_example,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{RUN_ID}.json"
    md_path = out_dir / f"{RUN_ID}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(build_report(payload), encoding="utf-8")
    print(f"Wrote {display_path(json_path)}", flush=True)
    print(f"Wrote {display_path(md_path)}", flush=True)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--run-mode", default="B", choices=sorted(RUN_MODE_ENV))
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--policy-json", default=DEFAULT_POLICY_PATH)
    parser.add_argument("--candidate-limit", default=24, type=int)
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
