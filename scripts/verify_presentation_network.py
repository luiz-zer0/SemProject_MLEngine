"""Exercise the real HTTP service and NLP worker against demo Firebase emulators."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
from firebase_admin import auth

from service.inference import TfidfMatcher
from service.runtime import db, firebase_app
from service.worker import process_job

BASE = "http://127.0.0.1:8000"


def login(role: str) -> dict[str, str]:
    email = f"presentation-{uuid4().hex}@strathmore.edu"
    account = auth.create_user(email=email, password="LocalDemo123!", email_verified=True, app=firebase_app())
    auth.set_custom_user_claims(account.uid, {"role": role}, app=firebase_app())
    result = httpx.post(
        "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo",
        json={"email": email, "password": "LocalDemo123!", "returnSecureToken": True}, timeout=15,
    )
    result.raise_for_status()
    return {"Authorization": f"Bearer {result.json()['idToken']}"}


def run() -> None:
    if not os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") or not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        raise SystemExit("Auth and Firestore emulators are required")
    if os.environ.get("FIREBASE_PROJECT_ID", "demo-strathmore-lost-found") != "demo-strathmore-lost-found":
        raise SystemExit("This smoke test refuses non-demo Firebase projects")
    os.environ["APP_ENV"] = "emulator"
    os.environ["FIREBASE_PROJECT_ID"] = "demo-strathmore-lost-found"
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "service.api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    try:
        with httpx.Client(base_url=BASE, timeout=15) as client:
            for _ in range(50):
                if server.poll() is not None:
                    raise RuntimeError("API server exited before becoming healthy")
                try:
                    if client.get("/health").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(0.2)
            else:
                raise RuntimeError("API server did not become healthy")
            student, office, stranger = login("student"), login("office_staff"), login("student")
            body = {"request_id": str(uuid4()), "report_type": "found", "item_name": "Metal water bottle",
                    "description": "blue metal water bottle with scratched lid", "category_id": "metal_water_bottle",
                    "location_id": "cafeteria", "event_date": "2026-11-01", "colour": "blue"}
            assert client.post("/v1/reports", json=body, headers=student).status_code == 403
            found_response = client.post("/v1/reports", json=body, headers=office)
            assert found_response.status_code == 201, found_response.text
            found_id = found_response.json()["id"]
            lost_body = {**body, "request_id": str(uuid4()), "report_type": "lost",
                         "item_name": "Water flask", "description": "my blue flask has a scraped cap",
                         "location_id": "msb"}
            assert client.post("/v1/reports", json={**lost_body, "description": ""}, headers=student).status_code == 422
            lost_response = client.post("/v1/reports", json=lost_body, headers=student)
            assert lost_response.status_code == 201, lost_response.text
            lost_id = lost_response.json()["id"]
            store = db()
            job = store.collection("matching_jobs").document(lost_id)
            assert process_job(store, job, TfidfMatcher()) is True
            assert client.get(f"/v1/reports/lost/{lost_id}/matches", headers=stranger).status_code == 403
            matches_response = client.get(f"/v1/reports/lost/{lost_id}/matches", headers=student)
            matches_response.raise_for_status()
            result = matches_response.json()
            assert result["matching_status"] == "complete"
            assert result["matches"] and result["matches"][0]["found_id"] == found_id
            first = result["matches"][0]
            assert 0 < first["score"] <= 1
            assert first["model_version"].startswith("tfidf-")
            assert "Ownership is unverified" in first["explanation"]
            assert first["workflow"]["release_authorized"] is False
            print({"http": "passed", "report_saved": True, "matching_status": result["matching_status"],
                   "candidate_count": len(result["matches"]), "model_version": first["model_version"],
                   "top_text_similarity": first["score"], "unauthorized_access": "rejected"})
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    run()
