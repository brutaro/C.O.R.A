#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

if docker compose version >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" down
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f "$COMPOSE_FILE" down
else
  echo "Docker Compose nao encontrado." >&2
  exit 1
fi
