from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SPATIAL_AGGREGATION_SCHEMA_VERSION = "ORDO-SPATIAL-AGGREGATION-v1"
REQUIRED_SPATIAL_SOURCE_FIELDS = (
    "boundary_version",
    "crs",
    "indicator_code",
    "quality_status",
    "spatial_unit_key",
    "spatial_unit_type",
    "value_numeric",
)


class OrdoSpatialAggregationContractV1(BaseModel):
    """Identity-based descriptive aggregation; deliberately not a geometry contract."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal["ORDO-SPATIAL-AGGREGATION-v1"] = SPATIAL_AGGREGATION_SCHEMA_VERSION
    aggregation_rule: Literal["count", "sum", "mean", "min", "max"]
    required_source_fields: tuple[str, ...] = REQUIRED_SPATIAL_SOURCE_FIELDS
    validated_quality_required: Literal[True] = True
    missing_numeric_rule: Literal["exclude_and_count"] = "exclude_and_count"
    weighted: Literal[False] = False
    spatial_join_performed: Literal[False] = False
    non_causal: Literal[True] = True
    automatic_policy_recommendation: Literal[False] = False

    @field_validator("required_source_fields", mode="before")
    @classmethod
    def exact_required_fields(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("required_source_fields must be a list")
        normalized = tuple(sorted(str(item).strip() for item in value))
        if normalized != tuple(sorted(REQUIRED_SPATIAL_SOURCE_FIELDS)):
            raise ValueError("required_source_fields must match the v1 spatial identity contract")
        return normalized


class SpatialAggregationCalculationV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    aggregation_rule: Literal["count", "sum", "mean", "min", "max"]
    input_record_count: int = Field(ge=0)
    matched_record_count: int = Field(ge=0)
    dropped_missing_numeric_count: int = Field(ge=0)
    aggregate_numeric_value: float


def aggregate_numeric_values(
    values: Sequence[int | float | None], aggregation_rule: str
) -> SpatialAggregationCalculationV1:
    """Apply one of the five generic arithmetic rules without imputation or weights."""

    if aggregation_rule not in {"count", "sum", "mean", "min", "max"}:
        raise ValueError("spatial_aggregation_rule_invalid")
    numeric: list[float] = []
    missing = 0
    for value in values:
        if value is None:
            missing += 1
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("spatial_numeric_evidence_invalid")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("spatial_numeric_evidence_non_finite")
        numeric.append(number)
    if aggregation_rule == "count":
        result = float(len(values))
        dropped = 0
        matched = len(values)
    else:
        if not numeric:
            raise ValueError("spatial_numeric_evidence_required")
        operations = {
            "sum": lambda: sum(numeric),
            "mean": lambda: sum(numeric) / len(numeric),
            "min": lambda: min(numeric),
            "max": lambda: max(numeric),
        }
        result = float(operations[aggregation_rule]())
        dropped = missing
        matched = len(numeric)
    return SpatialAggregationCalculationV1(
        aggregation_rule=aggregation_rule,
        input_record_count=len(values),
        matched_record_count=matched,
        dropped_missing_numeric_count=dropped,
        aggregate_numeric_value=result,
    )


def canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "OrdoSpatialAggregationContractV1",
    "REQUIRED_SPATIAL_SOURCE_FIELDS",
    "SPATIAL_AGGREGATION_SCHEMA_VERSION",
    "SpatialAggregationCalculationV1",
    "aggregate_numeric_values",
    "canonical_json",
    "canonical_sha256",
]
