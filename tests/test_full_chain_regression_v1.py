from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path

from scripts.full_chain_regression.run_full_chain_production_like_regression_v1 import build_query_specs


ARTIFACT_DIR = Path("artifacts/full_chain_regression")
DOC_PATH = Path("docs/full_chain_regression/full_chain_production_like_regression_v1.md")
DB_PATH = Path("artifacts/zjshl_v1.db")


class FullChainRegressionV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.query_set = json.loads((ARTIFACT_DIR / "full_chain_query_set_v1.json").read_text(encoding="utf-8"))
        cls.results = json.loads((ARTIFACT_DIR / "full_chain_regression_results_v1.json").read_text(encoding="utf-8"))
        cls.failures = json.loads((ARTIFACT_DIR / "full_chain_failure_cases_v1.json").read_text(encoding="utf-8"))
        cls.repair_queue = json.loads((ARTIFACT_DIR / "data_layer_repair_queue_v1.json").read_text(encoding="utf-8"))
        cls.latency = json.loads((ARTIFACT_DIR / "latency_snapshot_v1.json").read_text(encoding="utf-8"))
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_static_query_set_meets_required_coverage(self) -> None:
        specs = build_query_specs()
        counts: dict[str, int] = {}
        for spec in specs:
            counts[spec.query_category] = counts.get(spec.query_category, 0) + 1
        self.assertGreaterEqual(len(specs), 100)
        self.assertGreaterEqual(counts["ahv_v1_canonical"], 15)
        self.assertGreaterEqual(counts["ahv2_canonical"], 15)
        self.assertGreaterEqual(counts["cross_batch_adversarial"], 25)
        self.assertGreaterEqual(counts["formula"], 20)
        self.assertGreaterEqual(counts["learner_short_normal"], 20)
        self.assertGreaterEqual(counts["review_only_support_boundary"], 10)
        self.assertGreaterEqual(counts["negative_modern_unrelated"], 10)

    def test_required_artifacts_exist(self) -> None:
        required = [
            ARTIFACT_DIR / "full_chain_query_set_v1.json",
            ARTIFACT_DIR / "full_chain_query_set_v1.md",
            ARTIFACT_DIR / "full_chain_regression_results_v1.json",
            ARTIFACT_DIR / "full_chain_regression_results_v1.md",
            ARTIFACT_DIR / "full_chain_failure_cases_v1.json",
            ARTIFACT_DIR / "full_chain_failure_cases_v1.md",
            ARTIFACT_DIR / "data_layer_repair_queue_v1.json",
            ARTIFACT_DIR / "data_layer_repair_queue_v1.md",
            ARTIFACT_DIR / "latency_snapshot_v1.json",
            ARTIFACT_DIR / "latency_snapshot_v1.md",
            DOC_PATH,
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

    def test_result_schema_and_mode_completion(self) -> None:
        metrics = self.results["metrics"]
        self.assertGreaterEqual(metrics["query_count"], 100)
        self.assertIn("A_data_plane_baseline", metrics["completed_modes"])
        self.assertEqual(len(self.query_set["queries"]), metrics["query_count"])
        completed_modes = set(metrics["completed_modes"])
        for mode in completed_modes:
            records = [record for record in self.results["records"] if record["run_mode"] == mode]
            self.assertEqual(len(records), metrics["query_count"], mode)

        required_fields = {
            "query",
            "query_category",
            "run_mode",
            "answer_mode",
            "answer_text",
            "primary_ids",
            "secondary_ids",
            "review_ids",
            "primary_record_types",
            "forbidden_primary_items",
            "matched_formula_ids",
            "matched_definition_concept_ids",
            "query_focus_source",
            "term_normalization",
            "formula_normalization",
            "raw_top5_candidates",
            "rerank_top5_candidates",
            "llm_used",
            "latency_ms",
            "faithfulness_judgement",
            "mode_judgement",
            "citation_judgement",
            "failure_type",
            "pass",
        }
        for record in self.results["records"]:
            self.assertTrue(required_fields.issubset(record), record.get("query_id"))

    def test_each_failure_has_type_and_repair_queue_is_bounded(self) -> None:
        self.assertEqual(
            self.failures["failure_count"],
            sum(1 for record in self.results["records"] if not record["pass"]),
        )
        for failure in self.failures["failures"]:
            self.assertIsInstance(failure["failure_type"], str)
            self.assertNotEqual(failure["failure_type"], "none")
            self.assertTrue(failure["failure_reasons"])

        self.assertLessEqual(len(self.repair_queue["P0"]), 10)
        self.assertLessEqual(len(self.repair_queue["P1"]), 30)
        for priority in ("P0", "P1", "P2"):
            for item in self.repair_queue[priority]:
                self.assertIn("recommended_next_action", item)
                self.assertTrue(item["recommended_next_action"])

    def test_latency_snapshot_has_completed_modes(self) -> None:
        completed_modes = set(self.results["metrics"]["completed_modes"])
        self.assertTrue(completed_modes.issubset(set(self.latency["modes"])))
        for mode in completed_modes:
            data = self.latency["modes"][mode]
            self.assertGreaterEqual(data["count"], 100)
            self.assertGreater(data["latency_p50_ms"], 0)
            self.assertGreater(data["latency_p95_ms"], 0)

    def test_no_ahv3_object_added(self) -> None:
        ahv3_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE concept_id LIKE 'AHV3-%'
               OR promotion_source_layer LIKE '%ahv3%'
            """
        ).fetchone()[0]
        self.assertEqual(ahv3_count, 0)


if __name__ == "__main__":
    unittest.main()
