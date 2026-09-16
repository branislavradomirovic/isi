from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TIME_SERIES_SPEC_SCHEMA_VERSION = "ORDO-TIME-SERIES-SPEC-v1"
CANONICAL_BACKTEST_METRICS = {
    "MAE", "RMSE", "sMAPE", "MASE", "bias", "interval_coverage",
    "interval_width_sharpness", "seasonal_baseline_comparison",
}


class OrdoRollingOriginPlanV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backtest_strategy: Literal["rolling_origin_plan_only"] = "rolling_origin_plan_only"
    initial_train_periods: int = Field(ge=2)
    step_size: int = Field(ge=1)
    horizon: int = Field(ge=1)
    minimum_origins: int = Field(ge=2)
    required_metrics: tuple[str, ...]

    @field_validator("required_metrics", mode="before")
    @classmethod
    def validate_metrics(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or not value:
            raise ValueError("required_metrics must be nonempty")
        result = tuple(dict.fromkeys(str(item).strip() for item in value))
        if any(item not in CANONICAL_BACKTEST_METRICS for item in result):
            raise ValueError("unsupported backtest metric")
        return tuple(sorted(result))


class OrdoTimeSeriesSpecV1(BaseModel):
    """Human-approved forecast-readiness metadata with execution locked off."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True, allow_inf_nan=False)

    schema_version: Literal["ORDO-TIME-SERIES-SPEC-v1"] = TIME_SERIES_SPEC_SCHEMA_VERSION
    series_key: str = Field(min_length=1, max_length=140)
    target_indicator_code: str = Field(min_length=1, max_length=140)
    target_methodology_id: uuid.UUID
    target_methodology_version: int = Field(ge=1)
    target_methodology_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_semantic: Literal["continuous", "count", "proportion_rate"]
    time_index_field: str = Field(min_length=1, max_length=140)
    frequency: Literal["daily", "weekly", "monthly", "quarterly", "annual"]
    series_key_fields: tuple[str, ...]
    observation_window_start: date
    observation_window_end: date
    observation_as_of: date
    minimum_history_periods: int = Field(ge=2)
    maximum_missing_ratio: float = Field(ge=0, le=1)
    missing_data_rule: Literal["fail", "exclude_periods", "explicit_gap"]
    outlier_policy: str = Field(min_length=1, max_length=1000)
    revision_policy: str = Field(min_length=1, max_length=1000)
    comparability_policy: str = Field(min_length=1, max_length=1000)
    transformation: Literal["none", "log1p", "difference", "seasonal_difference"] = "none"
    trend_requirement: Literal["none", "allowed", "required"]
    seasonality_period: int | None = Field(default=None, ge=2)
    candidate_families: tuple[Literal["naive", "seasonal_naive", "ets", "sarima", "sarimax", "count_time_series"], ...]
    horizon: int = Field(ge=1)
    horizon_unit: Literal["days", "weeks", "months", "quarters", "years"]
    uncertainty_output_required: Literal[True] = True
    diagnostic_requirements: tuple[str, ...]
    limitations: tuple[str, ...]
    temporal_validation: OrdoRollingOriginPlanV1
    forecast_execution: Literal[False] = False
    automatic_model_selection: Literal[False] = False
    non_causal: Literal[True] = True

    @field_validator("series_key", "target_indicator_code", "time_index_field", mode="before")
    @classmethod
    def normalize_key(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("time-series keys must be nonblank")
        return value.strip().casefold()

    @field_validator("series_key_fields", "diagnostic_requirements", "limitations", mode="before")
    @classmethod
    def nonempty_unique_text(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)) or not value:
            raise ValueError("time-series lists must be nonempty")
        normalized = tuple(str(item).strip() for item in value)
        if any(not item for item in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("time-series list entries must be nonblank and unique")
        return normalized

    @field_validator("candidate_families")
    @classmethod
    def unique_candidates(cls, value):
        if not value or len(set(value)) != len(value):
            raise ValueError("candidate_families must be nonempty and unique")
        return tuple(sorted(value))

    @model_validator(mode="after")
    def validate_readiness_plan(self):
        if not (self.observation_window_start <= self.observation_window_end <= self.observation_as_of):
            raise ValueError("observation window must end on or before as-of")
        if self.temporal_validation.horizon != self.horizon:
            raise ValueError("backtest horizon must match specification horizon")
        seasonal = {"seasonal_naive", "sarima", "sarimax"}
        if (set(self.candidate_families) & seasonal or self.transformation == "seasonal_difference") and self.seasonality_period is None:
            raise ValueError("seasonality_period is required for seasonal metadata")
        if self.target_semantic == "count":
            if "count_time_series" not in self.candidate_families:
                raise ValueError("count targets require count_time_series candidate metadata")
        elif "count_time_series" in self.candidate_families:
            raise ValueError("count_time_series is allowed only for count targets")
        if self.minimum_history_periods < self.temporal_validation.initial_train_periods + self.horizon:
            raise ValueError("minimum history is insufficient for the rolling-origin plan")
        return self


def normalize_time_series_spec(value: OrdoTimeSeriesSpecV1 | dict[str, Any]):
    return value if isinstance(value, OrdoTimeSeriesSpecV1) else OrdoTimeSeriesSpecV1.model_validate(value)


def canonical_contract_json(value: OrdoTimeSeriesSpecV1 | dict[str, Any]) -> str:
    spec = normalize_time_series_spec(value)
    return json.dumps(spec.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def contract_fingerprint(value: OrdoTimeSeriesSpecV1 | dict[str, Any]) -> str:
    return hashlib.sha256(canonical_contract_json(value).encode("utf-8")).hexdigest()


spec_fingerprint = contract_fingerprint


__all__ = ["OrdoRollingOriginPlanV1", "OrdoTimeSeriesSpecV1", "canonical_contract_json", "contract_fingerprint", "normalize_time_series_spec", "spec_fingerprint"]
