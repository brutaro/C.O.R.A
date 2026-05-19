#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
CORA_DOCKER_PORT="${CORA_DOCKER_PORT:-8080}"

if docker compose version >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" ps
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f "$COMPOSE_FILE" ps
else
  echo "Docker Compose nao encontrado." >&2
  exit 1
fi

echo
if curl -sS --max-time 4 "http://127.0.0.1:${CORA_DOCKER_PORT}/api/health"; then
  echo
else
  echo "Health Docker indisponivel em http://127.0.0.1:${CORA_DOCKER_PORT}/api/health"
fi
