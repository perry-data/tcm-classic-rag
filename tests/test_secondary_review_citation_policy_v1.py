import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "apply_secondary_review_citation_policy_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "secondary_review_citation_policy_v1"
SUMMARY_JSON = ARTIFACT_DIR / "secondary_review_citation_policy_v1.json"
CASES_JSON = ARTIFACT_DIR / "secondary_review_policy_cases_v1.json"
POLICY_MD = ROOT / "docs" / "eval" / "secondary_review_citation_policy_v1.md"

RECLASSIFIED_JSON = (
    ROOT
    / "artifacts"
    / "eval"
    / "failure_report_reclassified_after_citation_audit_v1"
    / "failure_cases_reclassified_v1.json"
)
NEXT_QUEUE_JSON = (
    ROOT
    / "artifacts"
    / "eval"
    / "failure_report_reclassified_after_citation_audit_v1"
    / "next_repair_queue_after_citation_audit_v1.json"
)
ANSWER_JSON = ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
DATASET = ROOT / "data" / "eval" / "eval_dataset_v1.csv"

ALLOWED_POLICY_STATUSES = {
    "policy_accepted",
    "policy_needs_trace_improvement",
    "policy_violation",
    "manual_audit_required",
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
    "scripts/full_chain",
    "AHV3",
    "active contains",
    "active 单字 alias",
    "single_char",
)

REQUIRED_MARKDOWN_PHRASES = (
    "weak answer 可以引用 secondary/review，但必须带保守语气和可追踪证据槽",
    "strong answer 不允许引用 secondary/review 作为主引用",
    "这不是系统全通过",
    "这不是修 P2",
    "这不是 prompt 修改",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ids(rows: list[dict]) -> set[str]:
    return {str(row.get("id") or "") for row in rows if row.get("id")}


class SecondaryReviewCitationPolicyV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        cls.cases = json.loads(CASES_JSON.read_text(encoding="utf-8"))
        cls.case_ids = ids(cls.cases)
        cls.next_queue = json.loads(NEXT_QUEUE_JSON.read_text(encoding="utf-8"))
        cls.md_text = POLICY_MD.read_text(encoding="utf-8")
        cls.script_text = SCRIPT.read_text(encoding="utf-8")

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(SUMMARY_JSON.exists())
        self.assertIsInstance(self.summary, dict)
        self.assertTrue(CASES_JSON.exists())
        self.assertIsInstance(self.cases, list)
        self.assertTrue(POLICY_MD.exists())

    def test_summary_counts_are_computed_from_cases(self) -> None:
        status_counts = {
            status: sum(1 for case in self.cases if case["policy_status"] == status)
            for status in ALLOWED_POLICY_STATUSES
        }
        self.assertEqual(self.summary["run_id"], "secondary_review_citation_policy_v1")
        self.assertEqual(self.summary["policy_version"], "v1")
        self.assertEqual(self.summary["total_policy_decision_cases"], 9)
        self.assertEqual(self.summary["total_policy_decision_cases"], len(self.cases))
        self.assertEqual(self.summary["policy_accepted_count"], status_counts["policy_accepted"])
        self.assertEqual(
            self.summary["policy_needs_trace_improvement_count"],
            status_counts["policy_needs_trace_improvement"],
        )
        self.assertEqual(self.summary["policy_violation_count"], status_counts["policy_violation"])
        self.assertEqual(
            self.summary["manual_audit_required_count"],
            status_counts["manual_audit_required"],
        )
        self.assertTrue(self.summary["weak_secondary_review_allowed"])

    def test_each_case_has_valid_policy_status_and_strong_boundary(self) -> None:
        for case in self.cases:
            self.assertIn("policy_status", case)
            self.assertIn(case["policy_status"], ALLOWED_POLICY_STATUSES)
            if case["answer_mode"] == "strong":
                self.assertEqual(case["policy_status"], "policy_violation")

    def test_policy_cases_only_come_from_secondary_review_queue(self) -> None:
        policy_queue_ids = ids(self.next_queue["secondary_review_policy_decisions"])
        self.assertEqual(self.case_ids, policy_queue_ids)
        for case in self.cases:
            self.assertEqual(case["source_queue"], "secondary_review_policy_decisions")

    def test_excluded_repair_queues_do_not_enter_policy_cases(self) -> None:
        p2_ids = ids(self.next_queue["p2_manual_audit"])
        runtime_ids = ids(self.next_queue["runtime_citation_scope_repairs"])
        trace_ids = ids(self.next_queue["trace_or_evaluator_repairs"])
        self.assertFalse(self.case_ids & p2_ids)
        self.assertFalse(self.case_ids & runtime_ids)
        self.assertFalse(self.case_ids & trace_ids)
        self.assertEqual(
            self.summary["policy_cases_also_in_retrieval_or_chunking_repairs"],
            ["eval_026"],
        )

    def test_source_inputs_were_not_rewritten_by_policy_run(self) -> None:
        expected_sources = {
            "failure_cases_reclassified_v1": RECLASSIFIED_JSON,
            "next_repair_queue_after_citation_audit_v1": NEXT_QUEUE_JSON,
            "answer_eval_v1": ANSWER_JSON,
        }
        for key, path in expected_sources.items():
            self.assertEqual(self.summary["source_sha256"][key], sha256_file(path))
        self.assertEqual(
            self.summary["guarded_non_input_sha256"]["eval_dataset_v1"],
            sha256_file(DATASET),
        )

    def test_no_runtime_prompt_frontend_api_or_new_data_rules(self) -> None:
        self.assertFalse(self.summary["runtime_changed"])
        self.assertFalse(self.summary["prompt_changed"])
        self.assertFalse(self.summary["api_changed"])
        self.assertFalse(self.summary["frontend_changed"])
        self.assertFalse(self.summary["dataset_changed"])
        self.assertFalse(self.summary["existing_evaluator_changed"])
        self.assertFalse(self.summary["report_scope"]["runs_retrieval"])
        self.assertFalse(self.summary["report_scope"]["runs_answer_generation"])
        self.assertFalse(self.summary["report_scope"]["runs_answer_assembly"])
        self.assertFalse(self.summary["judge"]["llm_judge"])
        for forbidden in FORBIDDEN_SCRIPT_TEXT:
            self.assertNotIn(forbidden, self.script_text)

    def test_markdown_documents_required_policy_boundaries(self) -> None:
        for heading in (
            "## 本轮目标",
            "## 为什么要定义 secondary/review citation policy",
            "## answer_mode citation 规则",
            "## 9 条 policy decision 逐条表格",
            "## policy_accepted",
            "## policy_needs_trace_improvement",
            "## policy_violation",
            "## manual_audit_required",
            "## 为什么本轮不修 runtime",
            "## 下一步建议",
        ):
            self.assertIn(heading, self.md_text)
        for phrase in REQUIRED_MARKDOWN_PHRASES:
            self.assertIn(phrase, self.md_text)


if __name__ == "__main__":
    unittest.main()
