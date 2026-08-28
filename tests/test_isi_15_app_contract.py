from src.api.app import app


def test_deployment_readiness_route_is_registered():
    paths = set(app.openapi().get("paths", {}))
    assert "/api/v1/readiness" in paths
