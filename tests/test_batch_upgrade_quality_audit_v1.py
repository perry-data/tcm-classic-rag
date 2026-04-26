from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


LEDGER_PATH = Path("artifacts/data_plane_batch_audit/ahv_quality_audit_ledger_v1.json")
REGRESSION_PATH = Path("artifacts/data_plane_batch_audit/ahv_quality_audit_regression_v1.json")
DB_PATH = Path("artifacts/zjshl_v1.db")
REQUIRED_FOCUS_TERMS = {
    "太阳病",
    "伤寒",
    "温病",
    "柔痓",
    "痓病",
    "结脉",
    "促脉",
    "霍乱",
    "劳复",
    "食复",
}
ALLOWED_VERDICTS = {
    "keep_safe_primary",
    "keep_safe_primary_but_needs_notes",
    "adjust_alias",
    "adjust_primary_sentence",
    "downgrade_to_review_only",
    "downgrade_to_support_only",
    "defer_for_manual_review",
}


class BatchUpgradeQualityAuditV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.regression = json.loads(REGRESSION_PATH.read_text(encoding="utf-8"))
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_ledger_covers_all_ahv_objects_with_required_fields(self) -> None:
        objects = self.ledger["audited_objects"]
        self.assertEqual(self.ledger["metrics"]["audited_ahv_object_count"], 20)
        self.assertEqual(len(objects), 20)
        self.assertTrue(REQUIRED_FOCUS_TERMS.issubset({item["canonical_term"] for item in objects}))
        for item in objects:
            self.assertIn(item["quality_audit_verdict"], ALLOWED_VERDICTS)
            self.assertTrue(item["quality_reason"])
            self.assertTrue(item["fix_action"])
            self.assertIn(item["risk_level_after"], {"low", "medium", "high"})
            self.assertIn("primary_sentence_quality", item["checks"])
            self.assertIn("runtime_behavior", item["checks"])

    def test_primary_sentence_and_source_fixes_landed(self) -> None:
        expected = {
            "结脉": ("脉来缓，时一止复来者，名曰结", "records_main_passages"),
            "滑脉": ("翕奄沉，名曰滑", "records_main_passages"),
            "痓病": ("背反张者，痓病也", "records_passages"),
            "霍乱": ("呕吐而利，名曰霍乱", "records_main_passages"),
            "行尸": ("脉病患不病，名曰行尸", "risk_registry_ambiguous"),
            "内虚": ("人病脉不病，名曰内虚", "risk_registry_ambiguous"),
        }
        for term, (text, source_table) in expected.items():
            with self.subTest(term=term):
                row = self.conn.execute(
                    """
                    SELECT primary_evidence_text, primary_source_table
                    FROM definition_term_registry
                    WHERE canonical_term = ?
                      AND promotion_source_layer = 'ambiguous_high_value_batch_safe_primary'
                    """,
                    (term,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["primary_evidence_text"], text)
                self.assertEqual(row["primary_source_table"], source_table)

    def test_broad_aliases_are_deactivated_in_alias_and_learner_layers(self) -> None:
        deactivated_aliases = {
            "温病": "春温",
            "暑病": "暑病者",
            "时行寒疫": "寒疫",
            "劳复": "劳动病",
            "食复": "强食复病",
        }
        for term, alias in deactivated_aliases.items():
            with self.subTest(term=term, alias=alias):
                alias_row = self.conn.execute(
                    """
                    SELECT alias_type, is_active
                    FROM term_alias_registry
                    WHERE canonical_term = ?
                      AND alias = ?
                    """,
                    (term, alias),
                ).fetchone()
                self.assertIsNotNone(alias_row)
                self.assertEqual(alias_row["alias_type"], "learner_risky")
                self.assertEqual(alias_row["is_active"], 0)
                learner_count = self.conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM learner_query_normalization_lexicon
                    WHERE target_term = ?
                      AND surface_form = ?
                      AND is_active = 1
                    """,
                    (term, alias),
                ).fetchone()[0]
                self.assertEqual(learner_count, 0)

    def test_regression_metrics_hold_quality_boundaries(self) -> None:
        metrics = self.regression["metrics"]
        self.assertEqual(metrics["audited_ahv_object_count"], 20)
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_count"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(metrics["ahv_primary_hit_count"], metrics["keep_safe_primary_count"])
        self.assertEqual(metrics["ahv_primary_miss_count"], 0)
        self.assertEqual(metrics["regression_fail_count"], 0)


if __name__ == "__main__":
    unittest.main()
