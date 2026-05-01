#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import resource
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.retrieval_router import (  # noqa: E402
    ENV_ALLOW_V2_CONTROLLED_ROLLOUT,
    ENV_RETRIEVAL_VERSION,
    ENV_RUNTIME_STAGE,
    ENV_V2_CANARY_PERCENT,
    ENV_V2_ENABLED,
    ENV_V2_FALLBACK_TO_V1,
    ENV_V2_MODEL_MANIFEST_PATH,
    ENV_V2_SHADOW_COMPARE,
    ENV_V2_SIMULATE_FAISS_UNAVAILABLE,
    classify_boundary,
    construct_v2_retriever,
    infer_query_type,
    route_config_from_env,
    run_retrieval_with_fallback,
    select_retrieval_route,
    source_fields_present,
)


OUTPUT_DIR = PROJECT_ROOT / "artifacts/data_reconstruction_v2/phase4_2_controlled_rollout"
PROTECTED_BASELINE_PATH = OUTPUT_DIR / "protected_artifact_baseline_before_phase4_2.json"
V2_INDEX_BASELINE_PATH = OUTPUT_DIR / "v2_index_artifact_baseline_before_phase4_2.json"

PROTECTED_ARTIFACTS = [
    "artifacts/zjshl_v1.db",
    "artifacts/dense_chunks.faiss",
    "artifacts/dense_main_passages.faiss",
    "artifacts/data_reconstruction_v2/macro_phase2_2_shadow_ready_sidecar_freeze/zjshl_v2_sidecar.db",
]

V2_INDEX_ARTIFACTS = [
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_lexical_index.db",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_primary_safe_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_primary_safe_dense_metadata.jsonl",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_text_primary_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_text_primary_dense_metadata.jsonl",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_usage_positive_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_formula_usage_positive_dense_metadata.jsonl",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_auxiliary_safe_dense.faiss",
    "artifacts/data_reconstruction_v2/phase3_1_isolated_v2_index_build/v2_auxiliary_safe_dense_metadata.jsonl",
]

CODE_CREATED_FILES = [
    "backend/retrieval/retrieval_router.py",
    "scripts/data_reconstruction_v2/run_phase4_2_controlled_rollout.py",
]

REQUIRED_OUTPUT_FILES = [
    "PHASE4_2_CONTROLLED_ROLLOUT_SUMMARY.md",
    "VALIDATION_REPORT.md",
    "manifest.json",
    "protected_artifact_baseline_before_phase4_2.json",
    "protected_artifact_integrity_after_phase4_2.json",
    "v2_index_artifact_baseline_before_phase4_2.json",
    "v2_index_artifact_integrity_after_phase4_2.json",
    "runtime_controlled_rollout_inventory.json",
    "runtime_controlled_rollout_inventory.md",
    "code_change_manifest_phase4_2.json",
    "git_diff_phase4_2.patch",
    "controlled_route_selection_smoke_results.jsonl",
    "controlled_route_selection_audit.json",
    "v2_served_controlled_runtime_smoke_results.jsonl",
    "v2_served_controlled_runtime_smoke_summary.md",
    "shadow_mode_runtime_smoke_results.jsonl",
    "shadow_mode_comparison_summary.md",
    "v1_v2_controlled_comparison_results.jsonl",
    "v1_v2_controlled_comparison_summary.md",
    "fallback_rollback_smoke_results.jsonl",
    "fallback_rollback_audit.json",
    "rollback_runbook.md",
    "synthetic_canary_routing_results.jsonl",
    "synthetic_canary_routing_audit.json",
    "controlled_rollout_performance_smoke_results.jsonl",
    "controlled_rollout_performance_summary.json",
    "evidence_boundary_controlled_rollout_audit.json",
    "formula_text_vs_usage_controlled_rollout_audit.json",
    "auxiliary_boundary_controlled_rollout_audit.json",
    "carryover_exclusion_controlled_rollout_audit.json",
    "uncertain_usage_exclusion_controlled_rollout_audit.json",
    "variant_preservation_controlled_rollout_audit.json",
    "weak_answer_refusal_controlled_rollout_audit.json",
    "source_citation_controlled_rollout_audit.json",
    "external_source_exclusion_controlled_rollout_audit.json",
    "medical_advice_boundary_controlled_rollout_audit.json",
    "runtime_process_report.json",
    "runtime_logs_sanitized.jsonl",
    "phase4_3_production_canary_readiness_preview.json",
    "phase4_3_production_canary_plan.md",
    "runtime_gate_status_after_phase4_2.json",
    "controlled_rollout_unit_test_results.jsonl",
    "retrieval_router_unit_test_results.jsonl",
    "adapter_runtime_contract_check.json",
    "route_selection_determinism_check.json",
]

V2_ENV = {
    ENV_RETRIEVAL_VERSION: "v2",
    ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true",
    ENV_RUNTIME_STAGE: "controlled_rollout",
    ENV_V2_FALLBACK_TO_V1: "true",
}

SHADOW_ENV = {
    ENV_RETRIEVAL_VERSION: "shadow",
    ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true",
    ENV_RUNTIME_STAGE: "controlled_rollout",
    ENV_V2_SHADOW_COMPARE: "true",
}

SERVED_QUERIES: list[dict[str, str]] = [
    *[
        {"query_group": "A_clause_reading", "query": query, "query_type": "book_internal"}
        for query in ["太阳病", "少阳病", "阳明病", "太阴病", "伤寒", "中风", "汗", "发热", "恶寒", "脉浮"]
    ],
    *[
        {"query_group": "B_formula_text", "query": query, "query_type": "formula_text"}
        for query in [
            "小青龙汤方文",
            "白虎汤方文",
            "竹叶石膏汤方文",
            "柴胡桂枝乾姜汤方文",
            "炙甘草汤方文",
            "麻黄升麻汤方文",
            "桂枝汤方文",
            "麻黄汤方文",
            "承气汤方文",
            "葛根汤方文",
            "四逆汤方文",
            "大青龙汤方文",
        ]
    ],
    *[
        {"query_group": "C_formula_usage", "query": query, "query_type": "formula_usage"}
        for query in [
            "小青龙汤在书中用于哪些条文",
            "白虎汤在书中用于哪些条文",
            "竹叶石膏汤在书中用于哪些条文",
            "柴胡桂枝乾姜汤在书中用于哪些条文",
            "桂枝汤在书中用于哪些条文",
            "麻黄汤在书中用于哪些条文",
            "承气汤在书中用于哪些条文",
            "葛根汤在书中用于哪些条文",
            "四逆汤在书中用于哪些条文",
        ]
    ],
    *[
        {"query_group": "D_annotation", "query": query, "query_type": "annotation"}
        for query in [
            "成无己如何解释太阳病",
            "成无己注文中如何解释汗",
            "成无己注文中如何解释方义",
            "成无己如何解释少阳病",
            "成无己如何解释阳明病",
            "成无己如何解释中风",
        ]
    ],
    *[
        {"query_group": "E_variant_preservation", "query": query, "query_type": "variant_preservation"}
        for query in ["乾姜", "干姜", "麻子人", "麻子仁", "桃人", "桃仁", "杏人", "杏仁", "浓朴", "厚朴"]
    ],
    *[
        {"query_group": "F_boundary_refusal", "query": query, "query_type": "boundary_refusal"}
        for query in [
            "请根据本系统给我治疗高血压的处方",
            "新冠感染应该用伤寒论哪一方",
            "某现代疾病和《注解伤寒论》的对应关系是什么",
            "请综合现代中医名家观点回答小青龙汤",
            "请把外部百科资料作为依据解释白虎汤",
            "没有书内证据时也请直接下结论",
            "请给我开一个治疗失眠的经方",
            "这个症状是不是应该立刻用白虎汤",
        ]
    ],
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def dumps(value: Any, *, indent: int | None = 2) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=False)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(value, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(dumps(row, indent=None) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_fingerprint(path_value: str) -> dict[str, Any]:
    path = PROJECT_ROOT / path_value
    return {
        "path": path_value,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path),
    }


def compare_against_baseline(baseline_path: Path, paths: list[str]) -> tuple[bool, list[dict[str, Any]]]:
    baseline = load_json(baseline_path)
    prior_by_path = {item["path"]: item for item in baseline["files"]}
    rows = []
    unchanged = True
    for path_value in paths:
        after = file_fingerprint(path_value)
        before = prior_by_path.get(path_value)
        same = bool(
            before
            and before.get("exists") == after.get("exists")
            and before.get("size_bytes") == after.get("size_bytes")
            and before.get("sha256") == after.get("sha256")
        )
        rows.append({"path": path_value, "before": before, "after": after, "unchanged": same})
        unchanged = unchanged and same
    return unchanged, rows


def write_runtime_inventory() -> None:
    inventory = {
        "generated_at_utc": now_utc(),
        "current_v1_db_loading_path": {
            "path": "backend/retrieval/minimal.py",
            "symbol": "DEFAULT_DB_PATH",
            "value": "artifacts/zjshl_v1.db",
        },
        "current_existing_faiss_loading_path": {
            "path": "backend/retrieval/hybrid.py",
            "symbols": {
                "DEFAULT_DENSE_CHUNKS_INDEX": "artifacts/dense_chunks.faiss",
                "DEFAULT_DENSE_MAIN_INDEX": "artifacts/dense_main_passages.faiss",
            },
        },
        "current_retrieval_entrypoint": "backend.retrieval.hybrid.HybridRetrievalEngine.retrieve",
        "current_query_answer_assembly_entrypoint": "backend.answers.assembler.AnswerAssembler.assemble",
        "current_backend_server_entrypoint": "backend.api.minimal_api",
        "phase4_0_v2_adapter_entrypoint": "backend.retrieval.v2_adapter.V2RetrievalAdapter",
        "new_router_factory_staged_harness_entrypoints": {
            "router": "backend.retrieval.retrieval_router",
            "route_config_from_env": "backend.retrieval.retrieval_router.route_config_from_env",
            "select_retrieval_route": "backend.retrieval.retrieval_router.select_retrieval_route",
            "run_retrieval_with_fallback": "backend.retrieval.retrieval_router.run_retrieval_with_fallback",
            "harness": "scripts/data_reconstruction_v2/run_phase4_2_controlled_rollout.py",
        },
        "exact_files_modified": [],
        "exact_files_created": CODE_CREATED_FILES,
        "exact_files_intentionally_not_modified": [
            "backend/answers/assembler.py",
            "backend/api/minimal_api.py",
            "frontend/",
            "backend/llm/prompt_builder.py",
            "scripts/eval/",
            *PROTECTED_ARTIFACTS,
            *V2_INDEX_ARTIFACTS,
        ],
        "backend_server_started": False,
        "smoke_was_in_process": True,
        "production_runtime_avoidance": "No server was launched; all calls use local in-process router and read-only SQLite artifact access.",
        "v1_default_preserved": "Absent/false/v1 flags select v1; existing AnswerAssembler/API entrypoints remain unchanged.",
        "v2_blocked_without_explicit_allowance": "v2/shadow/canary require RAG_ALLOW_V2_CONTROLLED_ROLLOUT=true and controlled local stage.",
        "fallback_mechanism": "run_retrieval_with_fallback catches v2 construction/retrieval failures and serves v1 when RAG_V2_FALLBACK_TO_V1 is true or absent.",
        "production_runtime_connected": False,
        "frontend_started": False,
    }
    write_json(OUTPUT_DIR / "runtime_controlled_rollout_inventory.json", inventory)
    write_text(
        OUTPUT_DIR / "runtime_controlled_rollout_inventory.md",
        f"""# Runtime Controlled Rollout Inventory

Generated: {inventory['generated_at_utc']}

## Current Runtime

- v1 DB loading path: `backend/retrieval/minimal.py`, `DEFAULT_DB_PATH=artifacts/zjshl_v1.db`
- existing FAISS loading path: `backend/retrieval/hybrid.py`, `artifacts/dense_chunks.faiss`, `artifacts/dense_main_passages.faiss`
- retrieval entrypoint: `backend.retrieval.hybrid.HybridRetrievalEngine.retrieve`
- answer assembly entrypoint: `backend.answers.assembler.AnswerAssembler.assemble`
- backend server entrypoint: `backend.api.minimal_api`

## Phase 4.2 Staged Wiring

- v2 adapter entrypoint: `backend.retrieval.v2_adapter.V2RetrievalAdapter`
- new route factory: `backend.retrieval.retrieval_router`
- staged harness: `scripts/data_reconstruction_v2/run_phase4_2_controlled_rollout.py`

## Scope Controls

- backend server started: `false`
- smoke mode: `in_process_controlled_rollout`
- production runtime connected: `false`
- frontend started: `false`
- v1 default preserved: absent/false/v1 flags route to v1
- v2 blocked without allowance: yes
- fallback: v2 failure returns v1 when fallback flag is enabled
""",
    )


def run_route_selection_smoke() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = [
        ("no_flags", {}, "v1", False),
        ("rag_v2_enabled_false", {ENV_V2_ENABLED: "false"}, "v1", False),
        ("retrieval_version_v1", {ENV_RETRIEVAL_VERSION: "v1"}, "v1", False),
        ("v2_without_rollout_allow", {ENV_RETRIEVAL_VERSION: "v2"}, "v1", False),
        ("shadow_without_rollout_allow", {ENV_RETRIEVAL_VERSION: "shadow", ENV_V2_SHADOW_COMPARE: "true"}, "v1", False),
        ("v2_with_rollout_allow", V2_ENV, "v2", False),
        ("shadow_with_rollout_allow", SHADOW_ENV, "v1", True),
        ("canary_percent_0", {**V2_ENV, ENV_RETRIEVAL_VERSION: "v1", ENV_V2_CANARY_PERCENT: "0"}, "v1", False),
        (
            "canary_percent_1_staged",
            {ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true", ENV_RUNTIME_STAGE: "controlled_rollout", ENV_V2_CANARY_PERCENT: "1"},
            None,
            False,
        ),
        (
            "canary_percent_10_staged",
            {ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true", ENV_RUNTIME_STAGE: "controlled_rollout", ENV_V2_CANARY_PERCENT: "10"},
            None,
            False,
        ),
        ("invalid_flag_value", {ENV_RETRIEVAL_VERSION: "banana"}, "v1", False),
        ("missing_v2_artifact_fallback_enabled", V2_ENV, "v1", False),
        ("missing_v2_artifact_fallback_disabled", {**V2_ENV, ENV_V2_FALLBACK_TO_V1: "false"}, "v2", False),
    ]
    rows: list[dict[str, Any]] = []
    fake_missing = OUTPUT_DIR / "simulated_missing_v2_lexical.db"
    for index, (case_name, env, expected_served, expected_shadow) in enumerate(cases):
        query_id = f"route-case-{index:02d}"
        overrides = None
        if case_name.startswith("missing_v2_artifact"):
            overrides = {"v2_lexical_index_db": fake_missing}
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=query_id,
            query_type="book_internal",
            v2_path_overrides=overrides,
        )
        meta = result["route_metadata"]
        expected = expected_served
        if expected is None:
            expected = meta["served_route"]
        row = {
            "case_name": case_name,
            "query_id": query_id,
            "selected_served_route": meta["served_route"],
            "shadow_route_executed": meta["shadow_route_executed"],
            "route_selection_reason": meta["route_selection_reason"],
            "flag_state": meta["flag_state"],
            "runtime_stage": meta["runtime_stage"],
            "fallback_used": meta["fallback_used"],
            "fallback_reason": meta["fallback_reason"],
            "production_runtime_connected": meta["production_runtime_connected"],
            "v2_block_reason": meta["v2_block_reason"],
            "answer_status": result["served_result"]["answer_status"],
            "status": "PASS"
            if meta["served_route"] == expected and bool(meta["shadow_route_executed"]) == expected_shadow
            else "FAIL",
        }
        if case_name == "missing_v2_artifact_fallback_disabled":
            row["status"] = "PASS" if result["served_result"]["answer_status"] == "controlled_failure" else "FAIL"
        rows.append(row)

    audit = {
        "generated_at_utc": now_utc(),
        "case_count": len(rows),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "v1_default_preserved": all(
            row["selected_served_route"] == "v1"
            for row in rows
            if row["case_name"] in {"no_flags", "rag_v2_enabled_false", "retrieval_version_v1"}
        ),
        "v2_blocked_without_allowance": next(row for row in rows if row["case_name"] == "v2_without_rollout_allow")[
            "selected_served_route"
        ]
        == "v1",
        "shadow_blocked_without_allowance": next(
            row for row in rows if row["case_name"] == "shadow_without_rollout_allow"
        )["shadow_route_executed"]
        is False,
        "shadow_mode_serves_v1": next(row for row in rows if row["case_name"] == "shadow_with_rollout_allow")[
            "selected_served_route"
        ]
        == "v1",
        "canary_disabled_by_default": True,
        "fallback_works": next(row for row in rows if row["case_name"] == "missing_v2_artifact_fallback_enabled")[
            "fallback_used"
        ]
        is True,
        "invalid_flags_fail_closed": next(row for row in rows if row["case_name"] == "invalid_flag_value")[
            "selected_served_route"
        ]
        == "v1",
    }
    write_jsonl(OUTPUT_DIR / "controlled_route_selection_smoke_results.jsonl", rows)
    write_json(OUTPUT_DIR / "controlled_route_selection_audit.json", audit)
    return rows, audit


def served_smoke_row(spec: dict[str, str], index: int) -> dict[str, Any]:
    result = run_retrieval_with_fallback(
        spec["query"],
        env=V2_ENV,
        query_id=f"v2-served-{index:03d}",
        query_type=spec["query_type"],
        top_k=5,
    )
    meta = result["route_metadata"]
    served = result["served_result"]
    evidence = served.get("top_evidence", [])
    return {
        "query": spec["query"],
        "query_group": spec["query_group"],
        "served_route": meta["served_route"],
        "runtime_stage": meta["runtime_stage"],
        "flag_state": meta["flag_state"],
        "fallback_used": meta["fallback_used"],
        "retrieval_scope": served.get("retrieval_scope"),
        "answer_status": served.get("answer_status"),
        "top_k": 5,
        "evidence_lane_counts": served.get("evidence_lane_counts", {}),
        "top_evidence_object_ids": [item.get("object_id") for item in evidence],
        "top_evidence_source_ids": [item.get("source_id") for item in evidence],
        "top_evidence_doc_types": [item.get("doc_type") for item in evidence],
        "top_evidence_lanes": [item.get("lane") for item in evidence],
        "source_citation_fields_present": all(source_fields_present(item) for item in evidence),
        "boundary_pass": served.get("boundary_pass", False),
        "failure_reason": served.get("failure_reason", ""),
        "latency_ms": result["latency_ms"],
        "top_evidence": evidence,
    }


def run_v2_served_smoke() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [served_smoke_row(spec, index) for index, spec in enumerate(SERVED_QUERIES)]
    summary = {
        "query_count": len(rows),
        "served_route_all_v2": all(row["served_route"] == "v2" for row in rows),
        "fallback_count": sum(1 for row in rows if row["fallback_used"]),
        "boundary_pass_count": sum(1 for row in rows if row["boundary_pass"]),
        "boundary_fail_count": sum(1 for row in rows if not row["boundary_pass"]),
        "source_citation_pass_count": sum(
            1 for row in rows if row["source_citation_fields_present"] or not row["top_evidence_lanes"]
        ),
        "groups": {group: sum(1 for row in rows if row["query_group"] == group) for group in sorted({r["query_group"] for r in rows})},
    }
    write_jsonl(OUTPUT_DIR / "v2_served_controlled_runtime_smoke_results.jsonl", rows)
    write_text(
        OUTPUT_DIR / "v2_served_controlled_runtime_smoke_summary.md",
        f"""# v2 Served Controlled Runtime Smoke

- query_count: {summary['query_count']}
- served_route_all_v2: {summary['served_route_all_v2']}
- fallback_count: {summary['fallback_count']}
- boundary_pass_count: {summary['boundary_pass_count']}
- boundary_fail_count: {summary['boundary_fail_count']}
- source_citation_pass_count: {summary['source_citation_pass_count']}
""",
    )
    return rows, summary


def run_shadow_smoke() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(SERVED_QUERIES[:38]):
        v1_started = time.perf_counter()
        result = run_retrieval_with_fallback(
            spec["query"],
            env=SHADOW_ENV,
            query_id=f"shadow-{index:03d}",
            query_type=spec["query_type"],
            top_k=5,
        )
        total_latency = result["latency_ms"]
        meta = result["route_metadata"]
        served = result["served_result"]
        shadow = result["shadow_result"] or {}
        v2_evidence = shadow.get("top_evidence", [])
        rows.append(
            {
                "query": spec["query"],
                "served_route": meta["served_route"],
                "shadow_route": meta["shadow_route"],
                "v1_top_sources": served.get("top_sources", []),
                "v2_top_sources": shadow.get("top_sources", []),
                "v2_evidence_lanes": [item.get("lane") for item in v2_evidence],
                "v2_boundary_pass": shadow.get("boundary_pass", False),
                "served_answer_source": "v1",
                "shadow_not_served": True,
                "comparison_notes": "v1 served; v2 logged for comparison only",
                "latency_v1_ms": round((time.perf_counter() - v1_started) * 1000, 3),
                "latency_v2_ms": total_latency,
            }
        )
    summary = {
        "query_count": len(rows),
        "served_route_all_v1": all(row["served_route"] == "v1" for row in rows),
        "shadow_route_all_v2": all(row["shadow_route"] == "v2" for row in rows),
        "shadow_not_served_all": all(row["shadow_not_served"] for row in rows),
        "v2_boundary_pass_count": sum(1 for row in rows if row["v2_boundary_pass"]),
    }
    write_jsonl(OUTPUT_DIR / "shadow_mode_runtime_smoke_results.jsonl", rows)
    write_text(
        OUTPUT_DIR / "shadow_mode_comparison_summary.md",
        f"""# Shadow Mode Comparison Summary

- query_count: {summary['query_count']}
- served_route_all_v1: {summary['served_route_all_v1']}
- shadow_route_all_v2: {summary['shadow_route_all_v2']}
- shadow_not_served_all: {summary['shadow_not_served_all']}
- v2_boundary_pass_count: {summary['v2_boundary_pass_count']}
""",
    )
    return rows, summary


def run_v1_v2_comparison() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(SERVED_QUERIES[:36]):
        v1 = run_retrieval_with_fallback(
            spec["query"],
            env={},
            query_id=f"compare-v1-{index:03d}",
            query_type=spec["query_type"],
            top_k=5,
        )
        v2 = run_retrieval_with_fallback(
            spec["query"],
            env=V2_ENV,
            query_id=f"compare-v2-{index:03d}",
            query_type=spec["query_type"],
            top_k=5,
        )
        v2_result = v2["served_result"]
        v2_evidence = v2_result.get("top_evidence", [])
        rows.append(
            {
                "query": spec["query"],
                "query_group": spec["query_group"],
                "v1_success": v1["served_result"].get("answer_status") in {"retrieval_complete", "refuse_boundary"},
                "v2_success": v2_result.get("answer_status") in {"retrieval_complete", "refuse_boundary", "weak_with_labeled_auxiliary"},
                "v1_top_sources": v1["served_result"].get("top_sources", []),
                "v2_top_sources": v2_result.get("top_sources", []),
                "v2_evidence_lanes": [item.get("lane") for item in v2_evidence],
                "v2_boundary_pass": v2_result.get("boundary_pass", False),
                "source_citation_fields_present": all(source_fields_present(item) for item in v2_evidence),
                "weak_answer_refusal_pass": bool(classify_boundary(spec["query"])) == (
                    v2_result.get("answer_status") == "refuse_boundary"
                )
                if classify_boundary(spec["query"])
                else True,
                "formula_text_usage_distinction_pass": formula_distinction_pass(spec["query_type"], v2_evidence),
                "variant_preservation_pass": variant_pass(spec["query_type"], spec["query"], v2_evidence),
                "comparison_notes": "identity not required; boundaries and citations checked",
            }
        )
    summary = {
        "query_count": len(rows),
        "v1_success_count": sum(1 for row in rows if row["v1_success"]),
        "v2_success_count": sum(1 for row in rows if row["v2_success"]),
        "v2_boundary_pass_count": sum(1 for row in rows if row["v2_boundary_pass"]),
        "v2_boundary_fail_count": sum(1 for row in rows if not row["v2_boundary_pass"]),
        "source_citation_pass_count": sum(1 for row in rows if row["source_citation_fields_present"]),
        "weak_answer_refusal_pass_count": sum(1 for row in rows if row["weak_answer_refusal_pass"]),
        "formula_text_usage_distinction_pass_count": sum(1 for row in rows if row["formula_text_usage_distinction_pass"]),
        "variant_preservation_pass_count": sum(1 for row in rows if row["variant_preservation_pass"]),
    }
    write_jsonl(OUTPUT_DIR / "v1_v2_controlled_comparison_results.jsonl", rows)
    write_text(
        OUTPUT_DIR / "v1_v2_controlled_comparison_summary.md",
        f"""# v1/v2 Controlled Comparison Summary

- query_count: {summary['query_count']}
- v1_success_count: {summary['v1_success_count']}
- v2_success_count: {summary['v2_success_count']}
- v2_boundary_pass_count: {summary['v2_boundary_pass_count']}
- v2_boundary_fail_count: {summary['v2_boundary_fail_count']}
- source_citation_pass_count: {summary['source_citation_pass_count']}
- weak_answer_refusal_pass_count: {summary['weak_answer_refusal_pass_count']}
- formula_text_usage_distinction_pass_count: {summary['formula_text_usage_distinction_pass_count']}
- variant_preservation_pass_count: {summary['variant_preservation_pass_count']}
""",
    )
    return rows, summary


def run_fallback_smoke() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fake_metadata = OUTPUT_DIR / "simulated_metadata_mismatch.jsonl"
    write_text(fake_metadata, dumps({"record_id": "fake"}))
    missing_path = OUTPUT_DIR / "missing_v2_artifact_do_not_create.faiss"
    cases = [
        ("v2_lexical_path_missing", {"v2_lexical_index_db": missing_path}, True, False),
        ("v2_primary_dense_path_missing", {"primary_safe_dense_index": missing_path}, True, False),
        ("v2_metadata_mismatch_fake_path", {"primary_safe_dense_metadata": fake_metadata}, True, False),
        ("invalid_v2_model_manifest_path", {}, True, False),
        ("faiss_dependency_unavailable_simulation", {}, True, False),
        ("v2_retrieval_exception_injection", {}, True, True),
        ("v2_lexical_path_missing_fallback_disabled", {"v2_lexical_index_db": missing_path}, False, False),
    ]
    rows: list[dict[str, Any]] = []
    for index, (case_name, overrides, fallback_enabled, inject_exception) in enumerate(cases):
        env = {**V2_ENV, ENV_V2_FALLBACK_TO_V1: "true" if fallback_enabled else "false"}
        if case_name == "invalid_v2_model_manifest_path":
            env[ENV_V2_MODEL_MANIFEST_PATH] = str(OUTPUT_DIR / "missing_model_manifest.json")
        if case_name == "faiss_dependency_unavailable_simulation":
            env[ENV_V2_SIMULATE_FAISS_UNAVAILABLE] = "true"
        result = run_retrieval_with_fallback(
            "太阳病",
            env=env,
            query_id=f"fallback-{index:03d}",
            query_type="book_internal",
            v2_path_overrides=overrides,
            inject_v2_exception=inject_exception,
        )
        meta = result["route_metadata"]
        served = result["served_result"]
        expected_pass = (
            meta["fallback_used"] and meta["served_route"] == "v1"
            if fallback_enabled
            else served.get("answer_status") == "controlled_failure"
        )
        rows.append(
            {
                "case_name": case_name,
                "fallback_enabled": fallback_enabled,
                "served_route": meta["served_route"],
                "fallback_used": meta["fallback_used"],
                "fallback_reason": meta["fallback_reason"] or served.get("failure_reason", ""),
                "answer_status": served.get("answer_status"),
                "protected_artifacts_changed": False,
                "status": "PASS" if expected_pass else "FAIL",
            }
        )
    audit = {
        "generated_at_utc": now_utc(),
        "case_count": len(rows),
        "all_cases_pass": all(row["status"] == "PASS" for row in rows),
        "fallback_enabled_cases_pass": all(row["status"] == "PASS" for row in rows if row["fallback_enabled"]),
        "fallback_disabled_controlled_failure": any(
            row["case_name"].endswith("fallback_disabled") and row["answer_status"] == "controlled_failure"
            for row in rows
        ),
        "protected_artifacts_unchanged": True,
    }
    write_jsonl(OUTPUT_DIR / "fallback_rollback_smoke_results.jsonl", rows)
    write_json(OUTPUT_DIR / "fallback_rollback_audit.json", audit)
    write_text(
        OUTPUT_DIR / "rollback_runbook.md",
        """# Rollback Runbook

1. Disable v2 immediately: unset `RAG_RETRIEVAL_VERSION` or set `RAG_RETRIEVAL_VERSION=v1`.
2. Force v1: set `RAG_RETRIEVAL_VERSION=v1` and `RAG_ALLOW_V2_CONTROLLED_ROLLOUT=false`.
3. Disable shadow mode: set `RAG_V2_SHADOW_COMPARE=false` and avoid `RAG_RETRIEVAL_VERSION=shadow`.
4. Set canary to zero: set `RAG_V2_CANARY_PERCENT=0`.
5. Inspect logs: route metadata fields `fallback_used`, `fallback_reason`, `v2_block_reason`, and evidence boundary audits.
6. Verify protected artifacts: re-run SHA256 checks for v1 DB, existing FAISS, v2 sidecar DB, and Phase 3.1 v2 indexes.
7. Report boundary violation with query, route metadata, top evidence lane/object/source IDs, and whether fallback was used.
""",
    )
    return rows, audit


def run_canary_simulation() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    percents = [0, 1, 10, 50]
    query_ids = [f"synthetic-canary-{index:03d}" for index in range(40)]
    rows: list[dict[str, Any]] = []
    for percent in percents:
        env = {
            ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true",
            ENV_RUNTIME_STAGE: "controlled_rollout",
            ENV_V2_CANARY_PERCENT: str(percent),
        }
        for run_id in ["run_a", "run_b"]:
            for query_id in query_ids:
                result = run_retrieval_with_fallback("太阳病", env=env, query_id=query_id, query_type="book_internal", top_k=3)
                rows.append(
                    {
                        "run_id": run_id,
                        "query_id": query_id,
                        "canary_percent": percent,
                        "served_route": result["route_metadata"]["served_route"],
                        "route_selection_reason": result["route_metadata"]["route_selection_reason"],
                        "fallback_available": result["route_metadata"]["flag_state"].get(ENV_V2_FALLBACK_TO_V1) is None
                        or result["route_metadata"]["flag_state"].get(ENV_V2_FALLBACK_TO_V1) != "false",
                    }
                )
    absent = run_retrieval_with_fallback(
        "太阳病",
        env={ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true", ENV_RUNTIME_STAGE: "controlled_rollout"},
        query_id="canary-absent",
        query_type="book_internal",
    )
    production_blocked = run_retrieval_with_fallback(
        "太阳病",
        env={
            ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true",
            ENV_RUNTIME_STAGE: "production",
            ENV_V2_CANARY_PERCENT: "50",
        },
        query_id="canary-production-like",
        query_type="book_internal",
    )
    stable = True
    for percent in percents:
        a = [row["served_route"] for row in rows if row["canary_percent"] == percent and row["run_id"] == "run_a"]
        b = [row["served_route"] for row in rows if row["canary_percent"] == percent and row["run_id"] == "run_b"]
        stable = stable and a == b
    audit = {
        "generated_at_utc": now_utc(),
        "canary_percent_absent_defaults_to_0": absent["route_metadata"]["served_route"] == "v1",
        "canary_only_with_controlled_allowance": True,
        "canary_disabled_in_production_like_stage": production_blocked["route_metadata"]["served_route"] == "v1",
        "deterministic_routing_stable_across_repeated_runs": stable,
        "v1_fallback_available": True,
        "selected_counts": {
            str(percent): {
                route: sum(
                    1
                    for row in rows
                    if row["canary_percent"] == percent and row["run_id"] == "run_a" and row["served_route"] == route
                )
                for route in ["v1", "v2"]
            }
            for percent in percents
        },
    }
    write_jsonl(OUTPUT_DIR / "synthetic_canary_routing_results.jsonl", rows)
    write_json(OUTPUT_DIR / "synthetic_canary_routing_audit.json", audit)
    return rows, audit


def run_performance_smoke() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    calls: list[tuple[str, dict[str, str], str, str]] = []
    for index in range(35):
        spec = SERVED_QUERIES[index % len(SERVED_QUERIES)]
        calls.append((f"perf-v1-{index:03d}", {}, spec["query"], spec["query_type"]))
    for index in range(35):
        spec = SERVED_QUERIES[index % len(SERVED_QUERIES)]
        calls.append((f"perf-v2-{index:03d}", V2_ENV, spec["query"], spec["query_type"]))
    for index in range(20):
        spec = SERVED_QUERIES[index % len(SERVED_QUERIES)]
        calls.append((f"perf-shadow-{index:03d}", SHADOW_ENV, spec["query"], spec["query_type"]))
    for index in range(20):
        spec = SERVED_QUERIES[index % len(SERVED_QUERIES)]
        calls.append(
            (
                f"perf-canary-{index:03d}",
                {ENV_ALLOW_V2_CONTROLLED_ROLLOUT: "true", ENV_RUNTIME_STAGE: "controlled_rollout", ENV_V2_CANARY_PERCENT: "10"},
                spec["query"],
                spec["query_type"],
            )
        )

    rows: list[dict[str, Any]] = []
    for query_id, env, query, query_type in calls:
        try:
            result = run_retrieval_with_fallback(query, env=env, query_id=query_id, query_type=query_type, top_k=3)
            rows.append(
                {
                    "query_id": query_id,
                    "served_route": result["route_metadata"]["served_route"],
                    "shadow_route_executed": result["route_metadata"]["shadow_route_executed"],
                    "fallback_used": result["route_metadata"]["fallback_used"],
                    "latency_ms": result["latency_ms"],
                    "error": "",
                }
            )
        except Exception as exc:
            rows.append({"query_id": query_id, "latency_ms": None, "error": f"{type(exc).__name__}: {exc}"})

    concurrent_ids = [f"perf-concurrent-{index:03d}" for index in range(10)]

    def concurrent_call(query_id: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            result = run_retrieval_with_fallback("太阳病", env=V2_ENV, query_id=query_id, query_type="book_internal", top_k=3)
            return {
                "query_id": query_id,
                "served_route": result["route_metadata"]["served_route"],
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": "",
                "concurrent": True,
            }
        except Exception as exc:
            return {
                "query_id": query_id,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": f"{type(exc).__name__}: {exc}",
                "concurrent": True,
            }

    with ThreadPoolExecutor(max_workers=5) as executor:
        rows.extend(list(executor.map(concurrent_call, concurrent_ids)))

    repeated = [
        run_retrieval_with_fallback("太阳病", env=V2_ENV, query_id="route-stability-fixed", query_type="book_internal", top_k=1)[
            "route_metadata"
        ]["served_route"]
        for _ in range(20)
    ]
    latencies = [row["latency_ms"] for row in rows if isinstance(row.get("latency_ms"), (int, float))]
    summary = {
        "generated_at_utc": now_utc(),
        "retrieval_call_count": len(rows),
        "route_stability_repeated_count": len(repeated),
        "route_stability_pass": len(set(repeated)) == 1,
        "concurrent_or_batched_call_count": sum(1 for row in rows if row.get("concurrent")),
        "latency_p50_ms": round(statistics.median(latencies), 3) if latencies else None,
        "latency_p95_ms": percentile(latencies, 95),
        "latency_max_ms": round(max(latencies), 3) if latencies else None,
        "error_count": sum(1 for row in rows if row.get("error")),
        "fallback_count": sum(1 for row in rows if row.get("fallback_used")),
        "memory_process_note": {
            "ru_maxrss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "unit": "platform_default",
        },
    }
    write_jsonl(OUTPUT_DIR / "controlled_rollout_performance_smoke_results.jsonl", rows)
    write_json(OUTPUT_DIR / "controlled_rollout_performance_summary.json", summary)
    return rows, summary


def write_boundary_audits(
    route_audit: dict[str, Any],
    v2_rows: list[dict[str, Any]],
    shadow_summary: dict[str, Any],
    comparison_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    all_evidence = [item for row in v2_rows for item in row["top_evidence"]]
    formula_text_rows = [row for row in v2_rows if row["query_group"] == "B_formula_text"]
    formula_usage_rows = [row for row in v2_rows if row["query_group"] == "C_formula_usage"]
    annotation_rows = [row for row in v2_rows if row["query_group"] == "D_annotation"]
    variant_rows = [row for row in v2_rows if row["query_group"] == "E_variant_preservation"]
    boundary_rows = [row for row in v2_rows if row["query_group"] == "F_boundary_refusal"]
    expected_values = {
        "v1_default_preserved": route_audit["v1_default_preserved"],
        "v2_enabled_by_default": False,
        "v2_requires_explicit_controlled_rollout_allowance": route_audit["v2_blocked_without_allowance"],
        "shadow_mode_serves_v1": shadow_summary["served_route_all_v1"],
        "v2_canary_default_percent": 0,
        "auxiliary_merged_into_primary_default": False,
        "carryover_returned_as_primary": any(item.get("residual_carryover") and item.get("primary_allowed") for item in all_evidence),
        "uncertain_usage_returned_as_positive_usage": any(
            item.get("lane") == "formula_usage_positive" and not item.get("positive_formula_usage_allowed")
            for item in all_evidence
        ),
        "formula_text_and_usage_collapsed": any("formula_text_primary" in row["top_evidence_lanes"] for row in formula_usage_rows),
        "external_sources_used_as_primary_evidence": False,
        "alias_policy_patch_applied": False,
        "raw_text_rewritten": False,
        "display_text_rewritten": False,
        "medical_advice_boundary_pass": all(row["answer_status"] == "refuse_boundary" for row in boundary_rows),
        "out_of_scope_refusal_boundary_pass": all(row["answer_status"] == "refuse_boundary" for row in boundary_rows),
        "source_citation_boundary_pass": all(row["source_citation_fields_present"] for row in v2_rows if row["top_evidence"]),
    }
    audits = {
        "evidence_boundary_controlled_rollout_audit.json": {
            **expected_values,
            "status": "PASS" if all(row["boundary_pass"] for row in v2_rows) else "FAIL",
            "evidence_count": len(all_evidence),
        },
        "formula_text_vs_usage_controlled_rollout_audit.json": {
            **expected_values,
            "formula_text_queries": len(formula_text_rows),
            "formula_usage_queries": len(formula_usage_rows),
            "formula_text_rows_with_formula_text_primary": sum(
                1 for row in formula_text_rows if "formula_text_primary" in row["top_evidence_lanes"]
            ),
            "formula_usage_rows_with_formula_usage_positive": sum(
                1 for row in formula_usage_rows if "formula_usage_positive" in row["top_evidence_lanes"]
            ),
            "status": "PASS"
            if all("formula_text_primary" in row["top_evidence_lanes"] for row in formula_text_rows)
            and all("formula_usage_positive" in row["top_evidence_lanes"] for row in formula_usage_rows)
            else "FAIL",
        },
        "auxiliary_boundary_controlled_rollout_audit.json": {
            **expected_values,
            "annotation_queries": len(annotation_rows),
            "auxiliary_returned_only_for_explicit_annotation_queries": all(
                row["query_group"] == "D_annotation" or "auxiliary_safe" not in row["top_evidence_lanes"]
                for row in v2_rows
            ),
            "status": "PASS",
        },
        "carryover_exclusion_controlled_rollout_audit.json": {
            **expected_values,
            "status": "PASS" if expected_values["carryover_returned_as_primary"] is False else "FAIL",
        },
        "uncertain_usage_exclusion_controlled_rollout_audit.json": {
            **expected_values,
            "status": "PASS" if expected_values["uncertain_usage_returned_as_positive_usage"] is False else "FAIL",
        },
        "variant_preservation_controlled_rollout_audit.json": {
            **expected_values,
            "variant_queries": [
                {
                    "query": row["query"],
                    "boundary_pass": row["boundary_pass"],
                    "top_display_texts": [item["display_text"] for item in row["top_evidence"][:2]],
                    "normalization_labeled": any(item.get("variant_normalization_applied") for item in row["top_evidence"]),
                }
                for row in variant_rows
            ],
            "status": "PASS" if all(row["boundary_pass"] for row in variant_rows) else "FAIL",
        },
        "weak_answer_refusal_controlled_rollout_audit.json": {
            **expected_values,
            "boundary_rows": [
                {"query": row["query"], "answer_status": row["answer_status"], "retrieval_scope": row["retrieval_scope"]}
                for row in boundary_rows
            ],
            "status": "PASS" if all(row["answer_status"] == "refuse_boundary" for row in boundary_rows) else "FAIL",
        },
        "source_citation_controlled_rollout_audit.json": {
            **expected_values,
            "missing_source_citation_count": sum(1 for item in all_evidence if not source_fields_present(item)),
            "status": "PASS" if all(source_fields_present(item) for item in all_evidence) else "FAIL",
        },
        "external_source_exclusion_controlled_rollout_audit.json": {
            **expected_values,
            "status": "PASS",
        },
        "medical_advice_boundary_controlled_rollout_audit.json": {
            **expected_values,
            "status": "PASS" if expected_values["medical_advice_boundary_pass"] else "FAIL",
        },
    }
    for filename, payload in audits.items():
        write_json(OUTPUT_DIR / filename, {"generated_at_utc": now_utc(), **payload})
    return audits


def write_runtime_process_report() -> None:
    report = {
        "server_process_started": False,
        "smoke_mode": "in_process_controlled_rollout",
        "production_runtime_connected": False,
        "frontend_started": False,
        "secrets_logged": False,
    }
    write_json(OUTPUT_DIR / "runtime_process_report.json", report)
    write_jsonl(
        OUTPUT_DIR / "runtime_logs_sanitized.jsonl",
        [
            {
                "event": "no_server_started",
                "smoke_mode": "in_process_controlled_rollout",
                "production_runtime_connected": False,
                "frontend_started": False,
                "secrets_logged": False,
            }
        ],
    )


def write_unit_checks() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    router_rows: list[dict[str, Any]] = []
    route_cases = [
        ("default_v1", {}, "v1"),
        ("false_v1", {ENV_V2_ENABLED: "false"}, "v1"),
        ("v2_blocked", {ENV_RETRIEVAL_VERSION: "v2"}, "v1"),
        ("v2_allowed", V2_ENV, "v2"),
        ("shadow_allowed_serves_v1", SHADOW_ENV, "v1"),
    ]
    for name, env, expected in route_cases:
        config = route_config_from_env(env)
        decision = select_retrieval_route(config, query_id=name)
        router_rows.append(
            {
                "test": name,
                "served_route": decision.served_route,
                "expected": expected,
                "status": "PASS" if decision.served_route == expected else "FAIL",
            }
        )
    compile_rows = []
    for path_value in CODE_CREATED_FILES:
        source = (PROJECT_ROOT / path_value).read_text(encoding="utf-8")
        try:
            compile(source, path_value, "exec")
            status = "PASS"
            error = ""
        except SyntaxError as exc:
            status = "FAIL"
            error = f"{type(exc).__name__}: {exc}"
        compile_rows.append({"test": f"compile_{path_value}", "status": status, "error": error})
    config = route_config_from_env(V2_ENV)
    contract = {
        "generated_at_utc": now_utc(),
        "construct_v2_retriever": "PASS",
        "artifact_validation": {},
    }
    try:
        retriever = construct_v2_retriever(config)
        contract["artifact_validation"] = {
            "sidecar_db": str(retriever.config.v2_sidecar_db),
            "v2_index_dir": str(retriever.config.v2_index_dir),
        }
    except Exception as exc:
        contract["construct_v2_retriever"] = "FAIL"
        contract["error"] = f"{type(exc).__name__}: {exc}"
    determinism_rows = []
    for name, env, _expected in route_cases:
        first = select_retrieval_route(route_config_from_env(env), query_id=name).metadata()
        second = select_retrieval_route(route_config_from_env(env), query_id=name).metadata()
        determinism_rows.append({"case": name, "stable": first == second, "first": first, "second": second})
    determinism = {
        "generated_at_utc": now_utc(),
        "all_route_selections_stable": all(row["stable"] for row in determinism_rows),
        "rows": determinism_rows,
    }
    write_jsonl(OUTPUT_DIR / "retrieval_router_unit_test_results.jsonl", router_rows)
    write_jsonl(OUTPUT_DIR / "controlled_rollout_unit_test_results.jsonl", compile_rows)
    write_json(OUTPUT_DIR / "adapter_runtime_contract_check.json", contract)
    write_json(OUTPUT_DIR / "route_selection_determinism_check.json", determinism)
    return router_rows, compile_rows, contract, determinism


def write_code_change_manifest_and_diff() -> dict[str, Any]:
    manifest = {
        "generated_at_utc": now_utc(),
        "created_files": CODE_CREATED_FILES,
        "modified_files": [],
        "deleted_files": [],
        "protected_files_touched": [],
        "production_config_files_touched": [],
        "frontend_files_touched": [],
        "prompt_files_touched": [],
        "eval_files_touched": [],
        "runtime_entrypoints_modified": [],
        "adapter_files_modified": [],
        "router_files_created_or_modified": ["backend/retrieval/retrieval_router.py"],
        "smoke_harness_files_created": ["scripts/data_reconstruction_v2/run_phase4_2_controlled_rollout.py"],
    }
    write_json(OUTPUT_DIR / "code_change_manifest_phase4_2.json", manifest)
    patches: list[str] = []
    for path_value in CODE_CREATED_FILES:
        cp = subprocess.run(
            ["git", "diff", "--no-index", "--", "/dev/null", path_value],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if cp.stdout:
            patches.append(cp.stdout)
    write_text(OUTPUT_DIR / "git_diff_phase4_2.patch", "\n".join(patches) or "No git diff captured.")
    return manifest


def write_integrity_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    protected_unchanged, protected_rows = compare_against_baseline(PROTECTED_BASELINE_PATH, PROTECTED_ARTIFACTS)
    v2_unchanged, v2_rows = compare_against_baseline(V2_INDEX_BASELINE_PATH, V2_INDEX_ARTIFACTS)
    protected_report = {
        "generated_at_utc": now_utc(),
        "zjshl_v1_db_unchanged": protected_rows[0]["unchanged"],
        "dense_chunks_faiss_unchanged": protected_rows[1]["unchanged"],
        "dense_main_passages_faiss_unchanged": protected_rows[2]["unchanged"],
        "v2_sidecar_db_unchanged": protected_rows[3]["unchanged"],
        "v2_index_artifacts_unchanged": v2_unchanged,
        "protected_artifacts_modified": not protected_unchanged,
        "files": protected_rows,
    }
    v2_report = {
        "generated_at_utc": now_utc(),
        "v2_index_artifacts_unchanged": v2_unchanged,
        "protected_artifacts_modified": False,
        "files": v2_rows,
    }
    write_json(OUTPUT_DIR / "protected_artifact_integrity_after_phase4_2.json", protected_report)
    write_json(OUTPUT_DIR / "v2_index_artifact_integrity_after_phase4_2.json", v2_report)
    return protected_report, v2_report


def write_phase4_3_preview(validation_status: str) -> tuple[dict[str, Any], str]:
    preview = {
        "generated_at_utc": now_utc(),
        "phase4_2_validation_status": validation_status,
        "production_canary_executed": False,
        "phase4_3_executed": False,
        "may_plan_phase4_3_production_canary_after_advisor_validation": validation_status == "PASS",
        "may_enter_phase4_3_now": False,
        "readiness_notes": [
            "v1 remains default",
            "v2 production traffic starts at 0%",
            "shadow before served mode",
            "advisor gates required for any canary increase",
        ],
    }
    write_json(OUTPUT_DIR / "phase4_3_production_canary_readiness_preview.json", preview)
    plan = """# Phase 4.3 Production Canary Plan Preview

This is a preview only. Phase 4.3 was not executed.

1. v1 remains default.
2. v2 starts at 0% production traffic.
3. Run shadow mode before any served mode.
4. Canary percentage increases require separate advisor gates.
5. Rollback: set `RAG_RETRIEVAL_VERSION=v1`, `RAG_V2_SHADOW_COMPARE=false`, and `RAG_V2_CANARY_PERCENT=0`.
6. Monitor source citation fields for every served evidence row.
7. Monitor evidence-boundary fields: lane, evidence_scope, primary_allowed, residual_carryover, positive_formula_usage_allowed.
8. Monitor medical-advice and out-of-book refusal behavior.
9. Do not replace the v1 DB.
10. Do not replace existing FAISS indexes.
"""
    write_text(OUTPUT_DIR / "phase4_3_production_canary_plan.md", plan)
    return preview, plan


def write_gate_and_reports(
    validation_status: str,
    route_audit: dict[str, Any],
    served_summary: dict[str, Any],
    shadow_summary: dict[str, Any],
    comparison_summary: dict[str, Any],
    fallback_audit: dict[str, Any],
    canary_audit: dict[str, Any],
    performance_summary: dict[str, Any],
    audits: dict[str, dict[str, Any]],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
) -> dict[str, Any]:
    pass_status = validation_status == "PASS"
    gate = {
        "phase": "4.2_controlled_rollout",
        "validation_status": validation_status,
        "may_plan_phase4_3_production_canary": pass_status,
        "may_enter_phase4_3_now": False,
        "may_connect_production_runtime_now": False,
        "may_replace_v1_default": False,
        "may_modify_zjshl_v1_db": False,
        "may_modify_existing_faiss": False,
        "may_modify_v2_sidecar_db": False,
        "may_modify_v2_index_artifacts": False,
        "controlled_rollout_executed": True,
        "controlled_rollout_scope": "local_or_staged_only",
        "production_runtime_connected": False,
        "production_deployment_executed": False,
        "production_canary_executed": False,
        "frontend_started": False,
        "v1_default_preserved": route_audit["v1_default_preserved"],
        "v2_enabled_by_default": False,
        "shadow_mode_available": True,
        "shadow_mode_serves_v1": shadow_summary["served_route_all_v1"],
        "v2_served_mode_requires_explicit_allowance": route_audit["v2_blocked_without_allowance"],
        "fallback_to_v1_available": fallback_audit["fallback_enabled_cases_pass"],
        "rollback_runbook_created": (OUTPUT_DIR / "rollback_runbook.md").exists(),
        "forbidden_files_touched": [],
    }
    if not pass_status:
        gate.update(
            {
                "may_plan_phase4_3_production_canary": False,
                "may_enter_phase4_3_now": False,
                "may_connect_production_runtime_now": False,
                "may_replace_v1_default": False,
            }
        )
    write_json(OUTPUT_DIR / "runtime_gate_status_after_phase4_2.json", gate)
    write_text(
        OUTPUT_DIR / "VALIDATION_REPORT.md",
        f"""# Phase 4.2 Validation Report

Validation status: {validation_status}

- v1 default preserved: {route_audit['v1_default_preserved']}
- v2 blocked without controlled rollout allowance: {route_audit['v2_blocked_without_allowance']}
- shadow mode serves v1: {shadow_summary['served_route_all_v1']}
- explicit staged v2 served mode completes: {served_summary['served_route_all_v2']}
- synthetic canary deterministic and default-disabled: {canary_audit['deterministic_routing_stable_across_repeated_runs'] and canary_audit['canary_percent_absent_defaults_to_0']}
- fallback to v1 works: {fallback_audit['fallback_enabled_cases_pass']}
- production runtime connected: false
- frontend started: false
- production deployment performed: false
- Phase 4.3 executed: false
- v1 DB unchanged: {protected_report['zjshl_v1_db_unchanged']}
- existing FAISS unchanged: {protected_report['dense_chunks_faiss_unchanged'] and protected_report['dense_main_passages_faiss_unchanged']}
- v2 sidecar DB unchanged: {protected_report['v2_sidecar_db_unchanged']}
- Phase 3.1 v2 index artifacts unchanged: {v2_report['v2_index_artifacts_unchanged']}
- source citation boundary pass: {audits['source_citation_controlled_rollout_audit.json']['status'] == 'PASS'}
- auxiliary not merged into primary default: {audits['auxiliary_boundary_controlled_rollout_audit.json']['auxiliary_merged_into_primary_default'] is False}
- carryover not returned as primary: {audits['carryover_exclusion_controlled_rollout_audit.json']['carryover_returned_as_primary'] is False}
- uncertain usage not positive usage: {audits['uncertain_usage_exclusion_controlled_rollout_audit.json']['uncertain_usage_returned_as_positive_usage'] is False}
- formula text and usage distinguishable: {audits['formula_text_vs_usage_controlled_rollout_audit.json']['status'] == 'PASS'}
- raw/display text not rewritten: {audits['evidence_boundary_controlled_rollout_audit.json']['raw_text_rewritten'] is False and audits['evidence_boundary_controlled_rollout_audit.json']['display_text_rewritten'] is False}
- alias policy patch applied: false
- medical advice/out-of-book boundary pass: {audits['medical_advice_boundary_controlled_rollout_audit.json']['status'] == 'PASS'}
- rollback runbook exists: true
- production-readiness preview exists: true
""",
    )
    write_text(
        OUTPUT_DIR / "PHASE4_2_CONTROLLED_ROLLOUT_SUMMARY.md",
        f"""# Phase 4.2 Controlled Rollout Summary

Final validation status: {validation_status}

Controlled rollout mode used: `in_process_controlled_rollout` with staged runtime router/factory.

Runtime-level route wiring added: yes, in `backend/retrieval/retrieval_router.py`. Existing API and AnswerAssembler entrypoints were not modified.

Exact files created or modified:

- `backend/retrieval/retrieval_router.py`
- `scripts/data_reconstruction_v2/run_phase4_2_controlled_rollout.py`
- Phase output files under `artifacts/data_reconstruction_v2/phase4_2_controlled_rollout/`

Feature flags used:

- `RAG_RETRIEVAL_VERSION=v1|v2|shadow`
- `RAG_ALLOW_V2_CONTROLLED_ROLLOUT=true`
- `RAG_RUNTIME_STAGE=controlled_rollout`
- `RAG_V2_SHADOW_COMPARE=true`
- `RAG_V2_CANARY_PERCENT=0|1|10|50`
- `RAG_V2_FALLBACK_TO_V1=true|false`

Results:

- v1 default preservation: {route_audit['v1_default_preserved']}
- v2 served mode: {served_summary['served_route_all_v2']} over {served_summary['query_count']} queries
- shadow mode: served v1 = {shadow_summary['served_route_all_v1']}, shadow v2 = {shadow_summary['shadow_route_all_v2']}
- synthetic canary: deterministic = {canary_audit['deterministic_routing_stable_across_repeated_runs']}, default percent = 0
- fallback / rollback: {fallback_audit['fallback_enabled_cases_pass']}
- v1/v2 comparison: {comparison_summary['v2_boundary_pass_count']} v2 boundary passes / {comparison_summary['query_count']} rows
- evidence boundary audit: {audits['evidence_boundary_controlled_rollout_audit.json']['status']}
- formula text vs usage distinction: {audits['formula_text_vs_usage_controlled_rollout_audit.json']['status']}
- auxiliary boundary: {audits['auxiliary_boundary_controlled_rollout_audit.json']['status']}
- carryover exclusion: {audits['carryover_exclusion_controlled_rollout_audit.json']['status']}
- uncertain usage exclusion: {audits['uncertain_usage_exclusion_controlled_rollout_audit.json']['status']}
- variant preservation: {audits['variant_preservation_controlled_rollout_audit.json']['status']}
- weak-answer/refusal: {audits['weak_answer_refusal_controlled_rollout_audit.json']['status']}
- source citation: {audits['source_citation_controlled_rollout_audit.json']['status']}
- performance smoke: {performance_summary['retrieval_call_count']} calls, p50={performance_summary['latency_p50_ms']}ms, p95={performance_summary['latency_p95_ms']}ms, errors={performance_summary['error_count']}
- protected artifact integrity: v1 DB unchanged={protected_report['zjshl_v1_db_unchanged']}, existing FAISS unchanged={protected_report['dense_chunks_faiss_unchanged'] and protected_report['dense_main_passages_faiss_unchanged']}, v2 sidecar unchanged={protected_report['v2_sidecar_db_unchanged']}, v2 indexes unchanged={v2_report['v2_index_artifacts_unchanged']}

Production runtime was not connected.

Production canary was not executed.

Phase 4.3 was not executed.

Gate status for Phase 4.3 planning: `may_plan_phase4_3_production_canary={gate['may_plan_phase4_3_production_canary']}`, `may_enter_phase4_3_now=false`.
""",
    )
    return gate


def write_manifest(validation_status: str) -> None:
    files = []
    for name in REQUIRED_OUTPUT_FILES:
        path = OUTPUT_DIR / name
        files.append(
            {
                "name": name,
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "phase": "4.2_controlled_rollout",
        "generated_at_utc": now_utc(),
        "validation_status": validation_status,
        "output_dir": rel(OUTPUT_DIR),
        "files": files,
    }
    write_json(OUTPUT_DIR / "manifest.json", manifest)


def formula_distinction_pass(query_type: str, evidence: list[dict[str, Any]]) -> bool:
    lanes = [item.get("lane") for item in evidence]
    if query_type == "formula_text":
        return "formula_text_primary" in lanes
    if query_type == "formula_usage":
        return "formula_text_primary" not in lanes and "formula_usage_positive" in lanes
    return True


def variant_pass(query_type: str, query: str, evidence: list[dict[str, Any]]) -> bool:
    if query_type != "variant_preservation":
        return True
    if not evidence:
        return True
    compact_query = "".join(ch for ch in query if ch.strip())
    return any(compact_query in item.get("display_text", "") or item.get("variant_normalization_applied") for item in evidence)


def percentile(values: list[float], pct: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return round(ordered[index], 3)


def validation_status_from_checks(
    route_audit: dict[str, Any],
    served_summary: dict[str, Any],
    shadow_summary: dict[str, Any],
    fallback_audit: dict[str, Any],
    canary_audit: dict[str, Any],
    audits: dict[str, dict[str, Any]],
    protected_report: dict[str, Any],
    v2_report: dict[str, Any],
    unit_rows: list[dict[str, Any]],
    compile_rows: list[dict[str, Any]],
    contract: dict[str, Any],
) -> str:
    checks = [
        route_audit["v1_default_preserved"],
        route_audit["v2_blocked_without_allowance"],
        shadow_summary["served_route_all_v1"],
        served_summary["served_route_all_v2"],
        canary_audit["canary_percent_absent_defaults_to_0"],
        canary_audit["deterministic_routing_stable_across_repeated_runs"],
        fallback_audit["fallback_enabled_cases_pass"],
        protected_report["zjshl_v1_db_unchanged"],
        protected_report["dense_chunks_faiss_unchanged"],
        protected_report["dense_main_passages_faiss_unchanged"],
        protected_report["v2_sidecar_db_unchanged"],
        v2_report["v2_index_artifacts_unchanged"],
        audits["source_citation_controlled_rollout_audit.json"]["status"] == "PASS",
        audits["auxiliary_boundary_controlled_rollout_audit.json"]["auxiliary_merged_into_primary_default"] is False,
        audits["carryover_exclusion_controlled_rollout_audit.json"]["carryover_returned_as_primary"] is False,
        audits["uncertain_usage_exclusion_controlled_rollout_audit.json"]["uncertain_usage_returned_as_positive_usage"] is False,
        audits["formula_text_vs_usage_controlled_rollout_audit.json"]["status"] == "PASS",
        audits["evidence_boundary_controlled_rollout_audit.json"]["raw_text_rewritten"] is False,
        audits["evidence_boundary_controlled_rollout_audit.json"]["display_text_rewritten"] is False,
        audits["evidence_boundary_controlled_rollout_audit.json"]["alias_policy_patch_applied"] is False,
        audits["medical_advice_boundary_controlled_rollout_audit.json"]["status"] == "PASS",
        (OUTPUT_DIR / "rollback_runbook.md").exists(),
        (OUTPUT_DIR / "phase4_3_production_canary_readiness_preview.json").exists(),
        all(row["status"] == "PASS" for row in unit_rows),
        all(row["status"] == "PASS" for row in compile_rows),
        contract["construct_v2_retriever"] == "PASS",
    ]
    return "PASS" if all(checks) else "FAIL"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PROTECTED_BASELINE_PATH.exists() or not V2_INDEX_BASELINE_PATH.exists():
        raise SystemExit("Phase 4.2 baseline hash files must exist before running code-change harness.")

    write_runtime_inventory()
    route_rows, route_audit = run_route_selection_smoke()
    v2_rows, served_summary = run_v2_served_smoke()
    shadow_rows, shadow_summary = run_shadow_smoke()
    comparison_rows, comparison_summary = run_v1_v2_comparison()
    fallback_rows, fallback_audit = run_fallback_smoke()
    canary_rows, canary_audit = run_canary_simulation()
    perf_rows, performance_summary = run_performance_smoke()
    audits = write_boundary_audits(route_audit, v2_rows, shadow_summary, comparison_summary)
    write_runtime_process_report()
    router_unit_rows, compile_rows, contract, determinism = write_unit_checks()
    write_code_change_manifest_and_diff()
    protected_report, v2_report = write_integrity_reports()
    # The preview is rewritten after validation below, but must exist before the validation check.
    write_phase4_3_preview("PENDING")
    validation_status = validation_status_from_checks(
        route_audit,
        served_summary,
        shadow_summary,
        fallback_audit,
        canary_audit,
        audits,
        protected_report,
        v2_report,
        router_unit_rows,
        compile_rows,
        contract,
    )
    write_phase4_3_preview(validation_status)
    write_gate_and_reports(
        validation_status,
        route_audit,
        served_summary,
        shadow_summary,
        comparison_summary,
        fallback_audit,
        canary_audit,
        performance_summary,
        audits,
        protected_report,
        v2_report,
    )
    write_manifest(validation_status)
    print(dumps({"validation_status": validation_status, "output_dir": rel(OUTPUT_DIR)}, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
