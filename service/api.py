"""Authenticated report persistence and staff-reviewed matching API."""
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException
from google.cloud import firestore
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .runtime import db, identity, staff

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text())
app = FastAPI(title="Strathmore Lost & Found", version="1.0.0")


class ReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    request_id: UUID
    report_type: Literal["lost", "found"]
    item_name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=3, max_length=2000)
    category_id: str
    location_id: str
    event_date: date
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    colour: str = Field(default="", max_length=100)
    material: str = Field(default="", max_length=100)
    distinctive_features: list[str] = Field(default_factory=list, max_length=10)
    photo_reference: str = Field(default="", max_length=300)

    @field_validator("category_id", "location_id")
    @classmethod
    def canonical(cls, value, info):
        section = "categories" if info.field_name == "category_id" else "locations"
        if value not in {entry["id"] for entry in CATALOG[section]}:
            raise ValueError("Choose an entry from the shared catalog")
        return value

    @field_validator("event_date")
    @classmethod
    def past_date(cls, value):
        if value > datetime.now(ZoneInfo("Africa/Nairobi")).date():
            raise ValueError("Event date cannot be in the future")
        return value

    @field_validator("distinctive_features")
    @classmethod
    def feature_lengths(cls, value):
        if any(len(item) > 200 for item in value):
            raise ValueError("Each feature must be under 200 characters")
        return value


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["approved", "rejected", "collected"]


class DeviceInput(BaseModel):
    token: str = Field(min_length=20, max_length=4096)


def collection(kind):
    if kind not in ("lost", "found"):
        raise HTTPException(404, "Unknown report type")
    return f"{kind}_reports"


def report_access(client, kind, report_id, user):
    snapshot = client.collection(collection(kind)).document(report_id).get()
    if not snapshot.exists:
        raise HTTPException(404, "Report not found")
    row = snapshot.to_dict()
    if row["owner_uid"] != user["uid"] and not staff(user):
        raise HTTPException(403, "This report belongs to another user")
    return row


@app.get("/health")
def health():
    return {"status": "ok", "matching": "separate durable worker"}


@app.get("/v1/me")
def me(user=Depends(identity)):
    return user


@app.get("/v1/catalog")
def catalog(user=Depends(identity)):
    return CATALOG


@app.post("/v1/reports", status_code=201)
def create_report(body: ReportInput, user=Depends(identity), client=Depends(db)):
    if body.report_type == "found" and not staff(user):
        raise HTTPException(403, "Office staff must record found inventory")
    row = body.model_dump(mode="json")
    request_id = row.pop("request_id")
    report_id = hashlib.sha256(f"{user['uid']}:{request_id}".encode()).hexdigest()[:32]
    if body.photo_reference and body.photo_reference != f"report_photos/{user['uid']}/{request_id}/photo":
        raise HTTPException(422, "Photo must belong to this report request")
    digest = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    row.update(id=report_id, owner_uid=user["uid"], status="active", matching_status="pending",
               input_hash=digest, created_at=firestore.SERVER_TIMESTAMP)
    ref = client.collection(collection(body.report_type)).document(report_id)
    job = client.collection("matching_jobs").document(report_id)

    @firestore.transactional
    def save(transaction):
        existing = ref.get(transaction=transaction)
        if existing.exists:
            if existing.to_dict()["input_hash"] != digest:
                raise HTTPException(409, "This request ID was already used with different data")
            return existing.to_dict()
        existing_job = job.get(transaction=transaction)
        if existing_job.exists:
            raise HTTPException(409, "This request ID was already used for another report type")
        transaction.set(ref, row)
        transaction.set(job, {"report_id": report_id, "report_type": body.report_type,
                             "status": "pending", "attempts": 0, "lease_until": 0})
        return row

    saved = save(client.transaction())
    return {"id": report_id, "report_type": body.report_type, "status": "saved",
            "matching_status": saved["matching_status"]}


@app.get("/v1/reports")
def reports(user=Depends(identity), client=Depends(db)):
    rows = []
    for kind in ("lost", "found"):
        query = client.collection(collection(kind))
        if not staff(user):
            query = query.where(filter=firestore.FieldFilter("owner_uid", "==", user["uid"]))
        rows.extend(item.to_dict() for item in query.limit(100).stream())
    return {"reports": rows, "limit_per_type": 100}


@app.get("/v1/reports/{kind}/{report_id}/matches")
def matches(kind: str, report_id: str, user=Depends(identity), client=Depends(db)):
    report = report_access(client, kind, report_id, user)
    query = client.collection("matches").where(filter=firestore.FieldFilter(f"{kind}_id", "==", report_id))
    rows = [item.to_dict() for item in query.stream()]
    return {"matching_status": report["matching_status"],
            "matches": sorted(rows, key=lambda item: item["score"], reverse=True)[:20]}


@app.post("/v1/reports/{kind}/{report_id}/retry")
def retry(kind: str, report_id: str, user=Depends(identity), client=Depends(db)):
    report_access(client, kind, report_id, user)
    ref = client.collection("matching_jobs").document(report_id)

    @firestore.transactional
    def reset(transaction):
        job = ref.get(transaction=transaction).to_dict()
        if job and job["status"] in ("pending", "running"):
            return
        transaction.set(ref, {"report_id": report_id, "report_type": kind,
                              "status": "pending", "attempts": 0, "lease_until": 0})
        transaction.update(client.collection(collection(kind)).document(report_id), {"matching_status": "pending"})
    reset(client.transaction())
    return {"status": "pending"}


@app.post("/v1/matches/{match_id}/claim", status_code=201)
def claim(match_id: str, user=Depends(identity), client=Depends(db)):
    ref = client.collection("claims").document(match_id)

    @firestore.transactional
    def save(transaction):
        match = client.collection("matches").document(match_id).get(transaction=transaction)
        if not match.exists or match.to_dict()["owner_uid"] != user["uid"]:
            raise HTTPException(403, "Only the lost-report owner may claim this suggestion")
        data = match.to_dict()
        found = client.collection("found_reports").document(data["found_id"]).get(transaction=transaction)
        lost = client.collection("lost_reports").document(data["lost_id"]).get(transaction=transaction)
        existing = ref.get(transaction=transaction)
        if existing.exists:
            return existing.to_dict()
        if found.to_dict()["status"] != "active" or lost.to_dict()["status"] != "active":
            raise HTTPException(409, "This item is no longer available")
        row = {"id": match_id, "owner_uid": user["uid"], "lost_id": data["lost_id"],
               "found_id": data["found_id"], "status": "pending"}
        transaction.set(ref, row)
        return row
    return save(client.transaction())


@app.get("/v1/claims")
def claims(user=Depends(identity), client=Depends(db)):
    query = client.collection("claims")
    if not staff(user):
        query = query.where(filter=firestore.FieldFilter("owner_uid", "==", user["uid"]))
    return {"claims": [item.to_dict() for item in query.limit(100).stream()]}


@app.post("/v1/claims/{claim_id}/decision")
def decision(claim_id: str, body: Decision, user=Depends(identity), client=Depends(db)):
    if not staff(user):
        raise HTTPException(403, "Staff review required")
    ref = client.collection("claims").document(claim_id)

    @firestore.transactional
    def review(transaction):
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise HTTPException(404, "Claim not found")
        row = snap.to_dict()
        found_ref = client.collection("found_reports").document(row["found_id"])
        lost_ref = client.collection("lost_reports").document(row["lost_id"])
        found = found_ref.get(transaction=transaction).to_dict()
        lost = lost_ref.get(transaction=transaction).to_dict()
        allowed = {"pending": {"approved", "rejected"}, "approved": {"collected", "rejected"}}
        if body.status not in allowed.get(row["status"], set()):
            raise HTTPException(409, "Invalid claim transition")
        if body.status in ("approved", "collected"):
            if any(item.get("reserved_claim") not in (None, claim_id) or item["status"] != "active" for item in (found, lost)):
                raise HTTPException(409, "Another claim already reserves or closed these reports")
            update = {"reserved_claim": claim_id}
            if body.status == "collected":
                update["status"] = "closed"
            transaction.update(found_ref, update)
            transaction.update(lost_ref, update)
        elif row["status"] == "approved":
            transaction.update(found_ref, {"reserved_claim": firestore.DELETE_FIELD})
            transaction.update(lost_ref, {"reserved_claim": firestore.DELETE_FIELD})
        transaction.update(ref, {"status": body.status, "reviewer_uid": user["uid"]})
        transaction.set(client.collection("audit_logs").document(), {
            "claim_id": claim_id, "action": body.status, "actor_uid": user["uid"], "at": firestore.SERVER_TIMESTAMP})
        transaction.set(client.collection("notifications").document(), {
            "owner_uid": row["owner_uid"], "message": "Your claim status has changed.", "claim_id": claim_id,
            "created_at": firestore.SERVER_TIMESTAMP, "push_status": "pending"})
    review(client.transaction())
    return {"status": body.status}


@app.get("/v1/notifications")
def notifications(user=Depends(identity), client=Depends(db)):
    query = client.collection("notifications").where(filter=firestore.FieldFilter("owner_uid", "==", user["uid"]))
    return {"notifications": [item.to_dict() for item in query.limit(100).stream()]}


@app.post("/v1/devices")
def register_device(body: DeviceInput, user=Depends(identity), client=Depends(db)):
    key = hashlib.sha256(body.token.encode()).hexdigest()
    client.collection("device_tokens").document(key).set({"owner_uid": user["uid"], "token": body.token})
    return {"status": "registered"}
