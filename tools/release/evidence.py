"""Bind real release-gate reports to an exact repository candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

GROUPS = {
    "SIMPA": ("test_isi_23",),
    "ORDO": ("test_isi_24",),
    "models": ("test_isi_25",),
    "security": ("test_isi_20",),
    "privacy": ("test_isi_21",),
    "recovery": ("test_isi_19",),
    "performance": ("test_isi_26",),
}
REPORTS = {
    "regression": "pytest.xml",
    "native": "native-postgres.xml",
    "recovery": "recovery.json",
    "performance": "performance.jsonl",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def source_identity(root: Path) -> dict:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=root)

    if git("branch", "--show-current").strip() != b"main":
        raise ValueError("canonical_main_required")
    if git("diff", "--cached", "--name-only").strip():
        raise ValueError("index_must_be_empty")
    paths = sorted(set(git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")) - {b""})
    files = {}
    for raw in paths:
        relative = raw.decode()
        path = root / relative
        if path.is_symlink():
            raise ValueError("source_symlink_not_supported")
        files[relative] = digest(path) if path.is_file() else "DELETED"
    return {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
        "candidate_sha256": hashlib.sha256(canonical(files)).hexdigest(),
        "files": files,
    }


def junit(path: Path, *, native: bool = False) -> dict:
    document = ET.parse(path).getroot()
    cases = list(document.iter("testcase"))
    if not cases or list(document.iter("failure")) or list(document.iter("error")):
        raise ValueError("failed_or_empty_junit")
    skipped = [case for case in cases if case.find("skipped") is not None]
    if native and skipped:
        raise ValueError("native_skips_forbidden")
    passed = [case for case in cases if case.find("skipped") is None]
    groups = {
        name: sum(any(prefix in case.attrib.get("classname", "") for prefix in prefixes) for case in passed)
        for name, prefixes in GROUPS.items()
    }
    if not native and not all(groups.values()):
        raise ValueError("required_group_missing")
    return {"passed": len(passed), "skipped": len(skipped), "groups": groups}


def consolidate(root: Path, output: Path, identity: dict, gates: dict) -> dict:
    if source_identity(root) != identity:
        raise ValueError("source_changed_during_acceptance")
    if set(gates) != {"regression", "native", "performance", "policy", "diff"} or any(value != 0 for value in gates.values()):
        raise ValueError("gate_not_passed")
    regression = junit(output / REPORTS["regression"])
    native = junit(output / REPORTS["native"], native=True)
    recovery = json.loads((output / REPORTS["recovery"]).read_text())
    if any(recovery.get(key) != "success" for key in ("status", "postgresql17_restore", "object_storage_restore")):
        raise ValueError("recovery_not_passed")
    if recovery.get("server_verification") != "DEFERRED_SERVER_VERIFICATION":
        raise ValueError("invalid_server_claim")
    from tools.performance.evidence import validate_record
    from tools.performance.workloads import catalogue

    records = [json.loads(line) for line in (output / REPORTS["performance"]).read_text().splitlines()]
    results = [validate_record(record) for record in records]
    expected = {workload.workload_id for workload in catalogue()}
    actual = [result.contract.workload_id for result in results]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("performance_catalogue_incomplete")
    if any(not record["summary"]["accepted"] or record["repository_sha"] != identity["head"] for record in records):
        raise ValueError("performance_not_accepted")
    evaluations = {}
    for product in ("SIMPA", "ORDO"):
        path = root / f"tests/evals/{product}-EVAL-v1.json"
        fixture = json.loads(path.read_text())
        if fixture["product_code"] != product or fixture["frozen"] is not True or fixture["foundation_only_not_production_promotion_evidence"] is not True:
            raise ValueError("evaluation_foundation_boundary")
        evaluations[product] = {"path": str(path.relative_to(root)), "sha256": digest(path), "version": fixture["version"], "case_count": fixture["case_count"], "production_promotion_evidence": False}
    return {
        "schema": "ISI-27B-RC-PACK-v1",
        "source": identity,
        "gates": gates,
        "reports": {name: {"path": path, "sha256": digest(output / path)} for name, path in REPORTS.items()},
        "regression": regression,
        "native_postgres": native,
        "methodology": {product: {"contract_tests_passed": regression["groups"][product], "live_methodology_state_verified": False, "human_validation_required": True} for product in ("SIMPA", "ORDO")},
        "evaluation_provenance": evaluations,
        "model_authority": {str(path.relative_to(root)): digest(path) for path in sorted((root / "src/platform/ai").glob("*.py"))},
        "governance": {"path": "docs/release/ISI-RC-GOVERNANCE-PACK.md", "sha256": digest(root / "docs/release/ISI-RC-GOVERNANCE-PACK.md")},
        "limits": {"SERVER_VERIFIED": False, "CI_VERIFIED": False, "PRODUCTION_CAPACITY_VERIFIED": False, "timing": "INHERIT_ISI26_UNCALIBRATED", "resource": "INHERIT_ISI26_UNAVAILABLE"},
    }


def verify(root: Path, output: Path) -> dict:
    pack = json.loads((output / "pack.json").read_text())
    expected = consolidate(root, output, pack["source"], pack["gates"])
    if pack != expected:
        raise ValueError("pack_content_mismatch")
    if json.loads((output / "gates.json").read_text()) != pack["gates"]:
        raise ValueError("gate_record_mismatch")
    for product, acceptance in pack["methodology"].items():
        if json.loads((output / f"{product}-methodology.json").read_text()) != {"source": pack["source"], "acceptance": acceptance}:
            raise ValueError("methodology_artifact_mismatch")
    provenance = {"source": pack["source"], "evaluations": pack["evaluation_provenance"], "model_authority": pack["model_authority"]}
    if json.loads((output / "model-evaluation-provenance.json").read_text()) != provenance:
        raise ValueError("model_provenance_mismatch")
    return {"result": "PASS", "pack_sha256": digest(output / "pack.json"), "candidate_sha256": pack["source"]["candidate_sha256"]}
