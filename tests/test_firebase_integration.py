"""Run explicitly against local emulators, never a real Firebase project."""
import os
import time
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth

from service.api import app
from service.runtime import db, firebase_app
from service.worker import process_job
from service.inference import TfidfMatcher

pytestmark = pytest.mark.skipif(os.environ.get("RUN_FIREBASE_INTEGRATION") != "1", reason="Local emulators required")


def login(role="student", verified=True):
    assert os.environ.get("APP_ENV") == "emulator"
    assert os.environ["FIREBASE_PROJECT_ID"].startswith("demo-")
    email = f"test-{uuid4().hex}@strathmore.edu"
    user = auth.create_user(email=email, password="LocalTest123!", email_verified=verified, app=firebase_app())
    auth.set_custom_user_claims(user.uid, {"role": role}, app=firebase_app())
    result = httpx.post("http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo",
                        json={"email": email, "password": "LocalTest123!", "returnSecureToken": True}).json()
    return {"Authorization": f"Bearer {result['idToken']}"}


def test_end_to_end_persistence_matching_claims_and_access():
    client = TestClient(app)
    student, stranger, office, admin = login(), login(), login("office_staff"), login("admin")
    assert client.get("/v1/me", headers=login(verified=False)).status_code == 403
    body = {"request_id": str(uuid4()), "report_type": "lost", "item_name": "Blue bottle",
            "description": "blue metal water bottle scratched lid", "category_id": "metal_water_bottle",
            "location_id": "cafeteria", "event_date": "2026-11-01", "colour": "blue", "material": "metal"}
    first = client.post("/v1/reports", json=body, headers=student)
    assert first.status_code == 201, first.text
    lost_id = first.json()["id"]
    assert first.json()["matching_status"] == "pending"
    assert client.post("/v1/reports", json=body, headers=student).json()["id"] == lost_id
    assert client.post("/v1/reports", json={**body, "description": "different"}, headers=student).status_code == 409
    assert client.get(f"/v1/reports/lost/{lost_id}/matches", headers=stranger).status_code == 403
    found_body = {**body, "request_id": str(uuid4()), "report_type": "found"}
    assert client.post("/v1/reports", json=found_body, headers=student).status_code == 403
    found = client.post("/v1/reports", json=found_body, headers=office)
    assert found.status_code == 201, found.text
    found_id = found.json()["id"]
    sensitive = {**found_body, "request_id": str(uuid4()), "category_id": "wallet",
                 "item_name": "Wallet", "description": "Brown wallet", "sealed": True,
                 "custody_location": "Locked office cabinet"}
    assert client.post("/v1/reports", json=sensitive, headers=office).status_code == 201
    assert client.post("/v1/reports", json={**sensitive, "request_id": str(uuid4()), "sealed": False}, headers=office).status_code == 422
    assert client.post("/v1/reports", json={**found_body, "request_id": str(uuid4())}, headers=admin).status_code == 403
    assert client.get("/v1/admin/category-rules", headers=office).status_code == 403
    assert client.put("/v1/admin/category-rules/wallet", json={"retention_days": 30,
        "restricted": True, "requires_seal": True}, headers=admin).status_code == 200
    assert client.get("/v1/admin/category-rules", headers=admin).json()["rules"]
    target_email = f"role-{uuid4().hex}@strathmore.edu"
    target = auth.create_user(email=target_email, email_verified=True, app=firebase_app())
    assert client.get("/v1/admin/accounts", params={"email": target_email}, headers=office).status_code == 403
    account = client.get("/v1/admin/accounts", params={"email": target_email}, headers=admin)
    assert account.status_code == 200 and account.json()["account"]["uid"] == target.uid
    changed = client.put(f"/v1/admin/accounts/{target.uid}/role", json={"role": "office_staff"}, headers=admin)
    assert changed.status_code == 200 and changed.json()["account"]["role"] == "office_staff"
    assert auth.get_user(target.uid, app=firebase_app()).custom_claims["role"] == "office_staff"
    assert client.get("/v1/admin/audit", headers=admin).json()["events"]
    assert client.get("/v1/office/unclaimed", headers=admin).status_code == 403
    assert client.get("/v1/office/unclaimed", headers=office).status_code == 200
    store = db()

    class BrokenModel:
        def recommend(self, *args):
            raise RuntimeError("Injected model outage")
        version = "broken"

    job = store.collection("matching_jobs").document(lost_id)
    job.update({"status": "running", "lease_until": time.time() + 120, "lease": "other-worker"})
    assert process_job(store, job, BrokenModel()) is False
    job.update({"lease_until": 0})
    process_job(store, job, BrokenModel())
    assert store.collection("lost_reports").document(lost_id).get().exists
    assert job.get().to_dict()["status"] == "pending"
    job.update({"lease_until": 0})
    process_job(store, job, TfidfMatcher())
    result = client.get(f"/v1/reports/lost/{lost_id}/matches", headers=student).json()
    assert result["matching_status"] == "complete"
    match = next(row for row in result["matches"] if row["found_id"] == found_id)
    assert 0 <= match["score"] <= 1
    match_id = match["id"]
    candidate = client.get(f"/v1/matches/{match_id}/candidate", headers=student).json()["candidate"]
    assert candidate["id"] == found_id and "description" not in candidate and "photo_reference" not in candidate
    assert client.get(f"/v1/matches/{match_id}/candidate", headers=stranger).status_code == 403
    proof = {"ownership_details": "A small scratch is inside the left pocket."}
    assert client.post(f"/v1/matches/{match_id}/claim", json=proof, headers=stranger).status_code == 403
    assert client.post(f"/v1/matches/{match_id}/claim", json=proof, headers=student).status_code == 201
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "approved"}, headers=student).status_code == 403
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "collected"}, headers=office).status_code == 409
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "approved"}, headers=office).status_code == 200
    competing = client.post("/v1/reports", json={**body, "request_id": str(uuid4())}, headers=stranger).json()
    process_job(store, store.collection("matching_jobs").document(competing["id"]), TfidfMatcher())
    competing_id = f"{competing['id']}_{found_id}"
    assert client.post(f"/v1/matches/{competing_id}/claim", json=proof, headers=stranger).status_code == 201
    assert client.post(f"/v1/claims/{competing_id}/decision", json={"status": "approved"}, headers=office).status_code == 409
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "collected"}, headers=office).status_code == 200
    receipt = client.get(f"/v1/claims/{match_id}/receipt", headers=student)
    assert receipt.status_code == 200 and receipt.json()["claim_id"] == match_id
    assert client.get(f"/v1/claims/{match_id}/receipt", headers=stranger).status_code == 403
    assert store.collection("found_reports").document(found_id).get().to_dict()["status"] == "closed"
    assert client.get("/v1/notifications", headers=student).json()["notifications"]


def test_irrelevant_description_and_completed_zero_matches():
    from matching_system.report_relevance import INVALID_DESCRIPTION
    client = TestClient(app)
    student = login()
    body = {"request_id": str(uuid4()), "report_type": "lost", "item_name": "Telescope",
            "description": "I had chicken for lunch.", "category_id": "electronics",
            "location_id": "sbs_building", "event_date": "2026-11-01"}
    before = client.get("/v1/reports", headers=student).json()["reports"]
    rejected = client.post("/v1/reports", json=body, headers=student)
    assert rejected.status_code == 422, rejected.text
    assert rejected.json()["detail"] == INVALID_DESCRIPTION
    assert client.get("/v1/reports", headers=student).json()["reports"] == before
    # Correct the rejected request without changing its id; no report/job was saved.
    body["description"] = "Violet telescope"
    saved = client.post("/v1/reports", json=body, headers=student)
    assert saved.status_code == 201, saved.text
    report_id = saved.json()["id"]
    endpoint = f"/v1/reports/lost/{report_id}/matches"
    queued = client.get(endpoint, headers=student).json()
    assert queued["matching_outcome"] == "in_progress"
    assert queued["match_count"] is None
    process_job(db(), db().collection("matching_jobs").document(report_id), TfidfMatcher())
    completed = client.get(endpoint, headers=student).json()
    assert completed["matching_status"] == "complete"
    assert completed["matching_outcome"] == "no_matches"
    assert completed["match_count"] == 0
    assert completed["matches"] == []
