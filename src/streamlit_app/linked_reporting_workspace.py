"""Linked report inputs and safe map/XAI preview on live API responses."""

import streamlit as st
from src.streamlit_app.evidence_view import render_evidence
from src.streamlit_app.spatial_workspace import render_map_table
from src.streamlit_app.attribution_view import matrix_rows, heatmap, waterfall, render_chart as render_attribution_chart
from src.streamlit_app.xai_charts import render_chart, coefficient_chart, forecast_chart

HELP = (
    "Povezani izveštaj prikazuje jedan prihvaćeni nalaz sa izvorom, obuhvatom i opcionim numeričkim rezultatom.",
    "Koristite ga kada je ekstrakcija već pregledana; report review i publication su zasebni koraci.",
    "Čitanje zahteva report.read i data.read; rezultat analysis.read; kreiranje analysis.run; review/publication organization.manage.",
    "Izaberite prihvaćenu ekstrakciju, claim ID iz Podataka, opciono result UUID, napišite obrazloženje, potvrdite i pregledajte pa kreirajte draft.",
    "REVIEWED_ACCEPTED potvrđuje pregled ekstrakcije. UNRESOLVED znači da obuhvat nije potvrđen. UNAVAILABLE znači da nema podržanog izabranog rezultata.",
    "Primer: agregirani nalaz za 2025. i ljudski potvrđen poligon uporedite sa postojećim rezultatom; objasnite razliku između izvornog i modelskog perioda.",
    "Veza je kontekst koji korisnik bira. Ne potvrđuje automatski istinitost, slaganje perioda/jedinice/teritorije, kalibraciju ili uzrok.",
    "Ako je izvor povučen, geometrija promenjena ili prava ukinuta, ponovno čitanje/izvoz se blokira. Pripremite novu pregledanu ekstrakciju i novu verziju.",
    "Samo agregatni nepersonalni podaci; odvojeni SIMPA/ORDO scope. Preuzete kopije se ne mogu udaljeno opozvati; postupajte prema institucionalnim pravilima.",
    "Manifest čuva otiske izvora, izvlačenja, pregleda, granice i rezultata. Kvalitet ekstrakcije UNCALIBRATED; SIMPA SHAP samo podržani OLS, ORDO SHAP unavailable.",
)


def inputs(prefix):
    with st.expander("Pomoć — povezani nalazi i izveštaji"):
        for i, text in enumerate(HELP, 1):
            st.write(f"{i}. {text}")
    claim_id = st.text_input("ID prihvaćenog nalaza iz Podataka", value="c1", key=prefix + "claim")
    result_id = st.text_input("UUID numeričkog rezultata — opciono", key=prefix + "result")
    st.caption(
        "SIMPA: validirani continuous OLS rezultat. ORDO: sačuvana prognoza. Ostavite prazno kada nema podržanog rezultata."
    )
    note = st.text_area("Obrazloženje veze i razlika u periodu ili teritoriji", key=prefix + "note")
    attested = st.checkbox(
        "Potvrđujem ljudski izbor veze; ovo nije automatska potvrda istinitosti", key=prefix + "attested"
    )
    return {"claim_id": claim_id, "result_id": result_id.strip() or None, "note": note, "attested": attested}


def preview(content, scope):
    packet = content["packet"]
    st.warning(
        "Kontekstualna veza — bez automatske potvrde istinitosti ili institucionalne odluke. Ekstrakcija UNCALIBRATED."
    )
    st.text(packet["claim"]["statement"]["quote"])
    with st.expander("Struktura i citati nalaza"):
        render_evidence("Citirani nalaz i struktura", packet["claim"])
    geo = packet.get("geometry")
    if geo:
        render_map_table([geo], scope=scope, at_date=packet["territory"]["at_date"])
    else:
        st.info("Obuhvat nalaza UNRESOLVED — nema izmišljene lokacije.")
    evidence = packet["numerical_evidence"]
    if evidence.get("kind") == "simpa_statistical_result":
        render_chart(st, coefficient_chart(evidence["result"]))
        attribution = evidence["xai"]
        if attribution.get("status") == "AVAILABLE":
            artifact = attribution["artifact"]
            st.dataframe(matrix_rows(artifact), hide_index=True, width="stretch")
            st.bar_chart(
                [
                    {"feature": f, "mean_absolute_SHAP": v}
                    for f, v in zip(artifact["features"], artifact["global_mean_absolute"])
                ],
                x="feature",
                y="mean_absolute_SHAP",
            )
            render_attribution_chart(st, heatmap(artifact))
            sample = st.selectbox("Uzorak za lokalni doprinos", range(len(artifact["samples"])), key=scope + "-sample")
            render_attribution_chart(st, waterfall(artifact, sample))
        else:
            st.info("SHAP artifact nije kreiran. Ovaj pregled ne pokreće računanje.")
    elif evidence.get("kind") == "ordo_forecast_run":
        render_chart(st, forecast_chart(evidence["result"]))
        st.info("ORDO SHAP nije podržan za naive/seasonal-naive; koristite intervale i backtest dokaze.")
    else:
        st.info("Numerički rezultat UNAVAILABLE — nije izabran.")
    with st.expander("Izvor i pregled nalaza"):
        render_evidence(
            "Dokaz, izvor i ograničenja",
            {"source": packet["source"], "review": packet["review"], "provenance": packet["extraction_provenance"]},
        )
