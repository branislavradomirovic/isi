from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import administration_api as api, administration_workspace as ui
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired

IDS = [str(UUID(int=i)) for i in range(1, 8)]
COMMON = dict(organization_id=IDS[0], product_code="SIMPA")
SESSION = dict(
    session_id=IDS[4],
    created_at="2026-10-11T00:00:00Z",
    last_seen_at=None,
    expires_at="2026-10-12T00:00:00Z",
    is_current=False,
    is_revoked=False,
    revoked_at=None,
    revocation_reason=None,
    device_label="Mac computer",
)


def snapshot(manage=True):
    return dict(
        organization=dict(id=IDS[0], name="Sintetička organizacija", slug="synthetic", status="active"),
        entitlement=dict(is_active=True),
        capabilities=dict(
            members_read=True,
            members_manage=manage,
            workspace_manage=manage,
            org_wide_members_manage=manage,
            org_wide_manage=manage,
            audit_read=True,
        ),
        members=[
            dict(
                membership_id=IDS[1],
                display_name="Sintetički član",
                email="qa@example.invalid",
                membership_status="active",
                product_access_active=True,
                roles=[dict(role_code="analyst", scope="SIMPA", assignment_id=IDS[2])],
            )
        ],
        role_catalog=[dict(code="analyst"), dict(code="organization_admin")],
        workspaces=[dict(id=IDS[3], name="Sintetički prostor", status="active")],
        invitations=[
            dict(
                id=IDS[5],
                email="invite@example.invalid",
                status="pending",
                product_code="SIMPA",
                roles=["analyst"],
                expires_at="2026-10-12",
            )
        ],
        audit=[],
    )


def app():
    import streamlit as st
    from src.streamlit_app.administration_workspace import render_administration

    render_administration(
        token="synthetic",
        shell=dict(
            organization=dict(id=st.session_state["org"], name="Sintetička organizacija"),
            product=dict(code=st.session_state["product"]),
        ),
    )


def mounted(monkeypatch, data=None):
    data = snapshot() if data is None else data
    monkeypatch.setattr(ui.api, "snapshot", lambda *a, **kw: deepcopy(data))
    monkeypatch.setattr(ui, "render_topic_summary", lambda *a: None)
    at = AppTest.from_function(app)
    at.session_state["org"] = IDS[0]
    at.session_state["product"] = "SIMPA"
    at.run()
    return at, data


def label(items, name):
    return next(x for x in items if x.label == name)


def confirm(at, name):
    label(at.checkbox, "Potvrđujem pregledanu promenu: " + name).check().run()


@pytest.mark.parametrize(
    "status,kind", [(401, AuthenticationRequired), (403, AccessDenied), (422, AccessDenied), (500, ApiUnavailable)]
)
def test_errors_never_reflect_private_response(status, kind):
    private = "SYNTHETIC_PRIVATE_BODY"
    with pytest.raises(kind) as caught:
        api._checked(
            SimpleNamespace(status_code=status, json=lambda: dict(detail=[dict(input=private)])),
            unavailable="Nedostupno",
        )
    assert private not in str(caught.value)


def test_known_assurance_failure_and_204_success():
    assert api._checked(SimpleNamespace(status_code=204), unavailable="x") == dict(completed=True)
    with pytest.raises(AccessDenied, match="dodatna autentifikacija"):
        api._checked(
            SimpleNamespace(status_code=403, json=lambda: dict(detail="step_up_authentication_required")),
            unavailable="x",
        )


@pytest.mark.parametrize(
    "values", [dict(email="bad", role_code="analyst"), dict(email="qa@example.invalid", role_code="")]
)
def test_invalid_invitation_not_sent(monkeypatch, values):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(AccessDenied):
        api.invite("synthetic", **COMMON, **values)
    req.assert_not_called()


def test_invitation_receipt_strips_development_credentials(monkeypatch):
    req = Mock(
        return_value=SimpleNamespace(
            status_code=201,
            json=lambda: dict(
                id=IDS[5],
                status="pending",
                delivery_status="development_token",
                development_token="SYNTHETIC_UNSAFE_FIELD",
            ),
        )
    )
    monkeypatch.setattr(api, "request", req)
    value = api.invite("synthetic", **COMMON, email="qa@example.com", role_code="analyst")
    assert "development_token" not in value and "SYNTHETIC_UNSAFE_FIELD" not in repr(value)
    assert req.call_args.kwargs["json"]["organization_id"] == IDS[0]


@pytest.mark.parametrize("change", [dict(organization_id="../"), dict(product_code="OTHER")])
def test_bad_scope_not_sent(monkeypatch, change):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(AccessDenied):
        api.snapshot("synthetic", **(COMMON | change))
    req.assert_not_called()


def test_bad_path_not_sent(monkeypatch):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(AccessDenied):
        api.remove_role("synthetic", **COMMON, membership_id="id/..", assignment_id=IDS[2])
    req.assert_not_called()


def test_session_metadata_allowlist_and_scoped_revoke(monkeypatch):
    req = Mock(
        return_value=SimpleNamespace(status_code=200, json=lambda: [SESSION | dict(unsafe="SYNTHETIC_PRIVATE_FIELD")])
    )
    monkeypatch.setattr(api, "request", req)
    rows = api.member_sessions("synthetic", **COMMON, membership_id=IDS[1])
    assert set(rows[0]) == set(SESSION) and "unsafe" not in rows[0]
    req.return_value = SimpleNamespace(status_code=204)
    assert api.revoke_member_session("synthetic", **COMMON, membership_id=IDS[1], session_id=IDS[4])["completed"]
    assert req.call_args.args[1].endswith(IDS[1] + "/sessions/" + IDS[4])
    assert req.call_args.kwargs["params"] == COMMON


def test_invalid_session_response_bounded(monkeypatch):
    monkeypatch.setattr(
        api, "request", Mock(return_value=SimpleNamespace(status_code=200, json=lambda: [dict(unsafe="PRIVATE")]))
    )
    with pytest.raises(ApiUnavailable, match="nije važeći"):
        api.member_sessions("synthetic", **COMMON, membership_id=IDS[1])


def test_ui_explicit_target_and_confirmation_reset_on_values_scope_snapshot(monkeypatch):
    at, data = mounted(monkeypatch)
    assert not at.exception and not at.json
    assert label(at.selectbox, "Član za upravljanje").value is None
    label(at.selectbox, "Član za upravljanje").select_index(0).run()
    label(at.selectbox, "Željeni pristup proizvodu").select("Neaktivan").run()
    confirm(at, "Sačuvaj pristup proizvodu")
    assert not label(at.button, "Sačuvaj pristup proizvodu").disabled
    label(at.selectbox, "Željeni pristup proizvodu").select("Aktivan").run()
    assert not label(at.checkbox, "Potvrđujem pregledanu promenu: Sačuvaj pristup proizvodu").value
    label(at.selectbox, "Željeni pristup proizvodu").select("Neaktivan").run()
    assert not label(at.checkbox, "Potvrđujem pregledanu promenu: Sačuvaj pristup proizvodu").value
    data["members"][0]["display_name"] = "Promenjeni član"
    at.run()
    assert label(at.selectbox, "Član za upravljanje").value is None
    at.session_state["org"] = IDS[6]
    at.run()
    assert label(at.selectbox, "Član za upravljanje").value is None
    at.session_state["product"] = "ORDO"
    at.run()
    assert label(at.selectbox, "Član za upravljanje").value is None


def test_remove_failure_preserves_error_success_resets_and_receipt(monkeypatch):
    at, _ = mounted(monkeypatch)
    label(at.selectbox, "Član za upravljanje").select_index(0).run()
    fn = Mock(side_effect=AccessDenied("Odbijeno"))
    monkeypatch.setattr(api, "remove_role", fn)
    name = "Ukloni rolu analyst [SIMPA]"
    confirm(at, name)
    label(at.button, name).click().run()
    assert at.error and not at.success and not at.exception
    fn.side_effect = None
    fn.return_value = dict(completed=True)
    label(at.button, name).click().run()
    assert at.success and label(at.selectbox, "Član za upravljanje").value is None
    assert fn.call_args.kwargs == dict(**COMMON, membership_id=IDS[1], assignment_id=IDS[2])


def test_workspace_explicit_slug_and_success_reset(monkeypatch):
    at, _ = mounted(monkeypatch)
    fn = Mock(return_value=dict(id=IDS[3]))
    monkeypatch.setattr(api, "create_workspace", fn)
    assert label(at.text_input, "Slug novog radnog prostora").value == ""
    label(at.text_input, "Naziv novog radnog prostora").input("Novi prostor").run()
    assert label(at.button, "Kreiraj radni prostor").disabled
    label(at.text_input, "Slug novog radnog prostora").input("new-space").run()
    confirm(at, "Kreiraj radni prostor")
    label(at.button, "Kreiraj radni prostor").click().run()
    assert at.success and label(at.text_input, "Naziv novog radnog prostora").value == ""
    assert fn.call_args.kwargs == dict(**COMMON, name="Novi prostor", slug="new-space")


def test_readonly_has_no_mutation_controls(monkeypatch):
    at, _ = mounted(monkeypatch, snapshot(False))
    assert not at.button and not at.checkbox and not at.text_input and not at.exception


def test_sessions_explicit_load_refresh_resets_confirmation(monkeypatch):
    at, _ = mounted(monkeypatch)
    read = Mock(return_value=[SESSION.copy()])
    write = Mock(return_value=dict(completed=True))
    monkeypatch.setattr(api, "member_sessions", read)
    monkeypatch.setattr(api, "revoke_member_session", write)
    label(at.selectbox, "Član za upravljanje").select_index(0).run()
    read.assert_not_called()
    label(at.button, "Učitaj / osveži sesije izabranog člana").click().run()
    label(at.selectbox, "Sesija za opoziv").select_index(0).run()
    confirm(at, "Opozovi pregledanu sesiju člana")
    label(at.button, "Učitaj / osveži sesije izabranog člana").click().run()
    assert label(at.selectbox, "Sesija za opoziv").value is None
    label(at.selectbox, "Sesija za opoziv").select_index(0).run()
    assert label(at.button, "Opozovi pregledanu sesiju člana").disabled
    confirm(at, "Opozovi pregledanu sesiju člana")
    label(at.button, "Opozovi pregledanu sesiju člana").click().run()
    assert at.success and not at.exception
    assert write.call_args.kwargs == dict(**COMMON, membership_id=IDS[1], session_id=IDS[4])
