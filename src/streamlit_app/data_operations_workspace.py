"""Permission-bound existing backfill/replay/dead-letter recovery forms."""

import base64
from pathlib import Path

import streamlit as st

from src.streamlit_app import data_operations_api as api
from src.streamlit_app import data_ingestion_api as contracts_api
from src.streamlit_app.data_ingestion_workspace import binding_chain, _binding_key, _write, ERRORS


def replay_candidates(runs, policies):
    allowed = {str(x["id"]) for x in policies if x.get("backfill_contract", {}).get("replay_allowed")}
    return [
        x
        for x in runs
        if x.get("status") in {"SUCCEEDED", "FAILED"} and str(x.get("operational_policy_version_id")) in allowed
    ]


def _backfill(token, params, chain, key):
    if not all(chain.values()) or not chain["operations"].get("backfill_contract", {}).get("backfill_allowed"):
        st.caption("Backfill zahteva aktivan usaglašen lanac i politiku koja ga dozvoljava.")
        return
    with st.form(_binding_key(key, chain, tuple(contracts_api.RESOURCES))):
        uploaded = st.file_uploader("Datoteka backfill obrade", type=["csv", "json", "xlsx"], max_upload_size=16)
        identity = st.text_input("Backfill idempotency ključ", max_chars=200)
        start = st.text_input("Početni kursor prozora", max_chars=1000)
        end = st.text_input("Krajnji kursor prozora", max_chars=1000)
        observed = st.text_input("Backfill vreme opažanja (ISO sa UTC pomakom, opciono)", max_chars=80)
        confirmed = st.checkbox("Potvrđujem backfill datoteku, prozor i aktivne ugovore")
        submitted = st.form_submit_button("Pokreni backfill")
    if submitted:
        if uploaded is None:
            st.error("Izaberite datoteku.")
            return
        _write(
            lambda: api.recover(
                token,
                **params,
                operation="backfill",
                fields=dict(
                    connector_contract_version_id=str(chain["connector"]["id"]),
                    schema_mapping_version_id=str(chain["mapping"]["id"]),
                    idempotency_key=identity,
                    filename=uploaded.name,
                    content_type=uploaded.type or "application/octet-stream",
                    content_base64=base64.b64encode(uploaded.getvalue()).decode("ascii"),
                    source_observed_at=api.observed_time(observed),
                    window_start_cursor=start,
                    window_end_cursor=end,
                ),
            ),
            confirmed=confirmed,
        )


def _replay(token, params, runs, policies, key):
    candidates = replay_candidates(runs, policies)
    if not candidates:
        st.caption("Nema završene obrade čija vezana politika dozvoljava replay.")
        return
    run = st.selectbox(
        "Završena obrada za replay",
        candidates,
        format_func=lambda x: f"#{x['run_no']} · {x['status']} · {x['id']}",
        key=key + "_select",
    )
    with st.form(key + "_" + str(run["id"])):
        st.caption(
            "Replay koristi originalni sadržaj i pinovane ugovore, bez pomeranja forward kursora. Backend ponovo proverava dostupnost i politiku."
        )
        identity = st.text_input("Replay idempotency ključ", max_chars=200)
        confirmed = st.checkbox("Potvrđujem replay izabrane obrade")
        submitted = st.form_submit_button("Pokreni replay")
    if submitted:
        _write(
            lambda: api.recover(
                token, **params, operation="replay", artifact_id=str(run["id"]), fields=dict(idempotency_key=identity)
            ),
            confirmed=confirmed,
        )


def _dead_letter(token, params, rows, key, mutable):
    st.dataframe(
        [
            {
                field: x.get(field, "—")
                for field in ["id", "ingestion_run_id", "status", "reason_code", "error_category", "replacement_run_id"]
            }
            for x in rows
        ],
        hide_index=True,
        width="stretch",
    )
    open_rows = [x for x in rows if x["status"] == "OPEN"]
    if not mutable or not open_rows:
        st.caption("Nema dostupne OPEN stavke za izmenu ili nemate governance ovlašćenje.")
        return
    chosen = st.selectbox(
        "Otvorena dead-letter stavka",
        open_rows,
        format_func=lambda x: f"{x['id']} · {x['reason_code']}",
        key=key + "_selection",
    )
    artifact_key = key + "_" + str(chosen["id"])
    with st.form(artifact_key + "_requeue"):
        identity = st.text_input("Requeue idempotency ključ", max_chars=200)
        confirmed = st.checkbox("Potvrđujem kontrolisani replay dead-letter stavke")
        submitted = st.form_submit_button("Vrati stavku u obradu")
    if submitted:
        _write(
            lambda: api.recover(
                token,
                **params,
                operation="requeue",
                artifact_id=str(chosen["id"]),
                fields=dict(idempotency_key=identity),
            ),
            confirmed=confirmed,
        )
    with st.form(artifact_key + "_resolve"):
        status = st.selectbox("Ishod pregleda stavke", ["RESOLVED", "DISCARDED"])
        note = st.text_area("Obrazloženje zatvaranja", max_chars=1000)
        st.caption("DISCARDED čuva evidenciju odluke; ne briše podatke i ne prihvata odbijeni izlaz.")
        confirmed = st.checkbox("Potvrđujem ishod pregleda i obrazloženje")
        submitted = st.form_submit_button("Zatvori dead-letter stavku")
    if submitted:
        _write(
            lambda: api.recover(
                token,
                **params,
                operation="resolve",
                artifact_id=str(chosen["id"]),
                fields=dict(status=status, resolution_note=note),
            ),
            confirmed=confirmed,
        )


def render_ingestion_operations(*, token, shell, source_id, runs):
    permissions = set(shell["product"].get("permission_codes", []))
    if "data.read" not in permissions or not shell.get("workspace"):
        return
    scope = dict(
        organization_id=str(shell["organization"]["id"]),
        product_code=shell["product"]["code"],
        workspace_id=str(shell["workspace"]["id"]),
    )
    params = dict(source_id=source_id, scope=scope)
    key = "_".join(scope.values()) + "_" + source_id + "_operations"
    with st.expander("Uputstvo: oporavak kontrolisane obrade"):
        st.markdown((Path(__file__).resolve().parents[2] / "docs/help/ISI-INGESTION-RECOVERY-GUIDE.md").read_text())
    if st.button("Učitaj / osveži operativni pregled", key=key + "_load"):
        # Widget drafts and approvals are never inherited by a fresh operational view.
        for name in list(st.session_state):
            if name.startswith(key) and name not in {key + "_load", key + "_generation"}:
                del st.session_state[name]
        st.session_state[key + "_generation"] = st.session_state.get(key + "_generation", 0) + 1
        try:
            contracts = {
                resource: contracts_api.list_contracts(token, **params, resource=resource)
                for resource in contracts_api.RESOURCES
            }
            rows = api.list_dead_letters(token, **params)
            st.session_state[key + "_view"] = dict(contracts=contracts, rows=rows)
        except ERRORS as exc:
            st.error(str(exc))
    view = st.session_state.get(key + "_view")
    if not view:
        st.caption("Učitajte pregled za backfill, replay i dead-letter. Nijedna obrada se ne pokreće samim pregledom.")
        return
    key += "_g" + str(st.session_state.get(key + "_generation", 0))
    if "data.upload" in permissions:
        with st.expander("Backfill prozora"):
            _backfill(token, params, binding_chain(view["contracts"]), key + "_backfill")
        with st.expander("Replay završene obrade"):
            _replay(token, params, runs, view["contracts"]["operations"], key + "_replay")
    with st.expander("Dead-letter pregled i odluka"):
        _dead_letter(token, params, view["rows"], key + "_dead", "data.governance.manage" in permissions)
