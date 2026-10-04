from pathlib import Path
import json
import os
import sys

import pytest

from tools.release.evidence import GROUPS, digest, junit, source_identity

ROOT = Path(__file__).resolve().parents[1]


def write_junit(tmp_path, cases):
    path = tmp_path / "results.xml"
    path.write_text("<testsuites><testsuite>" + "".join(cases) + "</testsuite></testsuites>")
    return path


def test_consolidated_groups_count_real_successful_cases(tmp_path):
    cases = [f'<testcase classname="tests.{prefixes[0]}_contract" name="bounded"/>' for prefixes in GROUPS.values()]
    cases.append('<testcase classname="tests.test_native" name="native"><skipped/></testcase>')
    report = junit(write_junit(tmp_path, cases))
    assert report["groups"] == dict.fromkeys(GROUPS, 1)
    assert report["passed"] == len(GROUPS)
    assert report["skipped"] == 1


@pytest.mark.parametrize("child", ["failure", "error"])
def test_regression_failure_cannot_be_consolidated(tmp_path, child):
    with pytest.raises(ValueError, match="failed_or_empty"):
        junit(write_junit(tmp_path, [f'<testcase><{child}/></testcase>']))


def test_empty_report_cannot_claim_acceptance(tmp_path):
    with pytest.raises(ValueError, match="failed_or_empty"):
        junit(write_junit(tmp_path, []))


def test_partial_group_coverage_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="required_group_missing"):
        junit(write_junit(tmp_path, ['<testcase classname="tests.test_isi_23a"/>']))


def test_native_postgres_cannot_be_skipped(tmp_path):
    with pytest.raises(ValueError, match="native_skips_forbidden"):
        junit(write_junit(tmp_path, ['<testcase><skipped/></testcase>']), native=True)


def test_native_success_is_separate_from_regression(tmp_path):
    report = junit(write_junit(tmp_path, ['<testcase classname="tests.native"/>']), native=True)
    assert report["passed"] == 1 and report["skipped"] == 0


def test_candidate_identity_binds_all_sources_and_exact_main():
    identity = source_identity(ROOT)
    assert len(identity["head"]) == len(identity["tree"]) == 40
    assert len(identity["candidate_sha256"]) == 64
    assert identity["files"]["tools/release/evidence.py"] == digest(ROOT / "tools/release/evidence.py")
    assert identity["files"]["tests/evals/SIMPA-EVAL-v1.json"] != identity["files"]["tests/evals/ORDO-EVAL-v1.json"]


def test_bad_gate_or_source_change_rejected_before_report_access(tmp_path):
    from tools.release.evidence import consolidate

    identity = source_identity(ROOT)
    with pytest.raises(ValueError, match="gate_not_passed"):
        consolidate(ROOT, tmp_path, identity, {"regression": 0})
    changed = dict(identity, candidate_sha256="0" * 64)
    with pytest.raises(ValueError, match="source_changed"):
        consolidate(ROOT, tmp_path, changed, {})


def test_disposable_postgres_probes_final_tcp_server():
    for filename in ("native_postgres_tests.sh", "isi19_recovery_rehearsal.sh"):
        script = (ROOT / "tools/ci" / filename).read_text()
        probes = [line for line in script.splitlines() if "pg_isready" in line]
        assert len(probes) == 2
        assert all("pg_isready -h 127.0.0.1 -U ci_user -d isi_ci" in line for line in probes)


@pytest.mark.parametrize("artifact", ["pack.json", "gates.json", "SIMPA-methodology.json", "model-evaluation-provenance.json"])
def test_independent_verification_rejects_artifact_tampering(tmp_path, monkeypatch, artifact):
    from tools.release import evidence

    pack = {"source": {"candidate_sha256": "a" * 64}, "gates": {"regression": 0},
            "methodology": {"SIMPA": {"human_validation_required": True}},
            "evaluation_provenance": {"SIMPA": {"production_promotion_evidence": False}},
            "model_authority": {"source.py": "b" * 64}}
    monkeypatch.setattr(evidence, "consolidate", lambda *args: pack)
    artifacts = {
        "pack.json": pack,
        "gates.json": pack["gates"],
        "SIMPA-methodology.json": {"source": pack["source"], "acceptance": pack["methodology"]["SIMPA"]},
        "model-evaluation-provenance.json": {"source": pack["source"], "evaluations": pack["evaluation_provenance"], "model_authority": pack["model_authority"]},
    }
    for name, data in artifacts.items():
        (tmp_path / name).write_text(json.dumps(data))
    assert evidence.verify(ROOT, tmp_path)["result"] == "PASS"
    changed = dict(artifacts[artifact], forged_claim=True)
    (tmp_path / artifact).write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="mismatch"):
        evidence.verify(ROOT, tmp_path)


def test_machine_readable_gate_output_is_separate_from_warnings(tmp_path):
    from tools.qa.run_isi27b import execute_gate

    command = [sys.executable, "-c", 'import sys; print("{\\"result\\": true}"); print("fixture warning", file=sys.stderr)']
    assert execute_gate(command, root=tmp_path, output=tmp_path, filename="performance.jsonl", env=dict(os.environ)) == 0
    assert json.loads((tmp_path / "performance.jsonl").read_text()) == {"result": True}
    assert (tmp_path / "performance.jsonl.stderr").read_text().strip() == "fixture warning"


def test_surface_analysis_preserves_baseline_markdown_but_rejects_new_whitespace(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from tools.qa import analyze_isi27b as analyzer

    (tmp_path / "TECHNICAL_DOCUMENTATION.md").write_text("Historical Markdown hard break.  \n")
    monkeypatch.setattr(analyzer, "ROOT", tmp_path)
    state = {"status": " M TECHNICAL_DOCUMENTATION.md\n"}
    monkeypatch.setattr(analyzer.subprocess, "check_output", lambda command, **kwargs: analyzer.BASELINE + "\n" if command[1] == "rev-parse" else state["status"])
    monkeypatch.setattr(analyzer.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    analyzer.check_surface()
    state["status"] = "?? TECHNICAL_DOCUMENTATION.md\n"
    with pytest.raises(SystemExit, match="whitespace"):
        analyzer.check_surface()
