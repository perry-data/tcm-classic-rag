import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "retrieval_eval_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "retrieval_eval_v1"
RESULT_JSON = ARTIFACT_DIR / "retrieval_eval_v1.json"
RESULT_MD = ARTIFACT_DIR / "retrieval_eval_v1.md"

P2_QUERIES = {
    "少阴病是什么意思",
    "半表半里证和过经有什么不同",
    "荣气微和卫气衰有什么区别",
    "霍乱和伤寒有什么区别",
    "痓病和太阳病有什么不同",
}


class RetrievalEvalV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
        cls.examples = cls.payload["per_example"]

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(RESULT_JSON.exists())
        self.assertIsInstance(self.payload, dict)
        self.assertTrue(RESULT_MD.exists())

    def test_dataset_partition_counts(self) -> None:
        self.assertEqual(self.payload["total_examples"], 36)
        self.assertEqual(self.payload["answerable_metric_examples"], 25)
        self.assertEqual(self.payload["diagnostic_only_examples"], 5)
        self.assertEqual(self.payload["unanswerable_examples"], 6)
        self.assertEqual(len(self.examples), 36)

    def test_metric_fields_exist_and_are_bounded(self) -> None:
        for field in ["hit_at_1", "hit_at_3", "hit_at_5", "mrr", "recall_at_5"]:
            self.assertIn(field, self.payload)
            self.assertGreaterEqual(self.payload[field], 0.0)
            self.assertLessEqual(self.payload[field], 1.0)

    def test_p2_residuals_are_diagnostic_only(self) -> None:
        p2_rows = [row for row in self.examples if row["question"] in P2_QUERIES]
        self.assertEqual(len(p2_rows), 5)
        for row in p2_rows:
            self.assertTrue(row["manual_audit_required"])
            self.assertEqual(row["gold_chunk_ids"], [])
            self.assertFalse(row["included_in_metrics"])
            self.assertTrue(row["diagnostic_only"])
            self.assertEqual(row["example_class"], "diagnostic_only")

    def test_unanswerable_examples_are_not_metric_examples(self) -> None:
        unanswerable = [row for row in self.examples if row["should_answer"] is False]
        self.assertEqual(len(unanswerable), 6)
        for row in unanswerable:
            self.assertFalse(row["included_in_metrics"])
            self.assertEqual(row["example_class"], "unanswerable")

    def test_manual_audit_rows_are_not_counted_as_retrieval_failures(self) -> None:
        manual_rows = [row for row in self.examples if row["manual_audit_required"] is True]
        self.assertEqual(len(manual_rows), 5)
        self.assertTrue(all(not row["included_in_metrics"] for row in manual_rows))
        self.assertEqual(self.payload["answerable_metric_examples"], 25)

    def test_formula_exact_and_weak_boundary_have_retrieval_top5(self) -> None:
        formula_exact_rows = [row for row in self.examples if row["subtype"] == "formula_exact"]
        weak_boundary_rows = [row for row in self.examples if row["subtype"] == "weak_boundary"]
        self.assertTrue(any(row["top5_record_ids"] for row in formula_exact_rows))
        self.assertTrue(any(row["top5_record_ids"] for row in weak_boundary_rows))

    def test_no_llm_path_used(self) -> None:
        self.assertFalse(self.payload["llm_used"])
        self.assertEqual(self.payload["env_flags"]["PERF_DISABLE_LLM"], "1")
        script_text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("backend.answers", script_text)
        self.assertNotIn("backend.llm", script_text)
        self.assertNotIn("AnswerAssembler", script_text)
        self.assertNotIn(".assemble(", script_text)


if __name__ == "__main__":
    unittest.main()
