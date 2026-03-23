#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/.local-dev"

stop_from_pid_file() {
  local pid_file="$1"
  local label="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$label nao estava registrado."
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid"
    echo "$label parado (PID $pid)."
  else
    echo "$label ja estava parado."
  fi

  rm -f "$pid_file"
}

stop_from_pid_file "$STATE_DIR/backend.pid" "Backend"
stop_from_pid_file "$STATE_DIR/frontend.pid" "Frontend"
