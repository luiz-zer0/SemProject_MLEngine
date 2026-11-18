"""Run inside `firebase emulators:exec`; creates fictional local test records only."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
if not os.environ.get("FIRESTORE_EMULATOR_HOST") or not os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
    raise SystemExit("Run this script using Firebase emulators:exec")
os.environ.update(APP_ENV="emulator", FIREBASE_PROJECT_ID="demo-strathmore-lost-found",
                  RUN_FIREBASE_INTEGRATION="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "--tb=short"], cwd=root, check=True)
subprocess.run(["node", "rules.test.mjs"], cwd=root / "firebase", check=True)
