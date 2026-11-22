"""Serve the existing feature pipeline; never train on incoming app reports."""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from matching_system.feature_builder import FEATURE_NAMES, pair_features
from matching_system.models import Report


def as_report(row):
    fields = {key: row.get(key, "") for key in ("description", "brand", "model", "colour", "material")}
    return Report(
        report_id=row["id"], report_type=row["report_type"], **fields,
        category=row["category_id"], location=row["location_id"],
        distinctive_features=tuple(row.get("distinctive_features", [])),
        reported_at=datetime.fromisoformat(row["event_date"]).replace(tzinfo=timezone.utc),
    )


class Matcher:
    def __init__(self, path):
        # Only load a locally trained, trusted artifact: joblib can execute code.
        artifact = joblib.load(Path(path))
        if artifact["features"] != list(FEATURE_NAMES):
            raise ValueError("Model feature schema mismatch")
        self.classifier = artifact["classifier"]
        self.version = artifact["version"]

    def score(self, lost, found):
        features = pair_features(as_report(lost), as_report(found))
        table = pd.DataFrame([features], columns=list(FEATURE_NAMES))
        return float(self.classifier.predict_proba(table)[0, 1])


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
