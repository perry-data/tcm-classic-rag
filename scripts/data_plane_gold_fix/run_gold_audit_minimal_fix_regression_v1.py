#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


os.environ.setdefault("PERF_DISABLE_LLM", "1")
os.environ.setdefault("PERF_DISABLE_RERANK", "1")
os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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
    resolve_project_path,
)


DEFAULT_BEFORE_DB = "/tmp/zjshl_v1_before_gold_audit_minimal_fix_v1.db"
DEFAULT_OUTPUT_JSON = "artifacts/data_plane_gold_fix/gold_audit_minimal_fix_regression_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_plane_gold_fix/gold_audit_minimal_fix_regression_v1.md"
DEFAULT_DOC_PATH = "docs/data_plane_gold_fix/gold_audit_minimal_fixes_v1.md"
DEFAULT_OUTPUT_DIR = "artifacts/data_plane_gold_fix"

FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
RISK_ALIASES = {"口苦病", "胆瘅病"}

REGRESSION_QUERIES: tuple[dict[str, str], ...] = (
    {"category": "fahan", "query": "什么是发汗药", "target": "发汗药"},
    {"category": "fahan", "query": "发汗药是什么意思", "target": "发汗药"},
    {"category": "fahan", "query": "发汗药是干什么的", "target": "发汗药"},
    {"category": "fahan", "query": "发汗的药是什么意思", "target": "发汗药"},
    {"category": "dandan", "query": "什么是胆瘅", "target": "胆瘅"},
    {"category": "dandan", "query": "胆瘅是什么意思", "target": "胆瘅"},
    {"category": "dandan_alias", "query": "口苦病是什么意思", "target": "胆瘅"},
    {"category": "dandan_alias", "query": "胆瘅病是什么意思", "target": "胆瘅"},
    {"category": "formula", "query": "桂枝汤方的条文是什么？", "target": ""},
    {"category": "formula", "query": "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？", "target": ""},
    {"category": "gold_safe_definition", "query": "什么是下药", "target": "下药"},
    {"category": "gold_safe_definition", "query": "什么是四逆", "target": "四逆"},
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gold audit minimal fix regression v1.")
    parser.add_argument("--before-db", default=DEFAULT_BEFORE_DB)
    parser.add_argument("--after-db", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    return json.loads(value)


def safe_cell(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return text.replace("|", "／").replace("\n", "<br>")


def make_assembler(db_path: Path) -> AnswerAssembler:
    return AnswerAssembler(
        db_path=db_path,
        policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
        embed_model=DEFAULT_EMBED_MODEL,
        rerank_model=DEFAULT_RERANK_MODEL,
        cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
        dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
        dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
        dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
        dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
    )


def fetch_definition_row(conn: sqlite3.Connection, canonical_term: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM definition_term_registry WHERE canonical_term = ?",
        (canonical_term,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing definition term: {canonical_term}")
    out = dict(row)
    for key in (
        "definition_evidence_passage_ids_json",
        "explanation_evidence_passage_ids_json",
        "membership_evidence_passage_ids_json",
        "source_passage_ids_json",
        "chapter_ids_json",
        "query_aliases_json",
        "learner_surface_forms_json",
    ):
        out[key.removesuffix("_json")] = json_list(out.get(key))
    return out


def fetch_registry_snapshot(db_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        definition_rows = {
            term: fetch_definition_row(conn, term)
            for term in ("发汗药", "胆瘅", "下药", "四逆")
        }
        dandan_aliases = [
            dict(row)
            for row in conn.execute(
                """
                SELECT alias, normalized_alias, alias_type, confidence, source, notes, is_active
                FROM term_alias_registry
                WHERE canonical_term = '胆瘅'
                ORDER BY alias
                """
            )
        ]
        dandan_learner_entries = [
            dict(row)
            for row in conn.execute(
                """
                SELECT surface_form, normalized_surface_form, entry_type, target_term, target_id, confidence, source, notes, is_active
                FROM learner_query_normalization_lexicon
                WHERE target_term = '胆瘅' OR surface_form IN ('口苦病', '胆瘅病')
                ORDER BY surface_form, target_term
                """
            )
        ]
        return {
            "definition_rows": definition_rows,
            "dandan_aliases": dandan_aliases,
            "dandan_learner_entries": dandan_learner_entries,
            "dandan_risk_alias_count": sum(1 for row in dandan_aliases if row["alias"] in RISK_ALIASES),
            "dandan_risk_learner_entry_count": sum(
                1 for row in dandan_learner_entries if row["surface_form"] in RISK_ALIASES
            ),
        }
    finally:
        conn.close()


def primary_forbidden_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    forbidden: list[dict[str, Any]] = []
    for item in payload.get("primary_evidence") or []:
        record_id = str(item.get("record_id") or "")
        if item.get("record_type") in FORBIDDEN_PRIMARY_TYPES or record_id.startswith("full:passages:"):
            forbidden.append({"record_id": item.get("record_id"), "record_type": item.get("record_type")})
    return forbidden


def concept_ids(snapshot: dict[str, Any]) -> dict[str, str]:
    return {
        term: row["concept_id"]
        for term, row in snapshot["definition_rows"].items()
    }


def summarize_query(
    assembler: AnswerAssembler,
    snapshot: dict[str, Any],
    query: str,
    category: str,
    target: str,
) -> dict[str, Any]:
    ids_by_name = concept_ids(snapshot)
    retrieval = assembler.engine.retrieve(query)
    payload = assembler.assemble(query)
    raw_top = retrieval.get("raw_candidates") or []
    primary = payload.get("primary_evidence") or []
    primary_ids = [str(item.get("record_id") or "") for item in primary]
    primary_concept_ids = [
        record_id.rsplit(":", 1)[-1]
        for record_id in primary_ids
        if record_id.startswith("safe:definition_terms:")
    ]
    term_normalization = retrieval.get("query_request", {}).get("term_normalization") or {}
    target_id = ids_by_name.get(target, "")
    return {
        "category": category,
        "query": query,
        "target": target,
        "target_concept_id": target_id,
        "answer_mode": payload.get("answer_mode"),
        "query_focus_source": retrieval.get("query_request", {}).get("query_focus_source"),
        "term_normalization": term_normalization,
        "primary_ids": primary_ids,
        "primary_record_types": [item.get("record_type") for item in primary],
        "primary_forbidden_items": primary_forbidden_items(payload),
        "target_definition_primary_hit": bool(target_id and target_id in primary_concept_ids),
        "dandan_definition_primary_conflict": ids_by_name.get("胆瘅") in primary_concept_ids,
        "formula_bad_anchor_top5_count": sum(
            1 for row in raw_top[:5] if row.get("topic_consistency") in BAD_FORMULA_TOPICS
        ),
    }


def run_suite(db_path: Path) -> dict[str, Any]:
    snapshot = fetch_registry_snapshot(db_path)
    assembler = make_assembler(db_path)
    try:
        rows = [
            summarize_query(assembler, snapshot, item["query"], item["category"], item["target"])
            for item in REGRESSION_QUERIES
        ]
    finally:
        assembler.close()
    category_counts: dict[str, dict[str, int]] = {}
    for category in sorted({row["category"] for row in rows}):
        category_counts[category] = dict(
            sorted(Counter(row["answer_mode"] for row in rows if row["category"] == category).items())
        )
    summary = {
        "query_count": len(rows),
        "mode_counts": dict(sorted(Counter(row["answer_mode"] for row in rows).items())),
        "category_mode_counts": category_counts,
        "forbidden_primary_total": sum(len(row["primary_forbidden_items"]) for row in rows),
        "formula_query_count": sum(1 for row in rows if row["category"] == "formula"),
        "formula_strong_count": sum(
            1 for row in rows if row["category"] == "formula" and row["answer_mode"] == "strong"
        ),
        "formula_bad_anchor_top5_total": sum(
            row["formula_bad_anchor_top5_count"] for row in rows if row["category"] == "formula"
        ),
        "dandan_definition_primary_conflict_total": sum(
            1 for row in rows if row["dandan_definition_primary_conflict"]
        ),
        "dandan_risk_alias_count": snapshot["dandan_risk_alias_count"],
        "dandan_risk_learner_entry_count": snapshot["dandan_risk_learner_entry_count"],
        "gold_safe_definition_target_hit_count": sum(
            1
            for row in rows
            if row["category"] == "gold_safe_definition" and row["target_definition_primary_hit"]
        ),
        "fahan_target_hit_count": sum(
            1 for row in rows if row["category"] == "fahan" and row["target_definition_primary_hit"]
        ),
    }
    return {"snapshot": snapshot, "rows": rows, "summary": summary}


def pair_results(before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before_by_query = {row["query"]: row for row in before_rows}
    return [
        {
            "query": after["query"],
            "category": after["category"],
            "before": before_by_query[after["query"]],
            "after": after,
            "delta": {
                "mode_changed": before_by_query[after["query"]]["answer_mode"] != after["answer_mode"],
                "focus_changed": before_by_query[after["query"]]["query_focus_source"] != after["query_focus_source"],
                "target_hit_changed": before_by_query[after["query"]]["target_definition_primary_hit"]
                != after["target_definition_primary_hit"],
            },
        }
        for after in after_rows
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_registry_snapshots(output_dir: Path, after: dict[str, Any]) -> None:
    snapshot = after["snapshot"]
    write_json(
        output_dir / "definition_term_registry_gold_fix_v1_snapshot.json",
        {
            "generated_at_utc": now_utc(),
            "scope": "filtered objects touched or guarded by gold audit minimal fixes v1",
            "records": [
                snapshot["definition_rows"]["发汗药"],
                snapshot["definition_rows"]["胆瘅"],
                snapshot["definition_rows"]["下药"],
                snapshot["definition_rows"]["四逆"],
            ],
        },
    )
    write_json(
        output_dir / "term_alias_registry_gold_fix_v1_snapshot.json",
        {
            "generated_at_utc": now_utc(),
            "scope": "胆瘅 alias entries after cleanup",
            "records": snapshot["dandan_aliases"],
        },
    )
    write_json(
        output_dir / "learner_query_normalization_lexicon_gold_fix_v1_snapshot.json",
        {
            "generated_at_utc": now_utc(),
            "scope": "胆瘅 and risk learner surface entries after cleanup",
            "records": snapshot["dandan_learner_entries"],
        },
    )


def query_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| category | query | before_mode | after_mode | before_focus | after_focus | before_target_hit | after_target_hit | primary_after |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        before = row["before"]
        after = row["after"]
        lines.append(
            "| "
            + " | ".join(
                [
                    safe_cell(row["category"]),
                    safe_cell(row["query"]),
                    safe_cell(before["answer_mode"]),
                    safe_cell(after["answer_mode"]),
                    safe_cell(before["query_focus_source"]),
                    safe_cell(after["query_focus_source"]),
                    safe_cell(before["target_definition_primary_hit"]),
                    safe_cell(after["target_definition_primary_hit"]),
                    safe_cell(after["primary_ids"] or "-"),
                ]
            )
            + " |"
        )
    return lines


def write_regression_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Gold Audit Minimal Fix Regression v1",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- before_db: `{payload['before_db']}`",
        f"- after_db: `{payload['after_db']}`",
        "",
        "## Summary",
        "",
        f"- forbidden_primary before -> after: `{payload['before_summary']['forbidden_primary_total']} -> {payload['after_summary']['forbidden_primary_total']}`",
        f"- 胆瘅 risk alias count before -> after: `{payload['before_summary']['dandan_risk_alias_count']} -> {payload['after_summary']['dandan_risk_alias_count']}`",
        f"- 胆瘅 learner lexicon risk count before -> after: `{payload['before_summary']['dandan_risk_learner_entry_count']} -> {payload['after_summary']['dandan_risk_learner_entry_count']}`",
        f"- 胆瘅 definition primary conflicts before -> after: `{payload['before_summary']['dandan_definition_primary_conflict_total']} -> {payload['after_summary']['dandan_definition_primary_conflict_total']}`",
        f"- formula strong before -> after: `{payload['before_summary']['formula_strong_count']}/{payload['before_summary']['formula_query_count']} -> {payload['after_summary']['formula_strong_count']}/{payload['after_summary']['formula_query_count']}`",
        f"- formula bad anchors top5 before -> after: `{payload['before_summary']['formula_bad_anchor_top5_total']} -> {payload['after_summary']['formula_bad_anchor_top5_total']}`",
        f"- gold-safe definition hit before -> after: `{payload['before_summary']['gold_safe_definition_target_hit_count']} -> {payload['after_summary']['gold_safe_definition_target_hit_count']}`",
        f"- 发汗药 target hit before -> after: `{payload['before_summary']['fahan_target_hit_count']} -> {payload['after_summary']['fahan_target_hit_count']}`",
        "",
        "## Query Table",
        "",
        *query_table(payload["paired_results"]),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fahan_md(path: Path, payload: dict[str, Any]) -> None:
    before = payload["before"]["snapshot"]["definition_rows"]["发汗药"]
    after = payload["after"]["snapshot"]["definition_rows"]["发汗药"]
    rows = [row for row in payload["paired_results"] if row["category"] == "fahan"]
    lines = [
        "# 发汗药 Fix Before/After v1",
        "",
        "## Decision",
        "",
        "采用方案2：未找到比当前句更合格、更 learner-facing 且可独立成义的安全 definition/membership primary。当前句保留，但对象语义显式落为 explanation-primary，不再按严格术语定义对象理解。",
        "",
        "## Registry Before/After",
        "",
        f"- primary sentence: `{before['primary_evidence_text']}` -> `{after['primary_evidence_text']}`",
        f"- primary_evidence_type: `{before['primary_evidence_type']}` -> `{after['primary_evidence_type']}`",
        f"- definition evidence ids: `{safe_cell(before['definition_evidence_passage_ids'])}` -> `{safe_cell(after['definition_evidence_passage_ids'])}`",
        f"- explanation evidence ids: `{safe_cell(before['explanation_evidence_passage_ids'])}` -> `{safe_cell(after['explanation_evidence_passage_ids'])}`",
        f"- membership evidence ids: `{safe_cell(before['membership_evidence_passage_ids'])}` -> `{safe_cell(after['membership_evidence_passage_ids'])}`",
        f"- promotion_reason: `{before['promotion_reason']}` -> `{after['promotion_reason']}`",
        "",
        "## Notes Before",
        "",
        before["notes"],
        "",
        "## Notes After",
        "",
        after["notes"],
        "",
        "## Query Behavior",
        "",
        *query_table(rows),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_dandan_md(path: Path, payload: dict[str, Any]) -> None:
    before = payload["before"]["snapshot"]["definition_rows"]["胆瘅"]
    after = payload["after"]["snapshot"]["definition_rows"]["胆瘅"]
    rows = [row for row in payload["paired_results"] if row["category"] in {"dandan", "dandan_alias"}]
    lines = [
        "# 胆瘅 Alias Fix Before/After v1",
        "",
        "## Decision",
        "",
        "保持 `胆瘅` 为 review-only，不恢复 safe primary；清理 review-only 对象上的 learner aliases `口苦病` / `胆瘅病`，仅保留 canonical alias `胆瘅` 作为对象登记面。",
        "",
        "## Registry Before/After",
        "",
        f"- source_confidence: `{before['source_confidence']}` -> `{after['source_confidence']}`",
        f"- promotion_state: `{before['promotion_state']}` -> `{after['promotion_state']}`",
        f"- is_safe_primary_candidate: `{before['is_safe_primary_candidate']}` -> `{after['is_safe_primary_candidate']}`",
        f"- query_aliases: `{safe_cell(before['query_aliases'])}` -> `{safe_cell(after['query_aliases'])}`",
        f"- learner_surface_forms: `{safe_cell(before['learner_surface_forms'])}` -> `{safe_cell(after['learner_surface_forms'])}`",
        f"- risk alias count: `{payload['before_summary']['dandan_risk_alias_count']}` -> `{payload['after_summary']['dandan_risk_alias_count']}`",
        f"- risk learner lexicon count: `{payload['before_summary']['dandan_risk_learner_entry_count']}` -> `{payload['after_summary']['dandan_risk_learner_entry_count']}`",
        "",
        "## Alias Before",
        "",
        "```json",
        json.dumps(payload["before"]["snapshot"]["dandan_aliases"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Alias After",
        "",
        "```json",
        json.dumps(payload["after"]["snapshot"]["dandan_aliases"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Query Behavior",
        "",
        *query_table(rows),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_doc(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Gold Audit Minimal Fixes v1",
        "",
        "## Scope",
        "",
        "- 本轮只落实 small gold audit v1 指出的两个立即问题：`发汗药` primary sentence 裁决、`胆瘅` review-only alias cleanup。",
        "- 未扩容 definition/formula 对象，未修改 prompt、前端、API payload、answer_mode 或 commentarial 主逻辑。",
        "",
        "## 发汗药",
        "",
        "- 结论：采用方案2，保留当前句并显式标为 explanation-primary。",
        "- 理由：`桂枝汤者，发汗药也` 是具体方剂归属句，不是“发汗药”本身的独立定义；当前句能解释服法与发散机制，但不能当严格 definition-primary。",
        "- 落地：`primary_evidence_type` 维持 `exact_term_explanation`，`promotion_reason` 改为 `gold_fix_v1_explanation_primary_not_strict_definition`，notes 写明不是 strict definition。",
        "",
        "## 胆瘅",
        "",
        "- 结论：继续 review-only，清理 `口苦病` / `胆瘅病` learner alias 风险。",
        "- 落地：`query_aliases_json` 与 `learner_surface_forms_json` 清空；`retrieval_text` 移除风险 alias；`term_alias_registry` 只保留 canonical `胆瘅`。",
        "",
        "## Regression Summary",
        "",
        f"- forbidden_primary after: `{payload['after_summary']['forbidden_primary_total']}`",
        f"- 胆瘅 risk alias after: `{payload['after_summary']['dandan_risk_alias_count']}`",
        f"- 胆瘅 learner lexicon risk after: `{payload['after_summary']['dandan_risk_learner_entry_count']}`",
        f"- formula strong after: `{payload['after_summary']['formula_strong_count']}/{payload['after_summary']['formula_query_count']}`",
        f"- gold-safe definition hit after: `{payload['after_summary']['gold_safe_definition_target_hit_count']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    before_db = Path(args.before_db)
    after_db = resolve_project_path(args.after_db)
    output_dir = resolve_project_path(args.output_dir)

    before = run_suite(before_db)
    after = run_suite(after_db)
    payload = {
        "generated_at_utc": now_utc(),
        "before_db": str(before_db),
        "after_db": str(after_db),
        "before": before,
        "after": after,
        "before_summary": before["summary"],
        "after_summary": after["summary"],
        "paired_results": pair_results(before["rows"], after["rows"]),
    }

    write_json(resolve_project_path(args.output_json), payload)
    write_regression_md(resolve_project_path(args.output_md), payload)
    write_fahan_md(output_dir / "fahan_fix_before_after_v1.md", payload)
    write_dandan_md(output_dir / "dandan_alias_fix_before_after_v1.md", payload)
    write_registry_snapshots(output_dir, after)
    write_doc(resolve_project_path(args.doc_path), payload)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"wrote {output_dir / 'fahan_fix_before_after_v1.md'}")
    print(f"wrote {output_dir / 'dandan_alias_fix_before_after_v1.md'}")
    print(f"wrote {args.doc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
