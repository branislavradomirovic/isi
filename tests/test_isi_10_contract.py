from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ordo_boundary_and_no_simpa_smuggling():
    assert (ROOT / "src/domains/ordo/__init__.py").read_text().strip() == ""
    service = (ROOT / "src/domains/ordo/service.py").read_text()
    assert 'Workspace.product_code == "ORDO"' in service
    assert "src.domains.simpa" not in service


def test_ui_and_api_are_ordo_specific():
    routes = (ROOT / "src/api/ordo_routes.py").read_text()
    ui = (ROOT / "src/streamlit_app/ordo_workspace.py").read_text()
    assert 'prefix="/api/v1/ordo"' in routes
    assert "ORDO · Pregled destinacije" in ui
    assert "ne generiše vrednosti" in ui
