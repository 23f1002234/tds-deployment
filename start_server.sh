#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Activate project venv if it exists
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "Killing anything on port 8000 (if present)..."
lsof -ti:8000 | xargs -r kill -9 || true

# remove previous log
rm -f server.log

echo "Starting uvicorn in background, logging to server.log ..."
# start uvicorn in background and capture stdout+stderr
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level info > server.log 2>&1 &

UV_PID=$!
# give it a second to start
sleep 1

echo "Uvicorn PID: $UV_PID"
echo "---- server.log (head) ----"
head -n 80 server.log || true
echo "---- trying health endpoint (curl) ----"
curl -sS -D - http://127.0.0.1:8000/ || echo "curl failed"
echo "---- server.log (tail 120 lines) ----"
tail -n 120 server.log || true
echo "---- done ----"
