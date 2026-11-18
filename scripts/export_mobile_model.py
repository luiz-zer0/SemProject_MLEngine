"""Export development-only classifier; do not change existing experiment results."""
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd

from matching_system.feature_builder import FEATURE_NAMES
from matching_system.ml_model import new_classifier


def main():
    root = Path(__file__).resolve().parents[1]
    table_path = root / "data/processed/modelling_pairs.csv"
    split_path = root / "data/processed/campus_split.json"
    table = pd.read_csv(table_path)
    split = json.loads(split_path.read_text())["splits"]
    train = table[table.lost_report_id.isin(split["development"]["lost_ids"])]
    test = table[table.lost_report_id.isin(split["test"]["lost_ids"])]
    if set(train.lost_report_id) & set(test.lost_report_id) or set(train.found_report_id) & set(test.found_report_id):
        raise ValueError("Training/test leakage")
    if set(train.target) != {0, 1}:
        raise ValueError("Development data needs both classes")
    version = "campus-demo-" + hashlib.sha256(table_path.read_bytes() + split_path.read_bytes()).hexdigest()[:12]
    artifact = {"classifier": new_classifier().fit(train[list(FEATURE_NAMES)], train.target),
                "features": list(FEATURE_NAMES), "version": version}
    destination = root / "artifacts/mobile_model.joblib"
    destination.parent.mkdir(exist_ok=True)
    joblib.dump(artifact, destination)
    print(f"Exported {version} from {len(train)} development pairs to {destination}")
    print("Constructed coursework labels only; scores are not ownership probabilities or field validation.")


if __name__ == "__main__":
    main()
