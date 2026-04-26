from __future__ import annotations

import json
import os
import sqlite3
import unittest
from pathlib import Path

os.environ["PERF_DISABLE_LLM"] = "1"
os.environ["PERF_RETRIEVAL_MODE"] = "sparse"
os.environ["PERF_DISABLE_RERANK"] = "1"

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
from scripts.data_plane_batch_upgrade.run_ambiguous_high_value_evidence_upgrade_v1 import (  # noqa: E402
    RUN_ID,
)


FORBIDDEN_PRIMARY_TYPES = {"passages", "ambiguous_passages", "annotations", "annotation_links"}
BAD_FORMULA_TOPICS = {
    "different_formula_anchor",
    "expanded_formula_anchor",
    "comparison_out_of_scope_formula_anchor",
    "formula_query_off_topic",
}
REPRESENTATIVE_A_QUERIES = {
    "何谓太阳病": "太阳病",
    "促脉是什么": "促脉",
    "霍乱是什么": "霍乱",
    "劳复是什么意思": "劳复",
}


class AmbiguousHighValueEvidenceUpgradeV1Test(unittest.TestCase):
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

    def concept_ids_for_layer(self, layer: str) -> set[str]:
        return {
            row["concept_id"]
            for row in self.conn.execute(
                """
                SELECT concept_id
                FROM definition_term_registry
                WHERE promotion_source_layer = ?
                """,
                (layer,),
            )
        }

    def assert_no_forbidden_primary(self, payload: dict, query: str) -> None:
        for item in payload["primary_evidence"]:
            self.assertNotIn(item["record_type"], FORBIDDEN_PRIMARY_TYPES, query)
            self.assertFalse(str(item["record_id"]).startswith("full:passages:"), query)
            self.assertFalse(str(item["record_id"]).startswith("full:ambiguous_passages:"), query)

    def test_batch_registry_counts_and_safe_view(self) -> None:
        safe_ids = self.concept_ids_for_layer("ambiguous_high_value_batch_safe_primary")
        support_ids = self.concept_ids_for_layer("ambiguous_high_value_batch_support_only")
        view_ids = {
            row["concept_id"]
            for row in self.conn.execute(
                """
                SELECT concept_id
                FROM retrieval_ready_definition_view
                WHERE concept_id LIKE 'AHV-%'
                """
            )
        }

        self.assertEqual(len(safe_ids), 20)
        self.assertEqual(len(support_ids), 8)
        self.assertEqual(view_ids, safe_ids)

    def test_review_only_objects_do_not_get_safe_normalization(self) -> None:
        support_ids = self.concept_ids_for_layer("ambiguous_high_value_batch_support_only")
        placeholders = ",".join("?" for _ in support_ids)

        safe_view_conflicts = self.conn.execute(
            f"""
            SELECT COUNT(*)
            FROM retrieval_ready_definition_view
            WHERE concept_id IN ({placeholders})
            """,
            tuple(support_ids),
        ).fetchone()[0]
        learner_conflicts = self.conn.execute(
            f"""
            SELECT COUNT(*)
            FROM learner_query_normalization_lexicon
            WHERE target_id IN ({placeholders})
              AND is_active = 1
            """,
            tuple(support_ids),
        ).fetchone()[0]

        self.assertEqual(safe_view_conflicts, 0)
        self.assertEqual(learner_conflicts, 0)

    def test_risky_and_ambiguous_aliases_are_inactive(self) -> None:
        count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM term_alias_registry
            WHERE source = ?
              AND alias_type IN ('learner_risky', 'ambiguous')
              AND is_active = 1
            """,
            (RUN_ID,),
        ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_representative_a_queries_hit_batch_safe_definition_primary(self) -> None:
        for query, term in REPRESENTATIVE_A_QUERIES.items():
            with self.subTest(query=query):
                payload = self.assembler.assemble(query)
                self.assertEqual(payload["answer_mode"], "strong", query)
                self.assert_no_forbidden_primary(payload, query)
                definition_primary = [
                    item
                    for item in payload["primary_evidence"]
                    if item["record_type"] == "definition_terms"
                    and str(item["record_id"]).startswith("safe:definition_terms:AHV-")
                ]
                self.assertTrue(definition_primary, query)
                self.assertTrue(
                    any(
                        term
                        in " ".join(
                            str(item.get(field) or "")
                            for field in ("title", "snippet", "text")
                        )
                        for item in definition_primary
                    ),
                    query,
                )

    def test_support_only_and_rejected_terms_stay_out_of_runtime_primary(self) -> None:
        b_query = "寸口卫气盛名曰高是什么意思"
        b_retrieval = self.assembler.engine.retrieve(b_query)
        b_payload = self.assembler.assemble(b_query)
        self.assert_no_forbidden_primary(b_payload, b_query)
        self.assertFalse((b_retrieval["query_request"].get("term_normalization") or {}).get("concept_ids"))
        self.assertFalse(any(item["record_type"] == "definition_terms" for item in b_payload["primary_evidence"]))
        self.assertTrue(
            any(
                "ZJSHL-CH-004-P-0208" in str(item.get("record_id"))
                for item in b_payload["secondary_evidence"] + b_payload["review_materials"]
            ),
            b_query,
        )

        c_query = "动是什么意思"
        c_retrieval = self.assembler.engine.retrieve(c_query)
        c_payload = self.assembler.assemble(c_query)
        self.assert_no_forbidden_primary(c_payload, c_query)
        self.assertFalse((c_retrieval["query_request"].get("term_normalization") or {}).get("concept_ids"))
        self.assertFalse(any(item["record_type"] == "definition_terms" for item in c_payload["primary_evidence"]))

    def test_formula_guard_has_no_bad_anchor_or_forbidden_primary(self) -> None:
        query = "桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？"
        retrieval = self.assembler.engine.retrieve(query)
        payload = self.assembler.assemble(query)
        self.assertEqual(payload["answer_mode"], "strong", query)
        self.assert_no_forbidden_primary(payload, query)
        self.assertTrue(payload["primary_evidence"], query)
        self.assertTrue(all(item["record_type"] == "main_passages" for item in payload["primary_evidence"]), query)
        top5_bad_topics = [
            row.get("topic_consistency")
            for row in retrieval["raw_candidates"][:5]
            if row.get("topic_consistency") in BAD_FORMULA_TOPICS
        ]
        self.assertEqual(top5_bad_topics, [], query)

    def test_regression_artifact_records_passed_before_after_metrics(self) -> None:
        regression_path = Path("artifacts/data_plane_batch_upgrade/batch_upgrade_regression_v1.json")
        payload = json.loads(regression_path.read_text(encoding="utf-8"))
        metrics = payload["metrics"]

        self.assertEqual(payload["query_count"], 45)
        self.assertEqual(metrics["candidate_count"], 32)
        self.assertEqual(metrics["promoted_safe_primary_count"], 20)
        self.assertEqual(metrics["support_only_registered_count"], 8)
        self.assertEqual(metrics["rejected_count"], 4)
        self.assertEqual(metrics["new_safe_object_primary_hit_count"], 20)
        self.assertEqual(metrics["forbidden_primary_total"], 0)
        self.assertEqual(metrics["review_only_primary_conflict_count"], 0)
        self.assertEqual(metrics["alias_risk_conflict_count"], 0)
        self.assertEqual(metrics["formula_bad_anchor_top5_total"], 0)
        self.assertEqual(metrics["regression_fail_count"], 0)


if __name__ == "__main__":
    unittest.main()
