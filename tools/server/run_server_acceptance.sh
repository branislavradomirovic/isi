#!/usr/bin/env bash
set -euo pipefail

RELEASE_DIR="${ISI_RELEASE_DIR:-$(pwd)}"
ROOT="${ISI_SERVER_ROOT:-/home/ubuntu/ISI}"
ENV_FILE="${ISI_SERVER_ENV_FILE:-$ROOT/runtime/.env.server}"
CREDENTIALS="$ROOT/runtime/precutover-credentials.json"
COMPOSE_FILE="$RELEASE_DIR/docker-compose.server.yml"
EVIDENCE_DIR="$ROOT/evidence"
mkdir -p "$EVIDENCE_DIR"
chmod 700 "$EVIDENCE_DIR"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
DC=(docker compose --profile precutover --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p isi)

section() { printf '\n=== %s ===\n' "$1"; }

section "Service state"
"${DC[@]}" ps

section "PostgreSQL / Alembic"
"${DC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null
REVISION="$("${DC[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc 'select version_num from alembic_version;' | tr -d '\r')"
[[ "$REVISION" == "20260828_0013" ]] || { echo "ERROR Alembic mismatch: $REVISION"; exit 1; }
echo "PASS Alembic $REVISION"

section "Loopback edge health"
for _ in $(seq 1 90); do
  if curl -ksS --fail --max-time 3 "https://127.0.0.1:${ISI_PRECUTOVER_HTTPS_PORT}/api/v1/health" >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -ksS --fail --max-time 5 "https://127.0.0.1:${ISI_PRECUTOVER_HTTPS_PORT}/api/v1/health" >/dev/null

section "HTTPS/auth/readiness/public-safety smoke"
"${DC[@]}" run --rm --no-deps -v "$CREDENTIALS:/tmp/isi-credentials.json:ro" api \
  python tools/staging/smoke_https.py --base-url https://edge --credentials /tmp/isi-credentials.json

section "S3-compatible storage"
"${DC[@]}" exec -T api python tools/staging/probe_s3.py

section "SMTP capture"
"${DC[@]}" exec -T api python tools/staging/probe_smtp.py

section "RQ data + AI queues"
"${DC[@]}" exec -T api python tools/staging/probe_rq.py

section "Shared host Ollama connectivity"
"${DC[@]}" exec -T ai-worker python - <<'PY'
import httpx
r=httpx.get('http://host.docker.internal:11434/api/tags', timeout=5)
r.raise_for_status()
models={str(x.get('name') or x.get('model')) for x in r.json().get('models', [])}
required={'qwen2.5:7b-instruct'}
if not required.issubset(models):
    raise SystemExit(f'missing required Ollama model(s): {sorted(required - models)}')
print('PASS shared Ollama reachable; qwen2.5:7b-instruct present')
PY

section "Restart / persistence rehearsal"
"${DC[@]}" restart postgres redis minio data-worker ai-worker >/dev/null
for _ in $(seq 1 60); do
  if "${DC[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1 && \
     "${DC[@]}" exec -T redis redis-cli -n 1 ping 2>/dev/null | grep -q PONG; then break; fi
  sleep 1
done
"${DC[@]}" restart api streamlit edge >/dev/null
for _ in $(seq 1 60); do
  if curl -ksS --fail --max-time 3 "https://127.0.0.1:${ISI_PRECUTOVER_HTTPS_PORT}/api/v1/health" >/dev/null 2>&1; then break; fi
  sleep 1
done
"${DC[@]}" exec -T api python tools/staging/probe_s3.py --verify-existing
"${DC[@]}" exec -T api python tools/staging/probe_rq.py

section "Backup / isolated restore"
ISI_RELEASE_DIR="$RELEASE_DIR" ISI_SERVER_ROOT="$ROOT" ISI_SERVER_ENV_FILE="$ENV_FILE" \
  "$RELEASE_DIR/tools/server/backup_restore_rehearsal.sh"

section "Technical evidence"
python3 - "$EVIDENCE_DIR/isi15-server-technical-pass.json" "$REVISION" <<'PY'
import json,sys
from datetime import datetime,timezone
from pathlib import Path
path=Path(sys.argv[1])
path.write_text(json.dumps({
  'status':'PASS',
  'task':'ISI-15-PRODUCTION-STAGING',
  'recorded_at':datetime.now(timezone.utc).isoformat(),
  'alembic_revision':sys.argv[2],
  'target_server':'94.230.189.146',
  'ssh_port':222,
  'compose_project':'isi',
  'data_scope':'preproduction',
  'checks':['postgres','alembic','https_edge','readiness','public_draft_safety','auth_product_isolation','s3','smtp_mailpit','rq_data','rq_ai','shared_ollama','restart_persistence','backup_restore'],
  'manual_browser_qa_required':False,
  'production_cutover_performed':False,
  'dns_changed':False,
  'existing_apps_mutated':False,
  'secrets_recorded':False,
},indent=2)+'\n')
path.chmod(0o600)
PY

echo "=== ISI-15 TARGET SERVER AUTOMATED ACCEPTANCE PASSED ==="
