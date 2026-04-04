#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from run_minimal_retrieval import (
    DEFAULT_DB_PATH,
    DEFAULT_EXAMPLES,
    DEFAULT_POLICY_PATH,
    DEFAULT_TOTAL_LIMIT,
    SOURCE_BUDGETS,
    WEIGHT_BONUS,
    RetrievalEngine,
    build_query_terms,
    compute_text_match_score,
    evaluate_topic_consistency,
    baseline_topic_consistency,
    json_dumps,
    log,
    preview_text,
    unique_preserve_order,
)


DEFAULT_EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_RERANK_MODEL = "BAAI/bge-reranker-base"
DEFAULT_CACHE_DIR = "artifacts/hf_cache"
DEFAULT_EXAMPLES_OUT = "artifacts/hybrid_retrieval_examples.json"
DEFAULT_SMOKE_OUT = "artifacts/hybrid_retrieval_smoke_checks.md"
DEFAULT_DENSE_CHUNKS_INDEX = "artifacts/dense_chunks.faiss"
DEFAULT_DENSE_CHUNKS_META = "artifacts/dense_chunks_meta.json"
DEFAULT_DENSE_MAIN_INDEX = "artifacts/dense_main_passages.faiss"
DEFAULT_DENSE_MAIN_META = "artifacts/dense_main_passages_meta.json"

SPARSE_TOP_K = 20
DENSE_CHUNK_TOP_K = 20
DENSE_MAIN_TOP_K = 12
FUSION_TOP_K = 24
RRF_K = 60
RERANK_TOP_N = 18


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dense+sparse hybrid retrieval with rerank on zjshl_mvp.db.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument(
        "--policy-json",
        default=DEFAULT_POLICY_PATH,
        help="Path to layered enablement policy JSON.",
    )
    parser.add_argument("--query", help="Run a single query and print JSON to stdout.")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--rerank-model", default=DEFAULT_RERANK_MODEL, help="CrossEncoder rerank model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--dense-chunks-index", default=DEFAULT_DENSE_CHUNKS_INDEX, help="Path to dense chunks FAISS.")
    parser.add_argument("--dense-chunks-meta", default=DEFAULT_DENSE_CHUNKS_META, help="Path to dense chunks meta.")
    parser.add_argument("--dense-main-index", default=DEFAULT_DENSE_MAIN_INDEX, help="Path to dense main FAISS.")
    parser.add_argument("--dense-main-meta", default=DEFAULT_DENSE_MAIN_META, help="Path to dense main meta.")
    parser.add_argument("--examples-out", default=DEFAULT_EXAMPLES_OUT, help="Where to write example results JSON.")
    parser.add_argument("--smoke-checks-out", default=DEFAULT_SMOKE_OUT, help="Where to write smoke check markdown.")
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=DEFAULT_TOTAL_LIMIT,
        help="Maximum candidate count after rerank and budget trimming.",
    )
    return parser.parse_args()


def prepare_hf_cache(cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_dir))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(cache_dir))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(cache_dir))
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")


def sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1.0 + exp_pos)


def short_candidate_view(rows: list[dict[str, Any]], stage_score_field: str, limit: int = 6) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for row in rows[:limit]:
        summary.append(
            {
                "record_id": row["record_id"],
                "source_object": row["source_object"],
                "chapter_id": row["chapter_id"],
                "topic_consistency": row["topic_consistency"],
                stage_score_field: round(float(row.get(stage_score_field, 0.0)), 6),
                "text_preview": preview_text(row["retrieval_text"]),
            }
        )
    return summary


def is_dense_only_candidate(candidate: dict[str, Any]) -> bool:
    return candidate["text_match_score"] <= 0 and any(
        source in {"dense_chunks", "dense_main_passages"} for source in candidate["stage_sources"]
    )


def has_cached_model(cache_dir: Path, model_name: str) -> bool:
    return (cache_dir / f"models--{model_name.replace('/', '--')}").exists()


def resolve_cached_model_path(cache_dir: Path, model_name: str) -> Path | None:
    snapshots_dir = cache_dir / f"models--{model_name.replace('/', '--')}" / "snapshots"
    if not snapshots_dir.exists():
        return None
    snapshot_dirs = sorted(path for path in snapshots_dir.iterdir() if path.is_dir())
    return snapshot_dirs[-1] if snapshot_dirs else None


def load_sentence_transformer_model(sentence_transformer_cls: Any, model_name: str, cache_dir: Path) -> Any:
    cached_model_path = resolve_cached_model_path(cache_dir, model_name)
    if cached_model_path:
        return sentence_transformer_cls(
            str(cached_model_path),
            cache_folder=str(cache_dir),
            device="cpu",
            local_files_only=True,
        )
    try:
        return sentence_transformer_cls(model_name, cache_folder=str(cache_dir), device="cpu")
    except Exception:
        return sentence_transformer_cls(
            model_name,
            cache_folder=str(cache_dir),
            device="cpu",
            local_files_only=True,
        )


def load_cross_encoder_model(cross_encoder_cls: Any, model_name: str, cache_dir: Path, device: str) -> Any:
    cached_model_path = resolve_cached_model_path(cache_dir, model_name)
    if cached_model_path:
        return cross_encoder_cls(
            str(cached_model_path),
            cache_folder=str(cache_dir),
            device=device,
            local_files_only=True,
        )
    try:
        return cross_encoder_cls(model_name, cache_folder=str(cache_dir), device=device)
    except Exception:
        return cross_encoder_cls(
            model_name,
            cache_folder=str(cache_dir),
            device=device,
            local_files_only=True,
        )


class HybridRetrievalEngine(RetrievalEngine):
    def __init__(
        self,
        *args: Any,
        embed_model: str,
        rerank_model: str,
        cache_dir: Path,
        dense_chunks_index: Path,
        dense_chunks_meta: Path,
        dense_main_index: Path,
        dense_main_meta: Path,
        **kwargs: Any,
    ) -> None:
        self.embed_model_name = embed_model
        self.rerank_model_name = rerank_model
        self.cache_dir = cache_dir
        self.dense_chunks_index_path = dense_chunks_index
        self.dense_chunks_meta_path = dense_chunks_meta
        self.dense_main_index_path = dense_main_index
        self.dense_main_meta_path = dense_main_meta
        self._stage_trace: dict[str, Any] = {}
        super().__init__(*args, **kwargs)

    def __post_init__(self) -> None:
        prepare_hf_cache(self.cache_dir)
        try:
            import faiss
            import numpy as np
            import torch
            from sentence_transformers import CrossEncoder, SentenceTransformer
        except Exception as exc:  # pragma: no cover - dependency guard
            raise SystemExit(
                "Missing hybrid retrieval dependencies. Run with project venv: "
                "./.venv/bin/python run_hybrid_retrieval.py"
            ) from exc

        self.faiss = faiss
        self.np = np
        self.torch = torch
        self.SentenceTransformer = SentenceTransformer
        self.CrossEncoder = CrossEncoder
        super().__post_init__()

        self.record_by_id = {row["record_id"]: row for row in self.unified_rows}
        self.embedder = load_sentence_transformer_model(self.SentenceTransformer, self.embed_model_name, self.cache_dir)
        rerank_device = "mps" if self.torch.backends.mps.is_available() else "cpu"
        self.reranker = load_cross_encoder_model(
            self.CrossEncoder,
            self.rerank_model_name,
            self.cache_dir,
            rerank_device,
        )
        self.rerank_device = rerank_device

        self.dense_chunks_index = self.faiss.read_index(str(self.dense_chunks_index_path))
        self.dense_main_index = self.faiss.read_index(str(self.dense_main_index_path))
        self.dense_chunks_meta = json.loads(self.dense_chunks_meta_path.read_text(encoding="utf-8"))
        self.dense_main_meta = json.loads(self.dense_main_meta_path.read_text(encoding="utf-8"))

    def build_request(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        request = super().build_request(query_text, tight_primary_precision=tight_primary_precision)
        request["retrieval_strategy"] = {
            "type": "hybrid_rrf_rerank",
            "sparse_top_k": SPARSE_TOP_K,
            "dense_chunk_top_k": DENSE_CHUNK_TOP_K,
            "dense_main_top_k": DENSE_MAIN_TOP_K,
            "fusion_top_k": FUSION_TOP_K,
            "rerank_top_n": RERANK_TOP_N,
            "rrf_k": RRF_K,
            "embed_model": self.embed_model_name,
            "rerank_model": self.rerank_model_name,
            "rerank_device": self.rerank_device,
        }
        return request

    def retrieve(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        request = self.build_request(query_text, tight_primary_precision=tight_primary_precision)
        raw_candidates = self._collect_raw_candidates(request)
        resolved = self._resolve_candidates(raw_candidates, request)
        resolved["retrieval_trace"] = {
            **resolved["retrieval_trace"],
            **self._stage_trace,
        }
        slots = self._assemble_slots(resolved)
        mode_info = self._determine_mode(slots)
        return {
            "query_request": request,
            "raw_candidates": raw_candidates,
            "primary_evidence": slots["primary_evidence"],
            "secondary_evidence": slots["secondary_evidence"],
            "risk_materials": slots["risk_materials"],
            "retrieval_trace": resolved["retrieval_trace"],
            "mode": mode_info["mode"],
            "mode_reason": mode_info["mode_reason"],
            "runtime_risk_flags": mode_info["runtime_risk_flags"],
            "annotation_links_enabled": False,
        }

    def _topic_meta(self, request: dict[str, Any], candidate_text: str) -> dict[str, Any]:
        if request["precision_profile"] == "tight_primary":
            return evaluate_topic_consistency(request["query_theme"], candidate_text)
        return baseline_topic_consistency(candidate_text)

    def _base_candidate_from_row(
        self,
        row: dict[str, Any],
        request: dict[str, Any],
        *,
        text_match_score: float = 0.0,
        matched_terms: list[str] | None = None,
    ) -> dict[str, Any]:
        topic_meta = self._topic_meta(request, row["retrieval_text"])
        primary_supports_strong = text_match_score > 0 or topic_meta["topic_consistency"] == "exact_formula_anchor"
        primary_allowed = topic_meta["primary_allowed"] and primary_supports_strong
        candidate = dict(row)
        candidate.update(
            {
                "text_match_score": round(text_match_score, 6),
                "weight_bonus": WEIGHT_BONUS.get(row["default_weight_tier"], 0.0),
                "precision_adjustment": topic_meta["precision_adjustment"],
                "matched_terms": list(matched_terms or []),
                "topic_anchor": topic_meta["topic_anchor"],
                "topic_consistency": topic_meta["topic_consistency"],
                "primary_allowed": primary_allowed,
                "primary_block_reason": (
                    None
                    if primary_allowed
                    else (
                        "dense_only_primary_blocked"
                        if topic_meta["primary_allowed"] and not primary_supports_strong
                        else topic_meta["topic_consistency"]
                    )
                ),
                "sparse_score": 0.0,
                "dense_score": 0.0,
                "dense_rank_score": 0.0,
                "rrf_score": 0.0,
                "rerank_raw_score": None,
                "rerank_score": None,
                "combined_score": 0.0,
                "stage_sources": [],
                "stage_ranks": {},
            }
        )
        return candidate

    def _collect_sparse_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query_focus = request["query_text_normalized"]
        query_terms = build_query_terms(query_focus)
        scored: list[dict[str, Any]] = []

        for row in self.unified_rows:
            if row["source_object"] == "annotation_links":
                continue
            text_score, matched_terms = compute_text_match_score(query_focus, query_terms, row["normalized_text"])
            if text_score <= 0:
                continue
            candidate = self._base_candidate_from_row(row, request, text_match_score=text_score, matched_terms=matched_terms)
            candidate["sparse_score"] = round(
                text_score + candidate["weight_bonus"] + candidate["precision_adjustment"],
                6,
            )
            candidate["stage_sources"] = ["sparse"]
            scored.append(candidate)

        if not scored:
            return []

        max_text_score = max(candidate["text_match_score"] for candidate in scored)
        minimum_text_score = max(2.0, max_text_score * 0.2)
        filtered = [candidate for candidate in scored if candidate["text_match_score"] >= minimum_text_score]
        filtered.sort(
            key=lambda row: (
                -row["sparse_score"],
                -row["text_match_score"],
                -row["weight_bonus"],
                row["record_id"],
            )
        )

        selected: list[dict[str, Any]] = []
        per_source_counts: Counter[str] = Counter()
        for candidate in filtered:
            policy_source_id = candidate["policy_source_id"]
            limit = SOURCE_BUDGETS.get(policy_source_id, SPARSE_TOP_K)
            if per_source_counts[policy_source_id] >= limit:
                continue
            candidate["stage_ranks"]["sparse"] = len(selected) + 1
            selected.append(candidate)
            per_source_counts[policy_source_id] += 1
            if len(selected) >= SPARSE_TOP_K:
                break
        return selected

    def _collect_dense_candidates(
        self,
        request: dict[str, Any],
        *,
        index: Any,
        meta: dict[str, Any],
        top_k: int,
        stage_name: str,
    ) -> list[dict[str, Any]]:
        query_vector = self.embedder.encode(
            [request["query_text"]],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        query_vector = self.np.asarray(query_vector, dtype="float32")
        scores, positions = index.search(query_vector, top_k)

        dense_candidates: list[dict[str, Any]] = []
        raw_scores = [float(score) for score in scores[0].tolist()]
        top_score = max(raw_scores) if raw_scores else 0.0
        minimum_dense_score = max(0.35, top_score * 0.65) if top_score > 0 else 1.0

        for raw_rank, (score, position) in enumerate(zip(scores[0].tolist(), positions[0].tolist()), start=1):
            if position < 0:
                continue
            score = float(score)
            if score < minimum_dense_score:
                continue
            meta_row = meta["records"][position]
            row = self.record_by_id[meta_row["record_id"]]
            candidate = self._base_candidate_from_row(row, request, text_match_score=0.0, matched_terms=[])
            candidate["dense_score"] = round(score, 6)
            candidate["dense_rank_score"] = round(score + candidate["precision_adjustment"] / 100.0, 6)
            candidate["stage_sources"] = [stage_name]
            dense_candidates.append(candidate)

        dense_candidates.sort(
            key=lambda row: (
                -row["dense_rank_score"],
                -row["dense_score"],
                -row["weight_bonus"],
                row["record_id"],
            )
        )

        for rank, candidate in enumerate(dense_candidates, start=1):
            candidate["stage_ranks"][stage_name] = rank
        return dense_candidates

    def _fuse_candidates(self, *stage_groups: tuple[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for stage_name, candidates in stage_groups:
            for rank, candidate in enumerate(candidates, start=1):
                rrf_increment = 1.0 / (RRF_K + rank)
                existing = merged.get(candidate["record_id"])
                if not existing:
                    existing = dict(candidate)
                    existing["stage_sources"] = [stage_name]
                    existing["stage_ranks"] = {stage_name: rank}
                    existing["rrf_score"] = rrf_increment
                    merged[candidate["record_id"]] = existing
                    continue

                existing["rrf_score"] += rrf_increment
                existing["stage_sources"] = unique_preserve_order(existing["stage_sources"] + [stage_name])
                existing["stage_ranks"][stage_name] = rank
                existing["text_match_score"] = max(existing["text_match_score"], candidate["text_match_score"])
                existing["sparse_score"] = max(existing["sparse_score"], candidate["sparse_score"])
                existing["dense_score"] = max(existing["dense_score"], candidate["dense_score"])
                existing["dense_rank_score"] = max(existing["dense_rank_score"], candidate["dense_rank_score"])
                existing["matched_terms"] = unique_preserve_order(existing["matched_terms"] + candidate["matched_terms"])

        fused = list(merged.values())
        fused.sort(
            key=lambda row: (
                -row["rrf_score"],
                -row["sparse_score"],
                -row["dense_rank_score"],
                row["record_id"],
            )
        )
        return fused[:FUSION_TOP_K]

    def _rerank_candidates(self, request: dict[str, Any], fused_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rerank_slice = fused_candidates[:RERANK_TOP_N]
        if not rerank_slice:
            return []

        pairs = [(request["query_text"], candidate["retrieval_text"]) for candidate in rerank_slice]
        raw_scores = self.reranker.predict(pairs, batch_size=8, show_progress_bar=False)

        for candidate, raw_score in zip(rerank_slice, raw_scores.tolist(), strict=False):
            candidate["rerank_raw_score"] = round(float(raw_score), 6)
            candidate["rerank_score"] = round(sigmoid(float(raw_score)), 6)
            candidate["combined_score"] = round(
                candidate["rerank_score"] * 1000.0
                + candidate["rrf_score"] * 100.0
                + candidate["sparse_score"]
                + candidate["dense_rank_score"] * 10.0
                + candidate["weight_bonus"],
                6,
            )

        ordered_reranked = sorted(
            rerank_slice,
            key=lambda row: (
                -(row["rerank_score"] or 0.0),
                -row["rrf_score"],
                -row["sparse_score"],
                -row["dense_rank_score"],
                row["record_id"],
            ),
        )

        remainder = fused_candidates[RERANK_TOP_N:]
        for candidate in remainder:
            candidate["combined_score"] = round(
                candidate["rrf_score"] * 100.0
                + candidate["sparse_score"]
                + candidate["dense_rank_score"] * 10.0
                + candidate["weight_bonus"],
                6,
            )

        return ordered_reranked + remainder

    def _passes_final_candidate_gate(self, request: dict[str, Any], candidate: dict[str, Any]) -> bool:
        if not is_dense_only_candidate(candidate):
            return True

        if request["query_theme"]["type"] == "formula_name":
            return candidate["topic_consistency"] == "exact_formula_anchor"

        return candidate["dense_score"] >= 0.58 and (candidate["rerank_score"] or 0.0) >= 0.62

    def _collect_raw_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        sparse_candidates = self._collect_sparse_candidates(request)
        dense_chunk_candidates = self._collect_dense_candidates(
            request,
            index=self.dense_chunks_index,
            meta=self.dense_chunks_meta,
            top_k=DENSE_CHUNK_TOP_K,
            stage_name="dense_chunks",
        )
        dense_main_candidates = self._collect_dense_candidates(
            request,
            index=self.dense_main_index,
            meta=self.dense_main_meta,
            top_k=DENSE_MAIN_TOP_K,
            stage_name="dense_main_passages",
        )
        fused_candidates = self._fuse_candidates(
            ("sparse", sparse_candidates),
            ("dense_chunks", dense_chunk_candidates),
            ("dense_main_passages", dense_main_candidates),
        )
        reranked_candidates = self._rerank_candidates(request, fused_candidates)

        selected: list[dict[str, Any]] = []
        per_source_counts: Counter[str] = Counter()
        for candidate in reranked_candidates:
            if not self._passes_final_candidate_gate(request, candidate):
                continue
            policy_source_id = candidate["policy_source_id"]
            limit = SOURCE_BUDGETS.get(policy_source_id, self.candidate_limit)
            if per_source_counts[policy_source_id] >= limit:
                continue
            selected.append(candidate)
            per_source_counts[policy_source_id] += 1
            if len(selected) >= self.candidate_limit:
                break

        self._stage_trace = {
            "annotation_links_disabled": True,
            "dense_models": {
                "embed_model": self.embed_model_name,
                "rerank_model": self.rerank_model_name,
                "rerank_device": self.rerank_device,
            },
            "sparse_top_candidates": short_candidate_view(sparse_candidates, "sparse_score"),
            "dense_top_candidates": {
                "dense_chunks": short_candidate_view(dense_chunk_candidates, "dense_score"),
                "dense_main_passages": short_candidate_view(dense_main_candidates, "dense_score"),
            },
            "fusion_top_candidates": [
                {
                    "record_id": row["record_id"],
                    "source_object": row["source_object"],
                    "topic_consistency": row["topic_consistency"],
                    "rrf_score": round(row["rrf_score"], 6),
                    "stage_sources": row["stage_sources"],
                }
                for row in fused_candidates[:6]
            ],
            "rerank_top_candidates": [
                {
                    "record_id": row["record_id"],
                    "source_object": row["source_object"],
                    "topic_consistency": row["topic_consistency"],
                    "rerank_score": row["rerank_score"],
                    "combined_score": row["combined_score"],
                }
                for row in reranked_candidates[:6]
            ],
        }
        return selected


def build_examples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    from datetime import datetime, timezone

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "examples": results,
    }


def build_smoke_markdown(command: str, results: list[dict[str, Any]]) -> str:
    strong = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    weak = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    refuse = next(result for result in results if result["example_id"] == "refuse_no_match")

    strong_primary_ids = [row["record_id"] for row in strong["primary_evidence"]]
    gating_preserved = (
        all(row["source_object"] == "main_passages" for row in strong["primary_evidence"])
        and all(row["source_object"] != "annotations" for row in strong["primary_evidence"])
        and all(row["source_object"] != "passages" for row in strong["primary_evidence"])
        and all(row["source_object"] != "ambiguous_passages" for row in strong["primary_evidence"])
    )

    lines = [
        "# Hybrid Retrieval Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 结论",
        "",
    ]

    for result in results:
        lines.append(
            f"- `{result['query_request']['query_text']}` -> mode=`{result['mode']}`, "
            f"primary={len(result['primary_evidence'])}, "
            f"secondary={len(result['secondary_evidence'])}, "
            f"review={len(result['risk_materials'])}"
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- strong_precision_patch_preserved: `{'ZJSHL-CH-009' not in ''.join(strong_primary_ids)}`",
            f"- evidence_gating_preserved: `{gating_preserved}`",
            f"- annotation_links_disabled: `{all(not result['annotation_links_enabled'] for result in results)}`",
        ]
    )

    for result in results:
        trace = result["retrieval_trace"]
        lines.extend(
            [
                "",
                f"## Query: {result['query_request']['query_text']}",
                "",
                f"- mode: `{result['mode']}`",
                f"- mode_reason: {result['mode_reason']}",
                f"- runtime_risk_flags: `{json.dumps(result['runtime_risk_flags'], ensure_ascii=False)}`",
                "",
                "### Sparse Top Candidates",
                "",
                json_dumps(trace["sparse_top_candidates"]) if trace["sparse_top_candidates"] else "_no rows_",
                "",
                "### Dense Top Candidates",
                "",
                json_dumps(trace["dense_top_candidates"]),
                "",
                "### Fusion Top Candidates",
                "",
                json_dumps(trace["fusion_top_candidates"]) if trace["fusion_top_candidates"] else "_no rows_",
                "",
                "### Rerank Top Candidates",
                "",
                json_dumps(trace["rerank_top_candidates"]) if trace["rerank_top_candidates"] else "_no rows_",
                "",
                "### Final Evidence Summary",
                "",
                json_dumps(
                    {
                        "primary_evidence": [row["record_id"] for row in result["primary_evidence"]],
                        "secondary_evidence": [row["record_id"] for row in result["secondary_evidence"]],
                        "review_materials": [row["record_id"] for row in result["risk_materials"]],
                    }
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Checks",
            "",
            f"- weak_review_mode_kept: `{weak['mode'] == 'weak_with_review_notice'}`",
            f"- refuse_mode_kept: `{refuse['mode'] == 'refuse'}`",
        ]
    )

    return "\n".join(lines) + "\n"


def run_examples(engine: HybridRetrievalEngine) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in DEFAULT_EXAMPLES:
        result = engine.retrieve(example["query_text"])
        result["example_id"] = example["example_id"]
        result["expected_mode"] = example["expected_mode"]
        results.append(result)
    return results


def assert_smoke_expectations(results: list[dict[str, Any]]) -> None:
    mode_counts = Counter(result["mode"] for result in results)
    if mode_counts["strong"] < 1:
        raise AssertionError("expected at least one strong example")
    if mode_counts["weak_with_review_notice"] < 1:
        raise AssertionError("expected at least one weak_with_review_notice example")
    if mode_counts["refuse"] < 1:
        raise AssertionError("expected at least one refuse example")

    strong_result = next(result for result in results if result["example_id"] == "strong_chunk_backref")
    if strong_result["mode"] != "strong":
        raise AssertionError("strong_chunk_backref mode regressed")
    if any("ZJSHL-CH-009" in row["chapter_id"] for row in strong_result["primary_evidence"]):
        raise AssertionError("葛根黄芩黄连汤方-related primary evidence regressed")
    if any(row["source_object"] != "main_passages" for row in strong_result["primary_evidence"]):
        raise AssertionError("primary_evidence must remain main_passages only")

    weak_result = next(result for result in results if result["example_id"] == "weak_with_review_notice")
    if weak_result["mode"] != "weak_with_review_notice":
        raise AssertionError("weak_with_review_notice mode regressed")
    if weak_result["primary_evidence"]:
        raise AssertionError("weak_with_review_notice should not contain primary evidence")

    refuse_result = next(result for result in results if result["example_id"] == "refuse_no_match")
    if refuse_result["mode"] != "refuse":
        raise AssertionError("refuse mode regressed")

    for result in results:
        if result["annotation_links_enabled"]:
            raise AssertionError("annotation_links should remain disabled")
        if any(row["source_object"] == "annotation_links" for row in result["raw_candidates"]):
            raise AssertionError("annotation_links leaked into raw candidates")


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

    engine = HybridRetrievalEngine(
        db_path=db_path,
        policy_path=policy_path,
        candidate_limit=args.candidate_limit,
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
        log(f"[2/4] Loaded hybrid retrieval assets from {db_path} and dense index files")

        if args.query:
            result = engine.retrieve(args.query)
            print(json_dumps(result))
            log("[3/4] Ran single-query hybrid retrieval")
            log("[4/4] No artifact files updated in single-query mode")
            return 0

        results = run_examples(engine)
        assert_smoke_expectations(results)
        examples_out.write_text(json_dumps(build_examples_payload(results)) + "\n", encoding="utf-8")
        command = f"{Path(sys.executable).name} {Path(__file__).name}"
        smoke_out.write_text(build_smoke_markdown(command, results), encoding="utf-8")
        log("[3/4] Ran hybrid retrieval examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out} and {smoke_out}")
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
