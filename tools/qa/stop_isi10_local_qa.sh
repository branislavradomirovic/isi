#!/usr/bin/env bash
set -euo pipefail
STATE="/tmp/isi10-local-qa"
echo "=== STOP ISI-10 LOCAL QA ==="
for name in streamlit api; do file="$STATE/$name.pid"; if [[ -f "$file" ]]; then pid="$(cat "$file")"; if kill -0 "$pid" 2>/dev/null; then kill "$pid"; echo "$name: stopped pid $pid"; else echo "$name: stale PID $pid"; fi; rm -f "$file"; else echo "$name: no PID file"; fi; done
echo "Done. No unrelated process was killed."
