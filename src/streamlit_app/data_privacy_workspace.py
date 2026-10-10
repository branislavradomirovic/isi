"""Retention, holds, anonymization evidence and governed download controls."""

from pathlib import Path

import streamlit as st

from src.platform.data.governance import DataClassification, PrivacyCategory
from src.streamlit_app import data_privacy_api as api
from src.streamlit_app import data_api
from src.streamlit_app.data_ingestion_workspace import _write, ERRORS


def _policy(token, scope, key):
    with st.form(key):
        code = st.text_input("Oznaka politike čuvanja", max_chars=120)
        version = st.number_input("Verzija politike čuvanja", min_value=1, value=None)
        name = st.text_input("Naziv politike čuvanja", max_chars=240)
        days = st.number_input("Rok čuvanja (dani, prazno za neodređen rok)", min_value=0, value=None)
        tombstone = st.number_input("Rok tombstone evidencije (dani, opciono)", min_value=0, value=None)
        no_delete = st.checkbox("Bez automatskog brisanja", value=True)
        manual = st.checkbox("Obavezan ljudski pregled", value=True)
        archive = st.checkbox("Politika traži arhivu pre purge-a", value=True)
        reference = st.text_area("Referenca odobrene politike čuvanja", max_chars=1000)
        st.caption(
            "Nema automatskog arhiviranja ili brisanja. Rokove određuje ovlašćeni vlasnik; sistem ih ne izmišlja."
        )
        confirmed = st.checkbox("Potvrđujem odobrenu politiku i rokove čuvanja")
        submitted = st.form_submit_button("Registruj politiku čuvanja")
    if submitted:
        _write(
            lambda: api.create_policy(
                token,
                scope=scope,
                fields=dict(
                    policy_code=code,
                    version_no=version,
                    name=name,
                    retention_days=days,
                    tombstone_retention_days=tombstone,
                    no_auto_delete=no_delete,
                    manual_review_required=manual,
                    archive_before_purge=archive,
                    reference_text=reference,
                ),
            ),
            confirmed=confirmed,
        )


def _retention(token, scope, version, state, key, mutable):
    st.dataframe(
        [
            {
                name: state.get(name, "—")
                for name in [
                    "retention_start_at",
                    "retention_due_at",
                    "hold_active",
                    "hold_reason_ref",
                    "purge_status",
                    "revision",
                    "purge_result",
                    "tombstone_checksum",
                ]
            }
        ],
        hide_index=True,
        width="stretch",
    )
    if not mutable or version.get("content_state") != "AVAILABLE":
        return
    key += "_" + str(state["revision"])
    action = "release" if state["hold_active"] else "hold"
    with st.form(key + "_hold"):
        reason = st.text_input("Referenca zabrane brisanja (hold)", max_chars=500) if action == "hold" else None
        confirmed = st.checkbox("Potvrđujem postavljanje hold-a" if action == "hold" else "Potvrđujem ukidanje hold-a")
        submitted = st.form_submit_button("Postavi hold" if action == "hold" else "Ukloni hold")
    if submitted:
        _write(
            lambda: api.retention_action(
                token,
                version_id=str(version["id"]),
                scope=scope,
                revision=state["revision"],
                action=action,
                reason=reason,
            ),
            confirmed=confirmed,
        )
    st.info(
        "Hold sprečava purge. Fizičko brisanje je zaseban operativni postupak sa retention i step-up proverama. Ovaj ekran ga ne izvršava; nema potvrđenog automatskog arhiviranja."
    )
    if not state["hold_active"] and state["purge_status"] in {"NONE", "FAILED"}:
        with st.form(key + "_request"):
            st.caption(
                "Zahtev za pregled purge-a samo menja evidenciju. Backend proverava da je rok istekao i da politika dozvoljava postupak."
            )
            confirmed = st.checkbox("Potvrđujem zahtev za operativni pregled purge-a ove verzije")
            submitted = st.form_submit_button("Zatraži pregled purge-a")
        if submitted:
            _write(
                lambda: api.retention_action(
                    token, version_id=str(version["id"]), scope=scope, revision=state["revision"], action="request"
                ),
                confirmed=confirmed,
            )


def _proposal(token, scope, version, source_id, key):
    if version.get("content_state") != "AVAILABLE":
        st.caption("Predlog anonimizacije zahteva dostupan ulazni sadržaj.")
        return
    if st.button("Učitaj dostupne izlazne verzije drugih izvora", key=key + "_load"):
        st.session_state.pop(key + "_outputs", None)
        try:
            outputs = []
            for source in data_api.list_data_sources(token, **scope):
                if str(source["id"]) == source_id:
                    continue
                detail = data_api.get_source_detail(token, source_id=str(source["id"]), **scope)
                outputs.extend(
                    {**item, "source_name": source["name"]}
                    for item in detail.get("versions", [])
                    if item["content_state"] == "AVAILABLE"
                )
            st.session_state[key + "_outputs"] = outputs
        except ERRORS as exc:
            st.error(str(exc))
    outputs = st.session_state.get(key + "_outputs", [])
    if not outputs:
        st.caption(
            "Izlaz mora već postojati u drugom scoped izvoru. Ovo nije automatski anonimizator; prvo primenite i dokumentujte odobrenu metodu."
        )
        return
    with st.form(key):
        output = st.selectbox(
            "Izlazna verzija anonimizacije",
            outputs,
            format_func=lambda x: f"{x['source_name']} · v{x['version_no']} · {x['id']}",
        )
        method = st.text_input("Oznaka metode anonimizacije", max_chars=120)
        method_version = st.text_input("Verzija metode anonimizacije", max_chars=120)
        method_ref = st.text_input("Referenca metode anonimizacije", max_chars=500)
        parameters = st.text_area("Referenca parametara anonimizacije (opciono)", max_chars=1000)
        evidence = st.text_input("Referenca dokaza anonimizacije", max_chars=1000)
        checksum = st.text_input("Checksum dokaza anonimizacije (opciono)", max_chars=64)
        classification = st.selectbox(
            "Klasifikacija izlaza posle anonimizacije", [x.value for x in DataClassification], index=None
        )
        privacy = st.selectbox("Privatnost izlaza posle anonimizacije", [x.value for x in PrivacyCategory], index=None)
        confirmed = st.checkbox("Potvrđujem odvojeni izlaz i dokumentovanu metodu anonimizacije")
        submitted = st.form_submit_button("Registruj predlog anonimizacije")
    if submitted:
        _write(
            lambda: api.propose_anonymization(
                token,
                scope=scope,
                fields=dict(
                    input_version_id=str(version["id"]),
                    output_version_id=str(output["id"]),
                    method_code=method,
                    method_version=method_version,
                    method_reference=method_ref,
                    parameter_reference=parameters,
                    evidence_reference=evidence,
                    evidence_checksum=checksum,
                    classification_after=classification,
                    privacy_category_after=privacy,
                ),
            ),
            confirmed=confirmed,
        )


def _reviews(token, scope, key):
    page = st.number_input("Strana evidencije anonimizacije (50 zapisa)", min_value=1, value=1, key=key + "_page")
    page_key = key + "_p" + str(page)
    if st.button("Učitaj / osveži dokaze anonimizacije", key=key + "_load"):
        st.session_state.pop(page_key + "_rows", None)
        st.session_state[page_key + "_generation"] = st.session_state.get(page_key + "_generation", 0) + 1
        try:
            st.session_state[page_key + "_rows"] = api.list_records(token, scope=scope, offset=(page - 1) * 50)
        except ERRORS as exc:
            st.error(str(exc))
    rows = st.session_state.get(page_key + "_rows")
    if rows is None:
        st.caption("Učitajte scoped evidenciju za pregled ili odluku.")
        return
    st.dataframe(
        [
            {
                name: row.get(name, "—")
                for name in [
                    "id",
                    "input_version_id",
                    "output_version_id",
                    "method_code",
                    "method_version",
                    "status",
                    "classification_after",
                    "privacy_category_after",
                ]
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )
    candidates = [x for x in rows if x["status"] == "PROPOSED"]
    if not candidates:
        st.caption("Na ovoj strani nema PROPOSED predloga. Za sledeću stranu promenite broj i učitajte evidenciju.")
        return
    chosen = st.selectbox(
        "Predlog za ljudski pregled",
        candidates,
        format_func=lambda x: f"{x['id']} · {x['method_code']} · {x['method_version']}",
        key=page_key + "_selected",
    )
    st.dataframe(
        [
            dict(Polje=name, Vrednost=str(chosen.get(name, "—")))
            for name in [
                "input_version_id",
                "output_version_id",
                "method_reference",
                "parameter_reference",
                "evidence_checksum",
                "evidence_reference",
                "classification_before",
                "classification_after",
                "privacy_category_before",
                "privacy_category_after",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    with st.form(page_key + "_" + str(chosen["id"]) + "_g" + str(st.session_state.get(page_key + "_generation", 0))):
        decision = st.selectbox("Odluka o dokazu anonimizacije", ["VERIFIED", "REJECTED"], index=None)
        reference = st.text_input("Referenca ljudskog pregleda anonimizacije", max_chars=1000)
        reason = st.text_area("Obrazloženje pregleda anonimizacije (opciono)", max_chars=1000)
        confirmed = st.checkbox("Potvrđujem proveru ulaza, izlaza, metode i dokaza anonimizacije")
        submitted = st.form_submit_button("Registruj pregled anonimizacije")
    if submitted:
        _write(
            lambda: api.review_anonymization(
                token,
                record_id=str(chosen["id"]),
                scope=scope,
                fields=dict(decision=decision, review_reference=reference, review_reason=reason),
            ),
            confirmed=confirmed,
        )


def _export(token, scope, version, key):
    with st.form(key):
        purpose = st.text_input("Referenca svrhe izvoza verzije", max_chars=1000)
        st.caption(
            "Izvoz poštuje klasifikaciju, privatnost, politiku, hold i stanje sadržaja. Osetljivi izvoz zahteva postojeći governance i stvarni MFA assurance; ovaj obrazac ga ne zaobilazi."
        )
        confirmed = st.checkbox("Potvrđujem svrhu i dozvoljeni izvoz izabrane verzije")
        submitted = st.form_submit_button("Pripremi dozvoljeni izvoz verzije")
    if not submitted:
        return
    if not confirmed:
        st.error("Označite potvrdu pre slanja.")
        return
    try:
        result = api.export_version(token, version_id=str(version["id"]), scope=scope, purpose=purpose)
    except ERRORS as exc:
        st.error(str(exc))
        st.caption(
            "Ako backend traži step-up, otvorite Bezbednost naloga. Potvrda lozinke nije zamena za MFA kod osetljivog izvoza."
        )
        return
    except ValueError:
        st.error("Unesite važeću referencu svrhe izvoza.")
        return
    st.caption("Manifest izvoza: " + str(result["manifest_id"]))
    st.download_button(
        "Preuzmi dozvoljeni izvoz",
        data=result["payload"],
        file_name=Path(version["original_filename"]).name,
        mime=result["content_type"],
        key=key + "_download",
    )


def render_source_privacy(*, token, shell, source_id, versions):
    permissions = set(shell["product"].get("permission_codes", []))
    if "data.read" not in permissions or not shell.get("workspace"):
        return
    scope = dict(
        organization_id=str(shell["organization"]["id"]),
        workspace_id=str(shell["workspace"]["id"]),
        product_code=shell["product"]["code"],
    )
    key = "_".join(scope.values()) + "_" + source_id + "_privacy"
    with st.expander("Uputstvo: čuvanje, anonimizacija i izvoz"):
        st.markdown((Path(__file__).resolve().parents[2] / "docs/help/ISI-PRIVACY-CONTROLS-GUIDE.md").read_text())
    mutable = "data.governance.manage" in permissions
    if mutable:
        with st.expander("Registracija politike čuvanja"):
            _policy(token, scope, key + "_policy")
    if not versions:
        st.caption("Retencija i anonimizacija zahtevaju registrovanu verziju izvora.")
        return
    version = st.selectbox(
        "Verzija za privatnost i čuvanje",
        versions,
        format_func=lambda x: f"v{x['version_no']} · {x['original_filename']} · {x['content_state']}",
        key=key + "_version",
    )
    version_key = key + "_" + str(version["id"])
    with st.expander("Stanje čuvanja i hold"):
        if st.button("Učitaj / osveži stanje čuvanja", key=version_key + "_load"):
            st.session_state.pop(version_key + "_state", None)
            st.session_state[version_key + "_generation"] = st.session_state.get(version_key + "_generation", 0) + 1
            try:
                st.session_state[version_key + "_state"] = api.read_retention(
                    token, version_id=str(version["id"]), scope=scope
                )
            except ERRORS as exc:
                st.error(str(exc))
        state = st.session_state.get(version_key + "_state")
        if state:
            _retention(
                token,
                scope,
                version,
                state,
                version_key + "_g" + str(st.session_state.get(version_key + "_generation", 0)),
                mutable,
            )
    if mutable:
        with st.expander("Predlog anonimizacije odvojenog izlaza"):
            _proposal(token, scope, version, source_id, version_key + "_proposal")
        with st.expander("Pregled dokaza anonimizacije"):
            _reviews(token, scope, key + "_review")
    if "data.export" in permissions and version.get("content_state") == "AVAILABLE":
        with st.expander("Dozvoljeni izvoz verzije"):
            _export(token, scope, version, version_key + "_export")
