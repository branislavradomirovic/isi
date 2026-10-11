"""Typed ORDO aggregation request; no methodological authority in customer payload."""

from src.domains.ordo.analytics_schemas import SpatialAggregationRequest
from src.streamlit_app.api_client import request
from src.streamlit_app.ordo_analytics_api import _checked


def create(token, *, scope, analytics_run_id, reviewed_methodology_id, indicator_code, target_spatial_unit_id):
    body = SpatialAggregationRequest.model_validate(
        {
            **scope,
            "analytics_run_id": analytics_run_id,
            "reviewed_methodology_id": reviewed_methodology_id,
            "indicator_code": indicator_code,
            "target_spatial_unit_id": target_spatial_unit_id,
        }
    ).model_dump(mode="json")
    return _checked(
        request("POST", "/api/v1/ordo/analytics/spatial-aggregations", token=token, json=body),
        unavailable="Izvršenje je možda registrovano. Osvežite GIS pregled pre ponavljanja.",
    )
