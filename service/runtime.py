import os
import logging
import json
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, firestore, credentials
from google.auth.credentials import AnonymousCredentials
from google.auth.exceptions import DefaultCredentialsError
from firebase_admin import exceptions as firebase_exceptions
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)
log = logging.getLogger(__name__)


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
    credential = EmulatorCredentials() if emulator else None
    # Hosted services may supply a dedicated service account via the host's secret store.
    # Google Cloud deployments can instead use application default credentials.
    secret = os.environ.get("FIREBASE_ADMIN_CREDENTIALS_JSON", "")
    if emulator and secret:
        raise RuntimeError("Production credentials are forbidden in emulator mode")
    if secret:
        try:
            info = json.loads(secret)
            if not isinstance(info, dict) or info.get("project_id") != project:
                raise ValueError("Wrong service account project")
            credential = credentials.Certificate(info)
        except (ValueError, TypeError, KeyError):
            raise RuntimeError("Invalid Firebase deployment credentials") from None
    return firebase_admin.initialize_app(credential=credential, options={"projectId": project})


def configured_app():
    # Infrastructure errors must not be reported as invalid user credentials.
    try:
        return firebase_app()
    except (RuntimeError, ValueError, DefaultCredentialsError, firebase_exceptions.FirebaseError):
        log.error("Firebase service initialization failed")
        raise HTTPException(503, "Report service Firebase configuration unavailable") from None


def db():
    try:
        return firestore.client(app=configured_app())
    except (ValueError, DefaultCredentialsError, firebase_exceptions.FirebaseError):
        log.exception("Firestore client initialization failed")
        raise HTTPException(503, "Report database unavailable") from None


def identity(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if credentials is None:
        raise HTTPException(401, "Sign in first")
    app = configured_app()
    try:
        token = auth.verify_id_token(credentials.credentials, app=app, check_revoked=True)
    except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, auth.UserNotFoundError, ValueError):
        raise HTTPException(401, "Invalid or expired sign-in") from None
    except (firebase_exceptions.FirebaseError, DefaultCredentialsError):
        log.exception("Firebase token verification service unavailable")
        raise HTTPException(503, "Sign-in verification service unavailable; retry later") from None
    if not token.get("email_verified"):
        raise HTTPException(403, "Verify your email before using reports")
    if not token.get("email", "").lower().endswith("@strathmore.edu"):
        raise HTTPException(403, "A Strathmore account is required")
    return {"uid": token["uid"], "role": token.get("role", "student")}


def staff(user):
    return user["role"] == "office_staff"
