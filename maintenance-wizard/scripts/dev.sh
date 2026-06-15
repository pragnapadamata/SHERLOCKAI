#!/usr/bin/env bash
# Development: run the FastAPI backend (:8000) and the Vite dev server (:5173,
# which proxies /api and /health to the backend) together. Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Starting backend (uvicorn :8000) and frontend (vite :5173)…"
uv run uvicorn backend.app.main:app --reload --port 8000 &
BACK=$!
(cd frontend && npm run dev) &
FRONT=$!

trap 'kill "$BACK" "$FRONT" 2>/dev/null || true' INT TERM EXIT
wait
