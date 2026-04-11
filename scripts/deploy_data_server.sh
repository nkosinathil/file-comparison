#!/usr/bin/env bash
set -euo pipefail

# DATA SERVER DEPLOYMENT (PostgreSQL + Redis)
#
# Required env:
#   AUREX_DB_PASS
#
# Optional env:
#   AUREX_REPO_URL (default: official repo URL)
#   AUREX_REF (default: main)
#   AUREX_APP_DIR (default: /var/www/aurex)
#   AUREX_DB_NAME (default: aurex)
#   AUREX_DB_USER (default: aurex)
#   AUREX_DB_PORT (default: 5432)
#   AUREX_BACKEND_CIDR (default: 10.0.0.0/24)
#   AUREX_REDIS_BIND (default: 0.0.0.0)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (sudo)."
  exit 1
fi

AUREX_REPO_URL="${AUREX_REPO_URL:-https://github.com/nkosinathil/file-comparison.git}"
AUREX_REF="${AUREX_REF:-main}"
AUREX_APP_DIR="${AUREX_APP_DIR:-/var/www/aurex}"
AUREX_DB_NAME="${AUREX_DB_NAME:-aurex}"
AUREX_DB_USER="${AUREX_DB_USER:-aurex}"
AUREX_DB_PASS="${AUREX_DB_PASS:-}"
AUREX_DB_PORT="${AUREX_DB_PORT:-5432}"
AUREX_BACKEND_CIDR="${AUREX_BACKEND_CIDR:-10.0.0.0/24}"
AUREX_REDIS_BIND="${AUREX_REDIS_BIND:-0.0.0.0}"

if [[ -z "${AUREX_DB_PASS}" ]]; then
  echo "AUREX_DB_PASS is required."
  exit 1
fi

echo "[data] Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y postgresql postgresql-contrib redis-server git ca-certificates

echo "[data] Syncing repository"
mkdir -p "$(dirname "${AUREX_APP_DIR}")"
if [[ ! -d "${AUREX_APP_DIR}/.git" ]]; then
  git clone "${AUREX_REPO_URL}" "${AUREX_APP_DIR}"
fi
git -C "${AUREX_APP_DIR}" fetch origin "${AUREX_REF}" || git -C "${AUREX_APP_DIR}" fetch origin
if ! git -C "${AUREX_APP_DIR}" checkout "${AUREX_REF}" 2>/dev/null; then
  git -C "${AUREX_APP_DIR}" checkout -B "${AUREX_REF}" "origin/${AUREX_REF}"
fi
git -C "${AUREX_APP_DIR}" pull origin "${AUREX_REF}" || true

echo "[data] Configuring PostgreSQL role and database"
runuser -u postgres -- psql -v ON_ERROR_STOP=1 \
  -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='${AUREX_DB_USER}') THEN CREATE ROLE ${AUREX_DB_USER} LOGIN PASSWORD '${AUREX_DB_PASS}'; ELSE ALTER ROLE ${AUREX_DB_USER} WITH PASSWORD '${AUREX_DB_PASS}'; END IF; END \$\$;"
if [[ "$(runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname='${AUREX_DB_NAME}'")" != "1" ]]; then
  runuser -u postgres -- createdb -O "${AUREX_DB_USER}" "${AUREX_DB_NAME}"
fi

PG_CONF="$(ls /etc/postgresql/*/main/postgresql.conf | sed -n '1p')"
PG_HBA="$(ls /etc/postgresql/*/main/pg_hba.conf | sed -n '1p')"

echo "[data] Updating PostgreSQL network settings"
sed -ri "s/^#?\s*listen_addresses\s*=.*/listen_addresses = '*'/" "${PG_CONF}"
sed -ri "s/^#?\s*port\s*=.*/port = ${AUREX_DB_PORT}/" "${PG_CONF}"
if ! grep -q "host[[:space:]]\+${AUREX_DB_NAME}[[:space:]]\+${AUREX_DB_USER}[[:space:]]\+${AUREX_BACKEND_CIDR}[[:space:]]\+scram-sha-256" "${PG_HBA}"; then
  echo "host    ${AUREX_DB_NAME}    ${AUREX_DB_USER}    ${AUREX_BACKEND_CIDR}    scram-sha-256" >> "${PG_HBA}"
fi

systemctl enable postgresql
systemctl restart postgresql

echo "[data] Running DB migrations"
export PGPASSWORD="${AUREX_DB_PASS}"
psql -h 127.0.0.1 -U "${AUREX_DB_USER}" -d "${AUREX_DB_NAME}" -f "${AUREX_APP_DIR}/database/migrations/001_initial_schema.sql"
psql -h 127.0.0.1 -U "${AUREX_DB_USER}" -d "${AUREX_DB_NAME}" -f "${AUREX_APP_DIR}/database/migrations/002_audit_logs.sql"
unset PGPASSWORD

echo "[data] Configuring Redis"
sed -ri "s/^#?\s*bind\s+.*/bind ${AUREX_REDIS_BIND}/" /etc/redis/redis.conf
sed -ri "s/^#?\s*protected-mode\s+.*/protected-mode yes/" /etc/redis/redis.conf
systemctl enable redis-server
systemctl restart redis-server

echo "[data] Complete"
echo "[data] PostgreSQL ${AUREX_DB_NAME}@${AUREX_DB_PORT} user=${AUREX_DB_USER}"
echo "[data] Redis bind=${AUREX_REDIS_BIND}"
