from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


ARTIFACT_DIR = Path("artifacts/full_chain_p0_repairs")
DOC_PATH = Path("docs/full_chain_p0_repairs/full_chain_p0_boundary_repairs_v1.md")
DB_PATH = Path("artifacts/zjshl_v1.db")


class FullChainP0BoundaryRepairsV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.regression = json.loads((ARTIFACT_DIR / "p0_boundary_regression_v1.json").read_text(encoding="utf-8"))
        cls.before_after = json.loads((ARTIFACT_DIR / "p0_boundary_before_after_v1.json").read_text(encoding="utf-8"))
        cls.metrics_check = json.loads(
            (ARTIFACT_DIR / "failure_metrics_consistency_check_v1.json").read_text(encoding="utf-8")
        )
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_required_artifacts_exist(self) -> None:
        required = [
            DOC_PATH,
            ARTIFACT_DIR / "p0_boundary_before_after_v1.json",
            ARTIFACT_DIR / "p0_boundary_before_after_v1.md",
            ARTIFACT_DIR / "p0_boundary_regression_v1.json",
            ARTIFACT_DIR / "p0_boundary_regression_v1.md",
            ARTIFACT_DIR / "failure_metrics_consistency_check_v1.json",
            ARTIFACT_DIR / "failure_metrics_consistency_check_v1.md",
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

    def test_failure_metrics_consistency_is_explicit(self) -> None:
        self.assertTrue(self.metrics_check["consistent"])
        self.assertEqual(self.metrics_check["results_fail_record_count"], 37)
        self.assertEqual(self.metrics_check["failure_cases_failure_count"], 37)
        self.assertEqual(self.metrics_check["results_metric_failure_type_total"], 37)
        self.assertEqual(self.metrics_check["failure_cases_type_total"], 37)
        self.assertEqual(self.metrics_check["missing_or_none_failure_type_count"], 0)

    def test_p0_original_queries_are_no_longer_failures(self) -> None:
        metrics = self.regression["metrics"]
        self.assertEqual(metrics["p0_failure_count"], 0)
        self.assertEqual(metrics["regression_fail_count"], 0)
        self.assertEqual(self.before_after["after_failure_count"], 0)

        after = self.before_after["after"]
        self.assertEqual(len(after), 12)
        for record in after:
            self.assertTrue(record["p0_pass"], record["query"])
            self.assertFalse(record["primary_ids"], record["query"])
            self.assertNotEqual(record["answer_mode"], "strong", record["query"])
            if record["query"] == "白虎是什么意思？":
                self.assertEqual(record["answer_mode"], "refuse")
            else:
                self.assertEqual(record["answer_mode"], "weak_with_review_notice")

    def test_mainline_guards_have_no_regression(self) -> None:
        metrics = self.regression["metrics"]
        self.assertEqual(metrics["completed_modes"], [
            "A_data_plane_baseline",
            "B_retrieval_rerank",
            "C_production_like_full_chain",
        ])
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_count"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(metrics["ahv_guard_fail_count"], 0)
        self.assertEqual(metrics["formula_guard_fail_count"], 0)
        self.assertEqual(metrics["gold_safe_definition_fail_count"], 0)
        self.assertEqual(metrics["review_only_boundary_guard_fail_count"], 0)
        self.assertEqual(metrics["negative_modern_guard_fail_count"], 0)
        self.assertEqual(metrics["mainline_guard_failure_count"], 0)

    def test_white_tiger_formula_queries_remain_available(self) -> None:
        records = [
            record
            for record in self.regression["records"]
            if record["query_id"] in {"p0_variant_08", "p0_variant_09", "p0_variant_10", "p0_variant_11"}
            if record["query"] in {
                "白虎汤是什么意思？",
                "白虎汤方的条文是什么？",
                "白虎加人参汤方的条文是什么？",
                "白虎汤和白虎加人参汤有什么区别？",
            }
        ]
        self.assertEqual(len(records), 12)
        for record in records:
            self.assertTrue(record["p0_pass"], record["query"])
            self.assertNotEqual(record["answer_mode"], "refuse", record["query"])
            if record["query"] != "白虎汤是什么意思？":
                self.assertEqual(record["answer_mode"], "strong", record["query"])

    def test_no_p0_object_or_alias_backdoor_was_opened(self) -> None:
        ahv3_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE concept_id LIKE 'AHV3-%'
               OR promotion_source_layer LIKE '%ahv3%'
            """
        ).fetchone()[0]
        self.assertEqual(ahv3_count, 0)

        unsafe_safe_primary_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM retrieval_ready_definition_view
            WHERE canonical_term IN ('清邪中上', '反', '两阳', '白虎')
               OR normalized_term IN ('清邪中上', '反', '两阳', '白虎')
            """
        ).fetchone()[0]
        self.assertEqual(unsafe_safe_primary_count, 0)

        active_learner_backdoor_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE is_active = 1
              AND normalized_surface_form IN ('清邪中上', '清邪', '浊邪', '反', '两阳', '两阳病', '白虎')
            """
        ).fetchone()[0]
        self.assertEqual(active_learner_backdoor_count, 0)


if __name__ == "__main__":
    unittest.main()
