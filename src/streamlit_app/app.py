from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
TOKEN_KEY = "isi_access_token"
CONTEXT_KEY = "isi_app_context"
ORG_KEY = "isi_selected_org_id"
PRODUCT_KEY = "isi_selected_product"
WORKSPACE_KEY = "isi_selected_workspace_id"


st.set_page_config(page_title="ISI Platform", layout="wide")


def _headers() -> dict[str, str]:
    token = st.session_state.get(TOKEN_KEY)
    return {"Authorization": f"Bearer {token}"} if token else {}


def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(method, f"{API_BASE_URL}{path}", timeout=10.0, **kwargs)


def _clear_auth_state() -> None:
    for key in (TOKEN_KEY, CONTEXT_KEY, ORG_KEY, PRODUCT_KEY, WORKSPACE_KEY):
        st.session_state.pop(key, None)


def _login() -> None:
    st.title("ISI Platform")
    st.caption("Institut za socijalnu inkluziju — pristup platformama SIMPA i ORDO")
    with st.form("isi_login_form", clear_on_submit=False):
        email = st.text_input("Email", autocomplete="email")
        password = st.text_input("Lozinka", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Prijavi se", use_container_width=True)
    if not submitted:
        return
    try:
        response = _request("POST", "/api/v1/auth/login", json={"email": email, "password": password})
    except httpx.HTTPError:
        st.error("Servis za prijavu trenutno nije dostupan.")
        return
    if response.status_code != 200:
        st.error("Email ili lozinka nisu ispravni, ili nalog nije spreman za prijavu.")
        return
    st.session_state[TOKEN_KEY] = response.json()["access_token"]
    st.session_state.pop(CONTEXT_KEY, None)
    st.rerun()


def _load_context() -> dict[str, Any] | None:
    cached = st.session_state.get(CONTEXT_KEY)
    if cached is not None:
        return cached
    try:
        response = _request("GET", "/api/v1/app-context", headers=_headers())
    except httpx.HTTPError:
        st.error("ISI API trenutno nije dostupan.")
        return None
    if response.status_code == 401:
        _clear_auth_state()
        st.rerun()
    if response.status_code != 200:
        st.error("Nije moguće učitati pristupni kontekst.")
        return None
    context = response.json()
    st.session_state[CONTEXT_KEY] = context
    route = context.get("initial_route", {})
    if route.get("mode") in {"product", "workspace"}:
        st.session_state[ORG_KEY] = route.get("organization_id")
        st.session_state[PRODUCT_KEY] = route.get("product_code")
        st.session_state[WORKSPACE_KEY] = route.get("workspace_id")
    return context


def _organization_by_id(context: dict[str, Any], organization_id: str | None) -> dict[str, Any] | None:
    return next((item for item in context.get("organizations", []) if item["id"] == organization_id), None)


def _product_by_code(organization: dict[str, Any], product_code: str | None) -> dict[str, Any] | None:
    return next((item for item in organization.get("products", []) if item["code"] == product_code), None)


def _selector(context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None] | None:
    organizations = context.get("organizations", [])
    if not organizations:
        st.warning("Nalog je aktivan, ali još nema dodeljen pristup platformama SIMPA ili ORDO.")
        st.caption("Administrator organizacije treba da dodeli product access i odgovarajuću rolu.")
        return None

    org_ids = [item["id"] for item in organizations]
    current_org_id = st.session_state.get(ORG_KEY)
    if current_org_id not in org_ids:
        current_org_id = org_ids[0]
    selected_org_id = st.sidebar.selectbox(
        "Organizacija",
        org_ids,
        index=org_ids.index(current_org_id),
        format_func=lambda value: _organization_by_id(context, value)["name"],
    )
    st.session_state[ORG_KEY] = selected_org_id
    organization = _organization_by_id(context, selected_org_id)
    assert organization is not None

    products = organization.get("products", [])
    product_codes = [item["code"] for item in products]
    current_product = st.session_state.get(PRODUCT_KEY)
    if current_product not in product_codes:
        current_product = product_codes[0]
    selected_product_code = st.sidebar.selectbox(
        "Platforma",
        product_codes,
        index=product_codes.index(current_product),
        format_func=lambda value: value,
    )
    st.session_state[PRODUCT_KEY] = selected_product_code
    product = _product_by_code(organization, selected_product_code)
    assert product is not None

    workspaces = product.get("workspaces", [])
    workspace = None
    if workspaces:
        workspace_ids = [item["id"] for item in workspaces]
        current_workspace = st.session_state.get(WORKSPACE_KEY)
        if current_workspace not in workspace_ids:
            current_workspace = workspace_ids[0]
        selected_workspace_id = st.sidebar.selectbox(
            "Workspace",
            workspace_ids,
            index=workspace_ids.index(current_workspace),
            format_func=lambda value: next(item["name"] for item in workspaces if item["id"] == value),
        )
        st.session_state[WORKSPACE_KEY] = selected_workspace_id
        workspace = next(item for item in workspaces if item["id"] == selected_workspace_id)
    else:
        st.session_state.pop(WORKSPACE_KEY, None)

    return organization, product, workspace


def _logout() -> None:
    try:
        _request("POST", "/api/v1/auth/logout", headers=_headers())
    except httpx.HTTPError:
        pass
    _clear_auth_state()
    st.rerun()


def _render_shell(context: dict[str, Any], organization: dict[str, Any], product: dict[str, Any], workspace: dict[str, Any] | None) -> None:
    st.sidebar.markdown(f"**{context['display_name']}**")
    st.sidebar.caption(context["email"])
    if st.sidebar.button("Odjavi se", use_container_width=True):
        _logout()

    st.title(product["code"])
    st.caption(f"ISI Platform · {organization['name']}")
    if workspace is not None:
        st.subheader(workspace["name"])
    else:
        st.info("Pristup platformi je aktivan. Workspace još nije izabran ili kreiran.")

    roles = ", ".join(product.get("role_codes", [])) or "—"
    st.caption(f"Aktivne role: {roles}")

    if product["code"] == "SIMPA":
        st.markdown("### SIMPA Workspace")
        st.write("Shared authenticated shell je aktivan. SIMPA domain funkcije biće uvedene u ISI-08/09.")
    else:
        st.markdown("### ORDO Workspace")
        st.write("Shared authenticated shell je aktivan. ORDO domain funkcije biće uvedene u ISI-10/11.")


if not st.session_state.get(TOKEN_KEY):
    _login()
    st.stop()

context = _load_context()
if context is None:
    st.stop()

selection = _selector(context)
if selection is None:
    st.sidebar.markdown(f"**{context['display_name']}**")
    st.sidebar.caption(context["email"])
    if st.sidebar.button("Odjavi se", use_container_width=True):
        _logout()
    st.stop()

_render_shell(context, *selection)
