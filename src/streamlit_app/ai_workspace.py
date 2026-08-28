from __future__ import annotations

from typing import Any

import streamlit as st

from src.streamlit_app import ai_api
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
                use_container_width=True,
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
                use_container_width=True,
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
        use_container_width=True,
        hide_index=True,
    )
    latest = jobs[0]
    if latest.get("structured_output"):
        st.caption("Najnoviji strukturirani rezultat")
        st.json(latest["structured_output"])


def _render_local_ollama_diagnostic(
    token: str,
    shell: dict[str, Any],
    scope: tuple[str, str, str],
    capability: dict[str, Any],
    models: list[dict[str, Any]],
) -> None:
    organization_id, product_code, workspace_id = scope
    ollama_models = [
        item
        for item in models
        if item.get("provider_type") == "ollama" and item.get("purpose") == "chat"
    ]
    if not ollama_models:
        st.info("Lokalni Ollama chat model nije registrovan za aktivni proizvod.")
        return
    model = next(
        (item for item in ollama_models if item.get("model_key") == "isi-ollama-chat-default"),
        ollama_models[0],
    )
    st.markdown("### Lokalni Ollama foundation test")
    st.caption(
        f"Privremeni QA model: {model['model_name']} · provider: Ollama. "
        "Ovo proverava shared AI infrastrukturu; produkcijski SIMPA/ORDO modeli biće izabrani kasnije."
    )
    sensitivity = st.selectbox("Sensitivity", ["internal", "sensitive"], index=0, key="isi07_sensitivity")
    if product_code == "SIMPA" and sensitivity == "sensitive":
        st.caption("SIMPA sensitive zahtev ostaje prinudno local_only i zahteva human review.")
    if capability.get("development_stub_enabled"):
        st.caption("Deterministički QA stub ostaje dostupan samo za automatske policy/namespace kontrole.")
    if st.button(
        "Pokreni lokalni Ollama test",
        key="isi07_ollama_diagnostic_button",
        type="primary",
        use_container_width=True,
    ):
        result = _safe_call(
            ai_api.create_job,
            token,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
            input_text=f"Local Ollama infrastructure diagnostic for {product_code}",
            sensitivity=sensitivity,
            model_key=model["model_key"],
        )
        if result is not None:
            st.success(
                f"Ollama test završen: status={result['status']} · policy={result['effective_provider_policy']} · "
                f"provider={result.get('provider_name') or '—'} · model={result.get('model_name') or '—'}"
            )
            st.rerun()

def render_ai_workspace(*, token: str, shell: dict[str, Any]) -> None:
    product = shell["product"]
    organization = shell["organization"]
    workspace = shell.get("workspace")
    st.markdown(f'<div class="isi-eyebrow">{product["code"]} · AI</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Shared AI Foundation</h1>', unsafe_allow_html=True)
    st.caption("Provider gateway, model/prompt registry, policy guard, provenance, structured output i RAG namespace izolacija.")

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
    _render_local_ollama_diagnostic(token, shell, scope, capability, models)
