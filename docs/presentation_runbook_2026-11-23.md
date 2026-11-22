# Lost & Found presentation runbook — 23 November 2026

## What to show

The mobile app submits fictional lost/found reports to the authenticated FastAPI service. Firestore stores the report and a job; the worker ranks active found reports with TF-IDF and knowledge agents. The app displays possible matches, lexical similarity and a reason for staff review. Neither a score nor a suggestion proves ownership. The version 2 hybrid benchmark is an offline comparison, not the deployed model; its four no-match test queries all received false strong suggestions.

## Prepare the local demo

From `SemProject_MLEngine`, install `requirements-service.lock.txt` in `.venv-service` with Python 3.12+, then run `python -m scripts.export_mobile_model`. Run `npm ci` once in `firebase`. Use four PowerShell windows:

```powershell
.\scripts\start_local.ps1 -Service emulators
.\scripts\start_local.ps1 -Service seed
.\scripts\start_local.ps1 -Service api
.\scripts\start_local.ps1 -Service worker
```

Run seed after the emulators are ready. The demo project is `demo-strathmore-lost-found`. Sign in as `demo-office@strathmore.edu` or `demo-student@strathmore.edu`, both with `LocalDemo123!`; these are fictional emulator accounts. The emulator UI is `http://127.0.0.1:4000`; API docs are `http://127.0.0.1:8000/docs`.

In `MAD_project`, build with `./gradlew.bat -PdemoFirebase=true testDebugUnitTest assembleDebug` and install `app/build/outputs/apk/debug/app-debug.apk` on an Android emulator. This flag explicitly selects the demo Firebase project and `http://10.0.2.2:8000`, even if a local `firebase.properties` exists. It never changes release configuration. On a physical phone, `10.0.2.2` is unavailable; configure a reachable development API and Firebase emulator hosts before using it.

For a service-only rehearsal, from `firebase` run:

```powershell
npx.cmd firebase-tools emulators:exec --project demo-strathmore-lost-found --only "auth,firestore,storage" "..\.venv-service\Scripts\python.exe ..\scripts\verify_presentation_network.py"
```

The smoke starts a local HTTP server, creates fictional accounts and reports, processes a worker job, checks one scored suggestion and rejects an unrelated user. It cleans up the server. Run it with no other emulators or API bound to the same ports.

## Suggested 3–6 minute walkthrough

1. Explain the fictional inventory and the version 2 held-out benchmark. Show Top-1, Recall@5 and no-match errors from `results/ranking_benchmark_v2.json`, stating that no real-campus accuracy has been measured.
2. Sign in as office and submit a found report, for example a **blue metal water bottle with scratched lid** at MSB. Sign in as student and submit a matching lost report with different wording. Explain that a pending state can appear until the worker finishes.
3. Open Reports or Matches, refresh, and inspect the ranked result. Read its explanation and the “TF-IDF text similarity” label; demonstrate that it is lexical evidence, not a probability or ownership decision.
4. Submit an unrelated lost item to demonstrate an empty or weak result. Show the office review and handover workflow only after checking the claim and physical item.
5. State the limits: fictional training/evaluation data, no automatic release, live Storage unavailable on the current Firebase plan, and no current Android runtime verification.

## Verified status and remaining gate

On 23 November, the Python suite passed (49 passed, 1 skipped), the Firebase emulator suite passed (50 passed), the real HTTP smoke passed, and normal and demo Android unit-test/build commands passed. No device was connected. The configured `Medium_Phone` emulator could not start because the C: drive had insufficient free space (about 1.9 GB). Free space or attach a phone, then repeat the actual Android sign-in → report → worker → results sequence and capture a screen recording before describing it as an end-to-end mobile demonstration. The notebook was executed in-process, not yet in a clean Jupyter kernel; students must review and run it before submission.
