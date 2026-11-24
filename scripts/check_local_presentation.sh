#!/usr/bin/env bash
set -euo pipefail
python -m uvicorn service.api:app --host 127.0.0.1 --port 8000 > /tmp/strathmore-api.log 2>&1 &
api=$!
worker=""
cleanup() {
  kill "$api" 2>/dev/null || true
  if [ -n "$worker" ]; then kill "$worker" 2>/dev/null || true; fi
  cat /tmp/strathmore-api.log || true
  cat /tmp/strathmore-worker.log 2>/dev/null || true
}
trap cleanup EXIT
for i in $(seq 1 60); do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null; then break; fi
  sleep 1
done
curl --fail http://127.0.0.1:8000/health
python -m scripts.seed_emulator
python -m service.worker > /tmp/strathmore-worker.log 2>&1 &
worker=$!
python -m scripts.prepare_local_demo
