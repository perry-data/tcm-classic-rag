from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


ARTIFACT_DIR = Path("artifacts/data_plane_cross_batch")
DB_PATH = Path("artifacts/zjshl_v1.db")
AHV_V1_LAYER = "ambiguous_high_value_batch_safe_primary"
AHV2_LAYER = "ambiguous_high_value_evidence_upgrade_v2_safe_primary"


class CrossBatchAHVConsistencyV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads((ARTIFACT_DIR / "cross_batch_ahv_object_inventory_v1.json").read_text(encoding="utf-8"))
        cls.ledger = json.loads((ARTIFACT_DIR / "cross_batch_consistency_ledger_v1.json").read_text(encoding="utf-8"))
        cls.query_set = json.loads((ARTIFACT_DIR / "cross_batch_adversarial_query_set_v1.json").read_text(encoding="utf-8"))
        cls.before = json.loads((ARTIFACT_DIR / "cross_batch_adversarial_before_fix_v1.json").read_text(encoding="utf-8"))
        cls.after = json.loads((ARTIFACT_DIR / "cross_batch_adversarial_after_fix_v1.json").read_text(encoding="utf-8"))
        cls.fix_ledger = json.loads((ARTIFACT_DIR / "cross_batch_fix_ledger_v1.json").read_text(encoding="utf-8"))
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_inventory_covers_both_batches(self) -> None:
        self.assertEqual(self.inventory["audited_object_count"], 40)
        self.assertEqual(self.inventory["ahv_v1_object_count"], 20)
        self.assertEqual(self.inventory["ahv2_object_count"], 20)
        layer_counts = {
            row["promotion_source_layer"]: 0
            for row in self.inventory["objects"]
        }
        for row in self.inventory["objects"]:
            layer_counts[row["promotion_source_layer"]] += 1
        self.assertEqual(layer_counts[AHV_V1_LAYER], 20)
        self.assertEqual(layer_counts[AHV2_LAYER], 20)

    def test_consistency_ledger_after_fix_is_clean(self) -> None:
        metrics = self.ledger["metrics"]
        self.assertEqual(metrics["audited_object_count"], 40)
        self.assertEqual(metrics["duplicate_concept_count"], 0)
        self.assertEqual(metrics["active_contains_count"], 0)
        self.assertEqual(metrics["active_single_char_alias_count"], 0)
        self.assertEqual(metrics["duplicate_active_alias_count"], 0)
        self.assertEqual(metrics["inactive_alias_primary_backdoor_count"], 0)
        self.assertEqual(metrics["review_only_learner_safe_conflict_count"], 0)
        self.assertEqual(metrics["confidence_inconsistent_count"], 0)
        self.assertEqual(metrics["evidence_type_inconsistent_count"], 0)

    def test_query_set_meets_required_family_counts(self) -> None:
        counts = self.query_set["query_type_counts"]
        self.assertGreaterEqual(self.query_set["query_count"], 100)
        self.assertGreaterEqual(counts["ahv_v1_canonical_guard"], 10)
        self.assertGreaterEqual(counts["ahv2_canonical_guard"], 10)
        self.assertGreaterEqual(counts["cross_batch_concept_conflict"], 25)
        self.assertGreaterEqual(counts["non_definition_intent"], 20)
        self.assertGreaterEqual(counts["alias_partial_negative"], 20)
        self.assertGreaterEqual(counts["review_only_rejected_guard"], 10)

    def test_after_fix_regression_boundaries_hold(self) -> None:
        metrics = self.after["metrics"]
        self.assertEqual(metrics["total_query_count"], 120)
        self.assertEqual(metrics["wrong_ahv_primary_hit_count"], 0)
        self.assertEqual(metrics["wrong_term_normalization_count"], 0)
        self.assertEqual(metrics["non_definition_intent_hijack_count"], 0)
        self.assertEqual(metrics["comparison_primary_hijack_count"], 0)
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_count"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(metrics["ahv_v1_guard_pass_count"], 20)
        self.assertEqual(metrics["ahv2_guard_pass_count"], 20)
        self.assertEqual(metrics["regression_pass_count"], 120)
        self.assertEqual(metrics["regression_fail_count"], 0)
        self.assertFalse(self.after["failures"])

    def test_before_fix_had_metadata_work_but_no_object_expansion(self) -> None:
        self.assertEqual(self.before["metrics"]["total_query_count"], 120)
        self.assertEqual(self.fix_ledger["metrics"]["before_safe_object_count"], 40)
        self.assertEqual(self.fix_ledger["metrics"]["after_safe_object_count"], 40)
        self.assertEqual(self.fix_ledger["metrics"]["new_safe_object_count_delta"], 0)
        self.assertEqual(self.fix_ledger["metrics"]["downgraded_object_count"], 0)
        self.assertGreaterEqual(self.fix_ledger["metrics"]["changed_primary_evidence_type_count"], 1)

    def test_db_has_no_ahv3_or_active_contains_regression(self) -> None:
        ahv3_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE concept_id LIKE 'AHV3-%'
               OR promotion_source_layer LIKE '%ahv3%'
            """
        ).fetchone()[0]
        self.assertEqual(ahv3_count, 0)

        active_contains = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon AS l
            JOIN definition_term_registry AS d
              ON d.concept_id = l.target_id
            WHERE l.entry_type = 'term_surface'
              AND l.is_active = 1
              AND l.match_mode != 'exact'
              AND d.promotion_source_layer IN (?, ?)
            """,
            (AHV_V1_LAYER, AHV2_LAYER),
        ).fetchone()[0]
        self.assertEqual(active_contains, 0)


if __name__ == "__main__":
    unittest.main()
