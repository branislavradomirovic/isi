#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi10-local-qa"
for name in api streamlit; do file="$STATE/$name.pid"; if [[ ! -f "$file" ]]; then echo "$name: no PID file"; continue; fi; pid="$(cat "$file")"; if kill -0 "$pid" 2>/dev/null; then echo "$name: running pid $pid"; else echo "$name: stale pid $pid"; fi; done
