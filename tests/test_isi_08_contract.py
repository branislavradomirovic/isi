from pathlib import Path


def test_domain_files_and_routing_contract_are_present():
    required = [
        "src/domains/simpa/models.py",
        "src/domains/simpa/catalog.py",
        "src/domains/simpa/service.py",
        "src/domains/simpa/schemas.py",
        "src/api/simpa_routes.py",
        "src/streamlit_app/simpa_api.py",
        "src/streamlit_app/simpa_workspace.py",
    ]
    for item in required:
        assert Path(item).is_file(), item
    api = Path("src/api/simpa_routes.py").read_text()
    assert 'prefix="/api/v1/simpa"' in api
    assert 'product_code="SIMPA"' in api
    ui = Path("src/streamlit_app/app.py").read_text()
    assert "ISI-08 SIMPA domain routing" in ui
    assert "render_simpa_indicators" in ui
    assert "render_ordo_indicator_placeholder" in ui
    domain_ui = Path("src/streamlit_app/simpa_workspace.py").read_text()
    assert "Konfiguracija lokalnog sistema" in domain_ui
    assert "Novi monitoring ciklus" in domain_ui


def test_simpa_foundation_has_no_fake_domain_metrics_or_person_level_model():
    ui = Path("src/streamlit_app/simpa_workspace.py").read_text()
    models = Path("src/domains/simpa/models.py").read_text()
    assert "izmišljenu JLS" in ui
    assert "ne generiše indikator vrednosti" in ui
    for forbidden in ["person_id", "citizen_id", "jmbg", "beneficiary_name"]:
        assert forbidden not in models.lower()
