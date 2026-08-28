#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi11-local-qa"
for name in api streamlit; do
  pidfile="$STATE/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then echo "$name: running PID $pid"; else echo "$name: stale PID $pid"; fi
  else echo "$name: no PID file"; fi
done
