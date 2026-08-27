from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_health_endpoint_contract():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "isi-api",
        "phase": "foundation",
    }


def test_public_home_is_jinja_and_names_both_domains():
    response = client.get("/")
    assert response.status_code == 200
    text = response.text
    assert "Institut za socijalnu inkluziju" in text
    assert "SIMPA" in text
    assert "ORDO" in text
