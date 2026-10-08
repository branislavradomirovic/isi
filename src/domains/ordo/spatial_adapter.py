"""ORDO boundary/asset identity authority; preserves legacy identity-only rows."""

from sqlalchemy import select
from src.domains.ordo.models import OrdoAsset, OrdoSpatialUnit
from src.platform.spatial.contracts import GeometryError


def binding(session, *, organization_id, workspace_id, domain_kind, domain_id, geometry_type, valid_from, valid_to):
    models = {"spatial_unit": OrdoSpatialUnit, "asset": OrdoAsset}
    model = models.get(domain_kind)
    if (
        model is None
        or (domain_kind == "spatial_unit" and geometry_type == "Point")
        or (domain_kind == "asset" and geometry_type != "Point")
    ):
        raise GeometryError("ordo_geometry_domain_invalid")
    row = session.scalar(
        select(model).where(
            model.id == domain_id, model.organization_id == organization_id, model.workspace_id == workspace_id
        )
    )
    if row is None:
        raise GeometryError("geometry_domain_not_accessible")
    if domain_kind == "spatial_unit":
        if row.lifecycle_status != "validated" or not row.boundary_source or not row.boundary_version:
            raise GeometryError("geometry_domain_not_validated")
        if (row.valid_from is not None and valid_from < row.valid_from) or (
            row.valid_to is not None and (valid_to is None or valid_to > row.valid_to)
        ):
            raise GeometryError("geometry_domain_validity_mismatch")
        return {
            "kind": domain_kind,
            "id": str(row.id),
            "key": row.spatial_unit_key,
            "boundary_version": row.boundary_version,
            "boundary_source": row.boundary_source,
        }
    if not row.external_code:
        raise GeometryError("geometry_domain_code_required")
    return {"kind": domain_kind, "id": str(row.id), "key": row.external_code}


def targets(session, *, organization_id, workspace_id):
    result = []
    for kind, model in [("spatial_unit", OrdoSpatialUnit), ("asset", OrdoAsset)]:
        rows = session.scalars(
            select(model).where(model.organization_id == organization_id, model.workspace_id == workspace_id).limit(101)
        ).all()
        for row in rows:
            if kind == "spatial_unit" and row.lifecycle_status != "validated":
                continue
            code = row.spatial_unit_key if kind == "spatial_unit" else row.external_code
            if code:
                result.append(
                    {
                        "id": str(row.id),
                        "kind": kind,
                        "key": code,
                        "name": row.name,
                        "source_uri": row.boundary_source if kind == "spatial_unit" else None,
                        "source_version": row.boundary_version if kind == "spatial_unit" else None,
                    }
                )
    return result


def linked_results(session, *, organization_id, workspace_id, geometry_row):
    """Revalidate stored identity-only aggregations; never assign a synthetic period."""
    import math
    from src.domains.ordo.analytics_models import OrdoAnalyticsRun, OrdoSpatialAggregationRun, OrdoIndicatorMethodology
    from src.domains.ordo.analytics_service import (
        revalidate_analytics_run,
        _methodology_fingerprint,
        OrdoAnalyticsError,
    )
    from src.domains.ordo.spatial_processing import (
        canonical_sha256,
        aggregate_numeric_values,
        OrdoSpatialAggregationContractV1,
    )
    from src.domains.ordo.models import OrdoIndicatorDefinition

    if geometry_row.domain_kind != "spatial_unit":
        return {"status": "UNAVAILABLE", "reason": "asset_has_no_approved_result_binding", "results": []}
    if (geometry_row.organization_id, geometry_row.workspace_id, geometry_row.product_code) != (
        organization_id,
        workspace_id,
        "ORDO",
    ):
        raise GeometryError("linked_result_scope_not_accessible")
    unit = session.scalar(
        select(OrdoSpatialUnit).where(
            OrdoSpatialUnit.id == geometry_row.domain_id,
            OrdoSpatialUnit.organization_id == organization_id,
            OrdoSpatialUnit.workspace_id == workspace_id,
        )
    )
    if unit is None or unit.lifecycle_status != "validated":
        raise GeometryError("linked_result_unit_not_validated")
    rows = session.scalars(
        select(OrdoSpatialAggregationRun)
        .where(
            OrdoSpatialAggregationRun.organization_id == organization_id,
            OrdoSpatialAggregationRun.workspace_id == workspace_id,
            OrdoSpatialAggregationRun.target_spatial_unit_id == unit.id,
        )
        .order_by(OrdoSpatialAggregationRun.created_at.desc(), OrdoSpatialAggregationRun.id)
        .limit(11)
    ).all()
    results, unavailable = [], 0
    for row in rows[:10]:
        try:
            run = session.scalar(
                select(OrdoAnalyticsRun).where(
                    OrdoAnalyticsRun.id == row.analytics_run_id,
                    OrdoAnalyticsRun.organization_id == organization_id,
                    OrdoAnalyticsRun.workspace_id == workspace_id,
                )
            )
            method = session.get(OrdoIndicatorMethodology, row.methodology_id)
            indicator = session.get(OrdoIndicatorDefinition, row.indicator_id)
            if (
                not run
                or not method
                or not indicator
                or not indicator.active
                or method.status != "validated"
                or method.indicator_id != indicator.id
                or method.version_no != row.methodology_version
                or _methodology_fingerprint(method) != row.methodology_fingerprint
                or unit.boundary_version != row.boundary_version
                or unit.crs != row.crs
                or unit.spatial_unit_type != row.spatial_unit_type
            ):
                raise GeometryError("linked_result_binding_changed")
            contract = OrdoSpatialAggregationContractV1.model_validate(
                (method.source_requirements or {}).get("spatial_aggregation")
            )
            if contract.aggregation_rule != row.aggregation_rule or row.unit != indicator.unit_hint:
                raise GeometryError("linked_result_methodology_changed")
            data = revalidate_analytics_run(
                session, run=run, organization_id=organization_id, workspace_id=workspace_id
            )
            records = [r for r in data.records if r.payload.get("indicator_code") == indicator.code]
            if not records:
                raise GeometryError("linked_result_missing_records")
            normalized = []
            identity = {
                "spatial_unit_key": unit.spatial_unit_key,
                "spatial_unit_type": unit.spatial_unit_type,
                "boundary_version": unit.boundary_version,
                "crs": unit.crs,
            }
            values = []
            for record in records:
                if record.payload.get("quality_status") != "validated" or any(
                    record.payload.get(k) != v for k, v in identity.items()
                ):
                    raise GeometryError("linked_result_source_identity_changed")
                values.append(record.payload.get("value_numeric"))
                normalized.append(
                    {
                        "identity_fingerprint": record.identity_fingerprint,
                        "content_fingerprint": record.content_fingerprint,
                        **identity,
                        "value_numeric": record.payload.get("value_numeric"),
                    }
                )
            normalized.sort(key=lambda x: (x["identity_fingerprint"], x["content_fingerprint"]))
            calc = aggregate_numeric_values(values, row.aggregation_rule)
            trace = {
                "schema_version": row.schema_version,
                "aggregation_rule": row.aggregation_rule,
                "methodology_id": str(method.id),
                "methodology_version": method.version_no,
                "methodology_fingerprint": row.methodology_fingerprint,
                "target_spatial_unit_id": str(unit.id),
                "target_identity": identity,
                "input_snapshot_sha256": canonical_sha256(normalized),
                **calc.model_dump(exclude={"aggregation_rule"}),
                "weighted": False,
                "spatial_join_performed": False,
                "forecast_performed": False,
                "causal_claim": False,
                "automatic_policy_recommendation": False,
            }
            if (
                trace != row.computation_trace
                or canonical_sha256(trace) != row.run_fingerprint
                or trace["input_snapshot_sha256"] != row.input_snapshot_sha256
                or any(getattr(row, k) != v for k, v in calc.model_dump().items())
                or any(
                    getattr(row, k)
                    for k in (
                        "weighted",
                        "spatial_join_performed",
                        "forecast_performed",
                        "causal_claim",
                        "automatic_policy_recommendation",
                    )
                )
                or not math.isfinite(row.aggregate_numeric_value)
            ):
                raise GeometryError("linked_result_integrity_failed")
            results.append(
                {
                    "id": str(row.id),
                    "indicator": indicator.code,
                    "rule": row.aggregation_rule,
                    "value": row.aggregate_numeric_value,
                    "unit": row.unit,
                    "matched": row.matched_record_count,
                    "missing": row.dropped_missing_numeric_count,
                    "unmatched": row.input_record_count - row.matched_record_count - row.dropped_missing_numeric_count,
                    "fingerprint": row.run_fingerprint,
                    "methodology_version": row.methodology_version,
                    "period": "NOT_ASSIGNED",
                    "boundary_version": row.boundary_version,
                }
            )
        except (ValueError, TypeError, KeyError, OrdoAnalyticsError):
            unavailable += 1
    return {
        "status": "AVAILABLE" if results else "UNAVAILABLE",
        "results": results,
        "ineligible_count": unavailable,
        "truncated": len(rows) > 10,
        "limit": 10,
        "reason": "identity_only_no_observation_period_contract",
    }
