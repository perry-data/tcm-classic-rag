from __future__ import annotations

import os
import unittest

os.environ.setdefault("TCM_QA_TRACE_ENABLED", "0")
os.environ.setdefault("PERF_DISABLE_LLM", "1")
os.environ.setdefault("PERF_DISABLE_RERANK", "1")
os.environ.setdefault("PERF_RETRIEVAL_MODE", "sparse")

from backend.answers.assembler import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_DB_PATH,
    DEFAULT_DENSE_CHUNKS_INDEX,
    DEFAULT_DENSE_CHUNKS_META,
    DEFAULT_DENSE_MAIN_INDEX,
    DEFAULT_DENSE_MAIN_META,
    DEFAULT_EMBED_MODEL,
    DEFAULT_POLICY_PATH,
    DEFAULT_RERANK_MODEL,
    AnswerAssembler,
    resolve_project_path,
)


class FormulaComparisonTemplateV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assembler = AnswerAssembler(
            db_path=resolve_project_path(DEFAULT_DB_PATH),
            policy_path=resolve_project_path(DEFAULT_POLICY_PATH),
            embed_model=DEFAULT_EMBED_MODEL,
            rerank_model=DEFAULT_RERANK_MODEL,
            cache_dir=resolve_project_path(DEFAULT_CACHE_DIR),
            dense_chunks_index=resolve_project_path(DEFAULT_DENSE_CHUNKS_INDEX),
            dense_chunks_meta=resolve_project_path(DEFAULT_DENSE_CHUNKS_META),
            dense_main_index=resolve_project_path(DEFAULT_DENSE_MAIN_INDEX),
            dense_main_meta=resolve_project_path(DEFAULT_DENSE_MAIN_META),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.assembler.close()

    def test_bad_case_uses_direct_formula_comparison_template(self) -> None:
        payload = self.assembler.assemble("桂枝加浓朴杏子汤方和桂枝加附子汤方的区别是什么？")
        answer_text = payload["answer_text"]

        self.assertEqual(payload["answer_mode"], "strong")
        self.assertTrue(answer_text.startswith("结论："))
        for expected in (
            "共同点是都以桂枝汤方为基础方",
            "加浓朴、杏仁",
            "加附子",
            "太阳病，下之微喘者，表未解故也",
            "太阳病，发汗，遂漏不止",
            "方文依据",
            "条文语境依据",
            "不作为临床用药建议",
        ):
            self.assertIn(expected, answer_text)
        for forbidden in (
            "可以先把",
            "从现有片段看",
            "差后微烦证",
            "刘渡舟",
            "topic_mismatch_demoted",
            "ledger_mixed_roles",
            "ambiguous_source",
        ):
            self.assertNotIn(forbidden, answer_text)

        self.assertIsNone(payload.get("commentarial"))
        self.assertEqual(
            [item["record_id"] for item in payload["primary_evidence"]],
            [
                "safe:main_passages:ZJSHL-CH-025-P-0003",
                "safe:main_passages:ZJSHL-CH-025-P-0004",
            ],
        )
        self.assertIn("full:passages:ZJSHL-CH-009-P-0053", [item["record_id"] for item in payload["secondary_evidence"]])
        self.assertFalse(payload["review_materials"])
        self.assertTrue(all(citation["citation_role"] == "primary" for citation in payload["citations"]))

    def test_formula_comparison_regressions_stay_strong_without_commentarial(self) -> None:
        for query in (
            "麻黄汤方和桂枝汤方的区别是什么？",
            "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？",
        ):
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["answer_mode"], "strong")
                self.assertTrue(payload["answer_text"].startswith("结论："))
                self.assertIsNone(payload.get("commentarial"))
                self.assertTrue(payload["primary_evidence"])

    def test_single_formula_query_does_not_trigger_comparison_template(self) -> None:
        payload = self.assembler.assemble("桂枝加附子汤方是什么？")
        self.assertEqual(payload["answer_mode"], "strong")
        self.assertNotIn("比较：", payload["answer_text"])

    def test_p0_boundary_modes_do_not_regress(self) -> None:
        expected_modes = {
            "白虎是什么意思？": "refuse",
            "清邪中上是什么意思？": "weak_with_review_notice",
            "反是什么意思？": "weak_with_review_notice",
            "两阳是什么意思？": "weak_with_review_notice",
        }
        for query, expected_mode in expected_modes.items():
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["answer_mode"], expected_mode)
                self.assertFalse(payload["primary_evidence"])


if __name__ == "__main__":
    unittest.main()
