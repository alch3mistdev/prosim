#!/usr/bin/env bash
# Start ProSim backend + frontend. Ctrl+C to stop both.
# Frontend talks directly to backend (no proxy) to avoid timeout on long generate requests.
set -e
cd "$(dirname "$0")"

echo "Starting ProSim backend on port 8000..."
prosim serve --port 8000 &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM

sleep 2
echo "Starting frontend on port 3000..."
cd frontend && NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api npm run dev
