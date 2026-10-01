from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "f0047321ee4410522697144ecfa464087f1b83bc"
TREE = "06e419ec656ee2fb0bfb74b4a6b10d42ef275f25"
HISTORICAL_EVIDENCE = ROOT / "automation/specs/ISI-26-R1-HISTORICAL-GOVERNANCE-EVIDENCE.json"
RECOVERY_MUTABLE = {
    "automation/specs/ISI-25B-EVALUATION-PROMOTION-RUNTIME.md",
    "src/api/ai_routes.py", "src/platform/ai/evaluation.py", "src/platform/ai/governance.py",
    "src/platform/ai/promotion.py", "src/platform/ai/monitoring.py", "src/platform/ai/xai.py",
    "src/platform/ai/schemas.py",
    "tests/test_isi_25b_evaluation_engines.py", "tests/test_isi_25b_promotion.py",
    "tests/test_isi_25b_safety_retrieval.py", "tests/test_isi_25b_monitoring_xai_help.py",
    "tests/test_isi_25b_capability_runtime.py", "tests/test_isi_25b_governance_contract.py",
}
FROZEN_FHR1_SHA256 = {
    "automation/STATUS.md": "c032eededb9fb28a0d94a3426a974743363f01e231d06c7c9845c8ecfd54d156",
    "automation/tasks.json": "4d2c25c6b712f443d03dd5b3cc2f3854bda4b200e7a13ba5aefb0318a03d608e",
    "docs/help/ISI-AI-USER-GUIDE.md": "4ff151e7a216e339998f68166a7acd421db050298e8ee148d735b29cffd423f3",
    "docs/help/ISI-HELP-COVERAGE-MATRIX.md": "0496d3b353881148c27ce80cb3af29f86a1a8ec5b5dd1f1c55e1dbd0ef1c98e4",
    "docs/roadmap/ISI-25-MODEL-REGISTRY.md": "8511a9996829c3441dfa070e6f5c697bf96228ee7e7f034e034297cf7074f7df",
    "docs/roadmap/ISI-25-PROMOTION-POLICY.md": "c63f95377c0c3f2a2e66ee10b1884bf99e13343b16881be33aeb11d6c1034e8c",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md": "6edf87c64322e8fb002eabd6b4616d683e63bea87d15ce8850100c94df71ce46",
    "migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py": "75a413980e0d71b3d52454c38daf25bf9a89c4a95df8f4030ceb6578d1d0e451",
    "src/platform/ai/models.py": "2ef6b8bc8d8bcefbdeaccfec6f1c229eb5980e81ff49b624b64620bbbe87b86f",
    "src/platform/ai/service.py": "6b49e4b104f581aab91d54783c8249c5a7e3b70f300276f6e995ebfe394353d5",
    "tests/test_isi_24d_help_xai_contract.py": "472ed1e49bda3feea86c9e5df527dc1e9c26e75c77f312737379a81f1c58026b",
    "tests/test_isi_25a_api_contract.py": "970852f58be1fe8f9b5c024ce263f3c6b28d4ebb64c986abf74bddf7ce009b15",
    "tests/test_isi_25a_governance_contract.py": "a29bffdcb2b94de5c54dda001998b5158876c05d2f2b7a9464d8001fcaa12bae",
    "tests/test_isi_25a_model_registry.py": "645beee063ac28e78625bef6039dd22b37145a72e8eabf3d740fdf72c8082f2c",
}


def _text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def _historical_evidence():
    return json.loads(HISTORICAL_EVIDENCE.read_text(encoding="utf-8"))


def test_0034_revision_and_additive_runtime_tables():
    migration = _text("migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py")
    assert 'revision = "20260918_0034"' in migration
    assert 'down_revision = "20260917_0033"' in migration
    for table in ("core_ai_evaluation_benchmarks", "core_ai_capability_thresholds",
                  "core_ai_promotion_decisions", "core_ai_capability_runtime_states", "core_ai_drift_snapshots"):
        assert table in migration
    assert "DROP TABLE" not in migration.split("def downgrade", 1)[0].upper()


def test_25a_acceptance_truth_and_25b_current_without_false_ci_claim():
    historical = _historical_evidence()["fhr1_candidate"]
    assert historical["authority_sha"] == "7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e"
    assert historical["accepted_25a_sha"] == BASELINE
    assert historical["accepted_25a_tree"] == TREE
    assert historical["phase25_status"] == "planned"
    assert historical["phase25_phase_status"] == "in_progress"
    assert historical["phase25b_status"] == "in_progress"
    assert "IN PROGRESS" in historical["status_marker"]
    assert "No GitHub-hosted acceptance ran" in historical["hosted_acceptance_marker"]
    current = json.loads(_text("automation/tasks.json"))["tasks"]
    current_by_id = {item["id"]: item for item in current}
    assert current_by_id["ISI-25-INDUSTRIAL-AI-MLOPS"]["status"] == "done"
    assert current_by_id["ISI-25B-EVALUATION-PROMOTION-RUNTIME"]["status"] == "done"


def test_manual_only_workflow_and_no_new_permission_taxonomy():
    workflow = _text(".github/workflows/ci.yml")
    triggers = workflow.split("concurrency:", 1)[0]
    assert "workflow_dispatch:" in triggers
    assert all(item not in triggers for item in ("push:", "pull_request:", "schedule:", "workflow_run:"))
    routes = _text("src/api/ai_routes.py")
    for permission in ("ai.run", "analysis.run", "analysis.read", "report.publish"):
        assert permission in routes
    assert "ai.manage" not in routes


def test_frozen_protocol_and_foundation_fixtures_match_accepted_25a():
    expected = _historical_evidence()["fhr1_candidate"]["foundation_sha256"]
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_ordo_semantics_and_no_server_provider_worker_dependency_changes():
    master = _text("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md")
    for marker in ("scenario is not forecast", "NOT_ESTIMATED", "NO_APPROVED_RESPONSE_MODEL",
                   "LEGACY_NOT_EVALUATED", "no automatic selection/fallback"):
        assert marker in master
    historical_surface = set(_historical_evidence()["fhr1_candidate"]["recovery_mutable"])
    assert historical_surface == RECOVERY_MUTABLE
    assert not any(path.startswith((".github/", "src/workers/", "deploy/", "docker/")) for path in historical_surface)
    assert not any(path.endswith(("requirements.txt", "pyproject.toml", "uv.lock")) for path in historical_surface)


def test_recovery_surface_and_frozen_fhr1_bytes_are_exact_on_dirty_or_clean_checkout():
    frozen = set(FROZEN_FHR1_SHA256)
    assert RECOVERY_MUTABLE.isdisjoint(frozen)
    effective_surface = RECOVERY_MUTABLE | frozen
    assert len(RECOVERY_MUTABLE) == 14
    assert len(frozen) == 14
    assert len(effective_surface) == 28
    assert "tests/test_isi_24d_help_xai_contract.py" in frozen
    assert "automation/specs/ISI-25B-EVALUATION-PROMOTION-RUNTIME.md" in RECOVERY_MUTABLE
    evidence = _historical_evidence()["fhr1_candidate"]
    assert evidence["authority_sha"] == "7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e"
    assert evidence["frozen_sha256"] == FROZEN_FHR1_SHA256

def test_final_acceptance_markers_match_recovered_exact_28_surface():
    spec = _text("automation/specs/ISI-25B-EVALUATION-PROMOTION-RUNTIME.md")
    assert "independent exact-28 final-acceptance structural/semantic analyzer" in spec
    assert "exact 28 final-acceptance candidate surface locked" in spec
    assert "ISI25B_EXACT_28_CANDIDATE_SURFACE=PASS" in spec
    for stale in (
        "independent exact-27 structural/semantic analyzer",
        "exact 27 dirty",
        "ISI25B_EXACT_27_DIRTY_SURFACE=PASS",
    ):
        assert stale not in spec
