#!/usr/bin/env bash
set -euo pipefail

REPO="${ISI_REPO:-$(pwd)}"
RUNTIME="${ISI15_RUNTIME_DIR:-/tmp/isi15-staging}"
ENV_FILE="${ISI15_ENV_FILE:-$RUNTIME/.env.staging.runtime}"
COMPOSE_FILE="$REPO/docker-compose.staging.yml"
PRIMARY_PROJECT="${COMPOSE_PROJECT_NAME:-isi15stagingqa}"
RESTORE_PROJECT="isi15stagingrestore"
BACKUP="$RUNTIME/backup"

cd "$REPO"
[[ -f "$ENV_FILE" ]] || { echo "ERROR: staging runtime env missing: $ENV_FILE"; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
PRIMARY_PROJECT="${COMPOSE_PROJECT_NAME:-$PRIMARY_PROJECT}"
mkdir -p "$BACKUP"
chmod 700 "$BACKUP"

DC=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PRIMARY_PROJECT")
RDC=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$RESTORE_PROJECT")

cleanup_restore() {
  "${RDC[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup_restore EXIT

printf '%s\n' "=== ISI-15 BACKUP / RESTORE REHEARSAL ==="
"${DC[@]}" ps --status running >/dev/null

printf '%s\n' "=== Capture primary fingerprint ==="
"${DC[@]}" exec -T api python tools/staging/snapshot_probe.py --capture > "$BACKUP/fingerprint.json"

printf '%s\n' "=== PostgreSQL custom-format backup ==="
"${DC[@]}" exec -T postgres sh -ec 'export PGPASSWORD="$POSTGRES_PASSWORD"; pg_dump -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP/postgres.dump"
test -s "$BACKUP/postgres.dump"

printf '%s\n' "=== S3 object backup ==="
rm -rf "$BACKUP/objects"
mkdir -p "$BACKUP/objects"
"${DC[@]}" run --rm --no-deps --entrypoint /bin/sh -v "$BACKUP:/backup" minio-init -ec '
  mc alias set source http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  mc mirror --overwrite "source/$DATA_S3_BUCKET" /backup/objects >/dev/null
  echo "object mirror backup complete"
'

printf '%s\n' "=== Start isolated fresh restore target ==="
cleanup_restore
"${RDC[@]}" up -d postgres minio
for _ in $(seq 1 60); do
  if "${RDC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then break; fi
  sleep 1
done
"${RDC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null
"${RDC[@]}" run --rm minio-init >/dev/null

printf '%s\n' "=== Restore PostgreSQL into isolated target ==="
cat "$BACKUP/postgres.dump" | "${RDC[@]}" exec -T postgres sh -ec 'export PGPASSWORD="$POSTGRES_PASSWORD"; pg_restore -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges'

printf '%s\n' "=== Restore S3 objects into isolated target ==="
"${RDC[@]}" run --rm --no-deps --entrypoint /bin/sh -v "$BACKUP:/backup:ro" minio-init -ec '
  mc alias set target http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  mc mirror --overwrite /backup/objects "target/$DATA_S3_BUCKET" >/dev/null
  echo "object mirror restore complete"
'

printf '%s\n' "=== Verify isolated restore fingerprint ==="
"${RDC[@]}" run --rm --no-deps -v "$BACKUP:/backup:ro" api python tools/staging/snapshot_probe.py --verify /backup/fingerprint.json

printf '%s\n' "=== Restore target Alembic ==="
REVISION="$("${RDC[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc 'select version_num from alembic_version;' | tr -d '\r')"
[[ "$REVISION" == "20260828_0013" ]] || { echo "ERROR: restore Alembic mismatch: $REVISION"; exit 1; }
echo "PASS restore Alembic $REVISION"

echo "=== ISI-15 BACKUP / RESTORE PASS ==="
