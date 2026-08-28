#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi08-local-qa"
for name in api streamlit; do
  pidfile="$STATE/$name.pid"
  if [[ ! -f "$pidfile" ]]; then echo "$name: no PID file"; continue; fi
  pid="$(cat "$pidfile")"
  if kill -0 "$pid" 2>/dev/null; then echo "$name: running pid $pid"; else echo "$name: stale pid $pid"; fi
done
