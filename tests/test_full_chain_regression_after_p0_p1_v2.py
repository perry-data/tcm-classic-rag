from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


ARTIFACT_DIR = Path("artifacts/full_chain_regression")
DOC_PATH = Path("docs/full_chain_regression/full_chain_regression_after_p0_p1_v2.md")
DB_PATH = Path("artifacts/zjshl_v1.db")
MODES = (
    "A_data_plane_baseline",
    "B_retrieval_rerank",
    "C_production_like_full_chain",
)
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
AHV_SAFE_LAYERS = (
    "ambiguous_high_value_batch_safe_primary",
    "ambiguous_high_value_evidence_upgrade_v2_safe_primary",
)


class FullChainRegressionAfterP0P1V2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = json.loads((ARTIFACT_DIR / "full_chain_regression_results_v2.json").read_text(encoding="utf-8"))
        cls.failures = json.loads((ARTIFACT_DIR / "full_chain_failure_cases_v2.json").read_text(encoding="utf-8"))
        cls.delta = json.loads((ARTIFACT_DIR / "full_chain_v1_vs_v2_delta.json").read_text(encoding="utf-8"))
        cls.residual_queue = json.loads(
            (ARTIFACT_DIR / "residual_repair_queue_after_p0_p1_v2.json").read_text(encoding="utf-8")
        )
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def formula_id(self, canonical_name: str) -> str:
        row = self.conn.execute(
            "SELECT formula_id FROM formula_canonical_registry WHERE canonical_name = ?",
            (canonical_name,),
        ).fetchone()
        self.assertIsNotNone(row, canonical_name)
        return str(row["formula_id"])

    def records_for_query(self, query: str) -> list[dict]:
        return [record for record in self.results["records"] if record["query"] == query]

    def test_required_v2_artifacts_exist(self) -> None:
        required = [
            DOC_PATH,
            ARTIFACT_DIR / "full_chain_regression_results_v2.json",
            ARTIFACT_DIR / "full_chain_failure_cases_v2.json",
            ARTIFACT_DIR / "full_chain_v1_vs_v2_delta.json",
            ARTIFACT_DIR / "residual_repair_queue_after_p0_p1_v2.json",
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        self.assertEqual(self.results["query_count"], 120)
        self.assertEqual(self.results["record_count"], 360)
        self.assertEqual(self.failures["failure_count"], self.results["failed_cases"])
        self.assertEqual(len(self.failures["per_failure_record"]), self.failures["failure_count"])
        self.assertIn("P2_candidates", self.residual_queue)
        self.assertIn("P3_observations", self.residual_queue)

    def test_a_b_c_completed_and_c_uses_live_llm(self) -> None:
        statuses = {status["run_mode"]: status for status in self.results["mode_statuses"]}
        for mode in MODES:
            self.assertEqual(statuses[mode]["status"], "completed", statuses[mode])
            self.assertEqual(self.results[f"mode_{mode[0]}_result"]["total"], 120)

        c_status = statuses["C_production_like_full_chain"]
        self.assertTrue((c_status.get("llm_preflight") or {}).get("llm_attempted"))
        self.assertTrue((c_status.get("llm_preflight") or {}).get("llm_used"))
        c_records = [record for record in self.results["records"] if record["run_mode"] == "C_production_like_full_chain"]
        self.assertTrue(any(record["llm_used"] and record["llm_answer_source"] == "llm" for record in c_records))
        self.assertFalse(all((record.get("llm_debug") or {}).get("skipped_reason") == "disabled" for record in c_records))

    def test_p0_original_queries_still_pass(self) -> None:
        expectations = {
            "清邪中上是什么意思？": "weak_with_review_notice",
            "反是什么意思？": "weak_with_review_notice",
            "两阳是什么意思？": "weak_with_review_notice",
            "白虎是什么意思？": "refuse",
        }
        self.assertTrue(self.results["p0_guard_summary"]["pass"])
        self.assertTrue(self.delta["p0_delta"]["all_v2_pass"])
        for query, expected_answer_mode in expectations.items():
            records = self.records_for_query(query)
            self.assertEqual(len(records), 3, query)
            for record in records:
                with self.subTest(query=query, mode=record["run_mode"]):
                    self.assertTrue(record["pass"])
                    self.assertEqual(record["answer_mode"], expected_answer_mode)
                    self.assertEqual(record["failure_type"], "none")
                    self.assertEqual(record["primary_ids"], [])
                    self.assertEqual(record["matched_definition_concept_ids"], [])

    def test_p1_queries_still_pass(self) -> None:
        formula_expectations = {
            "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？": {
                "formula_ids": {
                    self.formula_id("桂枝加附子汤"),
                    self.formula_id("桂枝加浓朴杏子汤"),
                },
                "primary_ids": {
                    "safe:main_passages:ZJSHL-CH-025-P-0004",
                    "safe:main_passages:ZJSHL-CH-025-P-0003",
                },
            },
            "麻黄汤方和桂枝汤方的区别是什么？": {
                "formula_ids": {
                    self.formula_id("麻黄汤"),
                    self.formula_id("桂枝汤"),
                },
                "primary_ids": {
                    "safe:main_passages:ZJSHL-CH-009-P-0022",
                    "safe:main_passages:ZJSHL-CH-008-P-0217",
                },
            },
        }
        self.assertTrue(self.results["p1_guard_summary"]["pass"])
        self.assertTrue(self.delta["p1_delta"]["all_v2_pass"])
        for query, expected in formula_expectations.items():
            for record in self.records_for_query(query):
                with self.subTest(query=query, mode=record["run_mode"]):
                    self.assertTrue(record["pass"])
                    self.assertEqual(record["answer_mode"], "strong")
                    self.assertEqual(record["failure_type"], "none")
                    self.assertTrue(expected["formula_ids"].issubset(set(record["matched_formula_ids"])))
                    self.assertTrue(expected["primary_ids"].issubset(set(record["primary_ids"])))
                    self.assertEqual(record["citation_judgement"], "pass: citation slots match answer mode")

        for record in self.records_for_query("干呕是什么意思？"):
            with self.subTest(query="干呕是什么意思？", mode=record["run_mode"]):
                self.assertTrue(record["pass"])
                self.assertEqual(record["answer_mode"], "weak_with_review_notice")
                self.assertEqual(record["failure_type"], "none")
                self.assertEqual(record["primary_ids"], [])
                self.assertEqual(record["matched_definition_concept_ids"], [])
                self.assertEqual((record["term_normalization"] or {}).get("type"), "none")
                self.assertIn("safe:main_passages:ZJSHL-CH-014-P-0188", record["secondary_ids"])
                self.assertIn("safe:main_passages:ZJSHL-CH-015-P-0324", record["secondary_ids"])
                self.assertIn("safe:main_passages:ZJSHL-CH-008-P-0215", record["secondary_ids"])
                self.assertEqual(record["llm_answer_source"], "baseline_p1_conservative_learner_guard")

    def test_primary_evidence_boundary_metrics_are_clean(self) -> None:
        metrics = self.results["metrics"]
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_total"], 0)
        self.assertEqual(metrics["wrong_definition_primary_total"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)

    def test_raw_full_and_review_only_materials_stay_out_of_primary(self) -> None:
        for record in self.results["records"]:
            with self.subTest(query=record["query"], mode=record["run_mode"]):
                self.assertFalse(record["forbidden_primary_items"])
                self.assertFalse(record["review_only_primary_conflicts"])
                for record_id in record.get("primary_ids") or []:
                    self.assertFalse(str(record_id).startswith("full:passages:"))
                    self.assertFalse(str(record_id).startswith("full:ambiguous_passages:"))
                    self.assertFalse(str(record_id).startswith("full:annotations:"))
                    self.assertFalse(str(record_id).startswith("full:annotation_links:"))
                for record_type in record.get("primary_record_types") or []:
                    self.assertNotIn(record_type, FORBIDDEN_PRIMARY_TYPES)

    def test_ahv_v1_and_ahv2_exact_normalization_do_not_regress(self) -> None:
        ahv_records = [
            record
            for record in self.results["records"]
            if record["query_category"] in {"ahv_v1_canonical", "ahv2_canonical"}
        ]
        self.assertEqual(len(ahv_records), 96)
        for record in ahv_records:
            expected_ids = set(record.get("expected_concept_ids") or [])
            matched_ids = set(record.get("matched_definition_concept_ids") or [])
            primary_ids = set(record.get("primary_definition_ids") or [])
            matches = (record.get("term_normalization") or {}).get("matches") or []
            with self.subTest(query=record["query"], mode=record["run_mode"]):
                self.assertTrue(expected_ids)
                self.assertTrue(expected_ids & (matched_ids | primary_ids))
                self.assertTrue(any(match.get("match_mode") == "exact" for match in matches), record["query"])

    def test_no_ahv3_or_v2_normalization_backdoors_added(self) -> None:
        ahv3_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE concept_id LIKE 'AHV3-%'
               OR lower(promotion_source_layer) LIKE '%ahv3%'
            """
        ).fetchone()[0]
        self.assertEqual(ahv3_count, 0)

        non_exact_ahv_normalization_count = self.conn.execute(
            f"""
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon AS l
            JOIN definition_term_registry AS d ON d.concept_id = l.target_id
            WHERE l.is_active = 1
              AND l.match_mode != 'exact'
              AND d.promotion_source_layer IN ({",".join("?" for _ in AHV_SAFE_LAYERS)})
            """,
            AHV_SAFE_LAYERS,
        ).fetchone()[0]
        self.assertEqual(non_exact_ahv_normalization_count, 0)

        v2_active_contains_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE is_active = 1
              AND match_mode = 'contains'
              AND source LIKE '%full_chain_regression_after_p0_p1_v2%'
            """
        ).fetchone()[0]
        self.assertEqual(v2_active_contains_count, 0)

        active_single_char_alias_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM term_alias_registry
            WHERE is_active = 1
              AND length(normalized_alias) = 1
            """
        ).fetchone()[0]
        self.assertEqual(active_single_char_alias_count, 0)

        active_single_char_learner_surface_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE is_active = 1
              AND length(normalized_surface_form) = 1
            """
        ).fetchone()[0]
        self.assertEqual(active_single_char_learner_surface_count, 0)


if __name__ == "__main__":
    unittest.main()
