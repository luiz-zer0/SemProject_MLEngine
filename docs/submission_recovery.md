# Report submission recovery and deployment checklist

## Root cause and evidence

The exact screenshot error is from Android's older generic exception handler. The latest Louis branch (2920875c) already distinguishes HTTP errors and prevents a post-save refresh failure from masquerading as a failed submission. Its configuration still requires a reachable authenticated API. Both setup documents record that the live API and worker have not been deployed; Firebase sign-in alone does not prove report connectivity. No live endpoint or production credentials were provided for verification.

## Local demo

From this repo, install the locked dependencies and Firebase CLI as in FIREBASE_SETUP.md. Start emulators, API, worker in separate terminals, then seed the local accounts. Verify http://127.0.0.1:8000/health and /ready. Start the optional preview on port 8001 instead of 8000. Run the integration tests in FIREBASE_SETUP.md. The Android Studio emulator uses 10.0.2.2 and the debug demo build (-PdemoFirebase=true); use demo-student and demo-office only. A real Android phone with production Firebase must have a reachable HTTPS backend, or a correctly configured local real-project API via ADB reverse and authorized credentials. The existing demo emulator Auth/Storage hosts are hard-coded to 10.0.2.2, so a physical-phone emulator build additionally requires a coordinated Android change: parameterize the demo host as 127.0.0.1 for API/Auth/Storage, reverse ports 8000, 9099 and 9199, rebuild and install. Do not mix production accounts and emulator services or erase saved drafts.

## Android changes for Louis (write access required)

- Continue from codex/louis-deliverable3-demo (2920875c or later). Preserve the existing error parser and one-time token refresh. Add specific connection-refused, timeout, DNS and placeholder-URL messages; a 404 on /v1/reports suggests the wrong API. Never send tokens to the preview or an unverified endpoint.
- Align navigation with server roles: found intake is office_staff only; technical admin manages access. Do not broaden the global staff policy. Validate catalogue IDs, trimmed title/description and attribute lengths before submission. If the initial request receives a definitive 401/403/422, allow correction and keep the draft; if a transport failure leaves the result uncertain, preserve the original UUID and unchanged payload. A 409 requires reconciliation. Never clear a draft until the response includes the saved report ID.
- Add an explicit debug-only demoHost configuration restricted to 10.0.2.2 or 127.0.0.1, used by Firebase Auth, Storage and the API. For physical local demo use ADB reverse and rebuild; default emulator behavior remains unchanged. No production cleartext endpoint.
- Verify actual lost and found submissions on device, including role denial, valid/invalid input and exactly-once retry. Do not use the NLP preview or hard-coded matches as evidence of integration.

## Untethered production use

Deploy the existing Dockerfile API with APP_ENV=production, FIREBASE_PROJECT_ID=lost-and-found-9671c and authorized application default credentials. Deploy a separate continuously running worker using python -m service.worker. Use an authorized hosting account, HTTPS and appropriate IAM; do not expose service account keys or enable billing without approval. Verify /health, /ready, authenticated /v1/me, then a permitted test report and matching job. Build Android with the actual verified HTTPS endpoint. A source-code commit alone does not change an installed APK or deploy these services.

## Current notebook / presentation

NLP_Final.ipynb on main includes sections 7A (operational ranker evaluation) and 8A (required app demo), merged in PR #16. Execute all cells from a clean Jupyter kernel before citing new results. The offline TF-IDF comparison is 2/8 Top-1 and 4/8 Recall@5; operational metrics are not yet generated. The presenter guide allocates two minutes to the real app, within a total 5:30. If deployment is blocked, use the actual authenticated emulator workflow or explicitly state the limitation.
