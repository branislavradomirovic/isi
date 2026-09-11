from __future__ import annotations

import streamlit as st

from src.streamlit_app.api_client import ApiUnavailable, AuthenticationRequired
from src.streamlit_app import security_api


def render_account_security(*, token: str) -> None:
    st.markdown('<div class="isi-eyebrow">Bezbednost naloga</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Sesije i potvrda identiteta</h1>', unsafe_allow_html=True)
    st.caption("Prikaz koristi isključivo privatne, ograničene opise uređaja; mrežne adrese i puni user-agent podaci se ne prikazuju.")

    st.markdown("### Potvrda lozinke za privilegovani rad")
    with st.form("isi_password_assurance", clear_on_submit=True):
        password = st.text_input("Trenutna lozinka", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Potvrdi identitet")
    if submitted:
        try:
            if security_api.refresh_password_assurance(token, password):
                st.success("Potvrda identiteta je osvežena za ovu sesiju.")
            else:
                st.error("Lozinka nije potvrđena.")
        except (AuthenticationRequired, ApiUnavailable) as exc:
            st.error(str(exc))

    st.markdown("### Aktivne i opozvane sesije")
    try:
        sessions = security_api.list_sessions(token)
    except (AuthenticationRequired, ApiUnavailable) as exc:
        st.error(str(exc))
        return

    if st.button("Opozovi sve druge sesije"):
        try:
            count = security_api.revoke_other_sessions(token)
            st.success(f"Opozvano sesija: {count}.")
            st.rerun()
        except (AuthenticationRequired, ApiUnavailable) as exc:
            st.error(str(exc))

    for item in sessions:
        state = "opozvana" if item["is_revoked"] else "aktivna"
        current = " · trenutna sesija" if item["is_current"] else ""
        with st.container(border=True):
            st.markdown(f"**{item['device_label']}** · {state}{current}")
            st.caption(
                f"Kreirana: {item['created_at']} · poslednja aktivnost: {item.get('last_seen_at') or 'nije dostupno'} · ističe: {item['expires_at']}"
            )
            if not item["is_current"] and not item["is_revoked"]:
                if st.button("Opozovi sesiju", key=f"revoke_session_{item['session_id']}"):
                    try:
                        security_api.revoke_session(token, item["session_id"])
                        st.rerun()
                    except (AuthenticationRequired, ApiUnavailable) as exc:
                        st.error(str(exc))

    st.info(
        "Repozitorijum sadrži provider-neutral MFA challenge i assurance osnovu. "
        "Produkcioni upis i isporuka drugog faktora ostaju odloženi do integracije stvarnog provajdera."
    )
