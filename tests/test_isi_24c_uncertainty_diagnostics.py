import pytest

from src.domains.ordo.forecasting import (
    ForecastNotEstimated,
    clip_interval,
    empirical_quantile,
    empirical_residual_interval,
)


def test_empirical_interval_and_domain_clipping_are_deterministic():
    assert empirical_quantile([-2, 0, 2, 4], 0.5) == 1.0
    lower, upper = empirical_residual_interval(10, [-2, 0, 2, 4], 0.80)
    assert lower == pytest.approx(8.6)
    assert upper == pytest.approx(13.4)
    assert clip_interval(-2, 3, "count") == (0.0, 3)
    assert clip_interval(-0.2, 1.4, "proportion_rate") == (0.0, 1.0)


def test_interval_requires_three_completed_residuals():
    with pytest.raises(ForecastNotEstimated, match="INSUFFICIENT_INTERVAL_CALIBRATION"):
        empirical_residual_interval(1, [0, 1], 0.95)
