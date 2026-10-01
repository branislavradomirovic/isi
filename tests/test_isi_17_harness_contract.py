import json
import subprocess
import sys
from pathlib import Path

from tools.ci.policy_check import (
    validate_agents_text,
    validate_automation_text,
    validate_full_acceptance_workflow_text,
)


ROOT = Path(__file__).resolve().parents[1]

HISTORICAL_EVIDENCE = ROOT / "automation/specs/ISI-26-R1-HISTORICAL-GOVERNANCE-EVIDENCE.json"


def _historical_evidence() -> dict:
    return json.loads(HISTORICAL_EVIDENCE.read_text(encoding="utf-8"))


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
    weakened_ci = agents.replace("DO NOT enable or introduce automatic GitHub-hosted Actions triggers for full CI during development.", "")
    missing_ci = validate_agents_text(weakened_ci)
    assert "DO NOT enable or introduce automatic GitHub-hosted Actions triggers for full CI during development." in missing_ci


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
    assert "  workflow_dispatch:" in workflow
    for forbidden_trigger in ("push", "pull_request", "pull_request_target", "schedule", "workflow_run", "merge_group"):
        assert f"  {forbidden_trigger}:" not in workflow
    assert validate_full_acceptance_workflow_text(workflow) == []
    weakened_workflow = workflow.replace("  workflow_dispatch:", "  push:", 1)
    assert any("unauthorized automatic trigger: push" in item for item in validate_full_acceptance_workflow_text(weakened_workflow))
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
        "CI / GitHub Actions Cost & Acceptance Policy",
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
    assert "manual `workflow_dispatch`" in release
    assert "GitHub Actions usage is checked before and after" in release

    for rel in (
        "docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md",
        "docs/ops/ISI-SERVER-DEPLOYMENT-RUNBOOK.md",
        "docs/ops/ISI-15-STAGING-RUNBOOK.md",
        "automation/specs/ISI-15-PRODUCTION-STAGING.md",
    ):
        assert "HISTORICAL / SUPERSEDED - DO NOT EXECUTE" in (ROOT / rel).read_text()


def test_live_status_records_phase24_closeout_and_verified_predecessors() -> None:
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
    assert "Accepted ISI-23E closeout SHA: `3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73`." in status
    assert "run #84" in status
    assert "run ID `35084716444`" in status
    assert "Accepted ISI-24B implementation SHA: `0ad913db23cea44033e8adf693eb179edfa8fb5d`." in status
    assert "Accepted ISI-24B implementation tree: `1008022ebe4cf95b4d45a12ff746188e6c8efa11`." in status
    assert "run #86" in status and "run ID `35147730914`" in status
    assert "Accepted ISI-24C implementation SHA: `76e4ca5265f48a096d2253c88898e1aaedbff991`." in status
    assert "Accepted ISI-24C implementation tree: `0a6ec7b7ab4db5d43c570c714c065f8fef7093f4`." in status
    assert "run #87" in status and "run ID `35153774409`" in status
    assert "Accepted ISI-24D implementation SHA: `49377e808845fc8746f0484ea7b452954c9e83b4`." in status
    assert "Accepted ISI-24D implementation tree: `c8ea52299d80551ee303dbeef95d343b59448892`." in status
    assert "run #88" in status and "run ID `35220908672`" in status
    assert "Accepted ISI-24E remediation/closeout implementation SHA: `5937daa2ea7ff9c476bd6a05a04841d1534aefe2`." in status
    assert "run #90" in status and "run ID `35238623960`" in status
    assert "Overall `ISI-24-ORDO-PRODUCTION-METHODOLOGY` is `COMPLETE / CI_VERIFIED`." in status
    historical = _historical_evidence()["phase24_transition"]
    assert historical["authority_sha"] == "7e4db145c285aaff7a96f9c37279c44477f4432f"
    assert historical["status_marker"] == "ISI-25 bootstrap/audit - Industrial AI / MLOps"

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
    assert "ISI-23 is COMPLETE / CI_VERIFIED" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert "3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert "run #84 / 35084716444" in by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["note"]
    assert by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]["next"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY"
    assert by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["status"] == "done"
    assert "ISI-24D is COMPLETE / CI_VERIFIED on 49377e808845fc8746f0484ea7b452954c9e83b4" in by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["note"]
    assert "run #88 / 35220908672" in by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["note"]
    assert "5937daa2ea7ff9c476bd6a05a04841d1534aefe2" in by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["note"]
    assert "run #90 / 35238623960 attempt 2 completed success" in by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["note"]
    assert by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["spec"] == "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md"
    assert historical["phase25_status"] == "planned"
    assert historical["phase25_note_marker"] == "CURRENT/NEXT BOOTSTRAP"
    assert by_id["ISI-25-INDUSTRIAL-AI-MLOPS"]["status"] == "done"
    assert by_id["ISI-26-PERFORMANCE-LOAD-RESILIENCE"]["status"] == "in_progress"


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
    assert by_id["INV-A19"][3] == "CURRENT_AS_BUILT"
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
    assert by_id["INV-N07"][3] == "HISTORICAL"
    assert "isi.rs:8443" in " | ".join(by_id["INV-N07"])
    assert "central-ingress-nginx-1" in master
    assert "https://isi.opus.rs:8445/" in master
    assert "There is no application-owned scheduler" in master
    assert "no active external document-conversion service" in master
