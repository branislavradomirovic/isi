from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_routes_require_ordo_scope_and_permissions():
    text = (ROOT / "src/api/ordo_routes.py").read_text()
    assert 'product_code="ORDO"' in text
    assert 'permission_code="indicator.read"' in text
    assert 'permission_code="workspace.manage"' in text
    assert 'permission_code="indicator.manage"' in text
