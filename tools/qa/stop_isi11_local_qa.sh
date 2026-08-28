#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi11-local-qa"
echo "=== STOP ISI-11 LOCAL QA ==="
for name in streamlit api; do
  pidfile="$STATE/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then kill "$pid"; echo "$name: stopped PID $pid"; else echo "$name: PID $pid already stopped"; fi
    rm -f "$pidfile"
  else echo "$name: no PID file"; fi
done
echo "Done. No unrelated process was killed."
