"""Existing ORDO methodology lifecycle with explicit human approvals."""

from pathlib import Path

import streamlit as st

from src.streamlit_app import ordo_api, ordo_analytics_api as read_api, ordo_methodology_api as api
from src.streamlit_app.data_ingestion_workspace import ERRORS, _write


def render_ordo_methodology(*, token, shell):
    if shell.get("product", {}).get("code") != "ORDO" or not shell.get("workspace"):
        return
    permissions = set(shell["product"].get("permission_codes", []))
    if not {"indicator.manage", "analysis.read"} <= permissions:
        return
    scope = dict(organization_id=str(shell["organization"]["id"]), workspace_id=str(shell["workspace"]["id"]))
    key = "_".join(scope.values()) + "_ordo_methodology"
    with st.expander("Autorstvo i odobrenje ORDO metodologije"):
        st.warning(
            "Globalni ORDO metodološki registar: novo ljudsko odobrenje povlači prethodnu VALIDATED verziju istog indikatora. Ne unosite privatne tenant ili lične podatke u metodološke reference."
        )
        with st.expander("Uputstvo za ORDO metodologiju i forecast"):
            st.markdown(
                (Path(__file__).resolve().parents[2] / "docs/help/ORDO-METHODOLOGY-WORKFLOWS-GUIDE.md").read_text()
            )
        if st.button("Učitaj / osveži ORDO metodološki registar", key=key + "_load"):
            st.session_state.pop(key + "_registry", None)
            st.session_state[key + "_generation"] = st.session_state.get(key + "_generation", 0) + 1
            try:
                st.session_state[key + "_registry"] = dict(
                    catalog=ordo_api.catalog(token, **scope), methods=read_api.methodologies(token, **scope)
                )
            except ERRORS as exc:
                st.error(str(exc))
        registry = st.session_state.get(key + "_registry")
        if registry is None:
            st.caption("Učitajte postojeći katalog i metodologije pre autorstva ili pregleda.")
            return
        key += "_g" + str(st.session_state.get(key + "_generation", 0))
        indicators = [x for x in registry["catalog"].get("indicators", []) if x.get("active", True)]
        if indicators:
            with st.form(key + "_create"):
                selected = st.selectbox(
                    "Indikator za novu ORDO metodologiju",
                    indicators,
                    format_func=lambda x: f"{x['code']} · {x.get('name_sr', '')}",
                )
                note = st.text_area("Autorska napomena ORDO metodologije", max_chars=5000)
                st.caption(
                    "direct_observation prenosi postojeću validiranu agregatnu opservaciju, ne izračunava novu formulu."
                )
                spatial_rule = st.selectbox(
                    "Opciona odobrena prostorna agregacija identiteta",
                    ["count", "sum", "mean", "min", "max"],
                    index=None,
                )
                st.caption(
                    "Prazno: nema ovlašćenog prostornog pravila. Izbor registruje samo postojeći ORDO-SPATIAL-AGGREGATION-v1 ugovor: validiran identitet/granice/CRS, bez GIS join-a, pondera ili kauzalnog efekta. Izvršenje je zaseban postupak."
                )
                confirmed = st.checkbox("Potvrđujem autorizovani ORDO metodološki DRAFT")
                submitted = st.form_submit_button("Registruj ORDO metodološki DRAFT")
            if submitted:
                _write(
                    lambda: api.create_methodology(
                        token, scope=scope, indicator_code=selected["code"], note=note, spatial_rule=spatial_rule
                    ),
                    confirmed=confirmed,
                )
        methods = registry["methods"]
        if not methods:
            st.info("Nema metodologija za pregled.")
            return
        chosen = st.selectbox(
            "ORDO metodologija za pregled",
            methods,
            format_func=lambda x: f"{x['indicator_code']} · v{x['version_no']} · {x['status']}",
            key=key + "_chosen",
        )
        st.dataframe(
            [
                dict(Polje=name, Vrednost=str(chosen.get(name, "—")))
                for name in [
                    "id",
                    "indicator_code",
                    "version_no",
                    "status",
                    "computation_type",
                    "methodology_note",
                    "source_requirements",
                    "validation_note",
                    "approved_at",
                    "retirement_note",
                ]
            ],
            hide_index=True,
            width="stretch",
        )
        status = chosen["status"]
        action = {"draft": "propose", "proposed": "validate", "validated": "retire"}.get(status)
        if action is None:
            st.caption("RETIRED ostaje istorijski dokaz; nema ponovnog odobrenja.")
            return
        with st.form(key + "_" + str(chosen["id"]) + "_" + status):
            fields = {}
            if action == "validate":
                fields["validation_note"] = st.text_area("Obrazloženje ljudskog ORDO odobrenja", max_chars=5000)
                st.warning(
                    "Odobrenje se odnosi na pregledanu metodologiju. Nije forecast, potvrda modelskih performansi ili institucionalni zaključak."
                )
            elif action == "retire":
                fields["retirement_note"] = st.text_area("Razlog povlačenja ORDO metodologije", max_chars=5000)
            confirmed = st.checkbox("Potvrđujem ORDO prelaz " + action.upper() + " pregledane verzije")
            submitted = st.form_submit_button(
                {
                    "propose": "Predloži ORDO PROPOSED",
                    "validate": "Odobri ORDO VALIDATED",
                    "retire": "Povuci ORDO RETIRED",
                }[action]
            )
        if submitted:
            _write(
                lambda: api.transition(token, scope=scope, record_id=chosen["id"], action=action, fields=fields),
                confirmed=confirmed,
            )
