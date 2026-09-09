import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_policy_guard_accepts_repository() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.ci.policy_check"], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "POLICY PASS" in result.stdout


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
        "policy", "quality", "tests", "architecture-security", "migration",
        "compose", "supply-chain", "build", "acceptance",
    ):
        assert f"  {job}:" in workflow
    runner = (ROOT / "tools/ci/run_isi17_acceptance.sh").read_text()
    assert "set -Eeuo pipefail" in runner
    assert "|| true" not in runner


def test_dependency_and_container_hygiene_contracts_exist() -> None:
    assert "Python 3.11" in (ROOT / "requirements.lock").read_text().splitlines()[1]
    ignored = (ROOT / ".dockerignore").read_text().splitlines()
    assert ".git" in ignored
    assert ".env" in ignored
    assert "runtime" in ignored
