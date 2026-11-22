import unittest

from service.inference import TfidfMatcher


class TfidfMatcherCacheTests(unittest.TestCase):
    def test_reuses_inventory_and_refreshes_changed_text(self):
        matcher = TfidfMatcher()
        lost = {"id": "l1", "report_type": "lost", "description": "blue bottle"}
        found = {"id": "f1", "report_type": "found", "description": "blue bottle"}
        self.assertEqual(matcher.recommend(lost, [found])[0]["found_report_id"], "f1")
        pipeline = matcher._pipeline
        matcher.recommend(lost, [dict(found)])
        self.assertIs(matcher._pipeline, pipeline)
        matcher.recommend(lost, [{**found, "description": "red umbrella"}])
        self.assertIsNot(matcher._pipeline, pipeline)
        self.assertEqual(matcher.recommend(lost, [{**found, "description": "red umbrella"}]), [])


if __name__ == "__main__":
    unittest.main()
