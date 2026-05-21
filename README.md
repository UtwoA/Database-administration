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

Deploy secrets for GitHub Actions:

- `DEPLOY_HOST`
- `DEPLOY_PORT`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
