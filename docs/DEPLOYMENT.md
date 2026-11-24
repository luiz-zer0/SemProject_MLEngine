# Hosted API and matching worker deployment

Status: deployment configuration prepared; no live hosting resources have been created. This branch requires review, unit/integration tests, and a successful container build before live deployment. Production Firebase project: lost-and-found-9671c. Never use emulator tokens or demo credentials in production.

## Render blueprint

The root render.yaml defines an HTTPS web API running service.api:app and a separate continuously running worker (python -m service.worker). The API uses the free plan; the worker uses the smallest paid plan. Render's free API may sleep and cold start; monitor memory, latency and usage. Review current prices before approving any charges. The worker polls at 15 seconds to reduce idle Firestore reads and backs off on errors. Check actual Firebase quotas and worker logs; do not assume the free Firebase allowance guarantees no charges or uninterrupted service.

1. Connect an authorized Render account and the GitHub repository. Choose the reviewed branch or merged main containing render.yaml.
2. In Firebase/Google Cloud, an authorized project administrator must provide a dedicated service account with only the roles necessary for Firestore reads/writes, Firebase Authentication account operations and FCM where used. Prefer managed identity/ADC on Google Cloud; for Render, enter the service account JSON in FIREBASE_ADMIN_CREDENTIALS_JSON via encrypted secret settings for both processes. Do not paste credentials into chat, commit them, or put them in the Android app. Confirm the credential project ID matches the production project. Review and rotate keys according to the project's security requirements.
3. Review the plan, service names, billing and access permissions, then create the Blueprint if authorized. No emulator environment variables should be set. Build logs must show both containers starting.
4. Record the HTTPS URL returned by Render (never guess a URL). GET /health must identify authenticated_reports; GET /ready must return HTTP 200 with firestore reachable (cached for up to 30 seconds). Worker logs must show normal operation. Health is not evidence of completed matching.
5. With authorized isolated test accounts, check /v1/me, create a fictional found report as office_staff and a lost report as student, verify matching_jobs and real recommendations, and test invalid inputs and duplicate retries. Technical admin remains restricted from office check-in. Avoid modifying real records. Do not claim success until actual verification.
6. In MAD_project, set ML_API_BASE_URL in local firebase.properties to the verified HTTPS URL. Keep the existing public Firebase app identifiers; never place admin credentials there. Build and install the updated APK. Test on an untethered device. An installed older APK still uses its original build-time URL.

## Verification commands after deployment

PowerShell: Invoke-RestMethod https://<verified-api-host>/health ; Invoke-RestMethod https://<verified-api-host>/ready . Do not use the literal placeholder. Review provider logs and run the emulator regression tests described in FIREBASE_SETUP.md before production verification.

References: https://render.com/docs/blueprint-spec ; https://render.com/docs/background-workers ; https://render.com/pricing ; https://firebase.google.com/docs/admin/setup .

## Alternative: Cloudflare Tunnel on an existing authorized host

See [Cloudflare deployment](CLOUDFLARE_DEPLOYMENT.md) and compose.cloudflare.yaml. This option avoids a new Render background-worker subscription if suitable compute is already available; it does not provide free compute or a verified live endpoint.
