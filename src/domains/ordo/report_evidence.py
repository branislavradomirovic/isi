"""ORDO forecast identity and provenance for linked evidence reports."""
from src.domains.ordo import analytics_service as a
from src.domains.ordo.analytics_xai import build_forecast_xai


def result_evidence(db, *, result_id, organization_id, workspace_id):
    row = a.get_forecast_run(db, forecast_run_id=result_id, organization_id=organization_id, workspace_id=workspace_id)
    specrow, spec, run, governed = a._forecast_binding(
        db, organization_id=organization_id, workspace_id=workspace_id, time_series_spec_id=row.time_series_spec_id)
    if (row.analytics_run_id, row.time_series_spec_version, row.time_series_spec_fingerprint,
        row.target_indicator_id, row.target_methodology_id, row.target_methodology_version,
        row.methodology_fingerprint, row.input_snapshot_sha256) != (
        run.id, specrow.version_no, specrow.contract_fingerprint, specrow.target_indicator_id,
        specrow.target_methodology_id, specrow.target_methodology_version,
        specrow.methodology_fingerprint, specrow.input_snapshot_sha256):
        raise a.OrdoAnalyticsError("linked_forecast_binding_changed")
    if not row.non_causal or row.automatic_model_selection or row.automatic_policy_recommendation:
        raise a.OrdoAnalyticsError("linked_forecast_semantics_changed")
    if (row.horizon != spec.horizon or row.rolling_origin_plan != spec.temporal_validation.model_dump(mode="json")
            or row.observation_window != {"start": spec.observation_window_start.isoformat(),
                                          "end": spec.observation_window_end.isoformat(),
                                          "as_of": spec.observation_as_of.isoformat()}):
        raise a.OrdoAnalyticsError("linked_forecast_window_changed")
    request = {
        "organization_id": str(organization_id), "workspace_id": str(workspace_id),
        "time_series_spec_id": str(specrow.id), "time_series_spec_fingerprint": specrow.contract_fingerprint,
        "requested_family": row.requested_family, "series_identity": row.series_identity,
        "interval_level": row.interval_level,
    }
    if a._canonical_sha256(request) != row.request_fingerprint:
        raise a.OrdoAnalyticsError("linked_forecast_request_changed")
    fields = ("executed_family", "backtest_records", "aggregate_backtest_metrics", "metric_availability",
              "diagnostics", "warnings", "forecast_points")
    data = {name: getattr(row, name) for name in fields}
    payload = {
        **request, "schema_version": row.schema_version, "result_status": row.result_status,
        "reason_code": row.reason_code, "engine_key": row.engine_key, "engine_version": row.engine_version,
        "interval_method": row.interval_method, "analytics_run_id": str(run.id),
        "time_series_spec_version": specrow.version_no, "target_indicator_id": str(specrow.target_indicator_id),
        "target_methodology_id": str(specrow.target_methodology_id), "target_methodology_version": specrow.target_methodology_version,
        "methodology_fingerprint": specrow.methodology_fingerprint, "input_snapshot_sha256": specrow.input_snapshot_sha256,
        **data,
    }
    if a._canonical_sha256(payload) != row.result_fingerprint:
        raise a.OrdoAnalyticsError("linked_forecast_result_changed")
    # Verify source is still valid through _forecast_binding; no new fitting/inference.
    if row.result_status == "NOT_ESTIMATED" and (row.forecast_points or row.backtest_records):
        raise a.OrdoAnalyticsError("linked_forecast_unavailable_has_values")
    if row.result_status not in {"ESTIMATED", "NOT_ESTIMATED"}:
        raise a.OrdoAnalyticsError("linked_forecast_status_invalid")
    payload.update({"observation_window": row.observation_window, "training_window": row.training_window,
                    "horizon": row.horizon, "rolling_origin_plan": row.rolling_origin_plan})
    return {"kind": "ordo_forecast_run", "id": str(row.id), "fingerprint": row.result_fingerprint,
            "result": payload, "xai": build_forecast_xai(payload), "causal": False,
            "shap": "UNAVAILABLE_FOR_NAIVE_AND_SEASONAL_NAIVE",
            "scope_match": "HUMAN_CONTEXT_ONLY_NOT_AUTOMATICALLY_VERIFIED"}
