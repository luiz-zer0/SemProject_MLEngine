# Deliverable 3 technical audit and handover

Review date: 24 November 2026. This is a technical review for the team to inspect and correct; it is not a student-authored submission or a claim that the assessment is complete. No cleanup removals were made.

## A. Rubric compliance

| Area | Status | Current evidence | Remaining action / demonstration |
| --- | --- | --- | --- |
| Data collection | PARTIAL | Real found-only sources and provenance are documented. The Office source documents were inaccessible during the earlier audit; the tracked inventory is aggregate, not individual report records. | Verify the source transcription and usage terms with the team. Obtain consented, privacy-reviewed individual reports and verified same-item links before making real-case claims. |
| Data cleaning | PARTIAL | Preparation scripts and structural validators exist; synthetic ranking data is reproducible from controlled fixtures. The Delhi raw CSV is not part of a fresh clone. | Reproduce the Delhi cleaning only after obtaining the source file and confirming its current terms. Keep row-level derivatives local where required. |
| NLP preprocessing | PASS for the prototype | `matching_system/nlp_retrieval.py` normalizes report text and ranks with word and bigram TF-IDF over found reports. | Explain the actual settings and lexical limits in the notebook; do not describe similarity as probability. |
| Baseline model | PASS | The prior Logistic Regression notebook and implementation remain available, with saved campus baseline outputs. | Present it as the baseline/coursework experiment, not the authenticated worker model. |
| Final matching approach | PARTIAL | The TF-IDF ranker, matching agent, staff-workflow agent, local preview API, and Firebase worker exist. `NLP_Final.ipynb` documents the NLP approach, including TF-IDF. | Team review the notebook and ensure its demonstrated method agrees with the mobile service. No CLIP/image method is used. |
| Training / fitting | PARTIAL | The benchmark fits TF-IDF and Logistic Regression on grouped synthetic training data and chooses a hybrid weight on validation data. The live worker fits a lexical index on found inventory; it does not load the Logistic Regression artifact. | State this distinction explicitly and have the team justify the selected runtime method. |
| Validation and evaluation | PARTIAL | A reproducible, grouped fictional benchmark compares five methods on a 24-item pool. The held-out set contains eight matched queries and two no-match queries. | Review the authored examples, labels, groups, false suggestions, and limitations. Do not generalize these results to campus users. |
| Testing | PARTIAL | The ranking validator passed; 30 targeted retrieval, agent, API-preview, and ranking tests passed. Full discovery ran 44 tests: two test modules could not import because `pytest` and `firebase_admin` are absent from this Python environment. | Install the locked project dependencies in a clean environment, run all tests, and run Firebase emulator integration tests. |
| Ranking | PASS for the synthetic prototype | `results/ranking_benchmark.json` records Top-1, Recall@5, MRR, and no-match false suggestions. The local preview returns up to five candidates; the authenticated worker stores up to 20. | Demonstrate a correct suggestion, a misleading lexical candidate, and a no-match case. |
| Explainability | PARTIAL end to end | The agents return traceable fact states and plain-language staff actions; tests cover agreement, conflict, missing facts, and private-data redaction. Android code displays the similarity and explanation. | Verify the explanation on the running Android app against the live worker and explain one agreement, one conflict, and one unknown. |
| Invalid input | PARTIAL end to end | Preview API tests reject blank/invalid input and obvious private-data patterns with redacted errors. | Demonstrate safe form feedback in the Android app and authenticated service, including empty text, invalid dates, and no inventory. |
| Mobile integration | PARTIAL | Android branch `codex/mobile-nlp-results` calls the authenticated `/v1` report, match, claim, and admin routes. Its report fields and category/location IDs match the MLEngine API and shared catalog. | A current phone/emulator-to-Firebase-to-worker walkthrough has not been verified. Run it and capture evidence before claiming end-to-end operation. |
| Notebook completeness | PARTIAL | `NLP_Final.ipynb` has 16 cells covering sources, preparation, baseline, TF-IDF, hybrid evaluation, explanations, preview call, and limitations. A fresh kernel executed all 16 cells with no cell error outputs, but the driver exited with status 1 during kernel shutdown and emitted profile-permission warnings. | Rerun in a clean Jupyter environment and confirm a zero exit status. The student team must independently review and approve the content. |
| Repository organization | PARTIAL | The repository preserves the baseline, source/provenance notes, service, tests, and evaluation evidence. `docs/cleanup_manifest.md` records non-destructive recommendations. | Review the manifest before any move or removal. No files have been deleted or archived. |
| Presentation | PARTIAL | Synthetic cases, evaluation evidence, and a demo handoff exist. | Rehearse a 3–6 minute demonstration in the actual Android app with all team members; the mobile walkthrough remains unverified. |
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

See [the file-by-file cleanup manifest](cleanup_manifest.md). The unique Friday run transcript was moved intact to `results/archive/friday_run.txt`; generated-cache cleanup was unnecessary because the listed cache was absent. Other source-dependent items remain preserved pending provenance review. Nothing was deleted.

## D. Notebook review

`notebooks/NLP_Final.ipynb` is retained as the final notebook name because the project deliverable is the NLP approach; TF-IDF is the specific retrieval method documented in it. The generator and in-process runner point to this path. It has 16 cells and covers data sources, grouping, baseline comparison, TF-IDF/cosine similarity, hybrid evaluation, examples, explanation, and limits. A previous fresh-kernel attempt executed all cells without notebook error outputs, but returned exit status 1 during shutdown with IPython profile-permission warnings. A further isolated-kernel attempt in this review did not complete, so clean-kernel verification remains pending until it completes with exit status 0 in the team environment. Student review and authorship remain required.

## E. Android / MLEngine integration

The Android repo is `MAD_project`; the engine repo is `SemProject_MLEngine`. The Android development branch is `codex/mobile-nlp-results` (latest pushed commit `b48f8ef`). Static comparison confirms the Android report payload matches `service.api.ReportInput`, its category/location IDs match `service/catalog.json`, and the endpoints used by the connected screens exist in the authenticated API. Android labels the displayed value as TF-IDF text similarity. Photo upload remains disabled in the demo Firebase configuration. Static agreement does not prove a live mobile-to-worker run.

The current engine worker uses `TfidfMatcher` and the shared knowledge-agent pipeline. The separate Logistic Regression coursework experiment remains a baseline; it is not loaded by the active worker. No service/API contract changes were necessary for Android compatibility.

## F. Reproducibility and remaining work

| Check | Status | Evidence / next step |
| --- | --- | --- |
| Dependency declarations | PARTIAL | `requirements-service.lock.txt` pins service dependencies. Root `requirements.txt` uses lower bounds. Install the documented set in a clean environment and record the Python version. |
| Relative paths | PASS in the ranking scripts | Scripts derive repository paths from `__file__`; benchmark preparation and evaluation completed from the repository root. |
| Fixed inputs and grouping | PASS for the synthetic benchmark | Controlled fixtures build the 24-item pool; validation rejects structural/split errors. Labels remain unverified fiction. |
| Reproducible benchmark | PASS for this run | Preparation, validation, and evaluation commands completed successfully on 24 November 2026. |
| Fresh notebook execution | PARTIAL | Cells ran with no notebook error outputs, but the process exited 1 during kernel shutdown. Rerun cleanly with exit status 0. |
| Secret handling | PARTIAL | `.gitignore` excludes `.env`, Firebase credentials, and service account JSON. Recheck the full tracked tree before public submission. |
| Live Firebase / Android path | NOT VERIFIED | Required Firebase integration imports are unavailable in this environment, and no connected device/API walkthrough was performed. |

### Priority handover

- **P0:** Student team reviews/approves synthetic examples and labels; verifies source provenance; reruns the final notebook in a clean Jupyter environment; installs the locked dependencies and runs the full service/emulator suite; demonstrates the actual Android form → authenticated report → worker → ranked result flow.
- **P1:** Investigate false strong suggestions on both held-out no-match queries; test threshold behavior and failure messaging without presenting a score as probability; verify retry, access controls, and inventory refresh through the authenticated service.
- **P2:** Collect permitted, independently verified lost/found pairs and expand the held-out ranking evaluation. Consider production monitoring and retention only after privacy/access review.

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
- The notebook runner previously executed 16 cells with no cell error outputs, but exited with status 1 during teardown. A further isolated-kernel attempt did not complete. Clean-kernel acceptance remains open.
- The ranking dataset validator and benchmark evaluator were rerun successfully on 24 November 2026; the fixture still contains 24 found records, 27 queries, and 192 constructed labels.
- No Android-to-Firebase-to-worker walkthrough, real matched-pair evaluation, or independently verified institutional data was observed in this audit.
- No CLIP/image model was added, no files were deleted, and the untracked MLEngine `work/` directory was left untouched.
