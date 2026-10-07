from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.api.app import app
from src.api.dependencies import get_db, get_auth_context
from src.core.database import Base
from src.platform.access.models import RoleAssignment, Role
from src.platform.data.storage import LocalFilesystemStorage
from test_isi_29b_spatial_registry import setup_db
from test_isi_29b_geometry_contract import request


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        c = setup_db(db)

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override
    monkeypatch.setattr("src.platform.spatial.service.build_storage", lambda: LocalFilesystemStorage(tmp_path))
    with TestClient(app) as client:
        assert (
            client.get(
                "/api/v1/spatial/SIMPA/geometries",
                params={"organization_id": str(c["org"].id), "workspace_id": str(c["simpa"].id)},
            ).status_code
            == 401
        )
        app.dependency_overrides[get_auth_context] = lambda: SimpleNamespace(user=c["user"])
        yield client, c, factory
    app.dependency_overrides.clear()
    engine.dispose()


def params(c, product="SIMPA"):
    return {"organization_id": str(c["org"].id), "workspace_id": str(c[product.lower()].id)}


def test_api_lifecycle_geometry_metadata_and_no_cross_scope(api):
    client, c, _ = api
    body = request(organization_id=c["org"].id, workspace_id=c["simpa"].id, domain_id=c["local"].id).model_dump(
        mode="json"
    )
    response = client.post("/api/v1/spatial/SIMPA/geometries", json=body)
    assert response.status_code == 201, response.text
    assert client.post("/api/v1/spatial/SIMPA/geometries", json=body).status_code == 409
    row = response.json()
    gid = row["id"]
    revision = row["revision"]
    assert "storage_key" not in row
    url = f"/api/v1/spatial/SIMPA/geometries/{gid}"
    assert client.get(url, params=params(c) | {"at_date": "2026-01-01"}).status_code == 400
    for state in ["PROPOSED", "VALIDATED"]:
        response = client.post(
            url + "/review",
            params=params(c),
            json={"revision": revision, "state": state, "source_license_location_attested": True},
        )
        assert response.status_code == 200, response.text
        revision = response.json()["revision"]
    result = client.get(url, params=params(c) | {"at_date": "2026-01-01"})
    assert result.status_code == 200 and result.json()["geometry"] == body["geometry"]
    assert client.get(url, params=params(c) | {"at_date": "2025-01-01"}).status_code == 400
    assert (
        client.get(url, params=params(c) | {"organization_id": str(uuid4()), "at_date": "2026-01-01"}).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/spatial/ORDO/geometries/{gid}", params=params(c, "ORDO") | {"at_date": "2026-01-01"}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/spatial/ORDO/geometries", params=params(c, "ORDO")).json() == []
    assert client.get("/api/v1/spatial/SIMPA/geometries", params=params(c)).json()[0]["id"] == gid
    assert client.post(url + "/review", params=params(c), json={"revision": 1, "state": "RETIRED"}).status_code == 409


def test_viewer_cannot_register_propose_or_validate(api):
    client, c, factory = api
    with factory() as db:
        grant = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        grant.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    body = request(organization_id=c["org"].id, workspace_id=c["simpa"].id, domain_id=c["local"].id).model_dump(
        mode="json"
    )
    assert client.post("/api/v1/spatial/SIMPA/geometries", json=body).status_code == 403
    for state in ["PROPOSED", "VALIDATED", "RETIRED"]:
        assert (
            client.post(
                f"/api/v1/spatial/SIMPA/geometries/{uuid4()}/review",
                params=params(c),
                json={"revision": 1, "state": state, "source_license_location_attested": True},
            ).status_code
            == 403
        )
    assert client.get("/api/v1/spatial/SIMPA/geometries", params=params(c)).status_code == 200


def test_domain_shape_and_scope_mismatch_rejected(api):
    client, c, _ = api
    body = request(
        organization_id=c["org"].id,
        workspace_id=c["simpa"].id,
        domain_id=c["local"].id,
        geometry={"type": "Point", "coordinates": [0, 0]},
    ).model_dump(mode="json")
    assert client.post("/api/v1/spatial/SIMPA/geometries", json=body).status_code == 400
    body["domain_id"] = str(c["unit"].id)
    assert client.post("/api/v1/spatial/SIMPA/geometries", json=body).status_code == 400
    body["original_crs"] = "unknown"
    assert client.post("/api/v1/spatial/SIMPA/geometries", json=body).status_code == 422


def test_spatial_guide_has_ten_item_help_and_explicit_limits():
    from pathlib import Path
    from src.platform.spatial.contracts import MAX_BYTES, MAX_COORDINATES

    guide = Path("docs/help/ISI-SPATIAL-DATA-GUIDE.md").read_text()
    for index in range(1, 11):
        assert f"## {index}. " in guide
    for token in [
        "data.upload",
        "data.read",
        "data.validate",
        "data.governance.manage",
        "HUMAN_ATTESTED",
        "declared_source_sha256",
        "29C",
        str(MAX_BYTES),
        str(MAX_COORDINATES),
    ]:
        assert token in guide
