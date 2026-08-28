from pathlib import Path


def test_administration_navigation_is_real_not_placeholder():
    app = Path("src/streamlit_app/app.py").read_text()
    workspace = Path("src/streamlit_app/administration_workspace.py").read_text()
    assert "render_administration" in app
    assert 'nav_code == "administration"' in app
    for label in ("Pregled", "Članovi", "Pozivi", "Workspace-i", "Organizacija", "Audit"):
        assert label in workspace
    assert "Entitlement je read-only" in workspace
