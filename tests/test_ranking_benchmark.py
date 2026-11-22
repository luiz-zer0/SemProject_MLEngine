import unittest

from scripts.evaluate_ranking_benchmark import ranking_metrics


class RankingMetricsTests(unittest.TestCase):
    def test_rank_and_no_match_denominators(self):
        queries = [
            {"query_id": "q1", "lost_id": "l1", "relevant_found_ids": "f2", "has_match": "1"},
            {"query_id": "q2", "lost_id": "l2", "relevant_found_ids": "", "has_match": "0"},
        ]
        scores = {("l1", "f1"): 0.9, ("l1", "f2"): 0.5,
                  ("l2", "f1"): 0.1, ("l2", "f2"): 0.2}
        result = ranking_metrics(queries, scores, ["f1", "f2"])
        self.assertEqual(result["matched_queries"], 1)
        self.assertEqual(result["no_match_queries"], 1)
        self.assertEqual(result["top1_accuracy"], 0)
        self.assertEqual(result["recall_at_5"], 1)
        self.assertEqual(result["mrr"], 0.5)
        self.assertEqual(result["no_match_details"][0]["top_score"], 0.2)


if __name__ == "__main__":
    unittest.main()
