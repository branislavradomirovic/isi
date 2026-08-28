from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ordo_analytics_files_and_domain_boundary():
    required = [
        "src/domains/ordo/analytics_models.py",
        "src/domains/ordo/analytics_service.py",
        "src/domains/ordo/analytics_schemas.py",
        "src/api/ordo_analytics_routes.py",
        "src/streamlit_app/ordo_analytics_api.py",
        "src/streamlit_app/ordo_analytics_workspace.py",
    ]
    for item in required:
        assert (ROOT / item).exists(), item
    assert (ROOT / "src/domains/ordo/__init__.py").read_text().strip() == ""


def test_ordo_analytics_does_not_claim_destination_outcome_score():
    service = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    ui = (ROOT / "src/streamlit_app/ordo_analytics_workspace.py").read_text()
    assert "semantic_notice" in service
    assert "not a competitiveness" in service
    assert "evidence_readiness_only" in service
    assert '"forecast_performed": False' in service
    assert "ne izmišlja formule" in ui
    assert "ne prognozira efekte" in ui
