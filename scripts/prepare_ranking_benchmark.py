"""Build a small, explicitly fictional ranking exercise from authored fixtures."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "fixtures" / "ranking"
OUTPUT = ROOT / "data" / "processed" / "ranking"


def read(name):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write(name, fields, rows):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    items = read("controlled_items.csv")
    absent = read("no_match_queries.csv")
    if len({item["item_group_id"] for item in items}) != len(items):
        raise ValueError("Controlled item groups must be unique")
    inventory = read("../../raw/campus/office_inventory_aggregate.csv")
    quantities = Counter()
    for row in inventory:
        quantities[row["period"]] += int(row["quantity"])
    if dict(quantities) != {"2026-06_07": 388, "2026-08": 299}:
        raise ValueError(f"Aggregate transcription does not reconcile: {dict(quantities)}")
    found = []
    lost = []
    labels = []
    queries = []
    for item in items:
        group = item["item_group_id"]
        found.append(dict(found_id=f"f-{group}", item_group_id=group, category=item["category"],
                          description=item["found_description"], colour=item["colour"], brand=item["brand"],
                          distinguishing_attributes="", location=item["location"], event_date="",
                          report_status="active", source_type=item["source_type"], split=item["split"]))
        lost.append(dict(lost_id=f"l-{group}", item_group_id=group, category=item["category"],
                         description=item["lost_description"], colour=item["colour"], brand=item["brand"],
                         last_seen_location=item["location"], date_lost="", source_type=item["source_type"],
                         split=item["split"]))
    for item in items:
        group, split = item["item_group_id"], item["split"]
        lost_id = f"l-{group}"
        for candidate in items:
            if candidate["split"] != split:
                continue
            same = candidate["item_group_id"] == group
            labels.append(dict(lost_id=lost_id, found_id=f"f-{candidate['item_group_id']}",
                               label=int(same), label_source="controlled_fictional_identity",
                               item_group_id=group, reviewer="pending_independent_review", split=split))
        queries.append(dict(query_id=f"q-{group}", lost_id=lost_id, relevant_found_ids=f"f-{group}",
                            candidate_pool_id="all_constructed_found_v1", has_match=1, split=split))
    for row in absent:
        lost.append(dict(lost_id=row["lost_id"], item_group_id=row["lost_id"], category=row["category"],
                         description=row["description"], colour=row["colour"], brand=row["brand"],
                         last_seen_location=row["location"], date_lost="", source_type=row["source_type"],
                         split=row["split"]))
        queries.append(dict(query_id=f"q-{row['lost_id']}", lost_id=row["lost_id"], relevant_found_ids="",
                            candidate_pool_id="all_constructed_found_v1", has_match=0, split=row["split"]))
    write("found_reports.csv", list(found[0]), found)
    write("lost_reports.csv", list(lost[0]), lost)
    write("match_labels.csv", list(labels[0]), labels)
    write("evaluation_queries.csv", list(queries[0]), queries)
    (OUTPUT / "candidate_pools.json").write_text(json.dumps({"all_constructed_found_v1": [r["found_id"] for r in found]}, indent=2) + "\n", encoding="utf-8")
    audit = {"inventory_quantities": dict(quantities), "found_records": len(found),
             "lost_reports": len(lost), "controlled_positive_labels": len(items),
             "controlled_negative_labels": len(labels) - len(items), "no_match_queries": len(absent),
             "candidate_pool_size": len(found), "source_type": "AI-authored fictional controlled examples",
             "review": "Independent student review pending; no genuine same-item labels or campus performance."}
    (OUTPUT / "provenance.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
