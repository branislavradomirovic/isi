from __future__ import annotations

from typing import Any
import hashlib
import json

import streamlit as st

from src.streamlit_app import ai_api
from src.streamlit_app.ai_governance_workspace import render_ai_governance
from src.streamlit_app.evidence_view import render_evidence
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired


def _scope(shell: dict[str, Any]) -> tuple[str, str, str] | None:
    workspace = shell.get("workspace")
    if workspace is None:
        st.info("Izaberite ili konfigurišite workspace pre rada sa AI servisima.")
        return None
    return str(shell["organization"]["id"]), str(shell["product"]["code"]), str(workspace["id"])


def _safe_call(callable_, *args, **kwargs):
    try:
        return callable_(*args, **kwargs)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except AccessDenied as exc:
        st.error(str(exc))
    except ApiUnavailable as exc:
        st.error(str(exc))
    return None


def _render_capability(capability: dict[str, Any]) -> None:
    cols = st.columns(4)
    cols[0].metric("Provider default", capability.get("provider_default", "—"))
    cols[1].metric("pgvector", "enabled" if capability.get("pgvector_enabled") else "fallback")
    cols[2].metric("Native vector", "da" if capability.get("native_vector_table") else "ne")
    cols[3].metric("Dev stub", "QA" if capability.get("development_stub_enabled") else "isključen")
    if capability.get("development_stub_enabled"):
        st.warning("Razvojni stub je aktivan samo za lokalni QA. Njegov izlaz nije domenski AI odgovor.")
    st.caption(capability.get("human_accountability", "AI je pomoćni sloj; ljudska odgovornost ostaje obavezna."))


def _render_registry(models: list[dict[str, Any]], prompts: list[dict[str, Any]]) -> None:
    with st.expander("Model i prompt registry", expanded=False):
        if models:
            st.markdown("**Modeli dostupni aktivnom proizvodu**")
            st.dataframe(
                [
                    {
                        "Key": item["model_key"],
                        "Provider": item["provider_name"],
                        "Model": item["model_name"],
                        "Purpose": item["purpose"],
                        "Scope": item["product_scope"],
                        "Dev-only": "da" if item.get("development_only") else "ne",
                    }
                    for item in models
                ],
                width="stretch",
                hide_index=True,
            )
        if prompts:
            st.markdown("**Aktivni promptovi**")
            st.dataframe(
                [
                    {
                        "Key": item["prompt_key"],
                        "Naslov": item["title"],
                        "Scope": item["product_scope"],
                        "Verzija": (item.get("active_version") or {}).get("version_no", "—"),
                    }
                    for item in prompts
                ],
                width="stretch",
                hide_index=True,
            )


def _render_jobs(jobs: list[dict[str, Any]]) -> None:
    st.markdown("### AI job istorija aktivnog workspace-a")
    if not jobs:
        st.caption("Još nema AI job-ova u ovom workspace-u.")
        return
    st.dataframe(
        [
            {
                "Status": item["status"],
                "Prompt": f"{item['prompt_key']} v{item['prompt_version']}",
                "Policy": item["effective_provider_policy"],
                "Provider": item.get("provider_name") or "—",
                "Model": item.get("model_name") or item.get("model_key") or "—",
                "Pokušaji": item["attempts"],
                "Latency ms": item.get("latency_ms") if item.get("latency_ms") is not None else "—",
                "Review": item["human_review_status"],
            }
            for item in jobs
        ],
        width="stretch",
        hide_index=True,
    )
    st.caption("Sačuvani AI izlaz zahteva ljudski pregled; stanje job-a nije institucionalni zaključak.")


def _render_local_ollama_diagnostic(token, shell, scope, capability, models) -> None:
    organization_id, product_code, workspace_id = scope
    st.markdown("### Lokalni Ollama foundation test")
    st.caption(
        "Infrastrukturna dijagnostika sa fiksnim sintetičkim unosom. Ne analizira institucionalne podatke i ne potvrđuje spremnost domenskog modela."
    )
    if "analysis.run" not in shell["product"].get("permission_codes", []):
        st.info("Za pokretanje dijagnostike potrebno je analysis.run.")
        return
    # REQUIRED_COMPATIBILITY registry identity "isi-ollama-chat-default"; never auto-select.
    local = {
        item["model_key"]: item
        for item in models
        if item.get("provider_type") == "ollama" and item.get("purpose") == "chat" and item.get("enabled", True)
    }
    if not local:
        st.info("Lokalni Ollama chat model nije registrovan za aktivni proizvod.")
        return
    key = "ai_diagnostic:" + hashlib.sha256(json.dumps(scope).encode()).hexdigest()
    if st.session_state.get("ai_diagnostic:active") != key:
        st.session_state["ai_diagnostic:active"] = key
        st.session_state[key + ":generation"] = st.session_state.get(key + ":generation", 0) + 1
    generation = st.session_state.get(key + ":generation", 0)
    fields = key + f":{generation}"
    if st.session_state.get(key + ":receipt"):
        st.success(st.session_state[key + ":receipt"])
    model_key = st.selectbox(
        "Lokalni model za dijagnostiku",
        list(local),
        index=None,
        format_func=lambda v: local[v]["model_name"],
        key=fields + ":model",
    )
    sensitivity = st.selectbox("Sensitivity", ["internal", "sensitive"], index=None, key=fields + ":sensitivity")
    if product_code == "SIMPA" and sensitivity == "sensitive":
        st.caption("SIMPA sensitive zahtev ostaje local_only uz obavezni ljudski pregled.")
    binding = hashlib.sha256(
        json.dumps([model_key, sensitivity, local, generation], sort_keys=True).encode()
    ).hexdigest()
    previous, revision = st.session_state.get(key + ":binding", (None, 0))
    if previous != binding:
        revision += 1
        st.session_state[key + ":binding"] = (binding, revision)
    confirmed = st.checkbox(
        "Potvrđujem samo infrastrukturnu AI dijagnostiku izabranim lokalnim modelom",
        key=fields + f":confirm:{revision}",
    )
    if st.button(
        "Pokreni lokalni Ollama test", key=fields + ":submit", disabled=not (confirmed and model_key and sensitivity)
    ):
        result = _safe_call(
            ai_api.create_job,
            token,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
            input_text=f"Local Ollama infrastructure diagnostic for {product_code}",
            sensitivity=sensitivity,
            model_key=model_key,
        )
        if result is not None:
            st.session_state[key + ":receipt"] = (
                f"Dijagnostički zahtev registrovan: {result['id']} · status {result['status']}. Osvežite istoriju za rezultat; nema automatskog ponavljanja."
            )
            st.session_state[key + ":generation"] = generation + 1
            st.rerun()


def render_ai_workspace(*, token: str, shell: dict[str, Any]) -> None:
    product = shell["product"]
    organization = shell["organization"]
    workspace = shell.get("workspace")
    st.markdown(f'<div class="isi-eyebrow">{product["code"]} · AI</div>', unsafe_allow_html=True)
    # Shared AI Foundation is the accepted infrastructure authority.
    st.subheader("AI pomoć i pregled dokaza")
    st.caption(
        "Provider gateway, model/prompt registry, policy guard, provenance, structured output i RAG namespace izolacija."
    )

    scope = _scope(shell)
    if scope is None:
        return
    organization_id, product_code, workspace_id = scope
    st.info(f"Organizacija: {organization['name']} · Platforma: {product_code} · Workspace: {workspace['name']}")

    capability = _safe_call(
        ai_api.capabilities,
        token,
        organization_id=organization_id,
        product_code=product_code,
        workspace_id=workspace_id,
    )
    if capability is None:
        return
    models = _safe_call(
        ai_api.models,
        token,
        organization_id=organization_id,
        product_code=product_code,
        workspace_id=workspace_id,
    )
    prompts = _safe_call(
        ai_api.prompts,
        token,
        organization_id=organization_id,
        product_code=product_code,
        workspace_id=workspace_id,
    )
    jobs = _safe_call(
        ai_api.jobs,
        token,
        organization_id=organization_id,
        product_code=product_code,
        workspace_id=workspace_id,
    )
    if models is None or prompts is None or jobs is None:
        return

    _render_capability(capability)
    _render_registry(models, prompts)
    _render_jobs(jobs)
    selection_key = "ai_job:" + hashlib.sha256(json.dumps(scope).encode()).hexdigest()
    if st.session_state.get("ai_job:active") != selection_key:
        st.session_state["ai_job:active"] = selection_key
        st.session_state[selection_key + ":generation"] = st.session_state.get(selection_key + ":generation", 0) + 1
    if jobs:
        identities = {item["id"]: item for item in jobs}
        selected = st.selectbox(
            "AI job za pregled rezultata",
            list(identities),
            index=None,
            key=selection_key + ":" + str(st.session_state.get(selection_key + ":generation", 0)),
        )
        if selected:
            current = _safe_call(
                ai_api.job,
                token,
                scope=dict(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
                job_id=selected,
            )
            if current is not None:
                render_evidence("Izabrani AI rezultat i trag", current)
            if "analysis.read" in product.get("permission_codes", []):
                explanation = _safe_call(
                    ai_api.evidence_get,
                    token,
                    scope=dict(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
                    kind="job_xai",
                    record_id=selected,
                )
                if explanation is not None:
                    render_evidence("Pokušaji, fallback i nedostupna objašnjenja", explanation)
    render_ai_governance(
        token=token,
        shell=shell,
        scope=dict(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    _render_local_ollama_diagnostic(token, shell, scope, capability, models)
