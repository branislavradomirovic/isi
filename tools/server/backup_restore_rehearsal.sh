#!/usr/bin/env bash
set -euo pipefail

RELEASE_DIR="${ISI_RELEASE_DIR:-$(pwd)}"
ROOT="${ISI_SERVER_ROOT:-/home/ubuntu/ISI}"
ENV_FILE="${ISI_SERVER_ENV_FILE:-$ROOT/runtime/.env.server}"
COMPOSE_FILE="$RELEASE_DIR/docker-compose.server.yml"
BACKUP_DIR="$ROOT/backups/isi15-rehearsal-$(date -u +%Y%m%dT%H%M%SZ)"
RESTORE_ID="isi15restore$$"
RESTORE_ENV="$ROOT/runtime/.env.restore.$$"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
DC=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p isi)

cleanup() {
  if [[ -f "$RESTORE_ENV" ]]; then
    docker compose --env-file "$RESTORE_ENV" -f "$COMPOSE_FILE" -p "$RESTORE_ID" down -v --remove-orphans >/dev/null 2>&1 || true
    rm -f "$RESTORE_ENV"
  fi
}
trap cleanup EXIT

echo "=== Capture PostgreSQL backup ==="
"${DC[@]}" exec -T postgres sh -ec 'export PGPASSWORD="$POSTGRES_PASSWORD"; pg_dump -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP_DIR/postgres.dump"
test -s "$BACKUP_DIR/postgres.dump"

echo "=== Capture object-storage mirror ==="
mkdir -p "$BACKUP_DIR/objects"
"${DC[@]}" run --rm --no-deps --entrypoint /bin/sh -v "$BACKUP_DIR:/backup" minio-init -ec '
  mc alias set source http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  mc mirror --overwrite "source/$DATA_S3_BUCKET" /backup/objects >/dev/null
'

python3 - "$ENV_FILE" "$RESTORE_ENV" "$RESTORE_ID" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text().splitlines()
out = []
replacements = {
    "COMPOSE_PROJECT_NAME": sys.argv[3],
    "ISI_POSTGRES_VOLUME": sys.argv[3] + "_pg",
    "ISI_REDIS_VOLUME": sys.argv[3] + "_redis",
    "ISI_MINIO_VOLUME": sys.argv[3] + "_minio",
    "ISI_MAILPIT_VOLUME": sys.argv[3] + "_mailpit",
    "ISI_INTERNAL_NETWORK": sys.argv[3] + "_internal",
}
seen=set()
for line in src:
    key = line.split("=",1)[0] if "=" in line else ""
    if key in replacements:
        out.append(f"{key}={replacements[key]}")
        seen.add(key)
    else:
        out.append(line)
for key,value in replacements.items():
    if key not in seen:
        out.append(f"{key}={value}")
Path(sys.argv[2]).write_text("\n".join(out)+"\n")
Path(sys.argv[2]).chmod(0o600)
PY

RDC=(env
  -u COMPOSE_PROJECT_NAME
  -u ISI_POSTGRES_VOLUME
  -u ISI_REDIS_VOLUME
  -u ISI_MINIO_VOLUME
  -u ISI_MAILPIT_VOLUME
  -u ISI_INTERNAL_NETWORK
  docker compose --env-file "$RESTORE_ENV" -f "$COMPOSE_FILE" -p "$RESTORE_ID"
)
echo "=== Start isolated restore target ==="
"${RDC[@]}" up -d postgres minio
for _ in $(seq 1 60); do
  if "${RDC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then break; fi
  sleep 1
done
"${RDC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null
"${RDC[@]}" run --rm minio-init >/dev/null

echo "=== Restore PostgreSQL ==="
cat "$BACKUP_DIR/postgres.dump" | "${RDC[@]}" exec -T postgres sh -ec 'export PGPASSWORD="$POSTGRES_PASSWORD"; pg_restore -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges'
REVISION="$("${RDC[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc 'select version_num from alembic_version;' | tr -d '\r')"
[[ "$REVISION" == "20260828_0013" ]] || { echo "ERROR restore Alembic mismatch: $REVISION"; exit 1; }

echo "=== Restore object-storage mirror ==="
"${RDC[@]}" run --rm --no-deps --entrypoint /bin/sh -v "$BACKUP_DIR:/backup" minio-init -ec '
  mc alias set target http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  mc mirror --overwrite /backup/objects "target/$DATA_S3_BUCKET" >/dev/null
  rm -rf /backup/restored-objects
  mkdir -p /backup/restored-objects
  mc mirror --overwrite "target/$DATA_S3_BUCKET" /backup/restored-objects >/dev/null
'

ORIGINAL_HASHES="$(mktemp)"
RESTORED_HASHES="$(mktemp)"
trap 'rm -f "$ORIGINAL_HASHES" "$RESTORED_HASHES"; cleanup' EXIT
( cd "$BACKUP_DIR/objects" && find . -type f -print0 | sort -z | xargs -0 -r sha256sum ) > "$ORIGINAL_HASHES"
( cd "$BACKUP_DIR/restored-objects" && find . -type f -print0 | sort -z | xargs -0 -r sha256sum ) > "$RESTORED_HASHES"
diff -u "$ORIGINAL_HASHES" "$RESTORED_HASHES"
rm -f "$ORIGINAL_HASHES" "$RESTORED_HASHES"
trap cleanup EXIT

( cd "$BACKUP_DIR" && sha256sum postgres.dump > SHA256SUMS.txt && find objects -type f -print0 | sort -z | xargs -0 -r sha256sum >> SHA256SUMS.txt )
chmod 600 "$BACKUP_DIR/postgres.dump" "$BACKUP_DIR/SHA256SUMS.txt"
echo "=== ISI SERVER BACKUP/RESTORE REHEARSAL PASS ==="
