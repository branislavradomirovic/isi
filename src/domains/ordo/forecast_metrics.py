from __future__ import annotations

import math
from collections.abc import Sequence


def _finite(values: Sequence[float]) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result or any(not math.isfinite(value) for value in result):
        raise ValueError("finite_nonempty_values_required")
    return result


def point_errors(actual: Sequence[float], forecast: Sequence[float]) -> tuple[float, ...]:
    actual_values, forecast_values = _finite(actual), _finite(forecast)
    if len(actual_values) != len(forecast_values):
        raise ValueError("actual_forecast_length_mismatch")
    return tuple(predicted - observed for observed, predicted in zip(actual_values, forecast_values, strict=True))


def mae(actual: Sequence[float], forecast: Sequence[float]) -> float:
    errors = point_errors(actual, forecast)
    return sum(abs(error) for error in errors) / len(errors)


def rmse(actual: Sequence[float], forecast: Sequence[float]) -> float:
    errors = point_errors(actual, forecast)
    return math.sqrt(sum(error * error for error in errors) / len(errors))


def bias(actual: Sequence[float], forecast: Sequence[float]) -> float:
    errors = point_errors(actual, forecast)
    return sum(errors) / len(errors)


def smape(actual: Sequence[float], forecast: Sequence[float]) -> float:
    actual_values, forecast_values = _finite(actual), _finite(forecast)
    if len(actual_values) != len(forecast_values):
        raise ValueError("actual_forecast_length_mismatch")
    contributions = []
    for observed, predicted in zip(actual_values, forecast_values, strict=True):
        denominator = abs(observed) + abs(predicted)
        contributions.append(0.0 if denominator == 0 else 200.0 * abs(predicted - observed) / denominator)
    return sum(contributions) / len(contributions)


def mase_scale(training: Sequence[float], lag: int = 1) -> float | None:
    values = _finite(training)
    if lag < 1 or len(values) <= lag:
        return None
    scale = sum(abs(values[index] - values[index - lag]) for index in range(lag, len(values))) / (len(values) - lag)
    return scale if math.isfinite(scale) and scale > 0 else None


def mase(actual: Sequence[float], forecast: Sequence[float], training: Sequence[float], lag: int = 1) -> float | None:
    scale = mase_scale(training, lag)
    return None if scale is None else mae(actual, forecast) / scale


def aggregate_point_metrics(actual: Sequence[float], forecast: Sequence[float]) -> dict[str, float]:
    return {
        "MAE": mae(actual, forecast),
        "RMSE": rmse(actual, forecast),
        "bias": bias(actual, forecast),
        "sMAPE": smape(actual, forecast),
    }


__all__ = ["aggregate_point_metrics", "bias", "mae", "mase", "mase_scale", "point_errors", "rmse", "smape"]
