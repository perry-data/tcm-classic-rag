#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from backend.retrieval.minimal import compact_text, preview_text  # noqa: E402
from export_query_traces import (  # noqa: E402
    DEFAULT_GOLDSET,
    compact_row,
    instantiate_assembler,
    resolve_project_path,
    summarize_evidence_item,
    summarize_retrieval_call,
    trace_query,
    write_json,
)


DEFAULT_OUTPUT_JSON = "artifacts/data_diagnostics/suspected_failure_pool_v1.json"
DEFAULT_OUTPUT_MD = "artifacts/data_diagnostics/suspected_failure_pool_v1.md"
FORMULA_RE = re.compile(r"[\u4e00-\u9fff]{1,16}(?:汤方|散方|丸方|饮方|汤|散|丸|饮|方)")
REFUSAL_HINTS = (
    "能不能用",
    "我",
    "孩子",
    "老人",
    "孕妇",
    "发烧",
    "腹泻",
    "吃多少",
    "剂量",
    "疗程",
    "量子",
    "新冠",
    "糖尿病",
    "高血压",
    "癌症",
    "哪个好",
    "哪个更好",
)
SOURCE_LOOKUP_HINTS = ("条文", "原文", "在哪", "出处", "第几条")
FORMULA_EFFECT_HINTS = ("作用", "干什么", "治什么", "主治", "有什么用", "适用")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_formula_name(query: str) -> str | None:
    match = FORMULA_RE.search(query)
    if not match:
        return None
    raw = match.group(0)
    if raw.endswith("方"):
        return raw
    if raw.endswith(("汤", "散", "丸", "饮")):
        return raw + "方"
    return raw


def candidate_id(query: str) -> str:
    return "cand_" + hashlib.sha1(query.encode("utf-8")).hexdigest()[:10]


def dedupe_query_specs(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for spec in specs:
        query = str(spec.get("query") or "").strip()
        if not query or query in seen:
            continue
        seen.add(query)
        spec = dict(spec)
        spec["candidate_id"] = spec.get("candidate_id") or candidate_id(query)
        deduped.append(spec)
    return deduped


def build_candidate_queries(goldset_path: Path, max_candidates: int) -> list[dict[str, Any]]:
    goldset = load_json(goldset_path)
    items = goldset.get("items") or []
    specs: list[dict[str, Any]] = []

    for item in items:
        query = str(item.get("query") or "").strip()
        if not query:
            continue
        specs.append(
            {
                "query": query,
                "source": "goldset_original",
                "source_question_id": item.get("question_id"),
                "question_type": item.get("question_type"),
                "expected_mode": item.get("expected_mode"),
                "gold_record_ids": item.get("gold_record_ids") or [],
            }
        )

    formulas: list[str] = []
    terms: list[str] = []
    comparisons: list[str] = []
    for item in items:
        query = str(item.get("query") or "")
        question_type = item.get("question_type")
        formula = extract_formula_name(query)
        if formula:
            formulas.append(formula)
        if question_type == "meaning_explanation":
            terms.append(query.replace("是什么意思？", "").replace("是什么意思", "").strip("？?"))
        if question_type == "comparison":
            comparisons.append(query)

    for formula in list(dict.fromkeys(formulas))[:18]:
        for template in (
            "{x}在哪一条？",
            "{x}原文怎么说？",
            "{x}是干什么的？",
            "{x}有什么用？",
            "初学者怎么理解{x}？",
            "刘渡舟怎么讲{x}？",
            "郝万山怎么看{x}？",
        ):
            specs.append(
                {
                    "query": template.format(x=formula),
                    "source": "formula_common_rewrite",
                    "target_formula": formula,
                    "question_type": "auto_formula_rewrite",
                    "expected_mode": "strong" if "怎么讲" not in template and "怎么看" not in template else None,
                }
            )

    for term in list(dict.fromkeys(terms))[:16]:
        if not term:
            continue
        for template in (
            "这句话怎么理解：{x}？",
            "初学者怎么理解{x}？",
        ):
            specs.append(
                {
                    "query": template.format(x=term),
                    "source": "meaning_oral_rewrite",
                    "question_type": "auto_meaning_rewrite",
                    "expected_mode": None,
                }
            )

    for query in list(dict.fromkeys(comparisons))[:10]:
        specs.append(
            {
                "query": query.replace("区别是什么", "有什么不一样"),
                "source": "comparison_oral_rewrite",
                "question_type": "auto_comparison_rewrite",
                "expected_mode": None,
            }
        )

    for query in (
        "两位老师对太阳病提纲的看法有什么不同？",
        "刘渡舟怎么看小柴胡汤？",
        "郝万山怎么讲桂枝汤？",
        "名家怎么解释少阴病？",
        "初学者学习伤寒论先抓什么？",
    ):
        specs.append({"query": query, "source": "commentarial_view_seed", "question_type": "commentarial_view"})

    for query in (
        "我发烧了能不能用麻黄汤？",
        "小孩咳嗽能吃小青龙汤吗？",
        "孕妇能不能用桂枝汤？",
        "大承气汤和西药退烧药哪个好？",
        "糖尿病可以用白虎汤治疗吗？",
        "书中有没有提到量子纠缠？",
    ):
        specs.append({"query": query, "source": "refusal_boundary_seed", "question_type": "refusal", "expected_mode": "refuse"})

    deduped = dedupe_query_specs(specs)
    return deduped[:max_candidates]


class CanonicalIndex:
    def __init__(self, db_path: Path) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.main_rows = [dict(row) for row in self.conn.execute(
            "SELECT record_id, passage_id, text, normalized_text, chapter_id, chapter_name FROM records_main_passages"
        )]
        for row in self.main_rows:
            row["_compact"] = compact_text(row.get("normalized_text") or row.get("text") or "")

    def close(self) -> None:
        self.conn.close()

    def exact_hits(self, query: str, formula: str | None = None) -> list[dict[str, Any]]:
        compact_query = compact_text(query)
        anchors = [compact_text(formula)] if formula else []
        if not anchors:
            focus = query
            for hint in SOURCE_LOOKUP_HINTS + FORMULA_EFFECT_HINTS + ("是什么", "什么意思", "怎么理解", "初学者"):
                focus = focus.replace(hint, "")
            focus_compact = compact_text(focus)
            if len(focus_compact) >= 3:
                anchors.append(focus_compact)
        hits: list[dict[str, Any]] = []
        for row in self.main_rows:
            row_compact = row["_compact"]
            if any(anchor and anchor in row_compact for anchor in anchors):
                hits.append(row)
            elif compact_query and len(compact_query) >= 8 and compact_query in row_compact:
                hits.append(row)
            if len(hits) >= 12:
                break
        return hits


def flatten_candidates(trace_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for call in trace_result.get("retrieval_calls") or []:
        rows.extend(call.get("raw_candidates_after_final_gate_top") or [])
        rows.extend(call.get("sparse_top_k") or [])
        for dense_rows in (call.get("dense_top_k") or {}).values():
            rows.extend(dense_rows or [])
        rows.extend(call.get("rerank_top_k") or [])
    return rows


def flatten_commentarial_items(trace_result: dict[str, Any]) -> list[dict[str, Any]]:
    commentarial = (trace_result.get("final_response") or {}).get("commentarial") or {}
    rows: list[dict[str, Any]] = []
    for section in commentarial.get("sections") or []:
        for item in section.get("items") or []:
            enriched = dict(item)
            enriched["section_id"] = section.get("section_id")
            enriched["section_title"] = section.get("title")
            enriched["collapsed_by_default"] = section.get("collapsed_by_default")
            rows.append(enriched)
    return rows


def is_precise_lookup_query(query: str, formula: str | None) -> bool:
    if formula and any(hint in query for hint in SOURCE_LOOKUP_HINTS):
        return True
    if re.search(r"第\s*\d{1,3}\s*[上下AaBb]?\s*条", query):
        return True
    return False


def analyze_signals(
    spec: dict[str, Any],
    trace_result: dict[str, Any],
    canonical_hits: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    query = spec["query"]
    formula = spec.get("target_formula") or extract_formula_name(query)
    final = trace_result.get("final_response") or {}
    answer_mode = final.get("answer_mode")
    primary = final.get("primary_evidence") or []
    citations = final.get("citations") or []
    top_candidates = flatten_candidates(trace_result)
    commentarial_items = flatten_commentarial_items(trace_result)
    signals: list[dict[str, Any]] = []

    if canonical_hits and not primary:
        signals.append(
            {
                "signal_id": "canonical_exact_hit_but_primary_empty",
                "description": "query has lexical/formula hits in canonical main passages, but final primary_evidence is empty.",
                "evidence": [row["record_id"] for row in canonical_hits[:5]],
            }
        )

    if is_precise_lookup_query(query, formula) and answer_mode != "strong":
        signals.append(
            {
                "signal_id": "precise_lookup_degraded",
                "description": "precise formula/passage lookup did not return strong mode.",
                "evidence": {"answer_mode": answer_mode, "target_formula": formula},
            }
        )

    if formula:
        formula_compact = compact_text(formula)
        off_topic = [
            row
            for row in top_candidates
            if row.get("topic_consistency") in {"different_formula_anchor", "expanded_formula_anchor"}
            or (
                row.get("topic_anchor")
                and compact_text(str(row.get("topic_anchor"))) != formula_compact
                and str(row.get("topic_anchor")).endswith("方")
            )
        ][:6]
        if off_topic:
            signals.append(
                {
                    "signal_id": "formula_cross_target_candidates",
                    "description": "target formula query has high-position candidates anchored to another formula or expanded formula.",
                    "evidence": off_topic,
                }
            )

    if canonical_hits:
        hit_ids = {row["record_id"] for row in canonical_hits}
        citation_ids = {row.get("record_id") for row in citations}
        if citations and not citation_ids.intersection(hit_ids):
            signals.append(
                {
                    "signal_id": "exact_hit_but_citation_misaligned",
                    "description": "canonical exact hits exist, but final citations do not intersect those hit records.",
                    "evidence": {
                        "canonical_hit_ids": list(hit_ids)[:8],
                        "citation_ids": list(citation_ids)[:8],
                    },
                }
            )
        if not citations and answer_mode != "refuse":
            signals.append(
                {
                    "signal_id": "exact_hit_but_no_citation",
                    "description": "canonical exact hits exist, but non-refuse answer has no citation.",
                    "evidence": {"canonical_hit_ids": list(hit_ids)[:8]},
                }
            )

    risk_like = [
        row
        for row in top_candidates[:12]
        if row.get("source_object") in {"passages", "ambiguous_passages"}
        or row.get("display_allowed") == "risk_only"
        or "ambiguous" in json.dumps(row.get("risk_flag") or "", ensure_ascii=False)
    ]
    if len(risk_like) >= 4:
        signals.append(
            {
                "signal_id": "high_risk_candidate_dominance",
                "description": "top candidates are dominated by risk-only, ambiguous, or weak-anchor objects.",
                "evidence": risk_like[:6],
            }
        )

    if canonical_hits and answer_mode in {"weak_with_review_notice", "refuse"} and len(compact_text(query)) <= 18:
        signals.append(
            {
                "signal_id": "simple_query_over_degraded",
                "description": "short/simple query has canonical hits but degraded to weak/refuse.",
                "evidence": {"answer_mode": answer_mode, "query_length_compact": len(compact_text(query))},
            }
        )

    if spec.get("expected_mode") == "refuse" or any(hint in query for hint in REFUSAL_HINTS):
        if answer_mode != "refuse":
            signals.append(
                {
                    "signal_id": "refusal_boundary_missed",
                    "description": "query has refusal-boundary hints but system returned a non-refuse answer.",
                    "evidence": {"answer_mode": answer_mode},
                }
            )

    uncertain_commentarial = [
        item
        for item in commentarial_items
        if item.get("needs_manual_anchor_review")
        or item.get("needs_manual_content_review")
        or item.get("low_confidence_commentarial_unit")
        or item.get("anchor_type") == "theme"
        or not item.get("resolved_primary_anchor_passage_ids")
    ][:5]
    if uncertain_commentarial:
        signals.append(
            {
                "signal_id": "commentarial_uncertain_scope_displayed",
                "description": "commentarial material is displayed with theme/uncertain/no-primary-anchor signals; current data lacks unit_scope_type to separate incidental mentions.",
                "evidence": uncertain_commentarial,
            }
        )

    if not signals:
        return [], ""

    reason_parts = []
    if canonical_hits and not primary:
        reason_parts.append("canonical 命中但主证据为空")
    if any(signal["signal_id"] == "formula_cross_target_candidates" for signal in signals):
        reason_parts.append("存在串方候选风险")
    if any(signal["signal_id"] == "refusal_boundary_missed" for signal in signals):
        reason_parts.append("拒答边界可能漏判")
    if any(signal["signal_id"] == "commentarial_uncertain_scope_displayed" for signal in signals):
        reason_parts.append("名家材料范围类型不清")
    if not reason_parts:
        reason_parts.append("命中了一个或多个自动疑似失败信号")
    return signals, "；".join(reason_parts)


def current_output_summary(trace_result: dict[str, Any]) -> dict[str, Any]:
    final = trace_result.get("final_response") or {}
    return {
        "answer_mode": final.get("answer_mode"),
        "answer_text_excerpt": final.get("answer_text_excerpt"),
        "primary_record_ids": [row.get("record_id") for row in final.get("primary_evidence") or []],
        "secondary_record_ids": [row.get("record_id") for row in final.get("secondary_evidence") or []],
        "review_record_ids": [row.get("record_id") for row in final.get("review_materials") or []],
        "citation_record_ids": [row.get("record_id") for row in final.get("citations") or []],
        "commentarial_route": ((final.get("commentarial") or {}).get("route")),
        "commentarial_item_count": sum(
            len(section.get("items") or [])
            for section in ((final.get("commentarial") or {}).get("sections") or [])
        ),
    }


def build_markdown(pool: dict[str, Any]) -> str:
    lines = [
        "# 高疑似失败样本候选池 v1",
        "",
        f"- generated_at_utc: `{pool['generated_at_utc']}`",
        f"- scanned_query_count: `{pool['scanned_query_count']}`",
        f"- suspected_candidate_count: `{pool['suspected_candidate_count']}`",
        "- 判定边界: 本文件只表示自动规则筛出的“高疑似失败候选”，不表示人工已确认失败。",
        "",
        "## Signal Counts",
        "",
    ]
    for signal_id, count in pool.get("signal_counts", {}).items():
        lines.append(f"- `{signal_id}`: {count}")
    lines.extend(["", "## Candidates", ""])
    for index, item in enumerate(pool.get("suspected_candidates") or [], start=1):
        signal_ids = [signal["signal_id"] for signal in item.get("signals") or []]
        summary = item.get("current_output_summary") or {}
        lines.extend(
            [
                f"### {index}. {item['query']}",
                "",
                f"- candidate_id: `{item['candidate_id']}`",
                f"- source: `{item.get('source')}`",
                f"- answer_mode: `{summary.get('answer_mode')}`",
                f"- signals: `{', '.join(signal_ids)}`",
                f"- citations: `{json.dumps(summary.get('citation_record_ids') or [], ensure_ascii=False)}`",
                f"- primary: `{json.dumps(summary.get('primary_record_ids') or [], ensure_ascii=False)}`",
                f"- why_review: {item.get('why_review')}",
                f"- answer_excerpt: {summary.get('answer_text_excerpt') or ''}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a suspected failure candidate pool from existing and expanded queries.")
    parser.add_argument("--goldset", default=DEFAULT_GOLDSET)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--max-candidates", type=int, default=80)
    parser.add_argument("--max-suspected", type=int, default=40)
    parser.add_argument("--db-path", default="artifacts/zjshl_v1.db")
    parser.add_argument("--policy-json", default="config/layered_enablement_policy.json")
    parser.add_argument("--embed-model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--rerank-model", default="BAAI/bge-reranker-base")
    parser.add_argument("--cache-dir", default="artifacts/hf_cache")
    parser.add_argument("--dense-chunks-index", default="artifacts/dense_chunks.faiss")
    parser.add_argument("--dense-chunks-meta", default="artifacts/dense_chunks_meta.json")
    parser.add_argument("--dense-main-index", default="artifacts/dense_main_passages.faiss")
    parser.add_argument("--dense-main-meta", default="artifacts/dense_main_passages_meta.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["PERF_DISABLE_LLM"] = "1"
    os.environ.setdefault("TCM_RAG_LLM_ENABLED", "false")

    goldset_path = resolve_project_path(args.goldset)
    db_path = resolve_project_path(args.db_path)
    query_specs = build_candidate_queries(goldset_path, args.max_candidates)
    canonical_index = CanonicalIndex(db_path)
    assembler = instantiate_assembler(args)
    suspected: list[dict[str, Any]] = []
    scanned: list[dict[str, Any]] = []
    try:
        for index, spec in enumerate(query_specs, start=1):
            trace_spec = {
                "trace_id": spec["candidate_id"],
                "category": spec.get("question_type") or "candidate",
                "query": spec["query"],
            }
            trace_result = trace_query(assembler, trace_spec)
            formula = spec.get("target_formula") or extract_formula_name(spec["query"])
            canonical_hits = canonical_index.exact_hits(spec["query"], formula=formula)
            signals, why_review = analyze_signals(spec, trace_result, canonical_hits)
            scanned.append(
                {
                    "candidate_id": spec["candidate_id"],
                    "query": spec["query"],
                    "source": spec.get("source"),
                    "signal_count": len(signals),
                    "answer_mode": (trace_result.get("final_response") or {}).get("answer_mode"),
                }
            )
            if not signals:
                continue
            item = {
                "candidate_id": spec["candidate_id"],
                "query": spec["query"],
                "source": spec.get("source"),
                "source_question_id": spec.get("source_question_id"),
                "question_type": spec.get("question_type"),
                "target_formula": formula,
                "expected_mode": spec.get("expected_mode"),
                "current_output_summary": current_output_summary(trace_result),
                "signals": signals,
                "top_candidates": [
                    compact_row(row)
                    for row in flatten_candidates(trace_result)[:12]
                ],
                "canonical_exact_hits": [
                    {
                        "record_id": row["record_id"],
                        "passage_id": row["passage_id"],
                        "chapter_id": row["chapter_id"],
                        "chapter_name": row["chapter_name"],
                        "text_preview": preview_text(row["text"], limit=140),
                    }
                    for row in canonical_hits[:8]
                ],
                "citations": (trace_result.get("final_response") or {}).get("citations") or [],
                "why_review": why_review,
            }
            suspected.append(item)
    finally:
        assembler.close()
        canonical_index.close()

    suspected.sort(
        key=lambda item: (
            -len(item.get("signals") or []),
            item.get("current_output_summary", {}).get("answer_mode") == "strong",
            item["candidate_id"],
        )
    )
    suspected = suspected[: args.max_suspected]
    signal_counts = Counter(
        signal["signal_id"]
        for item in suspected
        for signal in item.get("signals") or []
    )
    payload = {
        "generated_at_utc": now_utc(),
        "scope_note": "Automatic suspected-failure candidate pool only. These rows require human review and are not proven failures.",
        "runtime_flags": {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "TCM_RAG_LLM_ENABLED": os.environ.get("TCM_RAG_LLM_ENABLED"),
        },
        "candidate_sources": [
            "goldset_original",
            "formula_common_rewrite",
            "meaning_oral_rewrite",
            "comparison_oral_rewrite",
            "commentarial_view_seed",
            "refusal_boundary_seed",
        ],
        "scanned_query_count": len(query_specs),
        "suspected_candidate_count": len(suspected),
        "signal_counts": dict(sorted(signal_counts.items())),
        "scanned_summary": scanned,
        "suspected_candidates": suspected,
    }
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    write_json(output_json, payload)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(build_markdown(payload), encoding="utf-8")
    print(f"[data-diagnostics] scanned={len(query_specs)} suspected={len(suspected)}")
    print(f"[data-diagnostics] wrote {output_json}")
    print(f"[data-diagnostics] wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
