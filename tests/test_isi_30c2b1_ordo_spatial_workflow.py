from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from streamlit.testing.v1 import AppTest

from src.domains.ordo.analytics_schemas import SpatialAggregationRequest
from src.domains.ordo.analytics_models import OrdoIndicatorMethodology, OrdoAnalyticsRun, OrdoSpatialAggregationRun
from src.domains.ordo.models import OrdoIndicatorDefinition
from src.domains.ordo import analytics_service as service
from src.domains.ordo.spatial_processing import OrdoSpatialAggregationContractV1
from src.platform.access.models import RoleAssignment, Role
from src.streamlit_app import ordo_spatial_analytics_api as api, ordo_spatial_analytics_workspace as ui
from test_isi_29b_spatial_api import api as fixture, params

server = fixture
IDS = [str(UUID(int=i)) for i in range(1, 8)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1])
METHOD = dict(
    id=IDS[2],
    indicator_code="synthetic",
    version_no=1,
    status="validated",
    source_requirements={
        "spatial_aggregation": OrdoSpatialAggregationContractV1(aggregation_rule="mean").model_dump(mode="json")
    },
)
RUN = dict(id=IDS[3], status="completed", analytical_artifact_type="ANALYTICAL_SNAPSHOT")
UNIT = dict(
    id=IDS[4],
    lifecycle_status="validated",
    spatial_unit_key="SYNTHETIC",
    spatial_unit_type="custom",
    boundary_version="v1",
    crs="OGC:CRS84",
)
REGISTRY = dict(methods=[METHOD], runs=[RUN], units=[UNIT])


def body(c, method):
    return dict(
        params(c, "ORDO"),
        reviewed_methodology_id=str(method.id),
        analytics_run_id=IDS[3],
        indicator_code="synthetic",
        target_spatial_unit_id=str(c["unit"].id),
    )


def seed(factory, c):
    with factory() as db:
        indicator = OrdoIndicatorDefinition(
            code="synthetic", name_sr="Synthetic", dimension_code="synthetic", pillar_code="synthetic"
        )
        db.add(indicator)
        db.flush()
        method = OrdoIndicatorMethodology(
            indicator_id=indicator.id,
            version_no=1,
            status="validated",
            source_requirements=METHOD["source_requirements"],
        )
        run = OrdoAnalyticsRun(
            id=UUID(IDS[3]),
            organization_id=c["org"].id,
            workspace_id=c["ordo"].id,
            analytical_artifact_type="ANALYTICAL_SNAPSHOT",
            analytical_snapshot_id=uuid4(),
            analytical_artifact_fingerprint="a" * 64,
            dataset_contract_version_id=uuid4(),
            dataset_contract_fingerprint="b" * 64,
            analytical_quality_state="ACCEPTED_CLEAN",
        )
        db.add_all([method, run])
        db.commit()
        return method


def governed(c, **changes):
    payload = dict(
        indicator_code="synthetic",
        quality_status="validated",
        spatial_unit_key=c["unit"].spatial_unit_key,
        spatial_unit_type=c["unit"].spatial_unit_type,
        boundary_version=c["unit"].boundary_version,
        crs=c["unit"].crs,
        value_numeric=4.0,
    )
    payload.update(changes)
    fields = tuple(
        dict(field_key=k, logical_type="NUMBER" if k == "value_numeric" else "STRING", required=True) for k in payload
    )
    return SimpleNamespace(
        field_contract=fields,
        records=[SimpleNamespace(payload=payload, identity_fingerprint="c" * 64, content_fingerprint="d" * 64)],
    )


def test_real_service_creation_persistence_actor_and_duplicate(server, monkeypatch):
    client, c, factory = server
    method = seed(factory, c)
    checker = Mock(return_value=governed(c))
    monkeypatch.setattr(service, "revalidate_analytics_run", checker)
    response = client.post("/api/v1/ordo/analytics/spatial-aggregations", json=body(c, method))
    assert response.status_code == 201, response.text
    assert response.json()["current_results"] == "GIS_REVALIDATION_REQUIRED"
    assert "aggregate_numeric_value" not in response.json()
    with factory() as db:
        row = db.get(OrdoSpatialAggregationRun, UUID(response.json()["id"]))
        assert row.aggregate_numeric_value == 4 and row.created_by_membership_id == c["member"].id
        assert row.methodology_id == method.id and not row.spatial_join_performed and not row.forecast_performed
    assert checker.call_count == 1
    assert client.post("/api/v1/ordo/analytics/spatial-aggregations", json=body(c, method)).status_code == 409


@pytest.mark.parametrize(
    "change",
    [{"quality_status": "draft"}, {"boundary_version": "v2"}, {"crs": "other"}, {"value_numeric": float("inf")}],
)
def test_real_service_fail_closed_and_no_persistence(server, monkeypatch, change):
    client, c, factory = server
    method = seed(factory, c)
    monkeypatch.setattr(service, "revalidate_analytics_run", lambda *a, **kw: governed(c, **change))
    response = client.post("/api/v1/ordo/analytics/spatial-aggregations", json=body(c, method))
    assert response.status_code == 400, response.text
    with factory() as db:
        assert db.scalar(select(OrdoSpatialAggregationRun)) is None


def test_stale_method_and_cross_product_scope_denied_before_execution(server, monkeypatch):
    client, c, factory = server
    method = seed(factory, c)
    checker = Mock(side_effect=AssertionError("must not access governed input"))
    monkeypatch.setattr(service, "revalidate_analytics_run", checker)
    b = body(c, method)
    assert (
        client.post(
            "/api/v1/ordo/analytics/spatial-aggregations", json=b | {"reviewed_methodology_id": str(uuid4())}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/ordo/analytics/spatial-aggregations", json=b | {"workspace_id": str(c["simpa"].id)}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/ordo/analytics/spatial-aggregations", json=b | {"organization_id": str(uuid4())}
        ).status_code
        == 403
    )
    with factory() as db:
        grant = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        grant.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    assert client.post("/api/v1/ordo/analytics/spatial-aggregations", json=b).status_code == 403
    checker.assert_not_called()


@pytest.mark.parametrize(
    "field", ["aggregation_rule", "methodology_version", "boundary_version", "weighted", "aggregate_numeric_value"]
)
def test_request_rejects_customer_authority(field):
    b = dict(
        SCOPE,
        analytics_run_id=IDS[3],
        reviewed_methodology_id=IDS[2],
        indicator_code="synthetic",
        target_spatial_unit_id=IDS[4],
    )
    with pytest.raises(ValidationError):
        SpatialAggregationRequest.model_validate(b | {field: True})


def test_typed_transport(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=201, json=lambda: {"id": IDS[5]}))
    monkeypatch.setattr(api, "request", req)
    api.create(
        "synthetic",
        scope=SCOPE,
        analytics_run_id=IDS[3],
        reviewed_methodology_id=IDS[2],
        indicator_code="synthetic",
        target_spatial_unit_id=IDS[4],
    )
    assert req.call_args.kwargs["json"]["workspace_id"] == IDS[1]
    with pytest.raises(ValidationError):
        api.create(
            "synthetic",
            scope=SCOPE,
            analytics_run_id="bad",
            reviewed_methodology_id=IDS[2],
            indicator_code="synthetic",
            target_spatial_unit_id=IDS[4],
        )
    assert req.call_count == 1


@pytest.mark.parametrize(
    "group,change",
    [
        ("methods", {"status": "draft"}),
        ("methods", {"source_requirements": {}}),
        ("runs", {"status": "failed"}),
        ("runs", {"analytical_artifact_type": "LEGACY_OBSERVATION"}),
        ("units", {"lifecycle_status": "retired"}),
    ],
)
def test_eligible_fail_closed(group, change):
    registry = {k: [x.copy() for x in v] for k, v in REGISTRY.items()}
    registry[group][0].update(change)
    assert not all(ui.eligible(registry))


def app():
    import streamlit as st
    from tests.test_isi_30c2b1_ordo_spatial_workflow import IDS
    from src.streamlit_app.ordo_spatial_analytics_workspace import render_ordo_spatial_aggregation

    shell = dict(
        organization={"id": st.session_state["org"]},
        workspace={"id": IDS[1]},
        product=dict(code=st.session_state["product"], permission_codes=st.session_state["permissions"]),
    )
    render_ordo_spatial_aggregation(token="synthetic", shell=shell)


def mounted(monkeypatch):
    monkeypatch.setattr(ui.read_api, "methodologies", lambda *a, **kw: [METHOD.copy()])
    monkeypatch.setattr(ui.read_api, "runs", lambda *a, **kw: [RUN.copy()])
    monkeypatch.setattr(ui.spatial_api, "call", lambda *a, **kw: dict(items=[UNIT.copy()], truncated=False))
    write = Mock(return_value={"id": IDS[5]})
    monkeypatch.setattr(ui.api, "create", write)
    at = AppTest.from_function(app)
    at.session_state["org"] = IDS[0]
    at.session_state["product"] = "ORDO"
    at.session_state["permissions"] = ["analysis.read", "data.read", "analysis.run"]
    at.run()
    return at, write


def test_ui_explicit_choices_confirmation_success_reset(monkeypatch):
    at, write = mounted(monkeypatch)
    assert not at.exception
    at.button[0].click().run()
    assert len(at.selectbox) == 3 and all(x.value is None for x in at.selectbox)
    for selector in at.selectbox:
        selector.select_index(0)
    at.run()
    assert at.button[-1].disabled
    at.checkbox[0].check().run()
    at.button[-1].click().run()
    assert not at.exception and write.call_count == 1 and len(at.selectbox) == 0 and len(at.checkbox) == 0
    assert at.success


def test_ui_refresh_and_scope_change_clear_approval(monkeypatch):
    at, write = mounted(monkeypatch)
    at.button[0].click().run()
    for selector in at.selectbox:
        selector.select_index(0)
    at.run()
    at.checkbox[0].check().run()
    at.button[0].click().run()
    assert all(x.value is None for x in at.selectbox) and not at.checkbox
    at.session_state["org"] = IDS[6]
    at.run()
    assert not at.selectbox and not at.checkbox
    write.assert_not_called()


@pytest.mark.parametrize(
    "product,permissions",
    [("SIMPA", ["analysis.read", "data.read", "analysis.run"]), ("ORDO", ["analysis.read", "data.read"])],
)
def test_ui_no_mutation_for_other_product_or_readonly(monkeypatch, product, permissions):
    at, write = mounted(monkeypatch)
    at.session_state["product"] = product
    at.session_state["permissions"] = permissions
    at.run()
    assert not at.button and not at.checkbox and not at.exception
    write.assert_not_called()
