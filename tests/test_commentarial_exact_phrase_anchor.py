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


class CommentarialExactPhraseAnchorTest(unittest.TestCase):
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

    def test_cheng_wuji_quoted_phrase_anchors_to_exact_main_and_annotation(self) -> None:
        payload = self.assembler.assemble("成无己如何解释“太阳之为病”？")

        self.assertEqual(payload["answer_mode"], "strong")
        self.assertEqual(payload["primary_evidence"][0]["record_id"], "safe:main_passages:ZJSHL-CH-008-P-0191")
        self.assertEqual(
            payload["secondary_evidence"][0]["record_id"],
            "full:annotations:ZJSHL-CH-008-P-0192",
        )
        self.assertIn("太阳之为病，脉浮，头项强痛而恶寒", payload["answer_text"])
        self.assertIn("太阳表病也", payload["answer_text"])
        self.assertNotIn("湿家之为病", "\n".join(item["snippet"] for item in payload["primary_evidence"]))

    def test_cheng_wuji_unquoted_six_stage_topic_uses_narrow_fallback_anchor(self) -> None:
        payload = self.assembler.assemble("成无己注文怎么看太阳病？")

        self.assertEqual(payload["primary_evidence"][0]["record_id"], "safe:main_passages:ZJSHL-CH-008-P-0191")
        self.assertEqual(
            payload["secondary_evidence"][0]["record_id"],
            "full:annotations:ZJSHL-CH-008-P-0192",
        )


if __name__ == "__main__":
    unittest.main()
