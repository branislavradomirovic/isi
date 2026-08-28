#!/usr/bin/env bash
set -euo pipefail
REPO="${ISI_REPO:-$(pwd)}"
RUNTIME="${ISI15_RUNTIME_DIR:-/tmp/isi15-staging}"
ENV_FILE="${ISI15_ENV_FILE:-$RUNTIME/.env.staging.runtime}"
COMPOSE_FILE="$REPO/docker-compose.staging.yml"
[[ -f "$ENV_FILE" ]] || { echo "ISI-15 staging runtime is not prepared; nothing to stop"; exit 0; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
PROJECT="${COMPOSE_PROJECT_NAME:-isi15stagingqa}"
cd "$REPO"
echo "=== STOP ISI-15 STAGING QA ==="
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT" down --remove-orphans
echo "Stopped only project: $PROJECT"
echo "Named QA volumes and /tmp runtime evidence were preserved. No unrelated process/container was touched."
