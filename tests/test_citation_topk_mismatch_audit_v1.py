import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "audit_citation_topk_mismatch_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "citation_topk_mismatch_audit_v1"
RESULT_JSON = ARTIFACT_DIR / "citation_topk_mismatch_audit_v1.json"
RESULT_MD = ARTIFACT_DIR / "citation_topk_mismatch_audit_v1.md"

DATASET = ROOT / "data" / "eval" / "eval_dataset_v1.csv"
RETRIEVAL_JSON = ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
ANSWER_JSON = ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
TRACE_JSONL = ROOT / "artifacts" / "eval" / "answer_eval_v1" / "qa_trace_answer_eval_v1.jsonl"
FAILURE_JSON = ROOT / "artifacts" / "eval" / "failure_report_v1" / "failure_cases_v1.json"

ALLOWED_ROOT_CAUSES = {
    "trace_topk_missing_equivalence",
    "formula_or_definition_source_expansion",
    "answer_uses_secondary_or_review_not_in_topk",
    "trace_logging_gap",
    "evaluator_id_equivalence_gap",
    "real_citation_assembly_issue",
    "manual_audit_required",
}

ALLOWED_ACTIONS = {
    "fix_trace_logging",
    "fix_evaluator_id_equivalence",
    "allow_formula_source_expansion_in_eval",
    "inspect_secondary_review_citation_policy",
    "fix_answer_assembly_citation_scope",
    "manual_audit_required",
    "none",
}

FORBIDDEN_SCRIPT_TEXT = (
    "backend.answers",
    "backend.llm",
    "AnswerAssembler",
    "LLMJudge",
    "judge_llm",
    "build_answer_text_prompt",
    "frontend/",
    "/api/v1/",
    "AHV3",
    "match_mode = 'contains'",
    "single_char",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CitationTopkMismatchAuditV1Tests(unittest.TestCase):
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

    def test_audits_only_citation_not_from_topk_rows(self) -> None:
        self.assertEqual(self.payload["run_id"], "citation_topk_mismatch_audit_v1")
        self.assertEqual(self.payload["source_failure_report"], "artifacts/eval/failure_report_v1/failure_cases_v1.json")
        self.assertEqual(self.payload["total_citation_not_from_topk"], 14)
        self.assertEqual(len(self.examples), 14)
        for row in self.examples:
            self.assertNotEqual(row.get("root_cause"), "manual_audit_required")
            self.assertNotEqual(row.get("category"), "超范围拒答")

    def test_each_example_has_root_cause_action_and_boolean_runtime_flag(self) -> None:
        for row in self.examples:
            self.assertIn(row["root_cause"], ALLOWED_ROOT_CAUSES)
            self.assertIn(row["recommended_next_action"], ALLOWED_ACTIONS)
            self.assertIsInstance(row["is_runtime_bug"], bool)
            self.assertTrue(row["citation_ids"])
            self.assertIsInstance(row["matched_by_existing_equivalence"], list)
            self.assertIsInstance(row["unmatched_citation_ids"], list)
            self.assertIsInstance(row["trace_top_k_record_ids"], list)
            self.assertIsInstance(row["retrieval_top5_record_ids"], list)
            self.assertIsInstance(row["gold_chunk_ids"], list)

    def test_summary_counts_are_consistent(self) -> None:
        root_counts = self.payload["root_cause_counts"]
        action_counts = self.payload["recommended_next_action_counts"]
        self.assertEqual(sum(root_counts.values()), 14)
        self.assertEqual(sum(action_counts.values()), 14)
        self.assertEqual(self.payload["runtime_bug_count"], 3)
        self.assertEqual(self.payload["evaluator_or_trace_issue_count"], 2)
        self.assertEqual(self.payload["manual_audit_required_count"], 0)
        self.assertEqual(root_counts["trace_topk_missing_equivalence"], 2)
        self.assertEqual(root_counts["answer_uses_secondary_or_review_not_in_topk"], 9)
        self.assertEqual(root_counts["real_citation_assembly_issue"], 3)

    def test_markdown_contains_required_sections(self) -> None:
        for heading in (
            "## 总览",
            "## root_cause_counts",
            "## 每条 citation_not_from_top_k 审计表",
            "## 哪些应修 trace",
            "## 哪些应修 evaluator id equivalence",
            "## 哪些可能是真 answer assembly bug",
            "## 下一轮建议",
        ):
            self.assertIn(heading, self.md_text)

    def test_source_inputs_were_not_rewritten_after_audit_generation(self) -> None:
        expected = {
            "eval_dataset_v1": DATASET,
            "retrieval_eval_v1": RETRIEVAL_JSON,
            "answer_eval_v1": ANSWER_JSON,
            "qa_trace_answer_eval_v1": TRACE_JSONL,
            "failure_report_v1": FAILURE_JSON,
        }
        for key, path in expected.items():
            self.assertTrue(path.exists())
            self.assertEqual(self.payload["source_sha256"][key], sha256_file(path))

    def test_no_runtime_repair_or_forbidden_paths_in_audit_script(self) -> None:
        self.assertFalse(self.payload["audit_scope"]["runs_retrieval"])
        self.assertFalse(self.payload["audit_scope"]["runs_answer_generation"])
        self.assertFalse(self.payload["audit_scope"]["llm_judge"])
        self.assertFalse(self.payload["audit_scope"]["includes_p2_diagnostic"])
        for forbidden in FORBIDDEN_SCRIPT_TEXT:
            self.assertNotIn(forbidden, self.script_text)


if __name__ == "__main__":
    unittest.main()
