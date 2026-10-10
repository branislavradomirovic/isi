"""Explicit existing SIMPA methodology and statistical contract authoring."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.domains.simpa.statistical_contracts import TARGET_SEMANTIC_FAMILIES
from src.streamlit_app import simpa_api, simpa_analytics_api as read_api, simpa_methodology_api as api
from src.streamlit_app.data_ingestion_workspace import ERRORS, _write

TEXT_FIELDS = {
    "purpose": "Svrha metodologije",
    "interpretation": "Tumačenje opservacije",
    "unit": "Jedinica mere",
    "scale": "Skala vrednosti",
    "eligible_aggregate_scope": "Dozvoljeni agregatni obuhvat",
    "time_aggregation": "Vremensko agregiranje",
    "geographic_aggregation": "Geografsko agregiranje",
    "missing_data_rule": "Pravilo nedostajućih podataka",
    "suppression_privacy_rule": "Pravilo privatnosti i potiskivanja",
    "quality_preconditions": "Preduslovi kvaliteta",
    "reference_dataset": "Referentni skup",
    "limitations": "Ograničenja metodologije",
}
SOURCE_FIELDS = [
    "indicator_code",
    "quality_status",
    "value_numeric",
    "value_text",
    "geography_code",
    "geography_label",
    "period_start",
    "period_end",
    "monitoring_cycle_id",
    "population_group",
]


def reference_cases(rows, indicator_code):
    """Blank channels stay absent; expected values are independently authored."""
    result = []
    for row in rows:
        clean = {key: (None if pd.isna(value) else value) for key, value in row.items()}
        if all(value is None or value == "" for value in clean.values()):
            continue
        result.append(
            dict(
                case_key=clean["case_key"],
                reference_record=dict(
                    indicator_code=indicator_code,
                    quality_status=clean["quality_status"],
                    value_numeric=clean["input_numeric"],
                    value_text=clean["input_text"],
                ),
                expected_result=dict(value_numeric=clean["expected_numeric"], value_text=clean["expected_text"]),
            )
        )
    return result


def _details(record, specification):
    st.dataframe(
        [dict(Polje=key, Vrednost=str(value)) for key, value in specification.items()], hide_index=True, width="stretch"
    )
    st.caption(
        f"ID: {record['id']} · v{record['version_no']} · {record['status']} · {record.get('contract_fingerprint', '')}"
    )


def _create_method(token, scope, indicators, key):
    if not indicators:
        st.info("Nema aktivnih indikatora u postojećem katalogu.")
        return
    with st.form(key):
        indicator = st.selectbox(
            "Indikator za novu metodologiju", indicators, format_func=lambda x: f"{x['code']} · {x.get('name_sr', '')}"
        )
        st.caption(
            "Postojeći computation_type = direct_observation: preuzimanje validirane agregatne opservacije; bez novih formula."
        )
        fields = {name: st.text_area(label, max_chars=5000) for name, label in TEXT_FIELDS.items()}
        required = st.multiselect("Obavezna izvorna polja", SOURCE_FIELDS)
        tolerance = st.number_input("Odobrena tolerancija referentne provere", min_value=0.0, value=None)
        note = st.text_area("Napomena autora metodologije", max_chars=5000)
        confirmed = st.checkbox("Potvrđujem autorizovani metodološki sadržaj novog DRAFT-a")
        submitted = st.form_submit_button("Registruj DRAFT metodologiju")
    if submitted:
        _write(
            lambda: api.create_methodology(
                token,
                scope=scope,
                unit_hint=indicator.get("unit_hint", ""),
                fields=dict(
                    indicator_code=indicator["code"],
                    methodology_note=note,
                    source_requirements={},
                    computation_spec={
                        **fields,
                        "required_source_fields": required,
                        "accepted_tolerance": tolerance,
                        "non_causal": True,
                    },
                ),
            ),
            confirmed=confirmed,
        )


def _lifecycle(token, scope, record, key, kind, *, passed=False):
    status = record["status"]
    if status == "retired":
        st.caption("RETIRED ostaje istorijski dokaz; ne može se ponovo odobriti ovim ekranom.")
        return
    action = "propose" if status == "draft" else "validate" if status == "proposed" else None
    if action == "validate" and kind == "methodologies" and not passed:
        st.info("Za VALIDATED je potreban PASSED suite_v1 za ovu metodologiju. Backend ponovo proverava dokaze.")
        action = None
    if action:
        with st.form(key + "_" + action):
            fields = {}
            if action == "validate":
                st.warning(
                    "Ljudsko odobrenje povlači prethodnu VALIDATED verziju u globalnom registru. PASSED ili rezultat modela nije institucionalno odobrenje."
                )
                fields["validation_note"] = st.text_area("Obrazloženje ljudskog odobrenja", max_chars=5000)
                if kind == "statistical-model-contracts":
                    fields["validation_evidence_reference"] = st.text_input(
                        "Referenca dokaza validacije", max_chars=2000
                    )
            confirmed = st.checkbox("Potvrđujem prelaz " + action.upper() + " ovog zapisa")
            submitted = st.form_submit_button("Predloži PROPOSED" if action == "propose" else "Odobri VALIDATED")
        if submitted:
            _write(
                lambda: api.transition(
                    token, scope=scope, record_id=record["id"], kind=kind, action=action, fields=fields
                ),
                confirmed=confirmed,
            )
    with st.form(key + "_retire"):
        reason = st.text_area("Razlog povlačenja verzije", max_chars=5000)
        confirmed = st.checkbox("Potvrđujem povlačenje ovog zapisa u RETIRED")
        submitted = st.form_submit_button("Povuci RETIRED")
    if submitted:
        _write(
            lambda: api.transition(
                token,
                scope=scope,
                record_id=record["id"],
                kind=kind,
                action="retire",
                fields=dict(retirement_note=reason),
            ),
            confirmed=confirmed,
        )


def _suite(token, scope, method, key):
    if method.get("reference_evidence_mode") != "suite_v1":
        st.caption("Istorijski legacy_inline dokaz zadržan je radi kompatibilnosti; novo autorstvo koristi suite_v1.")
        return
    if st.button("Učitaj / osveži referentne suite-ove", key=key + "_load"):
        st.session_state.pop(key + "_suites", None)
        st.session_state[key + "_generation"] = st.session_state.get(key + "_generation", 0) + 1
        try:
            st.session_state[key + "_suites"] = read_api.reference_suites(token, method["id"], **scope)
        except ERRORS as exc:
            st.error(str(exc))
    suites = st.session_state.get(key + "_suites", [])
    if suites:
        st.dataframe(
            [
                {
                    name: row.get(name)
                    for name in [
                        "id",
                        "version_no",
                        "status",
                        "reference_dataset_version",
                        "case_count",
                        "suite_fingerprint",
                        "result_fingerprint",
                    ]
                }
                for row in suites
            ],
            hide_index=True,
            width="stretch",
        )
    passed = any(x.get("status") == "passed" for x in suites)
    if method["status"] != "proposed":
        return passed
    if not passed:
        with st.form(key + "_create_g" + str(st.session_state.get(key + "_generation", 0))):
            st.caption(
                "Unesite odobrene agregatne referentne slučajeve i nezavisno očekivane izlaze. Nema automatskog popunjavanja ili tenant podataka."
            )
            dataset_version = st.text_input("Verzija referentnog skupa", max_chars=255)
            rows = st.data_editor(
                pd.DataFrame(
                    [
                        dict(
                            case_key=None,
                            quality_status=None,
                            input_numeric=None,
                            input_text=None,
                            expected_numeric=None,
                            expected_text=None,
                        )
                    ]
                ),
                num_rows="dynamic",
                hide_index=True,
                width="stretch",
                column_config={
                    "case_key": st.column_config.TextColumn("Oznaka slučaja", required=True),
                    "quality_status": st.column_config.SelectboxColumn(
                        "Kvalitet ulaza", options=["validated", "draft", "rejected"], required=True
                    ),
                    "input_numeric": st.column_config.NumberColumn("Numerički ulaz"),
                    "input_text": st.column_config.TextColumn("Tekstualni ulaz"),
                    "expected_numeric": st.column_config.NumberColumn("Očekivani numerički izlaz"),
                    "expected_text": st.column_config.TextColumn("Očekivani tekstualni izlaz"),
                },
            )
            confirmed = st.checkbox("Potvrđujem referentne slučajeve i nezavisno očekivane rezultate")
            submitted = st.form_submit_button("Registruj referentni suite")
        if submitted:
            _write(
                lambda: api.create_suite(
                    token,
                    scope=scope,
                    methodology_id=method["id"],
                    fields=dict(
                        reference_dataset_version=dataset_version,
                        cases=reference_cases(rows.to_dict("records"), method["indicator_code"]),
                    ),
                ),
                confirmed=confirmed,
            )
        pending = [x for x in suites if x.get("status") == "not_run"]
        if pending:
            with st.form(key + "_run_g" + str(st.session_state.get(key + "_generation", 0))):
                selected = st.selectbox(
                    "Referentni suite za izvršenje", pending, format_func=lambda x: f"v{x['version_no']} · {x['id']}"
                )
                st.dataframe(selected.get("cases", []), hide_index=True, width="stretch")
                confirmed = st.checkbox("Potvrđujem determinističko izvršenje izabranog referentnog suite-a")
                submitted = st.form_submit_button("Izvrši referentni suite")
            if submitted:
                _write(
                    lambda: api.run_suite(token, scope=scope, methodology_id=method["id"], suite_id=selected["id"]),
                    confirmed=confirmed,
                )
    return passed


def _statistical(token, scope, methods, key):
    eligible = [x for x in methods if x["status"] == "validated"]
    if not eligible:
        st.info("Statistički ugovor zahteva trenutno VALIDATED ciljnu metodologiju.")
        return
    # Semantic selection precedes the form so the binary-only field updates visibly.
    semantic = st.selectbox(
        "Semantika statističkog cilja", list(TARGET_SEMANTIC_FAMILIES), index=None, key=key + "_semantic"
    )
    if semantic is None:
        return
    family = TARGET_SEMANTIC_FAMILIES[semantic]
    with st.form(key + "_" + semantic):
        target = st.selectbox(
            "VALIDATED ciljna metodologija",
            eligible,
            format_func=lambda x: f"{x['indicator_code']} · v{x['version_no']} · {x['contract_fingerprint']}",
        )
        st.caption("Dozvoljeni model: " + family + "; agregatni nivo, bez kauzalne interpretacije.")
        analysis_key = st.text_input("Oznaka statističke analize", max_chars=140)
        features = st.text_area("Feature polja (jedno po redu)")
        confidence = st.number_input(
            "Odobreni nivo pouzdanosti (0 < vrednost < 1)", min_value=0.0, max_value=1.0, value=None
        )
        covariance = st.selectbox("Tip kovarijanse", ["nonrobust", "HC3"], index=None)
        purpose = st.text_area("Svrha statističke analize", max_chars=5000)
        limitations = st.text_area("Ograničenja statističke analize", max_chars=5000)
        positive = (
            st.text_area("Definicija pozitivnog sistemskog ishoda", max_chars=1000)
            if semantic == "binary_system_state"
            else None
        )
        st.caption(
            "target=value_numeric; complete_case; scaling=none; intercept=true; aggregate_only=true; non_causal=true. Nema klasifikacionog praga, građanskog skora ili automatskog championa."
        )
        confirmed = st.checkbox("Potvrđujem autorizovani statistički DRAFT i ciljnu metodologiju")
        submitted = st.form_submit_button("Registruj statistički DRAFT")
    if submitted:
        _write(
            lambda: api.create_statistical(
                token,
                scope=scope,
                fields=dict(
                    indicator_code=target["indicator_code"],
                    analysis_key=analysis_key,
                    target_semantic=semantic,
                    model_family=family,
                    feature_fields=features.splitlines(),
                    confidence_level=confidence,
                    covariance_type=covariance,
                    purpose=purpose,
                    limitations=limitations,
                    positive_outcome_definition=positive,
                ),
            ),
            confirmed=confirmed,
        )


def render_methodology_authoring(*, token, shell):
    if shell.get("product", {}).get("code") != "SIMPA" or not shell.get("workspace"):
        return
    permissions = set(shell["product"].get("permission_codes", []))
    if not {"analysis.read", "indicator.manage"} <= permissions:
        return
    scope = dict(organization_id=str(shell["organization"]["id"]), workspace_id=str(shell["workspace"]["id"]))
    key = "_".join(scope.values()) + "_simpa_methodology"
    with st.expander("Autorstvo i odobrenje SIMPA metodologije"):
        st.warning(
            "Ovo je globalni SIMPA metodološki registar. Promene odobrenih verzija utiču na naredne proračune drugih ovlašćenih SIMPA workspace-ova. Referentni podaci moraju biti odobreni za taj registar; ne unosite privatne tenant ili lične podatke."
        )
        with st.expander("Uputstvo za metodološki postupak"):
            st.markdown(
                (Path(__file__).resolve().parents[2] / "docs/help/SIMPA-METHODOLOGY-WORKFLOWS-GUIDE.md").read_text()
            )
        if st.button("Učitaj / osveži metodološki registar", key=key + "_load"):
            st.session_state.pop(key + "_registry", None)
            st.session_state[key + "_generation"] = st.session_state.get(key + "_generation", 0) + 1
            try:
                st.session_state[key + "_registry"] = dict(
                    catalog=simpa_api.catalog(token, **scope),
                    methods=read_api.methodologies(token, **scope),
                    contracts=read_api.statistical_model_contracts(token, **scope),
                )
            except ERRORS as exc:
                st.error(str(exc))
        registry = st.session_state.get(key + "_registry")
        if registry is None:
            st.caption("Učitajte postojeći katalog pre autorstva ili odobrenja.")
            return
        key += "_g" + str(st.session_state.get(key + "_generation", 0))
        with st.expander("Nova direct_observation metodologija"):
            _create_method(
                token,
                scope,
                [x for x in registry["catalog"].get("indicators", []) if x.get("active", True)],
                key + "_create",
            )
        methods = registry["methods"]
        if methods:
            with st.expander("Referentni suite i životni ciklus metodologije"):
                method = st.selectbox(
                    "Metodologija za pregled",
                    methods,
                    format_func=lambda x: f"{x['indicator_code']} · v{x['version_no']} · {x['status']}",
                    key=key + "_method",
                )
                _details(method, method.get("computation_spec", {}))
                method_key = key + "_" + str(method["id"])
                passed = _suite(token, scope, method, method_key + "_suite")
                _lifecycle(
                    token,
                    scope,
                    method,
                    method_key + "_sg" + str(st.session_state.get(method_key + "_suite_generation", 0)),
                    "methodologies",
                    passed=passed,
                )
        with st.expander("Novi statistički metodološki ugovor"):
            _statistical(token, scope, methods, key + "_stat_create")
        if registry["contracts"]:
            with st.expander("Životni ciklus statističkog ugovora"):
                contract = st.selectbox(
                    "Statistički ugovor za pregled",
                    registry["contracts"],
                    format_func=lambda x: f"{x['analysis_key']} · v{x['version_no']} · {x['status']}",
                    key=key + "_contract",
                )
                _details(contract, contract.get("contract", {}))
                _lifecycle(token, scope, contract, key + "_" + str(contract["id"]), "statistical-model-contracts")
