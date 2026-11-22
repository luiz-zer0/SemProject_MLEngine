import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_ranking_dataset import validate


class RankingDatasetValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("found_reports.csv", ["found_id", "item_group_id", "category", "description", "source_type"],
                   [["f1", "g1", "bottle", "blue bottle", "constructed"],
                    ["f2", "g2", "bottle", "green bottle", "constructed"]])
        self.write("lost_reports.csv", ["lost_id", "item_group_id", "category", "description", "source_type"],
                   [["l1", "g1", "bottle", "my blue flask", "constructed"]])
        self.write("match_labels.csv", ["lost_id", "found_id", "label", "label_source", "item_group_id", "reviewer", "split"],
                   [["l1", "f1", "1", "controlled", "g1", "reviewer1", "test"],
                    ["l1", "f2", "0", "controlled", "g1", "reviewer1", "test"]])
        self.write("evaluation_queries.csv", ["query_id", "lost_id", "relevant_found_ids", "candidate_pool_id", "has_match", "split"],
                   [["q1", "l1", "f1", "pool1", "1", "test"]])
        (self.root / "candidate_pools.json").write_text(json.dumps({"pool1": ["f1", "f2"]}), encoding="utf-8")

    def write(self, name, header, rows):
        with (self.root / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)

    def test_valid_constructed_fixture(self):
        self.assertTrue(validate(self.root)["valid"])

    def test_positive_identity_mismatch(self):
        self.write("match_labels.csv", ["lost_id", "found_id", "label", "label_source", "item_group_id", "reviewer", "split"],
                   [["l1", "f2", "1", "controlled", "g1", "reviewer1", "test"]])
        self.assertTrue(any("positive crosses" in issue for issue in validate(self.root)["errors"]))

    def test_cross_split_identity_leakage(self):
        self.write("match_labels.csv", ["lost_id", "found_id", "label", "label_source", "item_group_id", "reviewer", "split"],
                   [["l1", "f1", "1", "controlled", "g1", "reviewer1", "train"],
                    ["l1", "f2", "0", "controlled", "g1", "reviewer1", "test"]])
        self.assertTrue(any("crosses splits" in issue for issue in validate(self.root)["errors"]))


if __name__ == "__main__":
    unittest.main()
