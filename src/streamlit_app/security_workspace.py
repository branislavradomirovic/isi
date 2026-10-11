from __future__ import annotations

import hashlib
import json
from pathlib import Path
import streamlit as st
from src.streamlit_app.shared_help_workspace import render_topic_summary
from src.streamlit_app.api_client import ApiUnavailable, AuthenticationRequired
from src.streamlit_app import security_api


def _safe(fn, *args):
    try:
        return fn(*args)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except (ApiUnavailable, ValueError):
        st.error("Operacija nije potvrđena. Osvežite pregled sesija i proverite status pre ponavljanja.")
    return None


def _confirm(key, value, label):
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
    previous, revision = st.session_state.get(key + ":binding", (None, 0))
    if previous != digest:
        revision += 1
        st.session_state[key + ":binding"] = (digest, revision)
    return st.checkbox(label, key=key + f":confirm:{revision}")


def _stable(item):
    return {k: item.get(k) for k in ("session_id", "is_current", "is_revoked", "expires_at", "device_label")}


def _completed(message):
    st.session_state["security:receipt"] = message
    st.session_state["security:generation"] = st.session_state.get("security:generation", 0) + 1
    st.rerun()


def render_account_security(*, token: str) -> None:
    render_topic_summary("ISI-H10")
    st.markdown('<div class="isi-eyebrow">Bezbednost naloga</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Sesije i potvrda identiteta</h1>', unsafe_allow_html=True)
    st.caption(
        "Prikaz koristi isključivo privatne, ograničene opise uređaja; mrežne adrese i puni user-agent podaci se ne prikazuju."
    )
    with st.expander("Uputstvo za nalog, pristup i sesije"):
        st.markdown(
            Path(__file__)
            .resolve()
            .parents[2]
            .joinpath("docs/help/ISI-ACCOUNT-SECURITY-WORKFLOWS-GUIDE.md")
            .read_text()
        )
    st.markdown("### Potvrda lozinke za privilegovani rad")
    with st.form("isi_password_assurance", clear_on_submit=True):
        password = st.text_input("Trenutna lozinka", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Potvrdi identitet")
    if submitted:
        result = _safe(security_api.refresh_password_assurance, token, password)
        if result is True:
            st.success("Potvrda identiteta je osvežena za ovu sesiju.")
        elif result is False:
            st.error("Lozinka nije potvrđena.")

    st.markdown("### Aktivne i opozvane sesije")
    sessions = _safe(security_api.list_sessions, token)
    if sessions is None:
        st.info("Pregled nije učitan; to ne znači da nema aktivnih sesija.")
        return
    current_identity = next((item["session_id"] for item in sessions if item["is_current"]), None)
    if st.session_state.get("security:current-session") != current_identity:
        st.session_state["security:current-session"] = current_identity
        st.session_state["security:generation"] = st.session_state.get("security:generation", 0) + 1
        st.session_state.pop("security:receipt", None)
    prefix = f"security:{st.session_state.get('security:generation', 0)}:"
    if st.session_state.get("security:receipt"):
        st.success(st.session_state["security:receipt"])
    if not sessions:
        st.info("Nema sesija u vraćenom pregledu.")
    stable = sorted((_stable(item) for item in sessions), key=lambda row: row["session_id"])
    active_others = [item for item in sessions if not item["is_current"] and not item["is_revoked"]]
    st.caption(
        "Opoziv svih drugih sesija obuhvata sve vaše druge aktivne sesije u trenutku izvršenja, uključujući one otvorene posle ovog pregleda. Trenutna sesija ostaje aktivna."
    )
    confirmed = _confirm(prefix + "others", stable, "Potvrđujem opoziv svih svojih drugih aktivnih sesija")
    if st.button("Opozovi sve druge sesije", key=prefix + "others", disabled=not (confirmed and active_others)):
        count = _safe(security_api.revoke_other_sessions, token)
        if count is not None:
            _completed(f"Opozvano drugih sesija: {count}. Trenutna sesija je očuvana.")
    for item in sessions:
        state = "opozvana" if item["is_revoked"] else "aktivna"
        current = " · trenutna sesija" if item["is_current"] else ""
        with st.container(border=True):
            st.text(f"{item['device_label']} · {state}{current}")
            st.caption(
                f"Kreirana: {item['created_at']} · poslednja aktivnost: {item.get('last_seen_at') or 'nije dostupno'} · ističe: {item['expires_at']}"
            )
            if not item["is_current"] and not item["is_revoked"]:
                key = prefix + item["session_id"]
                confirmed = _confirm(key, _stable(item), "Potvrđujem opoziv ove druge sesije")
                if st.button("Opozovi sesiju", key=key, disabled=not confirmed):
                    if _safe(security_api.revoke_session, token, item["session_id"]) is not None:
                        _completed("Izabrana druga sesija je opozvana. Pregled je ponovo učitan.")
    st.info(
        "Repozitorijum sadrži provider-neutral MFA challenge i assurance osnovu. Produkcioni upis i isporuka drugog faktora ostaju odloženi do integracije stvarnog provajdera."
    )
