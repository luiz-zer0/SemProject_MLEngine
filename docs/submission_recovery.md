# Local report submission recovery

The presentation uses an isolated emulator project and the Android Studio emulator. If submission fails, distinguish local draft storage from confirmed API persistence.

1. Run the startup command in [local presentation](LOCAL_PRESENTATION.md); keep all three service windows open.
2. Confirm port 8000 is the authenticated API (`GET /health`); `GET /ready` checks Firestore access. The optional preview uses 8001 and cannot save reports.
3. Confirm the Android demo build uses `10.0.2.2` and `-PdemoFirebase=true`. Sign in with the seeded local student or office account, never a production account.
4. An HTTP 401 indicates sign-in failure, 403 a role/access restriction, 422 invalid input and 409 a conflicting retry. Only office_staff records found items. A transport error may leave a request unconfirmed: retry the unchanged request ID, not a duplicate report.
5. After successful submission, check the worker for pending/completed matching and refresh the report screen.

The backend smoke test passed in CI; the current Android app still needs a device rehearsal. Preserve existing drafts. The USB physical-phone configuration is not verified; all Android-specific changes belong in MAD_project. Do not deploy the backend or enable billing to troubleshoot the local demo.
