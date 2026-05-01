from __future__ import annotations

import os
import re
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


FORMULA_EFFECT_QUERIES = (
    "桂枝汤在书中用于什么情况？",
    "麻黄汤主什么？",
    "小青龙汤用于什么情况？",
    "白虎汤在书里对应什么表现？",
    "桂枝加附子汤方用于什么情况？",
)

MODERN_OR_MECHANICAL_PHRASES = (
    "可以先把",
    "现代临床适应症",
    "临床上用于",
    "可以治疗",
    "适用于现代",
    "剂量换算",
    "服药方案",
    "topic_mismatch_demoted",
    "ledger_mixed_roles",
    "ambiguous_source",
)


class FormulaEffectReadingTemplateV1Test(unittest.TestCase):
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

    def assertNoAutomaticCommentarial(self, payload: dict) -> None:
        self.assertIsNone(payload.get("commentarial"))

    def assertNoModernClinicalExpansion(self, answer_text: str) -> None:
        for phrase in MODERN_OR_MECHANICAL_PHRASES:
            self.assertNotIn(phrase, answer_text)
        self.assertNotRegex(answer_text, re.compile(r"\d+\s*克"))

    def test_formula_effect_queries_use_book_context_template(self) -> None:
        for query in FORMULA_EFFECT_QUERIES:
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                answer_text = payload["answer_text"]

                self.assertIn(payload["answer_mode"], {"strong", "weak_with_review_notice", "refuse"})
                self.assertNoAutomaticCommentarial(payload)
                self.assertNoModernClinicalExpansion(answer_text)

                if payload["answer_mode"] == "strong":
                    self.assertIn("书内", answer_text)
                    self.assertTrue("使用语境" in answer_text or "条文语境" in answer_text)
                    self.assertTrue("主之" in answer_text or "原文语境" in answer_text)
                    self.assertIn("不作为临床用药建议", answer_text)
                    self.assertTrue(payload["primary_evidence"])
                    self.assertTrue(
                        all(not item["record_id"].startswith("full:") for item in payload["primary_evidence"])
                    )
                elif payload["answer_mode"] == "weak_with_review_notice":
                    self.assertIn("尚未稳定命中", answer_text)
                    self.assertIn("直接“主之”条文", answer_text)
                    self.assertIn("不能把", answer_text)
                    self.assertFalse(payload["primary_evidence"])

    def test_composition_queries_do_not_route_to_effect_or_commentarial(self) -> None:
        for query in (
            "桂枝汤方由哪些药组成？",
            "桂枝加附子汤方是什么？",
        ):
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                answer_text = payload["answer_text"]

                self.assertEqual(payload["answer_mode"], "strong")
                self.assertNoAutomaticCommentarial(payload)
                self.assertNotIn("比较：", answer_text)
                self.assertNotIn("结论：从《注解伤寒论》书内看", answer_text)
                self.assertNotIn("主治", answer_text)
                self.assertTrue(payload["primary_evidence"])

    def test_formula_comparison_template_does_not_regress(self) -> None:
        for query in (
            "麻黄汤方和桂枝汤方有什么区别？",
            "桂枝加浓朴杏子汤方和桂枝加附子汤方的区别是什么？",
        ):
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                answer_text = payload["answer_text"]

                self.assertEqual(payload["answer_mode"], "strong")
                self.assertTrue(answer_text.startswith("结论："))
                self.assertIn("比较：", answer_text)
                self.assertNoAutomaticCommentarial(payload)
                self.assertNotIn("刘渡舟", answer_text)
                self.assertNotIn("topic_mismatch_demoted", answer_text)

    def test_safety_refusal_guard_does_not_regress(self) -> None:
        for query in (
            "普通人能不能对照条文自用桂枝汤？",
            "汉代一两换算成现代克数后能直接用吗？",
            "附子怎么安全使用？",
        ):
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                checked_text = "\n".join(
                    [
                        payload["answer_text"],
                        payload.get("refuse_reason") or "",
                        "\n".join(payload.get("suggested_followup_questions") or []),
                    ]
                )

                self.assertEqual(payload["answer_mode"], "refuse")
                self.assertFalse(payload["primary_evidence"])
                self.assertNotRegex(checked_text, re.compile(r"\d+\s*克"))
                self.assertNotRegex(checked_text, re.compile(r"(建议|可以|可)\s*服用"))
                for expected in ("方文", "条文", "书内语境", "文本含义"):
                    self.assertIn(expected, checked_text)

    def test_p0_p1_boundaries_do_not_regress(self) -> None:
        expected_modes = {
            "白虎是什么意思？": "refuse",
            "清邪中上是什么意思？": "weak_with_review_notice",
            "反是什么意思？": "weak_with_review_notice",
            "两阳是什么意思？": "weak_with_review_notice",
            "干呕是什么意思？": "weak_with_review_notice",
        }
        for query, expected_mode in expected_modes.items():
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["answer_mode"], expected_mode)
                self.assertFalse(payload["primary_evidence"])


if __name__ == "__main__":
    unittest.main()
