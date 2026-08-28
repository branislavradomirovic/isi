#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi12-local-qa"
echo "=== STOP ISI-12 LOCAL QA ==="
for name in streamlit api; do
  file="$STATE/$name.pid"
  if [[ -f "$file" ]]; then
    pid="$(cat "$file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      echo "$name: stopped PID $pid"
    else
      echo "$name: PID $pid already stopped"
    fi
    rm -f "$file"
  else
    echo "$name: no PID file"
  fi
done
echo "Done. No unrelated process was killed."
