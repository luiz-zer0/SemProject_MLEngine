from uuid import uuid4

from fastapi.testclient import TestClient
from service.api import app
from service.runtime import identity, db


def payload(**changes):
    return {"request_id": str(uuid4()), "report_type": "lost", "item_name": "Blue bottle",
            "description": "Blue metal bottle with scratched lid", "category_id": "metal_water_bottle",
            "location_id": "cafeteria", "event_date": "2026-11-01", **changes}


def test_anonymous_requests_rejected():
    client = TestClient(app)
    assert client.get("/v1/me").status_code == 401
    assert client.post("/v1/reports", json=payload()).status_code == 401
    assert client.get("/health").status_code == 200


def test_validation_and_role_boundaries():
    app.dependency_overrides[identity] = lambda: {"uid": "student", "role": "student"}
    app.dependency_overrides[db] = lambda: None
    try:
        client = TestClient(app)
        assert client.post("/v1/reports", json=payload(report_type="found")).status_code == 403
        assert client.post("/v1/reports", json=payload(owner_uid="another-user")).status_code == 422
        assert client.post("/v1/reports", json=payload(category_id="unknown")).status_code == 422
        assert client.post("/v1/reports", json=payload(event_date="2999-01-01")).status_code == 422
        assert client.post("/v1/reports", json=payload(photo_reference="report_photos/other/x/photo")).status_code == 422
        assert client.post("/v1/claims/x/decision", json={"status": "approved"}).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_cannot_act_as_office_staff():
    app.dependency_overrides[identity] = lambda: {"uid": "admin", "role": "admin"}
    app.dependency_overrides[db] = lambda: None
    try:
        client = TestClient(app)
        assert client.post("/v1/reports", json=payload(report_type="found")).status_code == 403
        assert client.post("/v1/claims/x/decision", json={"status": "approved"}).status_code == 403
    finally:
        app.dependency_overrides.clear()
