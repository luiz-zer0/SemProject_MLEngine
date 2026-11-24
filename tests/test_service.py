from uuid import uuid4

from fastapi.testclient import TestClient
from service.api import app
from service.api import auth_users
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
        assert client.get("/v1/admin/category-rules").status_code == 403
        assert client.get("/v1/admin/audit").status_code == 403
        assert client.post("/v1/reports", json=payload(report_type="found", category_id="wallet")).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_admin_cannot_act_as_office_staff():
    app.dependency_overrides[identity] = lambda: {"uid": "admin", "role": "admin"}
    app.dependency_overrides[db] = lambda: None
    try:
        client = TestClient(app)
        assert client.post("/v1/reports", json=payload(report_type="found")).status_code == 403
        assert client.post("/v1/claims/x/decision", json={"status": "approved"}).status_code == 403
        assert client.put("/v1/admin/category-rules/unknown", json={"retention_days": 30}).status_code == 404
        assert client.put("/v1/admin/category-rules/wallet", json={"retention_days": 30}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_admin_role_management_preserves_claims_and_audits():
    from types import SimpleNamespace

    class Users:
        def __init__(self):
            self.account = SimpleNamespace(uid="office-1", email="office@strathmore.edu",
                                           email_verified=True, custom_claims={"feature": "keep"})

        def by_email(self, email):
            assert email == self.account.email
            return self.account

        def by_uid(self, uid):
            assert uid == self.account.uid
            return self.account

        def set_claims(self, uid, claims):
            self.account.custom_claims = claims

        def revoke_sessions(self, uid):
            self.revoked_uid = uid

    class Collection:
        def __init__(self):
            self.events = []

        def document(self):
            return self

        def set(self, event):
            self.events.append(event)

    class DB:
        def __init__(self):
            self.audit = Collection()

        def collection(self, name):
            assert name == "audit_logs"
            return self.audit

    users, database = Users(), DB()
    app.dependency_overrides[identity] = lambda: {"uid": "admin-1", "role": "admin"}
    app.dependency_overrides[auth_users] = lambda: users
    app.dependency_overrides[db] = lambda: database
    try:
        client = TestClient(app)
        assert client.get("/v1/admin/accounts", params={"email": "office@strathmore.edu"}).json()["account"]["role"] == "student"
        response = client.put("/v1/admin/accounts/office-1/role", json={"role": "office_staff"})
        assert response.status_code == 200
        assert response.json()["account"]["role"] == "office_staff"
        assert users.account.custom_claims == {"feature": "keep", "role": "office_staff"}
        assert users.revoked_uid == "office-1"
        assert database.audit.events[0]["target_uid"] == "office-1"
        client.put("/v1/admin/accounts/office-1/role", json={"role": "office_staff"})
        assert len(database.audit.events) == 1
        client.put("/v1/admin/accounts/office-1/role", json={"role": "student"})
        assert users.account.custom_claims == {"feature": "keep"}
        assert client.put("/v1/admin/accounts/admin-1/role", json={"role": "student"}).status_code == 409
        users.account.email_verified = False
        assert client.put("/v1/admin/accounts/office-1/role", json={"role": "admin"}).status_code == 422
        assert client.get("/v1/admin/accounts", params={"email": "outside@example.com"}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_only_admin_can_manage_roles():
    app.dependency_overrides[identity] = lambda: {"uid": "office-1", "role": "office_staff"}
    app.dependency_overrides[db] = lambda: None
    try:
        client = TestClient(app)
        assert client.get("/v1/admin/accounts", params={"email": "office@strathmore.edu"}).status_code == 403
        assert client.put("/v1/admin/accounts/other/role", json={"role": "admin"}).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_health_identifies_authenticated_service():
    response = TestClient(app).get("/health")
    assert response.json()["service"] == "authenticated_reports"


def test_readiness_reports_firestore_failure(monkeypatch):
    from fastapi import HTTPException
    from service import api

    def unavailable():
        raise HTTPException(503, "not configured")

    monkeypatch.setattr(api, "db", unavailable)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["firestore"] == "unavailable"


def test_firebase_configuration_failure_is_not_invalid_login(monkeypatch):
    from service import runtime
    runtime.firebase_app.cache_clear()
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    try:
        response = TestClient(app).get("/v1/me", headers={"Authorization": "Bearer sample-token"})
        assert response.status_code == 503
    finally:
        runtime.firebase_app.cache_clear()
