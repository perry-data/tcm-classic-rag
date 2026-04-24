from __future__ import annotations

import os
import unittest

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


FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
ALLOWED_DEFINITION_PRIMARY_TYPES = {"definition_terms", "main_passages"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}

DEFINITION_BOUNDARY_QUERIES = [
    "什么是发汗药",
    "发汗药是什么意思",
    "阳结是什么",
    "阳结是什么意思",
    "坏病是什么",
    "坏病是什么意思",
    "下药是什么意思",
    "阳结是什么",
    "阴结是什么意思",
    "承气汤是下药吗",
    "桂枝汤是什么药",
]

DEFINITION_SUPPORT_QUERIES = {
    "什么是发汗药",
    "发汗药是什么意思",
    "坏病是什么",
    "坏病是什么意思",
}

FORMULA_REGRESSION_QUERIES = [
    "葛根黄芩黄连汤方的条文是什么？",
    "麻黄汤方的条文是什么？",
    "大青龙汤方的条文是什么？",
    "猪苓汤方的条文是什么？",
    "甘草乾姜汤方和芍药甘草汤方的区别是什么？",
    "栀子豉汤方和栀子乾姜汤方有什么不同？",
    "白虎汤方和白虎加人参汤方的区别是什么？",
    "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
]


class DefinitionPrimaryBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._old_env = {
            "PERF_DISABLE_LLM": os.environ.get("PERF_DISABLE_LLM"),
            "PERF_RETRIEVAL_MODE": os.environ.get("PERF_RETRIEVAL_MODE"),
            "PERF_DISABLE_RERANK": os.environ.get("PERF_DISABLE_RERANK"),
        }
        os.environ["PERF_DISABLE_LLM"] = "1"
        os.environ["PERF_RETRIEVAL_MODE"] = "sparse"
        os.environ["PERF_DISABLE_RERANK"] = "1"
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

    @classmethod
    def tearDownClass(cls) -> None:
        cls.assembler.close()
        for key, value in cls._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def assert_primary_is_clean_definition_source(self, payload: dict, query: str) -> None:
        for item in payload["primary_evidence"]:
            self.assertNotIn(item["record_type"], FORBIDDEN_PRIMARY_TYPES, query)
            self.assertIn(item["record_type"], ALLOWED_DEFINITION_PRIMARY_TYPES, query)
            if item["record_type"] == "main_passages":
                self.assertTrue(str(item["record_id"]).startswith("safe:main_passages:"), query)
            if item["record_type"] == "definition_terms":
                self.assertTrue(str(item["record_id"]).startswith("safe:definition_terms:"), query)

    def assert_primary_is_safe_main(self, payload: dict, query: str) -> None:
        for item in payload["primary_evidence"]:
            self.assertNotIn(item["record_type"], FORBIDDEN_PRIMARY_TYPES, query)
            self.assertEqual(item["record_type"], "main_passages", query)
            self.assertTrue(str(item["record_id"]).startswith("safe:main_passages:"), query)

    def test_definition_priority_keeps_full_passages_out_of_primary(self) -> None:
        for query in DEFINITION_BOUNDARY_QUERIES:
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                self.assert_primary_is_clean_definition_source(payload, query)
                debug = self.assembler.get_last_definition_priority_debug()
                if debug and not debug.get("fallback_to_standard"):
                    self.assertFalse(
                        any(str(record_id).startswith("full:passages:") for record_id in debug["selected_primary_ids"]),
                        query,
                    )
                    for candidate in debug["candidate_debug"]:
                        if candidate["record_type"] in FORBIDDEN_PRIMARY_TYPES:
                            self.assertFalse(candidate["primary_eligible"], query)

                support_items = payload["secondary_evidence"] + payload["review_materials"]
                if query in DEFINITION_SUPPORT_QUERIES:
                    self.assertEqual(payload["answer_mode"], "strong", query)
                    self.assertTrue(
                        any(
                            str(item["record_id"]).startswith("safe:definition_terms:")
                            for item in payload["primary_evidence"]
                        ),
                        query,
                    )

    def test_formula_object_regression_keeps_safe_main_primary(self) -> None:
        formula_backref_count = 0
        for query in FORMULA_REGRESSION_QUERIES:
            with self.subTest(query=query):
                retrieval = self.assembler.engine.retrieve(query)
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["answer_mode"], "strong", query)
                self.assertTrue(payload["primary_evidence"], query)
                self.assert_primary_is_safe_main(payload, query)

                formula_norm = retrieval["query_request"].get("formula_normalization") or {}
                self.assertTrue(formula_norm.get("enabled"), query)
                self.assertIn(formula_norm.get("type"), {"exact", "comparison"}, query)
                top5_bad_topics = [
                    row.get("topic_consistency")
                    for row in retrieval["raw_candidates"][:5]
                    if row.get("topic_consistency") in BAD_FORMULA_TOPICS
                ]
                self.assertEqual(top5_bad_topics, [], query)
                formula_backref_count += sum(
                    1
                    for row in retrieval["primary_evidence"]
                    for path in row.get("retrieval_paths") or []
                    if path.get("type") == "formula_object_backref"
                )

        self.assertGreater(formula_backref_count, 0)


if __name__ == "__main__":
    unittest.main()
