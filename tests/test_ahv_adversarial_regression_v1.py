from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


QUERY_SET_PATH = Path("artifacts/data_plane_adversarial/ahv_adversarial_query_set_v1.json")
BEFORE_PATH = Path("artifacts/data_plane_adversarial/ahv_adversarial_regression_before_fix_v1.json")
AFTER_PATH = Path("artifacts/data_plane_adversarial/ahv_adversarial_regression_after_fix_v1.json")
FIX_LEDGER_PATH = Path("artifacts/data_plane_adversarial/ahv_adversarial_fix_ledger_v1.json")
DB_PATH = Path("artifacts/zjshl_v1.db")
AHV_LAYER = "ambiguous_high_value_batch_safe_primary"


class AHVAdversarialRegressionV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.query_set = json.loads(QUERY_SET_PATH.read_text(encoding="utf-8"))
        cls.before = json.loads(BEFORE_PATH.read_text(encoding="utf-8"))
        cls.after = json.loads(AFTER_PATH.read_text(encoding="utf-8"))
        cls.fix_ledger = json.loads(FIX_LEDGER_PATH.read_text(encoding="utf-8"))
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_query_set_covers_required_adversarial_families(self) -> None:
        counts = self.query_set["query_type_counts"]
        self.assertGreaterEqual(self.query_set["query_count"], 80)
        self.assertEqual(counts["ahv_canonical_guard"], 20)
        self.assertGreaterEqual(counts["similar_concept_false_trigger"], 20)
        self.assertEqual(counts["disabled_alias_recheck"], 5)
        self.assertEqual(counts["partial_word_literal_similarity"], 10)
        self.assertEqual(counts["non_definition_intent"], 8)
        self.assertEqual(counts["negative_unrelated"], 10)
        self.assertEqual(counts["formula_guard"], 5)
        self.assertEqual(counts["gold_safe_definition_guard"], 5)
        self.assertEqual(counts["review_only_boundary_guard"], 4)

    def test_before_fix_exposes_real_adversarial_failures(self) -> None:
        metrics = self.before["metrics"]
        self.assertEqual(metrics["total_query_count"], 87)
        self.assertEqual(metrics["fail_count"], 20)
        self.assertEqual(metrics["wrong_ahv_primary_hit_count"], 2)
        self.assertEqual(metrics["wrong_term_normalization_count"], 18)
        self.assertEqual(metrics["disabled_alias_still_hit_count"], 2)

    def test_after_fix_holds_all_required_boundaries(self) -> None:
        metrics = self.after["metrics"]
        self.assertEqual(metrics["total_query_count"], 87)
        self.assertEqual(metrics["pass_count"], 87)
        self.assertEqual(metrics["fail_count"], 0)
        self.assertEqual(metrics["wrong_ahv_primary_hit_count"], 0)
        self.assertEqual(metrics["wrong_term_normalization_count"], 0)
        self.assertEqual(metrics["disabled_alias_still_hit_count"], 0)
        self.assertEqual(metrics["partial_word_false_positive_count"], 0)
        self.assertEqual(metrics["non_definition_intent_hijack_count"], 0)
        self.assertEqual(metrics["negative_sample_false_positive_count"], 0)
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_count"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(metrics["ahv_canonical_guard_pass_count"], 20)
        self.assertFalse(self.after["failures"])

    def test_fix_is_limited_to_ahv_normalization_without_object_expansion(self) -> None:
        metrics = self.fix_ledger["metrics"]
        self.assertEqual(metrics["changed_learner_surface_count"], 28)
        self.assertEqual(metrics["downgraded_object_count"], 0)
        self.assertEqual(metrics["deactivated_alias_count"], 0)
        self.assertEqual(metrics["new_ahv_object_count"], 0)
        ahv_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE promotion_source_layer = ?
              AND is_active = 1
            """,
            (AHV_LAYER,),
        ).fetchone()[0]
        self.assertEqual(ahv_count, 20)

    def test_active_ahv_learner_surfaces_are_exact_match(self) -> None:
        rows = self.conn.execute(
            """
            SELECT surface_form, target_term, match_mode
            FROM learner_query_normalization_lexicon
            WHERE entry_type = 'term_surface'
              AND is_active = 1
              AND target_id IN (
                  SELECT concept_id
                  FROM definition_term_registry
                  WHERE promotion_source_layer = ?
              )
            """,
            (AHV_LAYER,),
        ).fetchall()
        self.assertGreaterEqual(len(rows), 20)
        self.assertTrue(all(row["match_mode"] == "exact" for row in rows))


if __name__ == "__main__":
    unittest.main()
