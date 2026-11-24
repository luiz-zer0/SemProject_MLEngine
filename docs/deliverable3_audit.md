# Deliverable 3 current audit

| Requirement | Verified status |
|---|---|
| Base model | Historical Logistic Regression notebook and supporting code/data retained. |
| Final notebook | NLP_Final.ipynb on main; 27 Markdown explanation cells and 16 successfully executed code cells with saved results. |
| Data mining stages | Problem understanding, provenance, fictional data construction, quality checks, modelling, validation, evaluation, operational ranking and integration. |
| Model comparison | Five offline methods, held-out scores and limitations; separate operational TF-IDF results (50% Top-1, 87.5% Recall@5, MRR@5 0.629, no-match suggestions 2/2). |
| Local backend | Real authenticated API, Firestore/Auth emulators, worker, two charger rankings and invalid description test passed. |
| Mobile app | Separate MAD_project repository. Android Studio emulator rehearsal is still required. |
| Teamwork | All three presenters should participate, explain their actual contributions and keep cameras on. |

The verified [notebook run](https://github.com/nimrod-kobia/SemProject_MLEngine/actions/runs/45503554200) and [backend run](https://github.com/nimrod-kobia/SemProject_MLEngine/actions/runs/45504542376) are reproducible evidence, not proof of real-campus accuracy or Android testing.

The repository is now organized for the local demonstration. Cloud deployment configurations, unused service classifier adapter, obsolete in-process notebook runner and superseded legacy preview evidence scripts were removed from the active tree. Their history is retained; the assessed base notebook and baseline experiment dependencies were not deleted. See the README and [local presentation](LOCAL_PRESENTATION.md).

Remaining student tasks: rehearse real valid/invalid inputs in the Android app, review the fictional labels and office transcription independently, explain limitations and staff review, and follow the instructor's AI-use rules.
