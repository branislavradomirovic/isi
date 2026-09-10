#!/usr/bin/env bash
set -Eeuo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
mkdir -p test-results/native-postgres

owned_postgres=0
postgres_name=""
cleanup() {
  if [[ "$owned_postgres" == "1" && -n "$postgres_name" ]]; then
    docker rm -f "$postgres_name" >/dev/null 2>&1 || :
  fi
}
trap cleanup EXIT

if [[ -z "${DATABASE_URL:-}" ]]; then
  command -v docker >/dev/null || { echo "NATIVE POSTGRES FAIL: Docker is required when DATABASE_URL is unset" >&2; exit 1; }
  owned_postgres=1
  postgres_name="isi17-native-postgres-$RANDOM-$$"
  docker run -d --name "$postgres_name" -p 127.0.0.1::5432 \
    -e POSTGRES_DB=isi_ci -e POSTGRES_USER=ci_user -e POSTGRES_PASSWORD=ci_password \
    postgres:17-alpine >/dev/null
  port="$(docker port "$postgres_name" 5432/tcp | awk -F: '{print $NF}')"
  for _ in {1..30}; do
    if docker exec "$postgres_name" pg_isready -U ci_user -d isi_ci >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  docker exec "$postgres_name" pg_isready -U ci_user -d isi_ci >/dev/null
  export DATABASE_URL="postgresql+psycopg://ci_user:ci_password@127.0.0.1:$port/isi_ci"
fi

: "${DATABASE_URL:?DATABASE_URL is required}"
export ISI_NATIVE_POSTGRES_TEST=1
export ISI_RUN_NATIVE_DB_TESTS=1
export ISI_NATIVE_FIXTURE_REPORT_ROOT="$root/test-results/native-postgres/legacy"
export ISI_NATIVE_MEDIA_ROOT="$root/test-results/native-postgres/media"
mkdir -p "$ISI_NATIVE_FIXTURE_REPORT_ROOT" "$ISI_NATIVE_MEDIA_ROOT"

# A fresh native database must prove the full migration chain independently.
tools/ci/migration_check.sh live

# Reconstruct deterministic historical/public fixtures from committed source snapshots.
# Media is served by an in-process MockTransport; this gate performs zero production/server I/O.
python tools/import_legacy_isi_content.py \
  --report "$ISI_NATIVE_FIXTURE_REPORT_ROOT/import_report.json"
python -m tools.ci.prepare_native_postgres_media
python tools/seed_public_platform_pages.py
python tools/seed_domain_knowledge_content.py

mapfile -t native_tests < <(find tests -maxdepth 1 -type f -name '*native_postgres*.py' -print | sort)
if [[ "${#native_tests[@]}" -eq 0 ]]; then
  echo "NATIVE POSTGRES FAIL: no native PostgreSQL test files found" >&2
  exit 1
fi

python -m pytest -q "${native_tests[@]}" \
  --junitxml=test-results/native-postgres/pytest-native-postgres.xml

echo "NATIVE POSTGRES PASS: ${#native_tests[@]} native PostgreSQL test file(s), offline fixtures only"
