# Deliverable 3 technical audit and handover

Review date: 24 November 2026. This is a technical review for the team to inspect and correct; it is not a student-authored submission or a claim that the assessment is complete. Subsequent documentation consolidation changed Markdown paths and names; project data and source were retained.

## A. Rubric compliance

| Area | Status | Current evidence | Remaining action / demonstration |
| --- | --- | --- | --- |
| Data collection | PARTIAL | The user-provided Office transcription is now structured in `data/raw/campus/office_inventory_aggregate.csv`: 33 June–July rows (388 items) and 24 August rows (299 items), with normalized names and the supplied disposal value retained. The records are aggregate, not individual reports. | Verify the transcription and usage terms with the Office. Obtain consented, privacy-reviewed item-level reports and verified same-item links before making real-case claims. |
| Data cleaning | PARTIAL | Preparation scripts and structural validators exist; synthetic ranking data is reproducible from controlled fixtures. The Delhi raw CSV is not part of a fresh clone. | Reproduce the Delhi cleaning only after obtaining the source file and confirming its current terms. Keep row-level derivatives local where required. |
| NLP preprocessing | PASS for the prototype | `matching_system/nlp_retrieval.py` normalizes report text and ranks with word and bigram TF-IDF over found reports. | Explain the actual settings and lexical limits in the notebook; do not describe similarity as probability. |
| Baseline model | PASS | The prior Logistic Regression notebook and implementation remain available, with saved campus baseline outputs. | Present it as the baseline/coursework experiment, not the authenticated worker model. |
| Final matching approach | PASS for the stated text-only scope | The TF-IDF ranker, matching agent, staff-workflow agent, local preview API, and Firebase worker exist. `NLP_Final.ipynb` documents the NLP approach and names TF-IDF as the specific retrieval method. | Team review the notebook and ensure its demonstrated method agrees with the mobile service. No CLIP/image method is used. |
| Training / fitting | PASS for the prototype | The benchmark fits TF-IDF and Logistic Regression on grouped synthetic training data and chooses a hybrid weight on validation data. The live worker fits a lexical index on found inventory; it does not load the Logistic Regression artifact. | The team should explain why TF-IDF retrieval is the runtime method and keep the offline classifier labeled as a comparison. |
| Validation and evaluation | PASS for the fictional benchmark | A reproducible, grouped fictional benchmark compares five methods on a 24-item pool. The held-out set contains eight matched queries and two no-match queries. | Review the authored examples, labels, groups, false suggestions, and limitations. Do not generalize these results to campus users. |
| Testing | PARTIAL | The notebook's controlled fixture and inventory summary run in-process; the ranking validator passes; four focused benchmark/validator unit tests pass; and the local HTTP preview returns 200 for valid input and 422 for blank text and an invalid calendar date. | Run the complete locked service suite and Firebase emulator integration tests. In-process notebook execution is not a Jupyter-kernel run. |
| Ranking | PASS for the synthetic prototype | `results/ranking_benchmark.json` records Top-1, Recall@5, MRR, and no-match false suggestions. The local preview returns up to five candidates; the authenticated worker stores up to 20. | Demonstrate a correct suggestion, a misleading lexical candidate, and a no-match case. |
| Explainability | PARTIAL end to end | The agents return traceable fact states and plain-language staff actions; tests cover agreement, conflict, missing facts, and private-data redaction. Android code displays the similarity and explanation. | Verify the explanation on the running Android app against the live worker and explain one agreement, one conflict, and one unknown. |
| Invalid input | PARTIAL end to end | Preview API tests reject blank/invalid input and obvious private-data patterns with redacted errors. | Demonstrate safe form feedback in the Android app and authenticated service, including empty text, invalid dates, and no inventory. |
| Mobile integration | PARTIAL | The merged Android implementation calls the authenticated `/v1` report, match, claim, and admin routes. Its report fields and category/location IDs match the MLEngine API and shared catalog. | A current phone/emulator-to-Firebase-to-worker walkthrough has not been verified. Run it and capture evidence before claiming end-to-end operation. |
| Notebook completeness | PASS for the reproducible prototype workflow | `NLP_Final.ipynb` profiles the transcribed Office aggregate counts separately from the fictional matching benchmark, then documents structural validation, EDA, grouped splits, baseline and final methods, held-out measures, explanations and an opt-in HTTP check. The runner executes cells in-process, not in a Jupyter kernel. | Run the notebook in the team's clean Jupyter environment and review all examples and claims before submission. |
| Repository organization | PARTIAL | The repository preserves the baseline, source/provenance notes, service, tests, and evaluation evidence. Historical handoff notes are being reduced while current setup, source, API, and benchmark references remain. | Keep source provenance and operational setup documentation available; complete the agreed document cleanup without removing project data or code. |
| Presentation | PARTIAL | Synthetic cases, evaluation evidence, and a three-person timing/role plan are documented in the companion Android repository's `PRESENTATION_DEMO.md`. | Rehearse a 3–6 minute demonstration in the actual Android app with all team members; the mobile walkthrough remains unverified. |
| CLIP / image inference | PASS for the stated scope | The final engine does not use CLIP or image embeddings. | Keep image matching out of the final claims unless paired, permitted data and measured results are later produced. |

## B. ML evaluation

The regenerated benchmark validated successfully: 24 found records, 27 lost reports, 192 labels (24 constructed positives and 168 assumed negatives), and 27 queries including three authored no-match queries. The evaluation test partition uses eight matched queries, two no-match queries, and the same 24-item candidate pool for each method.

| Method | Test Top-1 | Recall@5 | MRR | Strong false suggestions on no-match queries |
| --- | ---: | ---: | ---: | ---: |
| Keyword overlap | 0.250 | 0.875 | 0.541 | 1/2 |
| Structured attributes | 1.000 | 1.000 | 1.000 | 1/2 |
| Logistic Regression | 1.000 | 1.000 | 1.000 | 1/2 |
| TF-IDF | 0.250 | 0.500 | 0.391 | 2/2 |
| Hybrid | 1.000 | 1.000 | 1.000 | 2/2 |

These are results on AI-authored controlled fiction. The perfect attribute and hybrid scores reflect constructed shared fields; the no-match false suggestions show that a high-ranked result is not proof of a match. The evaluation is not evidence of real Strathmore accuracy. Independent student review of every example and label is still required.

## C. Repository cleanup

The cleanup review preserved the unique prior demo transcript intact at `results/archive/prior_demo_run.txt`. Source-dependent Delhi outputs and local model data remain in place pending provenance review. A later documentation cleanup removed six completed or superseded Markdown handoff notes; project source and data were not removed.

## D. Notebook review

`notebooks/NLP_Final.ipynb` follows the requested `NLP_Final.ipynb` title and documents the specific TF-IDF retrieval approach used in the final worker. Its workflow includes task definition, provenance, controlled-data preparation, data-quality summaries, group leakage control, Logistic Regression comparison, TF-IDF/cosine similarity, validation-based hybrid selection, held-out ranking results, explanation checks, and an optional local HTTP smoke check. In-process execution is not the same as a clean Jupyter-kernel run; the team should still execute it in its submission environment.

## E. Android / MLEngine integration

The Android repo is `MAD_project`; the engine repo is `SemProject_MLEngine`. The Android development branch was merged into `main` in PR #2. Static comparison confirms the Android report payload matches `service.api.ReportInput`, its category/location IDs match `service/catalog.json`, and the endpoints used by the connected screens exist in the authenticated API. Android labels the displayed value as TF-IDF text similarity. Photo upload remains disabled in the demo Firebase configuration. Static agreement does not prove a live mobile-to-worker run.

The current engine worker uses `TfidfMatcher` and the shared knowledge-agent pipeline. The separate Logistic Regression coursework experiment remains a baseline; it is not loaded by the active worker. No service/API contract changes were necessary for Android compatibility.

## F. Reproducibility and remaining work

| Check | Status | Evidence / next step |
| --- | --- | --- |
| Dependency declarations | PARTIAL | `requirements-service.lock.txt` pins service dependencies. Root `requirements.txt` uses lower bounds. Install the documented set in a clean environment and record the Python version. |
| Relative paths | PASS in the ranking scripts | Scripts derive repository paths from `__file__`; benchmark preparation and evaluation completed from the repository root. |
| Fixed inputs and grouping | PASS for the synthetic benchmark | Controlled fixtures build the 24-item pool; validation rejects structural/split errors. Labels remain unverified fiction. |
| Reproducible benchmark | PASS for this run | Preparation, validation, and evaluation commands completed successfully on 24 November 2026. |
| Notebook execution | PARTIAL | Nine code cells ran without error outputs, including the optional HTTP preview check. This does not verify a Jupyter kernel. Run the compiled notebook in a clean team environment before submission. |
| Secret handling | PARTIAL | `.gitignore` excludes `.env`, Firebase credentials, and service account JSON. Recheck the full tracked tree before public submission. |
| Live Firebase / Android path | NOT VERIFIED | Required Firebase integration imports are unavailable in this environment, and no connected device/API walkthrough was performed. |

### Priority handover

- **P0:** Student team reviews/approves synthetic examples and labels; verifies source provenance; reruns the final notebook in a clean Jupyter environment; installs the locked dependencies and runs the full service/emulator suite; demonstrates the actual Android form → authenticated report → worker → ranked result flow.
- **P1:** Investigate false strong suggestions on both held-out no-match queries; test threshold behavior and failure messaging without presenting a score as probability; verify retry, access controls, and inventory refresh through the authenticated service.
- **P2:** Collect permitted, independently verified lost/found pairs and expand the held-out ranking evaluation. Consider production monitoring and retention only after privacy/access review.

### Follow-up implementation

- The assessed notebook is now `notebooks/NLP_Final.ipynb`, generated by `scripts/build_nlp_notebook.py` and executed by `scripts/execute_nlp_notebook_inprocess.py`.
- The notebook includes the June–July and August aggregate counts, a reproducible fictional-benchmark quality/EDA summary and Top-1 accuracy with matched-query denominators. It calls out the 2/2 TF-IDF false-suggestion result on the two fictional no-match test queries.
- The opt-in HTTP preview cell returned 200 for valid input and 422 for blank description and an invalid calendar date. This tests the local preview route, not the authenticated mobile service.
- The companion Android demo guide now contains a concrete app walkthrough, valid/invalid input cases, and three presenter roles. Actual emulator/phone execution is still required; no live device walkthrough is claimed here.

### Proposed 3–6 minute demo outline

1. **0:00–0:45:** Explain the campus lost-and-found workflow and that staff make ownership decisions.
2. **0:45–2:15:** In the Android app, submit two varied synthetic lost reports and show the ranked candidates.
3. **2:15–3:15:** Show a conflicting or unrelated case, an empty/no-match case, and safe invalid-input feedback.
4. **3:15–4:15:** Explain a candidate with one matching fact, one conflict, and one missing field; distinguish lexical similarity from probability.
5. **4:15–5:15:** Briefly show the final TF-IDF notebook, baseline comparison, ranking measures, and the constructed-data limitation.
6. **5:15–5:45:** State remaining limitations and that staff review before any handover. If the Android-to-service path is not live, disclose that instead of substituting notebook output for an app demo.

## G. Verified outcomes and limits

- Ranking fixture preparation and structural validation succeeded on 24 November 2026.
- The targeted offline suite previously passed 30 tests; this review reran the focused ranking/validator tests (4 passed). Full discovery ran 44 tests: 42 passed and two modules failed to import because `pytest` and `firebase_admin` are missing. Firebase emulator integration is not verified.
- The notebook runner executes its cells in-process; this is not a clean Jupyter-kernel run. Rerun the updated notebook before submission and review its aggregate transcription and fictional examples.
- The ranking dataset validator and benchmark evaluator were rerun successfully on 24 November 2026; the fixture still contains 24 found records, 27 queries, and 192 constructed labels.
- No Android-to-Firebase-to-worker walkthrough, real matched-pair evaluation, or independently verified institutional data was observed in this audit.
- No CLIP/image model was added. Only the six completed/historical Markdown handoff files listed in this cleanup change were removed; project data, source, and the untracked MLEngine `work/` directory were left untouched.
