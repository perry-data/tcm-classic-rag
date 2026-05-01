import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "answer_eval_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "answer_eval_v1"
RESULT_JSON = ARTIFACT_DIR / "answer_eval_v1.json"
RESULT_MD = ARTIFACT_DIR / "answer_eval_v1.md"
TRACE_JSONL = ARTIFACT_DIR / "qa_trace_answer_eval_v1.jsonl"

P2_QUERIES = {
    "少阴病是什么意思",
    "半表半里证和过经有什么不同",
    "荣气微和卫气衰有什么区别",
    "霍乱和伤寒有什么区别",
    "痓病和太阳病有什么不同",
}
RATE_FIELDS = {
    "has_citation_rate",
    "citation_from_top_k_rate",
    "gold_cited_rate",
    "refuse_when_should_not_answer_rate",
    "scope_qualified_rate",
    "answer_keyword_hit_rate",
    "expected_answer_mode_match_rate",
}
FORBIDDEN_PRIMARY_PREFIXES = (
    "full:passages:",
    "full:ambiguous_passages:",
)


class AnswerEvalV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
        cls.examples = cls.payload["per_example"]
        cls.trace_lines = TRACE_JSONL.read_text(encoding="utf-8").splitlines()
        cls.trace_records = [json.loads(line) for line in cls.trace_lines if line.strip()]

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(RESULT_JSON.exists())
        self.assertIsInstance(self.payload, dict)
        self.assertTrue(RESULT_MD.exists())
        self.assertTrue(TRACE_JSONL.exists())

    def test_trace_jsonl_has_full_dataset_and_is_parseable(self) -> None:
        self.assertGreaterEqual(len(self.trace_records), 36)
        for record in self.trace_records:
            self.assertIsInstance(record, dict)
            self.assertIn("query", record)
            self.assertIn("answer_mode", record)
            self.assertIn("top_k_chunks", record)

    def test_dataset_partition_counts(self) -> None:
        self.assertEqual(self.payload["total_examples"], 36)
        self.assertEqual(self.payload["answerable_metric_examples"], 25)
        self.assertEqual(self.payload["diagnostic_only_examples"], 5)
        self.assertEqual(self.payload["unanswerable_examples"], 6)
        self.assertEqual(len(self.examples), 36)

    def test_p2_residuals_are_diagnostic_only_and_excluded_from_gold_totals(self) -> None:
        p2_rows = [row for row in self.examples if row["question"] in P2_QUERIES]
        self.assertEqual(len(p2_rows), 5)
        for row in p2_rows:
            self.assertTrue(row["manual_audit_required"])
            self.assertTrue(row["diagnostic_only"])
            self.assertFalse(row["included_in_answer_metrics"])
            self.assertIsNone(row["gold_cited"])
            self.assertIsNone(row["answer_keyword_hit"])
        self.assertEqual(self.payload["metric_denominators"]["gold_cited"], 25)
        self.assertEqual(self.payload["metric_denominators"]["answer_keyword_hit"], 25)

    def test_unanswerable_examples_enter_refusal_metric(self) -> None:
        unanswerable = [row for row in self.examples if row["should_answer"] is False]
        self.assertEqual(len(unanswerable), 6)
        for row in unanswerable:
            self.assertEqual(row["example_class"], "unanswerable")
            self.assertIsNotNone(row["refuse_when_should_not_answer"])
            self.assertFalse(row["included_in_answer_metrics"])
        self.assertEqual(self.payload["metric_denominators"]["refuse_when_should_not_answer"], 6)

    def test_rate_fields_exist_and_are_bounded(self) -> None:
        for field in RATE_FIELDS:
            self.assertIn(field, self.payload)
            self.assertGreaterEqual(self.payload[field], 0.0)
            self.assertLessEqual(self.payload[field], 1.0)

    def test_no_llm_used_and_no_llm_judge(self) -> None:
        self.assertFalse(self.payload["llm_used"])
        self.assertEqual(self.payload["env_flags"]["PERF_DISABLE_LLM"], "1")
        self.assertEqual(self.payload["judge"], {"type": "rules_only", "llm_judge": False})
        script_text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("LLMJudge", script_text)
        self.assertNotIn("judge_llm", script_text)
        self.assertNotIn("llm_judge=True", script_text)

    def test_trace_primary_ids_do_not_promote_raw_full_passages(self) -> None:
        for record in self.trace_records:
            for record_id in record.get("primary_evidence_ids") or []:
                self.assertFalse(str(record_id).startswith(FORBIDDEN_PRIMARY_PREFIXES), record)

    def test_no_prompt_frontend_or_data_backdoor_edits_in_answer_eval_script(self) -> None:
        script_text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("build_answer_text_prompt", script_text)
        self.assertNotIn("frontend/", script_text)
        self.assertNotIn("AHV3", script_text)
        self.assertNotIn("match_mode = 'contains'", script_text)
        self.assertNotIn("single_char", script_text)


if __name__ == "__main__":
    unittest.main()
