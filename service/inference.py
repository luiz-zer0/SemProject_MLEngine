"""Operational text retrieval; the historical classifier remains in matching_system and the baseline notebook."""


class TfidfMatcher:
    """Use the shared NLP and knowledge-agent pipeline for mobile suggestions."""
    version = "tfidf-knowledge-agents-v1"

    def __init__(self):
        self._inventory_key = None
        self._pipeline = None

    def recommend(self, lost, found_rows):
        from matching_system.nlp_retrieval import TextReport
        from matching_system.pipeline import MatchingPipeline

        def convert(row):
            return TextReport(row["id"], row["report_type"], row.get("description", ""),
                              item_name=row.get("item_name", ""), category_id=row.get("category_id"),
                              location_id=row.get("location_id"), event_date=row.get("event_date"))

        found_reports = [convert(row) for row in found_rows]
        inventory_key = tuple(sorted(found_reports, key=lambda report: report.report_id))
        if inventory_key != self._inventory_key:
            self._pipeline = MatchingPipeline(found_reports)
            self._inventory_key = inventory_key
        return self._pipeline.recommend(convert(lost), limit=5)["matches"]
