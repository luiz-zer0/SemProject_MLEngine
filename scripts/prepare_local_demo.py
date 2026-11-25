"""Prepare fictional inventory via the real local API, then verify lost-to-found matching."""
import json
import os
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

API = "http://127.0.0.1:8000"
AUTH = "http://127.0.0.1:9099"
PROJECT = "demo-strathmore-lost-found"


def request(url, payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request(url, data=body, headers=headers), timeout=20) as response:
        return json.load(response)


def token(account):
    return request(AUTH + "/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo-api-key-not-a-secret",
                   {"email": f"demo-{account}@strathmore.edu", "password": "LocalDemo123!", "returnSecureToken": True})["idToken"]


def report(kind, key, name, description, auth_token):
    day = datetime.now(ZoneInfo("Africa/Nairobi")).date().isoformat()
    payload = {"request_id": str(uuid5(NAMESPACE_URL, f"strathmore-local-demo/{day}/{key}")),
               "report_type": kind, "item_name": name, "description": description,
               "category_id": "electronics", "location_id": "sbs_building", "event_date": day}
    return request(API + "/v1/reports", payload, auth_token)["id"]


def wait_matches(report_id, auth_token):
    for _ in range(45):
        result = request(API + f"/v1/reports/lost/{report_id}/matches", token=auth_token)
        if result["matching_status"] == "complete":
            return result["matches"]
        if result["matching_status"] == "failed":
            raise RuntimeError("Matching job failed; inspect worker logs.")
        time.sleep(2)
    raise RuntimeError("Matching job timed out; inspect worker logs.")


def main():
    if (os.environ.get("APP_ENV") != "emulator" or os.environ.get("FIREBASE_PROJECT_ID") != PROJECT
            or os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") != "127.0.0.1:9099"
            or os.environ.get("FIRESTORE_EMULATOR_HOST") != "127.0.0.1:8080"):
        raise RuntimeError("Only the isolated local emulator is supported.")
    if request(API + "/health").get("matching") != "separate durable worker":
        raise RuntimeError("The authenticated report API is not running.")
    office, student = token("office"), token("student")
    assert request(API + "/v1/me", token=office)["role"] == "office_staff"
    assert request(API + "/v1/me", token=student)["role"] == "student"
    items = [("hp", "HP 65W laptop charger", "Black HP 65W laptop charger with round connector"),
             ("dell", "Dell 90W laptop charger", "Black Dell 90W laptop charger with blue connector")]
    found = {key: report("found", key, name, desc, office) for key, name, desc in items}
    for key, name, desc in items:
        lost = report("lost", "smoke-" + key, name, desc, student)
        matches = wait_matches(lost, student)
        if not matches or matches[0]["found_id"] != found[key] or not matches[0].get("explanation"):
            raise RuntimeError(f"Unexpected {key} ranking; check emulator inventory and worker output.")
        print(f"{key}: top candidate {matches[0]['item_name']}; score={matches[0]['score']:.3f}")
        print(matches[0]["explanation"])
    try:
        request(API + "/v1/reports", {"request_id": str(uuid5(NAMESPACE_URL, "invalid-demo")),
                "report_type": "lost", "item_name": "Invalid", "description": "",
                "category_id": "electronics", "location_id": "sbs_building",
                "event_date": datetime.now(ZoneInfo("Africa/Nairobi")).date().isoformat()}, student)
    except HTTPError as error:
        if error.code != 422:
            raise
        print("Invalid description correctly rejected (422).")
    else:
        raise RuntimeError("Invalid input was accepted.")
    print("Actual local API/worker smoke test passed; Android still needs device verification.")


if __name__ == "__main__":
    main()
