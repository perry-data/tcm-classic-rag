import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval" / "run_eval_diagnostic_loop_v1.py"
ARTIFACT_DIR = ROOT / "artifacts" / "eval" / "eval_diagnostic_loop_v1"
SUMMARY_JSON = ARTIFACT_DIR / "eval_diagnostic_loop_summary_v1.json"
SUMMARY_MD = ARTIFACT_DIR / "eval_diagnostic_loop_summary_v1.md"

EXPECTED_STEPS = [
    "validate_eval_dataset_v1",
    "retrieval_eval_v1",
    "answer_eval_v1",
    "failure_report_v1",
    "citation_topk_mismatch_audit_v1",
    "failure_report_reclassified_after_citation_audit_v1",
]

RUNTIME_CITATION_IDS = {"eval_023", "eval_025", "eval_027"}
TRACE_OR_EVALUATOR_IDS = {"eval_002", "eval_009"}
P2_IDS = {"eval_011", "eval_012", "eval_013", "eval_014", "eval_015"}

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
    "active contains",
    "single_char",
    "active 单字 alias",
)


def ids(rows: list[dict]) -> set[str]:
    return {str(row.get("id") or "") for row in rows if row.get("id")}


def source_json(payload: dict, name: str) -> dict:
    path = Path(payload["source_artifacts"][name])
    if not path.is_absolute():
        path = ROOT / path
    return json.loads(path.read_text(encoding="utf-8"))


class EvalDiagnosticLoopRunnerV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        cls.md_text = SUMMARY_MD.read_text(encoding="utf-8")
        cls.script_text = SCRIPT.read_text(encoding="utf-8")

    def test_expected_files_exist_and_json_loads(self) -> None:
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(SUMMARY_JSON.exists())
        self.assertIsInstance(self.payload, dict)
        self.assertTrue(SUMMARY_MD.exists())

    def test_steps_all_passed_and_preserve_process_summaries(self) -> None:
        self.assertTrue(self.payload["all_steps_passed"])
        self.assertEqual([step["name"] for step in self.payload["steps"]], EXPECTED_STEPS)
        self.assertGreaterEqual(len(self.payload["steps"]), 6)
        for step in self.payload["steps"]:
            self.assertIn("returncode", step)
            self.assertIn("status", step)
            self.assertEqual(step["returncode"], 0)
            self.assertEqual(step["status"], "pass")
            self.assertIn("stdout_excerpt", step)
            self.assertIn("stderr_excerpt", step)

    def test_summary_values_match_source_artifacts(self) -> None:
        dataset = source_json(self.payload, "eval_dataset_v1")
        retrieval = source_json(self.payload, "retrieval_eval_v1")
        answer = source_json(self.payload, "answer_eval_v1")
        failure = source_json(self.payload, "failure_report_v1")
        citation = source_json(self.payload, "citation_topk_mismatch_audit_v1")
        reclassified = source_json(
            self.payload,
            "failure_report_reclassified_after_citation_audit_v1",
        )

        self.assertEqual(self.payload["dataset"]["total_examples"], dataset["total_examples"])
        self.assertEqual(self.payload["retrieval"]["hit_at_5"], retrieval["hit_at_5"])
        self.assertEqual(
            self.payload["answer"]["expected_answer_mode_match_rate"],
            answer["expected_answer_mode_match_rate"],
        )
        self.assertEqual(
            self.payload["failure_report"]["formal_fail_count"],
            failure["formal_fail_count"],
        )
        self.assertEqual(
            self.payload["citation_audit"]["total_citation_not_from_topk"],
            citation["total_citation_not_from_topk"],
        )
        self.assertEqual(
            self.payload["reclassified"]["reclassified_formal_fail_count"],
            reclassified["reclassified_formal_fail_count"],
        )

    def test_dataset_and_retrieval_counts(self) -> None:
        self.assertEqual(self.payload["dataset"]["total_examples"], 36)
        self.assertTrue(self.payload["dataset"]["dataset_valid"])
        self.assertEqual(self.payload["retrieval"]["answerable_metric_examples"], 25)
        self.assertEqual(self.payload["retrieval"]["diagnostic_only_examples"], 5)
        self.assertEqual(self.payload["retrieval"]["unanswerable_examples"], 6)

    def test_answer_eval_is_no_llm_rules_only(self) -> None:
        self.assertEqual(self.payload["run_mode"], "B_retrieval_rerank_no_llm")
        self.assertTrue(self.payload["no_llm"])
        self.assertFalse(self.payload["answer"]["llm_used"])
        self.assertEqual(self.payload["answer"]["env_flags"]["PERF_DISABLE_LLM"], "1")
        self.assertEqual(self.payload["answer"]["env_flags"]["PERF_DISABLE_RERANK"], "0")
        self.assertEqual(self.payload["answer"]["env_flags"]["PERF_RETRIEVAL_MODE"], "hybrid")
        self.assertFalse(self.payload["judge"]["llm_judge"])
        self.assertEqual(self.payload["answer"]["judge"], {"type": "rules_only", "llm_judge": False})

    def test_failure_audit_and_reclassified_counts(self) -> None:
        self.assertEqual(self.payload["failure_report"]["formal_fail_count"], 17)
        self.assertEqual(self.payload["citation_audit"]["total_citation_not_from_topk"], 14)
        self.assertEqual(self.payload["reclassified"]["original_formal_fail_count"], 17)
        self.assertEqual(self.payload["reclassified"]["reclassified_formal_fail_count"], 7)
        self.assertEqual(self.payload["reclassified"]["runtime_bug_count"], 3)
        self.assertEqual(self.payload["reclassified"]["tooling_count"], 2)
        self.assertEqual(self.payload["reclassified"]["policy_warning_count"], 9)
        self.assertEqual(self.payload["reclassified"]["diagnostic_count"], 5)

    def test_next_repair_queue_preserves_current_diagnostic_split(self) -> None:
        queue = self.payload["next_repair_queue"]
        runtime_ids = ids(queue["runtime_citation_scope_repairs"])
        p2_ids = ids(queue["p2_manual_audit"])
        self.assertEqual(runtime_ids, RUNTIME_CITATION_IDS)
        self.assertEqual(ids(queue["trace_or_evaluator_repairs"]), TRACE_OR_EVALUATOR_IDS)
        self.assertEqual(len(queue["secondary_review_policy_decisions"]), 9)
        self.assertEqual(p2_ids, P2_IDS)
        self.assertEqual(len(queue["p2_manual_audit"]), 5)
        self.assertFalse(runtime_ids & p2_ids)

    def test_markdown_has_required_wording_without_clean_pass_claim(self) -> None:
        for heading in (
            "## 本轮目标",
            "## 各步骤运行状态",
            "## dataset 概况",
            "## retrieval 指标",
            "## answer 指标",
            "## failure_report 原始归因",
            "## citation audit 结论",
            "## reclassified 归因",
            "## next repair queue",
            "## 下一步建议",
        ):
            self.assertIn(heading, self.md_text)
        self.assertIn("这是诊断闭环总览", self.md_text)
        self.assertIn("这不是系统全通过", self.md_text)
        self.assertIn("reclassified formal fail 仍为 7", self.md_text)
        self.assertIn("3 条是真 runtime citation bug", self.md_text)
        self.assertIn("2 条是 trace/evaluator 工具问题", self.md_text)
        self.assertIn("9 条是 secondary/review citation policy decision", self.md_text)
        self.assertIn("5 条 P2 仍是 diagnostic", self.md_text)
        self.assertNotIn("全部通过", self.md_text)

    def test_runner_scope_does_not_call_unrelated_repair_surfaces(self) -> None:
        for forbidden in FORBIDDEN_SCRIPT_TEXT:
            self.assertNotIn(forbidden, self.script_text)

        commands = "\n".join(step["command"] for step in self.payload["steps"])
        self.assertNotIn("scripts/full_chain", commands)
        self.assertNotIn("frontend/", commands)
        self.assertNotIn("/api/v1/", commands)
        self.assertIn("scripts/eval/answer_eval_v1.py", commands)
        self.assertIn("scripts/eval/retrieval_eval_v1.py", commands)


if __name__ == "__main__":
    unittest.main()
