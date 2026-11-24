# Cloudflare Tunnel deployment (existing host)

Status: prepared, NOT deployed or tested. The Cloudflare free Tunnel provides HTTPS ingress, not CPU or RAM for the existing FastAPI/scikit-learn service. Reuse an authorized, running Linux VM/server with adequate memory and Docker Compose v2; verify its current compute charges separately. Do not create a paid VM or modify another group's shared server without permission. The existing Firebase project remains unchanged.

## Before starting
- Review the branch and run the tests described in FIREBASE_SETUP.md. Build the container on the actual host and check its memory requirements.
- Obtain authorized access to the host, Cloudflare account/domain and the Firebase project lost-and-found-9671c. Do not upgrade billing without approval.
- Use a dedicated least-privilege Firebase service account appropriate for report persistence, authentication operations and FCM if enabled. Provision its JSON securely outside the checkout, or use an approved managed identity with a separately reviewed deployment. Never commit it, paste it into chat, or place it in Android. Limit file access to the authorized containers and host administrator.
- Create a remotely managed Cloudflare Tunnel. Configure a dedicated unused API hostname under a domain already managed by Cloudflare, and set the origin service URL to http://api:8000 (the Docker service name). Do not change unrelated DNS records. Store the tunnel token in a separate file outside the checkout, readable only by the authorized container and host administrator. Verify the cloudflared container user can read its mounted token file without making it publicly readable. Use a cloudflared version >= 2025.4.0 for --token-file; pin the tested image digest before production rollout.

## Run the three containers
Copy .env.cloudflare.example to .env.cloudflare and replace its example paths with the actual absolute paths. The environment file is ignored by Git; it contains paths, not secret values. From the reviewed checkout:

    docker compose --env-file .env.cloudflare -f compose.cloudflare.yaml config --quiet
    docker compose --env-file .env.cloudflare -f compose.cloudflare.yaml up -d --build
    docker compose --env-file .env.cloudflare -f compose.cloudflare.yaml ps
    docker compose --env-file .env.cloudflare -f compose.cloudflare.yaml logs --tail=100 api worker tunnel

No host port is published. The tunnel forwards HTTPS requests to FastAPI on the shared Compose network. The worker is not publicly exposed. Both use the same Firebase project and ADC secret mount. A 30-second default worker polling interval reduces idle Firestore reads; verify quotas, latency and memory. Container restart policies recover exited processes, not every possible health failure.

## Verification
- Confirm the actual hostname from Cloudflare and verify /health identifies authenticated_reports and /ready returns 200. Do not invent an endpoint.
- Ensure Cloudflare does not cache any authenticated API responses; bypass caching for /v1/* and diagnostic endpoints. Do not enable interactive Access login on this mobile API unless the Android client is deliberately adapted; existing Firebase token/role checks remain required.
- Verify authenticated /v1/me and a controlled lost/found report pair, the Firestore job, worker output, explanations, invalid inputs and idempotent retries. Use approved test accounts/records only.
- Build and reinstall the Android app with its ML_API_BASE_URL set to the verified HTTPS hostname, retaining the correct Firebase identifiers. Confirm operation from an untethered phone. Old APKs do not update their embedded URL automatically.

No new Cloudflare Tunnel fee is required for a published application on the free plan, but the host, domain and Firebase usage may have costs. A quick development tunnel is temporary and does not replace a production deployment. If no authorized server exists, evaluate an on-demand backend instead of an always-running free worker.

Official documentation: https://developers.cloudflare.com/tunnel/get-started/ and https://developers.cloudflare.com/tunnel/reference/run-parameters/
