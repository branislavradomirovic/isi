#!/usr/bin/env bash
set -euo pipefail
REPO="${ISI_REPO:-$(pwd)}"
RUNTIME="${ISI15_RUNTIME_DIR:-/tmp/isi15-staging}"
ENV_FILE="${ISI15_ENV_FILE:-$RUNTIME/.env.staging.runtime}"
COMPOSE_FILE="$REPO/docker-compose.staging.yml"
[[ -f "$ENV_FILE" ]] || { echo "ERROR: staging env missing"; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
PROJECT="${COMPOSE_PROJECT_NAME:-isi15stagingqa}"
OUT="$RUNTIME/diagnostics"
mkdir -p "$OUT"
chmod 700 "$OUT"
cd "$REPO"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT" ps > "$OUT/compose-ps.txt" 2>&1 || true
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT" logs --no-color --tail=250 \
  nginx api streamlit data-worker ai-worker postgres redis minio mailpit > "$OUT/compose-logs.txt" 2>&1 || true
{
  echo "head=$(git rev-parse HEAD)"
  echo "captured_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "project=$PROJECT"
} > "$OUT/metadata.txt"
echo "ISI-15 diagnostics captured outside Git: $OUT"
