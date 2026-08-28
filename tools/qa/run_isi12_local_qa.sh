#!/usr/bin/env bash
set -euo pipefail
REPO="${ISI_REPO:-/Users/branislavradomirovic/Applications/Python/ISI}"
STATE="/tmp/isi12-local-qa"
API_PORT="${ISI12_API_PORT:-8010}"
UI_PORT="${ISI12_UI_PORT:-8510}"
PASSWORD="${ISI_DEMO_PASSWORD:-ISI05-Demo-QA-2026!}"
mkdir -p "$STATE"
cleanup() {
  if [[ -f "$STATE/streamlit.pid" ]]; then kill "$(cat "$STATE/streamlit.pid")" 2>/dev/null || true; rm -f "$STATE/streamlit.pid"; fi
  if [[ -f "$STATE/api.pid" ]]; then kill "$(cat "$STATE/api.pid")" 2>/dev/null || true; rm -f "$STATE/api.pid"; fi
}
trap 'echo "ERROR: ISI-12 local QA launcher failed; stopping only processes started by this launcher"; cleanup' ERR
cd "$REPO"
echo "=== ISI-12 LOCAL QA LAUNCHER ==="
echo "=== Provision QA identities ==="
ISI_DEMO_PASSWORD="$PASSWORD" ./.venv/bin/python tools/provision_local_app_shell_demo.py --all --password "$PASSWORD"
echo "=== Start FastAPI ==="
ISI_ENV=development API_BASE_URL="http://127.0.0.1:$API_PORT" ./.venv/bin/uvicorn src.api.app:app --port "$API_PORT" >"$STATE/api.log" 2>&1 & echo $! > "$STATE/api.pid"
for _ in $(seq 1 40); do curl -fsS "http://127.0.0.1:$API_PORT/api/v1/health" >/dev/null 2>&1 && break; sleep .25; done
curl -fsS "http://127.0.0.1:$API_PORT/api/v1/health" >/dev/null
echo "=== Shared reporting API smoke ==="
ISI_API_BASE_URL="http://127.0.0.1:$API_PORT" ISI_DEMO_PASSWORD="$PASSWORD" ./.venv/bin/python tools/smoke_reporting.py
echo "=== Start Streamlit ==="
API_BASE_URL="http://127.0.0.1:$API_PORT" ./.venv/bin/streamlit run src/streamlit_app/app.py --server.port "$UI_PORT" --server.headless true >"$STATE/streamlit.log" 2>&1 & echo $! > "$STATE/streamlit.pid"
for _ in $(seq 1 60); do curl -fsS "http://127.0.0.1:$UI_PORT/_stcore/health" >/dev/null 2>&1 && break; sleep .25; done
curl -fsS "http://127.0.0.1:$UI_PORT/_stcore/health" >/dev/null
trap - ERR
URL="http://localhost:$UI_PORT"
if command -v open >/dev/null 2>&1; then open "$URL"; fi
cat <<OUT

=== ISI-12 LOCAL QA READY ===
Open:       $URL
SIMPA:      isi05-simpa@example.com
ORDO:       isi05-ordo@example.com
Dual:       isi05-dual@example.com
Password:   $PASSWORD
API log:    $STATE/api.log
Streamlit:  $STATE/streamlit.log
Stop:       tools/qa/stop_isi12_local_qa.sh
OUT
