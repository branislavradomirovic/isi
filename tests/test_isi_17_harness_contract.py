import json
import subprocess
import sys
from pathlib import Path

from tools.ci.policy_check import validate_agents_text, validate_automation_text


ROOT = Path(__file__).resolve().parents[1]


def test_policy_guard_accepts_repository() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.ci.policy_check"], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "POLICY PASS" in result.stdout


def test_agents_policy_contract_is_fail_closed() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert validate_agents_text(agents) == []
    weakened = agents.replace("The platform contains two domain products only: SIMPA and ORDO.", "")
    missing = validate_agents_text(weakened)
    assert "The platform contains two domain products only: SIMPA and ORDO." in missing


def test_automation_policy_rejects_server_contact_and_deploy_tooling() -> None:
    assert validate_automation_text(Path("synthetic.yml"), "run: ssh deploy@example.invalid")
    assert validate_automation_text(Path("synthetic.sh"), "scp artifact host:/tmp/")
    assert validate_automation_text(Path("synthetic.sh"), "tools/release/deploy_server_release.sh")
    assert validate_automation_text(Path("synthetic.sh"), "curl https://isi.rs/health")
    assert validate_automation_text(Path("synthetic.yml"), "run: kubectl apply -f prod.yml")


def test_industrialization_registry_is_complete_and_server_task_is_deferred() -> None:
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())["tasks"]
    by_id = {task["id"]: task for task in tasks}
    for number in range(17, 29):
        assert any(task_id.startswith(f"ISI-{number}-") for task_id in by_id)
    server_task = by_id["ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"]
    assert server_task["status"] in {"planned", "deferred"}
    assert "owner" in server_task["note"].lower()


def test_required_ci_jobs_and_fail_closed_runner_exist() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    for job in (
        "policy",
        "quality",
        "tests",
        "architecture-security",
        "migration",
        "native-postgres",
        "compose",
        "supply-chain",
        "build",
        "acceptance",
    ):
        assert f"  {job}:" in workflow
    assert "needs: [policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build]" in workflow
    runner = (ROOT / "tools/ci/run_isi17_acceptance.sh").read_text()
    assert "set -Eeuo pipefail" in runner
    assert "tools/ci/native_postgres_tests.sh" in runner
    assert "|| true" not in runner


def test_dependency_and_container_hygiene_contracts_exist() -> None:
    assert "Python 3.11" in (ROOT / "requirements.lock").read_text().splitlines()[1]
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert 'requires = ["setuptools==84.0.0", "wheel==0.48.0"]' in pyproject
    provenance = (ROOT / "automation/evidence/ISI-17/dependency-lock.md").read_text()
    assert "pip-tools==7.6.1" in provenance
    ignored = (ROOT / ".dockerignore").read_text().splitlines()
    assert ".git" in ignored
    assert ".env" in ignored
    assert "runtime" in ignored
