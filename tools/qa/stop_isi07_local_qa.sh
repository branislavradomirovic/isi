#!/usr/bin/env bash
set -euo pipefail
STATE_DIR="${ISI07_QA_STATE_DIR:-/tmp/isi07-local-qa}"
echo "=== STOP ISI-07 LOCAL AI QA ==="
for name in streamlit api; do
  file="$STATE_DIR/$name.pid"
  if [[ -f "$file" ]]; then
    pid="$(cat "$file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid"
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
