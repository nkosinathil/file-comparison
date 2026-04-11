#!/usr/bin/env bash
set -euo pipefail

# FRONTEND SERVER DEPLOYMENT (Apache + PHP app)
#
# Required env:
#   AUREX_APP_HOST
#   AUREX_PYTHON_API_KEY
#
# Optional env:
#   AUREX_REPO_URL (default: official repo URL)
#   AUREX_REF (default: main)
#   AUREX_APP_DIR (default: /var/www/aurex)
#   AUREX_APP_USER (default: aurex)
#   AUREX_DOMAIN (default: localhost)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

AUREX_REPO_URL="${AUREX_REPO_URL:-https://github.com/nkosinathil/file-comparison.git}"
AUREX_REF="${AUREX_REF:-main}"
AUREX_APP_DIR="${AUREX_APP_DIR:-/var/www/aurex}"
AUREX_APP_USER="${AUREX_APP_USER:-aurex}"
AUREX_APP_HOST="${AUREX_APP_HOST:-}"
AUREX_PYTHON_API_KEY="${AUREX_PYTHON_API_KEY:-}"
AUREX_DOMAIN="${AUREX_DOMAIN:-localhost}"

for required in AUREX_APP_HOST AUREX_PYTHON_API_KEY; do
  if [[ -z "${!required}" ]]; then
    echo "${required} is required."
    exit 1
  fi
done

if ! id -u "${AUREX_APP_USER}" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "${AUREX_APP_USER}"
fi

echo "[frontend] Installing packages"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  apache2 php8.2 php8.2-cli php8.2-curl php8.2-pgsql git curl ca-certificates

echo "[frontend] Syncing repository"
mkdir -p "$(dirname "${AUREX_APP_DIR}")"
if [[ ! -d "${AUREX_APP_DIR}/.git" ]]; then
  git clone "${AUREX_REPO_URL}" "${AUREX_APP_DIR}"
fi
git -C "${AUREX_APP_DIR}" fetch origin "${AUREX_REF}" || git -C "${AUREX_APP_DIR}" fetch origin
if ! git -C "${AUREX_APP_DIR}" checkout "${AUREX_REF}" 2>/dev/null; then
  git -C "${AUREX_APP_DIR}" checkout -B "${AUREX_REF}" "origin/${AUREX_REF}"
fi
git -C "${AUREX_APP_DIR}" pull origin "${AUREX_REF}" || true

ENV_FILE="${AUREX_APP_DIR}/.env"
echo "[frontend] Writing ${ENV_FILE}"
if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${AUREX_APP_DIR}/.env.example" "${ENV_FILE}"
fi

sed -i "s|^PYTHON_API_URL=.*|PYTHON_API_URL=http://${AUREX_APP_HOST}:8000|g" "${ENV_FILE}" || true
grep -q '^PYTHON_API_URL=' "${ENV_FILE}" || echo "PYTHON_API_URL=http://${AUREX_APP_HOST}:8000" >> "${ENV_FILE}"

sed -i "s|^PYTHON_API_KEY=.*|PYTHON_API_KEY=${AUREX_PYTHON_API_KEY}|" "${ENV_FILE}" || true
grep -q '^PYTHON_API_KEY=' "${ENV_FILE}" || echo "PYTHON_API_KEY=${AUREX_PYTHON_API_KEY}" >> "${ENV_FILE}"

echo "[frontend] Configuring Apache vhost"
cp "${AUREX_APP_DIR}/deploy/apache/aurex.conf" /etc/apache2/sites-available/aurex.conf
sed -i "s|ServerName .*|ServerName ${AUREX_DOMAIN}|g" /etc/apache2/sites-available/aurex.conf

a2enmod rewrite headers
a2dissite 000-default || true
a2ensite aurex
apache2ctl configtest

chown -R "${AUREX_APP_USER}:${AUREX_APP_USER}" "${AUREX_APP_DIR}"
systemctl enable apache2
systemctl restart apache2

echo "[frontend] Complete"
echo "[frontend] Check: curl http://127.0.0.1/api/health"
