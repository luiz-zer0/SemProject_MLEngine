# Deliverable 3 final checks

Review branch: notebook and presentation alignment. The operational model is unchanged.

## Notebook

- Install dependencies from the repository root: `python -m pip install -r requirements.txt`.
- Open `notebooks/NLP_Final.ipynb`. Restart the kernel and run all cells. Alternatively install nbconvert and ipykernel, then run `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/NLP_Final.ipynb --ExecutePreprocessor.timeout=180`.
- Review the fresh operational metrics in section 7A and compare with the offline table. The benchmark lacks item names; the runtime adapter leaves these blank. Do not report the new metrics before executing the cell.
- The optional preview runs on port 8001: `python -m uvicorn matching_system.api:app --host 127.0.0.1 --port 8001`. Set NLP_LIVE_HTTP_DEMO=1 before the kernel starts if you want that cell to run.
- Retain the separate LogisticRegression_Baseline.ipynb. Verify the office transcription and constructed labels. Existing saved outputs in unchanged cells are historical; new cells are intentionally unexecuted until a real run.

## Live presentation (5:30)

0:00–1:00 Nimrod: problem, data sources, cleaning and grouped split. 1:00–2:15 Louis: Logistic Regression baseline, TF-IDF/cosine, validation and operational distinction. 2:15–3:15 Alex: five-method benchmark, metrics and limits. 3:15–5:15 Louis with team: authenticated Android demo, two valid inputs, invalid input, ranked outputs and explanation. 5:15–5:30 Nimrod: conclusion. Cameras on throughout.

Use FIREBASE_SETUP.md to start the authenticated API on port 8000, Firebase emulators and worker. Rehearse office check-in and student reporting with fictional accounts; do not use preview output as proof of mobile operation. Record the actual outcomes and any remaining blockers. No live backend or device verification was performed as part of this notebook edit.
