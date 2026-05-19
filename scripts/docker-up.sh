#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
DOCKER_ENV_FILE="$ROOT_DIR/.env.docker"

if [[ -f "$DOCKER_ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$DOCKER_ENV_FILE"
  set +a
fi

export CORA_DOCKER_PORT="${CORA_DOCKER_PORT:-8080}"
export FIREBASE_SERVICE_ACCOUNT_FILE="${FIREBASE_SERVICE_ACCOUNT_FILE:-$ROOT_DIR/cora-9d120-firebase-adminsdk-fbsvc-9db52ba42d.json}"

if [[ ! -f "$ROOT_DIR/backend/.env" ]]; then
  echo "Arquivo backend/.env ausente." >&2
  exit 1
fi

if [[ ! -f "$FIREBASE_SERVICE_ACCOUNT_FILE" ]]; then
  echo "Service account Firebase nao encontrada em: $FIREBASE_SERVICE_ACCOUNT_FILE" >&2
  echo "Ajuste FIREBASE_SERVICE_ACCOUNT_FILE em .env.docker ou use FIREBASE_SERVICE_ACCOUNT_JSON no backend/.env." >&2
  exit 1
fi

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" "$@"
  else
    echo "Docker Compose nao encontrado." >&2
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  for _ in $(seq 1 60); do
    if curl -sS --max-time 4 "$url" >/dev/null 2>&1; then
      echo "C.O.R.A. pronta em $url"
      return 0
    fi
    sleep 1
  done

  echo "Container iniciou, mas o healthcheck HTTP nao respondeu a tempo." >&2
  compose logs --tail=120 cora >&2
  exit 1
}

compose up --build -d cora
wait_for_http "http://127.0.0.1:${CORA_DOCKER_PORT}/api/health"

echo
echo "C.O.R.A. Docker local:"
echo "App:    http://localhost:${CORA_DOCKER_PORT}"
echo "Health: http://127.0.0.1:${CORA_DOCKER_PORT}/api/health"
echo "Logs:   docker compose -f \"$COMPOSE_FILE\" logs -f cora"
