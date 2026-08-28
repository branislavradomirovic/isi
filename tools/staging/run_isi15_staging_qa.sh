#!/usr/bin/env bash
set -euo pipefail
cat <<'MSG'
ERROR: Local ISI Docker staging execution is disabled by the locked production workflow.

The developer workstation is not the ISI staging/production host.
Do not start docker-compose.staging.yml locally.

Continue with automated local validation, then run the read-only target-server preflight:
  tools/server/isi_server_preflight.sh

The exact server deployment is created only after that preflight is reviewed.
MSG
exit 64
