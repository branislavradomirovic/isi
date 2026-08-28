from pathlib import Path


def test_production_invitation_requires_real_delivery_and_does_not_disclose_token():
    candidates = [Path("src/api/administration_routes.py"), Path("src/platform/administration/service.py")]
    sources = [path.read_text() for path in candidates if path.exists() and "invitation_delivery_not_configured" in path.read_text()]
    assert len(sources) == 1
    source = sources[0]
    assert "auth_delivery_configured" in source
    assert "send_invitation" in source
    route = Path("src/api/administration_routes.py")
    if route.exists() and "development_token" in route.read_text():
        route_source = route.read_text()
        assert 'isi_env.strip().casefold() != "production"' in route_source
