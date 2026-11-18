import { readFileSync } from 'node:fs';
import { initializeTestEnvironment, assertFails, assertSucceeds } from '@firebase/rules-unit-testing';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { ref, uploadBytes, getBytes } from 'firebase/storage';

const env = await initializeTestEnvironment({
  projectId: 'demo-strathmore-lost-found',
  firestore: { host: '127.0.0.1', port: 8080, rules: readFileSync('firestore.rules', 'utf8') },
  storage: { host: '127.0.0.1', port: 9199, rules: readFileSync('storage.rules', 'utf8') }
});
try {
  const owner = env.authenticatedContext('owner', {email: 'owner@strathmore.edu', email_verified: true});
  const other = env.authenticatedContext('other', {email: 'other@strathmore.edu', email_verified: true});
  const staff = env.authenticatedContext('staff', {email: 'staff@strathmore.edu', email_verified: true, role: 'office_staff'});
  const anonymous = env.unauthenticatedContext();
  await env.withSecurityRulesDisabled(async context => {
    await setDoc(doc(context.firestore(), 'lost_reports/rules-test'), {owner_uid: 'owner', status: 'active'});
  });
  await assertSucceeds(getDoc(doc(owner.firestore(), 'lost_reports/rules-test')));
  await assertSucceeds(getDoc(doc(staff.firestore(), 'lost_reports/rules-test')));
  await assertFails(getDoc(doc(other.firestore(), 'lost_reports/rules-test')));
  await assertFails(getDoc(doc(anonymous.firestore(), 'lost_reports/rules-test')));
  await assertFails(setDoc(doc(owner.firestore(), 'users/owner'), {role: 'admin'}));
  await assertFails(setDoc(doc(staff.firestore(), 'matches/forged'), {score: 1}));
  await assertFails(getDoc(doc(owner.firestore(), 'matching_jobs/private')));
  const path = `report_photos/owner/${Date.now()}/photo`;
  await assertSucceeds(uploadBytes(ref(owner.storage(), path), new Uint8Array([1, 2, 3]), {contentType: 'image/png'}));
  await assertSucceeds(getBytes(ref(staff.storage(), path)));
  await assertFails(getBytes(ref(other.storage(), path)));
  await assertFails(uploadBytes(ref(owner.storage(), path), new Uint8Array([4]), {contentType: 'image/png'}));
  await assertFails(uploadBytes(ref(owner.storage(), `report_photos/owner/${Date.now()}bad/photo`), new Uint8Array([1]), {contentType: 'text/plain'}));
  console.log('Firestore and Storage authorization tests passed.');
} finally {
  await env.cleanup();
}
