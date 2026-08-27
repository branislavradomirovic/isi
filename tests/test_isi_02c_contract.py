from pathlib import Path


def test_app_context_contract_files_and_routes_are_present():
    assert Path("src/platform/app_context/service.py").exists()
    assert Path("src/platform/app_context/schemas.py").exists()
    app_source = Path("src/api/app.py").read_text()
    assert "app_context_router" in app_source
    assert "app.include_router(app_context_router)" in app_source
    streamlit_source = Path("src/streamlit_app/app.py").read_text()
    assert "/api/v1/auth/login" in streamlit_source
    assert "/api/v1/app-context" in streamlit_source
    assert "SIMPA Workspace" in streamlit_source
    assert "ORDO Workspace" in streamlit_source
    assert "st.session_state" in streamlit_source
