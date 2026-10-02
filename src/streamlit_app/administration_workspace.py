from __future__ import annotations

import re

import streamlit as st

from src.streamlit_app.shared_help_workspace import render_topic_summary

from src.streamlit_app import administration_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except AccessDenied as exc:
        st.error(str(exc))
    except ApiUnavailable as exc:
        st.error(str(exc))
    return None


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def render_administration(*, token: str, shell: dict) -> None:
    render_topic_summary("ISI-H09")
    product = shell["product"]
    product_code = product["code"]
    organization_id = str(shell["organization"]["id"])

    st.markdown(f'<div class="isi-eyebrow">ISI · Administracija · {product_code}</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Administracija</h1>', unsafe_allow_html=True)
    st.caption("Organizacioni pristup, članovi, role, product access i workspace-i. Role i product entitlement ostaju odvojeni sigurnosni slojevi.")

    data = _safe(administration_api.snapshot, token, organization_id, product_code)
    if not data:
        return
    caps = data.get("capabilities", {})
    entitlement = data.get("entitlement")

    top = st.columns(4)
    top[0].metric("Organizacija", data["organization"]["name"])
    top[1].metric("Platforma", product_code)
    top[2].metric("Članovi", len(data.get("members", [])))
    top[3].metric("Workspace-i", len(data.get("workspaces", [])))
    if entitlement:
        state = "aktivno" if entitlement.get("is_active") else "neaktivno"
        st.info(f"Organization entitlement za {product_code}: **{state}**. Entitlement je read-only u ISI-13; administratori organizacije ga ne mogu menjati.")
    else:
        st.warning(f"Organizacija nema evidentiran {product_code} entitlement.")

    tabs = st.tabs(["Pregled", "Članovi", "Pozivi", "Workspace-i", "Organizacija", "Audit"])

    with tabs[0]:
        st.markdown("### Granice administracije")
        st.write("Role određuju šta član sme da radi; product access određuje kojoj platformi može da pristupi; organization entitlement ostaje platformska granica.")
        st.write("Administrativne mutacije se beleže u append-only admin audit tragu.")
        st.caption("Organization admin nije platform superadmin i ne može menjati `is_platform_admin`.")

    with tabs[1]:
        if not (caps.get("members_read") or caps.get("members_manage")):
            st.info("Nemate members.read/members.manage u ovom product kontekstu.")
        else:
            members = data.get("members", [])
            if members:
                st.dataframe([
                    {
                        "ime": item["display_name"],
                        "email": item["email"],
                        "membership": item["membership_status"],
                        f"{product_code} access": item["product_access_active"],
                        "role": ", ".join(f"{r['role_code']}[{r['scope']}]" for r in item.get("roles", [])),
                    }
                    for item in members
                ], use_container_width=True, hide_index=True)
            if caps.get("members_manage") and members:
                member_map = {item["membership_id"]: item for item in members}
                selected_id = st.selectbox("Član za upravljanje", list(member_map), format_func=lambda value: f"{member_map[value]['display_name']} · {member_map[value]['email']}")
                member = member_map[selected_id]
                c1, c2 = st.columns(2)
                if caps.get("org_wide_members_manage"):
                    desired_status = c1.selectbox("Membership status", ["active", "suspended"], index=0 if member["membership_status"] == "active" else 1, key=f"member_status_{selected_id}")
                    if c1.button("Sačuvaj membership status", key=f"member_status_save_{selected_id}"):
                        if _safe(administration_api.member_status, token, membership_id=selected_id, organization_id=organization_id, product_code=product_code, status=desired_status) is not None:
                            st.rerun()
                else:
                    c1.caption("Membership status je organization-wide kontrola i zahteva organization-wide members.manage.")
                desired_access = c2.checkbox(f"Aktivan {product_code} product access", value=bool(member["product_access_active"]), key=f"member_access_{selected_id}")
                if c2.button("Sačuvaj product access", key=f"member_access_save_{selected_id}"):
                    if _safe(administration_api.product_access, token, membership_id=selected_id, organization_id=organization_id, product_code=product_code, active=desired_access) is not None:
                        st.rerun()

                st.markdown("#### Role")
                role_catalog = [role["code"] for role in data.get("role_catalog", [])]
                role_code = st.selectbox("Rola", role_catalog, key=f"role_code_{selected_id}")
                scope_options = ["product"] + (["organization"] if caps.get("org_wide_members_manage") else [])
                scope = st.selectbox("Scope role", scope_options, key=f"role_scope_{selected_id}")
                if st.button("Dodeli rolu", key=f"assign_role_{selected_id}"):
                    if _safe(administration_api.assign_role, token, membership_id=selected_id, organization_id=organization_id, product_code=product_code, role_code=role_code, scope=scope) is not None:
                        st.rerun()
                for role in member.get("roles", []):
                    cols = st.columns([0.75, 0.25])
                    cols[0].write(f"`{role['role_code']}` · scope `{role['scope']}`")
                    role_scope = "organization" if role["scope"] == "*" else "product"
                    can_remove = role_scope == "product" or caps.get("org_wide_members_manage")
                    if can_remove and cols[1].button("Ukloni", key=f"remove_role_{role['assignment_id']}"):
                        _safe(administration_api.remove_role, token, membership_id=selected_id, assignment_id=role["assignment_id"], organization_id=organization_id, product_code=product_code)
                        st.rerun()

    with tabs[2]:
        if not caps.get("members_manage"):
            st.info("Pozive može kreirati samo član sa members.manage.")
        else:
            role_catalog = [role["code"] for role in data.get("role_catalog", []) if role["code"] != "organization_admin"]
            with st.form(f"invite_{product_code}"):
                email = st.text_input("Email za poziv")
                role_code = st.selectbox("Početna product rola", role_catalog)
                submitted = st.form_submit_button("Kreiraj razvojni poziv")
            if submitted:
                result = _safe(administration_api.invite, token, organization_id=organization_id, product_code=product_code, email=email, role_code=role_code)
                if result:
                    st.success("Poziv je kreiran sa eksplicitnim product access + role grant-om.")
                    st.rerun()
            invitations = data.get("invitations", [])
            if invitations:
                st.dataframe([{k: row.get(k) for k in ("email", "status", "product_code", "roles", "expires_at")} for row in invitations], use_container_width=True, hide_index=True)
                pending = [row for row in invitations if row["status"] == "pending"]
                for row in pending:
                    if st.button(f"Opozovi · {row['email']}", key=f"revoke_inv_{row['id']}"):
                        _safe(administration_api.revoke_invite, token, invitation_id=row["id"], organization_id=organization_id, product_code=product_code)
                        st.rerun()

    with tabs[3]:
        workspaces = data.get("workspaces", [])
        if workspaces:
            st.dataframe(workspaces, use_container_width=True, hide_index=True)
        if not caps.get("workspace_manage"):
            st.info("Nemate workspace.manage u ovom product kontekstu.")
        else:
            with st.form(f"new_workspace_{product_code}"):
                name = st.text_input("Naziv novog workspace-a")
                slug = st.text_input("Slug", value=_slugify(name))
                create = st.form_submit_button("Kreiraj workspace")
            if create:
                if _safe(administration_api.create_workspace, token, organization_id=organization_id, product_code=product_code, name=name, slug=slug) is not None:
                    st.rerun()
            for row in workspaces:
                next_status = "archived" if row["status"] == "active" else "active"
                label = "Arhiviraj" if next_status == "archived" else "Reaktiviraj"
                if st.button(f"{label} · {row['name']}", key=f"workspace_state_{row['id']}"):
                    if _safe(administration_api.workspace_status, token, workspace_id=row["id"], organization_id=organization_id, product_code=product_code, status=next_status) is not None:
                        st.rerun()

    with tabs[4]:
        org = data["organization"]
        st.write(f"**Slug:** `{org['slug']}`")
        st.write(f"**Status:** `{org['status']}`")
        if caps.get("org_wide_manage"):
            new_name = st.text_input("Naziv organizacije", value=org["name"])
            if st.button("Sačuvaj naziv organizacije"):
                if _safe(administration_api.rename_organization, token, organization_id=organization_id, product_code=product_code, name=new_name) is not None:
                    st.rerun()
        else:
            st.info("Promena naziva zahteva organization-wide organization.manage. Slug i status nisu izmenjivi u ISI-13.")

    with tabs[5]:
        if not caps.get("audit_read"):
            st.info("Nemate audit.read u ovom product kontekstu.")
        else:
            audit = data.get("audit", [])
            if audit:
                st.dataframe(audit, use_container_width=True, hide_index=True)
            else:
                st.info("Još nema administrativnih mutation događaja za ovaj scope.")
