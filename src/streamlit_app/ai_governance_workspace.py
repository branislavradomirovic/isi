from __future__ import annotations

import hashlib
import json

import streamlit as st

from src.streamlit_app import ai_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired
from src.streamlit_app.evidence_view import render_evidence


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except (AccessDenied, ApiUnavailable) as exc:
        st.error(str(exc))
    return None


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def render_ai_governance(*, token: str, shell: dict, scope: dict) -> None:
    permissions = set(shell["product"].get("permission_codes", []))
    st.subheader("AI dokazi i ljudski pregled")
    st.caption(
        "Pregled evaluacije ne promoviše model niti objavljuje institucionalni zaključak. Modelski registar je zajednički/proizvodni; evaluacioni run pripada ovoj organizaciji i radnom prostoru."
    )
    if "analysis.read" not in permissions:
        st.info("Za evaluacione dokaze potrebno je analysis.read.")
        return
    key = "ai_review:" + _hash(scope)
    if st.session_state.get("ai_review:active") != key:
        st.session_state["ai_review:active"] = key
        st.session_state[key + ":generation"] = st.session_state.get(key + ":generation", 0) + 1
        st.session_state.pop(key + ":registry", None)
    if st.session_state.get(key + ":receipt"):
        st.success(st.session_state[key + ":receipt"])
    if st.button("Učitaj / osveži AI evaluacione dokaze", key=key + ":load"):
        st.session_state.pop(key + ":registry", None)
        registrations = _safe(ai_api.evidence_get, token, scope=scope, kind="registrations")
        runs = _safe(ai_api.evidence_get, token, scope=scope, kind="runs")
        st.session_state[key + ":generation"] = st.session_state.get(key + ":generation", 0) + 1
        if registrations is not None and runs is not None:
            st.session_state[key + ":registry"] = dict(registrations=registrations, runs=runs)
    registry = st.session_state.get(key + ":registry")
    if registry is None:
        return
    if registry["registrations"]:
        st.dataframe(
            [
                {
                    field: row.get(field)
                    for field in (
                        "model_key",
                        "product_scope",
                        "model_family",
                        "version",
                        "lifecycle_state",
                        "enabled",
                        "registry_fingerprint",
                    )
                }
                for row in registry["registrations"]
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nema registrovanih modelskih dokaza za ovaj proizvod.")
    runs = {row["id"]: row for row in registry["runs"]}
    if not runs:
        st.info("Nema evaluacionih run-ova u ovom kontekstu. Prazan registar nije potvrda kalibracije ili kvaliteta.")
        return
    generation = st.session_state.get(key + ":generation", 0)
    selected = st.selectbox(
        "Evaluacioni run za pregled",
        list(runs),
        index=None,
        format_func=lambda v: f"{runs[v]['status']} · {v}",
        key=key + f":run:{generation}",
    )
    if selected is None:
        return
    run = _safe(ai_api.evidence_get, token, scope=scope, kind="run", record_id=selected)
    results = _safe(ai_api.evidence_get, token, scope=scope, kind="results", record_id=selected)
    reviews = _safe(ai_api.evidence_get, token, scope=scope, kind="reviews", record_id=selected)
    explanation = _safe(ai_api.evidence_get, token, scope=scope, kind="evaluation_xai", record_id=selected)
    if any(value is None for value in (run, results, reviews, explanation)):
        return
    render_evidence("Identitet i vezani dokazi evaluacije", run)
    render_evidence("Rezultati evaluacije — sačuvani dokazi", results)
    render_evidence("Istorija ljudskih pregleda", reviews)
    render_evidence("Objašnjenje i ograničenja AI evaluacije", explanation)
    st.warning(
        "Odobrenje evaluacije je ljudski trag, a ne kalibrisana pouzdanost LLM-a, SHAP dokaz ili automatski izbor produkcionog modela. Konačni pregled jednog recenzenta ne može se prepisati."
    )
    if "report.publish" not in permissions:
        st.info("Samo pregled; pisanje ljudskog pregleda zahteva report.publish.")
        return
    terminal = run["status"] in {"completed", "failed"}
    identity = key + f":{generation}:" + _hash([run, results, reviews])
    decision = st.selectbox(
        "Odluka ljudskog pregleda",
        ["pending"] + (["approved", "changes_requested", "rejected"] if terminal else []),
        index=None,
        key=identity + ":decision",
    )
    notes = st.text_area("Obrazloženje AI pregleda", max_chars=5000, key=identity + ":notes")
    evidence_reference = st.text_input("Referenca dokaza AI pregleda", max_chars=500, key=identity + ":evidence")
    binding = _hash([identity, decision, notes, evidence_reference])
    state_key = key + ":confirmation_binding"
    previous, revision = st.session_state.get(state_key, (None, 0))
    if previous != binding:
        revision += 1
        st.session_state[state_key] = (binding, revision)
    confirmed = st.checkbox(
        "Potvrđujem pregledane AI dokaze i ovu ljudsku odluku", key=identity + f":confirmation:{revision}"
    )
    complete = decision is not None and (decision == "pending" or bool(notes.strip() and evidence_reference.strip()))
    if st.button("Sačuvaj ljudski AI pregled", key=identity + ":submit", disabled=not (complete and confirmed)):
        result = _safe(
            ai_api.review_evaluation,
            token,
            scope=scope,
            run=run,
            decision=decision,
            notes=notes.strip(),
            evidence_reference=evidence_reference.strip(),
        )
        if result is not None:
            st.session_state[key + ":receipt"] = (
                "Ljudski AI pregled je sačuvan. Ponovo učitajte dokaze; prethodne potvrde su poništene."
            )
            st.session_state[key + ":generation"] = generation + 1
            st.session_state.pop(key + ":registry", None)
            st.rerun()
