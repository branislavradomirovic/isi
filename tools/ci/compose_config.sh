#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat >"$tmp/runtime.env" <<'EOF'
APP_ENV=staging
DATABASE_URL=postgresql+psycopg://ci_user:ci_password@postgres:5432/isi_ci
REDIS_URL=redis://redis:6379/0
SESSION_SECRET=ci-synthetic-session-secret-with-at-least-32-characters
SECURITY_PEPPER=ci-synthetic-security-pepper-with-at-least-32-characters
DATA_S3_ENDPOINT_URL=http://minio:9000
DATA_S3_ACCESS_KEY_ID=ci_access_key
DATA_S3_SECRET_ACCESS_KEY=ci_synthetic_secret_key
DATA_S3_BUCKET=isi-ci
EOF
export POSTGRES_DB=isi_ci POSTGRES_USER=ci_user POSTGRES_PASSWORD=ci_password
export DATA_S3_ACCESS_KEY_ID=ci_access_key DATA_S3_SECRET_ACCESS_KEY=ci_synthetic_secret_key DATA_S3_BUCKET=isi-ci
export ISI15_ENV_FILE="$tmp/runtime.env" ISI_SERVER_ENV_FILE="$tmp/runtime.env"
export ISI15_HOST_DATA_DIR="$tmp/data" ISI_SERVER_HOST_DATA_DIR="$tmp/data"
cd "$root"
docker compose config --quiet
docker compose -f docker-compose.staging.yml config --quiet
docker compose -f docker-compose.server.yml config --quiet
echo "COMPOSE PASS: all supported manifests render with synthetic values"
