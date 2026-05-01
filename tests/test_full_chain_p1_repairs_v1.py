from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path


ARTIFACT_DIR = Path("artifacts/full_chain_p1_repairs")
DOC_PATH = Path("docs/full_chain_p1_repairs/full_chain_p1_repairs_v1.md")
DB_PATH = Path("artifacts/zjshl_v1.db")
MODES = ("A", "B", "C")
FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
AHV_SAFE_LAYERS = (
    "ambiguous_high_value_batch_safe_primary",
    "ambiguous_high_value_evidence_upgrade_v2_safe_primary",
)


class FullChainP1RepairsV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.regression = json.loads((ARTIFACT_DIR / "p1_regression_v1.json").read_text(encoding="utf-8"))
        cls.before_after = json.loads((ARTIFACT_DIR / "p1_before_after_v1.json").read_text(encoding="utf-8"))
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

    def concept_id(self, canonical_term: str) -> str:
        row = self.conn.execute(
            "SELECT concept_id FROM definition_term_registry WHERE canonical_term = ? AND is_active = 1",
            (canonical_term,),
        ).fetchone()
        self.assertIsNotNone(row, canonical_term)
        return str(row["concept_id"])

    def modes_for(self, query: str) -> dict[str, dict]:
        return self.regression["per_query_result"][query]["modes"]

    def test_required_artifacts_exist_and_metrics_are_clean(self) -> None:
        required = [
            DOC_PATH,
            ARTIFACT_DIR / "p1_before_after_v1.json",
            ARTIFACT_DIR / "p1_before_after_v1.md",
            ARTIFACT_DIR / "p1_regression_v1.json",
            ARTIFACT_DIR / "p1_regression_v1.md",
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))
            self.assertGreater(path.stat().st_size, 0, str(path))

        self.assertEqual(self.regression["total_cases"], 51)
        self.assertEqual(self.regression["passed_cases"], 51)
        self.assertEqual(self.regression["failed_cases"], 0)
        self.assertEqual(self.regression["forbidden_primary_total"], 0)
        self.assertEqual(self.regression["review_only_primary_conflict_total"], 0)
        self.assertEqual(self.regression["wrong_definition_primary_total"], 0)
        self.assertEqual(self.regression["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(self.regression["citation_error_total"], 0)
        self.assertEqual(self.regression["assembler_slot_error_total"], 0)
        self.assertEqual(self.regression["answer_mode_calibration_error_total"], 0)

        for mode_key in ("mode_A_result", "mode_B_result", "mode_C_result"):
            self.assertEqual(self.regression[mode_key]["status"], "pass")
            self.assertEqual(self.regression[mode_key]["failed_cases"], 0)

        c_status = next(
            status
            for status in self.regression["mode_statuses"]
            if status["run_mode"] == "C_production_like_full_chain"
        )
        self.assertEqual(c_status["status"], "completed")
        self.assertTrue((c_status["llm_preflight"] or {})["llm_attempted"])
        self.assertTrue((c_status["llm_preflight"] or {})["llm_used"])

    def test_three_p1_queries_pass_in_all_modes(self) -> None:
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
        for query, expected in formula_expectations.items():
            for mode, result in self.modes_for(query).items():
                with self.subTest(query=query, mode=mode):
                    self.assertTrue(result["pass"])
                    self.assertEqual(result["answer_mode"], "strong")
                    self.assertEqual(result["failure_type"], "none")
                    self.assertTrue(expected["formula_ids"].issubset(set(result["matched_formula_ids"])))
                    self.assertTrue(expected["primary_ids"].issubset(set(result["primary_ids"])))
                    self.assertEqual(result["citation_judgement"], "pass: citation slots match answer mode")

        for mode, result in self.modes_for("干呕是什么意思？").items():
            with self.subTest(query="干呕是什么意思？", mode=mode):
                self.assertTrue(result["pass"])
                self.assertEqual(result["answer_mode"], "weak_with_review_notice")
                self.assertEqual(result["failure_type"], "none")
                self.assertEqual(result["primary_ids"], [])
                self.assertEqual(result["matched_definition_concept_ids"], [])
                self.assertEqual((result["term_normalization"] or {}).get("type"), "none")
                self.assertIn("safe:main_passages:ZJSHL-CH-014-P-0188", result["secondary_ids"])
                self.assertIn("safe:main_passages:ZJSHL-CH-015-P-0324", result["secondary_ids"])
                self.assertIn("safe:main_passages:ZJSHL-CH-008-P-0215", result["secondary_ids"])
                self.assertEqual(result["llm_answer_source"], "baseline_p1_conservative_learner_guard")

    def test_p0_original_guards_still_pass(self) -> None:
        p0_queries = {
            "清邪中上是什么意思？": "weak_with_review_notice",
            "反是什么意思？": "weak_with_review_notice",
            "两阳是什么意思？": "weak_with_review_notice",
            "白虎是什么意思？": "refuse",
        }
        for query, expected_mode in p0_queries.items():
            for mode, result in self.modes_for(query).items():
                with self.subTest(query=query, mode=mode):
                    self.assertTrue(result["pass"])
                    self.assertEqual(result["answer_mode"], expected_mode)
                    self.assertEqual(result["primary_ids"], [])
                    self.assertEqual(result["matched_definition_concept_ids"], [])

    def test_white_tiger_formula_queries_remain_usable(self) -> None:
        expectations = {
            "白虎汤方的条文是什么？": {self.formula_id("白虎汤")},
            "白虎加人参汤方的条文是什么？": {self.formula_id("白虎加人参汤")},
            "白虎汤和白虎加人参汤有什么区别？": {
                self.formula_id("白虎汤"),
                self.formula_id("白虎加人参汤"),
            },
        }
        for query, expected_ids in expectations.items():
            for mode, result in self.modes_for(query).items():
                with self.subTest(query=query, mode=mode):
                    self.assertTrue(result["pass"])
                    self.assertEqual(result["answer_mode"], "strong")
                    self.assertTrue(result["primary_ids"])
                    self.assertTrue(expected_ids.issubset(set(result["matched_formula_ids"])))

    def test_ahv_v1_and_ahv2_exact_normalization_do_not_regress(self) -> None:
        expectations = {
            "何谓太阳病": self.concept_id("太阳病"),
            "伤寒是什么": self.concept_id("伤寒"),
            "少阴病是什么意思": self.concept_id("少阴病"),
            "半表半里证是什么": self.concept_id("半表半里证"),
        }
        for query, expected_id in expectations.items():
            for mode, result in self.modes_for(query).items():
                with self.subTest(query=query, mode=mode):
                    self.assertTrue(result["pass"])
                    self.assertIn(expected_id, result["expected_concept_ids"])
                    self.assertIn(expected_id, result["matched_definition_concept_ids"])
                    matches = (result["term_normalization"] or {}).get("matches") or []
                    self.assertTrue(matches, query)
                    self.assertTrue(any(match.get("match_mode") == "exact" for match in matches), query)

    def test_no_new_ahv3_or_active_contains_or_single_char_aliases(self) -> None:
        ahv3_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM definition_term_registry
            WHERE concept_id LIKE 'AHV3-%'
               OR promotion_source_layer LIKE '%ahv3%'
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

        p1_contains_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE is_active = 1
              AND match_mode = 'contains'
              AND source LIKE '%full_chain_p1%'
            """
        ).fetchone()[0]
        self.assertEqual(p1_contains_count, 0)

        single_char_alias_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM term_alias_registry
            WHERE is_active = 1
              AND length(normalized_alias) = 1
            """
        ).fetchone()[0]
        self.assertEqual(single_char_alias_count, 0)

        single_char_learner_surface_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE is_active = 1
              AND length(normalized_surface_form) = 1
            """
        ).fetchone()[0]
        self.assertEqual(single_char_learner_surface_count, 0)

    def test_review_only_and_raw_materials_stay_out_of_primary(self) -> None:
        for record in self.regression["records"]:
            with self.subTest(query=record["query"], mode=record["run_mode"]):
                self.assertFalse(record["forbidden_primary_items"])
                self.assertFalse(record["review_only_primary_conflicts"])
                for record_id in record.get("primary_ids") or []:
                    self.assertFalse(str(record_id).startswith("full:passages:"))
                    self.assertFalse(str(record_id).startswith("full:ambiguous_passages:"))
                for record_type in record.get("primary_record_types") or []:
                    self.assertNotIn(record_type, FORBIDDEN_PRIMARY_TYPES)

        for query in ("神丹是什么意思？", "将军是什么意思？", "胆瘅是什么意思？"):
            for mode, result in self.modes_for(query).items():
                with self.subTest(query=query, mode=mode):
                    self.assertTrue(result["pass"])
                    self.assertNotEqual(result["answer_mode"], "strong")
                    self.assertEqual(result["primary_ids"], [])
                    self.assertEqual(result["matched_definition_concept_ids"], [])


if __name__ == "__main__":
    unittest.main()
