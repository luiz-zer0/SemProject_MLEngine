# Data provenance and dataset boundaries


---

## Dataset sources

## Deliverable 3 notebook datasets

`notebooks/NLP_Final.ipynb` profiles the user-provided Office inventory transcription at `data/raw/campus/office_inventory_aggregate.csv`: 33 June–July rows (388 items) and 24 August rows (299 items). Original descriptions, normalized names, broad categories, quantities and disposal fields are retained. The June–July small-umbrella disposal destination is blank in the transcription; confirmation names were not provided. Verify every value with the office before submission. This is aggregate inventory data only: it contains no item-level report text, IDs or verified lost/found links, and is not used as model training or test data.

For model development, the same notebook prepares a separate controlled fictional lost/found benchmark from versioned fixtures. Its generated labels make a repeatable coding exercise, not a real recovery-rate estimate. Review all fictional cases and labels before presentation.

## Historical Delhi source and constructed-label experiment

The repository retains an earlier exploration of the [Delhi Metro Lost and Found dataset on Kaggle](https://www.kaggle.com/datasets/forgetabhi/delhi-metro-lost-and-found-dataset), published by `forgetabhi` and attributed there to Delhi Metro Rail Corporation. Its local original, when separately obtained, is `data/raw/delhi/delhi_lost_and_found.csv`, SHA-256 `38a91688e2ff5acaf1261e8893d006f254cdfd9597d48bc8564a9573f1bf475a`. It has **13,713 found-item rows**, but no corresponding lost claims, return confirmations or verified pairs. Confirm current source terms before redistribution.

`scripts/prepare_delhi_data.py` preserves the raw file and all rows, counts exact duplicates (zero) and missing values (8,208 descriptions; 10,511 quantities), collapses whitespace in a generated copy, adds casefolded text, and parses dates and times. It writes `data/processed/cleaned_items.csv` and a non-sensitive audit at `data/processed/delhi_preprocessing_report.json`. The audit also measures distinct source station strings, distinct whitespace-normalized strings, case-folded strings, and collision groups. In the observed source, all 13,713 station values are non-empty; the 229 distinct source strings remain 229 after whitespace cleanup and case-folding, although 44 rows had whitespace changed. There were zero whitespace or case-fold collision groups, so no semantic station alias mapping is applied: nearby or similarly named stations are not proven equivalent by these records. `station_name` is the receiving station recorded by the source; we do not assert it is the exact loss location. No original colour, brand or model columns exist, so these are left absent.

`scripts/create_delhi_experiment.py` uses seed 42. It selects 120 original found rows across ten frequent item names, creates one **fictional lost claim** per selected row, and makes 360 pair labels: 120 positives by construction, 120 assumed same-name negatives, and 120 assumed other-name negatives. Its generated files are `data/processed/synthetic_delhi_lost_claims.csv`, `data/processed/delhi_labelled_pairs.csv`, `data/processed/delhi_logistic_regression_pairs.csv`, and `data/processed/delhi_logistic_regression_split.json`. Dates and some locations in fictional claims are invented. Colour remains empty. A different found row is **not proof of a different physical item**, so the negative labels need real review before any field claim. The derived row-level files and model outputs are ignored by Git, just like the raw CSV, because found descriptions can contain personal details.

The Delhi preparation and pairing scripts are retained for reproducibility, but the current Deliverable 3 notebook does not require or load this external CSV. The older Delhi metrics test a synthetic pairing exercise only. The four `delhi_*.png` figures contain aggregate EDA counts.

## Data used by the current model

| File | Origin and purpose | What we changed | Limits |
|---|---|---|---|
| `data/raw/campus/synthetic_campus_reports.csv` | 46 **synthetic** lost/found campus reports already in the original project repository. They are examples, not records collected from Strathmore students. The original author and review process are not documented. | The raw file stays unchanged. Six rows have an extra empty CSV field; `scripts/prepare_campus_data.py` repairs the column shift in `data/processed/synthetic_campus_reports.csv`. Text standardisation happens when features are calculated. | A designed sample cannot tell us how often item types, wording, or mistakes occur on campus. |
| `data/raw/campus/labelled_campus_pairs.csv` | 32 designed lost/found pairs already in the repository: 14 `match`, 10 `non_match`, and 8 `plausible`. The original label creator/reviewer is not documented. | The original three-way label is retained. The model's table maps `match` to 1 and both other labels to 0. We also calculate a sensitivity check with `plausible` excluded. | `plausible` means unconfirmed, not proven different. Labels need independent review before real-world claims. |
| `data/raw/campus/office_inventory_aggregate.csv` | User-provided transcription of 33 June–July and 24 August Office category rows. | Original names and quantities are preserved; a normalized item label and broad category are added. Disposal and confirmation fields are recorded only where supplied. | Aggregate quantities only; no item descriptions or match labels. Verify the transcription and do not use counts as individual examples. |

The synthetic source files are part of this project; no external dataset licence is asserted for them. They are separate from aggregate inventory counts and any individual reports. The notebook profiles inventory totals, then prepares the controlled fixture, model features and benchmark results. Generated benchmark files under `data/processed/ranking/` are reproducible from the tracked fixture.

## Earlier Delhi exploration and source caution

The older Delhi pairing experiment remains separate from the Deliverable 3 benchmark. It does not create verified lost/found labels. The earlier dataset note reported Apache 2.0 for the Kaggle listing, but check the current source terms before reuse. A fresh clone requires a separate Delhi download.

## Images are future work

The [Roboflow Lost and Found dataset, version 2](https://universe.roboflow.com/rnomo/lost-and-found-nlb4x-e6ayk/dataset/2) is an **object-detection** dataset, not a set of verified photos of the same lost and found item. Its source page lists 4,546 images and CC BY 4.0. No images or annotations from it are included here, and no image model has been trained or evaluated in this repository. If the team later uses it, cite the creator, follow the licence, inspect the downloaded annotations, and define exactly what detection contributes to matching. To evaluate image matching, first collect consented photos with stable physical-item IDs and independent pair labels.

## Splits and leakage

`scripts/split_logistic_regression_data.py` uses seed 42 and groups all candidates for one lost report together. The development set has 24 pairs from 10 lost reports; the held-out test has 8 pairs from 4 different lost reports. Found IDs do not cross those partitions. Grouped cross-validation is applied only to development. This reduces repeated-description leakage, but the small synthetic test is still only a prototype check.

Run `python -m scripts.validate_delhi_experiment` after generating the Delhi experiment files to check that each synthetic lost claim has exactly three candidate pairs (one `constructed_positive` and two `assumed_*` negatives), found IDs are unique, lost and found IDs are covered by only one development/test split, and each manifest pair count matches the pair table. The focused `python -m unittest tests.test_delhi_validator` tests these checks with temporary CSV and JSON fixtures and needs no private Delhi CSV or download. A pass establishes only these structural properties: different source-row IDs may still refer to the same physical item, and the validator cannot verify that an assumed negative is truly negative.

---

## Synthetic campus data audit

46 synthetic reports: 14 lost, 32 found. 32 designed pairs: 14 match,
8 plausible, 10 non_match. Ledger contains 46 report rows and 32 pair rows; three
additional synthetic queries cover wording variation, similar items and no match.
Raw files remain unchanged. No real-campus accuracy is claimed.

Plausible is uncertain, excluded from binary metrics. All labels are synthetic
design assertions awaiting independent review, including non_match. Proposed
physical groups are provisional: join the report groups identified by each
match pair before grouped holdout; unresolved pairs must be adjudicated.
Missing evidence: real reports, consent, collection provenance, independent
review, verified ownership/identity, verified negatives and representative coverage.

## Real intake

CSV templates are headers only; JSON arrays are empty. Use CSV field names
as keys of objects in reports and pairs. Require unique IDs, report_type
lost/found, nonempty description, ISO 8601 dates with offset and source reference.
Pair references must resolve to a lost and a found report. Labels are match,
non_match or uncertain. Verified labels require reviewer, review timestamp,
verification method and evidence reference; pending records stay uncertain.
Keep private IDs and contact details out of model text; use protected evidence
references. Obtain consent before using real reports. Never fabricate evidence.

Legacy loader mapping: report_id, report_type and description map directly;
item_name maps to category as temporary legacy fallback only. Free-text location
is not a validated location_id; reported_at is not verified event_date.
Fit only on found inventory and rebuild on changes, as described in [the system guide](system_guide.md).
Evaluate ranking separately; use reviewed physical-item groups for holdout.
Synthetic fixtures cannot establish real-campus matching accuracy.

Initial audit checks: ledger coverage 78 rows; uncertain mapping 8; 46 unique report IDs; pair references resolve; three query rows; JSON parses. These checks validate structure, not the truth of the designed labels.
