from __future__ import annotations

import json
import os
import sqlite3
import unittest

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
from scripts.data_plane_formula_fix.run_formula_medium_span_fix_v1 import (  # noqa: E402
    BAD_FORMULA_TOPICS,
    FORMULA_FIXES,
    REGRESSION_QUERIES,
    TARGET_FORMULAS,
)


FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}


class FormulaMediumSpanFixV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_path = resolve_project_path(DEFAULT_DB_PATH)
        cls.conn = sqlite3.connect(cls.db_path)
        cls.conn.row_factory = sqlite3.Row
        cls.assembler = AnswerAssembler(
            db_path=cls.db_path,
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
        cls.conn.close()

    def test_target_formula_span_fields_match_fix_plan(self) -> None:
        rows = {
            row["canonical_name"]: row
            for row in self.conn.execute(
                """
                SELECT
                    canonical_name,
                    formula_span_start_passage_id,
                    formula_span_end_passage_id,
                    composition_passage_ids_json,
                    decoction_passage_ids_json,
                    usage_context_passage_ids_json,
                    source_passage_ids_json,
                    source_confidence,
                    formula_display_name,
                    composition_display_text,
                    span_fix_reason,
                    confidence_reason,
                    span_fix_status
                FROM formula_canonical_registry
                WHERE canonical_name IN ({})
                """.format(",".join("?" for _ in TARGET_FORMULAS)),
                TARGET_FORMULAS,
            )
        }
        self.assertEqual(set(rows), set(TARGET_FORMULAS))

        for name, fix in FORMULA_FIXES.items():
            with self.subTest(formula=name):
                row = rows[name]
                expected_source_ids = []
                for passage_id in (
                    fix["usage_context_passage_ids"]
                    + fix["composition_passage_ids"]
                    + fix["decoction_passage_ids"]
                ):
                    if passage_id not in expected_source_ids:
                        expected_source_ids.append(passage_id)

                self.assertEqual(row["formula_span_start_passage_id"], fix["formula_span_start_passage_id"])
                self.assertEqual(row["formula_span_end_passage_id"], fix["formula_span_end_passage_id"])
                self.assertEqual(json.loads(row["composition_passage_ids_json"]), fix["composition_passage_ids"])
                self.assertEqual(json.loads(row["decoction_passage_ids_json"]), fix["decoction_passage_ids"])
                self.assertEqual(json.loads(row["usage_context_passage_ids_json"]), fix["usage_context_passage_ids"])
                self.assertEqual(json.loads(row["source_passage_ids_json"]), expected_source_ids)
                self.assertEqual(row["source_confidence"], fix["source_confidence"])
                self.assertEqual(row["formula_display_name"], fix["formula_display_name"])
                self.assertEqual(row["composition_display_text"], fix["composition_display_text"])
                self.assertEqual(row["span_fix_reason"], fix["span_fix_reason"])
                self.assertEqual(row["confidence_reason"], fix["confidence_reason"])
                self.assertEqual(row["span_fix_status"], fix["post_fix_classification"])

    def test_confidence_classification_is_intentional(self) -> None:
        high = {
            row["canonical_name"]
            for row in self.conn.execute(
                """
                SELECT canonical_name
                FROM formula_canonical_registry
                WHERE canonical_name IN ({})
                  AND source_confidence = 'high'
                """.format(",".join("?" for _ in TARGET_FORMULAS)),
                TARGET_FORMULAS,
            )
        }
        medium = {
            row["canonical_name"]
            for row in self.conn.execute(
                """
                SELECT canonical_name
                FROM formula_canonical_registry
                WHERE canonical_name IN ({})
                  AND source_confidence = 'medium'
                """.format(",".join("?" for _ in TARGET_FORMULAS)),
                TARGET_FORMULAS,
            )
        }

        self.assertEqual(high, {"乌梅丸", "桂枝甘草龙骨牡蛎汤", "茵陈蒿汤", "麻黄附子甘草汤"})
        self.assertEqual(medium, {"旋复代赭石汤", "栀子浓朴汤"})

    def test_retrieval_ready_formula_view_uses_variant_stripped_display(self) -> None:
        rows = {
            row["canonical_name"]: row
            for row in self.conn.execute(
                """
                SELECT
                    canonical_name,
                    formula_display_name,
                    composition_display_text,
                    retrieval_text,
                    span_fix_status,
                    confidence_reason
                FROM retrieval_ready_formula_view
                WHERE canonical_name IN ({})
                """.format(",".join("?" for _ in TARGET_FORMULAS)),
                TARGET_FORMULAS,
            )
        }
        self.assertEqual(set(rows), set(TARGET_FORMULAS))

        for name, row in rows.items():
            with self.subTest(formula=name):
                self.assertEqual(row["formula_display_name"], name)
                self.assertEqual(row["composition_display_text"], FORMULA_FIXES[name]["composition_display_text"])
                self.assertIn("展示组成：", row["retrieval_text"])
                self.assertIn(FORMULA_FIXES[name]["composition_display_text"], row["retrieval_text"])
                self.assertIn(FORMULA_FIXES[name]["confidence_reason"], row["retrieval_text"])
                self.assertEqual(row["span_fix_status"], FORMULA_FIXES[name]["post_fix_classification"])
                self.assertEqual(row["confidence_reason"], FORMULA_FIXES[name]["confidence_reason"])
                self.assertNotIn("赵本", row["composition_display_text"])
                self.assertNotIn("医统本", row["composition_display_text"])

    def test_formula_lookup_and_comparison_regression_stays_safe(self) -> None:
        for item in REGRESSION_QUERIES:
            with self.subTest(query=item["query"]):
                retrieval = self.assembler.engine.retrieve(item["query"])
                payload = self.assembler.assemble(item["query"])
                primary = payload.get("primary_evidence") or []
                bad_anchor_count = sum(
                    1
                    for row in (retrieval.get("raw_candidates") or [])[:5]
                    if row.get("topic_consistency") in BAD_FORMULA_TOPICS
                )

                self.assertEqual(payload["answer_mode"], "strong")
                self.assertTrue(primary)
                self.assertEqual(bad_anchor_count, 0)
                self.assertTrue(
                    all(
                        item["record_type"] == "main_passages"
                        and str(item["record_id"]).startswith("safe:main_passages:")
                        for item in primary
                    )
                )
                self.assertFalse(
                    any(
                        item["record_type"] in FORBIDDEN_PRIMARY_TYPES
                        or str(item["record_id"]).startswith("full:passages:")
                        for item in primary
                    )
                )


if __name__ == "__main__":
    unittest.main()
