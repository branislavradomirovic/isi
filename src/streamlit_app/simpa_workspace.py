from __future__ import annotations

from typing import Any
from datetime import date
import streamlit as st

from src.streamlit_app import simpa_api


def _scope(shell: dict[str, Any]) -> tuple[str, str] | None:
    workspace = shell.get("workspace")
    if not workspace or shell.get("product", {}).get("code") != "SIMPA": return None
    return str(shell["organization"]["id"]), str(workspace["id"])


def _safe(call, *args, **kwargs):
    try: return call(*args, **kwargs)
    except Exception as exc:
        st.error(str(exc)); return None


def render_simpa_overview(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">SIMPA · Domain Foundation</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Lokalni sistem socijalne zaštite</h1>', unsafe_allow_html=True)
    st.caption("SIMPA u ISI arhitekturi: podaci, lokalni akteri, monitoring i konceptualni indikator registry. AI analitika nije deo ISI-08.")
    if scope is None:
        st.info("SIMPA workspace nije izabran."); return
    organization_id, workspace_id = scope
    summary = _safe(simpa_api.foundation, token, organization_id, workspace_id)
    if not summary: return
    profile = summary.get("profile")
    if profile:
        st.markdown(f"### {profile['jurisdiction_name']}")
        meta = []
        if profile.get("jurisdiction_code"): meta.append(f"šifra: {profile['jurisdiction_code']}")
        if profile.get("reference_year"): meta.append(f"referentna godina: {profile['reference_year']}")
        if meta: st.caption(" · ".join(meta))
    else:
        st.info("Profil lokalnog sistema još nije konfigurisan. ISI-08 ne upisuje izmišljenu JLS niti demo statistiku.")
    cols = st.columns(4)
    metrics = [("Lokalni akteri", summary["actor_count"]), ("Monitoring ciklusi", summary["cycle_count"]), ("Mapirani izvori", summary["mapping_count"]), ("Validirane opservacije", summary["validated_observation_count"])]
    for col, (label, value) in zip(cols, metrics): col.metric(label, value)
    st.markdown("### Foundation status")
    st.write("Konceptualni SIMPA indikatori:", summary["conceptual_indicator_count"])
    st.caption("Brojevi iznad potiču isključivo iz aktivnog workspace-a; nema fabričkih statistika o građanima, uslugama ili rizicima.")

    permissions = set(shell.get("product", {}).get("permission_codes", []))
    actors = _safe(simpa_api.actors, token, organization_id, workspace_id) or []
    cycles = _safe(simpa_api.cycles, token, organization_id, workspace_id) or []
    if actors:
        st.markdown("### Lokalni akteri")
        st.dataframe(actors, use_container_width=True, hide_index=True)
    if cycles:
        st.markdown("### Monitoring ciklusi")
        st.dataframe(cycles, use_container_width=True, hide_index=True)

    if "workspace.manage" in permissions:
        with st.expander("Konfiguracija lokalnog sistema", expanded=profile is None):
            with st.form("simpa_profile_form"):
                name = st.text_input("Naziv JLS / lokalnog sistema", value=(profile or {}).get("jurisdiction_name", ""))
                code = st.text_input("Šifra (opciono)", value=(profile or {}).get("jurisdiction_code", ""))
                year_default = int((profile or {}).get("reference_year") or date.today().year)
                year = st.number_input("Referentna godina", min_value=1900, max_value=2200, value=year_default, step=1)
                notes = st.text_area("Napomena", value=(profile or {}).get("notes", ""))
                if st.form_submit_button("Sačuvaj profil", use_container_width=True):
                    if not name.strip(): st.error("Naziv je obavezan.")
                    else:
                        result = _safe(simpa_api.upsert_profile, token, organization_id=organization_id, workspace_id=workspace_id, jurisdiction_name=name, jurisdiction_code=code, reference_year=int(year), notes=notes)
                        if result is not None: st.success("SIMPA profil je sačuvan."); st.rerun()
            with st.form("simpa_actor_form"):
                actor_type = st.selectbox("Tip lokalnog aktera", ["local_government", "social_work_center", "social_service_provider", "education", "health", "employment", "housing", "civil_society", "other"])
                actor_name = st.text_input("Naziv aktera")
                actor_code = st.text_input("Eksterna šifra aktera (opciono)")
                if st.form_submit_button("Dodaj aktera", use_container_width=True):
                    if not actor_name.strip(): st.error("Naziv aktera je obavezan.")
                    else:
                        result = _safe(simpa_api.create_actor, token, organization_id=organization_id, workspace_id=workspace_id, actor_type=actor_type, name=actor_name, external_code=actor_code)
                        if result is not None: st.success("Lokalni akter je dodat."); st.rerun()

    if "indicator.manage" in permissions:
        with st.expander("Novi monitoring ciklus"):
            with st.form("simpa_cycle_form"):
                cycle_code = st.text_input("Kod ciklusa")
                cycle_title = st.text_input("Naziv ciklusa")
                start = st.date_input("Početak perioda", value=date.today().replace(month=1, day=1))
                end = st.date_input("Kraj perioda", value=date.today())
                status = st.selectbox("Status", ["planned", "open", "closed"])
                if st.form_submit_button("Kreiraj ciklus", use_container_width=True):
                    if not cycle_code.strip() or not cycle_title.strip(): st.error("Kod i naziv ciklusa su obavezni.")
                    elif end < start: st.error("Kraj perioda ne može biti pre početka.")
                    else:
                        result = _safe(simpa_api.create_cycle, token, organization_id=organization_id, workspace_id=workspace_id, code=cycle_code, title=cycle_title, period_start=start, period_end=end, status=status)
                        if result is not None: st.success("Monitoring ciklus je kreiran."); st.rerun()


def render_simpa_indicators(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">SIMPA · Indikatori</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">SIMPA indicator registry</h1>', unsafe_allow_html=True)
    st.caption("ISI-08 registruje konceptualni katalog i provenance-ready opservacije. Formule i analitički modeli se validiraju u ISI-09.")
    if scope is None:
        st.info("SIMPA workspace nije izabran."); return
    organization_id, workspace_id = scope
    cat = _safe(simpa_api.catalog, token, organization_id, workspace_id)
    obs = _safe(simpa_api.observations, token, organization_id, workspace_id)
    if not cat: return
    indicators = cat.get("indicators", [])
    dimensions = {x["code"]: x["name_sr"] for x in cat.get("dimensions", [])}
    selected_dimension = st.selectbox("Oblast", ["ALL"] + list(dimensions.keys()), format_func=lambda x: "Sve oblasti" if x == "ALL" else dimensions.get(x, x))
    filtered = [x for x in indicators if selected_dimension == "ALL" or x.get("dimension_code") == selected_dimension]
    for item in filtered:
        st.markdown(f"**{item['name_sr']}**")
        st.caption(f"{dimensions.get(item.get('dimension_code'), item.get('dimension_code'))} · status metodologije: {item.get('methodology_status')} · {item.get('unit_hint') or 'jedinica nije zaključana'}")
    st.markdown("### Evidentirane opservacije")
    if obs:
        st.dataframe(obs, use_container_width=True, hide_index=True)
    else:
        st.info("Nema opservacija. ISI-08 namerno ne generiše indikator vrednosti bez izvora i provenance-a.")


def render_ordo_indicator_placeholder(shell: dict[str, Any]) -> None:
    st.markdown('<div class="isi-eyebrow">ORDO · Indikatori</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">ORDO indicator foundation</h1>', unsafe_allow_html=True)
    st.info("ORDO domain indicator model dolazi u ISI-10. SIMPA registry se nikada ne koristi kao ORDO registry.")
