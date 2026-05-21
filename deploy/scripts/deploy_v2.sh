#!/usr/bin/env bash
set -euo pipefail

APP_BASE="${APP_BASE:-/opt/Database-administration}"
APP_REPO="${APP_REPO:-$APP_BASE}"
APP_VERSION_DIR="$APP_REPO/v2.0"
SERVICE_NAME="${SERVICE_NAME:-dbadmin-v2.service}"

if [[ ! -d "$APP_VERSION_DIR" ]]; then
  echo "Directory $APP_VERSION_DIR not found"
  exit 1
fi

cd "$APP_VERSION_DIR"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created $APP_VERSION_DIR/.env from .env.example"
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is not available. Run deploy/scripts/bootstrap_server.sh first."
  exit 1
fi

docker compose up -d --build

sudo cp "$APP_REPO/deploy/nginx/database-administration.conf" /etc/nginx/sites-available/database-administration.conf
sudo ln -sf /etc/nginx/sites-available/database-administration.conf /etc/nginx/sites-enabled/database-administration.conf

sudo cp "$APP_REPO/deploy/systemd/dbadmin-v2.service" /etc/systemd/system/dbadmin-v2.service
sudo nginx -t

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl reload nginx

echo "v2.0 deployment completed"
