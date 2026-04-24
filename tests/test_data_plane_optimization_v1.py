from __future__ import annotations

import sqlite3
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


class DataPlaneOptimizationV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_path = resolve_project_path(DEFAULT_DB_PATH)
        cls.conn = sqlite3.connect(cls.db_path)
        cls.conn.row_factory = sqlite3.Row
        cls.assembler = AnswerAssembler(
            db_path=cls.db_path,
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
        cls.conn.close()

    def test_definition_registry_expanded(self) -> None:
        total_count = self.conn.execute("SELECT COUNT(*) FROM definition_term_registry").fetchone()[0]
        safe_count = self.conn.execute("SELECT COUNT(*) FROM retrieval_ready_definition_view").fetchone()[0]
        alias_count = self.conn.execute("SELECT COUNT(*) FROM term_alias_registry").fetchone()[0]
        learner_count = self.conn.execute("SELECT COUNT(*) FROM learner_query_normalization_lexicon").fetchone()[0]
        sentence_count = self.conn.execute("SELECT COUNT(*) FROM sentence_role_registry").fetchone()[0]

        self.assertGreaterEqual(total_count, 25)
        self.assertGreaterEqual(safe_count, 25)
        self.assertGreaterEqual(alias_count, 40)
        self.assertGreaterEqual(learner_count, 20)
        self.assertGreater(sentence_count, 3000)

    def test_short_term_definition_query_stays_off_full_primary(self) -> None:
        payload = self.assembler.assemble("下药是什么意思")
        self.assertEqual(payload["answer_mode"], "strong")
        self.assertTrue(payload["primary_evidence"])
        self.assertTrue(
            all(item["record_type"] not in FORBIDDEN_PRIMARY_TYPES for item in payload["primary_evidence"])
        )
        self.assertTrue(
            any(item["record_type"] == "definition_terms" for item in payload["primary_evidence"])
        )

    def test_learner_surface_query_uses_term_normalization(self) -> None:
        retrieval = self.assembler.engine.retrieve("睡着出汗是什么意思")
        payload = self.assembler.assemble("睡着出汗是什么意思")

        term_normalization = retrieval["query_request"].get("term_normalization") or {}
        self.assertEqual(retrieval["query_request"].get("query_focus_source"), "term_normalization")
        self.assertEqual(term_normalization.get("canonical_target_term"), "盗汗")
        self.assertEqual(payload["answer_mode"], "strong")
        self.assertTrue(
            all(item["record_type"] not in FORBIDDEN_PRIMARY_TYPES for item in payload["primary_evidence"])
        )

    def test_formula_primary_stays_safe_main_only(self) -> None:
        payload = self.assembler.assemble("桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？")
        self.assertEqual(payload["answer_mode"], "strong")
        self.assertTrue(payload["primary_evidence"])
        self.assertTrue(
            all(
                item["record_type"] == "main_passages"
                and str(item["record_id"]).startswith("safe:main_passages:")
                for item in payload["primary_evidence"]
            )
        )

    def test_review_only_terms_do_not_get_promoted_to_primary(self) -> None:
        payload = self.assembler.assemble("神丹是什么意思")
        self.assertEqual(payload["answer_mode"], "weak_with_review_notice")
        self.assertFalse(
            any(item["record_type"] == "definition_terms" for item in payload["primary_evidence"])
        )


if __name__ == "__main__":
    unittest.main()
