#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO="${ISI_REPO:-/Users/branislavradomirovic/Applications/Python/ISI}"
STATE_DIR="${ISI07_QA_STATE_DIR:-/tmp/isi07-local-qa}"
API_PORT="${ISI07_API_PORT:-8004}"
APP_PORT="${ISI07_APP_PORT:-8504}"
PASSWORD="${ISI_DEMO_PASSWORD:-ISI05-Demo-QA-2026!}"
OLLAMA_BASE_URL="${AI_OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_CHAT_MODEL="${AI_OLLAMA_CHAT_MODEL:-qwen2.5:7b-instruct}"

mkdir -p "$STATE_DIR"

cleanup_on_error() {
  code=$?
  if [[ $code -ne 0 ]]; then
    echo "ERROR: ISI-07 local QA launcher failed; stopping only processes started by this launcher"
    for name in streamlit api; do
      file="$STATE_DIR/$name.pid"
      if [[ -f "$file" ]]; then
        pid="$(cat "$file")"
        kill "$pid" >/dev/null 2>&1 || true
        rm -f "$file"
      fi
    done
  fi
  exit $code
}
trap cleanup_on_error EXIT

[[ -d "$REPO" ]] || { echo "ERROR: repo not found: $REPO"; exit 1; }
[[ -x "$REPO/.venv/bin/python" ]] || { echo "ERROR: repo .venv missing"; exit 1; }
[[ -x "$SCRIPT_DIR/stop_isi07_local_qa.sh" ]] || { echo "ERROR: stop script missing beside launcher"; exit 1; }
[[ -x "$SCRIPT_DIR/status_isi07_local_qa.sh" ]] || { echo "ERROR: status script missing beside launcher"; exit 1; }

cd "$REPO"

echo "=== ISI-07 LOCAL AI QA LAUNCHER ==="
if lsof -iTCP:"$API_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "ERROR: port $API_PORT already in use"
  lsof -iTCP:"$API_PORT" -sTCP:LISTEN
  exit 1
fi
if lsof -iTCP:"$APP_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "ERROR: port $APP_PORT already in use"
  lsof -iTCP:"$APP_PORT" -sTCP:LISTEN
  exit 1
fi

rm -f "$STATE_DIR/api.pid" "$STATE_DIR/streamlit.pid"

echo "=== Local Ollama preflight ==="
curl -fsS "$OLLAMA_BASE_URL/api/tags" > "$STATE_DIR/ollama-tags.json" || {
  echo "ERROR: local Ollama is not reachable at $OLLAMA_BASE_URL"
  exit 1
}
echo "Ollama:      $OLLAMA_BASE_URL"
echo "QA model:    $OLLAMA_CHAT_MODEL"

echo "=== Provision ISI QA identities ==="
ISI_DEMO_PASSWORD="$PASSWORD" ./.venv/bin/python tools/provision_local_app_shell_demo.py --all --password "$PASSWORD"

echo "=== Bootstrap AI registry (Ollama default + deterministic control stub) ==="
AI_ALLOW_DEV_STUB=1 AI_PROVIDER_DEFAULT=ollama AI_JOB_BACKEND=inline \
AI_OLLAMA_BASE_URL="$OLLAMA_BASE_URL" AI_OLLAMA_CHAT_MODEL="$OLLAMA_CHAT_MODEL" \
  ./.venv/bin/python tools/bootstrap_ai_foundation.py --include-dev-stub

echo "=== Start FastAPI ==="
AI_ALLOW_DEV_STUB=1 AI_PROVIDER_DEFAULT=ollama AI_JOB_BACKEND=inline \
AI_OLLAMA_BASE_URL="$OLLAMA_BASE_URL" AI_OLLAMA_CHAT_MODEL="$OLLAMA_CHAT_MODEL" \
  ./.venv/bin/uvicorn src.api.app:app --port "$API_PORT" >"$STATE_DIR/api.log" 2>&1 &
echo $! > "$STATE_DIR/api.pid"
for _ in $(seq 1 40); do
  if curl -fsS "http://localhost:$API_PORT/api/v1/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done
curl -fsS "http://localhost:$API_PORT/api/v1/health" >/dev/null

echo "=== Deterministic policy + namespace + embedding regression ==="
AI_ALLOW_DEV_STUB=1 AI_PROVIDER_DEFAULT=ollama AI_JOB_BACKEND=inline \
AI_OLLAMA_BASE_URL="$OLLAMA_BASE_URL" AI_OLLAMA_CHAT_MODEL="$OLLAMA_CHAT_MODEL" \
  ./.venv/bin/python tools/smoke_shared_ai_foundation.py --base-url "http://localhost:$API_PORT" --password "$PASSWORD"

echo "=== Real local Ollama gateway smoke ==="
AI_ALLOW_DEV_STUB=1 AI_PROVIDER_DEFAULT=ollama AI_JOB_BACKEND=inline \
AI_OLLAMA_BASE_URL="$OLLAMA_BASE_URL" AI_OLLAMA_CHAT_MODEL="$OLLAMA_CHAT_MODEL" \
  ./.venv/bin/python tools/smoke_local_ollama_chat.py \
    --base-url "http://localhost:$API_PORT" \
    --ollama-base-url "$OLLAMA_BASE_URL" \
    --model "$OLLAMA_CHAT_MODEL" \
    --password "$PASSWORD"

echo "=== Start Streamlit ==="
API_BASE_URL="http://localhost:$API_PORT" AI_ALLOW_DEV_STUB=1 AI_PROVIDER_DEFAULT=ollama AI_JOB_BACKEND=inline \
AI_OLLAMA_BASE_URL="$OLLAMA_BASE_URL" AI_OLLAMA_CHAT_MODEL="$OLLAMA_CHAT_MODEL" \
  ./.venv/bin/streamlit run src/streamlit_app/app.py \
    --server.port "$APP_PORT" \
    --server.headless true \
    --browser.gatherUsageStats false \
    >"$STATE_DIR/streamlit.log" 2>&1 &
echo $! > "$STATE_DIR/streamlit.pid"
for _ in $(seq 1 60); do
  if curl -fsS "http://localhost:$APP_PORT/_stcore/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done
curl -fsS "http://localhost:$APP_PORT/_stcore/health" >/dev/null

echo
echo "=== ISI-07 LOCAL AI QA READY ==="
echo "Open:        http://localhost:$APP_PORT"
echo "SIMPA:       isi05-simpa@example.com"
echo "ORDO:        isi05-ordo@example.com"
echo "Dual:        isi05-dual@example.com"
echo "Password:    $PASSWORD"
echo "Ollama:      $OLLAMA_BASE_URL"
echo "QA model:    $OLLAMA_CHAT_MODEL"
echo "API log:     $STATE_DIR/api.log"
echo "Streamlit:   $STATE_DIR/streamlit.log"
echo "Stop:        $SCRIPT_DIR/stop_isi07_local_qa.sh"
echo "Status:      $SCRIPT_DIR/status_isi07_local_qa.sh"

trap - EXIT
if command -v open >/dev/null 2>&1; then
  open "http://localhost:$APP_PORT" || true
fi
