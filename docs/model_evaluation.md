# Model evaluation and ranking benchmark


---

## Benchmark results and limitations

The earlier tracked campus files contain 46 synthetic reports and 32 designed pairs. They are not 46 verified physical items or independently checked matches. On 23 November, the user transcribed two Lost and Found Office category tables into the chat. The transcription is preserved in `data/raw/campus/office_inventory_aggregate.csv`: 33 June–July rows total 388 quantities, and 24 August rows total 299 quantities. The combined quantity is 687. The linked Google Docs returned permission denied to the connected account, so this transcription has not been checked against the original files. It contains categories and quantities only. Do not turn those counts into individual found records.

`scripts/prepare_ranking_benchmark.py` builds a separate fictional exercise from `data/fixtures/ranking/controlled_items.csv` and `no_match_queries.csv`. Those descriptions were AI authored as development examples; no team member has yet reviewed them independently. The output has 24 found records, 27 lost queries (three intentionally absent), 24 controlled positives and 168 controlled negatives among same-split item groups. Every query uses the explicit 24-item pool in `candidate_pools.json`. This is smaller than the earlier 120-query target to avoid multiplying repetitive synthetic examples.

`scripts/validate_ranking_dataset.py` accepts the four generated CSVs and `candidate_pools.json`. The required columns are listed in `SCHEMAS`. Put multiple relevant found IDs in `relevant_found_ids` with `|` between IDs. Run `python -m scripts.validate_ranking_dataset data/processed/ranking`. The command prints counts and errors and returns a nonzero exit code for structural failures. It checks references, positive and negative group consistency, duplicate labels, split leakage among labelled groups, candidate pool references and query relevance. It does not establish whether a controlled group truly describes one physical item, whether a negative is defensible, or whether each description was independently authored. Independent label review is required before using the benchmark as assessed evidence.

`scripts/evaluate_ranking_benchmark.py` evaluates the fixed pool with keyword overlap, attribute scoring, Logistic Regression, TF-IDF cosine similarity and a weighted hybrid. TF-IDF vocabulary and classifier are fitted using training rows only. The hybrid weight and strong-suggestion thresholds are selected on validation queries, then test metrics are calculated once. All measured values describe controlled fiction, never campus recovery rates.

Measured test results (eight matched queries, two no-match queries, 24 candidates per query):

| Method | Top-1 | Recall@5 | MRR | False strong suggestions |
| --- | ---: | ---: | ---: | ---: |
| Keyword overlap | 0.250 | 0.875 | 0.541 | 1/2 |
| Structured attributes | 1.000 | 1.000 | 1.000 | 1/2 |
| Logistic Regression pair baseline | 1.000 | 1.000 | 1.000 | 1/2 |
| TF-IDF cosine | 0.250 | 0.500 | 0.391 | 2/2 |
| Hybrid, TF-IDF weight 0.25 | 1.000 | 1.000 | 1.000 | 2/2 |

The attribute scores are inflated because each fictional lost record was constructed with category, colour and brand copied from its found record. This is a benchmark weakness, not a measured improvement in real matching. The test results have now been inspected; do not tune on this test set. A newly authored and independently reviewed frozen set is needed for a stronger claim. TF-IDF fitting on only eight training item groups leaves many useful test terms outside its vocabulary. The no-match failure counts show why the service must avoid confident ownership language.

The team's next data steps are to inspect the original office inventory under its access terms, record only observed fields, and have members independently author controlled fictional reports if no individual authorized records exist. Record author, source type, label reviewer and exclusions. Freeze candidate pools and group assignments before comparing keyword, weighted attributes, Logistic Regression, TF-IDF and hybrid ranking on the same held-out queries. Fit learned vocabulary and weights on training groups; tune on validation groups; use test groups once for final reporting. Report the actual query count and pool sizes, including no-match queries.

The service worker currently uses `TfidfMatcher` in `service/worker.py`, which calls `MatchingPipeline`; the unused service classifier adapter has been removed. The original classifier, feature engineering, data and baseline notebook remain in the historical experiment. `TfidfMatcher` now reuses its index while the complete found-report snapshot is unchanged and rebuilds it when a report changes. A larger Firestore inventory still needs paginated retrieval and a durable index. The API has authenticated report persistence and staff review paths, but this checkout has no verified end-to-end Android-to-Firebase-to-worker run. The final notebook was executed successfully; section 7A reports Top-1 4/8 (50%), Recall@5 7/8 (87.5%), MRR@5 0.629, and suggestions on both unmatched queries. This operational test uses the same TfidfMatcher as the worker, not the offline cutoff. The local backend smoke test passed; Android device rehearsal and independent label review remain required.
