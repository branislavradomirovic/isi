from pathlib import Path


def test_data_router_is_registered_and_permission_scoped():
    app = Path("src/api/app.py").read_text()
    routes = Path("src/api/data_routes.py").read_text()
    assert "data_router" in app
    assert "app.include_router(data_router)" in app
    assert 'prefix="/api/v1/data"' in routes
    assert 'permission_code="data.read"' in routes
    assert 'permission_code="data.upload"' in routes
    assert 'permission_code="data.validate"' in routes
    assert "resolve_selection" in routes
    assert "has_permission" in routes


def test_streamlit_data_navigation_is_real_module():
    app = Path("src/streamlit_app/app.py").read_text()
    assert "render_data_workspace" in app
    assert 'nav_code == "data"' in app
    workspace = Path("src/streamlit_app/data_workspace.py").read_text()
    assert "file_uploader" in workspace
    assert "list_data_sources" in workspace
    assert "create_data_source" in workspace
