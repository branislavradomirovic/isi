#!/usr/bin/env bash
set -euo pipefail
STATE_DIR="${ISI07_QA_STATE_DIR:-/tmp/isi07-local-qa}"
API_PORT="${ISI07_API_PORT:-8004}"
APP_PORT="${ISI07_APP_PORT:-8504}"
for name in api streamlit; do
  file="$STATE_DIR/$name.pid"
  if [[ -f "$file" ]]; then
    pid="$(cat "$file")"
    if kill -0 "$pid" >/dev/null 2>&1; then echo "$name: RUNNING pid=$pid"; else echo "$name: STOPPED pid=$pid"; fi
  else
    echo "$name: no PID file"
  fi
done
if lsof -iTCP:"$API_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then echo "port $API_PORT: LISTENING"; else echo "port $API_PORT: free"; fi
if lsof -iTCP:"$APP_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then echo "port $APP_PORT: LISTENING"; else echo "port $APP_PORT: free"; fi
