from datetime import date
from types import SimpleNamespace
from uuid import uuid4
import pytest
from test_isi_29d_attribution_service import attribution_case as target_attribution_fixture, lifecycle_case, args  # noqa: F401
from test_isi_24c_not_estimated_semantics import _spec
from src.domains.simpa import report_evidence as simpa, attribution_service
from src.domains.ordo import analytics_service as ordo_analytics, report_evidence as ordo


attribution_case = target_attribution_fixture

def test_simpa_stored_result_and_attribution_parity(attribution_case):
    c = attribution_case
    first = simpa.result_evidence(c["db"], **args(c))
    assert first["result"] == c["result"].result_detail and first["xai"]["status"] == "NOT_CREATED"
    artifact = attribution_service.create(c["db"], **args(c), actor_id=c["member"].id)
    second = simpa.result_evidence(c["db"], **args(c))
    assert second["xai"] == artifact and second["fingerprint"] == c["result"].result_fingerprint
    c["method"].status = "retired"
    with pytest.raises(ValueError):
        simpa.result_evidence(c["db"], **args(c))


@pytest.fixture
def forecast(monkeypatch):
    spec = _spec()
    row = SimpleNamespace(id=uuid4(), organization_id=uuid4(), workspace_id=uuid4(), analytics_run_id=uuid4(),
                          version_no=1, contract_fingerprint="c" * 64, target_indicator_id=uuid4(),
                          target_methodology_id=spec.target_methodology_id, target_methodology_version=1,
                          methodology_fingerprint=spec.target_methodology_fingerprint, input_snapshot_sha256="d" * 64)
    stored = []
    db = SimpleNamespace(add=lambda value: stored.append(value), flush=lambda: None)
    result = ordo_analytics._persist_forecast_outcome(db, row=row, spec=spec, series_identity={"destination": "A"},
                                                     requested_family="naive", interval_level=0.90, actor_id=uuid4(),
                                                     result_status="NOT_ESTIMATED", reason_code="INSUFFICIENT_HISTORY",
                                                     dates=[date(2024, 1, 1)])
    result.id = uuid4()
    monkeypatch.setattr(ordo_analytics, "get_forecast_run", lambda *a, **kw: result)
    monkeypatch.setattr(ordo_analytics, "_forecast_binding", lambda *a, **kw: (row, spec, SimpleNamespace(id=row.analytics_run_id), object()))
    return db, row, result


def test_ordo_not_estimated_is_not_numeric_or_shap(forecast):
    db, row, result = forecast
    value = ordo.result_evidence(db, result_id=result.id, organization_id=row.organization_id, workspace_id=row.workspace_id)
    assert not value["result"]["forecast_points"] and value["shap"].startswith("UNAVAILABLE")
    assert value["causal"] is False and value["result"]["result_status"] == "NOT_ESTIMATED"


@pytest.mark.parametrize("kind", ["result", "binding", "request", "causal", "window", "horizon"])
def test_ordo_forecast_integrity_fail_closed(forecast, kind):
    db, row, result = forecast
    if kind == "result":
        result.forecast_points = [{"point": 12}]
    elif kind == "binding":
        result.input_snapshot_sha256 = "e" * 64
    elif kind == "request":
        result.series_identity = {"destination": "B"}
    elif kind == "causal":
        result.non_causal = False
    elif kind == "window":
        result.observation_window = {}
    else:
        result.horizon = 999
    with pytest.raises(ValueError):
        ordo.result_evidence(db, result_id=result.id, organization_id=row.organization_id, workspace_id=row.workspace_id)
