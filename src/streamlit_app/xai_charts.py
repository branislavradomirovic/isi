"""Bounded graphical read models for existing persisted XAI evidence only."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
import math
from collections.abc import Mapping
from typing import Any

MAX_COEFFICIENTS = 24
MAX_POINTS = 60
MAX_ORIGINS = 40
MAX_LABEL = 128
MAX_SVG_BYTES = 128_000
WIDTH = 480
SUPPORTED_FAMILIES = {'ols', 'poisson_glm', 'binomial_logit', 'fractional_logit'}


@dataclass(frozen=True)
class Chart:
    svg: str = ''
    rows: tuple[dict[str, Any], ...] = ()
    notices: tuple[str, ...] = ()
    unavailable: str = ''


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _text(value: Any) -> str:
    text = str(value)
    return ''.join(c for c in text[:MAX_LABEL] if c.isprintable())


def _svg(title: str, description: str, height: int, body: str) -> str:
    result = (f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(title, quote=True)}" '
              f'viewBox="0 0 {WIDTH} {height}" style="width:100%;height:auto;max-width:800px;background:white;color:#162d40">'
              f'<title>{escape(title)}</title><desc>{escape(description)}</desc>'
              f'<g font-family="sans-serif" font-size="14" fill="#162d40">{body}</g></svg>')
    return result if len(result.encode()) <= MAX_SVG_BYTES else ''


def _scale(values: list[float], start: float, stop: float):
    lo, hi = min(values), max(values)
    if lo == hi:
        pad = max(abs(lo) * .05, 1.0)
        lo, hi = lo - pad, hi + pad
    span = hi - lo
    if not math.isfinite(span) or span <= 0:
        raise ValueError('numeric_range_unavailable')
    return lambda value: start + ((value - lo) / span) * (stop - start), lo, hi


def coefficient_chart(result: Mapping[str, Any]) -> Chart:
    detail = result.get('result_detail')
    if not isinstance(detail, Mapping):
        return Chart(unavailable='Nema podržanih sačuvanih koeficijenata.')
    schema = result.get('engine_schema_version') or detail.get('engine_schema_version')
    if schema != 'SIMPA-STATISTICAL-MODEL-v1' or detail.get('model_family') not in SUPPORTED_FAMILIES:
        return Chart(unavailable='Nepodržana verzija rezultata/modela; koristite izvornu tabelu.')
    source = detail.get('coefficients')
    if not isinstance(source, list) or not source:
        return Chart(unavailable='Nema sačuvanih koeficijenata za grafikon.')
    rows, notices = [], []
    if len(source) > MAX_COEFFICIENTS:
        notices.append(f'Grafikon prikazuje prvih {MAX_COEFFICIENTS} koeficijenata; puna tabela ostaje ispod.')
    for raw in source[:MAX_COEFFICIENTS]:
        if not isinstance(raw, Mapping) or not isinstance(raw.get('term'), str):
            return Chart(unavailable='Neispravan red koeficijenta; grafikon nije generisan.')
        estimate = _number(raw.get('estimate'))
        if estimate is None:
            return Chart(unavailable='Nefinitan/nedostajući koeficijent; proverite izvornu tabelu.')
        low, high = raw.get('confidence_interval_low'), raw.get('confidence_interval_high')
        a, b = _number(low), _number(high)
        if low is None and high is None:
            notices.append(f'{_text(raw["term"])}: interval nije dostupan; prikazana je samo tačka.')
        elif a is None or b is None or not a <= estimate <= b:
            return Chart(unavailable='Neispravan sačuvani interval; granice nisu popravljene niti zamenjene.')
        rows.append({'term': raw['term'], 'estimate': estimate, 'lower': a, 'upper': b})
    try:
        scale, lo, hi = _scale([0.0] + [v for row in rows for v in (row['estimate'], row['lower'], row['upper']) if v is not None], 160, 450)
    except ValueError:
        return Chart(unavailable='Numerički opseg nije moguće bezbedno prikazati.')
    height = 80 + 32 * len(rows)
    body = f'<line x1="{scale(0):.3f}" x2="{scale(0):.3f}" y1="20" y2="{height-45}" stroke="#aaa"/>'
    for i, row in enumerate(rows):
        y = 30 + i * 32
        label = _text(row['term'])
        body += f'<text x="8" y="{y+5}"><title>{escape(label)}</title>{escape(label[:18])}</text>'
        if row['lower'] is not None:
            body += f'<line x1="{scale(row["lower"]):.3f}" x2="{scale(row["upper"]):.3f}" y1="{y}" y2="{y}" stroke="#2563a0" stroke-width="3"/>'
        body += f'<circle cx="{scale(row["estimate"]):.3f}" cy="{y}" r="4" fill="#173e65"><title>{escape(label)}: {row["estimate"]:.6g}</title></circle>'
    body += f'<text x="160" y="{height-15}">{lo:.4g}</text><text x="390" y="{height-15}">{hi:.4g}</text>'
    return Chart(_svg('Koeficijenti i sačuvani intervali / Coefficients and stored intervals',
                      'Tačke su koeficijenti; linije su postojeći intervali. Skala zavisi od model family/link. Nije kauzalni efekat.', height, body), tuple(rows), tuple(notices))


def _series_chart(rows: list[dict], *, backtest: bool, notices: tuple[str, ...] = ()) -> Chart:
    fields = ('actual', 'forecast') if backtest else ('point', 'lower', 'upper')
    values = [row[f] for row in rows for f in fields if row[f] is not None]
    try:
        scale, lo, hi = _scale(values, 210, 35)
    except ValueError:
        return Chart(unavailable='Numerički opseg nije moguće bezbedno prikazati.')
    def x(i: int) -> float:
        return 60 + (i / max(1, len(rows) - 1)) * 365
    body = f'<text x="5" y="35">{hi:.4g}</text><text x="5" y="210">{lo:.4g}</text>'
    colors = {'actual': '#805000', 'forecast': '#18589a', 'point': '#18589a', 'lower': '#657988', 'upper': '#657988'}
    for field in fields:
        # Missing intervals are separate segments: never bridge missing evidence.
        previous = None
        for i, row in enumerate(rows):
            value = row[field]
            if value is None:
                previous = None
                continue
            cx, cy = x(i), scale(value)
            if previous is not None:
                body += f'<line x1="{previous[0]:.3f}" y1="{previous[1]:.3f}" x2="{cx:.3f}" y2="{cy:.3f}" stroke="{colors[field]}" stroke-width="2"/>'
            body += f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="3" fill="{colors[field]}"><title>{escape(_text(row["label"]))}: {field}={value:.6g}</title></circle>'
            previous = cx, cy
    for i in sorted({0, len(rows) - 1}):
        label = _text(rows[i]['label'])[:20]
        body += f'<text x="{60 if i == 0 else 425}" y="240" text-anchor="{"start" if i == 0 else "end"}">{escape(label)}</text>'
    legend = 'Braon: stvarno / actual; plavo: forecast' if backtest else 'Plavo: point; sivo: lower / upper'
    body += f'<text x="10" y="270">{legend}</text>'
    return Chart(_svg('Backtest jednog porekla / One-origin backtest' if backtest else 'Prognoza i intervali / Forecast and intervals',
                      'Samo sačuvane vrednosti; x osa je sačuvani redosled koraka. Detaljne vrednosti u tabeli.', 290, body), tuple(rows), notices)


def forecast_chart(result: Mapping[str, Any]) -> Chart:
    if result.get('result_status') != 'ESTIMATED':
        return Chart(unavailable='NOT_ESTIMATED/UNKNOWN: grafikon ne pravi zamenske nule ili tačke.')
    if result.get('schema_version') != 'ORDO-FORECAST-RUN-v1':
        return Chart(unavailable='Nepodržana verzija prognoze; koristite izvorni dokaz.')
    points = result.get('forecast_points')
    if not isinstance(points, list) or not points:
        return Chart(unavailable='Nema sačuvanih tačaka prognoze.')
    rows, notices = [], []
    if len(points) > MAX_POINTS:
        notices.append(f'Prikazano je prvih {MAX_POINTS} tačaka; puna tabela ostaje dostupna.')
    for i, point in enumerate(points[:MAX_POINTS], 1):
        if not isinstance(point, Mapping) or point.get('horizon_step') != i or not isinstance(point.get('time'), str):
            return Chart(unavailable='Neispravan redosled/identitet sačuvanih tačaka.')
        number = _number(point.get('point'))
        a, b = _number(point.get('lower')), _number(point.get('upper'))
        if number is None:
            return Chart(unavailable='Nedostajuća/neispravna point vrednost.')
        if point.get('lower') is None and point.get('upper') is None:
            notices.append(f'Korak {i}: interval nije dostupan.')
        elif a is None or b is None or a > b:
            return Chart(unavailable='Neispravan interval prognoze; vrednosti nisu popravljene.')
        rows.append({'label': point['time'], 'point': number, 'lower': a, 'upper': b})
    return _series_chart(rows, backtest=False, notices=tuple(notices))


def backtest_chart(result: Mapping[str, Any], origin_position: int) -> Chart:
    if result.get('result_status') != 'ESTIMATED' or result.get('schema_version') != 'ORDO-FORECAST-RUN-v1':
        return Chart(unavailable='Nema podržanog backtest rezultata.')
    origins = result.get('backtest_records')
    if not isinstance(origins, list) or isinstance(origin_position, bool) or not isinstance(origin_position, int) or not 0 <= origin_position < min(len(origins), MAX_ORIGINS):
        return Chart(unavailable='Poreklo nije dostupno.')
    record = origins[origin_position]
    if not isinstance(record, Mapping):
        return Chart(unavailable='Neispravan backtest zapis.')
    actual, forecast = record.get('actual'), record.get('forecast')
    start = record.get('test_start')
    if not isinstance(actual, list) or not isinstance(forecast, list) or not actual or len(actual) != len(forecast) or isinstance(start, bool) or not isinstance(start, int) or start < 0:
        return Chart(unavailable='Neusklađene/nepotpune sačuvane backtest serije.')
    rows = []
    for i in range(min(len(actual), MAX_POINTS)):
        a, b = _number(actual[i]), _number(forecast[i])
        if a is None or b is None:
            return Chart(unavailable='Nefinitan/nedostajući backtest podatak.')
        rows.append({'label': f'Index {start+i}', 'actual': a, 'forecast': b})
    notices = (f'Prvih {MAX_POINTS} koraka; kompletan zapis je u per-origin dokazu.',) if len(actual) > MAX_POINTS else ()
    return _series_chart(rows, backtest=True, notices=notices)


def render_chart(st: Any, chart: Chart) -> None:
    if chart.unavailable:
        st.info(chart.unavailable)
        return
    for notice in chart.notices:
        st.warning(notice)
    if chart.svg:
        # Only our fixed template enters HTML; every source label is escaped.
        st.markdown(chart.svg, unsafe_allow_html=True)
    else:
        st.info('Grafikon nije dostupan; koristite tabelu dokaza.')
    st.caption('SHAP atribucija nije dostupna u ovom prikazu. Grafikon nije dokaz uzročnosti.')
