#!/usr/bin/env bash
set -euo pipefail

ARCHIVE="${1:-}"
[[ -n "$ARCHIVE" && -f "$ARCHIVE" ]] || { echo "Usage: $0 /path/to/ISI-server-<sha>.tar.gz"; exit 2; }
USER="${ISI_SSH_USER:-ubuntu}"
HOST="${ISI_TARGET_HOST:-94.230.189.146}"
PORT="${ISI_SSH_PORT:-222}"
[[ "$USER" == "ubuntu" && "$HOST" == "94.230.189.146" && "$PORT" == "222" ]] || {
  echo "ERROR: target is locked to ubuntu@94.230.189.146:222"; exit 1;
}
BASE="$(basename "$ARCHIVE")"
SHA="$(tar -tzf "$ARCHIVE" | head -1 | cut -d/ -f1)"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "ERROR: archive does not have a Git-SHA release prefix"; exit 1; }
EXPECTED="$(sha256sum "$ARCHIVE" | awk '{print $1}')"

ssh -p "$PORT" "$USER@$HOST" 'mkdir -p /home/ubuntu/ISI/incoming /home/ubuntu/ISI/releases && chmod 700 /home/ubuntu/ISI/incoming'
scp -P "$PORT" "$ARCHIVE" "$USER@$HOST:/home/ubuntu/ISI/incoming/$BASE"
ssh -p "$PORT" "$USER@$HOST" bash -s -- "$BASE" "$SHA" "$EXPECTED" <<'REMOTE'
set -euo pipefail
BASE="$1"; SHA="$2"; EXPECTED="$3"
ROOT=/home/ubuntu/ISI
ARCHIVE="$ROOT/incoming/$BASE"
ACTUAL="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[[ "$ACTUAL" == "$EXPECTED" ]] || { echo "ERROR: transferred archive SHA mismatch"; exit 1; }
TARGET="$ROOT/releases/$SHA"
[[ ! -e "$TARGET" ]] || { echo "ERROR: release already exists: $TARGET"; exit 1; }
tar -xzf "$ARCHIVE" -C "$ROOT/releases"
[[ -x "$TARGET/tools/server/deploy_release_on_server.sh" ]] || chmod +x "$TARGET/tools/server/"*.sh "$TARGET/tools/release/"*.sh 2>/dev/null || true
ISI_RELEASE_DIR="$TARGET" ISI_SERVER_ROOT="$ROOT" "$TARGET/tools/server/deploy_release_on_server.sh"
REMOTE
