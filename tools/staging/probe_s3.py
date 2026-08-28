from __future__ import annotations

import argparse
import hashlib

from src.platform.data.storage import StorageError, build_storage

KEY = "__isi15_probe__/persistent.bin"
PAYLOAD = b"ISI-15 S3-compatible persistence probe v1\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    storage = build_storage()
    digest = hashlib.sha256(PAYLOAD).hexdigest()
    if args.verify_existing:
        got = storage.get_bytes(KEY)
        assert hashlib.sha256(got).hexdigest() == digest
        print(f"PASS S3 persistence readback sha256={digest[:16]}")
        return 0

    created = storage.put_bytes(KEY, PAYLOAD)
    got = storage.get_bytes(KEY)
    assert got == PAYLOAD
    assert storage.exists(KEY)
    duplicate = storage.put_bytes(KEY, PAYLOAD)
    assert duplicate is False
    collision_blocked = False
    try:
        storage.put_bytes(KEY, b"different bytes")
    except StorageError:
        collision_blocked = True
    assert collision_blocked
    print(f"PASS S3 write/read/hash/idempotency/collision created={created} sha256={digest[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
