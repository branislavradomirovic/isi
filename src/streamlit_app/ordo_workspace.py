from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from src.streamlit_app import ordo_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired


def _scope(shell: dict[str, Any]) -> tuple[str, str] | None:
    org = shell.get("organization") or {}
    workspace = shell.get("workspace") or {}
    if not org.get("id") or not workspace.get("id"): return None
    return str(org["id"]), str(workspace["id"])


def _safe(fn, *args, **kwargs):
    try: return fn(*args, **kwargs)
    except AuthenticationRequired as exc: st.error(str(exc))
    except AccessDenied as exc: st.warning(str(exc))
    except ApiUnavailable as exc: st.error(str(exc))
    return None


def render_ordo_overview(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">ORDO · Destination Foundation</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Razvoj destinacije kao povezan sistem</h1>', unsafe_allow_html=True)
    st.caption("Resursi, nasleđe, ljudi, ekonomija, infrastruktura, znanje, preduzetništvo, identitet i zajednica — bez izmišljenih ocena ili scenarija.")
    if scope is None: st.info("ORDO workspace nije izabran."); return
    organization_id, workspace_id = scope
    foundation = _safe(ordo_api.foundation, token, organization_id, workspace_id)
    cat = _safe(ordo_api.catalog, token, organization_id, workspace_id)
    if not foundation or not cat: return
    cols = st.columns(5)
    cols[0].metric("Stubovi", len(cat.get("pillars", [])))
    cols[1].metric("Oblasti", len(cat.get("dimensions", [])))
    cols[2].metric("Resursi", foundation.get("asset_count", 0))
    cols[3].metric("Akteri", foundation.get("stakeholder_count", 0))
    cols[4].metric("Opservacije", foundation.get("observation_count", 0))
    st.markdown("### Pet ORDO stubova")
    st.write(" · ".join(x["name_sr"] for x in cat.get("pillars", [])))
    profile = foundation.get("profile")
    if profile:
        st.markdown("### Profil destinacije")
        st.write(f"**{profile.get('destination_name')}**")
        st.caption(f"Tip: {profile.get('destination_type') or 'nije definisan'} · referentna godina: {profile.get('reference_year') or 'nije definisana'}")
    else:
        st.info("Profil destinacije još nije konfigurisan. ORDO ne pretpostavlja naziv, tip ili statistiku destinacije.")
    assets = _safe(ordo_api.assets, token, organization_id, workspace_id) or []
    stakeholders = _safe(ordo_api.stakeholders, token, organization_id, workspace_id) or []
    cycles = _safe(ordo_api.cycles, token, organization_id, workspace_id) or []
    if assets:
        st.markdown("### Resursi i elementi destinacije"); st.dataframe(assets, use_container_width=True, hide_index=True)
    if stakeholders:
        st.markdown("### Akteri destinacije"); st.dataframe(stakeholders, use_container_width=True, hide_index=True)
    if cycles:
        st.markdown("### Monitoring ciklusi"); st.dataframe(cycles, use_container_width=True, hide_index=True)
    permissions = set(shell.get("permissions") or [])
    if "workspace.manage" in permissions:
        with st.expander("Konfiguracija destinacije", expanded=profile is None):
            with st.form("ordo_profile_form"):
                name = st.text_input("Naziv destinacije", value=(profile or {}).get("destination_name", ""))
                code = st.text_input("Šifra (opciono)", value=(profile or {}).get("destination_code", ""))
                dtype = st.text_input("Tip destinacije (opciono)", value=(profile or {}).get("destination_type", ""))
                year = st.number_input("Referentna godina", min_value=1900, max_value=2200, value=int((profile or {}).get("reference_year") or date.today().year), step=1)
                notes = st.text_area("Napomena", value=(profile or {}).get("notes", ""))
                if st.form_submit_button("Sačuvaj profil", use_container_width=True):
                    if not name.strip(): st.error("Naziv destinacije je obavezan.")
                    else:
                        result = _safe(ordo_api.upsert_profile, token, organization_id=organization_id, workspace_id=workspace_id, destination_name=name, destination_code=code, destination_type=dtype, reference_year=int(year), notes=notes)
                        if result is not None: st.success("ORDO profil je sačuvan."); st.rerun()
            with st.form("ordo_asset_form"):
                asset_type = st.selectbox("Tip resursa", ["natural_resource", "cultural_heritage", "attraction", "experience", "infrastructure", "mobility", "accommodation", "gastronomy", "event", "knowledge", "entrepreneurship", "community", "other"])
                asset_name = st.text_input("Naziv resursa")
                location = st.text_input("Lokacija / područje (opciono)")
                description = st.text_area("Opis (opciono)")
                if st.form_submit_button("Dodaj resurs", use_container_width=True):
                    if not asset_name.strip(): st.error("Naziv resursa je obavezan.")
                    else:
                        result = _safe(ordo_api.create_asset, token, organization_id=organization_id, workspace_id=workspace_id, asset_type=asset_type, name=asset_name, external_code="", location_label=location, description=description)
                        if result is not None: st.success("ORDO resurs je dodat."); st.rerun()
            with st.form("ordo_stakeholder_form"):
                stakeholder_type = st.selectbox("Tip aktera", ["local_government", "tourism_organization", "heritage_institution", "protected_area_manager", "business", "entrepreneur", "education_research", "infrastructure_operator", "civil_society", "community", "other"])
                stakeholder_name = st.text_input("Naziv aktera")
                if st.form_submit_button("Dodaj aktera", use_container_width=True):
                    if not stakeholder_name.strip(): st.error("Naziv aktera je obavezan.")
                    else:
                        result = _safe(ordo_api.create_stakeholder, token, organization_id=organization_id, workspace_id=workspace_id, stakeholder_type=stakeholder_type, name=stakeholder_name, external_code="")
                        if result is not None: st.success("ORDO akter je dodat."); st.rerun()
    if "indicator.manage" in permissions:
        with st.expander("Novi monitoring ciklus"):
            with st.form("ordo_cycle_form"):
                code = st.text_input("Kod ciklusa")
                title = st.text_input("Naziv ciklusa")
                start = st.date_input("Početak perioda", value=date.today().replace(month=1, day=1))
                end = st.date_input("Kraj perioda", value=date.today())
                status = st.selectbox("Status", ["planned", "open", "closed"])
                if st.form_submit_button("Kreiraj ciklus", use_container_width=True):
                    if not code.strip() or not title.strip(): st.error("Kod i naziv ciklusa su obavezni.")
                    elif end < start: st.error("Kraj perioda ne može biti pre početka.")
                    else:
                        result = _safe(ordo_api.create_cycle, token, organization_id=organization_id, workspace_id=workspace_id, code=code, title=title, period_start=start, period_end=end, status=status)
                        if result is not None: st.success("ORDO monitoring ciklus je kreiran."); st.rerun()


def render_ordo_indicators(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">ORDO · Indikatori</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">ORDO conceptual indicator registry</h1>', unsafe_allow_html=True)
    st.caption("ORDO registruje indikatorske koncepte i provenance-ready opservacije. Metodologije, analitika, scenariji i forecast runtime postoje kao odvojeni governed slojevi; ovaj ekran ne izmišlja formule, modele ni vrednosti.")
    if scope is None: st.info("ORDO workspace nije izabran."); return
    organization_id, workspace_id = scope
    cat = _safe(ordo_api.catalog, token, organization_id, workspace_id)
    obs = _safe(ordo_api.observations, token, organization_id, workspace_id)
    if not cat: return
    dimensions = {x["code"]: x["name_sr"] for x in cat.get("dimensions", [])}
    pillars = {x["code"]: x["name_sr"] for x in cat.get("pillars", [])}
    selected = st.selectbox("Oblast", ["ALL"] + list(dimensions), format_func=lambda x: "Sve oblasti" if x == "ALL" else dimensions.get(x, x))
    for item in [x for x in cat.get("indicators", []) if selected == "ALL" or x.get("dimension_code") == selected]:
        st.markdown(f"**{item['name_sr']}**")
        st.caption(f"{dimensions.get(item.get('dimension_code'), item.get('dimension_code'))} · stub: {pillars.get(item.get('pillar_code'), item.get('pillar_code'))} · status metodologije: {item.get('methodology_status')} · {item.get('unit_hint') or 'jedinica nije zaključana'}")
    st.markdown("### Evidentirane opservacije")
    if obs: st.dataframe(obs, use_container_width=True, hide_index=True)
    else: st.info("Nema ORDO opservacija. ISI-10 ne generiše vrednosti bez stvarnog izvora i provenance-a.")
