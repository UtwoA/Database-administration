#!/usr/bin/env bash
set -euo pipefail

APP_BASE="${APP_BASE:-/opt/Database-administration}"
APP_REPO="${APP_REPO:-$APP_BASE}"
APP_VERSION_DIR="$APP_REPO/v1.0"
VENV_DIR="$APP_VERSION_DIR/.venv"
SERVICE_NAME="${SERVICE_NAME:-dbadmin-v1.service}"

if [[ ! -d "$APP_VERSION_DIR" ]]; then
  echo "Directory $APP_VERSION_DIR not found"
  exit 1
fi

cd "$APP_VERSION_DIR"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created $APP_VERSION_DIR/.env from .env.example"
fi

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is not available. Run deploy/scripts/bootstrap_server.sh first."
  exit 1
fi

docker compose up -d

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl reload nginx

echo "v1.0 deployment completed"
