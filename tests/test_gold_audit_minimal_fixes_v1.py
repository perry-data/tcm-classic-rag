from __future__ import annotations

import json
import os
import sqlite3
import unittest

os.environ.setdefault("PERF_DISABLE_LLM", "1")
os.environ.setdefault("PERF_DISABLE_RERANK", "1")
os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")

from backend.answers.assembler import (  # noqa: E402
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


class GoldAuditMinimalFixesV1Test(unittest.TestCase):
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

    def test_fahan_is_explicit_explanation_primary(self) -> None:
        row = self.conn.execute(
            """
            SELECT
                primary_evidence_text,
                primary_evidence_type,
                definition_evidence_passage_ids_json,
                explanation_evidence_passage_ids_json,
                membership_evidence_passage_ids_json,
                promotion_reason,
                notes
            FROM definition_term_registry
            WHERE canonical_term = '发汗药'
            """
        ).fetchone()

        self.assertEqual(row["primary_evidence_text"], "发汗药，须温暖服者，易为发散也")
        self.assertEqual(row["primary_evidence_type"], "exact_term_explanation")
        self.assertEqual(json.loads(row["definition_evidence_passage_ids_json"]), [])
        self.assertEqual(json.loads(row["explanation_evidence_passage_ids_json"]), ["ZJSHL-CH-006-P-0127"])
        self.assertEqual(json.loads(row["membership_evidence_passage_ids_json"]), ["ZJSHL-CH-006-P-0120"])
        self.assertEqual(row["promotion_reason"], "gold_fix_v1_explanation_primary_not_strict_definition")
        self.assertIn("explanation-primary, not definition-primary", row["notes"])

    def test_dandan_review_only_aliases_removed(self) -> None:
        row = self.conn.execute(
            """
            SELECT
                source_confidence,
                promotion_state,
                is_safe_primary_candidate,
                query_aliases_json,
                learner_surface_forms_json,
                retrieval_text,
                notes
            FROM definition_term_registry
            WHERE canonical_term = '胆瘅'
            """
        ).fetchone()

        self.assertEqual(row["source_confidence"], "review_only")
        self.assertEqual(row["promotion_state"], "review_only")
        self.assertEqual(row["is_safe_primary_candidate"], 0)
        self.assertEqual(json.loads(row["query_aliases_json"]), [])
        self.assertEqual(json.loads(row["learner_surface_forms_json"]), [])
        self.assertNotIn("口苦病", row["retrieval_text"])
        self.assertNotIn("胆瘅病", row["retrieval_text"])
        self.assertIn("removed review-only learner aliases 口苦病/胆瘅病", row["notes"])

        aliases = [
            dict(alias)
            for alias in self.conn.execute(
                """
                SELECT alias, alias_type
                FROM term_alias_registry
                WHERE canonical_term = '胆瘅'
                ORDER BY alias
                """
            )
        ]
        self.assertEqual(aliases, [{"alias": "胆瘅", "alias_type": "canonical"}])

    def test_dandan_learner_alias_queries_do_not_force_normalization(self) -> None:
        for query in ("口苦病是什么意思", "胆瘅病是什么意思"):
            with self.subTest(query=query):
                retrieval = self.assembler.engine.retrieve(query)
                payload = self.assembler.assemble(query)
                term_normalization = retrieval["query_request"].get("term_normalization") or {}

                self.assertNotEqual(retrieval["query_request"].get("query_focus_source"), "term_normalization")
                self.assertFalse(term_normalization.get("concept_ids"))
                self.assertFalse(
                    any(
                        str(item.get("record_id") or "").endswith(":DPO-3239213192a3")
                        for item in payload.get("primary_evidence") or []
                    )
                )


if __name__ == "__main__":
    unittest.main()
