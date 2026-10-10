"""Source privacy/classification and explicit record review presentation."""

import json
from pathlib import Path

import streamlit as st

from src.platform.data.governance import DataClassification, PrivacyCategory, AIUsePolicy, ExportPolicy, GovernanceState
from src.streamlit_app import data_governance_api as api
from src.streamlit_app.data_ingestion_workspace import _write, ERRORS

CATALOGS = {
    "classification": ("Klasifikacija", DataClassification),
    "privacy_category": ("Kategorija privatnosti", PrivacyCategory),
    "ai_use_policy": ("Dozvoljena AI upotreba", AIUsePolicy),
    "export_policy": ("Politika izvoza", ExportPolicy),
    "governance_state": ("Stanje governance-a", GovernanceState),
}


def profile_changes(profile, proposed):
    return {name: value for name, value in proposed.items() if value != profile.get(name)}


def _profile_form(token, params, profile, policies, key):
    with st.form(key + "_" + str(profile["revision"])):
        st.caption(
            f"Revizija {profile['revision']}. Izmenite samo odobrene vrednosti. Smanjenje osetljivosti zahteva provereni dokaz anonimizacije."
        )
        values = {}
        for name, (label, catalog) in CATALOGS.items():
            options = [x.value for x in catalog]
            values[name] = st.selectbox(label, options, index=options.index(profile[name]))
        values["processing_purpose"] = st.text_area(
            "Svrha obrade", value=profile.get("processing_purpose", ""), max_chars=1000
        )
        values["data_owner_ref"] = st.text_input(
            "Referenca vlasnika podataka", value=profile.get("data_owner_ref", ""), max_chars=300
        )
        values["classification_rationale"] = st.text_area(
            "Obrazloženje klasifikacije", value=profile.get("classification_rationale", ""), max_chars=1000
        )
        steward = st.text_input(
            "ID aktivnog stewardship članstva (opciono)",
            value=str(profile.get("data_steward_membership_id") or ""),
            max_chars=36,
        )
        values["data_steward_membership_id"] = steward.strip() or None
        active = {str(x["id"]): x for x in policies if x["status"] == "active"}
        current = str(profile.get("retention_policy_id") or "")
        ids = [""] + list(active)
        if current and current not in active:
            ids.append(current)
        chosen = st.selectbox(
            "Politika čuvanja",
            ids,
            index=ids.index(current),
            format_func=lambda x: (
                "Bez vezane politike"
                if not x
                else f"{active[x]['name']} · v{active[x]['version_no']}"
                if x in active
                else "Trenutna istorijska politika · " + x
            ),
        )
        values["retention_policy_id"] = chosen or None
        proof = st.text_input("ID proverenog dokaza anonimizacije (samo kada potreban)", max_chars=36)
        confirmed = st.checkbox("Potvrđujem governance promene i njihovo obrazloženje")
        submitted = st.form_submit_button("Sačuvaj governance profil")
    if submitted:
        changes = profile_changes(profile, values)
        if proof.strip():
            changes["verified_anonymization_record_id"] = proof.strip()
        if not changes:
            st.info("Nema izmenjenih vrednosti.")
            return
        _write(
            lambda: api.update_profile(token, **params, revision=profile["revision"], fields=changes),
            confirmed=confirmed,
        )


def _record_table(record):
    st.dataframe(
        [
            dict(
                Polje=str(name),
                Vrednost=json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value),
            )
            for name, value in record.items()
        ],
        hide_index=True,
        width="stretch",
    )


def _quarantine(token, params, rows, key):
    if not rows:
        st.caption("Nema zapisa u karantinu za ovaj izvor.")
        return
    st.dataframe(
        [
            {
                name: item.get(name, "—")
                for name in [
                    "id",
                    "source_record_ordinal",
                    "source_locator",
                    "quarantine_reason",
                    "content_fingerprint",
                ]
            }
            for item in rows
        ],
        hide_index=True,
        width="stretch",
    )
    chosen = st.selectbox(
        "Zapis u karantinu",
        rows,
        format_func=lambda x: f"{x['source_record_ordinal']} · {x['quarantine_reason']} · {x['id']}",
        key=key + "_selection",
    )
    record_key = key + "_" + str(chosen["id"]) + "_" + str(chosen["content_fingerprint"])
    if st.button("Učitaj zapis i aktuelni prihvaćeni zapis", key=record_key + "_load"):
        st.session_state.pop(record_key + "_detail", None)
        st.session_state[record_key + "_generation"] = st.session_state.get(record_key + "_generation", 0) + 1
        try:
            st.session_state[record_key + "_detail"] = api.read_quarantine(token, **params, record_id=str(chosen["id"]))
        except ERRORS as exc:
            st.error(str(exc))
    detail = st.session_state.get(record_key + "_detail")
    if not detail:
        st.caption("Pre odluke učitajte i pregledajte oba zapisa i njihov identitet.")
        return
    st.markdown("**Dolazni normalizovani zapis**")
    _record_table(detail["normalized_record"])
    st.markdown("**Aktuelni prihvaćeni zapis**")
    if detail.get("current_accepted_record") is None:
        st.caption("Ne postoji aktuelni prihvaćeni zapis za ovaj identitet.")
    else:
        _record_table(detail["current_accepted_record"])
    with st.form(
        record_key
        + "_"
        + str(detail.get("current_accepted_record_id"))
        + "_g"
        + str(st.session_state.get(record_key + "_generation", 0))
    ):
        decision = st.selectbox("Odluka o dolaznom zapisu", ["REJECT_INCOMING", "ACCEPT_INCOMING"])
        reference = st.text_input("Referenca pregleda odluke", max_chars=1000)
        reason = st.text_area("Obrazloženje odluke o zapisu (opciono)", max_chars=1000)
        st.caption(
            "ACCEPT_INCOMING nije popravka neispravnog identiteta. Backend dopušta prihvatanje samo za dozvoljen konflikt i proverava aktuelni prihvaćeni zapis."
        )
        confirmed = st.checkbox("Potvrđujem ljudski pregled identiteta, sadržaja i odluke")
        submitted = st.form_submit_button("Registruj odluku o zapisu")
    if submitted:
        _write(
            lambda: api.resolve_record(
                token,
                **params,
                record_id=str(chosen["id"]),
                fields=dict(
                    decision=decision,
                    resolution_reference=reference,
                    reason=reason or None,
                    expected_current_accepted_record_id=detail.get("current_accepted_record_id"),
                ),
            ),
            confirmed=confirmed,
        )


def render_source_governance(*, token, shell, source_id):
    permissions = set(shell["product"].get("permission_codes", []))
    if "data.read" not in permissions or not shell.get("workspace"):
        return
    scope = dict(
        organization_id=str(shell["organization"]["id"]),
        workspace_id=str(shell["workspace"]["id"]),
        product_code=shell["product"]["code"],
    )
    params = dict(source_id=source_id, scope=scope)
    key = "_".join(scope.values()) + "_" + source_id + "_governance"
    with st.expander("Uputstvo: governance izvora i karantin"):
        st.markdown((Path(__file__).resolve().parents[2] / "docs/help/ISI-SOURCE-GOVERNANCE-GUIDE.md").read_text())
    if st.button("Učitaj / osveži governance profil", key=key + "_load"):
        for name in list(st.session_state):
            if name.startswith(key) and name not in {key + "_load", key + "_generation"}:
                del st.session_state[name]
        st.session_state[key + "_generation"] = st.session_state.get(key + "_generation", 0) + 1
        try:
            profile = api.read_profile(token, **params)
            policies = api.list_retention_policies(token, scope=scope)
            st.session_state[key + "_view"] = dict(profile=profile, policies=policies)
        except ERRORS as exc:
            st.error(str(exc))
    view = st.session_state.get(key + "_view")
    if not view:
        st.caption("Učitajte važeći profil pre pregleda ili izmene governance podataka.")
        return
    key += "_g" + str(st.session_state.get(key + "_generation", 0))
    profile = view["profile"]
    st.dataframe(
        [
            {
                name: profile.get(name, "—")
                for name in [
                    "classification",
                    "privacy_category",
                    "governance_state",
                    "ai_use_policy",
                    "export_policy",
                    "processing_purpose",
                    "data_owner_ref",
                    "revision",
                ]
            }
        ],
        hide_index=True,
        width="stretch",
    )
    if "data.governance.manage" not in permissions:
        st.caption("Imate pristup profilu samo za čitanje. Karantin zahteva posebno governance ovlašćenje.")
        return
    with st.expander("Izmena governance profila"):
        _profile_form(token, params, profile, view["policies"], key + "_profile")
    with st.expander("Pregled i odluka o zapisima u karantinu"):
        if st.button("Učitaj karantin izvora", key=key + "_quarantine_load"):
            st.session_state.pop(key + "_quarantine_rows", None)
            st.session_state[key + "_quarantine_generation"] = (
                st.session_state.get(key + "_quarantine_generation", 0) + 1
            )
            try:
                st.session_state[key + "_quarantine_rows"] = api.list_quarantine(token, **params)
            except ERRORS as exc:
                st.error(str(exc))
        if key + "_quarantine_rows" in st.session_state:
            _quarantine(
                token,
                params,
                st.session_state[key + "_quarantine_rows"],
                key + "_quarantine_g" + str(st.session_state.get(key + "_quarantine_generation", 0)),
            )
