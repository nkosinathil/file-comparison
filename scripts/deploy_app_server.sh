#!/usr/bin/env bash
set -euo pipefail

# APP SERVER DEPLOYMENT (FastAPI + Celery)
#
# Required env:
#   AUREX_DB_HOST
#   AUREX_DB_PASS
#   AUREX_REDIS_HOST
#   AUREX_PYTHON_API_KEY
#
# Optional env:
#   AUREX_REPO_URL (default: official repo URL)
#   AUREX_REF (default: main)
#   AUREX_APP_DIR (default: /var/www/aurex)
#   AUREX_APP_USER (default: aurex)
#   AUREX_DB_NAME (default: aurex)
#   AUREX_DB_USER (default: aurex)
#   AUREX_DB_PORT (default: 5432)
#   AUREX_REDIS_PORT (default: 6379)
#   AUREX_RUNTIME_DIR (default: /var/aurex)
#   AUREX_VENV_DIR (default: venv)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

AUREX_REPO_URL="${AUREX_REPO_URL:-https://github.com/nkosinathil/file-comparison.git}"
AUREX_REF="${AUREX_REF:-main}"
AUREX_APP_DIR="${AUREX_APP_DIR:-/var/www/aurex}"
AUREX_APP_USER="${AUREX_APP_USER:-aurex}"
AUREX_DB_HOST="${AUREX_DB_HOST:-}"
AUREX_DB_NAME="${AUREX_DB_NAME:-aurex}"
AUREX_DB_USER="${AUREX_DB_USER:-aurex}"
AUREX_DB_PASS="${AUREX_DB_PASS:-}"
AUREX_DB_PORT="${AUREX_DB_PORT:-5432}"
AUREX_REDIS_HOST="${AUREX_REDIS_HOST:-}"
AUREX_REDIS_PORT="${AUREX_REDIS_PORT:-6379}"
AUREX_PYTHON_API_KEY="${AUREX_PYTHON_API_KEY:-}"
AUREX_RUNTIME_DIR="${AUREX_RUNTIME_DIR:-/var/aurex}"
AUREX_VENV_DIR="${AUREX_VENV_DIR:-venv}"

for required in AUREX_DB_HOST AUREX_DB_PASS AUREX_REDIS_HOST AUREX_PYTHON_API_KEY; do
  if [[ -z "${!required}" ]]; then
    echo "${required} is required."
    exit 1
  fi
done

BACKEND_DIR="${AUREX_APP_DIR}/python-backend"
VENV_PATH="${BACKEND_DIR}/${AUREX_VENV_DIR}"
ENV_FILE="${AUREX_APP_DIR}/.env"

echo "[app] Installing system packages"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-pip python3-venv build-essential libpq-dev \
  tesseract-ocr poppler-utils redis-tools git curl ca-certificates

if ! id -u "${AUREX_APP_USER}" >/dev/null 2>&1; then
  useradd -r -s /usr/sbin/nologin "${AUREX_APP_USER}"
fi

echo "[app] Syncing repository"
mkdir -p "$(dirname "${AUREX_APP_DIR}")"
if [[ ! -d "${AUREX_APP_DIR}/.git" ]]; then
  git clone "${AUREX_REPO_URL}" "${AUREX_APP_DIR}"
fi
git -C "${AUREX_APP_DIR}" fetch origin "${AUREX_REF}" || git -C "${AUREX_APP_DIR}" fetch origin
if ! git -C "${AUREX_APP_DIR}" checkout "${AUREX_REF}" 2>/dev/null; then
  git -C "${AUREX_APP_DIR}" checkout -B "${AUREX_REF}" "origin/${AUREX_REF}"
fi
git -C "${AUREX_APP_DIR}" pull origin "${AUREX_REF}" || true

echo "[app] Writing backend env file"
cat > "${ENV_FILE}" <<EOF
APP_NAME=Aurex
APP_URL=http://localhost
DEBUG=false
DB_HOST=${AUREX_DB_HOST}
DB_PORT=${AUREX_DB_PORT}
DB_NAME=${AUREX_DB_NAME}
DB_USER=${AUREX_DB_USER}
DB_PASS=${AUREX_DB_PASS}
DATABASE_URL=postgresql+psycopg2://${AUREX_DB_USER}:${AUREX_DB_PASS}@${AUREX_DB_HOST}:${AUREX_DB_PORT}/${AUREX_DB_NAME}
REDIS_URL=redis://${AUREX_REDIS_HOST}:${AUREX_REDIS_PORT}/0
PYTHON_API_KEY=${AUREX_PYTHON_API_KEY}
UPLOAD_PATH=${AUREX_RUNTIME_DIR}/uploads
CASE_STORAGE_PATH=${AUREX_RUNTIME_DIR}/cases
EOF
chmod 600 "${ENV_FILE}"
cp "${ENV_FILE}" "${BACKEND_DIR}/.env"
chmod 600 "${BACKEND_DIR}/.env"

echo "[app] Preparing runtime directories"
mkdir -p "${AUREX_RUNTIME_DIR}/uploads" "${AUREX_RUNTIME_DIR}/cases"
chown -R "${AUREX_APP_USER}:${AUREX_APP_USER}" "${AUREX_RUNTIME_DIR}"

echo "[app] Building virtualenv and installing Python requirements"
if [[ ! -d "${VENV_PATH}" ]]; then
  python3 -m venv "${VENV_PATH}"
fi
"${VENV_PATH}/bin/pip" install --upgrade pip
"${VENV_PATH}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt"

echo "[app] Installing and starting services"
cp "${AUREX_APP_DIR}/deploy/systemd/aurex-backend.service" /etc/systemd/system/aurex-backend.service
cp "${AUREX_APP_DIR}/deploy/systemd/aurex-worker.service" /etc/systemd/system/aurex-worker.service
chown -R "${AUREX_APP_USER}:${AUREX_APP_USER}" "${AUREX_APP_DIR}"

systemctl daemon-reload
systemctl enable aurex-backend aurex-worker
systemctl restart aurex-backend aurex-worker

echo "[app] Backend health check"
curl -fsS --max-time 10 "http://127.0.0.1:8000/health" >/dev/null

echo "[app] Complete"
