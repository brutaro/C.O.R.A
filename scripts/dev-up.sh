#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
STATE_DIR="$ROOT_DIR/.local-dev"
BACKEND_PID_FILE="$STATE_DIR/backend.pid"
FRONTEND_PID_FILE="$STATE_DIR/frontend.pid"
BACKEND_LOG="$STATE_DIR/backend.log"
FRONTEND_LOG="$STATE_DIR/frontend.log"
LOCAL_HOST="127.0.0.1"

mkdir -p "$STATE_DIR"

require_file() {
  local path="$1"
  local message="$2"
  if [[ ! -e "$path" ]]; then
    echo "$message" >&2
    exit 1
  fi
}

ensure_port_free() {
  local port="$1"
  local label="$2"
  if lsof -n -P -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "$label ja esta usando a porta $port. Pare o processo antes de subir novamente." >&2
    exit 1
  fi
}

is_pid_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file")"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

wait_for_http() {
  local url="$1"
  local label="$2"
  for _ in $(seq 1 45); do
    if curl -sS --max-time 4 "$url" >/dev/null 2>&1; then
      echo "$label pronto em $url"
      return 0
    fi
    sleep 1
  done

  echo "Falha ao iniciar $label. Veja $BACKEND_LOG e $FRONTEND_LOG." >&2
  exit 1
}

require_file "$BACKEND_DIR/.venv/bin/python" "Backend sem .venv. Crie o ambiente em backend/.venv antes de subir."
require_file "$BACKEND_DIR/.env" "Arquivo backend/.env ausente."
require_file "$FRONTEND_DIR/.env" "Arquivo frontend/.env ausente."
require_file "$FRONTEND_DIR/node_modules" "Frontend sem node_modules. Rode npm install em frontend/."
require_file "$BACKEND_DIR/reportlab/node_modules" "Dependencias do PDF ausentes. Rode npm install em backend/reportlab/."

if ! is_pid_running "$BACKEND_PID_FILE"; then
  ensure_port_free 8001 "Backend"
  (
    cd "$BACKEND_DIR"
    nohup ./.venv/bin/python -m uvicorn main:app --host "$LOCAL_HOST" --port 8001 >"$BACKEND_LOG" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
  )
else
  echo "Backend ja estava em execucao."
fi

wait_for_http "http://$LOCAL_HOST:8001/api/health" "Backend"

if ! is_pid_running "$FRONTEND_PID_FILE"; then
  ensure_port_free 3000 "Frontend"
  (
    cd "$FRONTEND_DIR"
    BROWSER=none PORT=3000 nohup npm start >"$FRONTEND_LOG" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
  )
else
  echo "Frontend ja estava em execucao."
fi

wait_for_http "http://localhost:3000" "Frontend"

echo
echo "C.O.R.A. local pronto:"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8001"
echo "Health:   http://localhost:8001/api/health"
echo "Logs:     $STATE_DIR"
