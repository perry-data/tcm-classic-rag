from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_RETRIEVAL_VERSION = "RAG_RETRIEVAL_VERSION"
ENV_V2_ENABLED = "RAG_V2_ENABLED"

DEFAULT_V1_DB_PATH = "artifacts/zjshl_v1.db"
DEFAULT_V1_DENSE_CHUNKS_INDEX = "artifacts/dense_chunks.faiss"
DEFAULT_V1_DENSE_MAIN_INDEX = "artifacts/dense_main_passages.faiss"

DEFAULT_V2_SIDECAR_DB = (
    "artifacts/data_reconstruction_v2/"
    "macro_phase2_2_shadow_ready_sidecar_freeze/zjshl_v2_sidecar.db"
)
DEFAULT_V2_INDEX_DIR = "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build"

TRUE_VALUES = {"1", "true", "yes", "on", "v2", "2"}
FALSE_VALUES = {"", "0", "false", "no", "off", "v1"}


@dataclass(frozen=True)
class V1RetrievalRoute:
    """Read-only description of the existing v1 route; it does not instantiate runtime."""

    db_path: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V1_DB_PATH))
    dense_chunks_index: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V1_DENSE_CHUNKS_INDEX))
    dense_main_index: Path = field(default_factory=lambda: resolve_project_path(DEFAULT_V1_DENSE_MAIN_INDEX))
    retrieval_entrypoint: str = "backend.retrieval.hybrid.HybridRetrievalEngine"
    query_pipeline_entrypoint: str = "backend.answers.assembler.AnswerAssembler"


@dataclass(frozen=True)
class V2LaneSpec:
    name: str
    evidence_scope: str
    lexical_table: str
    lexical_fts_table: str
    dense_index_name: str | None
    dense_metadata_name: str | None
    primary_by_default: bool
    auxiliary: bool = False


V2_LANE_SPECS: dict[str, V2LaneSpec] = {
    "primary_safe": V2LaneSpec(
        name="primary_safe",
        evidence_scope="primary",
        lexical_table="lexical_primary_docs",
        lexical_fts_table="lexical_primary_docs_fts",
        dense_index_name="v2_primary_safe_dense.faiss",
        dense_metadata_name="v2_primary_safe_dense_metadata.jsonl",
        primary_by_default=True,
    ),
    "main_text_primary": V2LaneSpec(
        name="main_text_primary",
        evidence_scope="primary",
        lexical_table="lexical_main_text_docs",
        lexical_fts_table="lexical_main_text_docs_fts",
        dense_index_name=None,
        dense_metadata_name=None,
        primary_by_default=False,
    ),
    "formula_text_primary": V2LaneSpec(
        name="formula_text_primary",
        evidence_scope="primary",
        lexical_table="lexical_formula_text_docs",
        lexical_fts_table="lexical_formula_text_docs_fts",
        dense_index_name="v2_formula_text_primary_dense.faiss",
        dense_metadata_name="v2_formula_text_primary_dense_metadata.jsonl",
        primary_by_default=False,
    ),
    "formula_usage_positive": V2LaneSpec(
        name="formula_usage_positive",
        evidence_scope="primary",
        lexical_table="lexical_formula_usage_docs",
        lexical_fts_table="lexical_formula_usage_docs_fts",
        dense_index_name="v2_formula_usage_positive_dense.faiss",
        dense_metadata_name="v2_formula_usage_positive_dense_metadata.jsonl",
        primary_by_default=False,
    ),
    "auxiliary_safe": V2LaneSpec(
        name="auxiliary_safe",
        evidence_scope="auxiliary",
        lexical_table="lexical_auxiliary_docs",
        lexical_fts_table="lexical_auxiliary_docs_fts",
        dense_index_name="v2_auxiliary_safe_dense.faiss",
        dense_metadata_name="v2_auxiliary_safe_dense_metadata.jsonl",
        primary_by_default=False,
        auxiliary=True,
    ),
}


@dataclass(frozen=True)
class RetrievalFlag:
    requested_version: str
    source: str
    raw_value: str | None
    v2_requested: bool
    conflict: bool = False
    reason: str = ""


@dataclass(frozen=True)
class AdapterSelection:
    selected_version: str
    selected_adapter: str
    flag: RetrievalFlag
    v1_route: V1RetrievalRoute
    v2_adapter: "V2RetrievalAdapter | None" = None
    v2_blocked_reason: str | None = None
    staged_context_required: bool = True


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def _clean_flag(value: str | None) -> str:
    return str(value or "").strip().lower()


def parse_retrieval_flag(env: Mapping[str, str] | None = None) -> RetrievalFlag:
    values = dict(os.environ if env is None else env)
    raw_version = values.get(ENV_RETRIEVAL_VERSION)
    raw_enabled = values.get(ENV_V2_ENABLED)
    version_value = _clean_flag(raw_version)
    enabled_value = _clean_flag(raw_enabled)

    if raw_version is not None:
        if version_value in {"v2", "2", "true", "yes", "on"}:
            if enabled_value in {"0", "false", "no", "off"}:
                return RetrievalFlag("v1", ENV_RETRIEVAL_VERSION, raw_version, False, True, "conflicting_false_v2_flag")
            return RetrievalFlag("v2", ENV_RETRIEVAL_VERSION, raw_version, True)
        if version_value in {"", "v1", "1", "false", "no", "off", "0"}:
            return RetrievalFlag("v1", ENV_RETRIEVAL_VERSION, raw_version, False)
        return RetrievalFlag("v1", ENV_RETRIEVAL_VERSION, raw_version, False, False, "unknown_version_defaults_to_v1")

    if raw_enabled is not None:
        if enabled_value in TRUE_VALUES:
            return RetrievalFlag("v2", ENV_V2_ENABLED, raw_enabled, True)
        if enabled_value in FALSE_VALUES:
            return RetrievalFlag("v1", ENV_V2_ENABLED, raw_enabled, False)
        return RetrievalFlag("v1", ENV_V2_ENABLED, raw_enabled, False, False, "unknown_enabled_flag_defaults_to_v1")

    return RetrievalFlag("v1", "absent", None, False, False, "flag_absent_defaults_to_v1")


def select_retrieval_adapter(
    env: Mapping[str, str] | None = None,
    *,
    allow_v2: bool = False,
    v2_sidecar_db: str | Path = DEFAULT_V2_SIDECAR_DB,
    v2_index_dir: str | Path = DEFAULT_V2_INDEX_DIR,
) -> AdapterSelection:
    flag = parse_retrieval_flag(env)
    v1_route = V1RetrievalRoute()
    if not flag.v2_requested:
        return AdapterSelection(
            selected_version="v1",
            selected_adapter="v1_route",
            flag=flag,
            v1_route=v1_route,
        )
    if not allow_v2:
        return AdapterSelection(
            selected_version="v1",
            selected_adapter="v1_route",
            flag=flag,
            v1_route=v1_route,
            v2_blocked_reason="explicit_v2_flag_requires_offline_or_staged_context",
        )
    return AdapterSelection(
        selected_version="v2",
        selected_adapter="v2_retrieval_adapter",
        flag=flag,
        v1_route=v1_route,
        v2_adapter=V2RetrievalAdapter(sidecar_db=v2_sidecar_db, index_dir=v2_index_dir),
    )


@dataclass(frozen=True)
class V2RetrievalAdapter:
    sidecar_db: str | Path = DEFAULT_V2_SIDECAR_DB
    index_dir: str | Path = DEFAULT_V2_INDEX_DIR

    @property
    def sidecar_db_path(self) -> Path:
        return resolve_project_path(self.sidecar_db)

    @property
    def index_dir_path(self) -> Path:
        return resolve_project_path(self.index_dir)

    @property
    def lexical_index_path(self) -> Path:
        return self.index_dir_path / "v2_lexical_index.db"

    def dense_index_path(self, lane: str) -> Path | None:
        spec = self._lane_spec(lane)
        if spec.dense_index_name is None:
            return None
        return self.index_dir_path / spec.dense_index_name

    def dense_metadata_path(self, lane: str) -> Path | None:
        spec = self._lane_spec(lane)
        if spec.dense_metadata_name is None:
            return None
        return self.index_dir_path / spec.dense_metadata_name

    def artifact_paths(self) -> dict[str, Any]:
        lanes: dict[str, Any] = {}
        for lane, spec in V2_LANE_SPECS.items():
            lanes[lane] = {
                "evidence_scope": spec.evidence_scope,
                "lexical_table": spec.lexical_table,
                "lexical_fts_table": spec.lexical_fts_table,
                "dense_index_path": str(self.dense_index_path(lane)) if self.dense_index_path(lane) else None,
                "dense_metadata_path": str(self.dense_metadata_path(lane)) if self.dense_metadata_path(lane) else None,
                "primary_by_default": spec.primary_by_default,
                "auxiliary": spec.auxiliary,
            }
        return {
            "sidecar_db": str(self.sidecar_db_path),
            "lexical_index_db": str(self.lexical_index_path),
            "lanes": lanes,
        }

    def path_status(self) -> dict[str, Any]:
        paths = {
            "sidecar_db": self.sidecar_db_path,
            "lexical_index_db": self.lexical_index_path,
        }
        for lane in V2_LANE_SPECS:
            dense_index = self.dense_index_path(lane)
            dense_metadata = self.dense_metadata_path(lane)
            if dense_index is not None:
                paths[f"{lane}_dense_index"] = dense_index
            if dense_metadata is not None:
                paths[f"{lane}_dense_metadata"] = dense_metadata
        return {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "is_file": path.is_file(),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in paths.items()
        }

    def connect_sidecar_read_only(self) -> sqlite3.Connection:
        return self._connect_read_only(self.sidecar_db_path)

    def connect_lexical_read_only(self) -> sqlite3.Connection:
        return self._connect_read_only(self.lexical_index_path)

    def lexical_count(self, lane: str) -> int:
        spec = self._lane_spec(lane)
        with self.connect_lexical_read_only() as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM {spec.lexical_table}").fetchone()
        return int(row[0])

    def dense_metadata_count(self, lane: str) -> int | None:
        metadata_path = self.dense_metadata_path(lane)
        if metadata_path is None:
            return None
        with metadata_path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)

    def dense_metadata_rows(self, lane: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        metadata_path = self.dense_metadata_path(lane)
        if metadata_path is None:
            return []
        rows: list[dict[str, Any]] = []
        with metadata_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
                if limit is not None and len(rows) >= limit:
                    break
        return rows

    def load_faiss_index_read_only(self, lane: str) -> dict[str, Any]:
        dense_index = self.dense_index_path(lane)
        if dense_index is None:
            return {
                "lane": lane,
                "status": "not_applicable",
                "reason": "lane_has_no_dedicated_dense_index",
            }
        try:
            import faiss  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - depends on local environment
            return {
                "lane": lane,
                "path": str(dense_index),
                "status": "dependency_blocked",
                "dependency": "faiss",
                "error": f"{type(exc).__name__}: {exc}",
            }
        index = faiss.read_index(str(dense_index))
        return {
            "lane": lane,
            "path": str(dense_index),
            "status": "loaded_read_only",
            "vector_count": int(index.ntotal),
        }

    def default_primary_lanes(self) -> list[str]:
        return [lane for lane, spec in V2_LANE_SPECS.items() if spec.primary_by_default]

    def assert_boundary_invariants(self) -> dict[str, Any]:
        counts = {lane: self.dense_metadata_count(lane) for lane in V2_LANE_SPECS}
        lexical_counts = {lane: self.lexical_count(lane) for lane in V2_LANE_SPECS}
        primary_rows = self.dense_metadata_rows("primary_safe")
        formula_usage_rows = self.dense_metadata_rows("formula_usage_positive")
        auxiliary_rows = self.dense_metadata_rows("auxiliary_safe")
        return {
            "default_primary_lanes": self.default_primary_lanes(),
            "dense_metadata_counts": counts,
            "lexical_counts": lexical_counts,
            "carryover_can_be_returned_as_primary": any(bool(row.get("residual_carryover")) for row in primary_rows),
            "uncertain_usage_can_be_returned_as_positive_usage": any(
                "uncertain_usage" in json.dumps(row, ensure_ascii=False).lower()
                or "uncertain usage" in json.dumps(row, ensure_ascii=False).lower()
                for row in formula_usage_rows
            ),
            "auxiliary_merged_into_primary_default": "auxiliary_safe" in self.default_primary_lanes()
            or any(bool(row.get("primary_allowed")) for row in auxiliary_rows),
            "formula_text_and_usage_collapsed": counts.get("formula_text_primary") == counts.get("formula_usage_positive")
            and lexical_counts.get("formula_text_primary") == lexical_counts.get("formula_usage_positive"),
        }

    def _lane_spec(self, lane: str) -> V2LaneSpec:
        try:
            return V2_LANE_SPECS[lane]
        except KeyError as exc:
            raise ValueError(f"Unknown v2 retrieval lane: {lane}") from exc

    @staticmethod
    def _connect_read_only(path: Path) -> sqlite3.Connection:
        uri = f"file:{path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn
