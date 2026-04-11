#!/usr/bin/env bash
set -euo pipefail

# Orchestrator:
# Runs one of the role scripts locally or over SSH.
#
# Usage:
#   ./scripts/deploy_all.sh local <data|app|frontend>
#   ./scripts/deploy_all.sh remote <data|app|frontend> <host> [ssh-user]
#
# All deployment values are read from environment variables expected by
# the role scripts (AUREX_*).
if [[ $# -lt 2 ]]; then
  cat <<'USAGE'
Usage:
  ./scripts/deploy_all.sh local  <data|app|frontend>
  ./scripts/deploy_all.sh remote <data|app|frontend> <host> [ssh-user]

Examples:
  AUREX_DB_PASS='secret' ./scripts/deploy_all.sh local data
  AUREX_DB_HOST=10.0.0.10 AUREX_REDIS_HOST=10.0.0.10 AUREX_PYTHON_API_KEY='key' \
    ./scripts/deploy_all.sh remote app 10.0.0.11 ubuntu
USAGE
  exit 1
fi

MODE="$1"
ROLE="$2"
HOST="${3:-}"
SSH_USER="${4:-ubuntu}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROLE_SCRIPT=""

case "$ROLE" in
  data)
    ROLE_SCRIPT="deploy_data_server.sh"
    ;;
  app)
    ROLE_SCRIPT="deploy_app_server.sh"
    ;;
  frontend)
    ROLE_SCRIPT="deploy_frontend_server.sh"
    ;;
  *)
    echo "Invalid role: ${ROLE}" >&2
    exit 2
    ;;
esac

case "$MODE" in
  local)
    exec "${SCRIPT_DIR}/${ROLE_SCRIPT}"
    ;;
  remote)
    if [[ -z "${HOST}" ]]; then
      echo "Host is required for remote mode." >&2
      exit 1
    fi
    scp "${SCRIPT_DIR}/${ROLE_SCRIPT}" "${SSH_USER}@${HOST}:/tmp/${ROLE_SCRIPT}"
    ssh "${SSH_USER}@${HOST}" "chmod +x /tmp/${ROLE_SCRIPT} && sudo -E /tmp/${ROLE_SCRIPT}"
    ;;
  *)
    echo "Invalid mode: ${MODE}. Use local or remote." >&2
    exit 2
    ;;
esac
