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
from backend.commentarial.layer import (
    ROUTE_ASSISTIVE,
    ROUTE_COMPARISON,
    ROUTE_META,
    ROUTE_NAMED,
    CommentarialLayer,
)


class CommentarialRouteRobustnessTests(unittest.TestCase):
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

    def _assert_detected_route(
        self,
        query: str,
        expected_route: str,
        expected_commentators: tuple[str, ...],
    ) -> None:
        plan = self.layer.detect_route(query)
        self.assertIsNotNone(plan, query)
        assert plan is not None
        self.assertEqual(plan.route, expected_route, query)
        self.assertEqual(plan.commentators, expected_commentators, query)

    @staticmethod
    def _commentarial_items(payload: dict) -> list[dict]:
        commentarial = payload.get("commentarial") or {}
        return [item for section in commentarial.get("sections", []) for item in section.get("items", [])]

    def test_named_route_variants(self) -> None:
        cases = [
            ("刘老怎么看第141条？", ("刘渡舟",)),
            ("刘渡舟老师怎么解释第141条？", ("刘渡舟",)),
            ("郝万山老师怎么看桂枝汤？", ("郝万山",)),
            ("名家是怎么讲第141条的？", ("刘渡舟", "郝万山")),
        ]
        for query, expected_commentators in cases:
            with self.subTest(query=query):
                self._assert_detected_route(query, ROUTE_NAMED, expected_commentators)

    def test_comparison_route_variants(self) -> None:
        cases = [
            "郝万山和刘渡舟对少阳病有什么不同？",
            "两位老师对少阳病的解释有何区别？",
            "这两家怎么看少阳病？",
        ]
        for query in cases:
            with self.subTest(query=query):
                self._assert_detected_route(query, ROUTE_COMPARISON, ("刘渡舟", "郝万山"))

    def test_meta_learning_route_variants(self) -> None:
        cases = [
            "《伤寒论》应该怎么学？",
            "初学者怎么读《伤寒论》？",
            "学习伤寒论有什么方法？",
        ]
        for query in cases:
            with self.subTest(query=query):
                self._assert_detected_route(query, ROUTE_META, ())

    def test_default_queries_stay_assistive_and_keep_canonical_primary(self) -> None:
        cases = [
            "桂枝汤是什么？",
            "少阳病是什么意思？",
            "黄连汤方的条文是什么？",
        ]
        for query in cases:
            with self.subTest(query=query):
                self.assertIsNone(self.layer.detect_route(query))
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["query"], query)
                commentarial = payload.get("commentarial")
                self.assertIsNotNone(commentarial)
                assert commentarial is not None
                self.assertEqual(commentarial["route"], ROUTE_ASSISTIVE)
                self.assertTrue(commentarial["sections"])
                self.assertTrue(all(section["collapsed_by_default"] for section in commentarial["sections"]))
                self.assertTrue(payload["primary_evidence"])
                self.assertTrue(all(item["record_type"] == "main_passages" for item in payload["primary_evidence"]))
                items = self._commentarial_items(payload)
                self.assertTrue(items)
                self.assertTrue(all(item["never_use_in_primary"] for item in items))
                self.assertTrue(all(not item["use_for_confidence_gate"] for item in items))

    def test_explicit_routes_do_not_pollute_canonical_citations(self) -> None:
        cases = [
            ("刘老怎么看第141条？", ROUTE_NAMED),
            ("两位老师对少阳病的解释有何区别？", ROUTE_COMPARISON),
            ("学习伤寒论有什么方法？", ROUTE_META),
        ]
        allowed_record_types = {"main_passages", "annotations", "passages", "ambiguous_passages"}
        for query, expected_route in cases:
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["query"], query)
                commentarial = payload.get("commentarial")
                self.assertIsNotNone(commentarial)
                assert commentarial is not None
                self.assertEqual(commentarial["route"], expected_route)
                self.assertTrue(commentarial["sections"])

                evidence_record_ids = {
                    row["record_id"]
                    for slot_name in ("primary_evidence", "secondary_evidence", "review_materials")
                    for row in payload.get(slot_name, [])
                }
                self.assertTrue(evidence_record_ids or not payload["citations"])
                for citation in payload["citations"]:
                    self.assertIn(citation["record_id"], evidence_record_ids)
                    self.assertIn(citation["record_type"], allowed_record_types)
                    self.assertFalse(str(citation["record_id"]).startswith("cmu_"))

                items = self._commentarial_items(payload)
                self.assertTrue(items)
                self.assertTrue(all(item["never_use_in_primary"] for item in items))
                self.assertTrue(all(not item["use_for_confidence_gate"] for item in items))
                self.assertNotIn(
                    "tier_4_do_not_default_display",
                    {item.get("theme_display_tier") for item in items if item.get("theme_display_tier")},
                )

    def test_unresolved_multi_never_becomes_unique_main_anchor(self) -> None:
        unresolved_multi_unit = next(
            unit for unit in self.layer.units if unit.get("anchor_priority_mode") == "unresolved_multi"
        )
        self.assertEqual(self.layer._classify_display_bucket(unresolved_multi_unit, ROUTE_NAMED), "folded")  # noqa: SLF001
        self.assertEqual(
            self.layer._classify_display_bucket(unresolved_multi_unit, ROUTE_COMPARISON),  # noqa: SLF001
            "folded",
        )

    def test_tier4_theme_stays_out_of_default_rendering(self) -> None:
        tier4_unit = next(
            unit for unit in self.layer.units if unit.get("theme_display_tier") == "tier_4_do_not_default_display"
        )
        for route in (ROUTE_NAMED, ROUTE_COMPARISON, ROUTE_META, ROUTE_ASSISTIVE):
            with self.subTest(route=route):
                self.assertEqual(self.layer._classify_display_bucket(tier4_unit, route), "exclude")  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
