#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/database-administration/app}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

sudo apt-get update
sudo apt-get install -y nginx python3 python3-venv python3-pip docker.io docker-compose-plugin rsync curl git

sudo useradd --system --home /opt/database-administration --shell /usr/sbin/nologin dbadmin 2>/dev/null || true

sudo mkdir -p /opt/database-administration
sudo mkdir -p "$APP_ROOT"
sudo chown -R "$USER":"$USER" /opt/database-administration

sudo usermod -aG docker "$USER"

sudo cp "$REPO_ROOT/deploy/nginx/database-administration.conf" /etc/nginx/sites-available/database-administration.conf
sudo ln -sf /etc/nginx/sites-available/database-administration.conf /etc/nginx/sites-enabled/database-administration.conf
sudo rm -f /etc/nginx/sites-enabled/default

sudo cp "$REPO_ROOT/deploy/systemd/dbadmin-v1.service" /etc/systemd/system/dbadmin-v1.service

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "Bootstrap completed. Copy the repository to $APP_ROOT and then run deploy/scripts/deploy_v1.sh"
