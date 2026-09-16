import pytest

from src.domains.ordo.forecasting import (
    ForecastNotEstimated,
    forecast_family,
    naive_forecast,
    seasonal_naive_forecast,
)


def test_naive_and_seasonal_naive_are_explicit_and_deterministic():
    assert naive_forecast([1, 2, 3], 4) == [3, 3, 3, 3]
    assert seasonal_naive_forecast([1, 2, 3, 4], 5, 2) == [3, 4, 3, 4, 3]
    assert forecast_family([1, 2, 3], 2, "naive") == [3, 3]


def test_seasonal_naive_never_falls_back_to_naive():
    with pytest.raises(ForecastNotEstimated, match="SEASONAL_PERIOD_REQUIRED"):
        seasonal_naive_forecast([1, 2, 3], 2, None)
    with pytest.raises(ForecastNotEstimated, match="SEASONAL_HISTORY_INSUFFICIENT"):
        seasonal_naive_forecast([1, 2, 3], 2, 4)
    with pytest.raises(ForecastNotEstimated, match="EXECUTABLE_FAMILY_NOT_DEFINED_24C"):
        forecast_family([1, 2, 3], 2, "ets")
