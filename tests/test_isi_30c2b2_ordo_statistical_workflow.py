from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from streamlit.testing.v1 import AppTest

from src.domains.ordo import statistical_authoring as author, analytics_service as service
from src.domains.ordo.analytics_models import OrdoStatisticalModelContract
from src.platform.access.models import Role, RoleAssignment
from src.streamlit_app import ordo_statistical_api as api, ordo_statistical_workspace as ui
from test_isi_24b_statistical_contract import _contract
from test_isi_29b_spatial_api import api as fixture, params
from tests.test_isi_30c2b1_ordo_spatial_workflow import IDS, METHOD, RUN, seed

server = fixture
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1])


def definition(**changes):
    value = {
        k: v
        for k, v in _contract().items()
        if k
        not in {
            "target_methodology_id",
            "target_methodology_version",
            "target_methodology_fingerprint",
            "non_causal",
            "automatic_policy_recommendation",
        }
    }
    value["target_indicator_code"] = "synthetic"
    value.update(changes)
    return value


def payload(c, method, **changes):
    return author.StatisticalCreate.model_validate(
        dict(
            params(c, "ORDO"),
            analytics_run_id=IDS[3],
            reviewed_methodology_id=method.id,
            definition=definition(**changes),
        )
    ).model_dump(mode="json")


def input_value():
    return SimpleNamespace(
        artifact_type="snapshot", artifact_id=UUID(IDS[3]), artifact_fingerprint="a" * 64, records=()
    )


def transition(client, c, row, action, **fields):
    return client.post(
        "/api/v1/ordo/analytics/statistical-model-contracts/" + row["id"] + "/" + action,
        json=dict(
            params(c, "ORDO"), reviewed_status=row["status"], reviewed_fingerprint=row["contract_fingerprint"], **fields
        ),
    )


def test_native_metadata_lifecycle_supersession_and_no_fitting(server, monkeypatch):
    client, c, factory = server
    method = seed(factory, c)
    monkeypatch.setattr(service, "revalidate_analytics_run", lambda *a, **kw: input_value())
    created = []
    for _ in range(2):
        response = client.post("/api/v1/ordo/analytics/statistical-model-contracts", json=payload(c, method))
        assert response.status_code == 201, response.text
        row = response.json()
        assert row["fitting"] == "NOT_IMPLEMENTED" and row["numerical_results"] == "NOT_PRESENT"
        assert row["definition"]["target_methodology_id"] == str(method.id)
        assert row["definition"]["non_causal"] and not row["definition"]["automatic_policy_recommendation"]
        response = transition(client, c, row, "propose")
        assert response.status_code == 200, response.text
        row = response.json()
        response = transition(
            client,
            c,
            row,
            "validate",
            validation_note="Synthetic review",
            validation_evidence_reference="Synthetic evidence",
        )
        assert response.status_code == 200, response.text
        row = response.json()
        created.append(row)
    assert created[1]["version_no"] == 2 and created[1]["approved_by_membership_id"] == str(c["member"].id)
    with factory() as db:
        assert db.get(OrdoStatisticalModelContract, UUID(created[0]["id"])).status == "retired"
    response = transition(client, c, created[1], "retire", retirement_note="Synthetic retirement")
    assert response.status_code == 200
    listing = client.get("/api/v1/ordo/analytics/statistical-model-contracts", params=params(c, "ORDO")).json()
    assert len(listing["items"]) == 2 and all(x["status"] == "retired" for x in listing["items"])
    assert (
        client.get(
            "/api/v1/ordo/analytics/statistical-model-contracts/" + created[1]["id"], params=params(c, "ORDO")
        ).status_code
        == 200
    )


def test_stale_status_hash_binding_and_review_evidence_fail_closed(server, monkeypatch):
    client, c, factory = server
    method = seed(factory, c)
    monkeypatch.setattr(service, "revalidate_analytics_run", lambda *a, **kw: input_value())
    row = client.post("/api/v1/ordo/analytics/statistical-model-contracts", json=payload(c, method)).json()
    bad = {**row, "contract_fingerprint": "f" * 64}
    assert transition(client, c, bad, "propose").status_code == 400
    proposed = transition(client, c, row, "propose").json()
    assert transition(client, c, row, "propose").status_code == 400
    assert transition(client, c, proposed, "validate").status_code == 400
    monkeypatch.setattr(
        service,
        "revalidate_analytics_run",
        lambda *a, **kw: SimpleNamespace(**{**vars(input_value()), "artifact_fingerprint": "f" * 64}),
    )
    assert (
        transition(
            client, c, proposed, "validate", validation_note="Review", validation_evidence_reference="Evidence"
        ).status_code
        == 400
    )
    with factory() as db:
        assert db.get(OrdoStatisticalModelContract, UUID(row["id"])).status == "proposed"


def test_cross_scope_read_write_and_viewer_mutation_denied(server, monkeypatch):
    client, c, factory = server
    method = seed(factory, c)
    monkeypatch.setattr(service, "revalidate_analytics_run", lambda *a, **kw: input_value())
    b = payload(c, method)
    url = "/api/v1/ordo/analytics/statistical-model-contracts"
    row = client.post(url, json=b).json()
    assert client.post(url, json=b | {"workspace_id": str(c["simpa"].id)}).status_code == 403
    assert client.post(url, json=b | {"reviewed_methodology_id": str(uuid4())}).status_code == 400
    assert (
        client.get(url + "/" + row["id"], params=params(c, "ORDO") | {"organization_id": str(uuid4())}).status_code
        == 403
    )
    with factory() as db:
        other = deepcopy(b)
        other["workspace_id"] = str(uuid4())
        assert author.get(
            db, organization_id=c["org"].id, workspace_id=c["ordo"].id, record_id=UUID(row["id"])
        ).id == UUID(row["id"])
        with pytest.raises(service.OrdoAnalyticsError):
            author.get(db, organization_id=c["org"].id, workspace_id=uuid4(), record_id=UUID(row["id"]))
        grant = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        grant.role_id = db.scalar(select(Role.id).where(Role.code == "viewer"))
        db.commit()
    assert client.get(url, params=params(c, "ORDO")).status_code == 200
    assert client.post(url, json=b).status_code == 403
    assert transition(client, c, row, "propose").status_code == 403


@pytest.mark.parametrize(
    "change",
    [
        {"model_family": "linear_regression"},
        {"response_family": "gaussian"},
        {"analysis_as_of": "2023-01-01"},
        {"features": []},
        {"features": _contract()["features"] * 2},
    ],
)
def test_strict_semantics_and_no_http_on_invalid_customer_definition(monkeypatch, change):
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    with pytest.raises(ValidationError):
        api.create(
            "synthetic",
            scope=SCOPE,
            analytics_run_id=IDS[3],
            reviewed_methodology_id=IDS[2],
            definition=definition(**change),
        )
    req.assert_not_called()


@pytest.mark.parametrize(
    "field",
    [
        "target_methodology_id",
        "target_methodology_version",
        "target_methodology_fingerprint",
        "non_causal",
        "automatic_policy_recommendation",
    ],
)
def test_no_customer_server_authority(field):
    with pytest.raises(ValidationError):
        author.StatisticalDefinition.model_validate(definition(**{field: True}))


def test_transport_scope_and_review_preconditions(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {"id": IDS[5]}))
    monkeypatch.setattr(api, "request", req)
    api.transition(
        "synthetic",
        scope=SCOPE,
        row=dict(id="id/+", status="draft", contract_fingerprint="a" * 64),
        action="propose",
        fields={"organization_id": IDS[6], "reviewed_status": "validated", "reviewed_fingerprint": "b" * 64},
    )
    body = req.call_args.kwargs["json"]
    assert (
        body["organization_id"] == IDS[0]
        and body["reviewed_status"] == "draft"
        and body["reviewed_fingerprint"] == "a" * 64
    )
    assert req.call_args.args[1].endswith("id%2F%2B/propose")


def record():
    return dict(
        id=IDS[5],
        analysis_key="synthetic",
        status="draft",
        version_no=1,
        contract_fingerprint="a" * 64,
        definition=author.StatisticalDefinition.model_validate(definition()).model_dump(mode="json"),
    )


def app():
    import streamlit as st
    from tests.test_isi_30c2b2_ordo_statistical_workflow import IDS
    from src.streamlit_app.ordo_statistical_workspace import render_ordo_statistical

    shell = dict(
        organization={"id": st.session_state["org"]},
        workspace={"id": IDS[1]},
        product=dict(code=st.session_state["product"], permission_codes=st.session_state["permissions"]),
    )
    render_ordo_statistical(token="synthetic", shell=shell)


def mounted(monkeypatch):
    monkeypatch.setattr(ui.read_api, "methodologies", lambda *a, **kw: [METHOD.copy()])
    monkeypatch.setattr(ui.read_api, "runs", lambda *a, **kw: [RUN.copy()])
    monkeypatch.setattr(ui.api, "list_contracts", lambda *a, **kw: dict(items=[record()], truncated=False, offset=0))
    at = AppTest.from_function(app)
    at.session_state["org"] = IDS[0]
    at.session_state["product"] = "ORDO"
    at.session_state["permissions"] = ["analysis.read", "indicator.manage"]
    at.run()
    return at


def bylabel(items, label):
    return next(x for x in items if x.label == label)


def test_ui_explicit_authoring_dates_and_incomplete_no_http(monkeypatch):
    at = mounted(monkeypatch)
    at.button[0].click().run()
    for label in [
        "VALIDATED metodologija ORDO statističkog cilja",
        "Governed run ORDO statističke specifikacije",
        "ORDO statistička semantika",
        "ORDO struktura analize",
    ]:
        bylabel(at.selectbox, label).select_index(0).run()
    assert not at.exception and all(x.value is None for x in at.date_input)
    assert bylabel(at.selectbox, "Predložena ORDO modelska porodica").value is None
    req = Mock()
    monkeypatch.setattr(api, "request", req)
    bylabel(at.checkbox, "Potvrđujem autorizovani ORDO statistički DRAFT i pregledanu metodologiju/ulaz").check().run()
    bylabel(at.button, "Registruj ORDO statistički DRAFT").click().run()
    assert at.error and not at.exception
    req.assert_not_called()


def test_ui_review_confirmation_success_reset_and_page_scope_change(monkeypatch):
    at = mounted(monkeypatch)
    write = Mock(return_value={"id": IDS[5]})
    monkeypatch.setattr(api, "transition", write)
    at.button[0].click().run()
    bylabel(at.selectbox, "ORDO statistička specifikacija za pregled").select_index(0).run()
    assert at.warning and not at.json and not at.exception
    bylabel(at.button, "Predloži ORDO statistički PROPOSED").click().run()
    write.assert_not_called()
    at.checkbox[0].check().run()
    bylabel(at.button, "Predloži ORDO statistički PROPOSED").click().run()
    assert write.call_count == 1 and not at.checkbox and at.success
    at.button[0].click().run()
    at.number_input[0].set_value(2).run()
    assert not at.selectbox
    at.session_state["org"] = IDS[6]
    at.run()
    assert not at.selectbox


@pytest.mark.parametrize("permissions", [["analysis.read"], []])
def test_readonly_no_authoring_or_mutation(monkeypatch, permissions):
    at = mounted(monkeypatch)
    at.session_state["permissions"] = permissions
    at.run()
    if permissions:
        at.button[0].click().run()
        assert not any(x.label == "VALIDATED metodologija ORDO statističkog cilja" for x in at.selectbox)
        bylabel(at.selectbox, "ORDO statistička specifikacija za pregled").select_index(0).run()
    assert (
        not at.checkbox and not any("DRAFT" in x.label or "PROPOSED" in x.label for x in at.button) and not at.exception
    )


def test_other_product_hides_workspace(monkeypatch):
    at = mounted(monkeypatch)
    at.session_state["product"] = "SIMPA"
    at.run()
    assert not at.button and not at.exception


def test_help_ten_item_and_truthful_limits():
    from pathlib import Path

    guide = Path("docs/help/ORDO-STATISTICAL-SPECIFICATION-GUIDE.md").read_text()
    for index in range(1, 11):
        assert f"## {index}. " in guide
    for term in [
        "NOT_IMPLEMENTED",
        "NOT_PRESENT",
        "analysis.read",
        "indicator.manage",
        "PROPOSED",
        "VALIDATED",
        "RETIRED",
        "30E",
    ]:
        assert term in guide


def test_author_requires_actor_before_database_access():
    body = author.StatisticalCreate.model_validate(
        dict(SCOPE, analytics_run_id=IDS[3], reviewed_methodology_id=IDS[2], definition=definition())
    )
    with pytest.raises(service.OrdoAnalyticsError, match="contract_actor_required"):
        author.create(None, body=body, actor_id=None)


def test_method_retirement_and_native_other_workspace_lookup_fail_closed(server, monkeypatch):
    from src.platform.workspaces.models import Workspace
    from src.domains.ordo.analytics_models import OrdoIndicatorMethodology

    client, c, factory = server
    method = seed(factory, c)
    monkeypatch.setattr(service, "revalidate_analytics_run", lambda *a, **kw: input_value())
    url = "/api/v1/ordo/analytics/statistical-model-contracts"
    row = client.post(url, json=payload(c, method)).json()
    with factory() as db:
        other = Workspace(
            organization_id=c["org"].id, product_code="ORDO", slug="other-stat", name="Synthetic other", status="active"
        )
        db.add(other)
        db.flush()
        other_id = str(other.id)
        db.get(OrdoIndicatorMethodology, method.id).status = "retired"
        db.commit()
    p = params(c, "ORDO") | {"workspace_id": other_id}
    assert client.get(url + "/" + row["id"], params=p).status_code == 404
    assert client.get(url, params=p).json()["items"] == []
    assert (
        client.post(
            url + "/" + row["id"] + "/propose",
            json=dict(p, reviewed_status="draft", reviewed_fingerprint=row["contract_fingerprint"]),
        ).status_code
        == 404
    )
    assert transition(client, c, row, "propose").status_code == 400
    with factory() as db:
        assert db.get(OrdoStatisticalModelContract, UUID(row["id"])).status == "draft"


def test_pagination_bounds_and_offset_are_explicit(server, monkeypatch):
    client, c, factory = server
    method = seed(factory, c)
    monkeypatch.setattr(service, "revalidate_analytics_run", lambda *a, **kw: input_value())
    url = "/api/v1/ordo/analytics/statistical-model-contracts"
    for _ in range(2):
        assert client.post(url, json=payload(c, method)).status_code == 201
    response = client.get(url, params=params(c, "ORDO") | {"offset": 1}).json()
    assert len(response["items"]) == 1 and response["offset"] == 1 and not response["truncated"]
    assert client.get(url, params=params(c, "ORDO") | {"offset": -1}).status_code == 422
