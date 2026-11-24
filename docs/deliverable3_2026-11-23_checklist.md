# Deliverable 3 handover — 23 November 2026

## What is reproducible now

- The original CAT 2 Logistic Regression notebook and scripts remain intact.
- The Office inventory transcription has 57 aggregate category rows and 687 quantities. The two linked Google Docs returned permission denied, so the transcription needs source verification.
- The new controlled-fiction dataset builds 24 found records, 27 lost queries, 24 positive labels, 168 negative labels, three no-match queries and one fixed 24-item pool. The structural validator passes. Descriptions were AI authored and need independent team review.
- `results/ranking_benchmark.json` contains the measured comparison. Eight matched and two no-match test queries were evaluated. The perfect structured-feature scores are caused by shared attributes in the constructed pairs, and the no-match checks still produce false strong suggestions. These are not real-campus accuracy results.
- `notebooks/NLP_Final.ipynb` presents data provenance, grouped preparation, the preserved classifier baseline, TF-IDF and cosine similarity, hybrid validation, measured metrics, explanations and a direct local preview-route call. It was executed in one Python process; a clean Jupyter kernel run and team review remain pending.
- The authenticated FastAPI service and Firestore worker exist in this repository; the worker calls the NLP pipeline. The companion Android application has report and match screens, but no current phone-to-service run was observed in this task.

## Three-developer review and demo ownership

1. **Dataset/NLP developer:** compare the transcribed aggregate table with both original Office documents; review all fictional descriptions, labels and split groups; run preparation, validation and evaluation from a clean environment; explain the artificial structured-feature advantage and TF-IDF misses.
2. **Backend developer:** run the service and worker tests against Firebase emulators; exercise authenticated report intake, matching job completion, ranked result access, invalid input and unauthorized claim/release actions; ensure ordinary users see only permitted details. Verify the worker's inventory cache refreshes after a found report changes.
3. **Android developer:** build the current app and show a real form submission, pending state, ranked results, explanations, no-match state and a clear invalid-input error against the running service. Capture network and device evidence. Do not substitute notebook or hard-coded screen data for this test.

All three should inspect the same test result JSON and understand why the controlled benchmark does not establish ownership or field recovery performance. Rehearse a 3–6 minute demonstration with every member present and camera on. Submit the executed, reviewed notebook and the required public repository or recording links by 25 November 2026, after checking the rubric and actual repository visibility.

## Current blockers

The original inventory Docs are inaccessible to the connected account. No verified individual Office records or independently reviewed same-item links are available. The HTTP `TestClient` run stalled in the temporary Python 3.14 environment used here; the notebook's direct route-function call is not an HTTP or mobile end-to-end result. A clean Jupyter kernel execution and an Android-to-Firebase-to-worker walkthrough have not been observed.
