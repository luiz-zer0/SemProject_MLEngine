"""Create fictional accounts locally only; never grants roles in a real project."""
import os

from firebase_admin import auth
from service.runtime import firebase_app


def main():
    if os.environ.get("APP_ENV") != "emulator" or not os.environ.get("FIREBASE_PROJECT_ID", "").startswith("demo-"):
        raise RuntimeError("This script is only for the local demo emulator")
    app = firebase_app()
    for uid, role in (("demo-student", "student"), ("demo-office", "office_staff")):
        email = f"{uid}@strathmore.edu"
        try:
            auth.get_user(uid, app=app)
        except auth.UserNotFoundError:
            auth.create_user(uid=uid, email=email, password="LocalDemo123!", email_verified=True, app=app)
        auth.set_custom_user_claims(uid, {"role": role}, app=app)
        print(f"Local-only {role}: {email} / LocalDemo123!")


if __name__ == "__main__":
    main()
