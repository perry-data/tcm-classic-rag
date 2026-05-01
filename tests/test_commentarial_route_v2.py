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
    META_BAND_STRONG,
    META_BAND_TOPIC,
    ROUTE_ASSISTIVE,
    ROUTE_COMPARISON,
    ROUTE_META,
    ROUTE_NAMED,
    CommentarialLayer,
)


class CommentarialRouteV2Tests(unittest.TestCase):
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

    def _assert_route(
        self,
        query: str,
        expected_route: str,
        expected_commentators: tuple[str, ...] = (),
        *,
        explicit: bool = True,
        expected_meta_band: str | None = None,
    ) -> None:
        plan = self.layer.detect_route(query)
        self.assertIsNotNone(plan, query)
        assert plan is not None
        self.assertEqual(plan.route, expected_route, query)
        self.assertEqual(plan.commentators, expected_commentators, query)
        self.assertEqual(plan.explicit, explicit, query)
        self.assertEqual(plan.meta_band, expected_meta_band, query)
        self.assertIsNotNone(plan.debug, query)
        assert plan.debug is not None
        self.assertEqual(plan.debug["chosen_route"], expected_route, query)
        self.assertIn("route_scores", plan.debug, query)
        self.assertIn("matched_signals", plan.debug, query)
        self.assertIn("rejected_signals", plan.debug, query)

    @staticmethod
    def _commentarial_items(payload: dict) -> list[dict]:
        commentarial = payload.get("commentarial") or {}
        return [item for section in commentarial.get("sections", []) for item in section.get("items", [])]

    def test_named_route_handles_more_natural_phrasings(self) -> None:
        cases = [
            ("刘老对141条怎么说？", ("刘渡舟",)),
            ("刘老师这里怎么讲第141条？", ("刘渡舟",)),
            ("郝老师对桂枝汤是怎么理解的？", ("郝万山",)),
            ("郝万山对桂枝汤的看法是什么？", ("郝万山",)),
        ]
        for query, expected_commentators in cases:
            with self.subTest(query=query):
                self._assert_route(query, ROUTE_NAMED, expected_commentators)
                plan = self.layer.detect_route(query)
                assert plan is not None and plan.debug is not None
                self.assertGreater(
                    plan.debug["route_scores"][ROUTE_NAMED],
                    plan.debug["route_scores"][ROUTE_META],
                    query,
                )

    def test_comparison_route_prefers_dual_view_over_named(self) -> None:
        cases = [
            "刘渡舟和郝万山对少阳病的看法有什么不同？",
            "两位老师怎么看少阳病？",
            "少阳病这两家解释有何分歧？",
        ]
        for query in cases:
            with self.subTest(query=query):
                self._assert_route(query, ROUTE_COMPARISON, ("刘渡舟", "郝万山"))
                plan = self.layer.detect_route(query)
                assert plan is not None and plan.debug is not None
                self.assertGreater(
                    plan.debug["route_scores"][ROUTE_COMPARISON],
                    plan.debug["route_scores"][ROUTE_NAMED],
                    query,
                )

    def test_meta_route_broadens_to_learning_understanding_queries(self) -> None:
        cases = [
            ("初学者应该怎么理解少阳病？", META_BAND_TOPIC),
            ("六经辨证入门应该先抓什么？", META_BAND_STRONG),
            ("读伤寒论应该先抓框架还是先背条文？", META_BAND_STRONG),
            ("学习伤寒论时少阳病这一块应该怎么把握？", META_BAND_TOPIC),
        ]
        for query, expected_meta_band in cases:
            with self.subTest(query=query):
                self._assert_route(
                    query,
                    ROUTE_META,
                    (),
                    expected_meta_band=expected_meta_band,
                )
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["commentarial"]["route"], ROUTE_META, query)
                items = self._commentarial_items(payload)
                self.assertTrue(items, query)
                visible_tiers = {item.get("theme_display_tier") for item in items if item.get("theme_display_tier")}
                self.assertTrue(
                    visible_tiers.intersection(
                        {"tier_1_named_view_ok", "tier_2_fold_only", "tier_3_meta_learning_only"}
                    ),
                    query,
                )
                self.assertNotIn("tier_4_do_not_default_display", visible_tiers, query)

    def test_ordinary_explanations_do_not_get_swallowed_by_meta(self) -> None:
        assistive_cases = [
            "少阳病是什么意思？",
        ]
        suppressed_template_cases = ["桂枝汤是什么？", "黄连汤方的条文是什么？"]
        for query in assistive_cases:
            with self.subTest(query=query):
                self._assert_route(query, ROUTE_ASSISTIVE, (), explicit=False)
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["commentarial"]["route"], ROUTE_ASSISTIVE)
                self.assertTrue(payload["primary_evidence"], query)
                self.assertTrue(all(item["record_type"] == "main_passages" for item in payload["primary_evidence"]))
        for query in suppressed_template_cases:
            with self.subTest(query=query):
                self._assert_route(query, ROUTE_ASSISTIVE, (), explicit=False)
                payload = self.assembler.assemble(query)
                self.assertIsNone(payload.get("commentarial"))
                self.assertTrue(payload["primary_evidence"], query)
                self.assertTrue(all(item["record_type"] == "main_passages" for item in payload["primary_evidence"]))

        self._assert_route("刘渡舟怎么看第141条？", ROUTE_NAMED, ("刘渡舟",))

    def test_route_debug_keeps_explainable_competition_trace(self) -> None:
        plan = self.layer.detect_route("两位老师怎么看少阳病？")
        self.assertIsNotNone(plan)
        assert plan is not None and plan.debug is not None
        debug = plan.debug
        self.assertEqual(debug["chosen_route"], ROUTE_COMPARISON)
        self.assertIn(ROUTE_NAMED, debug["route_scores"])
        self.assertIn(ROUTE_COMPARISON, debug["route_scores"])
        self.assertIn(ROUTE_META, debug["route_scores"])
        self.assertTrue(debug["matched_signals"])
        self.assertTrue(any(item["route"] == ROUTE_NAMED for item in debug["rejected_signals"]))

    def test_red_lines_still_hold_after_route_v2(self) -> None:
        queries = [
            "刘老对141条怎么说？",
            "两位老师怎么看少阳病？",
            "初学者应该怎么理解少阳病？",
        ]
        for query in queries:
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                items = self._commentarial_items(payload)
                self.assertTrue(items)
                self.assertTrue(all(item["never_use_in_primary"] for item in items))
                self.assertTrue(all(not item["use_for_confidence_gate"] for item in items))
                self.assertNotIn(
                    "tier_4_do_not_default_display",
                    {item.get("theme_display_tier") for item in items if item.get("theme_display_tier")},
                )

        suppressed_payload = self.assembler.assemble("桂枝汤是什么？")
        self.assertIsNone(suppressed_payload.get("commentarial"))

        unresolved_multi_unit = next(
            unit for unit in self.layer.units if unit.get("anchor_priority_mode") == "unresolved_multi"
        )
        self.assertEqual(self.layer._classify_display_bucket(unresolved_multi_unit, ROUTE_NAMED), "folded")  # noqa: SLF001
        self.assertEqual(self.layer._classify_display_bucket(unresolved_multi_unit, ROUTE_META), "folded")  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
