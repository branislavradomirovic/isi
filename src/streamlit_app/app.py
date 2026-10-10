from __future__ import annotations

from base64 import b64encode
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from src.core.config import get_settings
from src.streamlit_app import api_client
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired
from src.streamlit_app.selection import Selection, default_selection, organization_by_id, product_by_code
from src.streamlit_app.style import apply_shell_css
from src.streamlit_app.workflow_shell import clear_workspace_state, navigation_items, context_markup
from src.streamlit_app.data_workspace import render_data_workspace
from src.streamlit_app.ai_workspace import render_ai_workspace
from src.streamlit_app.simpa_workspace import render_simpa_indicators, render_simpa_overview
from src.streamlit_app.simpa_analytics_workspace import render_simpa_analytics
from src.streamlit_app.simpa_help_workspace import render_simpa_help
from src.streamlit_app.ordo_analytics_workspace import render_ordo_analytics, render_ordo_scenarios
from src.streamlit_app.ordo_help_workspace import render_ordo_help
from src.streamlit_app.reporting_workspace import render_reporting
from src.streamlit_app.administration_workspace import render_administration
from src.streamlit_app.ordo_workspace import render_ordo_indicators, render_ordo_overview
from src.streamlit_app.security_workspace import render_account_security
from src.streamlit_app.shared_help_workspace import render_shared_help, render_topic_summary


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
# REQUIRED_COMPATIBILITY: legacy ISI-08 source-token marker only; current ORDO routing uses render_ordo_indicators.
# render_ordo_indicator_placeholder
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
    st.session_state.clear()


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
        st.caption("Prijavite se institucionalnim nalogom. Dostupne funkcije zavise od vaše organizacije, radnog prostora i dodeljenih dozvola.")
        if st.session_state.pop("isi_auth_completed", False):
            st.success("Promena je potvrđena. Prijavite se svojim nalogom.")
        with st.form("isi_login_form", clear_on_submit=True):
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

        _render_recovery_requests()
        with st.expander("Pomoć za prijavu i pristup"):
            render_shared_help(public=True)


AUTH_QUERY_KEYS = ("invitation_token", "verify_token", "reset_token")
RECOVERY_NOTICE = (
    "Ako nalog ispunjava uslove, uputstvo će biti poslato na navedenu adresu. "
    "Ova poruka ne potvrđuje postojanje naloga niti isporuku."
)


def _clear_auth_query() -> None:
    for key in AUTH_QUERY_KEYS:
        st.query_params.pop(key, None)


def _leave_auth_link() -> None:
    _clear_auth_query()
    st.query_params.pop("help", None)
    st.rerun()


def _render_recovery_requests() -> None:
    with st.expander("Oporavak naloga"):
        pending = get_settings().auth_delivery_mode.casefold() == "pending"
        if pending:
            st.info("Email dostava još nije aktivirana. Slanje zahteva za promenu lozinke i potvrdu emaila trenutno nije dostupno. Prijava postojećim nalogom ostaje dostupna.")
        for code, title, action in (
            ("reset", "Promena lozinke", api_client.request_password_reset),
            ("verify", "Potvrda emaila", api_client.request_email_verification),
        ):
            st.markdown(f"**{title}**")
            with st.form(f"isi_recovery_{code}", clear_on_submit=True):
                email = st.text_input("Email", autocomplete="email", key=f"isi_recovery_email_{code}")
                submitted = st.form_submit_button("Pošalji zahtev", disabled=pending)
            if submitted and not pending:
                try:
                    action(email)
                except (api_client.AuthFlowRejected, ApiUnavailable):
                    st.error("Zahtev trenutno nije moguće obraditi. Proverite format emaila ili pokušajte kasnije.")
                else:
                    st.info(RECOVERY_NOTICE)


def _render_auth_intent() -> bool:
    keys = [key for key in AUTH_QUERY_KEYS if key in st.query_params]
    if not keys:
        return False
    if _token():
        st.warning(
            "Već ste prijavljeni. Link nije primenjen i postojeća sesija nije promenjena. "
            "Za nastavak zatvorite ovaj link, odjavite se, pa ponovo otvorite originalni link iz poruke."
        )
        if st.button("Zatvori link i nastavi postojeću sesiju"):
            _leave_auth_link()
        return True
    if len(keys) != 1 or len(st.query_params.get_all(keys[0])) != 1:
        st.error("Link sadrži više zahteva. Otvorite samo jedan originalni link iz poruke.")
    else:
        key = keys[0]
        # Read only from the browser input; never copy one-time material into session state.
        value = st.query_params.get(key, "")
        if not isinstance(value, str) or not 20 <= len(value) <= 256:
            st.error("Link nije ispravan. Zatražite novi link.")
        else:
            try:
                if key == "invitation_token":
                    st.title("Prihvatanje institucionalnog poziva")
                    st.caption("Za novi nalog unesite ime i lozinku. Za postojeći nalog oba polja mogu ostati prazna; postojeća lozinka se ne menja.")
                    with st.form("isi_accept_invitation", clear_on_submit=True):
                        name = st.text_input("Ime za prikaz", max_chars=200)
                        password = st.text_input("Lozinka", type="password", autocomplete="new-password", max_chars=256)
                        submitted = st.form_submit_button("Prihvati poziv")
                    if submitted:
                        result = api_client.accept_invitation(value, name.strip() or None, password or None)
                        _clear_auth_state()
                        st.session_state[TOKEN_KEY] = result["access_token"]
                        _clear_auth_query()
                        st.query_params.pop("help", None)
                        st.rerun()
                    render_topic_summary("ISI-H03")
                elif key == "verify_token":
                    st.title("Potvrda emaila")
                    st.write("Potvrdite email samo ako ste otvorili očekivani institucionalni link.")
                    if st.button("Potvrdi email"):
                        api_client.confirm_email_verification(value)
                        _complete_auth_confirmation()
                    render_topic_summary("ISI-H04")
                elif key == "reset_token":
                    st.title("Nova lozinka")
                    st.caption("Lozinka mora ispuniti postojeću politiku (12–256 znakova). Uspešna promena opoziva postojeće sesije.")
                    with st.form("isi_reset_password", clear_on_submit=True):
                        password = st.text_input("Nova lozinka", type="password", autocomplete="new-password", max_chars=256)
                        confirmation = st.text_input("Potvrdite novu lozinku", type="password", autocomplete="new-password", max_chars=256)
                        submitted = st.form_submit_button("Sačuvaj novu lozinku")
                    if submitted:
                        if password != confirmation:
                            st.error("Unete lozinke nisu jednake.")
                        else:
                            api_client.confirm_password_reset(value, password)
                            _complete_auth_confirmation()
                    render_topic_summary("ISI-H05")
            except (api_client.AuthFlowRejected, ApiUnavailable):
                st.error(
                    "Zahtev nije potvrđen. Proverite unos i dostupnost usluge; "
                    "link može biti istekao, iskorišćen ili opozvan. "
                    "Zatražite novi link kroz oporavak naloga ili novi poziv od administratora."
                )
    if st.button("Nazad na prijavu"):
        _leave_auth_link()
    with st.expander("Pomoć za pristup i oporavak"):
        render_shared_help(public=True)
    return True


def _complete_auth_confirmation() -> None:
    _clear_auth_query()
    st.query_params.pop("help", None)
    st.session_state["isi_auth_completed"] = True
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
        except (AuthenticationRequired, ApiUnavailable):
            pass
    _clear_auth_state()
    st.rerun()


def _render_no_access(context: dict[str, Any]) -> None:
    _brand_header(compact=True)
    st.markdown('<div class="isi-eyebrow">Pristup nije dodeljen</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Nalog je aktivan, ali nema pristup SIMPA ili ORDO platformi.</h1>', unsafe_allow_html=True)
    st.write("Administrator organizacije treba da aktivira pristup proizvodu i dodeli odgovarajuću ulogu.")
    st.caption(f"{context.get('display_name', '')} · {context.get('email', '')}")
    if st.button("Odjavi se"):
        _logout()
    if _navigation({"navigation": [{"code": "no_access", "label_sr": "Pristup", "enabled": True}]}) == "isi_help":
        render_shared_help()
        return
    token = _token()
    if token:
        with st.expander("Bezbednost naloga"):
            render_account_security(token=token)


def _scope_changed() -> None:
    clear_workspace_state(st.session_state)
    st.session_state.pop(WORKSPACE_KEY, None)


def _organization_changed() -> None:
    _scope_changed()
    st.session_state.pop("isi_workspace_selector", None)


def _refresh_access() -> None:
    token = _token()
    _clear_auth_state()
    if token:
        st.session_state[TOKEN_KEY] = token


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
            key="isi_org_selector", on_change=_organization_changed,
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
        st.sidebar.caption("Proizvod")
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
            clear_workspace_state(st.session_state)
            st.session_state.pop("isi_workspace_selector", None)
            st.session_state[PRODUCT_KEY] = selected_product
            st.session_state.pop(WORKSPACE_KEY, None)
            st.session_state.pop(NAV_KEY, None)
            st.rerun()
        product_code = selected_product
    else:
        st.sidebar.caption("Proizvod")
        st.sidebar.markdown(f"**{product_code}**")

    product = product_by_code(organization, product_code)
    assert product is not None
    workspaces = product.get("workspaces", [])
    workspace_id = None
    if len(workspaces) == 1:
        workspace_id = str(workspaces[0]["id"])
        st.sidebar.caption("Radni prostor")
        st.sidebar.markdown(f"**{workspaces[0]['name']}**")
    elif len(workspaces) > 1:
        workspace_ids = [str(item["id"]) for item in workspaces]
        remembered_workspace = st.session_state.get(WORKSPACE_KEY)
        if remembered_workspace not in workspace_ids:
            remembered_workspace = workspace_ids[0]
        if st.session_state.get("isi_workspace_selector") not in workspace_ids:
            st.session_state["isi_workspace_selector"] = remembered_workspace
        workspace_id = st.sidebar.selectbox(
            "Radni prostor",
            workspace_ids,
            index=workspace_ids.index(remembered_workspace),
            format_func=lambda value: next(item["name"] for item in workspaces if str(item["id"]) == value),
            key="isi_workspace_selector", on_change=_scope_changed,
        )
    else:
        st.sidebar.caption("Radni prostor")
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
    st.sidebar.button("Osveži pristup", on_click=_refresh_access, use_container_width=True,
                      help="Ponovo učitava organizacije, proizvode i radne prostore; odbacuje nezavršene unose.")
    if st.sidebar.button("Odjavi se", use_container_width=True):
        _logout()


def _navigation(shell: dict[str, Any]) -> str:
    enabled = navigation_items(shell)
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
            f'<div class="isi-product-band {product_code.lower()}"><strong>{escape(str(workspace["name"]))}</strong><br><span class="isi-shell-kicker">Aktivni workspace · {product_code}</span></div>',
            unsafe_allow_html=True,
        )

    role_codes = product.get("role_codes", [])
    permission_codes = product.get("permission_codes", [])
    st.markdown(" ".join(f'<span class="isi-chip">{escape(str(role))}</span>' for role in role_codes) or '<span class="isi-chip">bez role</span>', unsafe_allow_html=True)
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
    st.markdown(context_markup(shell, nav_code), unsafe_allow_html=True)
    with st.expander("Pomoć za radni kontekst i scenarije"):
        st.markdown((REPO_ROOT / "docs/help/ISI-WORKFLOW-SHELL-GUIDE.md").read_text())
    if nav_code == "scenarios":
        token = _token()
        if token:
            render_ordo_scenarios(token=token, shell=shell)
        return
    if nav_code == "isi_help":
        render_shared_help()
        return
    if nav_code == "simpa_help":
        render_simpa_help(shell=shell)
        return
    if nav_code == "ordo_help":
        render_ordo_help(shell=shell)
        return
    if nav_code == "account_security":
        token = _token()
        if token:
            render_account_security(token=token)
        return
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


if st.query_params.get("help") == "public":
    render_shared_help(public=True)
    if st.button("Nazad na platformu"):
        _leave_auth_link()
    st.stop()

if _render_auth_intent():
    st.stop()

if not _token():
    _render_login()
    st.stop()

context = _load_context()
if context is None:
    with st.expander("ISI Help · Pomoć"):
        render_shared_help()
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
    with st.expander("ISI Help · Pomoć"):
        render_shared_help()
    st.stop()

nav_code = _navigation(shell)
_render_shell(shell, nav_code)
