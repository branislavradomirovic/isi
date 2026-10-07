"""Read-only exact-candidate analyzer; no implementation/CI/server invocation."""

from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "cad6892fd2d710b8263b936c06bb3d8137cdeddc"
FILES = (
    "TECHNICAL_DOCUMENTATION.md",
    "automation/STATUS.md",
    "automation/tasks.json",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md",
    "docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md",
    "docs/help/ISI-SPATIAL-DATA-GUIDE.md",
    "docs/help/ISI-HELP-COVERAGE-MATRIX.md",
    "automation/specs/ISI-29B-GIS-CONTRACTS.md",
    "pyproject.toml",
    "requirements.lock",
    "requirements.runtime.lock",
    "src/platform/spatial/__init__.py",
    "src/platform/spatial/contracts.py",
    "src/platform/spatial/models.py",
    "src/platform/spatial/service.py",
    "src/domains/simpa/spatial_adapter.py",
    "src/domains/ordo/spatial_adapter.py",
    "src/platform/models.py",
    "src/api/app.py",
    "src/api/spatial_routes.py",
    "migrations/versions/20261007_0035_spatial_geometry_versions.py",
    "tests/test_isi_29b_geometry_contract.py",
    "tests/test_isi_29b_spatial_registry.py",
    "tests/test_isi_29b_spatial_api.py",
    "tests/test_isi_29b_native_postgres.py",
    "tools/qa/run_isi29b.py",
    "tools/qa/analyze_isi29b.py",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def manifest() -> dict:
    assert git("branch", "--show-current") == "main"
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/main") == BASELINE
    assert not git("diff", "--cached", "--name-only") and not git("stash", "list")
    assert git("worktree", "list", "--porcelain").count("worktree ") == 1
    dirty = set(git("diff", "--name-only").splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    assert dirty == set(FILES), sorted(dirty ^ set(FILES))
    files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    fingerprint = hashlib.sha256(
        json.dumps({"baseline": BASELINE, "files": files}, sort_keys=True).encode()
    ).hexdigest()
    return {"baseline": BASELINE, "files": files, "fingerprint": fingerprint}


def main() -> None:
    p = ROOT / "automation/evidence/ISI-29B"
    report = json.loads((p / "acceptance.json").read_text())
    assert report["status"] == "PASS" and report["candidate"] == manifest()
    assert len(report["gates"]) == 8
    assert set(report["xml_sha256"]) == {"focused.xml", "native.xml", "regression.xml"}
    compat = json.loads((p / "dependency-compatibility.json").read_text())
    audit_path = p / "dependency-audit.json"
    assert hashlib.sha256(audit_path.read_bytes()).hexdigest() == compat["audit_sha256"]
    audited = json.loads(audit_path.read_text())["dependencies"]
    assert all(not item.get("vulns") and not item.get("skip_reason") for item in audited)

    def packages(text):
        return {
            re.sub(r"[-_.]+", "-", k.lower()): v for k, v in re.findall(r"^([A-Za-z0-9_.-]+)==([^\s]+)", text, re.M)
        }

    for name in ("requirements.lock", "requirements.runtime.lock"):
        before = packages(git("show", BASELINE + ":" + name))
        after = packages((ROOT / name).read_text())
        assert all(after[k] == v for k, v in before.items())
        assert set(after) - set(before) == {"shapely"} and after["shapely"] == "2.1.2"
        if name == "requirements.runtime.lock":
            assert {item["name"]: item["version"] for item in audited} == after
    assert compat["status"] == "PASS" and compat["shapely"] == "2.1.2"
    assert any("cp311-musllinux_1_2_x86_64" in name for name in compat["wheels"])
    for name, sha in compat["wheels"].items():
        assert hashlib.sha256((p / "wheels" / name).read_bytes()).hexdigest() == sha
    for gate in report["gates"]:
        assert gate["returncode"] == 0
        assert hashlib.sha256((p / gate["log"]).read_bytes()).hexdigest() == gate["sha256"]
    for name, sha in report["xml_sha256"].items():
        assert hashlib.sha256((p / name).read_bytes()).hexdigest() == sha
        suites = ET.parse(p / name).getroot().iter("testsuite")
        count = 0
        for suite in suites:
            count += int(suite.get("tests", "0"))
            assert int(suite.get("failures", "0")) == int(suite.get("errors", "0")) == 0
            if name == "native.xml":
                assert int(suite.get("skipped", "0")) == 0
        assert count > 0
    print(json.dumps({"status": "PASS", "candidate": manifest(), "server": "DEFERRED_SERVER_VERIFICATION"}, indent=2))


if __name__ == "__main__":
    main()
