from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


ENGINE_KEY = "ordo_deterministic_baseline"
ENGINE_VERSION = "1"
INTERVAL_METHOD = "rolling_origin_empirical_residual_quantile_v1"


class ForecastNotEstimated(ValueError):
    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True)
class RollingOriginSplit:
    origin_index: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def _training_values(training: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in training)
    if not values or any(not math.isfinite(value) for value in values):
        raise ValueError("finite_training_values_required")
    return values


def naive_forecast(training: Sequence[float], horizon: int) -> list[float]:
    values = _training_values(training)
    if horizon < 1:
        raise ValueError("positive_horizon_required")
    return [values[-1]] * horizon


def seasonal_naive_forecast(training: Sequence[float], horizon: int, seasonality_period: int | None) -> list[float]:
    values = _training_values(training)
    if seasonality_period is None:
        raise ForecastNotEstimated("SEASONAL_PERIOD_REQUIRED")
    if seasonality_period < 2:
        raise ValueError("invalid_seasonality_period")
    if len(values) < seasonality_period:
        raise ForecastNotEstimated("SEASONAL_HISTORY_INSUFFICIENT")
    if horizon < 1:
        raise ValueError("positive_horizon_required")
    cycle = values[-seasonality_period:]
    return [cycle[index % seasonality_period] for index in range(horizon)]


def forecast_family(
    training: Sequence[float], horizon: int, family: str, seasonality_period: int | None = None
) -> list[float]:
    if family == "naive":
        return naive_forecast(training, horizon)
    if family == "seasonal_naive":
        return seasonal_naive_forecast(training, horizon, seasonality_period)
    raise ForecastNotEstimated("EXECUTABLE_FAMILY_NOT_DEFINED_24C")


def rolling_origin_splits(
    observation_count: int, initial_train_periods: int, step_size: int, horizon: int
) -> list[RollingOriginSplit]:
    if min(observation_count, initial_train_periods, step_size, horizon) < 1:
        raise ValueError("positive_rolling_origin_parameters_required")
    splits: list[RollingOriginSplit] = []
    train_end = initial_train_periods
    while train_end + horizon <= observation_count:
        splits.append(RollingOriginSplit(len(splits), 0, train_end, train_end, train_end + horizon))
        train_end += step_size
    return splits


def empirical_quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(_training_values(values))
    if not 0 <= probability <= 1:
        raise ValueError("quantile_probability_out_of_range")
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    weight = position - lower_index
    return ordered[lower_index] + weight * (ordered[upper_index] - ordered[lower_index])


def empirical_residual_interval(point: float, residuals: Sequence[float], interval_level: float) -> tuple[float, float]:
    if len(residuals) < 3:
        raise ForecastNotEstimated("INSUFFICIENT_INTERVAL_CALIBRATION")
    alpha = 1.0 - interval_level
    lower = float(point) + empirical_quantile(residuals, alpha / 2.0)
    upper = float(point) + empirical_quantile(residuals, 1.0 - alpha / 2.0)
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ValueError("non_finite_interval")
    return min(lower, upper), max(lower, upper)


def clip_interval(lower: float, upper: float, target_semantic: str) -> tuple[float, float]:
    if target_semantic == "count":
        return max(0.0, lower), max(0.0, upper)
    if target_semantic == "proportion_rate":
        return min(1.0, max(0.0, lower)), min(1.0, max(0.0, upper))
    return lower, upper


def run_rolling_origin(
    values: Sequence[float], *, family: str, initial_train_periods: int, step_size: int,
    horizon: int, minimum_origins: int, seasonality_period: int | None = None,
) -> list[dict[str, object]]:
    history = _training_values(values)
    splits = rolling_origin_splits(len(history), initial_train_periods, step_size, horizon)
    if len(splits) < minimum_origins:
        raise ForecastNotEstimated("INSUFFICIENT_ROLLING_ORIGINS")
    records: list[dict[str, object]] = []
    for split in splits:
        training = history[split.train_start:split.train_end]
        actual = history[split.test_start:split.test_end]
        forecast = forecast_family(training, horizon, family, seasonality_period)
        records.append({
            "origin_index": split.origin_index,
            "train_start": split.train_start,
            "train_end": split.train_end,
            "test_start": split.test_start,
            "test_end": split.test_end,
            "training": list(training),
            "actual": list(actual),
            "forecast": forecast,
            "residuals": [observed - predicted for observed, predicted in zip(actual, forecast, strict=True)],
        })
    return records


__all__ = [
    "ENGINE_KEY", "ENGINE_VERSION", "INTERVAL_METHOD", "ForecastNotEstimated", "RollingOriginSplit",
    "clip_interval", "empirical_quantile", "empirical_residual_interval", "forecast_family",
    "naive_forecast", "rolling_origin_splits", "run_rolling_origin", "seasonal_naive_forecast",
]
