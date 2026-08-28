#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi13-local-qa"
for name in api streamlit; do
  file="$STATE/$name.pid"
  if [[ -f "$file" ]] && kill -0 "$(cat "$file")" 2>/dev/null; then echo "$name: RUNNING pid=$(cat "$file")"; else echo "$name: STOPPED"; fi
done
for log in api streamlit; do
  echo "--- $log.log (tail) ---"
  [[ -f "$STATE/$log.log" ]] && tail -20 "$STATE/$log.log" || true
done
