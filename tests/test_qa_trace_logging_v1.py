from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.answers.assembler import (
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
from backend.diagnostics.qa_trace import (
    ENV_QA_TRACE_DIR,
    ENV_QA_TRACE_ENABLED,
    FORBIDDEN_PRIMARY_PREFIXES,
    TRACE_FIELDS,
    write_qa_trace_safely,
)


SMOKE_EXPECTATIONS = {
    "桂枝汤方的条文是什么？": "strong",
    "干呕是什么意思？": "weak_with_review_notice",
    "白虎是什么意思？": "refuse",
}
REQUIRED_FIELDS = {
    "trace_id",
    "timestamp_utc",
    "query",
    "normalized_query",
    "answer_mode",
    "retrieval_method",
    "top_k_chunks",
    "primary_evidence_ids",
    "secondary_evidence_ids",
    "review_material_ids",
    "citations",
    "final_answer",
    "latency_ms",
    "model_name",
    "llm_used",
    "llm_answer_source",
}


class QATraceLoggingV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._old_env = {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
            "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
            ENV_QA_TRACE_DIR: os.environ.get(ENV_QA_TRACE_DIR),
            ENV_QA_TRACE_ENABLED: os.environ.get(ENV_QA_TRACE_ENABLED),
        }
        cls._tempdir = tempfile.TemporaryDirectory()
        cls.trace_dir = Path(cls._tempdir.name) / "qa_traces"
        os.environ["PERF_DISABLE_LLM"] = "1"
        os.environ["PERF_RETRIEVAL_MODE"] = "sparse"
        os.environ["PERF_DISABLE_RERANK"] = "1"
        os.environ[ENV_QA_TRACE_DIR] = str(cls.trace_dir)
        os.environ[ENV_QA_TRACE_ENABLED] = "1"
        cls.assembler = AnswerAssembler(
            db_path=resolve_project_path(DEFAULT_DB_PATH),
            policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
            embed_model=DEFAULT_EMBED_MODEL,
            rerank_model=DEFAULT_RERANK_MODEL,
            cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
            dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
            dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
            dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
            dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
        )
        cls.payloads = {query: cls.assembler.assemble(query) for query in SMOKE_EXPECTATIONS}
        trace_paths = sorted(cls.trace_dir.glob("qa_trace_*.jsonl"))
        assert trace_paths, "qa trace log was not created"
        cls.trace_path = trace_paths[-1]
        cls.trace_lines = cls.trace_path.read_text(encoding="utf-8").splitlines()
        cls.trace_records = [json.loads(line) for line in cls.trace_lines]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.assembler.close()
        cls._tempdir.cleanup()
        for key, value in cls._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_real_smoke_questions_generate_jsonl_traces(self) -> None:
        self.assertGreaterEqual(len(self.trace_records), 3)
        by_query = {record["query"]: record for record in self.trace_records}
        for query, expected_mode in SMOKE_EXPECTATIONS.items():
            with self.subTest(query=query):
                self.assertIn(query, by_query)
                self.assertEqual(self.payloads[query]["answer_mode"], expected_mode)
                self.assertEqual(by_query[query]["answer_mode"], expected_mode)

    def test_trace_schema_is_stable_and_parseable(self) -> None:
        for line in self.trace_lines:
            record = json.loads(line)
            self.assertEqual(set(record), set(TRACE_FIELDS))
            self.assertTrue(REQUIRED_FIELDS.issubset(record))
            self.assertIsInstance(record["top_k_chunks"], list)
            self.assertIsInstance(record["citations"], list)
            self.assertTrue(record["final_answer"])
            self.assertIsInstance(record["latency_ms"], (int, float))
            for top_k_item in record["top_k_chunks"]:
                self.assertLessEqual(len(top_k_item.get("main_text_summary") or ""), 120)
                self.assertLessEqual(len(top_k_item.get("annotation_summary") or ""), 120)

    def test_non_refuse_traces_include_retrieval_candidates(self) -> None:
        for record in self.trace_records:
            if record["answer_mode"] == "refuse":
                continue
            with self.subTest(query=record["query"]):
                self.assertTrue(record["top_k_chunks"])
                self.assertIn(
                    record["retrieval_method"],
                    {"sparse", "hybrid", "hybrid+rerank", "formula_object", "definition_object", "guarded_baseline"},
                )

    def test_trace_primary_ids_do_not_include_raw_full_passages(self) -> None:
        for record in self.trace_records:
            with self.subTest(query=record["query"]):
                for record_id in record["primary_evidence_ids"]:
                    self.assertFalse(str(record_id).startswith(FORBIDDEN_PRIMARY_PREFIXES), record)

    def test_trace_write_failure_does_not_interrupt_answer(self) -> None:
        blocking_path = Path(self._tempdir.name) / "not_a_directory"
        blocking_path.write_text("blocks directory creation", encoding="utf-8")
        old_trace_dir = os.environ[ENV_QA_TRACE_DIR]
        os.environ[ENV_QA_TRACE_DIR] = str(blocking_path)
        try:
            payload = self.assembler.assemble("白虎是什么意思？")
            self.assertEqual(payload["answer_mode"], "refuse")
            result = write_qa_trace_safely(
                query="write failure probe",
                payload=payload,
                llm_debug=self.assembler.get_last_llm_debug(),
                log_dir=blocking_path,
            )
            self.assertIsNone(result)
        finally:
            os.environ[ENV_QA_TRACE_DIR] = old_trace_dir

    def test_no_ahv3_or_trace_backdoor_normalization_added(self) -> None:
        conn = sqlite3.connect(resolve_project_path(DEFAULT_DB_PATH))
        try:
            ahv3_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM definition_term_registry
                WHERE concept_id LIKE 'AHV3-%'
                   OR lower(promotion_source_layer) LIKE '%ahv3%'
                """
            ).fetchone()[0]
            self.assertEqual(ahv3_count, 0)

            trace_contains_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM learner_query_normalization_lexicon
                WHERE is_active = 1
                  AND match_mode = 'contains'
                  AND lower(source) LIKE '%qa_trace%'
                """
            ).fetchone()[0]
            self.assertEqual(trace_contains_count, 0)

            active_single_char_alias_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM term_alias_registry
                WHERE is_active = 1
                  AND length(normalized_alias) = 1
                """
            ).fetchone()[0]
            self.assertEqual(active_single_char_alias_count, 0)

            active_single_char_learner_surface_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM learner_query_normalization_lexicon
                WHERE is_active = 1
                  AND length(normalized_surface_form) = 1
                """
            ).fetchone()[0]
            self.assertEqual(active_single_char_learner_surface_count, 0)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
