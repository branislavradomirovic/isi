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


def test_masterplan_bootstrap_and_legacy_governance_is_enforced() -> None:
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    for required in (
        "Mandatory bootstrap for every new chat, feature or task",
        "Mandatory legacy/drift audit",
        "Canonical Codex execution contract",
        "Canonical Git/GitHub development contract",
        "Canonical platform architecture map",
        "Canonical SYSTEM INVENTORY - complete product map",
        "Accepted ISI-22E implementation checkpoint - 2026-09-13",
    ):
        assert required in master

    template = (ROOT / "automation/specs/TASK-TEMPLATE.md").read_text()
    for section in (
        "Canonical bootstrap evidence",
        "Canonical system inventory impact",
        "Legacy/drift audit",
        "Exact mutable surface",
        "Implementation-tool authority",
        "Human review and owner gate",
    ):
        assert f"## {section}" in template

    release = (ROOT / "docs/ops/ISI-RELEASE-POLICY.md").read_text()
    assert "direct `main`" in release
    assert "feature branch or pull request is not required" in release

    for rel in (
        "docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md",
        "docs/ops/ISI-SERVER-DEPLOYMENT-RUNBOOK.md",
        "docs/ops/ISI-15-STAGING-RUNBOOK.md",
        "automation/specs/ISI-15-PRODUCTION-STAGING.md",
    ):
        assert "HISTORICAL / SUPERSEDED - DO NOT EXECUTE" in (ROOT / rel).read_text()


def test_live_status_records_current_slice_and_phase22_history() -> None:
    status = (ROOT / "automation/STATUS.md").read_text()
    assert "Accepted ISI-22G implementation SHA: `fd0e46631b5047c64b731d041645e528292f3664`." in status
    assert "Accepted ISI-22G implementation tree: `1a405a65a6fa67f2845ee0a10f2a6f44b11e355e`." in status
    assert "run #75" in status
    assert "run ID `34856573722`" in status
    assert "Accepted ISI-22F implementation SHA: `cfe1574532df65589132bbdd10625172b32fb959`." in status
    assert "Accepted ISI-22E implementation SHA: `44002aa0774a902bdf2d7a0ae56ff3558303571c`." in status
    assert "Accepted ISI-22E implementation tree: `15578107fb21b6aae174a4bf77fc62812377949c`." in status
    assert "Canonical main SHA:" not in status
    assert "Canonical tree:" not in status
    assert status.count("## Owner-facing state model") == 1
    assert "run #70" in status
    assert "whole-phase gap/legacy audit" in status
    assert "Overall `ISI-22-INDUSTRIAL-DATA-PLATFORM` is `COMPLETE / CI_VERIFIED`." in status
    assert "Accepted ISI-23A implementation SHA: `238a881ef39906a2adebbb03fabe80a043017697`." in status
    assert "Accepted ISI-23A implementation tree: `3778f29627100fb48ba369f0618250534870d0a8`." in status
    assert "run #77" in status
    assert "run ID `34900812947`" in status
    assert "Accepted ISI-23B implementation SHA: `088fe79904bd0cc85c4d52d5442218884501b538`." in status
    assert "Accepted ISI-23B implementation tree: `5f8530f6fc7ca82afe7050f39a9f787b048fd8db`." in status
    assert "run #79" in status
    assert "run ID `35018144968`" in status
    assert "Accepted final ISI-23C canonical main SHA: `a49b3faf171dfdbcf9306cfbe50fdc6ad1aabbff`." in status
    assert "run #82" in status
    assert "run ID `35075352285`" in status
    assert "Accepted ISI-23D implementation SHA: `a39caa8160f01dee4e30ab7912a732f0aa68c0d6`." in status
    assert "Accepted ISI-23D implementation tree: `05384a755462790484794714e741f74762d6da0d`." in status
    assert "run #83" in status
    assert "run ID `35081472982`" in status
    assert "Current/final closeout is ISI-23E" in status

    tasks = json.loads((ROOT / "automation/tasks.json").read_text())["tasks"]
    by_id = {task["id"]: task for task in tasks}
    assert by_id["ISI-15-PRODUCTION-STAGING"]["status"] == "historical"
    assert by_id["ISI-16-ISI-RS-PRODUCTION-CUTOVER"]["status"] == "superseded"
    assert by_id["ISI-19-BACKUP-RESTORE-DISASTER-RECOVERY"]["status"] == "done"
    assert by_id["ISI-22-INDUSTRIAL-DATA-PLATFORM"]["status"] == "done"
    assert "22E 44002aa0774a902bdf2d7a0ae56ff3558303571c" in by_id["ISI-22-INDUSTRIAL-DATA-PLATFORM"]["note"]
    assert "22G fd0e46631b5047c64b731d041645e528292f3664" in by_id["ISI-22-INDUSTRIAL-DATA-PLATFORM"]["note"]
    assert "run #75 (34856573722)" in by_id["ISI-22-INDUSTRIAL-DATA-PLATFORM"]["note"]
    assert by_id["ISI-22-INDUSTRIAL-DATA-PLATFORM"]["next"] == "ISI-23-SIMPA-PRODUCTION-METHODOLOGY"
    assert by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["status"] == "done"
    assert "ISI-23B is COMPLETE / CI_VERIFIED on 088fe79904bd0cc85c4d52d5442218884501b538" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert "ISI-23C is COMPLETE / CI_VERIFIED on a49b3faf171dfdbcf9306cfbe50fdc6ad1aabbff" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert "ISI-23D is COMPLETE / CI_VERIFIED on a39caa8160f01dee4e30ab7912a732f0aa68c0d6" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert "run #83 / 35081472982" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert "ISI-23E is the final evidence/test/governance closeout" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["next"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY"


def test_canonical_system_inventory_is_complete_and_self_contained() -> None:
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert master.count("### 0.7 Canonical SYSTEM INVENTORY - complete product map") == 1
    rows = []
    for line in master.splitlines():
        if line.startswith("| INV-"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            assert len(cells) == 18
            assert all(cells)
            rows.append(cells)
    assert len(rows) >= 210
    ids = [row[0] for row in rows]
    assert len(ids) == len(set(ids))
    for letter in "ABCDEFGHIJKLMN":
        assert any(row[0].startswith(f"INV-{letter}") for row in rows)
    by_id = {row[0]: row for row in rows}
    assert by_id["INV-D05"][3] == "NOT_PRESENT"
    assert by_id["INV-E08"][3] == "NOT_PRESENT"
    assert by_id["INV-E09"][3] == "NOT_PRESENT"
    assert by_id["INV-F06"][3] == "NOT_PRESENT"
    assert by_id["INV-H01"][3] == "NOT_PRESENT"
    assert by_id["INV-H02"][3] == "NOT_PRESENT"
    assert by_id["INV-H03"][3] == "NOT_PRESENT"
    assert by_id["INV-H04"][3] == "NOT_PRESENT"
    assert by_id["INV-H05"][3] == "CURRENT_AS_BUILT"
    assert by_id["INV-A17"][3] == "NOT_PRESENT"
    assert by_id["INV-A18"][3] == "CURRENT_AS_BUILT"
    assert by_id["INV-A19"][3] == "PLANNED"
    assert by_id["INV-A20"][3] == "NOT_PRESENT"
    assert by_id["INV-A21"][3] == "CURRENT_AS_BUILT"
    assert by_id["INV-J13"][3] == "TARGET"
    assert by_id["INV-J15"][3] == "TARGET"
    assert by_id["INV-J16"][3] == "DEVELOPMENT_ONLY"
    assert by_id["INV-J21"][3] == "HISTORICAL"
    assert by_id["INV-J31"][3] == "HISTORICAL"
    assert by_id["INV-L07"][3] == "NOT_PRESENT"
    assert by_id["INV-L08"][3] == "NOT_PRESENT"
    assert "isi.opus.rs:8445" in master
    assert "historical `isi.rs:8443`" in master
    assert "There is no application-owned scheduler" in master
    assert "no active external document-conversion service" in master
