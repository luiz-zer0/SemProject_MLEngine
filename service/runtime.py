import os
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, firestore, credentials
from google.auth.credentials import AnonymousCredentials
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


class EmulatorCredentials(credentials.Base):
    def get_credential(self):
        return AnonymousCredentials()


@lru_cache
def firebase_app():
    project = os.environ.get("FIREBASE_PROJECT_ID", "")
    if not project:
        raise RuntimeError("Set FIREBASE_PROJECT_ID before starting the service")
    emulator = os.environ.get("APP_ENV") == "emulator"
    hosts = [os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"), os.environ.get("FIRESTORE_EMULATOR_HOST")]
    if emulator and (not project.startswith("demo-") or not all(hosts)):
        raise RuntimeError("Emulators require a demo- project and both emulator hosts")
    if not emulator and (any(hosts) or project.startswith("demo-")):
        raise RuntimeError("Emulator settings forbidden outside APP_ENV=emulator")
    return firebase_admin.initialize_app(credential=EmulatorCredentials() if emulator else None,
                                         options={"projectId": project})


def db():
    return firestore.client(app=firebase_app())


def identity(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if credentials is None:
        raise HTTPException(401, "Sign in first")
    try:
        token = auth.verify_id_token(credentials.credentials, app=firebase_app(), check_revoked=True)
    except Exception:
        raise HTTPException(401, "Invalid or expired sign-in") from None
    if not token.get("email_verified"):
        raise HTTPException(403, "Verify your email before using reports")
    if not token.get("email", "").lower().endswith("@strathmore.edu"):
        raise HTTPException(403, "A Strathmore account is required")
    return {"uid": token["uid"], "role": token.get("role", "student")}


def staff(user):
    return user["role"] in ("office_staff", "admin")
