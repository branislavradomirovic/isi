from copy import deepcopy
import math
import xml.etree.ElementTree as ET

import pytest

from src.streamlit_app.xai_charts import (
    MAX_COEFFICIENTS, MAX_POINTS, backtest_chart, coefficient_chart, forecast_chart,
)


def simpa(family='ols'):
    return {'engine_schema_version': 'SIMPA-STATISTICAL-MODEL-v1', 'result_detail': {
        'model_family': family, 'coefficients': [
            {'term': 'intercept', 'estimate': 0, 'confidence_interval_low': -1, 'confidence_interval_high': 1},
            {'term': 'feature', 'estimate': 2, 'confidence_interval_low': 1, 'confidence_interval_high': 3},
        ]}}


def ordo():
    return {'schema_version': 'ORDO-FORECAST-RUN-v1', 'result_status': 'ESTIMATED',
            'forecast_points': [{'horizon_step': 1, 'time': '2026-11-01', 'point': 0, 'lower': 0, 'upper': 1},
                                {'horizon_step': 2, 'time': '2026-12-01', 'point': 2, 'lower': 1, 'upper': 4}],
            'backtest_records': [ {'origin_index': 2, 'test_start': 2, 'actual': [1, 3], 'forecast': [2, 2]},
                                  {'origin_index': 3, 'test_start': 3, 'actual': [3, 4], 'forecast': [3, 3]}]}


@pytest.mark.parametrize('family', ['ols', 'poisson_glm', 'binomial_logit', 'fractional_logit'])
def test_coefficients_exact_values_immutable_and_svg_valid(family):
    source = simpa(family)
    before = deepcopy(source)
    chart = coefficient_chart(source)
    assert chart.rows[0]['estimate'] == 0
    assert chart.rows[1] == {'term': 'feature', 'estimate': 2, 'lower': 1, 'upper': 3}
    assert not chart.unavailable and ET.fromstring(chart.svg).tag.endswith('svg')
    assert source == before


@pytest.mark.parametrize('value', [math.nan, math.inf, -math.inf, True, '1', 10**400])
def test_invalid_coefficients_fail_closed(value):
    source = simpa()
    source['result_detail']['coefficients'][0]['estimate'] = value
    assert coefficient_chart(source).unavailable


def test_missing_interval_is_not_zero_width_and_invalid_not_repaired():
    source = simpa()
    row = source['result_detail']['coefficients'][0]
    row.pop('confidence_interval_low')
    row.pop('confidence_interval_high')
    chart = coefficient_chart(source)
    assert chart.rows[0]['lower'] is None and chart.notices
    row.update(confidence_interval_low=2, confidence_interval_high=1)
    assert coefficient_chart(source).unavailable


def test_unknown_schema_and_family():
    source = simpa()
    source['engine_schema_version'] = 'future'
    assert coefficient_chart(source).unavailable
    assert coefficient_chart(simpa('tree')).unavailable
    source = ordo()
    source['schema_version'] = 'future'
    assert forecast_chart(source).unavailable and backtest_chart(source, 0).unavailable


def test_labels_cannot_inject_elements_or_attributes():
    source = simpa()
    source['result_detail']['coefficients'][0]['term'] = '<script>alert(1)</script><img src="x" onerror="x">'
    chart = coefficient_chart(source)
    tags = {e.tag.split('}')[-1] for e in ET.fromstring(chart.svg).iter()}
    assert tags <= {'svg', 'title', 'desc', 'g', 'text', 'line', 'circle'}
    assert not any(k.startswith('on') for e in ET.fromstring(chart.svg).iter() for k in e.attrib)
    assert '<script>' not in chart.svg
    assert 'width:100%;height:auto' in chart.svg and '<desc>' in chart.svg


def test_size_caps_are_explicit_not_silent():
    source = simpa()
    source['result_detail']['coefficients'] *= 20
    chart = coefficient_chart(source)
    assert len(chart.rows) == MAX_COEFFICIENTS and chart.notices
    source = ordo()
    source['forecast_points'] = [dict(source['forecast_points'][0], horizon_step=i, time=f'period {i}') for i in range(1, 80)]
    chart = forecast_chart(source)
    assert len(chart.rows) == MAX_POINTS and chart.notices


def test_forecast_parity_zero_and_intervals_not_forced_to_contain_point():
    source = ordo()
    before = deepcopy(source)
    source['forecast_points'][1].update(lower=3, upper=4)
    chart = forecast_chart(source)
    assert chart.rows[0]['point'] == 0
    assert chart.rows[1]['lower'] == 3
    assert source['backtest_records'] == before['backtest_records']
    assert ET.fromstring(chart.svg).attrib['viewBox'] == '0 0 480 290'


def test_missing_intervals_and_invalid_order():
    source = ordo()
    source['forecast_points'][0].update(lower=None, upper=None)
    assert forecast_chart(source).notices
    source['forecast_points'][1]['horizon_step'] = 3
    assert forecast_chart(source).unavailable


def test_not_estimated_does_not_draw_even_if_points_exist():
    source = ordo()
    source['result_status'] = 'NOT_ESTIMATED'
    assert not forecast_chart(source).svg and not forecast_chart(source).rows
    assert not backtest_chart(source, 0).svg


def test_backtest_origins_stay_separate_and_keep_actuals():
    source = ordo()
    a, b = backtest_chart(source, 0), backtest_chart(source, 1)
    assert a.rows == ({'label': 'Index 2', 'actual': 1, 'forecast': 2}, {'label': 'Index 3', 'actual': 3, 'forecast': 2})
    assert b.rows[0]['actual'] == 3 and b.rows[0]['forecast'] == 3
    source['backtest_records'][0]['actual'] = [1]
    assert backtest_chart(source, 0).unavailable
    assert backtest_chart(source, -1).unavailable
    assert backtest_chart(source, True).unavailable


def test_extreme_range_and_malformed_records_safe():
    source = simpa()
    source['result_detail']['coefficients'][0].update(estimate=0, confidence_interval_low=-1e308, confidence_interval_high=1e308)
    assert coefficient_chart(source).unavailable
    source = ordo()
    source['forecast_points'] = [None]
    assert forecast_chart(source).unavailable
