import math

import pytest

from src.domains.ordo.spatial_processing import aggregate_numeric_values


@pytest.mark.parametrize(("rule", "expected"), [("count", 4.0), ("sum", 8.0), ("mean", 8 / 3), ("min", 1.0), ("max", 5.0)])
def test_generic_reference_calculations(rule, expected):
    result = aggregate_numeric_values([1, None, 2, 5], rule)
    assert result.aggregate_numeric_value == pytest.approx(expected)
    if rule == "count":
        assert result.matched_record_count == 4 and result.dropped_missing_numeric_count == 0
    else:
        assert result.matched_record_count == 3 and result.dropped_missing_numeric_count == 1


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True, "3"])
def test_nonfinite_or_nonnumeric_evidence_is_rejected(value):
    with pytest.raises(ValueError):
        aggregate_numeric_values([value], "sum")


def test_missing_is_never_zero_filled():
    with pytest.raises(ValueError, match="spatial_numeric_evidence_required"):
        aggregate_numeric_values([None, None], "sum")
