from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.platform.security.middleware import SecurityHeadersMiddleware


def test_security_headers_and_request_id():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, environment="development")

    @app.get("/api/v1/auth/example")
    def example():
        return {"ok": True}

    response = TestClient(app).get("/api/v1/auth/example")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]
    assert "strict-transport-security" not in response.headers
