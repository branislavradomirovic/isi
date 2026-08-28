from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import psycopg

from src.core.config import get_settings
from src.platform.data.storage import S3CompatibleStorage, build_storage


def _dsn(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def db_snapshot() -> dict[str, object]:
    settings = get_settings()
    with psycopg.connect(_dsn(settings.database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            revision = cursor.fetchone()[0]
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
            tables = [row[0] for row in cursor.fetchall()]
            counts: dict[str, int] = {}
            for table in tables:
                cursor.execute(f'SELECT count(*) FROM "{table.replace(chr(34), chr(34) * 2)}"')
                counts[table] = int(cursor.fetchone()[0])
    return {"alembic_revision": revision, "table_counts": counts}


def object_snapshot() -> dict[str, str]:
    storage = build_storage()
    if not isinstance(storage, S3CompatibleStorage):
        raise RuntimeError("snapshot probe requires S3-compatible storage")
    client = storage._client()
    hashes: dict[str, str] = {}
    token: str | None = None
    while True:
        kwargs: dict[str, object] = {"Bucket": storage.bucket}
        if token:
            kwargs["ContinuationToken"] = token
        response = client.list_objects_v2(**kwargs)
        for item in response.get("Contents", []) or []:
            key = str(item["Key"])
            body = client.get_object(Bucket=storage.bucket, Key=key)["Body"].read()
            hashes[key] = hashlib.sha256(body).hexdigest()
        if not response.get("IsTruncated"):
            break
        token = str(response.get("NextContinuationToken") or "")
    return dict(sorted(hashes.items()))


def capture() -> dict[str, object]:
    return {"database": db_snapshot(), "objects": object_snapshot()}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--capture", action="store_true")
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    current = capture()
    if args.capture:
        print(json.dumps(current, indent=2, sort_keys=True))
        return 0
    expected = json.loads(args.verify.read_text())
    if current != expected:
        print("EXPECTED:")
        print(json.dumps(expected, indent=2, sort_keys=True))
        print("CURRENT:")
        print(json.dumps(current, indent=2, sort_keys=True))
        raise SystemExit("restore verification mismatch")
    print("PASS isolated restore database/object fingerprint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
