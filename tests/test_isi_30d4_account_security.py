from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID
import pytest
from streamlit.testing.v1 import AppTest
from src.streamlit_app import security_api as api, security_workspace as ui
from src.streamlit_app.api_client import ApiUnavailable, AuthenticationRequired

IDS = [str(UUID(int=n)) for n in range(1, 5)]


def inventory():
    return [
        dict(
            session_id=IDS[i],
            created_at="2026-10-11T00:00:00Z",
            last_seen_at=None,
            expires_at="2026-10-12T00:00:00Z",
            is_current=i == 0,
            is_revoked=i == 2,
            revoked_at=None,
            revocation_reason=None,
            device_label="Sintetički uređaj " + str(i),
        )
        for i in range(3)
    ]


def app():
    import streamlit as st
    from src.streamlit_app.security_workspace import render_account_security

    render_account_security(token=st.session_state.get("synthetic-context", "synthetic"))


def mounted(monkeypatch):
    data = inventory()
    monkeypatch.setattr(ui, "render_topic_summary", lambda *a: None)
    monkeypatch.setattr(api, "list_sessions", lambda *a: deepcopy(data))
    at = AppTest.from_function(app).run()
    assert not at.exception
    return at, data


def item(elements, label):
    return next(x for x in elements if x.label == label)


@pytest.mark.parametrize(
    "status,kind", [(401, AuthenticationRequired), (403, ApiUnavailable), (422, ApiUnavailable), (500, ApiUnavailable)]
)
def test_private_errors_not_reflected(status, kind):
    with pytest.raises(kind) as caught:
        api._authenticated(SimpleNamespace(status_code=status, json=lambda: {"detail": "PRIVATE_SYNTHETIC_BODY"}))
    assert "PRIVATE_SYNTHETIC_BODY" not in str(caught.value)


def test_typed_inventory_strips_extra_private_fields(monkeypatch):
    values = inventory()
    values[0]["private_extra"] = "PRIVATE_SYNTHETIC_BODY"
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: values))
    monkeypatch.setattr(api, "request", req)
    result = api.list_sessions("synthetic")
    assert "private_extra" not in result[0] and len(result) == 3
    assert req.call_args.kwargs == {"token": "synthetic"}


@pytest.mark.parametrize("value", [{}, [{"session_id": "../private"}], None])
def test_invalid_inventory_bounded(monkeypatch, value):
    monkeypatch.setattr(api, "request", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: value))
    with pytest.raises(ApiUnavailable):
        api.list_sessions("synthetic")


def test_invalid_session_uuid_no_transport(monkeypatch):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(ValueError):
        api.revoke_session("synthetic", "../private")
    req.assert_not_called()


def test_204_receipt(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=204))
    monkeypatch.setattr(api, "request", req)
    assert api.revoke_session("synthetic", IDS[1]) == {"completed": True}
    assert req.call_args.args == ("DELETE", "/api/v1/auth/sessions/" + IDS[1])


@pytest.mark.parametrize("value", [{"revoked_count": -1}, {}, {"revoked_count": "private"}])
def test_invalid_bulk_receipt_bounded(monkeypatch, value):
    monkeypatch.setattr(api, "request", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: value))
    with pytest.raises(ApiUnavailable):
        api.revoke_other_sessions("synthetic")


def test_no_implicit_revocation_or_current_revoked_button(monkeypatch):
    calls = Mock()
    monkeypatch.setattr(api, "revoke_session", calls)
    monkeypatch.setattr(api, "revoke_other_sessions", calls)
    at, _ = mounted(monkeypatch)
    assert len([b for b in at.button if b.label == "Opozovi sesiju"]) == 1
    assert item(at.button, "Opozovi sesiju").disabled
    assert item(at.button, "Opozovi sve druge sesije").disabled
    calls.assert_not_called()


def test_individual_success_receipt_resets(monkeypatch):
    at, data = mounted(monkeypatch)

    def revoke(*args):
        data[1]["is_revoked"] = True
        return {"completed": True}

    req = Mock(side_effect=revoke)
    monkeypatch.setattr(api, "revoke_session", req)
    item(at.checkbox, "Potvrđujem opoziv ove druge sesije").check().run()
    item(at.button, "Opozovi sesiju").click().run()
    assert not at.exception and req.call_count == 1
    assert any("Izabrana druga sesija je opozvana" in s.value for s in at.success)
    assert not any(b.label == "Opozovi sesiju" for b in at.button)
    assert not item(at.checkbox, "Potvrđujem opoziv svih svojih drugih aktivnih sesija").value


@pytest.mark.parametrize("field,value", [("device_label", "Promenjeni uređaj"), ("expires_at", "2026-10-13T00:00:00Z")])
def test_changed_roundtrip_inventory_invalidates(monkeypatch, field, value):
    at, data = mounted(monkeypatch)
    old = data[1][field]
    item(at.checkbox, "Potvrđujem opoziv ove druge sesije").check().run()
    data[1][field] = value
    at.run()
    assert item(at.button, "Opozovi sesiju").disabled
    data[1][field] = old
    at.run()
    assert item(at.button, "Opozovi sesiju").disabled


def test_activity_does_not_invalidate_stable_identity(monkeypatch):
    at, data = mounted(monkeypatch)
    item(at.checkbox, "Potvrđujem opoziv ove druge sesije").check().run()
    data[0]["last_seen_at"] = "2026-10-11T00:05:00Z"
    at.run()
    assert not item(at.button, "Opozovi sesiju").disabled


def test_current_session_change_invalidates_and_roundtrip(monkeypatch):
    at, data = mounted(monkeypatch)
    item(at.checkbox, "Potvrđujem opoziv ove druge sesije").check().run()
    data[0]["session_id"] = IDS[3]
    at.run()
    assert item(at.button, "Opozovi sesiju").disabled
    data[0]["session_id"] = IDS[0]
    at.run()
    assert item(at.button, "Opozovi sesiju").disabled


def test_bulk_success_includes_zero_count_and_no_false_receipt(monkeypatch):
    at, _ = mounted(monkeypatch)
    req = Mock(return_value=0)
    monkeypatch.setattr(api, "revoke_other_sessions", req)
    item(at.checkbox, "Potvrđujem opoziv svih svojih drugih aktivnih sesija").check().run()
    item(at.button, "Opozovi sve druge sesije").click().run()
    assert req.call_count == 1 and any("Opozvano drugih sesija: 0" in s.value for s in at.success)
    assert item(at.button, "Opozovi sve druge sesije").disabled


def test_failure_no_success_and_no_private_echo(monkeypatch):
    at, _ = mounted(monkeypatch)
    req = Mock(side_effect=ApiUnavailable("PRIVATE_SYNTHETIC_BODY"))
    monkeypatch.setattr(api, "revoke_session", req)
    item(at.checkbox, "Potvrđujem opoziv ove druge sesije").check().run()
    item(at.button, "Opozovi sesiju").click().run()
    assert req.call_count == 1 and not at.success
    assert at.error and all("PRIVATE_SYNTHETIC_BODY" not in x.value for x in at.error)


def test_unavailable_read_is_not_empty(monkeypatch):
    at, _ = mounted(monkeypatch)
    monkeypatch.setattr(api, "list_sessions", Mock(side_effect=ApiUnavailable("PRIVATE_SYNTHETIC_BODY")))
    at.run()
    assert not at.exception and any("Pregled nije učitan" in s.value for s in at.info)
    assert not any(b.label.startswith("Opozovi") for b in at.button)


def test_device_label_plain_text(monkeypatch):
    at, data = mounted(monkeypatch)
    data[1]["device_label"] = "[Sintetički uređaj](https://example.invalid)"
    at.run()
    assert any(data[1]["device_label"] in s.value for s in at.text)
    assert not any(data[1]["device_label"] in s.value for s in at.markdown)


def test_ten_section_guide_and_no_credential_copy(monkeypatch):
    from pathlib import Path

    at, _ = mounted(monkeypatch)
    guide = Path("docs/help/ISI-ACCOUNT-SECURITY-WORKFLOWS-GUIDE.md").read_text()
    assert guide.count("\n## ") == 10
    assert "SMTP" in guide and "SIMPA i ORDO" in guide
    assert "security:active-token" not in at.session_state
