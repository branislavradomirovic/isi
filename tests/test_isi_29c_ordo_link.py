from types import SimpleNamespace
import pytest
from src.domains.ordo.spatial_adapter import linked_results
from src.domains.ordo.analytics_models import OrdoAnalyticsRun, OrdoSpatialAggregationRun, OrdoIndicatorMethodology
from src.domains.ordo.models import OrdoIndicatorDefinition, OrdoDimension, OrdoPillar
from src.domains.ordo.analytics_service import _methodology_fingerprint, OrdoAnalyticsError
from src.domains.ordo.spatial_processing import canonical_sha256, OrdoSpatialAggregationContractV1
from test_isi_29b_spatial_registry import create, args
from test_isi_29b_spatial_registry import context as spatial_context_fixture

from src.platform.spatial.service import review_geometry
from src.platform.spatial.contracts import GeometryReview

context = spatial_context_fixture


def setup(c, monkeypatch):
    db = c["db"]
    unit = c["unit"]
    unit.crs = "OGC:CRS84"
    geometry = create(c, "ORDO")
    for state in ["PROPOSED", "VALIDATED"]:
        review_geometry(
            db,
            **args(c, "ORDO"),
            geometry_id=geometry.id,
            payload=GeometryReview(state=state, revision=geometry.revision, source_license_location_attested=True),
            storage=c["storage"],
        )
    pillar = OrdoPillar(code="synthetic", name_sr="Synthetic", sort_order=1)
    dimension = OrdoDimension(code="synthetic", name_sr="Synthetic", sort_order=1)
    db.add_all([pillar, dimension])
    db.flush()
    indicator = OrdoIndicatorDefinition(
        code="SYNTHETIC-COUNT",
        name_sr="Synthetic",
        dimension_code="synthetic",
        pillar_code="synthetic",
        unit_hint="units",
    )
    db.add(indicator)
    db.flush()
    method = OrdoIndicatorMethodology(
        indicator_id=indicator.id,
        version_no=1,
        status="validated",
        computation_type="direct_observation",
        source_requirements={
            "spatial_aggregation": OrdoSpatialAggregationContractV1(aggregation_rule="sum").model_dump(mode="json")
        },
        computation_spec={},
        methodology_note="Synthetic",
    )
    run = OrdoAnalyticsRun(organization_id=c["org"].id, workspace_id=c["ordo"].id, status="completed", snapshot={})
    db.add_all([method, run])
    db.flush()
    identity = {
        "spatial_unit_key": unit.spatial_unit_key,
        "spatial_unit_type": unit.spatial_unit_type,
        "boundary_version": unit.boundary_version,
        "crs": unit.crs,
    }
    normalized = [{"identity_fingerprint": "a" * 64, "content_fingerprint": "b" * 64, **identity, "value_numeric": 0}]
    trace = {
        "schema_version": "ORDO-SPATIAL-AGGREGATION-v1",
        "aggregation_rule": "sum",
        "methodology_id": str(method.id),
        "methodology_version": 1,
        "methodology_fingerprint": _methodology_fingerprint(method),
        "target_spatial_unit_id": str(unit.id),
        "target_identity": identity,
        "input_snapshot_sha256": canonical_sha256(normalized),
        "input_record_count": 1,
        "matched_record_count": 1,
        "dropped_missing_numeric_count": 0,
        "aggregate_numeric_value": 0.0,
        "weighted": False,
        "spatial_join_performed": False,
        "forecast_performed": False,
        "causal_claim": False,
        "automatic_policy_recommendation": False,
    }
    row = OrdoSpatialAggregationRun(
        organization_id=c["org"].id,
        workspace_id=c["ordo"].id,
        analytics_run_id=run.id,
        indicator_id=indicator.id,
        methodology_id=method.id,
        methodology_version=1,
        methodology_fingerprint=trace["methodology_fingerprint"],
        target_spatial_unit_id=unit.id,
        schema_version=trace["schema_version"],
        aggregation_rule="sum",
        boundary_version=unit.boundary_version,
        crs=unit.crs,
        spatial_unit_type=unit.spatial_unit_type,
        input_snapshot_sha256=trace["input_snapshot_sha256"],
        input_record_count=1,
        matched_record_count=1,
        dropped_missing_numeric_count=0,
        aggregate_numeric_value=0,
        unit="units",
        computation_trace=trace,
        run_fingerprint=canonical_sha256(trace),
    )
    db.add(row)
    db.commit()
    source = SimpleNamespace(
        records=[
            SimpleNamespace(
                identity_fingerprint="a" * 64,
                content_fingerprint="b" * 64,
                payload={
                    **identity,
                    "value_numeric": 0,
                    "indicator_code": indicator.code,
                    "quality_status": "validated",
                },
            )
        ]
    )
    monkeypatch.setattr("src.domains.ordo.analytics_service.revalidate_analytics_run", lambda *a, **k: source)
    return geometry, row, method, unit, source


def call(c, geometry):
    return linked_results(c["db"], organization_id=c["org"].id, workspace_id=c["ordo"].id, geometry_row=geometry)


def test_exact_zero_parity_no_invented_period_or_source_payload(context, monkeypatch):
    geometry, row, _, _, _ = setup(context, monkeypatch)
    result = call(context, geometry)
    assert result["status"] == "AVAILABLE" and result["results"][0]["value"] == 0
    assert result["results"][0]["period"] == "NOT_ASSIGNED"
    assert result["results"][0]["fingerprint"] == row.run_fingerprint
    assert not context["db"].new and not context["db"].dirty


@pytest.mark.parametrize(
    "change", ["value", "method", "boundary", "source_identity", "source_invalidation", "trace", "foreign_scope"]
)
def test_invalidated_or_tampered_result_not_exposed(context, monkeypatch, change):
    geometry, row, method, unit, source = setup(context, monkeypatch)
    if change == "value":
        row.aggregate_numeric_value = 1
    if change == "method":
        method.status = "retired"
    if change == "boundary":
        unit.boundary_version = "v2"
    if change == "source_identity":
        source.records[0].payload["spatial_unit_key"] = "OTHER"
    if change == "source_invalidation":

        def invalid(*a, **k):
            raise OrdoAnalyticsError("analytical_source_invalidated")

        monkeypatch.setattr("src.domains.ordo.analytics_service.revalidate_analytics_run", invalid)
    if change == "trace":
        row.computation_trace = {}
    if change == "foreign_scope":
        row.workspace_id = context["simpa"].id
    result = call(context, geometry)
    assert result["results"] == []


def test_asset_no_fake_aggregation(context, monkeypatch):
    geometry = create(context, "ORDO", kind="asset")
    assert call(context, geometry)["status"] == "UNAVAILABLE"
