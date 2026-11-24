# Free local presentation — Windows
No deployment, Firebase cloud credentials or billing upgrade required. This runs the real authenticated FastAPI service, Firestore/Auth emulators and operational NLP worker. All records and accounts are fictional. The optional cloud deployment remains separate in PR #17.

## One-time preparation and startup
Use Python 3.12, Node.js compatible with the pinned Firebase CLI, and Java 21 (Android Studio JBR). From the ML repository root:
    powershell -ExecutionPolicy Bypass -File scripts/start_presentation.ps1 -Install
On later runs omit -Install. Install/download dependencies and emulator binaries before presentation day. Close previously started demo windows before restarting. The script checks occupied ports instead of killing processes; it launches three service windows, seeds accounts and two fictional found chargers, submits two fictional lost reports through the authenticated API, verifies actual ranked results/explanations, and checks invalid input rejection. Keep the windows open. The smoke test is not a substitute for testing the phone.

## Android Studio emulator (preferred)
Use Louis's codex/louis-deliverable3-demo branch and build:
    .\gradlew.bat -PdemoFirebase=true assembleDebug
Install the debug APK on an Android Studio emulator. It uses 10.0.2.2 for API 8000, Auth 9099 and Storage 9199. Sign in with demo-student@strathmore.edu or demo-office@strathmore.edu; password LocalDemo123! (emulator only). Only office_staff records found inventory. Do not use actual accounts or clear production drafts.

## USB phone (optional)
Direct Android repository writes were denied. The ML repository contains a narrow compatibility patch. With a local Android checkout on Louis's branch:
    .\.venv-service\Scripts\python.exe -m scripts.patch_android_demo ..\MAD_project
    .\.venv-service\Scripts\python.exe -m scripts.patch_android_demo ..\MAD_project --apply
Review git diff; the script refuses unfamiliar source. On the laptop with authorized USB debugging:
    adb devices
    adb reverse tcp:8000 tcp:8000
    adb reverse tcp:9099 tcp:9099
    adb reverse tcp:9199 tcp:9199
    cd ..\MAD_project
    .\gradlew.bat -PdemoFirebase=true -PdemoHost=127.0.0.1 assembleDebug
    adb install -r app\build\outputs\apk\debug\app-debug.apk
Prefer a separate test phone or emulator; preserve existing drafts. Reconnect ADB reverse if disconnected.

## Rehearsal
Use the seeded HP and Dell chargers as inventory. Submit two new valid lost reports on the student app with distinct charger descriptions, refresh until matching completes, display actual score and explanation, then demonstrate blank input rejection. Use the office account to record a found item and, if time permits, demonstrate claim review. The model runs locally exactly as in the backend. Notebook section 7A is a separate operational ranker evaluation; execute it before citing metrics. The preview API on port 8001 is not the authenticated mobile service. No claim of production deployment or device testing is made by this configuration.
