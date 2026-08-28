#!/usr/bin/env bash
set -euo pipefail
REPO="${ISI_REPO:-$(pwd)}"
RUNTIME="${ISI15_RUNTIME_DIR:-/tmp/isi15-staging}"
ENV_FILE="${ISI15_ENV_FILE:-$RUNTIME/.env.staging.runtime}"
COMPOSE_FILE="$REPO/docker-compose.staging.yml"
[[ -f "$ENV_FILE" ]] || { echo "ISI-15 staging runtime is not prepared"; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
PROJECT="${COMPOSE_PROJECT_NAME:-isi15stagingqa}"
cd "$REPO"
echo "=== ISI-15 STAGING QA STATUS ==="
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT" ps
echo
echo "HTTPS: https://localhost:${ISI15_HTTPS_PORT}/app/"
echo "Mailpit: http://localhost:${ISI15_MAILPIT_UI_PORT}"
