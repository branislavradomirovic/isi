#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi12-local-qa"
echo "=== ISI-12 LOCAL QA STATUS ==="
for name in api streamlit; do
  file="$STATE/$name.pid"
  if [[ -f "$file" ]]; then
    pid="$(cat "$file")"
    if kill -0 "$pid" 2>/dev/null; then echo "$name: running PID $pid"; else echo "$name: stale PID $pid"; fi
  else
    echo "$name: not started by ISI-12 launcher"
  fi
done
