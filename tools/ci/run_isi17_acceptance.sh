#!/usr/bin/env bash
set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
trap 'rc=$?; echo "=== ISI-17 ACCEPTANCE FAIL (exit $rc) ===" >&2; exit "$rc"' ERR
phase() { printf '\n=== %s ===\n' "$1"; }
phase policy; python -m tools.ci.policy_check
phase dependencies; python -m pip check
phase compile; python -m compileall -q src tests tools/ci
phase lint; python -m ruff check --select E9 src tests
python -m ruff check tools/ci tests/test_isi_17_harness_contract.py
phase type-baseline; python -m mypy
phase tests; python -m pytest -q --junitxml=automation/evidence/ISI-17/pytest.xml
phase architecture-security
python -m pytest -q tests/test_architecture_contract.py tests/test_isi_07_policy.py tests/test_isi_14_session_contract.py tests/test_isi_14_production_config_contract.py
phase migration-offline; tools/ci/migration_check.sh offline
phase migration-live; tools/ci/migration_live_docker.sh
phase compose; tools/ci/compose_config.sh
phase secret-scan
docker run --rm -v "$root:/repo" zricethezav/gitleaks:v8.28.0 detect --source=/repo --no-banner
phase dependency-audit; python -m pip_audit -r requirements.lock
phase sast; python -m bandit -q -r src -lll -ii
phase build; docker build --pull=false -f docker/Dockerfile -t isi:isi17-ci .
phase whitespace; git diff --check
trap - ERR
echo "=== ISI-17 ACCEPTANCE PASS ==="
