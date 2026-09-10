#!/usr/bin/env bash
set -Eeuo pipefail
name="isi17-postgres-$RANDOM-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || :; }
trap cleanup EXIT
docker run -d --name "$name" -p 127.0.0.1::5432 \
  -e POSTGRES_DB=isi_ci -e POSTGRES_USER=ci_user -e POSTGRES_PASSWORD=ci_password postgres:17-alpine >/dev/null
port="$(docker port "$name" 5432/tcp | awk -F: '{print $NF}')"
for _ in {1..30}; do docker exec "$name" pg_isready -U ci_user -d isi_ci >/dev/null 2>&1 && break; sleep 1; done
docker exec "$name" pg_isready -U ci_user -d isi_ci >/dev/null
DATABASE_URL="postgresql+psycopg://ci_user:ci_password@127.0.0.1:$port/isi_ci" tools/ci/migration_check.sh live
