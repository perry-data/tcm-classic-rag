import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "build_policy_integrated_diagnostic_summary_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "eval_diagnostic_loop_policy_integrated_v1"
SUMMARY_JSON = ARTIFACT_DIR / "eval_diagnostic_loop_policy_integrated_summary_v1.json"
SUMMARY_MD = ARTIFACT_DIR / "eval_diagnostic_loop_policy_integrated_summary_v1.md"
NEXT_QUEUE_JSON = ARTIFACT_DIR / "next_repair_queue_policy_integrated_v1.json"

RUNTIME_CITATION_IDS = {"eval_023", "eval_025", "eval_027"}
TRACE_OR_EVALUATOR_IDS = {"eval_002", "eval_009"}
P2_MANUAL_AUDIT_IDS = {"eval_011", "eval_012", "eval_013", "eval_014", "eval_015"}
POLICY_ACCEPTED_IDS = {
    "eval_006",
    "eval_010",
    "eval_016",
    "eval_017",
    "eval_018",
    "eval_022",
    "eval_024",
    "eval_026",
    "eval_030",
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
    "full_chain",
    "AHV3",
    "active contains",
    "active 单字 alias",
    "single_char",
)


def ids(rows: list[dict]) -> set[str]:
    return {str(row.get("id") or "") for row in rows if row.get("id")}


class EvalDiagnosticLoopPolicyIntegratedV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        cls.next_queue = json.loads(NEXT_QUEUE_JSON.read_text(encoding="utf-8"))
        cls.md_text = SUMMARY_MD.read_text(encoding="utf-8")
        cls.script_text = SCRIPT.read_text(encoding="utf-8")

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(SUMMARY_JSON.exists())
        self.assertIsInstance(self.summary, dict)
        self.assertTrue(SUMMARY_MD.exists())
        self.assertTrue(NEXT_QUEUE_JSON.exists())
        self.assertIsInstance(self.next_queue, dict)

    def test_summary_counts_match_policy_integrated_scope(self) -> None:
        self.assertEqual(self.summary["run_id"], "eval_diagnostic_loop_policy_integrated_v1")
        self.assertEqual(self.summary["total_examples"], 36)
        self.assertEqual(self.summary["original_failure_report_formal_fail_count"], 17)
        self.assertEqual(self.summary["reclassified_formal_fail_count_before_policy"], 7)
        self.assertEqual(self.summary["secondary_review_policy_decision_count"], 9)
        self.assertEqual(self.summary["secondary_review_policy_accepted_count"], 9)
        self.assertEqual(self.summary["secondary_review_policy_violation_count"], 0)
        self.assertEqual(self.summary["secondary_review_policy_needs_trace_improvement_count"], 0)
        self.assertEqual(self.summary["policy_integrated_runtime_bug_count"], 3)
        self.assertEqual(self.summary["policy_integrated_tooling_issue_count"], 2)
        self.assertEqual(self.summary["policy_integrated_policy_blocking_count"], 0)
        self.assertEqual(self.summary["policy_integrated_diagnostic_count"], 5)
        self.assertFalse(self.summary["system_all_passed"])

    def test_next_queue_keeps_runtime_trace_policy_and_p2_boundaries(self) -> None:
        runtime_ids = ids(self.next_queue["runtime_citation_scope_repairs"])
        trace_ids = ids(self.next_queue["trace_or_evaluator_repairs"])
        policy_ids = ids(self.next_queue["policy_accepted_no_runtime_repair"])
        p2_ids = ids(self.next_queue["p2_manual_audit"])

        self.assertEqual(runtime_ids, RUNTIME_CITATION_IDS)
        self.assertEqual(trace_ids, TRACE_OR_EVALUATOR_IDS)
        self.assertEqual(policy_ids, POLICY_ACCEPTED_IDS)
        self.assertEqual(p2_ids, P2_MANUAL_AUDIT_IDS)
        self.assertEqual(len(self.next_queue["policy_accepted_no_runtime_repair"]), 9)
        self.assertEqual(len(self.next_queue["p2_manual_audit"]), 5)
        self.assertFalse(policy_ids & runtime_ids)

    def test_eval_026_policy_acceptance_does_not_remove_retrieval_identity(self) -> None:
        retrieval_rows = self.next_queue["retrieval_or_chunking_repairs"]
        retrieval_ids = ids(retrieval_rows)
        self.assertIn("eval_026", retrieval_ids)
        eval_026 = next(row for row in retrieval_rows if row["id"] == "eval_026")
        self.assertEqual(eval_026["recommended_next_action"], "fix_retrieval_or_chunking")
        self.assertIn(
            "policy accepted 只解决 secondary/review citation policy",
            eval_026["notes"],
        )
        self.assertIn("不代表 retrieval/chunking 已修", eval_026["notes"])

    def test_summary_id_lists_match_next_queue(self) -> None:
        self.assertEqual(set(self.summary["runtime_citation_bug_ids"]), RUNTIME_CITATION_IDS)
        self.assertEqual(set(self.summary["trace_or_evaluator_issue_ids"]), TRACE_OR_EVALUATOR_IDS)
        self.assertEqual(set(self.summary["policy_accepted_ids"]), POLICY_ACCEPTED_IDS)
        self.assertEqual(set(self.summary["p2_manual_audit_ids"]), P2_MANUAL_AUDIT_IDS)
        self.assertIn("eval_026", self.summary["retrieval_or_chunking_repair_ids"])
        self.assertEqual(
            self.summary["policy_cases_also_in_retrieval_or_chunking_repairs"],
            ["eval_026"],
        )

    def test_markdown_documents_required_boundaries_without_clean_pass_claim(self) -> None:
        for heading in (
            "## 本轮目标",
            "## 输入 artifacts",
            "## 旧 reclassified summary",
            "## secondary_review_citation_policy_v1 结果",
            "## policy-integrated 后的真实待办队列",
            "## 9 条 policy accepted 列表",
            "## 3 条 runtime citation bug 列表",
            "## 2 条 trace/evaluator issue 列表",
            "## retrieval/chunking repair 列表",
            "## 5 条 P2 manual audit 列表",
            "## 下一步建议",
        ):
            self.assertIn(heading, self.md_text)
        for phrase in (
            "这不是系统全通过",
            "9 条 secondary/review policy warning 已被 policy 接受",
            "policy accepted 不等于所有相关样本都没有别的问题",
            "eval_026 policy accepted，但仍保留 retrieval/chunking repair 观察",
            "本轮不修 runtime、不改 prompt、不改 API",
        ):
            self.assertIn(phrase, self.md_text)
        self.assertNotIn("全部通过", self.md_text)
        self.assertNotIn("all passed", self.md_text.lower())

    def test_no_runtime_prompt_frontend_api_or_data_rule_changes(self) -> None:
        self.assertFalse(self.summary["runtime_changed"])
        self.assertFalse(self.summary["prompt_changed"])
        self.assertFalse(self.summary["api_changed"])
        self.assertFalse(self.summary["frontend_changed"])
        self.assertFalse(self.summary["dataset_changed"])
        self.assertFalse(self.summary["existing_evaluator_changed"])
        self.assertTrue(self.summary["report_scope"]["source_artifacts_only"])
        self.assertFalse(self.summary["report_scope"]["runs_retrieval"])
        self.assertFalse(self.summary["report_scope"]["runs_answer_generation"])
        self.assertFalse(self.summary["report_scope"]["runs_answer_assembly"])
        self.assertFalse(self.summary["report_scope"]["modifies_runtime"])
        self.assertFalse(self.summary["judge"]["llm_judge"])
        for forbidden in FORBIDDEN_SCRIPT_TEXT:
            self.assertNotIn(forbidden, self.script_text)


if __name__ == "__main__":
    unittest.main()
