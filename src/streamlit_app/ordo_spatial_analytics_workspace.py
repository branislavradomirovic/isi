"""Explicit identity aggregation; existing GIS viewer owns current numerical truth."""

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError
import streamlit as st

from src.domains.ordo.spatial_processing import OrdoSpatialAggregationContractV1
from src.streamlit_app import ordo_analytics_api as read_api, spatial_api, ordo_spatial_analytics_api as api
from src.streamlit_app.data_ingestion_workspace import ERRORS


def eligible(registry):
    methods = []
    for method in registry["methods"]:
        if method.get("status") != "validated":
            continue
        try:
            contract = OrdoSpatialAggregationContractV1.model_validate(
                (method.get("source_requirements") or {}).get("spatial_aggregation")
            )
        except (ValidationError, TypeError):
            continue
        methods.append({**method, "spatial_rule": contract.aggregation_rule})
    runs = [
        x
        for x in registry["runs"]
        if x.get("status") == "completed"
        and x.get("analytical_artifact_type") in {"ANALYTICAL_SNAPSHOT", "ANALYTICAL_FEATURE_VERSION"}
    ]
    units = [x for x in registry["units"] if x.get("lifecycle_status") == "validated"]
    return methods, runs, units


def render_ordo_spatial_aggregation(*, token, shell):
    if shell.get("product", {}).get("code") != "ORDO" or not shell.get("workspace"):
        return
    permissions = set(shell["product"].get("permission_codes", []))
    if not {"analysis.read", "data.read", "analysis.run"} <= permissions:
        return
    scope = dict(organization_id=str(shell["organization"]["id"]), workspace_id=str(shell["workspace"]["id"]))
    state = "_".join(scope.values()) + "_ordo_spatial_aggregation"
    receipt = st.session_state.get(state + "_receipt")
    if receipt:
        st.success(f"Registrovana ORDO prostorna agregacija: {receipt['id']}")
        st.caption(
            "Podaci → GIS: osvežite validiranu geometriju povezane jedinice i rezultate. Registracija nije potvrda trenutne numeričke dostupnosti; datum geometrije nije period opservacije."
        )
    with st.expander("ORDO prostorna agregacija validiranog identiteta"):
        st.caption(
            "Deskriptivna agregacija postojećih podataka; nije GIS join, ponderisanje, forecast ili kauzalni efekat."
        )
        with st.expander("Uputstvo za ORDO prostornu agregaciju"):
            st.markdown(
                (Path(__file__).resolve().parents[2] / "docs/help/ORDO-SPATIAL-AGGREGATION-GUIDE.md").read_text()
            )
        if st.button("Učitaj / osveži ORDO prostorne ulaze", key=state + "_load"):
            st.session_state.pop(state + "_registry", None)
            st.session_state[state + "_generation"] = st.session_state.get(state + "_generation", 0) + 1
            try:
                response = spatial_api.call(token, "ORDO", "units", **scope)
                st.session_state[state + "_registry"] = dict(
                    methods=read_api.methodologies(token, **scope),
                    runs=read_api.runs(token, **scope),
                    units=response["items"],
                    truncated=response.get("truncated", False),
                )
            except ERRORS as exc:
                st.error(str(exc))
        registry = st.session_state.get(state + "_registry")
        if registry is None:
            st.info("Učitajte metodologije, governed izvršenja i prostorne jedinice pre izbora.")
            return
        if registry.get("truncated"):
            st.warning("Prikazan je ograničen spisak jedinica. Nedostajuća jedinica nije dokaz da ne postoji.")
        methods, runs, units = eligible(registry)
        if not methods or not runs or not units:
            st.info(
                "Potrebni su VALIDATED metodologija sa prostornim ugovorom, completed governed run i VALIDATED jedinica."
            )
            return
        key = state + "_g" + str(st.session_state.get(state + "_generation", 0))
        method = st.selectbox(
            "Metodologija prostorne agregacije",
            methods,
            index=None,
            key=key + "_method",
            format_func=lambda x: f"{x['indicator_code']} · v{x['version_no']} · {x['spatial_rule']}",
        )
        run = st.selectbox(
            "Governed izvršenje za prostornu agregaciju",
            runs,
            index=None,
            key=key + "_run",
            format_func=lambda x: f"{x['id']} · {x['analytical_artifact_type']}",
        )
        unit = st.selectbox(
            "Validirana ORDO prostorna jedinica",
            units,
            index=None,
            key=key + "_unit",
            format_func=lambda x: f"{x['spatial_unit_key']} · {x['boundary_version']} · {x['crs']}",
        )
        if not all([method, run, unit]):
            st.caption("Izaberite sve tri stavke. Nema automatski potvrđenog izbora.")
            return
        reviewed = dict(methodology=method, run=run, unit=unit)
        binding = hashlib.sha256(json.dumps(reviewed, sort_keys=True, default=str).encode()).hexdigest()
        st.dataframe(
            [
                dict(Polje=name, Vrednost=str(value))
                for name, value in {
                    "Indikator": method["indicator_code"],
                    "Metodologija": method["id"],
                    "Verzija": method["version_no"],
                    "Pravilo": method["spatial_rule"],
                    "Governed run": run["id"],
                    "Jedinica": unit["id"],
                    "Identitet": unit["spatial_unit_key"],
                    "Tip": unit["spatial_unit_type"],
                    "Granice": unit["boundary_version"],
                    "CRS": unit["crs"],
                }.items()
            ],
            hide_index=True,
            width="stretch",
        )
        st.warning(
            "Backend ponovo proverava metodologiju, ulaz, kvalitet i potpuno podudaranje identiteta/granica/CRS. Pregledani izbor ne zaobilazi te provere."
        )
        confirmed = st.checkbox(
            "Potvrđujem izvršenje pregledane ORDO prostorne agregacije", key=key + binding + "_confirm"
        )
        if st.button("Izvrši ORDO prostornu agregaciju", key=key + binding + "_execute", disabled=not confirmed):
            try:
                result = api.create(
                    token,
                    scope=scope,
                    analytics_run_id=run["id"],
                    reviewed_methodology_id=method["id"],
                    indicator_code=method["indicator_code"],
                    target_spatial_unit_id=unit["id"],
                )
                st.session_state.pop(state + "_registry", None)
                st.session_state[state + "_generation"] = st.session_state.get(state + "_generation", 0) + 1
                st.session_state[state + "_receipt"] = result
                st.rerun()
            except ValidationError:
                st.error("Proverite izabrane identifikatore. Zahtev nije poslat.")
            except ERRORS as exc:
                st.error(str(exc))
                st.warning("Osvežite GIS pregled pre ponovnog slanja; izvršenje je moglo biti registrovano.")
