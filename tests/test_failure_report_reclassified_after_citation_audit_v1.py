import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "reclassify_failure_report_after_citation_audit_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "failure_report_reclassified_after_citation_audit_v1"
RESULT_JSON = ARTIFACT_DIR / "failure_cases_reclassified_v1.json"
RESULT_MD = ARTIFACT_DIR / "failure_cases_reclassified_v1.md"
NEXT_QUEUE_JSON = ARTIFACT_DIR / "next_repair_queue_after_citation_audit_v1.json"

DATASET = ROOT / "data" / "eval" / "eval_dataset_v1.csv"
RETRIEVAL_JSON = ROOT / "artifacts" / "eval" / "retrieval_eval_v1" / "retrieval_eval_v1.json"
ANSWER_JSON = ROOT / "artifacts" / "eval" / "answer_eval_v1" / "answer_eval_v1.json"
FAILURE_JSON = ROOT / "artifacts" / "eval" / "failure_report_v1" / "failure_cases_v1.json"
CITATION_AUDIT_JSON = (
    ROOT
    / "artifacts"
    / "eval"
    / "citation_topk_mismatch_audit_v1"
    / "citation_topk_mismatch_audit_v1.json"
)

REAL_CITATION_IDS = {"eval_023", "eval_025", "eval_027"}
TRACE_EQUIVALENCE_IDS = {"eval_002", "eval_009"}
SECONDARY_REVIEW_POLICY_IDS = {
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
P2_IDS = {"eval_011", "eval_012", "eval_013", "eval_014", "eval_015"}

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
    "/api/v1/",
    "full_chain",
    "AHV3",
    "match_mode = 'contains'",
    "single_char",
    "active contains",
    "active 单字 alias",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class FailureReportReclassifiedAfterCitationAuditV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
        cls.examples = cls.payload["per_example"]
        cls.examples_by_id = {row["id"]: row for row in cls.examples}
        cls.next_queue = json.loads(NEXT_QUEUE_JSON.read_text(encoding="utf-8"))
        cls.md_text = RESULT_MD.read_text(encoding="utf-8")
        cls.script_text = SCRIPT.read_text(encoding="utf-8")

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(RESULT_JSON.exists())
        self.assertIsInstance(self.payload, dict)
        self.assertTrue(RESULT_MD.exists())
        self.assertTrue(NEXT_QUEUE_JSON.exists())
        self.assertIsInstance(self.next_queue, dict)

    def test_top_level_counts_match_current_audit_inputs(self) -> None:
        self.assertEqual(self.payload["run_id"], "failure_report_reclassified_after_citation_audit_v1")
        self.assertEqual(self.payload["total_examples"], 36)
        self.assertEqual(len(self.examples), 36)
        self.assertEqual(self.payload["original_formal_fail_count"], 17)
        self.assertEqual(
            self.payload["source_metric_summary"]["citation_topk_mismatch_audit_v1"][
                "total_citation_not_from_topk"
            ],
            14,
        )
        self.assertEqual(self.payload["runtime_bug_count"], 3)

    def test_real_citation_assembly_issues_enter_runtime_queue(self) -> None:
        runtime_ids = {row["id"] for row in self.next_queue["runtime_citation_scope_repairs"]}
        self.assertEqual(runtime_ids, REAL_CITATION_IDS)
        for row_id in REAL_CITATION_IDS:
            row = self.examples_by_id[row_id]
            self.assertEqual(row["citation_audit_root_cause"], "real_citation_assembly_issue")
            self.assertIn("real_citation_assembly_issue", row["reclassified_failure_types"])
            self.assertTrue(row["is_runtime_bug"])
            self.assertEqual(row["recommended_next_action"], "fix_answer_assembly_citation_scope")

    def test_trace_equivalence_rows_enter_tooling_queue(self) -> None:
        trace_ids = {row["id"] for row in self.next_queue["trace_or_evaluator_repairs"]}
        self.assertEqual(trace_ids, TRACE_EQUIVALENCE_IDS)
        for row_id in TRACE_EQUIVALENCE_IDS:
            row = self.examples_by_id[row_id]
            self.assertEqual(row["citation_audit_root_cause"], "trace_topk_missing_equivalence")
            self.assertEqual(row["reclassified_primary_failure_type"], "trace_or_evaluator_equivalence_gap")
            self.assertEqual(row["reclassified_severity"], "tooling")
            self.assertFalse(row["is_runtime_bug"])

    def test_secondary_review_rows_enter_policy_decision_queue(self) -> None:
        policy_ids = {row["id"] for row in self.next_queue["secondary_review_policy_decisions"]}
        self.assertEqual(policy_ids, SECONDARY_REVIEW_POLICY_IDS)
        self.assertEqual(self.payload["policy_warning_count"], 9)
        for row_id in SECONDARY_REVIEW_POLICY_IDS:
            row = self.examples_by_id[row_id]
            self.assertEqual(
                row["citation_audit_root_cause"],
                "answer_uses_secondary_or_review_not_in_topk",
            )
            self.assertIn(
                "secondary_review_citation_policy_needs_decision",
                row["reclassified_failure_types"],
            )
            self.assertFalse(row["is_runtime_bug"])

    def test_p2_residuals_remain_diagnostic_and_out_of_runtime_queue(self) -> None:
        p2_queue_ids = {row["id"] for row in self.next_queue["p2_manual_audit"]}
        runtime_ids = {row["id"] for row in self.next_queue["runtime_citation_scope_repairs"]}
        self.assertEqual(p2_queue_ids, P2_IDS)
        self.assertFalse(p2_queue_ids & runtime_ids)
        for row_id in P2_IDS:
            row = self.examples_by_id[row_id]
            self.assertTrue(row["manual_audit_required"])
            self.assertEqual(row["reclassified_severity"], "diagnostic")
            self.assertEqual(row["reclassified_primary_failure_type"], "manual_audit_required")
            self.assertEqual(row["recommended_next_action"], "manual_audit_required")

    def test_unanswerable_refusals_do_not_gain_out_of_scope_failures(self) -> None:
        unanswerable = [row for row in self.examples if row["should_answer"] is False]
        self.assertEqual(len(unanswerable), 6)
        for row in unanswerable:
            self.assertTrue(row["refuse_when_should_not_answer"])
            self.assertEqual(row["reclassified_severity"], "ok")
            self.assertNotIn("out_of_scope_not_rejected", row["reclassified_failure_types"])

    def test_source_inputs_were_not_rewritten_after_reclassification(self) -> None:
        expected = {
            "eval_dataset_v1": DATASET,
            "retrieval_eval_v1": RETRIEVAL_JSON,
            "answer_eval_v1": ANSWER_JSON,
            "failure_report_v1": FAILURE_JSON,
            "citation_topk_mismatch_audit_v1": CITATION_AUDIT_JSON,
        }
        for key, path in expected.items():
            self.assertTrue(path.exists())
            self.assertEqual(self.payload["source_sha256"][key], sha256_file(path))

    def test_no_runtime_repair_paths_or_forbidden_changes_in_script(self) -> None:
        self.assertTrue(self.payload["report_scope"]["source_artifacts_only"])
        self.assertFalse(self.payload["report_scope"]["runs_retrieval"])
        self.assertFalse(self.payload["report_scope"]["runs_answer_generation"])
        self.assertFalse(self.payload["report_scope"]["llm_judge"])
        self.assertFalse(self.payload["report_scope"]["modifies_runtime"])
        self.assertEqual(
            self.payload["judge"],
            {"type": "rules_only_artifact_reclassification", "llm_judge": False},
        )
        for forbidden in FORBIDDEN_SCRIPT_TEXT:
            self.assertNotIn(forbidden, self.script_text)

    def test_markdown_has_required_sections_and_no_clean_pass_claim(self) -> None:
        for heading in (
            "## 总览",
            "## 原 failure_report_v1 计数",
            "## citation audit 计数",
            "## 重分类后的计数",
            "## 真 runtime citation bug 列表",
            "## trace / evaluator 问题列表",
            "## secondary / review citation policy 问题列表",
            "## retrieval / chunking 仍需修复的问题列表",
            "## P2 diagnostic-only 列表",
            "## 下一步建议",
        ):
            self.assertIn(heading, self.md_text)

        json_text = json.dumps(self.payload, ensure_ascii=False)
        for phrase in FORBIDDEN_REPORT_CLAIMS:
            self.assertNotIn(phrase, self.md_text)
            self.assertNotIn(phrase, json_text)


if __name__ == "__main__":
    unittest.main()
