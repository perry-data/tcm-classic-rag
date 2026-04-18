#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
from collections import Counter
from pathlib import Path
from typing import Any

from backend.perf import load_perf_settings, record_metadata, stage_timer
from backend.retrieval.minimal import (
    DEFAULT_DB_PATH,
    DEFAULT_EXAMPLES,
    DEFAULT_POLICY_PATH,
    DEFAULT_TOTAL_LIMIT,
    SOURCE_BUDGETS,
    WEIGHT_BONUS,
    RetrievalEngine,
    build_query_terms,
    compact_text,
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
DEFAULT_FTS_EXAMPLES_OUT = "artifacts/fts5_retrieval_examples.json"
DEFAULT_FTS_SMOKE_OUT = "artifacts/fts5_smoke_checks.md"
DEFAULT_DENSE_CHUNKS_INDEX = "artifacts/dense_chunks.faiss"
DEFAULT_DENSE_CHUNKS_META = "artifacts/dense_chunks_meta.json"
DEFAULT_DENSE_MAIN_INDEX = "artifacts/dense_main_passages.faiss"
DEFAULT_DENSE_MAIN_META = "artifacts/dense_main_passages_meta.json"
DEFAULT_CONTROLLED_REPLAY_CONFIG = "config/controlled_replay/fahan_main_passages_allowlist_v1.json"
DEFAULT_FULL_MAIN_PASSAGES_PATH = "data/processed/zjshl_dataset_v2/main_passages.json"

SPARSE_TOP_K = 20
DENSE_CHUNK_TOP_K = 20
DENSE_MAIN_TOP_K = 12
FUSION_TOP_K = 24
RRF_K = 60
RERANK_TOP_N = 18
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPARSE_FTS_TABLE = "retrieval_sparse_fts"
SPARSE_FTS_TOKENIZER = "trigram"
SPARSE_FTS_QUERY_LIMIT = SPARSE_TOP_K * 8
FTS5_COMPARISON_EXAMPLES = DEFAULT_EXAMPLES + [
    {
        "example_id": "extra_formula_exact",
        "query_text": "桂枝汤方的条文是什么？",
        "expected_mode": None,
    }
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dense+sparse hybrid retrieval with rerank on zjshl_v1.db.")
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
        "--fts-examples-out",
        default=DEFAULT_FTS_EXAMPLES_OUT,
        help="Where to write FTS5/BM25 sparse comparison JSON.",
    )
    parser.add_argument(
        "--fts-smoke-checks-out",
        default=DEFAULT_FTS_SMOKE_OUT,
        help="Where to write FTS5/BM25 sparse comparison markdown.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=DEFAULT_TOTAL_LIMIT,
        help="Maximum candidate count after rerank and budget trimming.",
    )
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def ensure_runtime_file(path: Path, description: str, recovery_hint: str) -> None:
    if path.exists():
        return
    raise SystemExit(f"Missing {description}: {path}\n{recovery_hint}")


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


def env_flag_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


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


def sparse_candidate_view(rows: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for row in rows[:limit]:
        summary.append(
            {
                "record_id": row["record_id"],
                "source_object": row["source_object"],
                "chapter_id": row["chapter_id"],
                "topic_consistency": row["topic_consistency"],
                "text_match_score": round(float(row.get("text_match_score", 0.0)), 6),
                "sparse_score": round(float(row.get("sparse_score", 0.0)), 6),
                "sparse_bm25_raw": row.get("sparse_bm25_raw"),
                "sparse_bm25_score": row.get("sparse_bm25_score"),
                "matched_terms": list(row.get("matched_terms", [])),
                "text_preview": preview_text(row["retrieval_text"]),
            }
        )
    return summary


def build_sparse_fts_match_terms(query_focus: str, limit: int = 14) -> list[str]:
    if not query_focus:
        return []
    ordered_terms = [query_focus]
    ordered_terms.extend(term for term in build_query_terms(query_focus) if len(term) >= 3)
    terms: list[str] = []
    for term in unique_preserve_order(ordered_terms):
        if len(term) < 3:
            continue
        terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def quote_fts_phrase(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def build_sparse_fts_match_expression(query_focus: str) -> dict[str, Any]:
    terms = build_sparse_fts_match_terms(query_focus)
    return {
        "query_focus": query_focus,
        "match_terms": terms,
        "match_expression": " OR ".join(quote_fts_phrase(term) for term in terms),
    }


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
        self._query_vector_cache: dict[str, Any] = {}
        self._query_vector_cache_lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def __post_init__(self) -> None:
        ensure_runtime_file(self.db_path, "SQLite runtime database", "Run `python scripts/build_v1_database.py`.")
        ensure_runtime_file(
            self.dense_chunks_index_path,
            "dense chunks FAISS index",
            "Run `python scripts/build_dense_index.py` before starting the API on a fresh clone.",
        )
        ensure_runtime_file(
            self.dense_main_index_path,
            "dense main passages FAISS index",
            "Run `python scripts/build_dense_index.py` before starting the API on a fresh clone.",
        )
        ensure_runtime_file(
            self.dense_chunks_meta_path,
            "dense chunks meta JSON",
            "Run `python scripts/build_dense_index.py` before starting the API on a fresh clone.",
        )
        ensure_runtime_file(
            self.dense_main_meta_path,
            "dense main passages meta JSON",
            "Run `python scripts/build_dense_index.py` before starting the API on a fresh clone.",
        )
        prepare_hf_cache(self.cache_dir)
        try:
            import faiss
            import numpy as np
            import torch
            from sentence_transformers import CrossEncoder, SentenceTransformer
        except Exception as exc:  # pragma: no cover - dependency guard
            raise SystemExit(
                "Missing hybrid retrieval dependencies. Install them first with "
                "`python -m pip install -r requirements.txt`, then run "
                "`python -m backend.retrieval.hybrid`."
            ) from exc

        self.faiss = faiss
        self.np = np
        self.torch = torch
        self.SentenceTransformer = SentenceTransformer
        self.CrossEncoder = CrossEncoder
        super().__post_init__()

        self._chapter_name_by_id = {
            row["chapter_id"]: row["chapter_name"]
            for row in self.unified_rows
            if row.get("chapter_id") and row.get("chapter_name")
        }
        self.controlled_replay_config = self._load_controlled_replay_config()
        self.controlled_replay_enabled = self._is_controlled_replay_enabled(self.controlled_replay_config)
        self.controlled_replay_rows = self._build_controlled_replay_rows(self.controlled_replay_config)
        self.record_by_id = {row["record_id"]: row for row in self.unified_rows}
        self.record_by_id.update({row["record_id"]: row for row in self.controlled_replay_rows})
        self._ensure_sparse_fts_index()
        self.embedder = load_sentence_transformer_model(self.SentenceTransformer, self.embed_model_name, self.cache_dir)
        mps_backend = getattr(self.torch.backends, "mps", None)
        rerank_device = "mps" if mps_backend is not None and mps_backend.is_available() else "cpu"
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

    def _load_controlled_replay_config(self) -> dict[str, Any]:
        config_path = resolve_project_path(DEFAULT_CONTROLLED_REPLAY_CONFIG)
        if not config_path.exists():
            return {
                "experiment_id": "fahan_main_controlled_replay_v1",
                "enabled_by_default": False,
                "env_flag": "TCM_ENABLE_FAHAN_CONTROLLED_REPLAY_V1",
                "target_layers": {
                    "recall": True,
                    "vector": False,
                    "primary_candidate": False,
                },
                "allowed_main_passage_ids": [],
                "_config_path": str(config_path),
            }
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["_config_path"] = str(config_path)
        return config

    def _is_controlled_replay_enabled(self, config: dict[str, Any]) -> bool:
        env_flag = str(config.get("env_flag") or "").strip()
        if env_flag and os.getenv(env_flag) is not None:
            return env_flag_enabled(os.getenv(env_flag))
        return bool(config.get("enabled_by_default"))

    def _build_controlled_replay_rows(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.controlled_replay_enabled:
            return []

        source_path = resolve_project_path(DEFAULT_FULL_MAIN_PASSAGES_PATH)
        if not source_path.exists():
            return []

        allowed_ids = list(dict.fromkeys(config.get("allowed_main_passage_ids") or []))
        if not allowed_ids:
            return []

        payload = json.loads(source_path.read_text(encoding="utf-8"))
        rows_by_id = {row.get("passage_id"): row for row in payload if row.get("passage_id")}
        replay_rows: list[dict[str, Any]] = []
        for passage_id in allowed_ids:
            row = rows_by_id.get(passage_id)
            if not row or not row.get("text"):
                continue
            chapter_id = row.get("chapter_id")
            replay_rows.append(
                {
                    "record_id": f"controlled:main_passages:{passage_id}",
                    "record_table": "controlled_replay_main_passages",
                    "source_object": "main_passages",
                    "passage_id": passage_id,
                    "retrieval_text": row["text"],
                    "normalized_text": row.get("normalized_text") or row["text"],
                    "chapter_id": chapter_id,
                    "chapter_name": self._chapter_name_by_id.get(chapter_id),
                    "policy_source_id": "controlled_replay_main_passages",
                    "evidence_level": "B",
                    "display_allowed": "secondary",
                    "risk_flag": json.dumps(
                        [
                            "controlled_replay_main_passage",
                            "secondary_only_replay",
                            "manual_review_l2_allowlist",
                        ],
                        ensure_ascii=False,
                    ),
                    "default_weight_tier": "medium_low",
                    "requires_disclaimer": 1,
                }
            )
        return replay_rows

    def build_request(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        perf_settings = load_perf_settings()
        request = super().build_request(query_text, tight_primary_precision=tight_primary_precision)
        request["retrieval_strategy"] = {
            "type": "hybrid_rrf_rerank",
            "sparse_top_k": SPARSE_TOP_K,
            "dense_chunk_top_k": DENSE_CHUNK_TOP_K,
            "dense_main_top_k": DENSE_MAIN_TOP_K,
            "fusion_top_k": FUSION_TOP_K,
            "rerank_top_n": perf_settings.rerank_top_n,
            "rrf_k": RRF_K,
            "embed_model": self.embed_model_name,
            "rerank_model": self.rerank_model_name,
            "rerank_device": self.rerank_device,
            "retrieval_mode": perf_settings.retrieval_mode,
            "perf_disable_rerank": perf_settings.disable_rerank,
        }
        return request

    def retrieve(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        request = self.build_request(query_text, tight_primary_precision=tight_primary_precision)
        raw_candidates = self._collect_raw_candidates(request)
        with stage_timer("evidence_gating"):
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
                "sparse_bm25_raw": None,
                "sparse_bm25_score": None,
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

    def _ensure_sparse_fts_index(self) -> None:
        table_exists = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (SPARSE_FTS_TABLE,),
        ).fetchone()
        if not table_exists:
            self._create_sparse_fts_table()
            self._rebuild_sparse_fts_index()
            return

        fts_count = self.conn.execute(f"SELECT COUNT(*) FROM {SPARSE_FTS_TABLE}").fetchone()[0]
        if fts_count != len(self.unified_rows):
            self._rebuild_sparse_fts_index()

    def _create_sparse_fts_table(self) -> None:
        try:
            self.conn.execute(
                f"""
                CREATE VIRTUAL TABLE {SPARSE_FTS_TABLE} USING fts5(
                    record_id UNINDEXED,
                    record_table UNINDEXED,
                    source_object UNINDEXED,
                    chapter_id UNINDEXED,
                    policy_source_id UNINDEXED,
                    default_weight_tier UNINDEXED,
                    search_text,
                    tokenize = '{SPARSE_FTS_TOKENIZER}'
                )
                """
            )
        except Exception as exc:  # pragma: no cover - explicit runtime guard
            raise SystemExit(
                "SQLite FTS5 is required for the sparse retrieval layer, "
                "but the runtime failed to create the retrieval_sparse_fts table."
            ) from exc

    def _rebuild_sparse_fts_index(self) -> None:
        payload = [
            (
                row["record_id"],
                row["record_table"],
                row["source_object"],
                row["chapter_id"],
                row["policy_source_id"],
                row["default_weight_tier"],
                compact_text(row["retrieval_text"]),
            )
            for row in self.unified_rows
        ]
        with self.conn:
            self.conn.execute(f"DELETE FROM {SPARSE_FTS_TABLE}")
            self.conn.executemany(
                f"""
                INSERT INTO {SPARSE_FTS_TABLE} (
                    record_id,
                    record_table,
                    source_object,
                    chapter_id,
                    policy_source_id,
                    default_weight_tier,
                    search_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )

    def _collect_sparse_candidates_lexical_baseline(self, request: dict[str, Any]) -> list[dict[str, Any]]:
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

        return self._trim_sparse_candidates(scored)

    def _collect_sparse_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query_focus = request["query_text_normalized"]
        query_terms = build_query_terms(query_focus)
        fts_query = build_sparse_fts_match_expression(query_focus)
        if not fts_query["match_expression"]:
            return self._collect_sparse_candidates_lexical_baseline(request)

        rows = self.conn.execute(
            f"""
            SELECT record_id, bm25({SPARSE_FTS_TABLE}) AS sparse_bm25_raw
            FROM {SPARSE_FTS_TABLE}
            WHERE {SPARSE_FTS_TABLE} MATCH ?
            ORDER BY sparse_bm25_raw
            LIMIT ?
            """,
            (fts_query["match_expression"], SPARSE_FTS_QUERY_LIMIT),
        ).fetchall()

        scored: list[dict[str, Any]] = []
        for row in rows:
            candidate_row = self.record_by_id.get(row["record_id"])
            if not candidate_row or candidate_row["source_object"] == "annotation_links":
                continue
            text_score, matched_terms = compute_text_match_score(query_focus, query_terms, candidate_row["normalized_text"])
            if text_score <= 0:
                continue
            candidate = self._base_candidate_from_row(
                candidate_row,
                request,
                text_match_score=text_score,
                matched_terms=matched_terms,
            )
            sparse_bm25_raw = float(row["sparse_bm25_raw"])
            candidate["sparse_bm25_raw"] = round(sparse_bm25_raw, 6)
            candidate["sparse_bm25_score"] = round(max(0.0, -sparse_bm25_raw), 6)
            candidate["stage_sources"] = ["sparse"]
            scored.append(candidate)

        if not scored:
            return []

        top_bm25_score = max(candidate["sparse_bm25_score"] or 0.0 for candidate in scored)
        for candidate in scored:
            bm25_ratio = (candidate["sparse_bm25_score"] or 0.0) / top_bm25_score if top_bm25_score > 0 else 0.0
            candidate["sparse_score"] = round(
                candidate["text_match_score"]
                + bm25_ratio * 24.0
                + candidate["weight_bonus"]
                + candidate["precision_adjustment"],
                6,
            )

        return self._trim_sparse_candidates(scored)

    def _trim_sparse_candidates(self, scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not scored:
            return []

        max_text_score = max(candidate["text_match_score"] for candidate in scored)
        minimum_text_score = max(2.0, max_text_score * 0.2)
        filtered = [candidate for candidate in scored if candidate["text_match_score"] >= minimum_text_score]
        filtered.sort(
            key=lambda row: (
                -row["sparse_score"],
                -(row.get("sparse_bm25_score") or 0.0),
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

    def compare_sparse_strategies(self, query_text: str, tight_primary_precision: bool = True) -> dict[str, Any]:
        request = self.build_request(query_text, tight_primary_precision=tight_primary_precision)
        lexical_candidates = self._collect_sparse_candidates_lexical_baseline(request)
        fts_candidates = self._collect_sparse_candidates(request)
        hybrid_result = self.retrieve(query_text, tight_primary_precision=tight_primary_precision)
        return {
            "query_request": request,
            "legacy_sparse_top_candidates": sparse_candidate_view(lexical_candidates),
            "fts5_sparse_top_candidates": sparse_candidate_view(fts_candidates),
            "sparse_backend": hybrid_result["retrieval_trace"]["sparse_backend"],
            "hybrid_result_summary": {
                "mode": hybrid_result["mode"],
                "mode_reason": hybrid_result["mode_reason"],
                "primary_evidence": [row["record_id"] for row in hybrid_result["primary_evidence"]],
                "secondary_evidence": [row["record_id"] for row in hybrid_result["secondary_evidence"]],
                "review_materials": [row["record_id"] for row in hybrid_result["risk_materials"]],
            },
        }

    def _collect_dense_candidates(
        self,
        request: dict[str, Any],
        query_vector: Any,
        *,
        index: Any,
        meta: dict[str, Any],
        top_k: int,
        stage_name: str,
    ) -> list[dict[str, Any]]:
        with stage_timer("dense_search_faiss"):
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

    def _encode_query_vector(self, request: dict[str, Any]) -> Any:
        perf_settings = load_perf_settings()
        cache_key = request["query_text"]
        cached_vector = None

        if perf_settings.enable_query_embed_cache:
            with self._query_vector_cache_lock:
                cached_vector = self._query_vector_cache.pop(cache_key, None)
                if cached_vector is not None:
                    self._query_vector_cache[cache_key] = cached_vector

        if cached_vector is not None:
            record_metadata("dense_embed_cache_hit", True)
            return self.np.asarray(cached_vector, dtype="float32")

        record_metadata("dense_embed_cache_hit", False)
        with stage_timer("dense_embed"):
            query_vector = self.embedder.encode(
                [request["query_text"]],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            query_vector = self.np.asarray(query_vector, dtype="float32")

        if perf_settings.enable_query_embed_cache:
            with self._query_vector_cache_lock:
                self._query_vector_cache[cache_key] = query_vector.copy()
                while len(self._query_vector_cache) > perf_settings.query_embed_cache_size:
                    oldest_key = next(iter(self._query_vector_cache))
                    self._query_vector_cache.pop(oldest_key, None)
        return query_vector

    def _collect_controlled_replay_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.controlled_replay_rows:
            return []

        query_focus = request["query_text_normalized"]
        query_terms = build_query_terms(query_focus)
        scored: list[dict[str, Any]] = []
        for row in self.controlled_replay_rows:
            text_score, matched_terms = compute_text_match_score(query_focus, query_terms, row["normalized_text"])
            if text_score <= 0:
                continue
            candidate = self._base_candidate_from_row(
                row,
                request,
                text_match_score=text_score,
                matched_terms=matched_terms,
            )
            candidate["sparse_score"] = round(
                text_score + candidate["weight_bonus"] + candidate["precision_adjustment"],
                6,
            )
            candidate["stage_sources"] = ["controlled_replay_recall"]
            scored.append(candidate)

        return self._trim_sparse_candidates(scored)

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
                sparse_bm25_values = [
                    value
                    for value in (existing["sparse_bm25_raw"], candidate["sparse_bm25_raw"])
                    if value is not None
                ]
                existing["sparse_bm25_raw"] = min(sparse_bm25_values) if sparse_bm25_values else None
                existing["sparse_bm25_score"] = max(
                    existing["sparse_bm25_score"] or 0.0,
                    candidate["sparse_bm25_score"] or 0.0,
                ) or None
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
        perf_settings = load_perf_settings()
        rerank_top_n = min(perf_settings.rerank_top_n, len(fused_candidates))
        rerank_slice = fused_candidates[:rerank_top_n]
        if not rerank_slice:
            return []

        if perf_settings.disable_rerank:
            for candidate in fused_candidates:
                candidate["combined_score"] = round(
                    candidate["rrf_score"] * 100.0
                    + candidate["sparse_score"]
                    + candidate["dense_rank_score"] * 10.0
                    + candidate["weight_bonus"],
                    6,
                )
            return fused_candidates

        pairs = [(request["query_text"], candidate["retrieval_text"]) for candidate in rerank_slice]
        with stage_timer("rerank_cross_encoder"):
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

        remainder = fused_candidates[rerank_top_n:]
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
        perf_settings = load_perf_settings()
        if not is_dense_only_candidate(candidate):
            return True

        if request["query_theme"]["type"] == "formula_name":
            return candidate["topic_consistency"] == "exact_formula_anchor"

        if perf_settings.disable_rerank:
            return candidate["dense_score"] >= 0.58
        return candidate["dense_score"] >= 0.58 and (candidate["rerank_score"] or 0.0) >= 0.62

    def _collect_raw_candidates(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        perf_settings = load_perf_settings()
        record_metadata("retrieval_mode_effective", perf_settings.retrieval_mode)
        sparse_query = build_sparse_fts_match_expression(request["query_text_normalized"])
        sparse_candidates: list[dict[str, Any]] = []
        dense_chunk_candidates: list[dict[str, Any]] = []
        dense_main_candidates: list[dict[str, Any]] = []
        controlled_replay_candidates: list[dict[str, Any]] = []

        if perf_settings.retrieval_mode in {"hybrid", "sparse"}:
            with stage_timer("sparse_retrieval"):
                sparse_candidates = self._collect_sparse_candidates(request)
            controlled_replay_candidates = self._collect_controlled_replay_candidates(request)

        if perf_settings.retrieval_mode in {"hybrid", "dense"}:
            query_vector = self._encode_query_vector(request)
            dense_chunk_candidates = self._collect_dense_candidates(
                request,
                query_vector,
                index=self.dense_chunks_index,
                meta=self.dense_chunks_meta,
                top_k=DENSE_CHUNK_TOP_K,
                stage_name="dense_chunks",
            )
            dense_main_candidates = self._collect_dense_candidates(
                request,
                query_vector,
                index=self.dense_main_index,
                meta=self.dense_main_meta,
                top_k=DENSE_MAIN_TOP_K,
                stage_name="dense_main_passages",
            )

        with stage_timer("fusion_rrf"):
            fused_candidates = self._fuse_candidates(
                ("sparse", sparse_candidates),
                ("dense_chunks", dense_chunk_candidates),
                ("dense_main_passages", dense_main_candidates),
                ("controlled_replay_recall", controlled_replay_candidates),
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
                "perf_rerank_top_n": perf_settings.rerank_top_n,
            },
            "sparse_backend": {
                "type": "sqlite_fts5_bm25" if sparse_query["match_expression"] else "lexical_fallback_short_query",
                "fts_table": SPARSE_FTS_TABLE,
                "tokenizer": SPARSE_FTS_TOKENIZER,
                "query_focus": request["query_text_normalized"],
                "match_terms": sparse_query["match_terms"],
                "match_expression": sparse_query["match_expression"],
            },
            "sparse_top_candidates": sparse_candidate_view(sparse_candidates),
            "dense_top_candidates": {
                "dense_chunks": short_candidate_view(dense_chunk_candidates, "dense_score"),
                "dense_main_passages": short_candidate_view(dense_main_candidates, "dense_score"),
            },
            "controlled_replay": {
                "enabled": self.controlled_replay_enabled,
                "config_path": self.controlled_replay_config.get("_config_path"),
                "env_flag": self.controlled_replay_config.get("env_flag"),
                "target_layers": self.controlled_replay_config.get("target_layers", {}),
                "allowed_main_passage_ids": self.controlled_replay_config.get("allowed_main_passage_ids", []),
                "top_candidates": sparse_candidate_view(controlled_replay_candidates),
            },
            "perf_flags": {
                "retrieval_mode": perf_settings.retrieval_mode,
                "disable_rerank": perf_settings.disable_rerank,
                "enable_query_embed_cache": perf_settings.enable_query_embed_cache,
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
        return self._dedupe_semantic_candidates(selected)


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
            f"- sparse_backend_fts5_enabled: `{all(result['retrieval_trace']['sparse_backend']['type'] == 'sqlite_fts5_bm25' for result in results)}`",
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
                "### Sparse Backend",
                "",
                json_dumps(trace["sparse_backend"]),
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


def build_fts_examples_payload(engine: HybridRetrievalEngine) -> dict[str, Any]:
    from datetime import datetime, timezone

    comparisons: list[dict[str, Any]] = []
    for example in FTS5_COMPARISON_EXAMPLES:
        comparison = engine.compare_sparse_strategies(example["query_text"])
        comparison["example_id"] = example["example_id"]
        comparison["expected_mode"] = example["expected_mode"]
        comparisons.append(comparison)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sparse_backend": {
            "type": "sqlite_fts5_bm25",
            "fts_table": SPARSE_FTS_TABLE,
            "tokenizer": SPARSE_FTS_TOKENIZER,
        },
        "examples": comparisons,
    }


def build_fts_smoke_markdown(command: str, payload: dict[str, Any]) -> str:
    lines = [
        "# FTS5 / BM25 Sparse Smoke Checks",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 结论",
        "",
        f"- sparse backend: `{payload['sparse_backend']['type']}`",
        f"- fts table: `{payload['sparse_backend']['fts_table']}`",
        f"- tokenizer: `{payload['sparse_backend']['tokenizer']}`",
        "",
    ]

    for example in payload["examples"]:
        summary = example["hybrid_result_summary"]
        lines.append(
            f"- `{example['query_request']['query_text']}` -> mode=`{summary['mode']}`, "
            f"legacy_top={len(example['legacy_sparse_top_candidates'])}, "
            f"fts5_top={len(example['fts5_sparse_top_candidates'])}, "
            f"primary={len(summary['primary_evidence'])}"
        )

    for example in payload["examples"]:
        lines.extend(
            [
                "",
                f"## Query: {example['query_request']['query_text']}",
                "",
                f"- query_focus: `{example['query_request']['query_text_normalized']}`",
                f"- sparse_backend: `{example['sparse_backend']['type']}`",
                f"- fts_match_expression: `{example['sparse_backend']['match_expression']}`",
                "",
                "### Legacy Sparse Top Candidates",
                "",
                json_dumps(example["legacy_sparse_top_candidates"]) if example["legacy_sparse_top_candidates"] else "_no rows_",
                "",
                "### FTS5 Sparse Top Candidates",
                "",
                json_dumps(example["fts5_sparse_top_candidates"]) if example["fts5_sparse_top_candidates"] else "_no rows_",
                "",
                "### Final Hybrid Summary",
                "",
                json_dumps(example["hybrid_result_summary"]),
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
        if result["retrieval_trace"]["sparse_backend"]["type"] != "sqlite_fts5_bm25":
            raise AssertionError("hybrid sparse backend must use sqlite_fts5_bm25")


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
    fts_examples_out = resolve_project_path(args.fts_examples_out)
    fts_smoke_out = resolve_project_path(args.fts_smoke_checks_out)

    examples_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)
    fts_examples_out.parent.mkdir(parents=True, exist_ok=True)
    fts_smoke_out.parent.mkdir(parents=True, exist_ok=True)

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
        fts_examples_payload = build_fts_examples_payload(engine)
        fts_examples_out.write_text(json_dumps(fts_examples_payload) + "\n", encoding="utf-8")
        command = f"{Path(sys.executable).name} -m backend.retrieval.hybrid"
        smoke_out.write_text(build_smoke_markdown(command, results), encoding="utf-8")
        fts_smoke_out.write_text(build_fts_smoke_markdown(command, fts_examples_payload), encoding="utf-8")
        log("[3/4] Ran hybrid retrieval examples and validated strong / weak_with_review_notice / refuse")
        log(f"[4/4] Wrote {examples_out}, {smoke_out}, {fts_examples_out}, and {fts_smoke_out}")
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
