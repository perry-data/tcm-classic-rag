import csv
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "eval" / "eval_dataset_v1.csv"
SUMMARY_JSON = (
    ROOT
    / "artifacts"
    / "eval"
    / "eval_dataset_v1"
    / "eval_dataset_summary_v1.json"
)
VALIDATOR = ROOT / "scripts" / "eval" / "validate_eval_dataset_v1.py"

REQUIRED_FIELDS = {
    "id",
    "category",
    "question",
    "gold_chunk_ids",
    "gold_answer",
    "should_answer",
}
ALLOWED_CATEGORIES = {
    "原文定位",
    "术语解释",
    "方剂关联",
    "症候检索",
    "注文理解",
    "超范围拒答",
}
P2_QUERIES = {
    "少阴病是什么意思",
    "半表半里证和过经有什么不同",
    "荣气微和卫气衰有什么区别",
    "霍乱和伤寒有什么区别",
    "痓病和太阳病有什么不同",
}


def load_rows() -> list[dict[str, str]]:
    with DATASET.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class EvalDatasetV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_rows()

    def test_dataset_exists_and_has_required_fields(self) -> None:
        self.assertTrue(DATASET.exists())
        with DATASET.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertTrue(REQUIRED_FIELDS.issubset(set(reader.fieldnames or [])))

    def test_dataset_size_and_category_coverage(self) -> None:
        self.assertGreaterEqual(len(self.rows), 36)
        self.assertLessEqual(len(self.rows), 42)
        counts = Counter(row["category"] for row in self.rows)
        self.assertEqual(set(counts), ALLOWED_CATEGORIES)
        for category in ALLOWED_CATEGORIES:
            self.assertGreaterEqual(counts[category], 5)

    def test_ids_questions_and_should_answer_values(self) -> None:
        ids = [row["id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(row["question"].strip() for row in self.rows))
        should_answer_values = {row["should_answer"] for row in self.rows}
        self.assertLessEqual(should_answer_values, {"true", "false"})
        self.assertGreaterEqual(
            sum(1 for row in self.rows if row["should_answer"] == "false"),
            5,
        )

    def test_p2_residual_queries_are_included(self) -> None:
        questions = {row["question"] for row in self.rows}
        self.assertLessEqual(P2_QUERIES, questions)

    def test_manual_audit_rows_are_not_ordinary_gold_pass_rows(self) -> None:
        manual_rows = [
            row for row in self.rows if row.get("manual_audit_required") == "true"
        ]
        self.assertGreaterEqual(len(manual_rows), len(P2_QUERIES))
        for row in manual_rows:
            self.assertIn(row["question"], P2_QUERIES)
            self.assertEqual(row["gold_chunk_ids"], "")
            self.assertIn("manual audit", row["notes"].lower())

    def test_summary_json_is_valid_and_dataset_valid_true(self) -> None:
        summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        self.assertTrue(summary["dataset_valid"])
        self.assertEqual(summary["total_examples"], len(self.rows))

    def test_validator_cli_accepts_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--dataset",
                    str(DATASET.relative_to(ROOT)),
                    "--out-dir",
                    temp_dir,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary_path = Path(temp_dir) / "eval_dataset_summary_v1.json"
            self.assertTrue(json.loads(summary_path.read_text(encoding="utf-8"))["dataset_valid"])


if __name__ == "__main__":
    unittest.main()
