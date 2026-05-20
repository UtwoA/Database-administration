#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/Database-administration}"
APP_VERSION_DIR="$APP_ROOT/v1.0"

if [[ ! -d "$APP_VERSION_DIR" ]]; then
  echo "Directory $APP_VERSION_DIR not found"
  exit 1
fi

cd "$APP_VERSION_DIR"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created $APP_VERSION_DIR/.env from .env.example"
fi

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

docker compose up -d

sudo systemctl daemon-reload
sudo systemctl enable dbadmin-v1.service
sudo systemctl restart dbadmin-v1.service
sudo systemctl reload nginx

echo "v1.0 deployment completed"
