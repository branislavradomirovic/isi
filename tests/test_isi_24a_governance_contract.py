import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_24a_governance_and_non_goals_are_explicit() -> None:
    status = (ROOT / "automation/STATUS.md").read_text(encoding="utf-8")
    tasks = json.loads((ROOT / "automation/tasks.json").read_text(encoding="utf-8"))
    spec = (ROOT / "automation/specs/ISI-24A-ORDO-GOVERNED-EVIDENCE-SCENARIO-GIS-CONTRACTS.md").read_text(encoding="utf-8")
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text(encoding="utf-8")
    assert "3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73" in status
    assert "#84" in status and "35084716444" in status
    assert "Current slice is `ISI-24A" in status
    t24 = next(x for x in tasks["tasks"] if x["id"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY")
    assert t24["status"] == "in_progress"
    assert t24["spec"].endswith("ISI-24A-ORDO-GOVERNED-EVIDENCE-SCENARIO-GIS-CONTRACTS.md")
    for marker in ["no automatic policy recommendation", "No API", "No Codex", "production-server"]:
        assert marker.lower() in spec.lower()
    assert "| INV-C33 | ORDO governed reference evidence |" in master
    assert "| INV-C34 | ORDO governed spatial-unit identity |" in master
    assert "tests/test_isi_24a*.py" in master


def test_24a_migration_is_linear_truthful_and_legacy_safe() -> None:
    migration = (ROOT / "migrations/versions/20260916_0030_ordo_governed_evidence_gis_contracts.py").read_text(encoding="utf-8")
    assert 'revision = "20260916_0030"' in migration
    assert 'down_revision = "20260915_0029"' in migration
    assert 'server_default="LEGACY_UNVERSIONED"' in migration
    assert 'server_default="legacy_evidence_readiness"' in migration
    assert 'server_default="0"' in migration
    assert "WHEN status = 'reviewed' THEN 'reviewed'" in migration
    assert 'batch.alter_column("scenario_contract_version", server_default="ORDO-SCENARIO-CONTRACT-v1")' in migration
