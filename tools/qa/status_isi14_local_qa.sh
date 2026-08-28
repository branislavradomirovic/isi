#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi14-local-qa"
echo "=== ISI-14 LOCAL QA STATUS ==="
for name in api streamlit; do
  file="$STATE/$name.pid"
  if [[ -f "$file" ]] && kill -0 "$(cat "$file")" 2>/dev/null; then echo "$name: running PID $(cat "$file")"; else echo "$name: not running"; fi
done
[[ -f "$STATE/api.log" ]] && { echo "--- API tail ---"; tail -n 20 "$STATE/api.log"; }
[[ -f "$STATE/streamlit.log" ]] && { echo "--- Streamlit tail ---"; tail -n 20 "$STATE/streamlit.log"; }
