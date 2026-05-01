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


class CommonLearnerRoutingV1Test(unittest.TestCase):
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

    def test_formula_comparison_template_still_routes(self) -> None:
        for query in (
            "桂枝加浓朴杏子汤方和桂枝加附子汤方的区别是什么？",
            "麻黄汤方和桂枝汤方有什么区别？",
        ):
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                answer_text = payload["answer_text"]

                self.assertEqual(payload["answer_mode"], "strong")
                self.assertTrue(answer_text.startswith("结论："))
                self.assertIn("比较：", answer_text)
                self.assertNotIn("可以先把", answer_text)
                self.assertNotIn("刘渡舟", answer_text)
                self.assertNotIn("topic_mismatch_demoted", answer_text)
                self.assertIsNone(payload.get("commentarial"))

    def test_non_formula_comparison_is_not_formula_refusal(self) -> None:
        forbidden = (
            "请明确写出两个方名",
            "当前无法稳定识别两个待比较的方名",
            "当前无法稳定识别两个待比较方剂",
        )
        for query in (
            "中风和伤寒有什么区别？",
            "结胸和痞证有什么不同？",
            "太阳病和阳明病有什么区别？",
        ):
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                answer_text = payload["answer_text"]
                refuse_reason = payload.get("refuse_reason") or ""

                for phrase in forbidden:
                    self.assertNotIn(phrase, answer_text)
                    self.assertNotIn(phrase, refuse_reason)
                comparison_debug = self.assembler.get_last_comparison_debug()
                self.assertIsNone(comparison_debug)

    def test_generic_self_medication_and_dosage_safety_refuses(self) -> None:
        for query in (
            "普通人能不能对照条文自用桂枝汤？",
            "汉代一两换算成现代克数后能直接用吗？",
            "我发热恶寒能不能用麻黄汤？",
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
                self.assertIn("个人用药", checked_text)
                self.assertIn("剂量换算", checked_text)
                self.assertIn("服药安全", checked_text)
                self.assertIn("方文", checked_text)
                self.assertIn("条文", checked_text)
                self.assertIn("书内语境", checked_text)
                self.assertIn("文本含义", checked_text)
                self.assertNotRegex(payload["answer_text"], re.compile(r"\d+\s*克"))
                self.assertFalse(payload["primary_evidence"])
                self.assertFalse(payload["citations"])

    def test_formula_value_comparison_refuses_without_name_resolution_message(self) -> None:
        payload = self.assembler.assemble("桂枝汤和麻黄汤哪个更适合我？")
        checked_text = "\n".join(
            [
                payload["answer_text"],
                payload.get("refuse_reason") or "",
                "\n".join(payload.get("suggested_followup_questions") or []),
            ]
        )

        self.assertEqual(payload["answer_mode"], "refuse")
        self.assertIn("不支持判断哪个更好、更适合谁或临床优劣", checked_text)
        self.assertNotIn("请明确写出两个方名", checked_text)
        self.assertNotIn("当前无法稳定识别两个待比较", checked_text)
        self.assertFalse(payload["primary_evidence"])

    def test_p0_p1_and_single_formula_boundaries_do_not_regress(self) -> None:
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

        payload = self.assembler.assemble("桂枝加附子汤方是什么？")
        self.assertEqual(payload["answer_mode"], "strong")
        self.assertNotIn("比较：", payload["answer_text"])
        self.assertTrue(
            all(not item["record_id"].startswith("full:") for item in payload["primary_evidence"])
        )
        self.assertIsNone(self.assembler.get_last_comparison_debug())


if __name__ == "__main__":
    unittest.main()
