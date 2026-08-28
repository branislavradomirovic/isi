#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi08-local-qa"
echo "=== STOP ISI-08 LOCAL QA ==="
for name in streamlit api; do
  pidfile="$STATE/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then kill "$pid"; echo "$name: stopped pid $pid"; else echo "$name: pid $pid already stopped"; fi
    rm -f "$pidfile"
  else
    echo "$name: no PID file"
  fi
done
echo "Done. No unrelated process was killed."
