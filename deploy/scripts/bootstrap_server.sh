#!/usr/bin/env bash
set -euo pipefail

APP_BASE="${APP_BASE:-/opt/Database-administration}"
APP_REPO="${APP_REPO:-$APP_BASE}"
APP_USER="${APP_USER:-deploy}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source /etc/os-release

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

sudo install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
  curl -fsSL https://download.docker.com/linux/${ID}/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
fi

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt-get update
sudo apt-get remove -y docker.io docker-doc docker-compose podman-docker containerd runc || true
sudo apt-get install -y nginx python3 python3-venv python3-pip docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin rsync git curl

if ! id "$APP_USER" >/dev/null 2>&1; then
  sudo useradd --create-home --home-dir "$APP_BASE" --shell /bin/bash "$APP_USER"
fi
sudo usermod -aG docker "$APP_USER" || true

sudo install -d -o "$APP_USER" -g "$APP_USER" "$APP_BASE"
sudo install -d -o "$APP_USER" -g "$APP_USER" "$APP_REPO"
sudo install -d -o "$APP_USER" -g "$APP_USER" "$APP_BASE/logs"

sudo cp "$REPO_ROOT/deploy/nginx/database-administration.conf" /etc/nginx/sites-available/database-administration.conf
sudo ln -sf /etc/nginx/sites-available/database-administration.conf /etc/nginx/sites-enabled/database-administration.conf
sudo rm -f /etc/nginx/sites-enabled/default

sudo cp "$REPO_ROOT/deploy/systemd/dbadmin-v1.service" /etc/systemd/system/dbadmin-v1.service
cat <<EOF | sudo tee /etc/sudoers.d/database-administration-deploy >/dev/null
$APP_USER ALL=(root) NOPASSWD: /usr/bin/systemctl daemon-reload, /usr/bin/systemctl enable dbadmin-v1.service, /usr/bin/systemctl restart dbadmin-v1.service, /usr/bin/systemctl reload nginx
EOF
sudo chmod 440 /etc/sudoers.d/database-administration-deploy
sudo systemctl daemon-reload
sudo systemctl enable docker
sudo systemctl restart docker

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "Bootstrap completed."
echo "Next steps:"
echo "  1. Copy the repository to $APP_REPO"
echo "  2. Run deploy/scripts/deploy_v1.sh"
