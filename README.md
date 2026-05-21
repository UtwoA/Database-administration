# Database Administration

Repository for a multi-version educational stand for the Database Administration course.

Structure:

- `v1.0` ... `v8.0` - project versions
- `portal/` - version landing page
- `deploy/` - Nginx, systemd and server bootstrap/deploy scripts
- `.github/workflows/` - CI/CD workflows

Recommended server layout:

- `/opt/Database-administration` - synced repository
- `/` - portal
- `/v1/` - `v1.0`
- `/v2/` - `v2.0`

Current deploy workflow (`.github/workflows/deploy.yml`) syncs the repository and runs:
- `deploy/scripts/deploy_v1.sh`
- `deploy/scripts/deploy_v2.sh`

Deploy secrets for GitHub Actions:

- `DEPLOY_HOST`
- `DEPLOY_PORT`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
