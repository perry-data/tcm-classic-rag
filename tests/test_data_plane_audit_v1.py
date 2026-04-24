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


class DataPlaneAuditV1Test(unittest.TestCase):
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

    def test_dan_dan_downgraded_to_review_only(self) -> None:
        row = self.conn.execute(
            """
            SELECT source_confidence, promotion_state, is_safe_primary_candidate
            FROM definition_term_registry
            WHERE canonical_term = '胆瘅'
            """
        ).fetchone()
        self.assertEqual(row["source_confidence"], "review_only")
        self.assertEqual(row["promotion_state"], "review_only")
        self.assertEqual(row["is_safe_primary_candidate"], 0)

    def test_dan_dan_not_in_learner_safe_lexicon(self) -> None:
        count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE target_term = '胆瘅' AND entry_type = 'term_surface'
            """
        ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_yin_yang_yi_no_longer_forces_term_normalization(self) -> None:
        retrieval = self.assembler.engine.retrieve("阴阳易是什么意思")
        self.assertNotEqual(retrieval["query_request"].get("query_focus_source"), "term_normalization")
        self.assertFalse((retrieval["query_request"].get("term_normalization") or {}).get("concept_ids"))

    def test_si_ni_sentence_role_is_membership_not_formula_composition(self) -> None:
        row = self.conn.execute(
            """
            SELECT primary_role, role_tags_json
            FROM sentence_role_registry
            WHERE passage_id = 'ZJSHL-CH-015-P-0203'
              AND sentence_text = '四逆者，四肢不温也。'
            """
        ).fetchone()
        self.assertEqual(row["primary_role"], "membership_sentence")
        self.assertNotIn("formula_composition_sentence", row["role_tags_json"])

    def test_feng_wen_upgraded_to_high(self) -> None:
        row = self.conn.execute(
            """
            SELECT source_confidence
            FROM definition_term_registry
            WHERE canonical_term = '风温'
            """
        ).fetchone()
        self.assertEqual(row["source_confidence"], "high")

    def test_formula_medium_upgrades_applied(self) -> None:
        upgraded = {
            row["canonical_name"]
            for row in self.conn.execute(
                """
                SELECT canonical_name
                FROM formula_canonical_registry
                WHERE source_confidence = 'high'
                  AND canonical_name IN (
                    '四逆加人参汤',
                    '四逆加猪胆汁汤',
                    '柴胡加芒硝汤',
                    '桂枝加浓朴杏子汤',
                    '桂枝加芍药汤',
                    '桂枝去桂加茯苓白术汤',
                    '桂枝去芍药加附子汤',
                    '桂枝去芍药汤'
                  )
                """
            )
        }
        self.assertEqual(
            upgraded,
            {
                "四逆加人参汤",
                "四逆加猪胆汁汤",
                "柴胡加芒硝汤",
                "桂枝加浓朴杏子汤",
                "桂枝加芍药汤",
                "桂枝去桂加茯苓白术汤",
                "桂枝去芍药加附子汤",
                "桂枝去芍药汤",
            },
        )


if __name__ == "__main__":
    unittest.main()
