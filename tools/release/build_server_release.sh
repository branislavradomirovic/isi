#!/usr/bin/env bash
set -euo pipefail

REPO="${ISI_REPO:-$(pwd)}"
OUT_DIR="${ISI_RELEASE_OUT_DIR:-$HOME/Downloads}"
cd "$REPO"
[[ -d .git ]] || { echo "ERROR: not an ISI Git repository"; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo "ERROR: release build requires a clean committed worktree"; exit 1; }
HEAD="$(git rev-parse HEAD)"
SHORT="${HEAD:0:12}"
NAME="ISI-server-${SHORT}.tar.gz"
mkdir -p "$OUT_DIR"
git archive --format=tar.gz --prefix="${HEAD}/" -o "$OUT_DIR/$NAME" HEAD
sha256sum "$OUT_DIR/$NAME" > "$OUT_DIR/$NAME.sha256"
printf '{"git_head":"%s","archive":"%s"}\n' "$HEAD" "$NAME" > "$OUT_DIR/$NAME.manifest.json"
echo "$OUT_DIR/$NAME"
