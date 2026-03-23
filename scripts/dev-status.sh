#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/.local-dev"

print_process_status() {
  local pid_file="$1"
  local label="$2"

  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      echo "$label: rodando (PID $pid)"
      return 0
    fi
  fi

  echo "$label: parado"
}

print_process_status "$STATE_DIR/backend.pid" "Backend"
print_process_status "$STATE_DIR/frontend.pid" "Frontend"

echo
if curl -sS --max-time 4 http://localhost:8001/api/health >/dev/null 2>&1; then
  echo "Health backend: OK"
else
  echo "Health backend: indisponivel"
fi

if curl -sS --max-time 4 http://localhost:3000 >/dev/null 2>&1; then
  echo "Frontend HTTP: OK"
else
  echo "Frontend HTTP: indisponivel"
fi
