# Local Firebase + Android + NLP service

The demonstration uses Firebase Authentication, Firestore and Storage **emulators**, an authenticated FastAPI service and the separate NLP worker. It is not a public deployment. Use fictional reports only.

## Quick start

See [local presentation instructions](docs/LOCAL_PRESENTATION.md) for prerequisites, startup, seeded accounts, Android emulator and rehearsal.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_presentation.ps1 -Install
```

After the initial dependency and emulator binary downloads, omit `-Install`. The separate terminal commands remain available for diagnosis:

```powershell
.\scripts\start_local.ps1 -Service emulators
.\scripts\start_local.ps1 -Service api
.\scripts\start_local.ps1 -Service worker
.\scripts\start_local.ps1 -Service seed
```

Wait for the emulators before starting API/worker or seeding. The API is on port 8000, Auth 9099, Firestore 8080, Storage 9199, UI 4000. The Android Studio emulator uses `10.0.2.2` and a debug build with `-PdemoFirebase=true`. Use [MAD_project](https://github.com/luiz-zer0/MAD_project/tree/codex/louis-deliverable3-demo). Physical-phone setup is not the supported presentation target. Android configuration belongs in that repository.

## Persistence, matching and security

- The API checks Firebase ID tokens, verified university email and server-assigned roles. Only office_staff can record found items; technical admin manages access.
- Report creation atomically stores the report and a matching job. A stable request ID makes retries idempotent. Changed content with the same ID returns 409.
- The worker leases jobs, retries failures and retains reports if matching fails. It ranks active candidates using TF-IDF and adds knowledge-agent explanations. Human review is required.
- Firestore client writes are denied; authorized API endpoints make business mutations. Storage rules restrict private photos. No image inference is used.
- Claims and collection are transactional, with role and ownership checks, audit and receipt. Sensitive wallet/document intake requires sealed custody.
- In-app notifications are stored locally. Production-only push is skipped by emulator mode. No live notification or cloud service is required.
- Local emulator data is temporary unless explicitly exported. A draft is not a submitted report. Keep production accounts and local accounts separate.

## Tests

With no other emulators running, from `firebase/` run:

```powershell
npx.cmd firebase-tools emulators:exec --project demo-strathmore-lost-found --only "auth,firestore,storage" "..\.venv-service\Scripts\python.exe ..\scripts\verify_local.py"
```

This runs model/API tests, real local emulator integration and authorization rules tests. The independent [local backend smoke test](https://github.com/nimrod-kobia/SemProject_MLEngine/actions/runs/45504542376) verified two charger rankings and HTTP 422 rejection. It does not prove Android device execution.

## Troubleshooting

Check `GET /health` (authenticated_reports, not synthetic_preview) and `GET /ready` (Firestore read); then sign in with a local account. Check the worker window if a report remains pending. Keep the optional preview on port 8001 to avoid conflict. See [report submission recovery](docs/submission_recovery.md). Do not deploy or configure a live Firebase project for this presentation.
