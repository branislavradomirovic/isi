from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from typing import Any

import streamlit as st

from src.streamlit_app import api_client
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired
from src.streamlit_app.selection import Selection, default_selection, organization_by_id, product_by_code
from src.streamlit_app.style import apply_shell_css
from src.streamlit_app.data_workspace import render_data_workspace
from src.streamlit_app.ai_workspace import render_ai_workspace
from src.streamlit_app.simpa_workspace import render_ordo_indicator_placeholder, render_simpa_indicators, render_simpa_overview
from src.streamlit_app.simpa_analytics_workspace import render_simpa_analytics
from src.streamlit_app.ordo_analytics_workspace import render_ordo_analytics
from src.streamlit_app.reporting_workspace import render_reporting
from src.streamlit_app.administration_workspace import render_administration
from src.streamlit_app.ordo_workspace import render_ordo_indicators, render_ordo_overview


TOKEN_KEY = "isi_access_token"
CONTEXT_KEY = "isi_app_context"
ORG_KEY = "isi_selected_org_id"
PRODUCT_KEY = "isi_selected_product"
WORKSPACE_KEY = "isi_selected_workspace_id"
NAV_KEY = "isi_shell_navigation"

REPO_ROOT = Path(__file__).resolve().parents[2]
ISI_LOGO = REPO_ROOT / "src/public/static/img/brand/isi-logo-transparent.svg"
SIMPA_MARK = REPO_ROOT / "src/public/static/img/simpa-mark.svg"
ORDO_MARK = REPO_ROOT / "src/public/static/img/ordo-mark.svg"

# Backward-compatible ISI-02C integration markers.
# Runtime HTTP calls remain centralized in src.streamlit_app.api_client.
LEGACY_AUTH_LOGIN_ROUTE = "/api/v1/auth/login"
LEGACY_APP_CONTEXT_ROUTE = "/api/v1/app-context"
LEGACY_SIMPA_WORKSPACE_LABEL = "SIMPA Workspace"
LEGACY_ORDO_WORKSPACE_LABEL = "ORDO Workspace"


st.set_page_config(
    page_title="ISI Platform",
    page_icon="◌",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_shell_css()


def _clear_auth_state() -> None:
    for key in (TOKEN_KEY, CONTEXT_KEY, ORG_KEY, PRODUCT_KEY, WORKSPACE_KEY, NAV_KEY):
        st.session_state.pop(key, None)


def _token() -> str | None:
    value = st.session_state.get(TOKEN_KEY)
    return str(value) if value else None


def _brand_markup(*, compact: bool = False) -> str:
    if not ISI_LOGO.exists():
        return '<div class="isi-brand-fallback"><strong>ISI</strong><span>Institut za socijalnu inkluziju</span></div>'
    encoded = b64encode(ISI_LOGO.read_bytes()).decode("ascii")
    size_class = " compact" if compact else ""
    return (
        f'<div class="isi-brand-lockup{size_class}">'
        f'<img src="data:image/svg+xml;base64,{encoded}" alt="ISI — Institut za socijalnu inkluziju">'
        '</div>'
    )


def _brand_header(*, compact: bool = False) -> None:
    st.markdown(_brand_markup(compact=compact), unsafe_allow_html=True)


def _render_login() -> None:
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        _brand_header()
        st.markdown('<div class="isi-eyebrow">Privatna ISI platforma</div>', unsafe_allow_html=True)
        st.markdown('<h1 class="isi-shell-title">Pristup platformama SIMPA i ORDO</h1>', unsafe_allow_html=True)
        st.caption("Prijavite se institucionalnim nalogom. Pristup platformama zavisi od organizacije, product entitlement-a i dodeljenih rola.")
        with st.form("isi_login_form", clear_on_submit=False):
            email = st.text_input("Email", autocomplete="email")
            password = st.text_input("Lozinka", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Prijavi se", use_container_width=True)
        if submitted:
            try:
                result = api_client.login(email, password)
            except AuthenticationRequired as exc:
                st.error(str(exc))
            except ApiUnavailable as exc:
                st.error(str(exc))
            else:
                st.session_state[TOKEN_KEY] = result["access_token"]
                for key in (CONTEXT_KEY, ORG_KEY, PRODUCT_KEY, WORKSPACE_KEY, NAV_KEY):
                    st.session_state.pop(key, None)
                st.rerun()


def _load_context() -> dict[str, Any] | None:
    cached = st.session_state.get(CONTEXT_KEY)
    if cached is not None:
        return cached
    token = _token()
    if not token:
        return None
    try:
        context = api_client.app_context(token)
    except AuthenticationRequired:
        _clear_auth_state()
        st.rerun()
    except AccessDenied as exc:
        st.error(str(exc))
        return None
    except ApiUnavailable as exc:
        st.error(str(exc))
        return None
    st.session_state[CONTEXT_KEY] = context

    default = default_selection(context)
    if default is not None:
        st.session_state[ORG_KEY] = default.organization_id
        st.session_state[PRODUCT_KEY] = default.product_code
        if default.workspace_id:
            st.session_state[WORKSPACE_KEY] = default.workspace_id
        else:
            st.session_state.pop(WORKSPACE_KEY, None)
    return context


def _logout() -> None:
    token = _token()
    if token:
        try:
            api_client.logout(token)
        except ApiUnavailable:
            pass
    _clear_auth_state()
    st.rerun()


def _render_no_access(context: dict[str, Any]) -> None:
    _brand_header(compact=True)
    st.markdown('<div class="isi-eyebrow">Pristup nije dodeljen</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Nalog je aktivan, ali nema pristup SIMPA ili ORDO platformi.</h1>', unsafe_allow_html=True)
    st.write("Administrator organizacije treba da dodeli odgovarajući product entitlement, membership product access i rolu.")
    st.caption(f"{context.get('display_name', '')} · {context.get('email', '')}")
    if st.button("Odjavi se"):
        _logout()


def _choose_selection(context: dict[str, Any]) -> Selection | None:
    organizations = context.get("organizations", [])
    current = default_selection(
        context,
        organization_id=st.session_state.get(ORG_KEY),
        product_code=st.session_state.get(PRODUCT_KEY),
        workspace_id=st.session_state.get(WORKSPACE_KEY),
    )
    if current is None:
        return None

    org_ids = [str(item["id"]) for item in organizations]
    if len(organizations) > 1:
        org_id = st.sidebar.selectbox(
            "Organizacija",
            org_ids,
            index=org_ids.index(current.organization_id),
            format_func=lambda value: organization_by_id(context, value)["name"],
        )
    else:
        org_id = org_ids[0]
        st.sidebar.caption("Organizacija")
        st.sidebar.markdown(f"**{organizations[0]['name']}**")

    organization = organization_by_id(context, org_id)
    assert organization is not None
    products = organization.get("products", [])
    product_codes = [item["code"] for item in products]
    remembered_product = st.session_state.get(PRODUCT_KEY)
    product_code = remembered_product if remembered_product in product_codes else product_codes[0]

    if len(products) > 1:
        st.sidebar.caption("Platforma")
        product_columns = st.sidebar.columns(len(product_codes))
        selected_product = product_code
        for column, code in zip(product_columns, product_codes):
            if column.button(
                code,
                key=f"isi_product_button_{code}",
                type="primary" if code == product_code else "secondary",
                use_container_width=True,
            ):
                selected_product = code
        if selected_product != product_code:
            st.session_state[PRODUCT_KEY] = selected_product
            st.session_state.pop(WORKSPACE_KEY, None)
            st.session_state.pop(NAV_KEY, None)
            st.rerun()
        product_code = selected_product
    else:
        st.sidebar.caption("Platforma")
        st.sidebar.markdown(f"**{product_code}**")

    product = product_by_code(organization, product_code)
    assert product is not None
    workspaces = product.get("workspaces", [])
    workspace_id = None
    if len(workspaces) == 1:
        workspace_id = str(workspaces[0]["id"])
        st.sidebar.caption("Workspace")
        st.sidebar.markdown(f"**{workspaces[0]['name']}**")
    elif len(workspaces) > 1:
        workspace_ids = [str(item["id"]) for item in workspaces]
        remembered_workspace = st.session_state.get(WORKSPACE_KEY)
        if remembered_workspace not in workspace_ids:
            remembered_workspace = workspace_ids[0]
        workspace_id = st.sidebar.selectbox(
            "Workspace",
            workspace_ids,
            index=workspace_ids.index(remembered_workspace),
            format_func=lambda value: next(item["name"] for item in workspaces if str(item["id"]) == value),
        )
    else:
        st.sidebar.caption("Workspace")
        st.sidebar.info("Još nije konfigurisan.")

    st.session_state[ORG_KEY] = org_id
    st.session_state[PRODUCT_KEY] = product_code
    if workspace_id:
        st.session_state[WORKSPACE_KEY] = workspace_id
    else:
        st.session_state.pop(WORKSPACE_KEY, None)

    return Selection(org_id, product_code, workspace_id)


def _load_shell(selection: Selection) -> dict[str, Any] | None:
    token = _token()
    if not token:
        return None
    try:
        return api_client.app_shell(
            token,
            organization_id=selection.organization_id,
            product_code=selection.product_code,
            workspace_id=selection.workspace_id,
        )
    except AuthenticationRequired:
        _clear_auth_state()
        st.rerun()
    except AccessDenied as exc:
        st.error(str(exc))
        st.session_state.pop(WORKSPACE_KEY, None)
        return None
    except ApiUnavailable as exc:
        st.error(str(exc))
        return None


def _sidebar_identity(context: dict[str, Any]) -> None:
    st.sidebar.markdown(_brand_markup(compact=True), unsafe_allow_html=True)
    st.sidebar.markdown(f"**{context['display_name']}**")
    st.sidebar.caption(context["email"])
    if st.sidebar.button("Odjavi se", use_container_width=True):
        _logout()


def _navigation(shell: dict[str, Any]) -> str:
    enabled = [item for item in shell.get("navigation", []) if item.get("enabled")]
    codes = [item["code"] for item in enabled]
    current = st.session_state.get(NAV_KEY)
    if current not in codes:
        current = codes[0] if codes else "overview"
    st.sidebar.caption("Navigacija")
    selected_code = current
    for item in enabled:
        code = item["code"]
        if st.sidebar.button(
            item["label_sr"],
            key=f"isi_nav_button_{code}",
            type="primary" if code == current else "secondary",
            use_container_width=True,
        ):
            selected_code = code
    if selected_code != current:
        st.session_state[NAV_KEY] = selected_code
        st.rerun()
    st.session_state[NAV_KEY] = selected_code
    return selected_code


def _product_mark(product_code: str) -> None:
    path = SIMPA_MARK if product_code == "SIMPA" else ORDO_MARK
    if path.exists():
        st.image(str(path), width=92)


def _render_overview(shell: dict[str, Any]) -> None:
    product = shell["product"]
    organization = shell["organization"]
    workspace = shell.get("workspace")
    product_code = product["code"]

    mark_col, title_col = st.columns([0.14, 0.86], vertical_alignment="center")
    with mark_col:
        _product_mark(product_code)
    with title_col:
        st.markdown(f'<div class="isi-eyebrow">{product_code} workspace</div>', unsafe_allow_html=True)
        st.markdown(
            f'<h1 class="isi-shell-title">{"Socijalna politika zasnovana na dokazima" if product_code == "SIMPA" else "Arhitektura odluka zasnovanih na podacima i modelima"}</h1>',
            unsafe_allow_html=True,
        )
        st.caption(f"ISI Platform · {organization['name']}")

    if workspace is None:
        st.info("Pristup platformi je aktivan, ali workspace još nije konfigurisan ili izabran. Domain operacije ostaju zaključane dok workspace ne postoji.")
    else:
        st.markdown(
            f'<div class="isi-product-band {product_code.lower()}"><strong>{workspace["name"]}</strong><br><span class="isi-shell-kicker">Aktivni workspace · {product_code}</span></div>',
            unsafe_allow_html=True,
        )

    role_codes = product.get("role_codes", [])
    permission_codes = product.get("permission_codes", [])
    st.markdown(" ".join(f'<span class="isi-chip">{role}</span>' for role in role_codes) or '<span class="isi-chip">bez role</span>', unsafe_allow_html=True)
    st.caption(f"Aktivnih dozvola: {len(permission_codes)} · product entitlement: {product_code}")

    st.markdown("### Shared platform foundation")
    cols = st.columns(3)
    cards = [
        ("Identitet i pristup", "Jedan ISI nalog, tenant kontekst, role i product entitlement ostaju odvojeni."),
        ("Workspace kontekst", "Sve naredne data, analytics i reporting operacije biće vezane za organizaciju, proizvod i workspace."),
        ("Human accountability", "AI i analitika će podržavati stručni rad; odgovornost i institucionalne odluke ostaju ljudske."),
    ]
    for col, (title, body) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="isi-foundation-card"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)


def _render_future_section(shell: dict[str, Any], nav_code: str) -> None:
    item = next(item for item in shell["navigation"] if item["code"] == nav_code)
    st.markdown(f'<div class="isi-eyebrow">{shell["product"]["code"]} · {item["label_sr"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="isi-shell-title">{item["label_sr"]}</h1>', unsafe_allow_html=True)
    st.info(
        f"Ovaj ulaz je aktiviran u shared shell-u na osnovu dozvola, ali funkcionalni modul se implementira u {item['implementation_phase']}. "
        "Ovaj ekran namerno ne prikazuje izmišljene podatke ili funkcije."
    )
    st.caption(f"Organizacija: {shell['organization']['name']}")
    if shell.get("workspace"):
        st.caption(f"Workspace: {shell['workspace']['name']}")


def _render_shell(shell: dict[str, Any], nav_code: str) -> None:
    # ISI-13 administration routing
    if nav_code == "administration":
        token = _token()
        if token:
            render_administration(token=token, shell=shell)
        return
    # ISI-12 shared reporting routing
    if nav_code == "reports":
        token = _token()
        if token:
            render_reporting(token=token, shell=shell)
        return
    # ISI-09 SIMPA analytics routing
    product_code = shell.get("product", {}).get("code")
    if nav_code == "analysis":
        if product_code == "SIMPA":
            token = _token()
            if token:
                render_simpa_analytics(token=token, shell=shell)
        else:
            token = _token()
            if token:
                render_ordo_analytics(token=token, shell=shell)
        return
    # ISI-08 SIMPA domain routing
    product_code = shell.get("product", {}).get("code")
    # ISI-10 ORDO domain routing
    if product_code == "ORDO" and nav_code == "overview":
        token = _token()
        if token:
            render_ordo_overview(token=token, shell=shell)
        return
    if product_code == "SIMPA" and nav_code == "overview":
        token = _token()
        if token:
            render_simpa_overview(token=token, shell=shell)
        return
    if nav_code == "indicators":
        if product_code == "SIMPA":
            token = _token()
            if token:
                render_simpa_indicators(token=token, shell=shell)
        else:
            token = _token()
            if token:
                render_ordo_indicators(token=token, shell=shell)
        return
    if nav_code == "overview":
        _render_overview(shell)
    elif nav_code == "data":
        token = _token()
        if token:
            render_data_workspace(token=token, shell=shell)
    elif nav_code == "ai":
        token = _token()
        if token:
            render_ai_workspace(token=token, shell=shell)
    else:
        _render_future_section(shell, nav_code)


if not _token():
    _render_login()
    st.stop()

context = _load_context()
if context is None:
    st.stop()
if not context.get("organizations"):
    _render_no_access(context)
    st.stop()

_sidebar_identity(context)
selection = _choose_selection(context)
if selection is None:
    _render_no_access(context)
    st.stop()

shell = _load_shell(selection)
if shell is None:
    st.stop()

nav_code = _navigation(shell)
_render_shell(shell, nav_code)
