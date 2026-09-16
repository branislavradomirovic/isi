import uuid

import pytest
from pydantic import ValidationError

from src.api.ordo_analytics_routes import router
from src.domains.ordo.analytics_schemas import ForecastExecutionRequest


def _request(**changes):
    value = {
        "organization_id": uuid.UUID(int=1), "workspace_id": uuid.UUID(int=2),
        "time_series_spec_id": uuid.UUID(int=3), "requested_family": "naive",
        "series_identity": {"destination": "A"}, "interval_level": 0.90,
    }
    value.update(changes)
    return value


def test_forecast_request_is_explicit_and_closed():
    assert ForecastExecutionRequest.model_validate(_request()).interval_level == 0.90
    with pytest.raises(ValidationError):
        ForecastExecutionRequest.model_validate(_request(interval_level=0.85))
    with pytest.raises(ValidationError):
        ForecastExecutionRequest.model_validate(_request(extra="forbidden"))


def test_forecast_routes_and_permission_contract_exist():
    paths = {(route.path, method) for route in router.routes for method in route.methods}
    assert ("/api/v1/ordo/analytics/forecasts", "POST") in paths
    assert ("/api/v1/ordo/analytics/forecasts", "GET") in paths
    assert ("/api/v1/ordo/analytics/forecasts/{forecast_run_id}", "GET") in paths
