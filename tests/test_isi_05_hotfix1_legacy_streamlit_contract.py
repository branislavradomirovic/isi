from pathlib import Path


def test_legacy_streamlit_contract_markers_are_preserved_without_reembedding_http_calls():
    app = Path("src/streamlit_app/app.py").read_text()
    api_client = Path("src/streamlit_app/api_client.py").read_text()

    assert 'LEGACY_AUTH_LOGIN_ROUTE = "/api/v1/auth/login"' in app
    assert 'LEGACY_APP_CONTEXT_ROUTE = "/api/v1/app-context"' in app
    assert 'LEGACY_SIMPA_WORKSPACE_LABEL = "SIMPA Workspace"' in app
    assert 'LEGACY_ORDO_WORKSPACE_LABEL = "ORDO Workspace"' in app

    # Networking remains centralized in the API client.
    assert 'request("POST", "/api/v1/auth/login"' in api_client
    assert 'request("GET", "/api/v1/app-context"' in api_client
    assert "httpx.request" not in app
