"""Compare ranking methods on one frozen, fictional candidate pool."""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

from matching_system.feature_builder import FEATURE_NAMES, pair_features
from matching_system.models import Report
from scripts.validate_ranking_dataset import validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "ranking"
RESULT = ROOT / "results" / "ranking_benchmark.json"


def rows(name):
    with (DATA / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def tokens(value):
    from matching_system.nlp_retrieval import normalize_report_text
    return set(normalize_report_text(value).split())


def keyword(lost, found):
    left, right = tokens(lost["description"]), tokens(found["description"])
    return len(left & right) / len(left | right) if left and right else 0.0


def attributes(lost, found):
    score = 0.0
    for field, weight in (("category", 0.5), ("colour", 0.25), ("brand", 0.25)):
        a, b = lost.get(field, "").casefold(), found.get(field, "").casefold()
        if a and b:
            score += weight if a == b else -weight
    return max(0.0, score)


def as_report(row, kind):
    return Report(report_id=row[f"{kind}_id"], report_type=kind, description=row["description"],
                  category=row["category"], colour=row.get("colour", ""), brand=row.get("brand", ""),
                  location=row.get("last_seen_location" if kind == "lost" else "location", ""))


def ranking_metrics(queries, scores, found_ids):
    matched, unmatched = [], []
    for query in queries:
        ranked = sorted(found_ids, key=lambda fid: (-scores[(query["lost_id"], fid)], fid))
        relevant = set(filter(None, query["relevant_found_ids"].split("|")))
        top = scores[(query["lost_id"], ranked[0])] if ranked else 0.0
        if relevant:
            positions = [i + 1 for i, fid in enumerate(ranked) if fid in relevant]
            matched.append({"query_id": query["query_id"], "first_rank": min(positions) if positions else None,
                            "recall_at_5": len([p for p in positions if p <= 5]) / len(relevant)})
        else:
            unmatched.append({"query_id": query["query_id"], "top_score": top})
    n = len(matched)
    return {"matched_queries": n, "no_match_queries": len(unmatched), "candidate_pool_size": len(found_ids),
            "top1_accuracy": sum(row["first_rank"] == 1 for row in matched) / n if n else None,
            "recall_at_5": sum(row["recall_at_5"] for row in matched) / n if n else None,
            "mrr": sum(1 / row["first_rank"] if row["first_rank"] else 0 for row in matched) / n if n else None,
            "matched_details": matched, "no_match_details": unmatched}


def main():
    audit = validate(DATA)
    if not audit["valid"]:
        raise ValueError(audit["errors"])
    found = {row["found_id"]: row for row in rows("found_reports.csv")}
    lost = {row["lost_id"]: row for row in rows("lost_reports.csv")}
    labels = rows("match_labels.csv")
    queries = rows("evaluation_queries.csv")
    pools = json.loads((DATA / "candidate_pools.json").read_text(encoding="utf-8"))
    if len(pools) != 1 or len({q["candidate_pool_id"] for q in queries}) != 1:
        raise ValueError("This comparison expects one frozen candidate pool")
    found_ids = next(iter(pools.values()))
    train_found = [row for row in found.values() if row["split"] == "train"]
    train_lost = [row for row in lost.values() if row["split"] == "train"]
    if not train_found or not train_lost:
        raise ValueError("Training reports are required")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")
    vectorizer.fit([r["description"] for r in train_found + train_lost])
    found_matrix = vectorizer.transform([found[fid]["description"] for fid in found_ids])
    lost_matrix = vectorizer.transform([lost[q["lost_id"]]["description"] for q in queries])
    cosine = cosine_similarity(lost_matrix, found_matrix)
    feature_cache = {}
    for q in queries:
        for fid in found_ids:
            key = (q["lost_id"], fid)
            feature_cache[key] = pair_features(as_report(lost[key[0]], "lost"), as_report(found[fid], "found"))
    training = [row for row in labels if row["split"] == "train" and row["label"] in {"0", "1"}]
    x_train = np.array([[feature_cache[(r["lost_id"], r["found_id"])][name] for name in FEATURE_NAMES] for r in training])
    y_train = np.array([int(r["label"]) for r in training])
    classifier = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42).fit(x_train, y_train)
    all_keys = list(feature_cache)
    x_all = np.array([[feature_cache[key][name] for name in FEATURE_NAMES] for key in all_keys])
    classifier_scores = dict(zip(all_keys, classifier.predict_proba(x_all)[:, 1]))
    scores = {name: {} for name in ("keyword", "attributes", "logistic_regression", "tfidf", "hybrid")}
    for qi, q in enumerate(queries):
        for fi, fid in enumerate(found_ids):
            key = (q["lost_id"], fid)
            scores["keyword"][key] = keyword(lost[key[0]], found[fid])
            scores["attributes"][key] = attributes(lost[key[0]], found[fid])
            scores["logistic_regression"][key] = float(classifier_scores[key])
            scores["tfidf"][key] = float(cosine[qi, fi])
    validation = [q for q in queries if q["split"] == "validation"]
    choices = []
    for weight in (0.25, 0.5, 0.75):
        candidate = {key: weight * scores["tfidf"][key] + (1 - weight) * scores["attributes"][key] for key in all_keys}
        metric = ranking_metrics(validation, candidate, found_ids)
        choices.append((metric["recall_at_5"], metric["mrr"], weight, candidate))
    _, _, weight, scores["hybrid"] = max(choices, key=lambda item: (item[0], item[1], -item[2]))
    output = {"provenance": "AI-authored controlled fiction; no real-campus accuracy claim",
              "dataset": audit["counts"], "sklearn_version": sklearn.__version__,
              "tfidf": {"fit_split": "train", "ngram_range": [1, 2], "vocabulary_size": len(vectorizer.vocabulary_)},
              "logistic_regression": {"fit_split": "train", "pair_count": len(training), "features": list(FEATURE_NAMES)},
              "hybrid": {"tfidf_weight_selected_on_validation": weight}, "methods": {}}
    for name, method_scores in scores.items():
        val = ranking_metrics(validation, method_scores, found_ids)
        no_match_top = [row["top_score"] for row in val["no_match_details"]]
        threshold = max(no_match_top, default=0.0) + 1e-9
        test = ranking_metrics([q for q in queries if q["split"] == "test"], method_scores, found_ids)
        false_suggestions = sum(row["top_score"] >= threshold for row in test["no_match_details"])
        output["methods"][name] = {"validation": val, "test": test,
                                    "strong_match_threshold_from_validation": threshold,
                                    "test_no_match_false_suggestions": false_suggestions,
                                    "test_no_match_denominator": test["no_match_queries"]}
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: info["test"] for name, info in output["methods"].items()}, indent=2))


if __name__ == "__main__":
    main()
