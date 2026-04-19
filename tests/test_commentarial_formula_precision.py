from __future__ import annotations

import unittest

from backend.answers.assembler import (
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
from backend.commentarial.layer import ROUTE_ASSISTIVE, CommentarialLayer


class CommentarialFormulaPrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.layer = CommentarialLayer()
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

    @staticmethod
    def _commentarial_items(payload: dict) -> list[dict]:
        commentarial = payload.get("commentarial") or {}
        return [item for section in commentarial.get("sections", []) for item in section.get("items", [])]

    def test_formula_queries_only_return_formula_consistent_items(self) -> None:
        cases = [
            ("小青龙汤有哪些功效？", "小青龙汤"),
            ("桂枝汤有哪些功效？", "桂枝汤"),
            ("小柴胡汤有哪些功效？", "小柴胡汤"),
            ("五苓散有哪些功效？", "五苓散"),
        ]
        for query, expected_formula in cases:
            with self.subTest(query=query):
                plan = self.layer.detect_route(query)
                self.assertIsNotNone(plan)
                assert plan is not None
                self.assertEqual(plan.route, ROUTE_ASSISTIVE)
                self.assertEqual(plan.formula_topic, expected_formula)

                payload = self.assembler.assemble(query)
                commentarial = payload.get("commentarial")
                self.assertIsNotNone(commentarial)
                assert commentarial is not None
                self.assertEqual(commentarial["route"], ROUTE_ASSISTIVE)

                items = self._commentarial_items(payload)
                self.assertTrue(items, query)
                for item in items:
                    unit = self.layer.units_by_id[item["unit_id"]]
                    assessment = self.layer._assess_formula_consistency(unit, expected_formula)  # noqa: SLF001
                    self.assertTrue(assessment["passes"], f"{query}: {item['unit_id']}")

    def test_formula_queries_block_known_cross_formula_leaks(self) -> None:
        leak_cases = [
            ("小青龙汤有哪些功效？", {"cmu_liu_p072", "cmu_liu_p105"}),
            ("桂枝汤有哪些功效？", {"cmu_liu_p007", "cmu_hao_rw056"}),
            ("小柴胡汤有哪些功效？", {"cmu_liu_p105", "cmu_hao_rw082"}),
            ("五苓散有哪些功效？", {"cmu_hao_rw187", "cmu_liu_p029"}),
        ]
        for query, banned_unit_ids in leak_cases:
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                item_ids = {item["unit_id"] for item in self._commentarial_items(payload)}
                self.assertTrue(item_ids)
                self.assertTrue(item_ids.isdisjoint(banned_unit_ids), f"{query}: {item_ids}")

    def test_formula_query_prefers_empty_over_off_topic_commentarial(self) -> None:
        query = "白散方有哪些功效？"
        plan = self.layer.detect_route(query)
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.route, ROUTE_ASSISTIVE)
        self.assertEqual(plan.formula_topic, "白散")

        payload = self.assembler.assemble(query)
        self.assertIsNone(payload.get("commentarial"))

    def test_formula_precision_keeps_commentarial_red_lines(self) -> None:
        queries = [
            "小青龙汤有哪些功效？",
            "桂枝汤有哪些功效？",
            "小柴胡汤有哪些功效？",
            "五苓散有哪些功效？",
        ]
        for query in queries:
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                commentarial = payload.get("commentarial")
                self.assertIsNotNone(commentarial)
                assert commentarial is not None
                self.assertTrue(all(section["collapsed_by_default"] for section in commentarial["sections"]))
                self.assertTrue(payload["primary_evidence"])
                self.assertTrue(all(item["record_type"] == "main_passages" for item in payload["primary_evidence"]))

                items = self._commentarial_items(payload)
                self.assertTrue(items)
                self.assertTrue(all(item["never_use_in_primary"] for item in items))
                self.assertTrue(all(not item["use_for_confidence_gate"] for item in items))


if __name__ == "__main__":
    unittest.main()
