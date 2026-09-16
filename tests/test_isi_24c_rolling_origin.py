import pytest

from src.domains.ordo.forecasting import ForecastNotEstimated, rolling_origin_splits, run_rolling_origin


def test_splits_are_chronological_complete_horizons_only():
    splits = rolling_origin_splits(10, initial_train_periods=4, step_size=2, horizon=3)
    assert [(item.train_end, item.test_start, item.test_end) for item in splits] == [(4, 4, 7), (6, 6, 9)]
    records = run_rolling_origin(
        list(range(10)), family="naive", initial_train_periods=4,
        step_size=2, horizon=3, minimum_origins=2,
    )
    assert records[0]["training"] == [0.0, 1.0, 2.0, 3.0]
    assert records[0]["forecast"] == [3.0, 3.0, 3.0]
    assert records[0]["actual"] == [4.0, 5.0, 6.0]


def test_minimum_origins_is_a_domain_outcome():
    with pytest.raises(ForecastNotEstimated, match="INSUFFICIENT_ROLLING_ORIGINS"):
        run_rolling_origin([1, 2, 3, 4, 5], family="naive", initial_train_periods=3, step_size=1, horizon=2, minimum_origins=2)
