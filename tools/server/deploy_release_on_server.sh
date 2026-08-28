#!/usr/bin/env bash
set -euo pipefail

ROOT="${ISI_SERVER_ROOT:-/home/ubuntu/ISI}"
RELEASE_DIR="${ISI_RELEASE_DIR:-$(pwd)}"
ENV_FILE="$ROOT/runtime/.env.server"
CREDENTIALS="$ROOT/runtime/precutover-credentials.json"
COMPOSE_FILE="$RELEASE_DIR/docker-compose.server.yml"

[[ "$(uname -s)" == "Linux" ]] || { echo "ERROR: server deployment requires Linux"; exit 1; }
[[ "$(id -un)" == "ubuntu" ]] || { echo "ERROR: expected target-server user ubuntu"; exit 1; }
command -v docker >/dev/null
command -v openssl >/dev/null

docker info >/dev/null
docker compose version >/dev/null

AVAILABLE_KB="$(df -Pk /home | awk 'NR==2{print $4}')"
[[ "$AVAILABLE_KB" -ge 8388608 ]] || { echo "ERROR: at least 8 GiB free disk is required"; exit 1; }

if ! curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "ERROR: shared host Ollama is not reachable on 127.0.0.1:11434"
  exit 1
fi

mkdir -p "$ROOT/releases" "$ROOT/runtime" "$ROOT/backups" "$ROOT/evidence"
chmod 700 "$ROOT/runtime" "$ROOT/backups" "$ROOT/evidence"

if ! docker network inspect isi_ingress >/dev/null 2>&1; then
  docker network create --label com.isi.owner=isi isi_ingress >/dev/null
fi

python3 "$RELEASE_DIR/tools/server/prepare_server_runtime.py" --root "$ROOT"
[[ -f "$ENV_FILE" && -f "$CREDENTIALS" ]] || { echo "ERROR: server runtime preparation incomplete"; exit 1; }

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)${ISI_PRECUTOVER_HTTPS_PORT}$"; then
  if ! docker ps --format '{{.Names}}' | grep -qx 'isi-edge-1'; then
    echo "ERROR: reserved loopback port ${ISI_PRECUTOVER_HTTPS_PORT} is occupied by a non-ISI process"
    exit 1
  fi
fi

RELEASE_ID="$(basename "$RELEASE_DIR")"
SHORT_ID="${RELEASE_ID:0:12}"
export ISI_APP_IMAGE="isi-app:${SHORT_ID}"
DC=(docker compose --profile precutover --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p isi)

cleanup_error() {
  code=$?
  if [[ $code -ne 0 ]]; then
    echo "ERROR: ISI server deployment failed; existing Krcuga/OralScan/central-ingress were not targeted"
    "${DC[@]}" ps || true
    "${DC[@]}" logs --tail=120 api streamlit data-worker ai-worker edge postgres redis minio mailpit || true
  fi
  exit $code
}
trap cleanup_error EXIT

echo "=== Validate target-server Compose ==="
"${DC[@]}" config -q

echo "=== Build immutable ISI application image ${ISI_APP_IMAGE} ==="
"${DC[@]}" build api

echo "=== Start ISI preproduction stateful services only ==="
"${DC[@]}" up -d postgres redis minio mailpit
for _ in $(seq 1 60); do
  if "${DC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1 && \
     "${DC[@]}" exec -T redis redis-cli -n 1 ping 2>/dev/null | grep -q PONG; then break; fi
  sleep 1
done
"${DC[@]}" run --rm minio-init

echo "=== Run Alembic on isolated preproduction database ==="
"${DC[@]}" run --rm migrate

echo "=== Provision temporary preproduction QA identities ==="
DEMO_PASSWORD="$(python3 - "$CREDENTIALS" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['password'])
PY
)"
"${DC[@]}" run --rm --no-deps \
  -e ISI_ENV=development \
  -e ISI_DEPLOYMENT_PROFILE=development \
  -e AUTH_DELIVERY_MODE=null \
  -e SECURITY_TRUST_PROXY_HEADERS=false \
  -e PUBLIC_BASE_URL=http://localhost \
  -e APP_BASE_URL=http://localhost/app \
  api python tools/staging/find_demo_provisioner.py --repo /app --password "$DEMO_PASSWORD"
unset DEMO_PASSWORD

echo "=== Start ISI API/UI/workers and loopback-only acceptance edge ==="
"${DC[@]}" up -d api streamlit data-worker ai-worker edge

ISI_RELEASE_DIR="$RELEASE_DIR" ISI_SERVER_ROOT="$ROOT" ISI_SERVER_ENV_FILE="$ENV_FILE" \
  "$RELEASE_DIR/tools/server/run_server_acceptance.sh"

ln -sfn "$RELEASE_DIR" "$ROOT/current"
trap - EXIT
echo "=== ISI-15 SERVER RELEASE INSTALLED AND AUTOMATICALLY ACCEPTED ==="
echo "current=$RELEASE_DIR"
echo "public_cutover=false"
