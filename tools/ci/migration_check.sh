#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then echo "usage: $0 offline|live" >&2; exit 2; fi
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
heads="$(alembic heads | awk '/\(head\)/ {count++} END {print count+0}')"
[[ "$heads" == 1 ]] || { echo "MIGRATION FAIL: expected one head, found $heads" >&2; exit 1; }
case "$1" in
  offline) DATABASE_URL=postgresql+psycopg://ci:ci@localhost/isi_ci alembic upgrade head --sql >/tmp/isi17-alembic.sql
           test -s /tmp/isi17-alembic.sql ;;
  live) : "${DATABASE_URL:?DATABASE_URL is required for live migration}"
        alembic upgrade head
        test "$(alembic current | awk '/\(head\)/ {count++} END {print count+0}')" = 1 ;;
  *) echo "usage: $0 offline|live" >&2; exit 2 ;;
esac
echo "MIGRATION PASS: $1 single-head check"
