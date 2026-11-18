"""Durable Firestore jobs with expiring leases. Run beside the API."""
import logging
import os
import time
import uuid

from firebase_admin import messaging
from google.cloud import firestore

from .inference import TfidfMatcher
from .runtime import db, firebase_app

log = logging.getLogger(__name__)


def process_job(client, ref, matcher):
    lease = str(uuid.uuid4())

    @firestore.transactional
    def acquire(transaction):
        job = ref.get(transaction=transaction).to_dict()
        if not job or job["status"] not in ("pending", "running") or job.get("lease_until", 0) > time.time():
            return None
        transaction.update(ref, {"status": "running", "lease": lease, "lease_until": time.time() + 120,
                                 "attempts": job.get("attempts", 0) + 1})
        return job
    job = acquire(client.transaction())
    if job is None:
        return False
    source_ref = client.collection(f"{job['report_type']}_reports").document(job["report_id"])
    try:
        source = source_ref.get().to_dict()
        opposite = "found" if job["report_type"] == "lost" else "lost"
        candidates = client.collection(f"{opposite}_reports").limit(201).stream()
        candidates = [item.to_dict() for item in candidates]
        if len(candidates) > 200:
            raise ValueError("Candidate limit exceeded; refine retrieval before processing")
        results = []
        if source["status"] == "active":
            active = [candidate for candidate in candidates
                      if candidate["status"] == "active" and candidate["owner_uid"] != source["owner_uid"]]
            pairs = []
            if opposite == "found":
                found_by_id = {row["id"]: row for row in active}
                for evidence in matcher.recommend(source, active):
                    pairs.append((source, found_by_id[evidence["found_report_id"]], evidence))
            else:
                for lost in active:
                    for evidence in matcher.recommend(lost, [source]):
                        pairs.append((lost, source, evidence))
            for lost, found, evidence in pairs:
                match_id = f"{lost['id']}_{found['id']}"
                results.append({"id": match_id, "lost_id": lost["id"], "found_id": found["id"],
                                "owner_uid": lost["owner_uid"], "score": evidence["text_similarity"],
                                "explanation": evidence["explanation"], "workflow": evidence["workflow"],
                                "item_name": found["item_name"], "model_version": matcher.version,
                                "status": "suggested", "review_required": True})

        @firestore.transactional
        def finish(transaction):
            current = ref.get(transaction=transaction).to_dict()
            if current.get("lease") != lease:
                return
            for result in results:
                transaction.set(client.collection("matches").document(result["id"]), result)
            # One deterministic notification per lost report; no item/identity details in push text.
            for lost_id, owner in {(result["lost_id"], result["owner_uid"]) for result in results}:
                transaction.set(client.collection("notifications").document(f"matches_{lost_id}"), {
                    "owner_uid": owner, "message": "Possible matches are ready for review.",
                    "report_id": lost_id, "created_at": firestore.SERVER_TIMESTAMP, "push_status": "pending"})
            transaction.update(source_ref, {"matching_status": "complete"})
            transaction.update(ref, {"status": "complete", "lease_until": 0})
        finish(client.transaction())
    except Exception:
        log.exception("Matching job failed: %s", ref.id)

        @firestore.transactional
        def fail(transaction):
            current = ref.get(transaction=transaction).to_dict()
            if current.get("lease") != lease:
                return
            status = "failed" if current["attempts"] >= 3 else "pending"
            transaction.update(ref, {"status": status, "lease_until": time.time() + 15})
            transaction.update(source_ref, {"matching_status": status})
        fail(client.transaction())
    return True


def main():
    logging.basicConfig(level=logging.INFO)
    matcher = TfidfMatcher()
    client = db()
    while True:
        for status in ("pending", "running"):
            query = client.collection("matching_jobs").where(filter=firestore.FieldFilter("status", "==", status))
            for snapshot in query.limit(50).stream():
                process_job(client, snapshot.reference, matcher)
        if os.environ.get("APP_ENV") != "emulator":
            deliver_push(client)
        time.sleep(3)


def deliver_push(client):
    # In-app notifications are durable even if FCM is unavailable. Push is at-least-once.
    pending = client.collection("notifications").where(filter=firestore.FieldFilter("push_status", "==", "pending"))
    for note in pending.limit(20).stream():
        row = note.to_dict()
        tokens = client.collection("device_tokens").where(filter=firestore.FieldFilter("owner_uid", "==", row["owner_uid"]))
        try:
            for token in tokens.limit(10).stream():
                try:
                    messaging.send(messaging.Message(token=token.to_dict()["token"], notification=messaging.Notification(
                        title="Lost & Found update", body="Open the app to review your updates.")), app=firebase_app())
                except messaging.UnregisteredError:
                    token.reference.delete()
            note.reference.update({"push_status": "sent"})
        except Exception:
            log.exception("Push unavailable; in-app notification retained")


if __name__ == "__main__":
    main()
