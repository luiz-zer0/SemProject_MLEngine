"""Validate a proposed ranking benchmark without treating constructed labels as verified."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


SCHEMAS = {
    "found_reports.csv": {"found_id", "item_group_id", "category", "description", "source_type"},
    "lost_reports.csv": {"lost_id", "item_group_id", "category", "description", "source_type"},
    "match_labels.csv": {"lost_id", "found_id", "label", "label_source", "item_group_id", "reviewer", "split"},
    "evaluation_queries.csv": {"query_id", "lost_id", "relevant_found_ids", "candidate_pool_id", "has_match", "split"},
}
SPLITS = {"train", "validation", "test"}


def read_table(directory: Path, filename: str) -> list[dict[str, str]]:
    with (directory / filename).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = SCHEMAS[filename] - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{filename}: missing columns {sorted(missing)}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def validate(directory: Path) -> dict:
    tables = {name: read_table(directory, name) for name in SCHEMAS}
    errors: list[str] = []
    found, lost, labels, queries = (tables[name] for name in SCHEMAS)
    for name, rows, key in (("found", found, "found_id"), ("lost", lost, "lost_id"),
                            ("query", queries, "query_id")):
        ids = [row[key] for row in rows]
        if not all(ids) or len(ids) != len(set(ids)):
            errors.append(f"{name}: blank or duplicate IDs")
    found_by_id = {row["found_id"]: row for row in found}
    lost_by_id = {row["lost_id"]: row for row in lost}
    pool_path = directory / "candidate_pools.json"
    pools = json.loads(pool_path.read_text(encoding="utf-8")) if pool_path.exists() else {}
    if not pools:
        errors.append("candidate_pools.json: missing or empty")
    for pool_id, ids in pools.items():
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or set(ids) - set(found_by_id):
            errors.append(f"candidate pool {pool_id}: empty, duplicate, or unknown found IDs")
    for name, rows, key in (("found", found, "found_id"), ("lost", lost, "lost_id")):
        for row in rows:
            if not row["item_group_id"] or not row["category"] or not row["description"] or not row["source_type"]:
                errors.append(f"{name} {row[key]}: missing required provenance or item fields")
    group_splits: dict[str, set[str]] = defaultdict(set)
    pair_labels: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in labels:
        pair = (row["lost_id"], row["found_id"])
        pair_labels[pair].add(row["label"])
        if row["label"] not in {"0", "1", "unresolved"} or row["split"] not in SPLITS:
            errors.append(f"label {pair}: invalid label or split")
        left, right = lost_by_id.get(pair[0]), found_by_id.get(pair[1])
        if left is None or right is None:
            errors.append(f"label {pair}: unknown report")
            continue
        if row["item_group_id"] != left["item_group_id"]:
            errors.append(f"label {pair}: group differs from lost report")
        if row["label"] == "1" and left["item_group_id"] != right["item_group_id"]:
            errors.append(f"label {pair}: positive crosses item identities")
        if row["label"] == "0" and left["item_group_id"] == right["item_group_id"]:
            errors.append(f"label {pair}: negative shares item identity")
        group_splits[left["item_group_id"]].add(row["split"])
        group_splits[right["item_group_id"]].add(row["split"])
        if not row["label_source"]:
            errors.append(f"label {pair}: missing label provenance")
        if not row["reviewer"]:
            errors.append(f"label {pair}: missing reviewer")
    for pair, values in pair_labels.items():
        if len(values) > 1 or sum((row["lost_id"], row["found_id"]) == pair for row in labels) > 1:
            errors.append(f"label {pair}: duplicate or contradictory labels")
    for group, splits in group_splits.items():
        if len(splits) > 1:
            errors.append(f"item group {group}: crosses splits {sorted(splits)}")
    for row in queries:
        query_id, lost_id = row["query_id"], row["lost_id"]
        if lost_id not in lost_by_id or row["split"] not in SPLITS:
            errors.append(f"query {query_id}: unknown lost report or invalid split")
            continue
        group = lost_by_id[lost_id]["item_group_id"]
        if group in group_splits and row["split"] not in group_splits[group]:
            errors.append(f"query {query_id}: split disagrees with labels")
        if row["has_match"] not in {"0", "1"}:
            errors.append(f"query {query_id}: invalid has_match")
        relevant = [part.strip() for part in row["relevant_found_ids"].split("|") if part.strip()]
        if (row["has_match"] == "1") != bool(relevant):
            errors.append(f"query {query_id}: relevant IDs disagree with has_match")
        for found_id in relevant:
            if pair_labels.get((lost_id, found_id)) != {"1"}:
                errors.append(f"query {query_id}: relevant item lacks a positive label")
        pool = pools.get(row["candidate_pool_id"])
        if pool is None:
            errors.append(f"query {query_id}: candidate pool missing")
        elif any(found_id not in pool for found_id in relevant):
            errors.append(f"query {query_id}: relevant found item absent from pool")
    return {"counts": {name: len(rows) for name, rows in tables.items()},
            "label_counts": dict(Counter(row["label"] for row in labels)),
            "errors": errors, "valid": not errors,
            "note": "Structural checks do not verify physical identity, independent authorship, or label truth."}


if __name__ == "__main__":
    result = validate(Path(sys.argv[1] if len(sys.argv) > 1 else "data/ranking"))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)
