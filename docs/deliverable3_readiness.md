# ICS 3202 Deliverable 3: readiness and team plan

Review date: 17 November 2026. Source: the three-page `Project Deliverable 3.pdf` supplied by the team. The brief starts the presentation window on **Monday 23 November** and sets the due date at **end of Wednesday 25 November 2026**. Treat the brief as assessment requirements; the work assignments below are our implementation plan.

## What the brief asks the team to show

- A **3–6 minute** live demonstration of the ML engine operating in the **mobile application**, with a team member acting as the end user, entering varied sample inputs, and interpreting varied outputs. Invalid input and an explainable result matter to the app-functionality rubric.
- All three members present with cameras on, whether presenting live or in a recorded demonstration. If recording, upload the video to an online repository or Drive/OneDrive and submit its link.
- One **executed final notebook** in this public repository, named `<Approach>_Final.ipynb`, containing the complete data-mining path, training/fitting, testing, validation, clear descriptions and the final ML logic for review. Confirm repository visibility and submission link before the deadline.
- The brief explicitly warns against directly using AI-generated text to develop the submitted work. Each student must independently write, understand and review the final notebook, presentation and narration under the course rules.

## Current evidence and gaps

| Requirement | Verified repository state | Remaining work |
| --- | --- | --- |
| NLP engine | `matching_system/nlp_retrieval.py` fits word and bigram TF-IDF on found reports and ranks up to five positive-overlap candidates. | Put the exact final pipeline and its limits into one executed notebook. Freeze the implementation before demo. |
| Knowledge-based explanations | Two rule modules, traceable facts/actions, and API candidate explanations exist. | Show explanations in the mobile app and explain one agreement, one conflict and one unknown without implying ownership. |
| Fitting, testing and validation | Synthetic 46-report corpus, 14 designed matched lost queries, 32 found records, grouped development/test results and one authored empty-result query are recorded. Test cohort has only three queries. | Review split/labels, show denominators and error cases in notebook. No real-campus accuracy claim without verified real pairs. |
| Mobile end-user flow | No Android files in this repository. Companion `AI-project/android` is a Compose starter showing “Hello Android”; its README states no reporting/API integration. | Build a read-only staff preview screen, connect it to the synthetic API and demonstrate it on an emulator or phone. Verify an actual build and runtime path. |
| Invalid input | FastAPI rejects malformed requests and obvious email/phone/labeled-ID patterns with a generic 422 response. | Show form validation and a safe error state in the app. Test blank text, bad date and one rejected synthetic private-data pattern. |
| Final notebook | Only `notebooks/LogisticRegression_Base.ipynb` exists; it is a separate offline constructed-pair classifier. | Create and execute `TFIDF_Final.ipynb` (or another accurate approach name) with the current NLP method and agents. No stale outputs or undocumented imports. |
| CLIP | No CLIP implementation in this repository. Companion `matching_system/clip_encoder.py` raises `NotImplementedError`; there are no verified paired images or CLIP metrics. | Keep CLIP out of the final engine and demo unless actual image data, working code and evaluation arrive in time. Do not present a placeholder as implemented. |

The API's fixed synthetic inventory, no persistence and no authentication are acceptable for a clearly labeled local **synthetic demonstration** only. The app should not collect real claimant data for this demo. The current explanation is staff-facing, so make the staff member the demonstrated end user. A generic student/claimant flow would need different copy and access design.

## Decision on classification and CLIP

Keep the old Logistic Regression notebook and scripts in the repository as **prior coursework evidence**, clearly separated from the final NLP path. Deleting them now would remove provenance and would not strengthen the deliverable. Do not present its constructed-pair scores as validation of the NLP engine. The final notebook and live app should use the same TF-IDF retrieval and knowledge-agent code, with no competing classifier in the runtime path.

CLIP is optional future research, not part of this week's acceptance path. Image input is not required by this brief. Adding it without paired, permitted images and measured behavior would put the required mobile/NLP demo at risk.

## Dated work plan

| Date | Nimrod: NLP and final notebook | Alex: API and agent explanations | Louis: mobile app, evaluation and demo |
| --- | --- | --- | --- |
| **Wed 18 Nov** | Agree final input/output contract; outline `TFIDF_Final.ipynb` as data audit → preparation → fit → validation → errors → inference. | Freeze preview API fields and rule/explanation wording; provide a stable sample JSON response. | Confirm Android checkout, SDK, emulator/phone and build. Replace starter with a form and result-screen skeleton using synthetic values. |
| **Thu 19 Nov** | Draft notebook using imports from the actual runtime modules; include source counts, preprocessing, TF-IDF parameters and grouped split. | Add/repair tests for valid, conflicting, missing, empty and invalid requests; verify no ownership/release claim. | Connect the screen to the local API; handle loading, network failure and 422 safely. Use emulator host routing or a tested device-accessible endpoint. |
| **Fri 20 Nov** | Run notebook top-to-bottom in a clean environment; reconcile metrics with checked-in evaluation output. | Verify response stability with the mobile client and document the high-level reasoning in student-authored language. | Build and run the app; capture a first real app-to-API walkthrough. Report exact environment and blockers. |
| **Sat–Sun 21–22 Nov** | Freeze engine/notebook logic and correct reproducibility issues. | Review candidate explanations and privacy boundary; help fix integration failures. | Rehearse four cases: plausible result, misleading result, empty result and invalid input. Prepare a fallback recording of the actual app if the live network is unreliable. |
| **Mon 23 Nov** | Present fitting, grouped validation and limitations in about one minute. | Present rule trace and explainability in about one minute. | Operate the mobile app as staff end user. Run a timed 3–6 minute rehearsal with all cameras on. Prefer presenting during class for immediate feedback. |
| **Tue 24 Nov** | Confirm final notebook name, execution outputs and public repository link. | Confirm final API/agent code and tests at the submitted commit. | Recheck app build/runtime, video link if recording, and all demonstration inputs. Reserve this day as the last repair buffer. |
| **Wed 25 Nov** | Verify submitted notebook and commit. | Support final question-and-answer. | Submit required links before end of day; keep a copy of submission confirmation. |

## Acceptance rehearsal before presentation

1. From a fresh checkout, install dependencies, run the complete test suite, execute `TFIDF_Final.ipynb` top-to-bottom, and verify that notebook counts/scores match the script's synthetic output.
2. Build and launch the mobile app on an emulator or phone, enter the authored bottle query, and show multiple ranked candidates with scores labeled **text similarity**, structured evidence and a readable explanation. Inspect the plastic distractor's category conflict.
3. Enter the telescope no-overlap query and show an empty-result message that does not claim no physical counterpart exists.
4. Enter blank text, an invalid date and a synthetic private-data pattern; show a comprehensible app error without echoing the private value.
5. Time the full narrated demo to 3–6 minutes. Every member speaks and is present on camera. Keep a locally tested recording route if the live class platform fails.

The synthetic fixtures demonstrate operation, not real-campus matching accuracy. If permitted verified pairs arrive, keep their evaluation separate and do not retune on the held-out group. If they do not arrive, state the evidence limit plainly and still deliver the functioning app and reproducible notebook.
