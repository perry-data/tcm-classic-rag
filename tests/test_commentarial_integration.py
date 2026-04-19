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


class CommentarialIntegrationTests(unittest.TestCase):
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

    def test_commentarial_bundle_loaded(self) -> None:
        self.assertTrue(self.layer.enabled, self.layer.load_error)
        self.assertGreater(len(self.layer.units), 0)
        self.assertIn("handoff_manifest", self.layer.support_files)
        self.assertIn("acceptance_report", self.layer.support_files)
        self.assertIn("manual_review_queue", self.layer.support_files)

    def test_anchor_resolution_artifacts_loaded(self) -> None:
        resolution = self.layer.resolution
        self.assertIn("by_source", resolution)
        self.assertEqual(
            resolution["by_source"]["liu_duzhou_shanghan_lectures_2007"]["PASSAGE_NO:001"]["canonical_passage_id"],
            "ZJSHL-CH-008-P-0191",
        )
        self.assertEqual(
            resolution["by_source"]["hao_wanshan_shanghan_lectures_2007"]["PASSAGE_NO:104A"]["canonical_passage_id"],
            "ZJSHL-CH-009-P-0253",
        )
        self.assertEqual(
            resolution["global"]["PASSAGE_NO:007"]["status"],
            "conflicting_source_scope",
        )

    def test_named_view_retrieval(self) -> None:
        payload = self.assembler.assemble("刘渡舟怎么看第141条？")
        commentarial = payload.get("commentarial")
        self.assertIsNotNone(commentarial)
        self.assertEqual(commentarial["route"], ROUTE_NAMED)
        items = [item for section in commentarial["sections"] for item in section["items"]]
        self.assertTrue(items)
        self.assertTrue(all(item["commentator"] == "刘渡舟" for item in items))
        self.assertTrue(any("ZJSHL-CH-010-P-0015" in item["resolved_primary_anchor_passage_ids"] for item in items))

    def test_comparison_view_retrieval(self) -> None:
        payload = self.assembler.assemble("两家如何解释少阳病？")
        commentarial = payload.get("commentarial")
        self.assertIsNotNone(commentarial)
        self.assertEqual(commentarial["route"], ROUTE_COMPARISON)
        commentators = {section.get("commentator") for section in commentarial["sections"]}
        self.assertIn("刘渡舟", commentators)
        self.assertIn("郝万山", commentators)

    def test_meta_learning_view_retrieval(self) -> None:
        payload = self.assembler.assemble("怎么学《伤寒论》？")
        commentarial = payload.get("commentarial")
        self.assertIsNotNone(commentarial)
        self.assertEqual(commentarial["route"], ROUTE_META)
        items = [item for section in commentarial["sections"] for item in section["items"]]
        self.assertTrue(any(item["theme_display_tier"] == "tier_3_meta_learning_only" for item in items))

    def test_default_assistive_preserves_canonical_primary(self) -> None:
        payload = self.assembler.assemble("桂枝汤是什么？")
        commentarial = payload.get("commentarial")
        self.assertIsNotNone(commentarial)
        self.assertEqual(commentarial["route"], ROUTE_ASSISTIVE)
        self.assertGreater(len(payload["primary_evidence"]), 0)
        self.assertTrue(all(item["record_type"] == "main_passages" for item in payload["primary_evidence"]))
        self.assertTrue(all(section["collapsed_by_default"] for section in commentarial["sections"]))

    def test_commentarial_flags_stay_out_of_primary_and_confidence_gate(self) -> None:
        payload = self.assembler.assemble("桂枝汤是什么？")
        items = [item for section in payload["commentarial"]["sections"] for item in section["items"]]
        self.assertTrue(items)
        self.assertTrue(all(item["never_use_in_primary"] for item in items))
        self.assertTrue(all(not item["use_for_confidence_gate"] for item in items))

    def test_display_summary_hides_internal_commentary_function_tags(self) -> None:
        payload = self.assembler.assemble("桂枝汤是什么？")
        items = [item for section in payload["commentarial"]["sections"] for item in section["items"]]
        tagged_units = [
            (item, self.layer.units_by_id[item["unit_id"]])
            for item in items
            if "重点涉及" in str(self.layer.units_by_id[item["unit_id"]].get("summary_text") or "")
        ]
        self.assertTrue(tagged_units)
        for item, raw_unit in tagged_units:
            self.assertIn("重点涉及", raw_unit["summary_text"])
            self.assertNotIn("重点涉及", item["summary_text"])
            self.assertNotRegex(item["summary_text"], r"[a-z]+_[a-z_]+")

    def test_unresolved_multi_stays_folded(self) -> None:
        unresolved_multi_unit = next(
            unit for unit in self.layer.units if unit.get("anchor_priority_mode") == "unresolved_multi"
        )
        bucket = self.layer._classify_display_bucket(unresolved_multi_unit, ROUTE_NAMED)  # noqa: SLF001
        self.assertEqual(bucket, "folded")

    def test_tier4_theme_not_default_display(self) -> None:
        tier4_unit = next(
            unit for unit in self.layer.units if unit.get("theme_display_tier") == "tier_4_do_not_default_display"
        )
        self.assertEqual(self.layer._classify_display_bucket(tier4_unit, ROUTE_NAMED), "exclude")  # noqa: SLF001
        self.assertEqual(self.layer._classify_display_bucket(tier4_unit, ROUTE_ASSISTIVE), "exclude")  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
