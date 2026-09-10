#!/usr/bin/env bash
set -Eeuo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

report_root="$root/test-results/isi19-recovery"
rm -rf "$report_root"
mkdir -p "$report_root"

command -v docker >/dev/null || { echo "ISI-19 RECOVERY FAIL: Docker is required" >&2; exit 1; }

source_name="isi19-source-$RANDOM-$$"
target_name="isi19-target-$RANDOM-$$"
cleanup() {
  docker rm -f "$source_name" "$target_name" >/dev/null 2>&1 || :
}
trap cleanup EXIT

for name in "$source_name" "$target_name"; do
  docker run -d --name "$name" -p 127.0.0.1::5432 \
    -e POSTGRES_DB=isi_ci -e POSTGRES_USER=ci_user -e POSTGRES_PASSWORD=ci_password \
    postgres:17-alpine >/dev/null
  for _ in {1..30}; do
    if docker exec "$name" pg_isready -U ci_user -d isi_ci >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  docker exec "$name" pg_isready -U ci_user -d isi_ci >/dev/null
done

source_port="$(docker port "$source_name" 5432/tcp | awk -F: '{print $NF}')"
target_port="$(docker port "$target_name" 5432/tcp | awk -F: '{print $NF}')"
source_url="postgresql+psycopg://ci_user:ci_password@127.0.0.1:${source_port}/isi_ci"
target_url="postgresql+psycopg://ci_user:ci_password@127.0.0.1:${target_port}/isi_ci"

DATABASE_URL="$source_url" tools/ci/migration_check.sh live

docker exec "$source_name" psql -U ci_user -d isi_ci -v ON_ERROR_STOP=1 -c \
  "CREATE TABLE isi19_recovery_fixture (product_code text PRIMARY KEY, payload text NOT NULL); INSERT INTO isi19_recovery_fixture(product_code,payload) VALUES ('SIMPA','synthetic-simpa'),('ORDO','synthetic-ordo');" >/dev/null

python - "$report_root" <<'PY'
from pathlib import Path
import json
import sys

from src.platform.data.storage import LocalFilesystemStorage
from src.platform.recovery.service import backup_storage_objects, restore_storage_objects, verify_manifest_artifacts, write_manifest

root = Path(sys.argv[1])
source = LocalFilesystemStorage(root / "object-source")
target = LocalFilesystemStorage(root / "object-target")
fixtures = {
    "org-ci/SIMPA/workspace-ci/aa/simpa.bin": b"synthetic-simpa-object",
    "org-ci/ORDO/workspace-ci/bb/ordo.bin": b"synthetic-ordo-object",
}
for key, payload in fixtures.items():
    source.put_bytes(key, payload)
manifest = backup_storage_objects(
    source,
    keys=tuple(fixtures),
    backup_root=root / "object-backup",
    backup_id="isi19-synthetic-object-backup",
    created_at="2026-09-10T00:00:00Z",
    source_descriptor="synthetic-ci-object-storage",
)
write_manifest(manifest, root / "object-recovery-manifest.json")
verify_manifest_artifacts(manifest, backup_root=root / "object-backup")
restored = restore_storage_objects(
    manifest,
    backup_root=root / "object-backup",
    target_storage=target,
    target_label="ci",
)
assert set(restored) == set(fixtures)
for key, payload in fixtures.items():
    assert target.get_bytes(key) == payload
(root / "object-summary.json").write_text(
    json.dumps({"status": "success", "restored_keys": sorted(restored)}, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

docker exec "$source_name" pg_dump -U ci_user -d isi_ci --format=custom --no-owner --no-privileges > "$report_root/postgresql.dump"
test -s "$report_root/postgresql.dump"
dump_sha="$(sha256sum "$report_root/postgresql.dump" | awk '{print $1}')"
docker cp "$report_root/postgresql.dump" "$target_name:/tmp/isi19.dump" >/dev/null
docker exec "$target_name" pg_restore -U ci_user -d isi_ci --no-owner --no-privileges --exit-on-error /tmp/isi19.dump >/dev/null

DATABASE_URL="$target_url" tools/ci/migration_check.sh live
actual_rows="$(docker exec "$target_name" psql -U ci_user -d isi_ci -Atc "SELECT product_code || ':' || payload FROM isi19_recovery_fixture ORDER BY product_code")"
expected_rows=$'ORDO:synthetic-ordo\nSIMPA:synthetic-simpa'
[[ "$actual_rows" == "$expected_rows" ]] || { echo "ISI-19 RECOVERY FAIL: relational verification mismatch" >&2; exit 1; }

python - "$report_root/rehearsal-summary.json" "$dump_sha" <<'PY'
import json
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "postgresql17_restore": "success",
            "postgresql_dump_sha256": sys.argv[2],
            "relational_isolation_fixture": ["ORDO", "SIMPA"],
            "object_storage_restore": "success",
            "server_verification": "DEFERRED_SERVER_VERIFICATION",
            "status": "success",
        },
        sort_keys=True,
    ) + "\n",
    encoding="utf-8",
)
PY

echo "ISI-19 RECOVERY PASS: PostgreSQL 17 and scoped object storage restored and verified"
