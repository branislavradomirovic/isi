"""Accessible bounded SHAP tables/heatmap/waterfall; data never becomes HTML."""

from __future__ import annotations

from html import escape
import math
from pathlib import Path
from src.domains.simpa.statistical_attribution import (
    SCHEMA,
    METHOD,
    TOLERANCE,
    MAX_RECORDS,
    MAX_FEATURES,
    number,
    close,
)
from src.streamlit_app.xai_charts import Chart, _svg, _scale

MAX_HEATMAP_ROWS = 60


def checked(artifact):
    if (
        artifact.get("schema") != SCHEMA
        or artifact.get("method") != METHOD
        or artifact.get("output_scale") != "identity"
    ):
        raise ValueError("Nepodržani SHAP ugovor.")
    features, samples, matrix = artifact["features"], artifact["samples"], artifact["matrix"]
    if (
        not all(isinstance(f, str) and f.strip() for f in features)
        or not isinstance(artifact.get("unit"), str)
        or not artifact["unit"].strip()
        or not 0 < len(features) <= MAX_FEATURES
        or not 0 < len(samples) <= MAX_RECORDS
        or len(matrix) != len(samples)
        or len(set(features)) != len(features)
        or len(artifact["global_mean_absolute"]) != len(features)
        or len(artifact["background_means"]) != len(features)
        or artifact["background_count"] != len(samples)
        or artifact["tolerance"] != TOLERANCE
        or not artifact["non_causal"]
        or not artifact["in_sample_only"]
    ):
        raise ValueError("Neispravna SHAP matrica.")
    for i, (sample, contributions) in enumerate(zip(samples, matrix)):
        if sample["sample"] != i + 1 or len(contributions) != len(features) or len(sample["values"]) != len(features):
            raise ValueError("Red/feature identitet nije podudaran.")
        for v in [*contributions, *sample["values"], sample["prediction"], artifact["baseline"]]:
            number(v)
        close(math.fsum([artifact["baseline"], *contributions]), sample["prediction"])
        actual_error = abs(math.fsum([artifact["baseline"], *contributions]) - sample["prediction"])
        if number(sample["additivity_error"]) < 0:
            raise ValueError("Neispravna additivity greška.")
        close(actual_error, sample["additivity_error"])
    for j, value in enumerate(artifact["global_mean_absolute"]):
        close(artifact["background_means"][j], math.fsum(sample["values"][j] for sample in samples) / len(samples))
        close(value, math.fsum(abs(row[j]) for row in matrix) / len(matrix))
    return artifact


def matrix_rows(artifact):
    checked(artifact)
    return [
        {"uzorak": s["sample"], **{f"SHAP · {f}": v for f, v in zip(artifact["features"], row)}}
        for s, row in zip(artifact["samples"], artifact["matrix"])
    ]


def heatmap(artifact):
    checked(artifact)
    features, matrix = artifact["features"], artifact["matrix"][:MAX_HEATMAP_ROWS]
    peak = max(abs(v) for row in matrix for v in row) or 1
    cell = 400 / len(features)
    body = ""
    for j, feature in enumerate(features):
        body += f'<text x="{70 + j * cell:.3f}" y="20"><title>{escape(feature)}</title>{j + 1}</text>'
    for i, row in enumerate(matrix):
        body += f'<text x="8" y="{49 + i * 18}">{i + 1}</text>'
        for j, value in enumerate(row):
            alpha = 0.08 + 0.92 * abs(value) / peak
            color = "#9c2958" if value > 0 else "#236aa0" if value < 0 else "#d1d5db"
            if value == 0:
                alpha = 1.0
            tip = f"{features[j]} · uzorak {i + 1} · input={artifact['samples'][i]['values'][j]:.6g} · SHAP={value:.6g} · baseline={artifact['baseline']:.6g} · {artifact['unit']}"
            body += f'<rect x="{60 + j * cell:.3f}" y="{35 + i * 18}" width="{cell:.3f}" height="17" fill="{color}" fill-opacity="{alpha:.4f}"><title>{escape(tip)}</title></rect>'
    notices = (
        ("Heatmap prikazuje prvih60 uzoraka; puna matrica je dostupna u tabeli.",)
        if len(artifact["matrix"]) > MAX_HEATMAP_ROWS
        else ()
    )
    return Chart(
        svg=_svg(
            "SHAP matrica",
            "Plavo negativan, ružičasto pozitivan, sivo nulti doprinos; intenzitet apsolutna veličina. Kolone slede redosled features iz tabele.",
            55 + 18 * len(matrix),
            body,
        ),
        notices=notices,
    )


def waterfall(artifact, index):
    checked(artifact)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(artifact["samples"]):
        raise ValueError("Neispravan izbor uzorka.")
    row, sample = artifact["matrix"][index], artifact["samples"][index]
    start = artifact["baseline"]
    steps = []
    for f, x, value in zip(artifact["features"], sample["values"], row):
        stop = math.fsum([start, value])
        steps.append({"feature": f, "input": x, "SHAP": value, "od": start, "do": stop, "jedinica": artifact["unit"]})
        start = stop
    close(start, sample["prediction"])
    scale, lo, hi = _scale(
        [artifact["baseline"], sample["prediction"], *[v for s in steps for v in (s["od"], s["do"])]], 150, 450
    )
    body = ""
    for i, s in enumerate(steps):
        x1, x2 = scale(s["od"]), scale(s["do"])
        y = 32 + i * 30
        color = "#9c2958" if s["SHAP"] > 0 else "#236aa0" if s["SHAP"] < 0 else "#d1d5db"
        body += f'<text x="8" y="{y + 5}"><title>{escape(s["feature"])}</title>{escape(s["feature"][:17])}</text>'
        tip = f"{s['feature']}: input={s['input']:.6g}; SHAP={s['SHAP']:.6g}; {artifact['unit']}"
        body += f'<rect x="{min(x1, x2):.3f}" y="{y - 7}" width="{max(abs(x2 - x1), 1):.3f}" height="16" fill="{color}"><title>{escape(tip)}</title></rect>'
    height = 65 + 30 * len(steps)
    body += f'<text x="150" y="{height - 12}">{lo:.5g}</text><text x="365" y="{height - 12}">{hi:.5g}</text>'
    return Chart(
        svg=_svg(
            "Lokalni SHAP waterfall", "Uzastopni doprinosi od zabeleženog baseline-a do outputa modela.", height, body
        ),
        rows=tuple(steps),
    )


def render_chart(st, chart: Chart) -> None:
    """Render verified attribution without the legacy non-SHAP caption."""
    for notice in chart.notices:
        st.warning(notice)
    st.markdown(chart.svg, unsafe_allow_html=True)
    st.caption("SHAP objašnjava doprinos modelu; grafikon nije dokaz uzročnosti.")


def render_attribution(st, *, token, organization_id, workspace_id, result, permissions, api):
    with st.expander("SHAP — matrica i doprinosi postojećeg OLS modela"):
        with st.expander("SHAP Help — značenje, koraci i ograničenja"):
            st.markdown(Path(__file__).resolve().parents[2].joinpath("docs/help/ISI-SHAP-GUIDE.md").read_text())
        if (result.get("result_detail") or {}).get("model_family") != "ols" or not result.get("production_eligible"):
            st.info("SHAP nije dostupan: potreban je sačuvan continuous OLS rezultat izvršen sa VALIDATED ugovorom.")
            return
        if "analysis.read" not in permissions:
            st.info("Nemate dozvolu za čitanje analitičkog dokaza.")
            return
        key = f"shap-{organization_id}-{workspace_id}-{result['id']}-{result['result_fingerprint']}"
        create = "analysis.run" in permissions and st.button(
            "Kreiraj SHAP dokaz iz postojećeg rezultata", key=key + "-create"
        )
        if create:
            st.session_state[key + "-load"] = True
        load = st.checkbox("Učitaj sačuvani SHAP dokaz", key=key + "-load")
        if not create and not load:
            st.caption("Označite učitavanje da biste pregledali sačuvani dokaz.")
            return
        from src.streamlit_app.api_client import AuthenticationRequired, AccessDenied, ApiUnavailable

        try:
            response = api.attribution(token, organization_id, workspace_id, result["id"], create=create)
        except (AuthenticationRequired, AccessDenied, ApiUnavailable):
            st.warning("SHAP nije dostupan u trenutnom kontekstu. Proverite sesiju/dozvole i ponovo pokušajte.")
            return
        if response["status"] != "AVAILABLE":
            st.info(
                response.get("reason") or "SHAP dokaz nije kreiran. Ovlašćeni analitičar ga kreira zasebnim korakom."
            )
            return
        try:
            artifact = checked(response["artifact"])
        except (ValueError, TypeError, KeyError):
            st.error("SHAP dokaz nije podudaran sa ugovorom; prikaz je zaustavljen.")
            return
        st.text(
            f"Baseline={artifact['baseline']:.6g} · jedinica={artifact['unit']} · background n={artifact['background_count']} · output skala=identity"
        )
        st.warning(artifact["limitations"])
        st.markdown("**Globalni doprinos — srednja apsolutna SHAP vrednost**")
        ranking = sorted(
            [
                {"feature": f, "mean_absolute_SHAP": v}
                for f, v in zip(artifact["features"], artifact["global_mean_absolute"])
            ],
            key=lambda r: -r["mean_absolute_SHAP"],
        )
        st.bar_chart(ranking, x="feature", y="mean_absolute_SHAP", y_label=artifact["unit"])
        st.dataframe(ranking, hide_index=True, width="stretch")
        st.markdown("**Matrica: uzorak × feature**")
        st.text(
            "Kolone heatmap-a su numerisane po redosledu: "
            + ", ".join(f"{i + 1}={f}" for i, f in enumerate(artifact["features"]))
        )
        render_chart(st, heatmap(artifact))
        st.dataframe(matrix_rows(artifact), hide_index=True, width="stretch")
        index = st.selectbox(
            "Uzorak za lokalno objašnjenje",
            list(range(len(artifact["samples"]))),
            format_func=lambda i: f"Uzorak {i + 1}",
            key=key + "-sample",
        )
        chart = waterfall(artifact, index)
        render_chart(st, chart)
        st.dataframe(list(chart.rows), hide_index=True, width="stretch")
        sample = artifact["samples"][index]
        st.caption(
            f"Baseline + ΣSHAP = {sample['prediction']:.8g}; additivity greška={sample['additivity_error']:.3g}, tehnička tolerancija={artifact['tolerance']}. Nije prag institucionalne odluke."
        )
        st.json(
            {
                "schema": artifact["schema"],
                "method": artifact["method"],
                "fingerprint": response["fingerprint"],
                "background_fingerprint": artifact["background_fingerprint"],
                "background_policy": artifact["background_policy"],
                "provenance": artifact["provenance"],
            }
        )
