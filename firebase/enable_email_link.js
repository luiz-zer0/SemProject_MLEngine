// One-time Firebase Auth setup for the Lost & Found Android app.
// Uses the existing Firebase CLI login; never prints or stores an access token.
const auth = require('firebase-tools/lib/auth');

async function main() {
  const projectId = 'lost-and-found-9671c';
  const account = auth.getGlobalDefaultAccount();
  if (!account?.tokens?.refresh_token) throw new Error('Firebase CLI login is required.');
  const token = (await auth.getAccessToken(account.tokens.refresh_token,
    ['https://www.googleapis.com/auth/cloud-platform'])).access_token;
  const url = `https://identitytoolkit.googleapis.com/admin/v2/projects/${projectId}/config`;
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const currentResponse = await fetch(url, { headers });
  if (!currentResponse.ok) throw new Error(`Reading Auth config failed (${currentResponse.status}).`);
  const current = await currentResponse.json();
  console.log(`Current email sign-in: ${JSON.stringify(current.signIn?.email)}`);
  if (!current.authorizedDomains?.includes(`${projectId}.firebaseapp.com`)) {
    throw new Error('The Firebase Hosting domain is not authorized for Auth links.');
  }
  if (current.signIn?.email?.enabled && current.signIn?.email?.passwordRequired !== true) return;
  const response = await fetch(`${url}?updateMask=signIn.email.enabled,signIn.email.passwordRequired`, {
    method: 'PATCH', headers,
    body: JSON.stringify({ signIn: { email: { enabled: true, passwordRequired: false } } }),
  });
  if (!response.ok) throw new Error(`Updating Auth config failed (${response.status}).`);
  const updated = await response.json();
  console.log(`Updated email sign-in: ${JSON.stringify(updated.signIn?.email)}`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
