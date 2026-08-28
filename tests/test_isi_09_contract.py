from pathlib import Path


def test_simpa_analytics_files_and_boundary_contract():
    required = [
        "src/domains/simpa/analytics_models.py",
        "src/domains/simpa/analytics_service.py",
        "src/domains/simpa/analytics_schemas.py",
        "src/api/simpa_analytics_routes.py",
        "src/streamlit_app/simpa_analytics_workspace.py",
        "src/streamlit_app/simpa_analytics_api.py",
    ]
    for item in required:
        assert Path(item).exists(), item
    assert Path("src/domains/simpa/__init__.py").read_text().strip() == ""


def test_simpa_analytics_does_not_claim_domain_risk_score():
    service = Path("src/domains/simpa/analytics_service.py").read_text()
    workspace = Path("src/streamlit_app/simpa_analytics_workspace.py").read_text()
    assert "semantic_notice" in service
    assert "not a social-risk" in service
    assert "Kvalitet dokaza" in workspace
    assert "ne izmišlja formule" in workspace
