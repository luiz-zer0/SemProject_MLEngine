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
from service.inference import Matcher

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
    student, stranger, office = login(), login(), login("office_staff")
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
    store = db()

    class BrokenModel:
        def score(self, *args):
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
    process_job(store, job, Matcher("artifacts/mobile_model.joblib"))
    result = client.get(f"/v1/reports/lost/{lost_id}/matches", headers=student).json()
    assert result["matching_status"] == "complete"
    match = next(row for row in result["matches"] if row["found_id"] == found_id)
    assert 0 <= match["score"] <= 1
    match_id = match["id"]
    assert client.post(f"/v1/matches/{match_id}/claim", headers=stranger).status_code == 403
    assert client.post(f"/v1/matches/{match_id}/claim", headers=student).status_code == 201
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "approved"}, headers=student).status_code == 403
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "collected"}, headers=office).status_code == 409
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "approved"}, headers=office).status_code == 200
    competing = client.post("/v1/reports", json={**body, "request_id": str(uuid4())}, headers=stranger).json()
    process_job(store, store.collection("matching_jobs").document(competing["id"]), Matcher("artifacts/mobile_model.joblib"))
    competing_id = f"{competing['id']}_{found_id}"
    assert client.post(f"/v1/matches/{competing_id}/claim", headers=stranger).status_code == 201
    assert client.post(f"/v1/claims/{competing_id}/decision", json={"status": "approved"}, headers=office).status_code == 409
    assert client.post(f"/v1/claims/{match_id}/decision", json={"status": "collected"}, headers=office).status_code == 200
    assert store.collection("found_reports").document(found_id).get().to_dict()["status"] == "closed"
    assert client.get("/v1/notifications", headers=student).json()["notifications"]
