#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🐳  Starting database..."
docker compose -f "$ROOT/docker-compose.yml" up -d

echo "⏳  Waiting for Postgres to be healthy..."
until docker compose -f "$ROOT/docker-compose.yml" exec -T db pg_isready -U postgres &>/dev/null; do
  sleep 1
done

echo "🐍  Starting backend..."
cd "$ROOT/backend"
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "⚛️   Starting frontend..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅  ResearchForge is running"
echo "   App  →  http://localhost:3000"
echo "   API  →  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop everything."

# Shut down both processes cleanly on Ctrl+C
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose -f '$ROOT/docker-compose.yml' stop; exit 0" INT TERM

wait $BACKEND_PID $FRONTEND_PID
