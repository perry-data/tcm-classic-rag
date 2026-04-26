from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


ARTIFACT_DIR = Path("artifacts/data_plane_batch_upgrade_v2")
DB_PATH = Path("artifacts/zjshl_v1.db")
AHV2_SAFE_LAYER = "ambiguous_high_value_evidence_upgrade_v2_safe_primary"
AHV2_SUPPORT_LAYER = "ambiguous_high_value_evidence_upgrade_v2_support_only"


class AmbiguousHighValueEvidenceUpgradeV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        cls.candidate_pool = json.loads((ARTIFACT_DIR / "ahv2_candidate_pool_v1.json").read_text(encoding="utf-8"))
        cls.batch_ledger = json.loads((ARTIFACT_DIR / "ahv2_batch_upgrade_ledger_v1.json").read_text(encoding="utf-8"))
        cls.quality = json.loads((ARTIFACT_DIR / "ahv2_quality_audit_ledger_v1.json").read_text(encoding="utf-8"))
        cls.query_set = json.loads((ARTIFACT_DIR / "ahv2_adversarial_query_set_v1.json").read_text(encoding="utf-8"))
        cls.before = json.loads((ARTIFACT_DIR / "ahv2_adversarial_before_fix_v1.json").read_text(encoding="utf-8"))
        cls.after = json.loads((ARTIFACT_DIR / "ahv2_adversarial_after_fix_v1.json").read_text(encoding="utf-8"))
        cls.fix_ledger = json.loads((ARTIFACT_DIR / "ahv2_fix_ledger_v1.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_candidate_pool_and_batch_counts(self) -> None:
        self.assertEqual(self.candidate_pool["candidate_count"], 32)
        self.assertEqual(self.candidate_pool["category_counts"], {"A": 20, "B": 8, "C": 4})
        summary = self.batch_ledger["summary"]
        self.assertEqual(summary["promoted_safe_primary_count"], 20)
        self.assertEqual(summary["support_only_registered_count"], 8)
        self.assertEqual(summary["rejected_count"], 4)
        self.assertEqual(summary["new_active_contains_learner_surface_count"], 0)
        self.assertEqual(summary["single_active_alias_count"], 0)
        self.assertEqual(summary["risky_or_review_active_alias_count"], 0)

    def test_registry_view_and_support_boundaries(self) -> None:
        safe_ids = {
            row["concept_id"]
            for row in self.conn.execute(
                "SELECT concept_id FROM definition_term_registry WHERE promotion_source_layer = ?",
                (AHV2_SAFE_LAYER,),
            )
        }
        support_ids = {
            row["concept_id"]
            for row in self.conn.execute(
                "SELECT concept_id FROM definition_term_registry WHERE promotion_source_layer = ?",
                (AHV2_SUPPORT_LAYER,),
            )
        }
        view_ids = {
            row["concept_id"]
            for row in self.conn.execute(
                "SELECT concept_id FROM retrieval_ready_definition_view WHERE concept_id LIKE 'AHV2-%'"
            )
        }
        self.assertEqual(len(safe_ids), 20)
        self.assertEqual(len(support_ids), 8)
        self.assertEqual(view_ids, safe_ids)

        support_active_lexicon = self.conn.execute(
            f"""
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE target_id IN ({','.join('?' for _ in support_ids)})
              AND is_active = 1
            """,
            tuple(support_ids),
        ).fetchone()[0]
        self.assertEqual(support_active_lexicon, 0)

    def test_active_ahv2_normalization_is_exact_only(self) -> None:
        rows = self.conn.execute(
            """
            SELECT surface_form, target_term, match_mode
            FROM learner_query_normalization_lexicon
            WHERE is_active = 1
              AND target_id IN (
                  SELECT concept_id
                  FROM definition_term_registry
                  WHERE promotion_source_layer = ?
              )
            """,
            (AHV2_SAFE_LAYER,),
        ).fetchall()
        self.assertGreaterEqual(len(rows), 20)
        self.assertTrue(all(row["match_mode"] == "exact" for row in rows))

    def test_quality_audit_covers_all_a_objects(self) -> None:
        metrics = self.quality["metrics"]
        self.assertEqual(metrics["quality_audited_A_count"], 20)
        self.assertEqual(metrics["adjust_alias_before_release_count"], 0)
        self.assertEqual(metrics["support_only_instead_count"], 0)
        self.assertEqual(metrics["reject_instead_count"], 0)

    def test_adversarial_query_set_covers_required_families(self) -> None:
        counts = self.query_set["query_type_counts"]
        self.assertGreaterEqual(self.query_set["query_count"], 80)
        self.assertEqual(counts["ahv2_canonical_guard"], 20)
        self.assertGreaterEqual(counts["similar_concept_false_trigger"], 20)
        self.assertEqual(counts["disabled_alias_recheck"], 5)
        self.assertEqual(counts["partial_word_literal_similarity"], 10)
        self.assertEqual(counts["non_definition_intent"], 10)
        self.assertEqual(counts["negative_unrelated"], 10)
        self.assertEqual(counts["formula_guard"], 5)
        self.assertEqual(counts["gold_safe_definition_guard"], 5)
        self.assertEqual(counts["ahv_v1_guard"], 5)
        self.assertEqual(counts["review_only_boundary_guard"], 4)

    def test_before_fix_exposes_closed_loop_failure(self) -> None:
        metrics = self.before["metrics"]
        self.assertEqual(metrics["total_query_count"], 94)
        self.assertEqual(metrics["wrong_ahv2_primary_hit_count"], 0)
        self.assertEqual(metrics["wrong_term_normalization_count"], 0)
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["regression_fail_count"], 4)

    def test_after_fix_holds_all_required_boundaries(self) -> None:
        metrics = self.after["metrics"]
        self.assertEqual(metrics["total_query_count"], 94)
        self.assertEqual(metrics["new_safe_object_primary_hit_count"], 20)
        self.assertEqual(metrics["wrong_ahv2_primary_hit_count"], 0)
        self.assertEqual(metrics["wrong_term_normalization_count"], 0)
        self.assertEqual(metrics["disabled_alias_still_hit_count"], 0)
        self.assertEqual(metrics["partial_word_false_positive_count"], 0)
        self.assertEqual(metrics["non_definition_intent_hijack_count"], 0)
        self.assertEqual(metrics["negative_sample_false_positive_count"], 0)
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_count"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(metrics["ahv_v1_guard_pass_count"], 5)
        self.assertEqual(metrics["regression_pass_count"], 94)
        self.assertEqual(metrics["regression_fail_count"], 0)
        self.assertFalse(self.after["failures"])

    def test_fix_ledger_keeps_data_changes_minimal(self) -> None:
        metrics = self.fix_ledger["metrics"]
        self.assertEqual(metrics["changed_learner_surface_count"], 0)
        self.assertEqual(metrics["deactivated_alias_count"], 0)
        self.assertEqual(metrics["downgraded_object_count"], 0)
        self.assertEqual(metrics["new_ahv2_object_count"], 0)
        self.assertGreaterEqual(len(self.fix_ledger["runtime_fixes"]), 2)


if __name__ == "__main__":
    unittest.main()
