import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "build_failure_report_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "failure_report_v1"
RESULT_JSON = ARTIFACT_DIR / "failure_cases_v1.json"
RESULT_MD = ARTIFACT_DIR / "failure_cases_v1.md"

DATASET = ROOT / "data" / "eval" / "eval_dataset_v1.csv"
RETRIEVAL_JSON = ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
ANSWER_JSON = ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"

P2_QUERIES = {
    "少阴病是什么意思",
    "半表半里证和过经有什么不同",
    "荣气微和卫气衰有什么区别",
    "霍乱和伤寒有什么区别",
    "痓病和太阳病有什么不同",
}

FORBIDDEN_REPORT_CLAIMS = (
    "全部通过",
    "all pass",
    "all passed",
)

FORBIDDEN_SCRIPT_TEXT = (
    "backend.answers",
    "backend.llm",
    "AnswerAssembler",
    "LLMJudge",
    "judge_llm",
    "build_answer_text_prompt",
    "frontend/",
    "AHV3",
    "match_mode = 'contains'",
    "single_char",
)


class FailureReportV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
        cls.examples = cls.payload["per_example"]
        cls.md_text = RESULT_MD.read_text(encoding="utf-8")
        cls.script_text = SCRIPT.read_text(encoding="utf-8")

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(RESULT_JSON.exists())
        self.assertIsInstance(self.payload, dict)
        self.assertTrue(RESULT_MD.exists())

    def test_source_inputs_still_exist(self) -> None:
        self.assertTrue(DATASET.exists())
        self.assertTrue(RETRIEVAL_JSON.exists())
        self.assertTrue(ANSWER_JSON.exists())

    def test_dataset_partition_counts(self) -> None:
        self.assertEqual(self.payload["total_examples"], 36)
        self.assertEqual(self.payload["answerable_metric_examples"], 25)
        self.assertEqual(self.payload["diagnostic_only_examples"], 5)
        self.assertEqual(self.payload["unanswerable_examples"], 6)
        self.assertEqual(len(self.examples), 36)

    def test_p2_residuals_are_diagnostic_and_not_formal_failures(self) -> None:
        p2_rows = [row for row in self.examples if row["question"] in P2_QUERIES]
        self.assertEqual(len(p2_rows), 5)
        for row in p2_rows:
            self.assertTrue(row["manual_audit_required"])
            self.assertEqual(row["example_class"], "diagnostic_only")
            self.assertEqual(row["severity"], "diagnostic")
            self.assertEqual(row["primary_failure_type"], "manual_audit_required")
            self.assertEqual(row["recommended_next_action"], "manual_audit_required")

        formal_fail_ids = {row["id"] for row in self.examples if row["severity"] == "fail"}
        self.assertFalse(formal_fail_ids & {row["id"] for row in p2_rows})
        self.assertEqual(
            self.payload["formal_fail_count"],
            sum(1 for row in self.examples if row["severity"] == "fail"),
        )

    def test_unanswerable_refusals_are_not_misclassified_as_failures(self) -> None:
        unanswerable = [row for row in self.examples if row["should_answer"] is False]
        self.assertEqual(len(unanswerable), 6)
        for row in unanswerable:
            self.assertEqual(row["example_class"], "unanswerable")
            self.assertTrue(row["refuse_when_should_not_answer"])
            self.assertNotIn("out_of_scope_not_rejected", row["all_failure_types"])
            self.assertNotEqual(row["severity"], "fail")

    def test_failure_type_counts_keep_diagnostic_signals(self) -> None:
        counts = self.payload["failure_type_counts"]
        self.assertTrue(
            "citation_not_from_top_k" in counts or "scope_qualifier_missing" in counts,
            counts,
        )
        self.assertIn("manual_audit_required", counts)

    def test_non_ok_examples_have_actions_and_all_failure_types(self) -> None:
        for row in self.examples:
            self.assertIsInstance(row["all_failure_types"], list)
            if row["severity"] in {"fail", "warning", "diagnostic"}:
                self.assertTrue(row["all_failure_types"])
                self.assertNotEqual(row["recommended_next_action"], "none")

    def test_json_and_markdown_do_not_claim_clean_pass(self) -> None:
        json_text = json.dumps(self.payload, ensure_ascii=False)
        for phrase in FORBIDDEN_REPORT_CLAIMS:
            self.assertNotIn(phrase, json_text)
            self.assertNotIn(phrase, self.md_text)

    def test_no_llm_or_runtime_repair_paths_in_report_builder(self) -> None:
        self.assertEqual(self.payload["judge"], {"type": "rules_only_artifact_merge", "llm_judge": False})
        for forbidden in FORBIDDEN_SCRIPT_TEXT:
            self.assertNotIn(forbidden, self.script_text)

    def test_report_does_not_replace_source_artifact_paths(self) -> None:
        self.assertEqual(self.payload["dataset_path"], "data/eval/eval_dataset_v1.csv")
        self.assertEqual(
            self.payload["retrieval_eval_source"],
            "artifacts/eval/retrieval_eval_v1/retrieval_eval_v1.json",
        )
        self.assertEqual(
            self.payload["answer_eval_source"],
            "artifacts/eval/answer_eval_v1/answer_eval_v1.json",
        )


if __name__ == "__main__":
    unittest.main()
