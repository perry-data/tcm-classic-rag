#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = "artifacts/zjshl_mvp.db"
DEFAULT_INDEX_DIR = "artifacts"
DEFAULT_EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_CACHE_DIR = "artifacts/hf_cache"
DEFAULT_REPORT_PATH = "artifacts/dense_index_build_report.md"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dense retrieval indexes for zjshl_mvp.db.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the MVP sqlite database.")
    parser.add_argument("--index-dir", default=DEFAULT_INDEX_DIR, help="Directory to store FAISS indexes and meta.")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="SentenceTransformer embedding model.")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local model cache directory.")
    parser.add_argument("--batch-size", type=int, default=8, help="Embedding batch size.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Markdown build report path.")
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def log(message: str) -> None:
    print(message, flush=True)


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def prepare_hf_cache(cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_dir))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(cache_dir))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(cache_dir))
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")


def load_rows(conn: sqlite3.Connection, source_object: str) -> list[dict[str, Any]]:
    query = """
        SELECT
            record_id,
            record_table,
            source_object,
            retrieval_text,
            normalized_text,
            chapter_id,
            chapter_name,
            evidence_level,
            display_allowed,
            risk_flag,
            default_weight_tier,
            policy_source_id,
            backref_target_type,
            backref_target_ids_json
        FROM vw_retrieval_records_unified
        WHERE source_object = ?
        ORDER BY record_id
    """
    return [dict(row) for row in conn.execute(query, (source_object,))]


def has_cached_model(cache_dir: Path, model_name: str) -> bool:
    return (cache_dir / f"models--{model_name.replace('/', '--')}").exists()


def resolve_cached_model_path(cache_dir: Path, model_name: str) -> Path | None:
    snapshots_dir = cache_dir / f"models--{model_name.replace('/', '--')}" / "snapshots"
    if not snapshots_dir.exists():
        return None
    snapshot_dirs = sorted(path for path in snapshots_dir.iterdir() if path.is_dir())
    return snapshot_dirs[-1] if snapshot_dirs else None


def load_embedding_model(sentence_transformer_cls: Any, model_name: str, cache_dir: Path) -> Any:
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


def build_single_index(
    model: Any,
    faiss_mod: Any,
    np_mod: Any,
    rows: list[dict[str, Any]],
    batch_size: int,
    index_path: Path,
    meta_path: Path,
    label: str,
) -> dict[str, Any]:
    texts = [row["retrieval_text"] or row["normalized_text"] or "" for row in rows]
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embeddings = np_mod.asarray(embeddings, dtype="float32")

    index = faiss_mod.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    faiss_mod.write_index(index, str(index_path))

    meta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_label": label,
        "count": len(rows),
        "dimension": int(embeddings.shape[1]),
        "normalized": True,
        "records": [
            {
                "position": idx,
                "record_id": row["record_id"],
                "record_table": row["record_table"],
                "source_object": row["source_object"],
                "chapter_id": row["chapter_id"],
                "chapter_name": row["chapter_name"],
                "evidence_level": row["evidence_level"],
                "display_allowed": row["display_allowed"],
                "policy_source_id": row["policy_source_id"],
                "backref_target_type": row["backref_target_type"],
                "backref_target_ids_json": row["backref_target_ids_json"],
            }
            for idx, row in enumerate(rows)
        ],
    }
    meta_path.write_text(json_dumps(meta) + "\n", encoding="utf-8")

    return {
        "label": label,
        "count": len(rows),
        "dimension": int(embeddings.shape[1]),
        "index_path": str(index_path),
        "meta_path": str(meta_path),
    }


def build_report(command: str, embed_model: str, build_summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Dense Index Build Report",
        "",
        "## 运行命令",
        "",
        f"`{command}`",
        "",
        "## 配置",
        "",
        f"- embedding_model: `{embed_model}`",
        f"- index_count: `{len(build_summaries)}`",
        "",
        "## 构建结果",
        "",
    ]

    for summary in build_summaries:
        lines.extend(
            [
                f"### {summary['label']}",
                "",
                f"- count: `{summary['count']}`",
                f"- dimension: `{summary['dimension']}`",
                f"- index_path: `{summary['index_path']}`",
                f"- meta_path: `{summary['meta_path']}`",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    db_path = resolve_project_path(args.db_path)
    index_dir = resolve_project_path(args.index_dir)
    cache_dir = resolve_project_path(args.cache_dir)
    report_path = resolve_project_path(args.report_path)

    index_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_hf_cache(cache_dir)

    try:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - dependency guard
        raise SystemExit(
            "Missing dense retrieval dependencies. Run this script with the project venv: "
            "./.venv/bin/python scripts/build_dense_index.py"
        ) from exc

    model = load_embedding_model(SentenceTransformer, args.embed_model, cache_dir)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        chunk_rows = load_rows(conn, "chunks")
        main_rows = load_rows(conn, "main_passages")

        log(f"[1/5] Loaded database from {db_path}")
        log(f"[2/5] Loaded embedding model {args.embed_model}")
        log(f"[3/5] Preparing dense indexes for chunks={len(chunk_rows)} and main_passages={len(main_rows)}")

        build_summaries = [
            build_single_index(
                model=model,
                faiss_mod=faiss,
                np_mod=np,
                rows=chunk_rows,
                batch_size=args.batch_size,
                index_path=index_dir / "dense_chunks.faiss",
                meta_path=index_dir / "dense_chunks_meta.json",
                label="chunks",
            ),
            build_single_index(
                model=model,
                faiss_mod=faiss,
                np_mod=np,
                rows=main_rows,
                batch_size=args.batch_size,
                index_path=index_dir / "dense_main_passages.faiss",
                meta_path=index_dir / "dense_main_passages_meta.json",
                label="main_passages",
            ),
        ]

        report_path.write_text(
            build_report(
                command=f"{Path(sys.executable).name} scripts/build_dense_index.py",
                embed_model=args.embed_model,
                build_summaries=build_summaries,
            ),
            encoding="utf-8",
        )
        log("[4/5] Built FAISS indexes and meta files")
        log(f"[5/5] Wrote {report_path}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
