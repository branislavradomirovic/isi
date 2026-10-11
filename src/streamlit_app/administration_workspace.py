from __future__ import annotations

import hashlib
import json

import streamlit as st

from src.streamlit_app import administration_api as api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired
from src.streamlit_app.shared_help_workspace import render_topic_summary


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except (AccessDenied, ApiUnavailable) as exc:
        st.error(str(exc))
    return None


def _fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _action(*, scope: str, action: str, label: str, reviewed, values: dict, fn, token: str, enabled=True):
    generation = st.session_state.get(scope + ":generation", 0)
    binding = _fingerprint([generation, reviewed, values])
    state_key = scope + ":" + action + ":binding"
    previous, revision = st.session_state.get(state_key, (None, 0))
    if previous != binding:
        revision += 1
        st.session_state[state_key] = (binding, revision)
    key = scope + ":" + action + ":" + str(revision) + ":" + binding
    confirmed = st.checkbox("Potvrđujem pregledanu promenu: " + label, key=key + ":confirm", disabled=not enabled)
    if st.button(label, key=key + ":submit", disabled=not (enabled and confirmed)):
        result = _safe(fn, token, **values)
        if result is not None:
            message = "Sačuvano: " + label + ". Pregled je osvežen; prethodne potvrde su poništene."
            if action == "invite":
                message += " Poziv nije isto što i aktivan nalog. "
                message += (
                    "Isporuka: SMTP."
                    if result.get("delivery_status") == "smtp"
                    else "Razvojni poziv; spoljna email isporuka nije potvrđena."
                )
            st.session_state[scope + ":receipt"] = message
            st.session_state[scope + ":generation"] = generation + 1
            st.rerun()


def render_administration(*, token: str, shell: dict) -> None:
    render_topic_summary("ISI-H09")
    product_code = shell["product"]["code"]
    organization_id = str(shell["organization"]["id"])
    scope = f"admin:{organization_id}:{product_code}"
    if st.session_state.get("admin:active_scope") != scope:
        st.session_state["admin:active_scope"] = scope
        st.session_state[scope + ":generation"] = st.session_state.get(scope + ":generation", 0) + 1
    common = dict(organization_id=organization_id, product_code=product_code)
    st.subheader("Administracija")
    st.caption(f"{shell['organization']['name']} · {product_code} · organizacioni pristup, članovi i radni prostori")
    st.markdown("Detaljna uputstva: **ISI-ADMINISTRATION-WORKFLOWS-GUIDE** u Help dokumentaciji.")
    receipt = st.session_state.get(scope + ":receipt")
    if receipt:
        st.success(receipt)
    data = _safe(api.snapshot, token, **common)
    if not data:
        return
    caps = data.get("capabilities", {})
    reviewed = _fingerprint(data)
    if st.session_state.get(scope + ":reviewed") != reviewed:
        st.session_state[scope + ":reviewed"] = reviewed
        st.session_state[scope + ":generation"] = st.session_state.get(scope + ":generation", 0) + 1
    controls = scope + ":fields:" + reviewed + ":" + str(st.session_state.get(scope + ":generation", 0))
    entitlement = data.get("entitlement")
    st.info(
        f"Pravo organizacije na {product_code}: {'aktivno' if entitlement and entitlement.get('is_active') else 'neaktivno'}. Entitlement je read-only. Ovo pravo se ovde ne menja."
    )
    st.markdown("### Pregled administrativnih granica")
    st.caption(
        "Role određuju ovlašćenja; pristup proizvodu i pravo organizacije su zasebni uslovi. Administrator organizacije nije platformski superadministrator. Server ponovo proverava sve granice."
    )
    tabs = st.tabs(["Članovi", "Pozivi", "Workspace-i", "Organizacija", "Audit"])

    def action(name, label, values, fn, enabled=True, target=reviewed):
        _action(
            scope=scope,
            action=name,
            label=label,
            reviewed=target,
            values=dict(**common, **values),
            fn=fn,
            token=token,
            enabled=enabled,
        )

    with tabs[0]:
        if not (caps.get("members_read") or caps.get("members_manage")):
            st.info("Nemate ovlašćenje za pregled članova.")
        else:
            members = data.get("members", [])
            if members:
                st.dataframe(
                    [
                        {
                            "Ime": row["display_name"],
                            "Email": row["email"],
                            "Članstvo": row["membership_status"],
                            "Pristup proizvodu": row["product_access_active"],
                            "Role": ", ".join(f"{r['role_code']} [{r['scope']}]" for r in row.get("roles", [])),
                        }
                        for row in members
                    ],
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("Nema članova u ovom kontekstu.")
            if caps.get("members_manage") and members:
                member_map = {row["membership_id"]: row for row in members}
                selected = st.selectbox(
                    "Član za upravljanje",
                    list(member_map),
                    index=None,
                    format_func=lambda v: member_map[v]["display_name"] + " · " + member_map[v]["email"],
                    key=controls + ":member",
                )
                if selected:
                    member = member_map[selected]
                    fields = controls + ":" + selected
                    st.write(f"Cilj: **{member['display_name']}** · {member['email']} · {product_code}")
                    if caps.get("org_wide_members_manage"):
                        st.warning("Promena statusa članstva važi za celu organizaciju, uključujući oba proizvoda.")
                        desired = st.selectbox(
                            "Status članstva", ["active", "suspended"], index=None, key=fields + ":status"
                        )
                        action(
                            "status",
                            "Sačuvaj status članstva",
                            dict(membership_id=selected, status=desired),
                            api.member_status,
                            desired is not None and desired != member["membership_status"],
                        )
                    desired_access = st.selectbox(
                        "Željeni pristup proizvodu", ["Aktivan", "Neaktivan"], index=None, key=fields + ":access"
                    )
                    active = desired_access == "Aktivan"
                    action(
                        "access",
                        "Sačuvaj pristup proizvodu",
                        dict(membership_id=selected, active=active),
                        api.product_access,
                        desired_access is not None and active != bool(member["product_access_active"]),
                    )
                    role = st.selectbox(
                        "Rola za dodelu",
                        [r["code"] for r in data.get("role_catalog", [])],
                        index=None,
                        key=fields + ":role",
                    )
                    role_scope = st.selectbox(
                        "Obuhvat role",
                        ["product"] + (["organization"] if caps.get("org_wide_members_manage") else []),
                        index=None,
                        key=fields + ":role_scope",
                    )
                    if role_scope == "organization":
                        st.warning("Ova rola važi za celu organizaciju; pristup svakom proizvodu ostaje zaseban uslov.")
                    action(
                        "assign",
                        "Dodeli pregledanu rolu",
                        dict(membership_id=selected, role_code=role, scope=role_scope),
                        api.assign_role,
                        role is not None and role_scope is not None,
                    )
                    for row in member.get("roles", []):
                        if row["scope"] != "*" or caps.get("org_wide_members_manage"):
                            action(
                                "remove:" + row["assignment_id"],
                                f"Ukloni rolu {row['role_code']} [{row['scope']}]",
                                dict(membership_id=selected, assignment_id=row["assignment_id"]),
                                api.remove_role,
                            )
                    if caps.get("org_wide_members_manage"):
                        st.markdown("#### Sesije člana")
                        st.caption(
                            "Globalne sesije prijave. Sopstvene sesije se upravljaju u ličnom nalogu; član više organizacija nije podržan ovde. Opoziv zahteva postojeći dodatni nivo autentifikacije."
                        )
                        inventory_key = fields + ":sessions_inventory"
                        if st.button("Učitaj / osveži sesije izabranog člana", key=fields + ":sessions"):
                            st.session_state.pop(inventory_key, None)
                            sessions = _safe(api.member_sessions, token, membership_id=selected, **common)
                            if sessions is not None:
                                st.session_state[inventory_key] = sessions
                                st.session_state[fields + ":sessions_generation"] = (
                                    st.session_state.get(fields + ":sessions_generation", 0) + 1
                                )
                        sessions = st.session_state.get(inventory_key)
                        if sessions is not None:
                            st.caption(
                                "Bezbedni metapodaci poslednjeg eksplicitnog učitavanja; server proverava cilj i ovlašćenja ponovo pri opozivu."
                            )
                            if sessions:
                                st.dataframe(sessions, width="stretch", hide_index=True)
                            else:
                                st.info("Nema sesija za izabranog člana.")
                            active_sessions = {s["session_id"]: s for s in sessions if not s["is_revoked"]}
                            if active_sessions:
                                loaded_key = (
                                    fields
                                    + ":sessions:"
                                    + str(st.session_state.get(fields + ":sessions_generation", 0))
                                )
                                session_id = st.selectbox(
                                    "Sesija za opoziv",
                                    list(active_sessions),
                                    index=None,
                                    key=loaded_key + ":target",
                                    format_func=lambda v: active_sessions[v]["device_label"] + " · " + v,
                                )
                                if session_id:
                                    target = active_sessions[session_id]
                                    st.write(
                                        f"Pregledani cilj: {target['session_id']} · {target['device_label']} · {target['expires_at']}"
                                    )
                                    action(
                                        "session:" + loaded_key,
                                        "Opozovi pregledanu sesiju člana",
                                        dict(membership_id=selected, session_id=session_id),
                                        api.revoke_member_session,
                                        target=[reviewed, target],
                                    )

    with tabs[1]:
        st.info(
            "SMTP je pending dok se ne podesi spoljni servis. Poziv i aktivan nalog nisu isti status; platforma ne zaobilazi sigurnosne uslove za isporuku."
        )
        if caps.get("members_manage"):
            email = st.text_input("Email za poziv", key=controls + ":invite_email")
            role = st.selectbox(
                "Početna product rola",
                [r["code"] for r in data.get("role_catalog", []) if r["code"] != "organization_admin"],
                index=None,
                key=controls + ":invite_role",
            )
            action(
                "invite",
                "Kreiraj pregledani poziv",
                dict(email=email, role_code=role),
                api.invite,
                bool(email.strip()) and role is not None,
            )
        invitations = data.get("invitations", [])
        if invitations:
            st.dataframe(
                [
                    {k: r.get(k) for k in ("email", "status", "product_code", "roles", "expires_at")}
                    for r in invitations
                ],
                width="stretch",
                hide_index=True,
            )
            if caps.get("members_manage"):
                for row in invitations:
                    if row["status"] == "pending":
                        action(
                            "revoke:" + row["id"],
                            "Opozovi poziv · " + row["email"],
                            dict(invitation_id=row["id"]),
                            api.revoke_invite,
                        )

    with tabs[2]:
        workspaces = data.get("workspaces", [])
        if workspaces:
            st.dataframe(workspaces, width="stretch", hide_index=True)
        if caps.get("workspace_manage"):
            name = st.text_input("Naziv novog radnog prostora", key=controls + ":workspace_name")
            slug = st.text_input(
                "Slug novog radnog prostora",
                key=controls + ":workspace_slug",
                help="Izričito unesite jedinstven identifikator. Ne izvodi se automatski iz naziva.",
            )
            action(
                "workspace:create",
                "Kreiraj radni prostor",
                dict(name=name, slug=slug),
                api.create_workspace,
                len(name.strip()) >= 2 and len(slug.strip()) >= 2,
            )
            for row in workspaces:
                status = "archived" if row["status"] == "active" else "active"
                label = ("Arhiviraj" if status == "archived" else "Reaktiviraj") + " radni prostor · " + row["name"]
                action(
                    "workspace:" + row["id"], label, dict(workspace_id=row["id"], status=status), api.workspace_status
                )

    with tabs[3]:
        org = data["organization"]
        st.write(f"Slug: {org['slug']} · status: {org['status']}")
        if caps.get("org_wide_manage"):
            st.warning(
                "Naziv se menja za celu organizaciju, uključujući SIMPA i ORDO. Slug i status ostaju neizmenjivi."
            )
            name = st.text_input("Naziv organizacije", value=org["name"], key=controls + ":org_name")
            action(
                "organization",
                "Sačuvaj naziv organizacije",
                dict(name=name),
                api.rename_organization,
                name.strip() != org["name"] and len(name.strip()) >= 2,
            )
        else:
            st.info("Promena naziva zahteva organization-wide organization.manage.")
    with tabs[4]:
        if caps.get("audit_read"):
            if data.get("audit"):
                st.dataframe(data["audit"], width="stretch", hide_index=True)
            else:
                st.info("Nema administrativnih promena u ovom kontekstu.")
        else:
            st.info("Nemate audit.read u ovom kontekstu.")
