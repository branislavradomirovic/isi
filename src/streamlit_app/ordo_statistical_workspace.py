"""Existing metadata authoring/lifecycle, explicitly separate from model fitting."""

from pathlib import Path

import pandas as pd
from pydantic import ValidationError
import streamlit as st

from src.domains.ordo.statistical_contracts import CROSS_SECTIONAL_FAMILIES, PANEL_FAMILIES, RESPONSE_FAMILIES
from src.streamlit_app import ordo_statistical_api as api, ordo_analytics_api as read_api
from src.streamlit_app.data_ingestion_workspace import ERRORS

FEATURE_COLUMNS = ["feature_key", "role", "source_field", "version_identity", "transformation", "missing_rule"]


def feature_rows(rows):
    return [{key: (None if pd.isna(value) else value) for key, value in row.items()} for row in rows]


def review(row):
    st.warning(
        "SPECIFIKACIJA / METAPODACI — fitting NOT_IMPLEMENTED, numerical_results NOT_PRESENT. VALIDATED nije potvrda koeficijenata, SHAP-a ili performansi modela."
    )
    definition = row.get("definition") or {}
    keys = [
        "analysis_key",
        "purpose",
        "target_indicator_code",
        "target_semantic",
        "analysis_structure",
        "model_family",
        "response_family",
        "analysis_window_start",
        "analysis_window_end",
        "analysis_as_of",
        "non_causal",
        "automatic_policy_recommendation",
    ]
    st.dataframe([dict(Polje=k, Vrednost=str(definition.get(k, "—"))) for k in keys], hide_index=True, width="stretch")
    st.markdown("**Feature definicije**")
    st.dataframe(definition.get("features", []), hide_index=True, width="stretch")
    for key, label in [
        ("assumptions", "Pretpostavke"),
        ("required_diagnostics", "Potrebna dijagnostika"),
        ("limitations", "Ograničenja"),
    ]:
        st.markdown("**" + label + "**")
        for item in definition.get(key, []):
            st.write("• " + str(item))
    st.markdown("**Verzija, provenance i ljudski trag**")
    st.dataframe(
        [dict(Polje=k, Vrednost=str(v)) for k, v in row.items() if k != "definition"], hide_index=True, width="stretch"
    )
    st.caption(
        "Pregled je istorijska specifikacija. Backend ponovo proverava metodologiju i ulaz pri PROPOSED/VALIDATED; numerički rezultati nisu dostupni."
    )


def _write(callback, state):
    try:
        result = callback()
        st.session_state.pop(state + "_registry", None)
        st.session_state[state + "_generation"] = st.session_state.get(state + "_generation", 0) + 1
        st.session_state[state + "_receipt"] = str(result["id"])
        st.rerun()
    except ValidationError:
        st.error("Proverite obavezna polja, datume, feature definicije i semantiku. Zahtev nije poslat.")
    except ValueError as exc:
        st.error(str(exc))
    except ERRORS as exc:
        st.error(str(exc))
        st.warning("Osvežite stanje pre ponavljanja; promena je mogla biti registrovana.")


def render_ordo_statistical(*, token, shell):
    if shell.get("product", {}).get("code") != "ORDO" or not shell.get("workspace"):
        return
    permissions = set(shell["product"].get("permission_codes", []))
    if "analysis.read" not in permissions:
        return
    mutable = "indicator.manage" in permissions
    scope = dict(organization_id=str(shell["organization"]["id"]), workspace_id=str(shell["workspace"]["id"]))
    state = "_".join(scope.values()) + "_ordo_statistical"
    with st.expander("ORDO statističke specifikacije i ljudski pregled"):
        st.caption(
            "Postojeći statistički ugovor je specifikacija bez fitting-a i numeričkih rezultata; nema automatskog modelskog ili institucionalnog odobrenja."
        )
        with st.expander("Uputstvo za ORDO statističke specifikacije"):
            st.markdown(
                (Path(__file__).resolve().parents[2] / "docs/help/ORDO-STATISTICAL-SPECIFICATION-GUIDE.md").read_text()
            )
        if st.session_state.get(state + "_receipt"):
            st.success("Registrovana promena ORDO specifikacije: " + st.session_state[state + "_receipt"])
        page = st.number_input(
            "Stranica ORDO specifikacija (100 po stranici)",
            min_value=1,
            max_value=1001,
            value=1,
            step=1,
            key=state + "_page",
        )
        if st.button("Učitaj / osveži ORDO statistički registar", key=state + "_load"):
            st.session_state.pop(state + "_registry", None)
            st.session_state[state + "_generation"] = st.session_state.get(state + "_generation", 0) + 1
            try:
                st.session_state[state + "_registry"] = dict(
                    contracts=api.list_contracts(token, scope=scope, offset=(page - 1) * 100),
                    page=page,
                    methods=read_api.methodologies(token, **scope) if mutable else [],
                    runs=read_api.runs(token, **scope) if mutable else [],
                )
            except ERRORS as exc:
                st.error(str(exc))
        registry = st.session_state.get(state + "_registry")
        if registry is None or registry["page"] != page:
            st.info("Učitajte izabranu stranicu registra pre pregleda ili autorstva.")
            return
        key = state + "_g" + str(st.session_state.get(state + "_generation", 0))
        if registry["contracts"].get("truncated"):
            st.caption("Postoje naredne stavke: izaberite sledeću stranicu i učitajte registar.")
        if mutable:
            methods = [x for x in registry["methods"] if x.get("status") == "validated"]
            runs = [
                x
                for x in registry["runs"]
                if x.get("status") == "completed"
                and x.get("analytical_artifact_type") in {"ANALYTICAL_SNAPSHOT", "ANALYTICAL_FEATURE_VERSION"}
            ]
            with st.expander("Novi ORDO statistički DRAFT"):
                if not methods or not runs:
                    st.info("Potrebni VALIDATED ciljna metodologija i completed governed run.")
                else:
                    _author(token, scope, state, key, methods, runs)
        rows = registry["contracts"]["items"]
        if not rows:
            st.info("Nema statističkih specifikacija na ovoj stranici.")
            return
        row = st.selectbox(
            "ORDO statistička specifikacija za pregled",
            rows,
            index=None,
            key=key + "_chosen",
            format_func=lambda x: f"{x['analysis_key']} · v{x['version_no']} · {x['status']}",
        )
        if row is None:
            return
        review(row)
        action = {"draft": "propose", "proposed": "validate", "validated": "retire"}.get(row["status"])
        if not mutable or action is None:
            return
        with st.form(key + "_" + row["id"] + "_" + row["status"] + "_" + row["contract_fingerprint"]):
            fields = {}
            if action == "validate":
                st.warning(
                    "VALIDATED odobrava samo specifikaciju; zamenjuje prethodnu validiranu verziju istog analysis_key u ovom workspace-u."
                )
                fields["validation_note"] = st.text_area("Obrazloženje ljudskog pregleda specifikacije", max_chars=5000)
                fields["validation_evidence_reference"] = st.text_input(
                    "Referenca dokaza pregleda specifikacije", max_chars=500
                )
            elif action == "retire":
                fields["retirement_note"] = st.text_area(
                    "Razlog povlačenja ORDO statističke specifikacije", max_chars=5000
                )
            confirmed = st.checkbox("Potvrđujem pregledani statistički prelaz " + action.upper())
            submitted = st.form_submit_button(
                {
                    "propose": "Predloži ORDO statistički PROPOSED",
                    "validate": "Odobri ORDO statistički VALIDATED",
                    "retire": "Povuci ORDO statistički RETIRED",
                }[action]
            )
        if submitted:
            if confirmed:
                _write(lambda: api.transition(token, scope=scope, row=row, action=action, fields=fields), state)
            else:
                st.error("Označite potvrdu pregledane verzije pre slanja.")


def _author(token, scope, state, key, methods, runs):
    method = st.selectbox(
        "VALIDATED metodologija ORDO statističkog cilja",
        methods,
        index=None,
        key=key + "_method",
        format_func=lambda x: f"{x['indicator_code']} · v{x['version_no']}",
    )
    run = st.selectbox(
        "Governed run ORDO statističke specifikacije", runs, index=None, key=key + "_run", format_func=lambda x: x["id"]
    )
    semantic = st.selectbox(
        "ORDO statistička semantika", list(CROSS_SECTIONAL_FAMILIES), index=None, key=key + "_semantic"
    )
    structure = st.selectbox("ORDO struktura analize", ["cross_sectional", "panel"], index=None, key=key + "_structure")
    if not all([method, run, semantic, structure]):
        return
    families = sorted(CROSS_SECTIONAL_FAMILIES[semantic] if structure == "cross_sectional" else PANEL_FAMILIES)
    with st.form(key + "_" + method["id"] + "_" + run["id"] + "_" + semantic + "_" + structure):
        analysis_key = st.text_input("Oznaka ORDO statističke analize", max_chars=140)
        purpose = st.text_area("Svrha ORDO statističke analize", max_chars=5000)
        family = st.selectbox("Predložena ORDO modelska porodica", families, index=None)
        response = st.selectbox("ORDO response porodica", sorted(RESPONSE_FAMILIES[semantic]), index=None)
        features = st.data_editor(
            pd.DataFrame(columns=FEATURE_COLUMNS),
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "role": st.column_config.SelectboxColumn(
                    options=["predictor", "control", "offset", "exposure"], required=True
                ),
                "transformation": st.column_config.SelectboxColumn(
                    options=["none", "log1p", "standardize", "categorical"], required=True
                ),
                "missing_rule": st.column_config.SelectboxColumn(
                    options=["complete_case", "exclude", "missing_indicator"], required=True
                ),
            },
        )
        start = st.date_input("Početak ORDO statističkog prozora", value=None)
        end = st.date_input("Kraj ORDO statističkog prozora", value=None)
        asof = st.date_input("ORDO statistički as-of", value=None)
        assumptions = st.text_area("ORDO pretpostavke (jedna po redu)", max_chars=5000)
        diagnostics = st.text_area("ORDO potrebna dijagnostika (jedna po redu)", max_chars=5000)
        limitations = st.text_area("ORDO ograničenja (jedno po redu)", max_chars=5000)
        st.caption(
            "Definicije features su metodološki metapodaci, ne fitting. Verzije izvora/polja morate pregledati; nema izmišljene selekcije modela, kauzalnog efekta ili preporuke."
        )
        confirmed = st.checkbox("Potvrđujem autorizovani ORDO statistički DRAFT i pregledanu metodologiju/ulaz")
        submitted = st.form_submit_button("Registruj ORDO statistički DRAFT")
    if submitted:
        if not confirmed:
            st.error("Označite potvrdu pre slanja.")
            return
        definition = dict(
            analysis_key=analysis_key,
            purpose=purpose,
            target_indicator_code=method["indicator_code"],
            target_semantic=semantic,
            analysis_structure=structure,
            model_family=family,
            response_family=response,
            features=feature_rows(features.to_dict("records")),
            analysis_window_start=start,
            analysis_window_end=end,
            analysis_as_of=asof,
            assumptions=assumptions.splitlines(),
            required_diagnostics=diagnostics.splitlines(),
            limitations=limitations.splitlines(),
        )
        _write(
            lambda: api.create(
                token,
                scope=scope,
                analytics_run_id=run["id"],
                reviewed_methodology_id=method["id"],
                definition=definition,
            ),
            state,
        )
