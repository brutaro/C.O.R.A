#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

check_path() {
  local label="$1"
  local path="$2"
  if [[ -e "$path" ]]; then
    echo "[OK] $label"
  else
    echo "[FALTA] $label -> $path"
  fi
}

check_env_key() {
  local label="$1"
  local env_file="$2"
  local key="$3"
  if grep -q "^${key}=" "$env_file"; then
    echo "[OK] $label"
  else
    echo "[FALTA] $label -> chave ${key} em ${env_file}"
  fi
}

check_path "backend/.venv" "$BACKEND_DIR/.venv"
check_path "backend/.env" "$BACKEND_DIR/.env"
check_path "frontend/.env" "$FRONTEND_DIR/.env"
check_path "frontend/node_modules" "$FRONTEND_DIR/node_modules"
check_path "backend/reportlab/node_modules" "$BACKEND_DIR/reportlab/node_modules"

check_env_key "GEMINI_API_KEY ou GOOGLE_API_KEY" "$BACKEND_DIR/.env" "GEMINI_API_KEY"
check_env_key "PINECONE_API_KEY" "$BACKEND_DIR/.env" "PINECONE_API_KEY"
check_env_key "REDIS_HOST" "$BACKEND_DIR/.env" "REDIS_HOST"
check_env_key "REACT_APP_FIREBASE_PROJECT_ID" "$FRONTEND_DIR/.env" "REACT_APP_FIREBASE_PROJECT_ID"

service_account_path="$(grep '^FIREBASE_SERVICE_ACCOUNT_PATH=' "$BACKEND_DIR/.env" | cut -d= -f2- || true)"
if [[ -n "$service_account_path" && -f "$service_account_path" ]]; then
  echo "[OK] FIREBASE_SERVICE_ACCOUNT_PATH existe"
else
  echo "[FALTA] FIREBASE_SERVICE_ACCOUNT_PATH invalido ou ausente"
fi
