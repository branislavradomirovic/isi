from uuid import uuid4
from sqlalchemy import select
from src.platform.access.models import RoleAssignment, Role
from test_isi_29b_spatial_api import api as spatial_api_fixture, params
from test_isi_29b_geometry_contract import request

api = spatial_api_fixture


def validated(client, c):
    body = request(organization_id=c["org"].id, workspace_id=c["simpa"].id, domain_id=c["local"].id).model_dump(
        mode="json"
    )
    row = client.post("/api/v1/spatial/SIMPA/geometries", json=body).json()
    url = "/api/v1/spatial/SIMPA/geometries/" + row["id"]
    for state in ["PROPOSED", "VALIDATED"]:
        row = client.post(
            url + "/review",
            params=params(c),
            json={"state": state, "revision": row["revision"], "source_license_location_attested": True},
        ).json()
    return url, row


def test_scoped_targets_are_product_specific(api):
    client, c, _ = api
    simpa = client.get("/api/v1/spatial/SIMPA/targets", params=params(c)).json()
    ordo = client.get("/api/v1/spatial/ORDO/targets", params=params(c, "ORDO")).json()
    assert {x["kind"] for x in simpa} == {"local_system", "local_actor"}
    assert {x["kind"] for x in ordo} == {"spatial_unit", "asset"}
    assert not {x["id"] for x in simpa} & {x["id"] for x in ordo}
    assert (
        client.get("/api/v1/spatial/SIMPA/targets", params=params(c) | {"workspace_id": str(c["ordo"].id)}).status_code
        == 403
    )


def test_export_is_exact_and_revalidates_state_date_scope(api):
    client, c, factory = api
    url, row = validated(client, c)
    p = params(c) | {"at_date": "2026-01-01"}
    exported = client.get(url + "/export", params=p)
    assert exported.status_code == 200
    from src.platform.data.models import DataAuditEvent

    with factory() as db:
        event = db.scalar(select(DataAuditEvent).where(DataAuditEvent.event_type == "spatial.geometry.exported"))
        assert event.actor_membership_id == c["member"].id
        assert "coordinates" not in event.detail
    feature = exported.json()["features"][0]
    assert feature["id"] == row["id"] and feature["properties"]["fingerprint"] == row["fingerprint"]
    assert "storage_key" not in exported.text and exported.json()["observation_period"] == "NOT_ASSIGNED"
    assert client.get(url + "/export", params=p | {"at_date": "2025-01-01"}).status_code == 400
    assert client.get(url + "/export", params=p | {"organization_id": str(uuid4())}).status_code == 403
    client.post(url + "/review", params=params(c), json={"state": "RETIRED", "revision": row["revision"]})
    assert client.get(url + "/export", params=p).status_code == 400


def test_viewer_export_and_result_permission_backend(api):
    client, c, factory = api
    url, _ = validated(client, c)
    with factory() as db:
        assignment = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        assignment.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    p = params(c) | {"at_date": "2026-01-01"}
    assert client.get(url, params=p).status_code == 200
    assert client.get(url + "/export", params=p).status_code == 403
    # Viewer may read analytics, but no SIMPA model geography is invented.
    response = client.get(url + "/results", params=p)
    assert response.status_code == 200 and response.json()["results"] == []
    assert "not_approved" in response.json()["reason"]


def test_ordo_unit_create_review_selector_lifecycle(api):
    client, c, _ = api
    p = params(c, "ORDO")
    body = dict(
        p,
        spatial_unit_key="ANOTHER",
        spatial_unit_type="custom",
        name="Synthetic unit",
        boundary_source="https://example.org/unit",
        boundary_version="v1",
        geometry_id="source-id",
        crs="OGC:CRS84",
        artifact_sha256="a" * 64,
        valid_from="2026-01-01",
    )
    response = client.post("/api/v1/spatial/ORDO/units", json=body)
    assert response.status_code == 201, response.text
    row = response.json()
    assert row["lifecycle_status"] == "draft"
    url = f"/api/v1/spatial/ORDO/units/{row['id']}/review"
    assert client.post(url, params=p, json={"state": "validated", "note": "Synthetic review"}).status_code == 400
    for state in ["proposed", "validated", "retired"]:
        result = client.post(url, params=p, json={"state": state, "note": "Synthetic review"})
        assert result.status_code == 200, result.text
    assert client.post(url, params=p, json={"state": "validated", "note": "Synthetic review"}).status_code == 400
    assert all(x["id"] != row["id"] for x in client.get("/api/v1/spatial/ORDO/targets", params=p).json())
    assert any(x["id"] == row["id"] for x in client.get("/api/v1/spatial/ORDO/units", params=p).json()["items"])
    assert (
        client.post(
            "/api/v1/spatial/ORDO/units", json=body | {"boundary_source": "https://example.org/?token=x"}
        ).status_code
        == 422
    )


def test_unit_governance_denied_for_viewer(api):
    client, c, factory = api
    with factory() as db:
        assignment = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        assignment.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    p = params(c, "ORDO")
    assert client.get("/api/v1/spatial/ORDO/units", params=p).status_code == 200
    assert (
        client.post(
            f"/api/v1/spatial/ORDO/units/{c['unit'].id}/review",
            params=p,
            json={"state": "retired", "note": "No privilege"},
        ).status_code
        == 403
    )


def test_data_manager_cannot_read_analytics_before_storage_access(api, monkeypatch):
    client, c, factory = api
    url, _ = validated(client, c)
    with factory() as db:
        grant = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        grant.role_id = db.scalar(select(Role.id).where(Role.code == "data_manager"))
        db.commit()
    p = params(c) | {"at_date": "2026-01-01"}
    assert client.get(url, params=p).status_code == 200

    def forbidden(*a, **k):
        raise AssertionError("storage must not be accessed without analysis.read")

    monkeypatch.setattr("src.api.spatial_routes.get_geometry", forbidden)
    assert client.get(url + "/results", params=p).status_code == 403
