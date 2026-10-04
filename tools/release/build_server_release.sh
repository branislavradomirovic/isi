#!/usr/bin/env bash
set -euo pipefail
# Portable builder owns git status --porcelain and git archive checks.
REPO="${ISI_REPO:-$(pwd)}"
OUT_DIR="${ISI_RELEASE_OUT_DIR:-$HOME/Downloads/ISI-release-$(date -u +%Y%m%dT%H%M%SZ)}"
cd "$REPO"
exec "${ISI_PYTHON:-python3}" -m tools.release.build --output "$OUT_DIR" "$@"
