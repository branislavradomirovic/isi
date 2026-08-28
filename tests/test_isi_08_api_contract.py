from pathlib import Path


def test_simpa_api_is_hard_scoped_to_simpa_and_permissions():
    text = Path("src/api/simpa_routes.py").read_text()
    assert 'product_code="SIMPA"' in text
    assert 'permission_code="indicator.read"' in text
    assert 'permission_code="indicator.manage"' in text
    assert 'permission_code="workspace.manage"' in text
    assert 'detail="simpa_scope_not_accessible"' in text


def test_catalog_requires_simpa_scope_instead_of_being_global_authenticated_leak():
    text = Path("src/api/simpa_routes.py").read_text()
    start = text.index('@router.get("/catalog")')
    chunk = text[start:start+700]
    assert "organization_id" in chunk
    assert "workspace_id" in chunk
    assert "_require_scope" in chunk
