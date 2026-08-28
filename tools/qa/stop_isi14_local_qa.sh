#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi14-local-qa"
echo "=== STOP ISI-14 LOCAL QA ==="
for name in streamlit api; do
  file="$STATE/$name.pid"
  if [[ -f "$file" ]]; then
    pid="$(cat "$file")"
    if kill "$pid" 2>/dev/null; then echo "$name: stopped PID $pid"; else echo "$name: PID $pid not running"; fi
    rm -f "$file"
  else
    echo "$name: no PID file"
  fi
done
echo "Done. No unrelated process was killed."
