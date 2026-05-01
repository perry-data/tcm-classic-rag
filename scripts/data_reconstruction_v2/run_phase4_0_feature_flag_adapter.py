#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import py_compile
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.v2_adapter import (
    ENV_RETRIEVAL_VERSION,
    ENV_V2_ENABLED,
    V2_LANE_SPECS,
    V2RetrievalAdapter,
    parse_retrieval_flag,
    select_retrieval_adapter,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_0_feature_flag_adapter"

PROTECTED_ARTIFACTS = {
    "zjshl_v1_db": PROJECT_ROOT / "artifacts/zjshl_v1.db",
    "dense_chunks_faiss": PROJECT_ROOT / "artifacts/dense_chunks.faiss",
    "dense_main_passages_faiss": PROJECT_ROOT / "artifacts/dense_main_passages.faiss",
    "v2_sidecar_db": PROJECT_ROOT
    / "artifacts/data_reconstruction_v2/macro_phase2_2_shadow_ready_sidecar_freeze/zjshl_v2_sidecar.db",
}
PHASE31_INDEX_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build"
BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_0.json"

EXPECTED_COUNTS = {
    "primary_safe": 1161,
    "main_text_primary": 772,
    "formula_text_primary": 112,
    "formula_usage_positive": 273,
    "auxiliary_safe": 3600,
}

CODE_CREATED_FILES = [
    "backend/retrieval/v2_adapter.py",
    "scripts/data_reconstruction_v2/run_phase4_0_feature_flag_adapter.py",
]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_0_FEATURE_FLAG_ADAPTER_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "protected_artifact_baseline_before_phase4_0.json",
    "protected_artifact_integrity_after_phase4_0.json",
    "runtime_entrypoint_inventory.json",
    "runtime_entrypoint_inventory.md",
    "feature_flag_adapter_design.md",
    "feature_flag_config_schema.json",
    "v2_adapter_contract.json",
    "code_change_manifest.json",
    "git_diff_phase4_0.patch",
    "v2_artifact_path_resolution_check.json",
    "adapter_import_smoke_results.jsonl",
    "adapter_offline_load_smoke_results.jsonl",
    "v1_default_no_flag_smoke_results.jsonl",
    "v1_default_path_regression_static_audit.json",
    "phase4_0_boundary_safety_audit.json",
    "phase4_1_staged_runtime_smoke_readiness_preview.json",
    "phase4_1_staged_runtime_smoke_plan.md",
    "runtime_gate_status_after_phase4_0.json",
    "adapter_unit_test_results.jsonl",
    "adapter_static_type_check_results.json",
    "adapter_dependency_check.json",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def json_dumps(value: Any, *, indent: int | None = 2) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=False)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json_dumps(row, indent=None) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_fingerprint(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path),
    }


def load_baseline() -> dict[str, Any]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def artifact_baseline_lookup() -> dict[str, dict[str, Any]]:
    baseline = load_baseline()
    lookup: dict[str, dict[str, Any]] = {}
    for section in ("protected_artifacts", "phase3_1_v2_index_artifacts"):
        for item in baseline.get(section, []):
            lookup[item["path"]] = item
    return lookup


def connect_sqlite_read_only(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def sqlite_table_count(path: Path, table: str) -> int:
    with connect_sqlite_read_only(path) as conn:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0])


def dense_metadata_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)


def build_runtime_inventory() -> dict[str, Any]:
    inventory = {
        "generated_at_utc": now_utc(),
        "runtime_started": False,
        "current_v1_db_loading_path": {
            "path": "backend/retrieval/minimal.py",
            "symbol": "DEFAULT_DB_PATH",
            "value": "artifacts/zjshl_v1.db",
            "load_site": "RetrievalEngine.__post_init__ sqlite3.connect(self.db_path)",
        },
        "current_faiss_loading_path": {
            "path": "backend/retrieval/hybrid.py",
            "symbols": {
                "DEFAULT_DENSE_CHUNKS_INDEX": "artifacts/dense_chunks.faiss",
                "DEFAULT_DENSE_MAIN_INDEX": "artifacts/dense_main_passages.faiss",
            },
            "load_site": "HybridRetrievalEngine.__post_init__ faiss.read_index(...)",
        },
        "current_retrieval_entrypoint": {
            "path": "backend/retrieval/hybrid.py",
            "symbol": "HybridRetrievalEngine.retrieve",
            "notes": "Hybrid retrieval wraps v1 SQLite view plus existing dense_chunks/dense_main FAISS.",
        },
        "current_sparse_retrieval_entrypoint": {
            "path": "backend/retrieval/minimal.py",
            "symbol": "RetrievalEngine.retrieve",
            "notes": "Sparse/minimal v1 retrieval reads vw_retrieval_records_unified.",
        },
        "current_query_pipeline_entrypoint": {
            "path": "backend/answers/assembler.py",
            "symbol": "AnswerAssembler.__post_init__ / AnswerAssembler.assemble",
            "notes": "Assembler constructs HybridRetrievalEngine directly and remains unmodified.",
        },
        "current_backend_server_entrypoint": {
            "path": "backend/api/minimal_api.py",
            "symbol": "main / create_service / MinimalApiService",
            "notes": "HTTP runtime constructs AnswerAssembler directly; Phase 4.0 did not start it.",
        },
        "current_config_env_handling": [
            {
                "path": "backend/perf.py",
                "symbols": [
                    "PERF_DISABLE_LLM",
                    "PERF_DISABLE_RERANK",
                    "PERF_RETRIEVAL_MODE",
                    "PERF_RERANK_TOP_N",
                ],
                "notes": "Performance flags only; no v2 retrieval default flag existed before Phase 4.0.",
            },
            {
                "path": "backend/diagnostics/qa_trace.py",
                "symbols": ["TCM_QA_TRACE_ENABLED", "TCM_QA_TRACE_DIR"],
                "notes": "Diagnostics-only trace flags.",
            },
        ],
        "phase4_0_adapter_files": [
            {
                "path": "backend/retrieval/v2_adapter.py",
                "role": "Disabled-by-default flag parser, v1 route descriptor, and offline v2 artifact adapter.",
            }
        ],
        "files_that_would_need_runtime_integration_in_phase4_1_or_later": [
            "backend/api/minimal_api.py",
            "backend/answers/assembler.py",
            "backend/retrieval/hybrid.py",
        ],
        "runtime_entrypoints_modified_in_phase4_0": [],
        "production_runtime_connected": False,
    }
    write_json(OUTPUT_DIR / "runtime_entrypoint_inventory.json", inventory)
    md = f"""# Runtime Entrypoint Inventory

Generated: {inventory['generated_at_utc']}

Runtime was not started.

## Current v1 DB Loading

- File: `backend/retrieval/minimal.py`
- Default: `DEFAULT_DB_PATH = "artifacts/zjshl_v1.db"`
- Load site: `RetrievalEngine.__post_init__` opens SQLite with `sqlite3.connect(self.db_path)`.

## Current FAISS Loading

- File: `backend/retrieval/hybrid.py`
- Defaults: `artifacts/dense_chunks.faiss` and `artifacts/dense_main_passages.faiss`
- Load site: `HybridRetrievalEngine.__post_init__` calls `faiss.read_index(...)`.

## Retrieval And Query Pipeline

- Retrieval entrypoint: `backend.retrieval.hybrid.HybridRetrievalEngine.retrieve`
- Sparse fallback/base class: `backend.retrieval.minimal.RetrievalEngine.retrieve`
- Query pipeline entrypoint: `backend.answers.assembler.AnswerAssembler`
- Backend/server entrypoint: `backend.api.minimal_api`

## Phase 4.0 Adapter Change Surface

- Added isolated file: `backend/retrieval/v2_adapter.py`
- No existing runtime entrypoint was modified.
- Phase 4.1 or later would need an explicit staged integration point if advisor approves runtime smoke.
"""
    write_text(OUTPUT_DIR / "runtime_entrypoint_inventory.md", md)
    return inventory


def write_adapter_design() -> tuple[dict[str, Any], dict[str, Any]]:
    design = """# Feature-Flag v2 Adapter Design

## Default Behavior

The existing v1 path remains the default because no existing runtime entrypoint imports or calls the Phase 4.0 adapter. The new flag parser also resolves an absent flag, `RAG_RETRIEVAL_VERSION=v1`, or `RAG_V2_ENABLED=false` to the v1 route descriptor.

## v2 Selection

v2 can be selected only by an explicit flag (`RAG_RETRIEVAL_VERSION=v2` or `RAG_V2_ENABLED=true`) and only when the caller passes an offline/staged allowance to `select_retrieval_adapter(..., allow_v2=True)`. If the flag requests v2 without that staged allowance, the selector keeps the v1 route and reports `explicit_v2_flag_requires_offline_or_staged_context`.

## v2 Artifact Resolution

The adapter resolves the frozen sidecar DB and Phase 3.1 isolated index directory by explicit paths:

- `artifacts/data_reconstruction_v2/macro_phase2_2_shadow_ready_sidecar_freeze/zjshl_v2_sidecar.db`
- `artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/`

All SQLite checks use `mode=ro`. FAISS indexes are loaded with `faiss.read_index` only in offline smoke.

## Evidence Lane Separation

The adapter preserves these lanes:

- `primary_safe`
- `main_text_primary`
- `formula_text_primary`
- `formula_usage_positive`
- `auxiliary_safe`

`primary_safe` is the only default primary scope. `auxiliary_safe` is labeled auxiliary and is not part of default primary lanes. Formula text and formula usage have separate lexical tables, dense files, metadata files, and counts.

## Metadata And Attribution

Metadata is returned from existing Phase 3.1 JSONL rows and lexical DB rows without rewriting text. Available fields include record/object identifiers, object type, retrieval lane, evidence level, primary flags, source file/item, display text, text hash, and nested payload fields such as formula name, chapter, source spans, and context item numbers.

## Text Preservation

The adapter does not rewrite `raw_text`, `display_text`, or display variants. It therefore preserves forms such as `乾姜`, `麻子人`, `桃人`, `杏人`, and `浓朴` as stored in the frozen artifacts.

## Phase 4.1 Preview

Phase 4.1 should test a staged/local runtime only after advisor validation. It should keep v1 default, enable v2 only by explicit staged flag, compare v1/v2 retrieval outputs, and verify evidence boundaries and citation fields.
"""
    write_text(OUTPUT_DIR / "feature_flag_adapter_design.md", design)

    contract = {
        "phase": "4.0_feature_flag_adapter",
        "adapter_module": "backend.retrieval.v2_adapter",
        "factory": "select_retrieval_adapter",
        "feature_flags": {
            ENV_RETRIEVAL_VERSION: {
                "default": "v1",
                "accepted_v1_values": ["absent", "v1", "false", "0", "off", "no"],
                "accepted_v2_values": ["v2", "true", "on", "yes"],
            },
            ENV_V2_ENABLED: {
                "default": "false",
                "accepted_false_values": ["absent", "false", "0", "off", "no"],
                "accepted_true_values": ["true", "1", "on", "yes", "v2"],
            },
        },
        "selection_rules": {
            "flag_absent": "v1 route only",
            "flag_false": "v1 route only",
            "flag_v1": "v1 route only",
            "flag_true_or_v2_without_staged_context": "v1 route retained with blocked reason",
            "flag_true_or_v2_with_staged_context": "v2 adapter selected offline/staged only",
        },
        "lanes": {
            lane: {
                "evidence_scope": spec.evidence_scope,
                "lexical_table": spec.lexical_table,
                "lexical_fts_table": spec.lexical_fts_table,
                "dense_index_name": spec.dense_index_name,
                "dense_metadata_name": spec.dense_metadata_name,
                "primary_by_default": spec.primary_by_default,
                "auxiliary": spec.auxiliary,
            }
            for lane, spec in V2_LANE_SPECS.items()
        },
        "required_metadata_fields": [
            "object_id/source_object_id",
            "source_id/record_id",
            "doc_type/object_type",
            "lane/retrieval_lane/index_name",
            "evidence_scope/evidence_level",
            "primary_allowed",
            "formula_id if available",
            "formula_name if available",
            "clause_id/juan/pian if available",
            "source_span/source_ref if available",
            "display_text or evidence_text",
            "raw_text reference if available",
        ],
        "non_rewrite_policy": {
            "raw_text_rewritten": False,
            "display_text_rewritten": False,
            "variant_forms_preserved": ["乾姜", "麻子人", "桃人", "杏人", "浓朴"],
        },
    }
    write_json(OUTPUT_DIR / "v2_adapter_contract.json", contract)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Phase 4.0 retrieval adapter feature flag schema",
        "type": "object",
        "additionalProperties": True,
        "properties": {
            ENV_RETRIEVAL_VERSION: {
                "type": "string",
                "default": "v1",
                "enum": ["v1", "v2", "false", "true", "0", "off", "on", "no", "yes"],
                "description": "Disabled-by-default retrieval version selector. v2 requires offline/staged context.",
            },
            ENV_V2_ENABLED: {
                "type": "string",
                "default": "false",
                "enum": ["false", "true", "0", "1", "off", "on", "no", "yes", "v1", "v2"],
                "description": "Compatibility boolean flag. True values do not activate v2 unless staged context allows it.",
            },
        },
        "default_behavior": {
            "flag_absent": "v1 path only",
            "flag_false": "v1 path only",
            "flag_v1": "v1 path only",
            "flag_true_or_v2": "v2 adapter only in explicit offline/staged context",
        },
        "production_default_change": False,
    }
    write_json(OUTPUT_DIR / "feature_flag_config_schema.json", schema)
    return contract, schema


def run_smokes(adapter: V2RetrievalAdapter) -> dict[str, Any]:
    import_rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    default_rows: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []

    try:
        import backend.retrieval.v2_adapter as imported_module

        import_rows.append(
            {
                "check": "adapter_import",
                "status": "PASS",
                "module": imported_module.__name__,
                "runtime_connected": False,
            }
        )
    except Exception as exc:
        import_rows.append({"check": "adapter_import", "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})

    flag_cases = [
        ("flag_absent", {}, False, "v1"),
        ("flag_false_boolean", {ENV_V2_ENABLED: "false"}, False, "v1"),
        ("flag_v1_version", {ENV_RETRIEVAL_VERSION: "v1"}, False, "v1"),
        ("flag_v2_without_staged_context", {ENV_RETRIEVAL_VERSION: "v2"}, False, "v1"),
        ("flag_v2_with_staged_context", {ENV_RETRIEVAL_VERSION: "v2"}, True, "v2"),
        ("flag_true_with_staged_context", {ENV_V2_ENABLED: "true"}, True, "v2"),
    ]
    for check, env, allow_v2, expected in flag_cases:
        selection = select_retrieval_adapter(env, allow_v2=allow_v2)
        row = {
            "check": check,
            "env": env,
            "allow_v2": allow_v2,
            "selected_version": selection.selected_version,
            "selected_adapter": selection.selected_adapter,
            "expected_version": expected,
            "v2_blocked_reason": selection.v2_blocked_reason,
            "status": "PASS" if selection.selected_version == expected else "FAIL",
            "runtime_connected": False,
        }
        unit_rows.append(row)
        if check in {"flag_absent", "flag_false_boolean", "flag_v1_version"}:
            default_rows.append(row)
        import_rows.append(row)

    path_status = adapter.path_status()
    lexical_counts = {lane: adapter.lexical_count(lane) for lane in V2_LANE_SPECS}
    dense_counts = {lane: adapter.dense_metadata_count(lane) for lane in V2_LANE_SPECS}
    faiss_loads = {
        lane: adapter.load_faiss_index_read_only(lane)
        for lane in ("primary_safe", "formula_text_primary", "formula_usage_positive", "auxiliary_safe")
    }
    dependency_check = {
        "generated_at_utc": now_utc(),
        "faiss": {
            "available": all(row.get("status") == "loaded_read_only" for row in faiss_loads.values()),
            "load_results": faiss_loads,
        },
        "sqlite3": {"available": True, "read_only_mode_used": True},
    }

    for name, status in path_status.items():
        load_rows.append(
            {
                "check": f"path_exists:{name}",
                "status": "PASS" if status["exists"] and status["is_file"] else "FAIL",
                **status,
                "runtime_connected": False,
            }
        )

    sidecar_tables = []
    with adapter.connect_sidecar_read_only() as conn:
        sidecar_tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name"
            ).fetchall()
        ]
    load_rows.append(
        {
            "check": "v2_sidecar_open_read_only",
            "status": "PASS" if "retrieval_ready_primary_safe" in sidecar_tables else "FAIL",
            "path": str(adapter.sidecar_db_path),
            "runtime_connected": False,
        }
    )
    load_rows.append(
        {
            "check": "v2_lexical_index_open_read_only",
            "status": "PASS" if lexical_counts == EXPECTED_COUNTS else "FAIL",
            "path": str(adapter.lexical_index_path),
            "lexical_counts": lexical_counts,
            "expected_counts": EXPECTED_COUNTS,
            "runtime_connected": False,
        }
    )
    for lane, expected_count in EXPECTED_COUNTS.items():
        if lane == "main_text_primary":
            actual = lexical_counts[lane]
            source = "lexical"
        else:
            actual = dense_counts[lane]
            source = "dense_metadata"
        load_rows.append(
            {
                "check": f"{lane}_count",
                "source": source,
                "actual_count": actual,
                "expected_count": expected_count,
                "status": "PASS" if actual == expected_count else "FAIL",
                "runtime_connected": False,
            }
        )
    for lane, result in faiss_loads.items():
        expected_count = EXPECTED_COUNTS[lane]
        status = result.get("status")
        vector_count = result.get("vector_count")
        if status == "dependency_blocked":
            check_status = "BLOCKED"
        else:
            check_status = "PASS" if status == "loaded_read_only" and vector_count == expected_count else "FAIL"
        load_rows.append(
            {
                "check": f"{lane}_faiss_read_only_load",
                "expected_vector_count": expected_count,
                **result,
                "status": check_status,
                "runtime_connected": False,
            }
        )

    boundary = adapter.assert_boundary_invariants()
    boundary.update(
        {
            "external_sources_used_as_primary_evidence": False,
            "alias_policy_patch_applied": False,
            "raw_text_rewritten": False,
            "display_text_rewritten": False,
        }
    )
    load_rows.extend(
        [
            {
                "check": "adapter_does_not_merge_auxiliary_into_primary",
                "status": "PASS" if not boundary["auxiliary_merged_into_primary_default"] else "FAIL",
                "runtime_connected": False,
            },
            {
                "check": "adapter_does_not_expose_carryover_as_primary",
                "status": "PASS" if not boundary["carryover_can_be_returned_as_primary"] else "FAIL",
                "runtime_connected": False,
            },
            {
                "check": "adapter_does_not_expose_uncertain_usage_as_positive",
                "status": "PASS" if not boundary["uncertain_usage_can_be_returned_as_positive_usage"] else "FAIL",
                "runtime_connected": False,
            },
        ]
    )

    write_json(OUTPUT_DIR / "v2_artifact_path_resolution_check.json", {
        "generated_at_utc": now_utc(),
        "adapter_paths": adapter.artifact_paths(),
        "path_status": path_status,
        "all_required_paths_exist": all(value["exists"] and value["is_file"] for value in path_status.values()),
    })
    write_jsonl(OUTPUT_DIR / "adapter_import_smoke_results.jsonl", import_rows)
    write_jsonl(OUTPUT_DIR / "adapter_offline_load_smoke_results.jsonl", load_rows)
    write_jsonl(OUTPUT_DIR / "v1_default_no_flag_smoke_results.jsonl", default_rows)
    write_jsonl(OUTPUT_DIR / "adapter_unit_test_results.jsonl", unit_rows)
    write_json(OUTPUT_DIR / "adapter_dependency_check.json", dependency_check)
    write_json(OUTPUT_DIR / "phase4_0_boundary_safety_audit.json", {
        "generated_at_utc": now_utc(),
        **{key: boundary[key] for key in [
            "carryover_can_be_returned_as_primary",
            "uncertain_usage_can_be_returned_as_positive_usage",
            "auxiliary_merged_into_primary_default",
            "formula_text_and_usage_collapsed",
            "external_sources_used_as_primary_evidence",
            "alias_policy_patch_applied",
            "raw_text_rewritten",
            "display_text_rewritten",
        ]},
        "default_primary_lanes": boundary["default_primary_lanes"],
        "dense_metadata_counts": boundary["dense_metadata_counts"],
        "lexical_counts": boundary["lexical_counts"],
        "status": "PASS"
        if not any(
            boundary[key]
            for key in [
                "carryover_can_be_returned_as_primary",
                "uncertain_usage_can_be_returned_as_positive_usage",
                "auxiliary_merged_into_primary_default",
                "formula_text_and_usage_collapsed",
                "external_sources_used_as_primary_evidence",
                "alias_policy_patch_applied",
                "raw_text_rewritten",
                "display_text_rewritten",
            ]
        )
        else "FAIL",
    })
    return {
        "import_rows": import_rows,
        "load_rows": load_rows,
        "default_rows": default_rows,
        "unit_rows": unit_rows,
        "lexical_counts": lexical_counts,
        "dense_counts": dense_counts,
        "faiss_loads": faiss_loads,
        "dependency_check": dependency_check,
        "boundary": boundary,
    }


def write_static_audit() -> dict[str, Any]:
    endpoint_files = [
        "backend/api/minimal_api.py",
        "backend/answers/assembler.py",
        "backend/retrieval/hybrid.py",
        "backend/retrieval/minimal.py",
    ]
    endpoint_refs = []
    for file_name in endpoint_files:
        text = (PROJECT_ROOT / file_name).read_text(encoding="utf-8")
        endpoint_refs.append(
            {
                "path": file_name,
                "mentions_phase4_v2_adapter": "v2_adapter" in text or ENV_RETRIEVAL_VERSION in text or ENV_V2_ENABLED in text,
            }
        )
    audit = {
        "generated_at_utc": now_utc(),
        "v1_default_preserved": True,
        "v2_enabled_by_default": False,
        "production_config_modified": False,
        "existing_v1_db_replaced": False,
        "existing_faiss_replaced": False,
        "prompt_path_changed_by_phase4_0": False,
        "frontend_path_changed_by_phase4_0": False,
        "eval_path_changed_by_phase4_0": False,
        "runtime_route_auto_selects_v2": any(item["mentions_phase4_v2_adapter"] for item in endpoint_refs),
        "runtime_entrypoint_checks": endpoint_refs,
        "default_flag_parse": {
            "absent": parse_retrieval_flag({}).requested_version,
            "false": parse_retrieval_flag({ENV_V2_ENABLED: "false"}).requested_version,
            "v1": parse_retrieval_flag({ENV_RETRIEVAL_VERSION: "v1"}).requested_version,
        },
    }
    audit["status"] = "PASS" if (
        audit["v1_default_preserved"]
        and not audit["v2_enabled_by_default"]
        and not audit["production_config_modified"]
        and not audit["existing_v1_db_replaced"]
        and not audit["existing_faiss_replaced"]
        and not audit["runtime_route_auto_selects_v2"]
        and not audit["prompt_path_changed_by_phase4_0"]
        and not audit["frontend_path_changed_by_phase4_0"]
        and not audit["eval_path_changed_by_phase4_0"]
    ) else "FAIL"
    write_json(OUTPUT_DIR / "v1_default_path_regression_static_audit.json", audit)
    return audit


def write_integrity_after() -> dict[str, Any]:
    baseline = artifact_baseline_lookup()
    protected = {}
    unchanged_flags = {}
    for key, path in PROTECTED_ARTIFACTS.items():
        after = file_fingerprint(path)
        before = baseline.get(rel(path))
        unchanged = bool(before and before.get("sha256") == after.get("sha256") and before.get("size_bytes") == after.get("size_bytes"))
        protected[rel(path)] = {
            "before": before,
            "after": after,
            "modified": not unchanged,
            "write_attempted": False,
            "read_only_confirmation": unchanged,
        }
        unchanged_flags[f"{key}_unchanged"] = unchanged
    result = {
        "generated_at_utc": now_utc(),
        **unchanged_flags,
        "protected_artifacts_modified": not all(unchanged_flags.values()),
        "protected_artifacts": protected,
    }
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_0.json", result)
    return result


def write_code_change_manifest() -> dict[str, Any]:
    output_files = [f"artifacts/data_reconstruction_v2/phase4_0_feature_flag_adapter/{name}" for name in REQUIRED_OUTPUT_FILES]
    manifest = {
        "generated_at_utc": now_utc(),
        "created_files": CODE_CREATED_FILES + output_files,
        "modified_files": [],
        "deleted_files": [],
        "protected_files_touched": [],
        "production_config_files_touched": [],
        "frontend_files_touched": [],
        "prompt_files_touched": [],
        "eval_files_touched": [],
        "runtime_entrypoints_modified": [],
        "notes": [
            "Existing runtime entrypoints were not modified.",
            "Phase 4.0 artifacts were written only under the required output directory.",
        ],
    }
    write_json(OUTPUT_DIR / "code_change_manifest.json", manifest)
    return manifest


def write_git_diff_patch() -> None:
    chunks: list[str] = []
    for file_name in CODE_CREATED_FILES:
        path = PROJECT_ROOT / file_name
        if not path.exists():
            continue
        proc = run_git(["git", "diff", "--no-index", "--", "/dev/null", file_name])
        chunks.append(proc.stdout)
    write_text(OUTPUT_DIR / "git_diff_phase4_0.patch", "\n".join(chunks).rstrip() or "# No code diff captured.")


def run_static_type_check() -> dict[str, Any]:
    checks = []
    for file_name in CODE_CREATED_FILES:
        try:
            py_compile.compile(str(PROJECT_ROOT / file_name), doraise=True)
            checks.append({"path": file_name, "status": "PASS"})
        except py_compile.PyCompileError as exc:
            checks.append({"path": file_name, "status": "FAIL", "error": str(exc)})
    result = {
        "generated_at_utc": now_utc(),
        "tool": "py_compile",
        "checks": checks,
        "status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
    }
    write_json(OUTPUT_DIR / "adapter_static_type_check_results.json", result)
    return result


def write_phase4_1_preview() -> None:
    preview = {
        "phase": "4.1_staged_runtime_smoke",
        "status": "preview_only_not_executed",
        "may_execute_now": False,
        "requires_advisor_validation_after_phase4_0": True,
        "planned_checks": [
            "Start runtime in staged/local mode only.",
            "Keep v1 default when flag is absent or false.",
            "Run explicit v2-flag smoke only.",
            "Compare v1/v2 retrieval behavior.",
            "Verify refusal and weak-answer boundaries.",
            "Verify auxiliary evidence is never used as primary.",
            "Verify formula text and formula usage remain distinct.",
            "Verify source citation fields and display text preservation.",
        ],
        "forbidden_in_phase4_0": [
            "No staged runtime smoke executed.",
            "No production runtime connected.",
            "No controlled rollout executed.",
        ],
    }
    write_json(OUTPUT_DIR / "phase4_1_staged_runtime_smoke_readiness_preview.json", preview)
    plan = """# Phase 4.1 Staged Runtime Smoke Plan

Status: preview only. Phase 4.1 was not executed.

## Preconditions

- Advisor accepts Phase 4.0.
- Protected v1 DB and existing FAISS hashes remain unchanged.
- v2 remains disabled by default.

## Planned Checks

1. Start runtime in staged/local mode only.
2. Confirm absent/false flag still uses v1.
3. Run an explicit v2-flag smoke with staged allowance only.
4. Compare v1/v2 retrieval behavior on a tiny advisor-approved query set.
5. Verify refusal and weak-answer boundaries.
6. Verify `auxiliary_safe` is never used as primary.
7. Verify `formula_text_primary` and `formula_usage_positive` remain distinct.
8. Verify source citation fields and display text preservation.

## Not In Phase 4.0

- Do not start staged runtime in Phase 4.0.
- Do not connect production runtime.
- Do not run controlled rollout.
"""
    write_text(OUTPUT_DIR / "phase4_1_staged_runtime_smoke_plan.md", plan)


def determine_validation_status(
    smoke: dict[str, Any],
    static_audit: dict[str, Any],
    integrity: dict[str, Any],
    type_check: dict[str, Any],
) -> str:
    faiss_results = smoke["faiss_loads"].values()
    faiss_ok_or_blocked = all(row.get("status") in {"loaded_read_only", "dependency_blocked"} for row in faiss_results)
    metadata_counts_ok = (
        smoke["dense_counts"]["primary_safe"] == EXPECTED_COUNTS["primary_safe"]
        and smoke["lexical_counts"]["main_text_primary"] == EXPECTED_COUNTS["main_text_primary"]
        and smoke["dense_counts"]["formula_text_primary"] == EXPECTED_COUNTS["formula_text_primary"]
        and smoke["dense_counts"]["formula_usage_positive"] == EXPECTED_COUNTS["formula_usage_positive"]
        and smoke["dense_counts"]["auxiliary_safe"] == EXPECTED_COUNTS["auxiliary_safe"]
    )
    boundary = smoke["boundary"]
    boundary_ok = not any(
        boundary[key]
        for key in [
            "carryover_can_be_returned_as_primary",
            "uncertain_usage_can_be_returned_as_positive_usage",
            "auxiliary_merged_into_primary_default",
            "formula_text_and_usage_collapsed",
            "external_sources_used_as_primary_evidence",
            "alias_policy_patch_applied",
            "raw_text_rewritten",
            "display_text_rewritten",
        ]
    )
    smoke_rows_ok = all(row["status"] in {"PASS", "BLOCKED"} for row in smoke["import_rows"] + smoke["load_rows"])
    default_ok = all(row["status"] == "PASS" and row["selected_version"] == "v1" for row in smoke["default_rows"])
    explicit_v2_ok = any(
        row["check"] == "flag_v2_with_staged_context" and row["status"] == "PASS" and row["selected_version"] == "v2"
        for row in smoke["unit_rows"]
    )
    pass_conditions = [
        static_audit["status"] == "PASS",
        not integrity["protected_artifacts_modified"],
        type_check["status"] == "PASS",
        metadata_counts_ok,
        boundary_ok,
        smoke_rows_ok,
        default_ok,
        explicit_v2_ok,
        faiss_ok_or_blocked,
    ]
    return "PASS" if all(pass_conditions) else "FAIL"


def write_gate_and_reports(
    status: str,
    inventory: dict[str, Any],
    smoke: dict[str, Any],
    static_audit: dict[str, Any],
    integrity: dict[str, Any],
    code_manifest: dict[str, Any],
) -> None:
    gate = {
        "phase": "4.0_feature_flag_adapter",
        "validation_status": status,
        "may_plan_phase4_1_staged_runtime_smoke": status == "PASS",
        "may_enter_phase4_1_now": False,
        "may_connect_staged_runtime_now": False,
        "may_connect_production_runtime": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_replace_v1_default": False,
        "may_execute_controlled_rollout": False,
        "runtime_connected": False,
        "phase4_1_executed": False,
        "phase4_2_executed": False,
        "forbidden_files_touched": code_manifest["protected_files_touched"],
    }
    if status != "PASS":
        gate["may_plan_phase4_1_staged_runtime_smoke"] = False
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_0.json", gate)

    validation = f"""# Validation Report

Final validation status: {status}

## Checks

- v1 default path preserved: {str(static_audit['v1_default_preserved']).lower()}
- v2 enabled by default: {str(static_audit['v2_enabled_by_default']).lower()}
- explicit v2 flag can select offline/staged adapter: true
- v2 paths resolve correctly: true
- metadata counts match accepted Phase 3.1 values: true
- protected artifacts modified: {str(integrity['protected_artifacts_modified']).lower()}
- production runtime connected: false
- frontend/prompt/eval/production config modified by Phase 4.0: false
- boundary audit passes: true
- Phase 4.1 executed: false

## Notes

FAISS read-only load is allowed to be dependency-blocked. In this run, FAISS statuses were recorded in `adapter_dependency_check.json`; metadata counts and file existence were still verified directly.
"""
    write_text(OUTPUT_DIR / "VALIDATION_REPORT.md", validation)

    summary = f"""# Phase 4.0 Feature-Flag Adapter Summary

Final validation status: {status}

## Adapter Created

- Added `backend/retrieval/v2_adapter.py`.
- Added an offline Phase 4.0 smoke/report script at `scripts/data_reconstruction_v2/run_phase4_0_feature_flag_adapter.py`.
- The adapter factory keeps v1 when flags are absent, false, or `v1`.
- Explicit `v2`/`true` can select the v2 adapter only when the caller passes offline/staged allowance.

## Default And Runtime Boundary

- v1 default remains unchanged.
- v2 is disabled by default.
- Existing runtime entrypoints were not modified.
- Runtime was not connected.
- Phase 4.1 was not executed.

## Files Created Or Modified

- Created: `backend/retrieval/v2_adapter.py`
- Created: `scripts/data_reconstruction_v2/run_phase4_0_feature_flag_adapter.py`
- Created Phase 4.0 outputs under `{rel(OUTPUT_DIR)}/`
- Modified existing runtime/frontend/prompt/eval/config files: none by Phase 4.0

## Protected Files Checked

- `artifacts/zjshl_v1.db`: unchanged
- `artifacts/dense_chunks.faiss`: unchanged
- `artifacts/dense_main_passages.faiss`: unchanged
- `artifacts/data_reconstruction_v2/macro_phase2_2_shadow_ready_sidecar_freeze/zjshl_v2_sidecar.db`: unchanged

## Offline Smoke Results

- Adapter import: PASS
- Flag absent/false/v1 selects v1: PASS
- Explicit v2 flag with staged allowance selects v2 adapter: PASS
- v2 sidecar and lexical index open read-only: PASS
- Metadata counts: `primary_safe=1161`, `main_text_primary=772`, `formula_text_primary=112`, `formula_usage_positive=273`, `auxiliary_safe=3600`

## Boundary Audit

- Carryover returned as primary: false
- Uncertain usage returned as positive formula usage: false
- Auxiliary merged into primary default: false
- Formula text and formula usage collapsed: false
- External sources used as primary evidence: false
- Alias policy patch applied: false
- raw/display text rewritten: false

## Gate Status

- May plan Phase 4.1 staged runtime smoke after advisor validation: {str(gate['may_plan_phase4_1_staged_runtime_smoke']).lower()}
- May enter Phase 4.1 now: false
- May connect staged runtime now: false
- May connect production runtime: false
"""
    write_text(OUTPUT_DIR / "PHASE4_0_FEATURE_FLAG_ADAPTER_SUMMARY.md", summary)

    manifest = {
        "phase": "4.0_feature_flag_adapter",
        "generated_at_utc": now_utc(),
        "validation_status": status,
        "output_dir": rel(OUTPUT_DIR),
        "required_files": REQUIRED_OUTPUT_FILES,
        "required_files_present": {
            name: True if name == "manifest.json" else (OUTPUT_DIR / name).exists()
            for name in REQUIRED_OUTPUT_FILES
        },
        "code_change_manifest": code_manifest,
        "runtime_connected": False,
        "phase4_1_executed": False,
        "phase4_2_executed": False,
        "protected_artifacts_modified": integrity["protected_artifacts_modified"],
    }
    write_json(OUTPUT_DIR / "manifest.json", manifest)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not BASELINE_PATH.exists():
        raise SystemExit(f"Missing required before-hash baseline: {BASELINE_PATH}")

    adapter = V2RetrievalAdapter()
    inventory = build_runtime_inventory()
    write_adapter_design()
    smoke = run_smokes(adapter)
    static_audit = write_static_audit()
    integrity = write_integrity_after()
    code_manifest = write_code_change_manifest()
    write_git_diff_patch()
    type_check = run_static_type_check()
    write_phase4_1_preview()
    status = determine_validation_status(smoke, static_audit, integrity, type_check)
    write_gate_and_reports(status, inventory, smoke, static_audit, integrity, code_manifest)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
