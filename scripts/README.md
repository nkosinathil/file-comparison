# Deployment Scripts

These scripts are for a 3-server deployment:

1. **Data server**: PostgreSQL + Redis
2. **App server**: FastAPI backend + Celery worker (systemd)
3. **Frontend server**: Apache + PHP app

## Files

- `deploy_data_server.sh`
- `deploy_app_server.sh`
- `deploy_frontend_server.sh`
- `deploy_all.sh` (local/remote role runner)

## Core environment variables

Shared:
- `AUREX_REPO_URL` (default: `https://github.com/nkosinathil/file-comparison.git`)
- `AUREX_REF` (default: `main`)
- `AUREX_APP_DIR` (default: `/var/www/aurex`)

Data server (`deploy_data_server.sh`):
- Required: `AUREX_DB_PASS`
- Optional: `AUREX_DB_NAME`, `AUREX_DB_USER`, `AUREX_DB_PORT`, `AUREX_BACKEND_CIDR`, `AUREX_REDIS_BIND`

App server (`deploy_app_server.sh`):
- Required: `AUREX_DB_HOST`, `AUREX_DB_PASS`, `AUREX_REDIS_HOST`, `AUREX_PYTHON_API_KEY`
- Optional: `AUREX_DB_NAME`, `AUREX_DB_USER`, `AUREX_DB_PORT`, `AUREX_REDIS_PORT`, `AUREX_APP_USER`, `AUREX_RUNTIME_DIR`, `AUREX_VENV_DIR`

Frontend server (`deploy_frontend_server.sh`):
- Required: `AUREX_APP_HOST`, `AUREX_PYTHON_API_KEY`
- Optional: `AUREX_DOMAIN`, `AUREX_APP_USER`

## Usage

### Run directly on each target server

```bash
sudo -E bash scripts/deploy_data_server.sh
sudo -E bash scripts/deploy_app_server.sh
sudo -E bash scripts/deploy_frontend_server.sh
```

### Run via orchestrator (local/remote)

Local:

```bash
AUREX_DB_PASS='secret' ./scripts/deploy_all.sh local data
```

Remote:

```bash
AUREX_DB_HOST=10.0.0.10 \
AUREX_REDIS_HOST=10.0.0.10 \
AUREX_DB_PASS='secret' \
AUREX_PYTHON_API_KEY='super-key' \
./scripts/deploy_all.sh remote app 10.0.0.11 ubuntu
```

## Notes

- Scripts are designed to be idempotent and safe to re-run.
- They install dependencies, sync code, configure services, and restart/reload services.
- For production TLS, run Certbot on the frontend server after DNS is configured.
