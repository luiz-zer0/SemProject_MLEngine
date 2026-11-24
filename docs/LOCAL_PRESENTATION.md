# Free local presentation — Windows
No deployment, Firebase cloud credentials or billing upgrade required. This runs the real authenticated FastAPI service, Firestore/Auth emulators and operational NLP worker. All records and accounts are fictional. The optional cloud deployment configuration is retained on main but not required.

## One-time preparation and startup
Use Python 3.12, Node.js compatible with the pinned Firebase CLI, and Java 21 (Android Studio JBR). From the ML repository root:
    powershell -ExecutionPolicy Bypass -File scripts/start_presentation.ps1 -Install
On later runs omit -Install. Install/download dependencies and emulator binaries before presentation day. Close previously started demo windows before restarting. The script checks occupied ports instead of killing processes; it launches three service windows, seeds accounts and two fictional found chargers, submits two fictional lost reports through the authenticated API, verifies actual ranked results/explanations, and checks invalid input rejection. Keep the windows open. The smoke test is not a substitute for testing the phone.

## Android Studio emulator (preferred)
Use Louis's codex/louis-deliverable3-demo branch and build:
    .\gradlew.bat -PdemoFirebase=true assembleDebug
Install the debug APK on an Android Studio emulator. It uses 10.0.2.2 for API 8000, Auth 9099 and Storage 9199. Sign in with demo-student@strathmore.edu or demo-office@strathmore.edu; password LocalDemo123! (emulator only). Only office_staff records found inventory. Do not use actual accounts or clear production drafts.

## Android connection
The Android Studio emulator is the supported presentation target. Android build and USB configuration belong in [MAD_project](https://github.com/luiz-zer0/MAD_project/tree/codex/louis-deliverable3-demo). Do not use a physical phone until both API and Firebase hosts are verified in the Android repository. Preserve existing production drafts.

## Rehearsal
Use the seeded HP and Dell chargers as inventory. Submit two new valid lost reports on the student app with distinct charger descriptions, refresh until matching completes, display actual score and explanation, then demonstrate blank input rejection. Use the office account to record a found item and, if time permits, demonstrate claim review. The model runs locally exactly as in the backend. Notebook section 7A was executed successfully in GitHub Actions (run 45503554200): Top-1 4/8, Recall@5 7/8, MRR@5 0.629, false suggestions 2/2. It is a separate operational ranker evaluation, not a mobile device test. The preview API on port 8001 is not the authenticated mobile service. No claim of production deployment or device testing is made by this configuration.
