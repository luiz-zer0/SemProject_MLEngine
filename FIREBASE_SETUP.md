# Firebase + Android + NLP matching service

This integration uses Firebase Authentication, Cloud Firestore, an authenticated FastAPI service,
and a separate worker using the shared TF-IDF and knowledge-agent pipeline.
There is no CLIP, image inference, or vector database. Existing experiment scripts and results
are not replaced. Photographs are viewed by their uploader and authorized staff only.

Validation on 19 November 2026: the Android debug APK and unit tests pass; service role tests,
the end-to-end Firebase emulator flow, and Firestore/Storage authorization tests pass. The APK
was installed and launched on a connected Samsung Android device. Signed-in staff/admin screens
could not be tested on that device because no live staff/admin claim or deployed API exists.

The live project is `lost-and-found-9671c`. Email-link authentication and Firestore rules are
configured. Firebase Console requires a billing upgrade before Storage can be initialized on
this Spark-plan project. Photo upload is therefore unavailable in the connected app. The API
and matching worker are not deployed; a production Android build cannot submit or load reports
until they have an HTTPS endpoint. The app presents honest offline states meanwhile.

## Local setup (no Firebase account required)

Use Python 3.12+, Node.js supported by firebase-tools, and Java 21+ on PATH.
On this computer Java is available in Android Studio's `jbr/bin` folder.
Run these commands from `SemProject_MLEngine`:

```powershell
py -3.12 -m venv .venv-service
.\.venv-service\Scripts\python.exe -m pip install -r requirements-service.lock.txt
.\.venv-service\Scripts\python.exe -m scripts.export_mobile_model
cd firebase
npm ci
cd ..
```

In separate terminals, run:

```powershell
.\scripts\start_local.ps1 -Service emulators
.\scripts\start_local.ps1 -Service api
.\scripts\start_local.ps1 -Service worker
```

After the emulators start, seed fictional accounts once:

```powershell
.\scripts\start_local.ps1 -Service seed
```

Local accounts: `demo-student@strathmore.edu` and `demo-office@strathmore.edu`.
Both use `LocalDemo123!`. The seed script refuses non-emulator projects.
The Emulator UI is at http://127.0.0.1:4000 and API docs at http://127.0.0.1:8000/docs.
Emulator data is temporary unless you explicitly export/import it with Firebase CLI.

Clone [MAD_project](https://github.com/luiz-zer0/MAD_project), open it in Android Studio, and run the debug
build on an Android emulator. Without `firebase.properties`, debug connects to the host
through `10.0.2.2`. The API/Auth/Storage ports are 8000/9099/9199. This configuration is
for the Android emulator; a physical device needs a deliberately configured development
connection. Release builds never enable the emulator settings.

1. Sign in as the office account and check in a found item.
2. Sign out, sign in as the student, and submit a lost item in the same category.
3. Refresh Reports after the worker runs, then review suggestions and request ownership review.
4. Sign in as office staff, check the claim and report details, approve after verification,
   then mark collected only after physical handover. Both reports close together.

## Persistence, security and matching

- FastAPI verifies Firebase ID tokens, email verification and the university email domain.
  `role` is a server-assigned custom claim, never a user-selected profile field.
- Report creation atomically stores a report and matching job. A stable request ID prevents
  retries from creating duplicate reports; changing the body for the same ID returns 409.
- The worker uses a 120-second lease and retries failures up to three times. Failed jobs can
  be explicitly retried. Model failure never removes the report. Run one worker initially.
- Active candidates are ranked through the TF-IDF and knowledge-agent pipeline. More than 200
  candidates fails explicitly rather than silently evaluating a truncated set. The app shows
  up to 20 ranked suggestions; report lists are limited to 100 records per type.
- Scores are retrieval evidence, not validated ownership probabilities. No automatic
  release or ownership decision is made.
- Firestore client writes are denied; business mutations run through authorized API endpoints.
  Admin SDK bypasses Rules, so API ownership and role checks are mandatory.
- Storage rules for private immutable photos are tested in the emulator. Live photo uploads remain
  disabled until Storage is initialized and its rules are deployed.
- Claim approval reserves both reports transactionally; collection closes both and writes an
  audit record and handover receipt. A second claim cannot reserve an already-reserved report.
- Candidate details are returned in a sanitized response. The claimant provides private ownership
  details to office staff; technical admins cannot read office evidence or act as office staff.
- Wallet and document check-in requires a seal and secure custody location. Retention review only
  flags items after an admin has configured that category's retention period; it does not dispose of items.
- In-app notifications work locally. FCM push is wired for a real project, with generic text,
  and is skipped in emulator mode. FCM has no local emulator; live delivery needs cloud testing.
- This API-mediated workflow requires connectivity to submit. It does not claim Firestore's
  automatic offline synchronization for API requests. A saved local input is not a submitted report.

## Tests

For an automated run that starts/stops its own emulators, use this from `firebase/`
with Java on PATH and no other emulators running:

```powershell
npx.cmd firebase-tools emulators:exec --project demo-strathmore-lost-found --only "auth,firestore,storage" "..\.venv-service\Scripts\python.exe ..\scripts\verify_local.py"
```

To run checks against already-running emulators:

```powershell
.\.venv-service\Scripts\python.exe -m pytest tests -q
# With local emulators running, in this shell:
$env:APP_ENV='emulator'
$env:FIREBASE_PROJECT_ID='demo-strathmore-lost-found'
$env:FIREBASE_AUTH_EMULATOR_HOST='127.0.0.1:9099'
$env:FIRESTORE_EMULATOR_HOST='127.0.0.1:8080'
$env:RUN_FIREBASE_INTEGRATION='1'
.\.venv-service\Scripts\python.exe -m pytest tests/test_firebase_integration.py -q
cd firebase
node rules.test.mjs
```

## Completing the live project

1. The project, Android app, email-link sign-in and Firestore are already configured.
2. Copy the Android project's `firebase.properties.example` to `firebase.properties` and fill
   the identifiers from its `google-services.json`. This app initializes Firebase explicitly,
   so it does not require the Google Services Gradle plugin. Never put Admin keys in this file.
3. Firestore rules were deployed. After a billing upgrade and Storage setup, deploy
   `firebase/storage.rules` using `firebase deploy --only storage --project lost-and-found-9671c`.
4. Deploy the API and worker with `FIREBASE_PROJECT_ID`, `MODEL_PATH` and Application Default
   Credentials for a dedicated service account. Unset all emulator environment variables and
   set `APP_ENV=production`. Use HTTPS for the API URL in the Android configuration.
5. Grant office and technical-admin custom claims through trusted administrative tooling. The local seed script
   intentionally cannot assign production roles. Users must refresh/sign in again after a role change.
   Once the API is deployed, a signed-in technical admin can look up an existing account by exact
   Strathmore email in Access & Audit and assign student, office, or admin access. The account must
   have a verified email. Changes preserve unrelated claims, revoke the affected account's sessions,
   and record the actor, target UID, old role, and new role in the audit log. The admin cannot change
   their own role. The app never receives Admin SDK credentials.
6. Verify cloud sign-in/email delivery, Storage access, FCM notification permission/delivery,
   API/worker restart recovery and Android runtime behavior before using real reports.

The Dockerfile packages the API. Deploy the worker using the same
image with command `python -m service.worker`. The container recipe is provided but has not been
built locally; local validation uses the Python environment and Firebase emulators.

The code is a working integration baseline, not a finished production operations setup:
add deployment monitoring, rate limiting, pagination, retention/deletion policy and independently
reviewed campus evaluation before a real rollout. Sensitive-ID matching is outside this general-item flow.

Official references: https://firebase.google.com/docs/android/setup,
https://firebase.google.com/docs/auth/admin/verify-id-tokens,
https://firebase.google.com/docs/emulator-suite/connect_auth,
https://firebase.google.com/docs/emulator-suite/connect_firestore.
