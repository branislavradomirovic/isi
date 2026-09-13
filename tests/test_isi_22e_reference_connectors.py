from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from src.platform.data.models import DataGovernedIngestionOutput, DataIngestionEvaluation
from src.workers import data_jobs

from test_isi_22e_ingestion_operations import build_case, create_run


FIXTURE = Path("tests/fixtures/isi_22e/reference_cases.json")


def _fixture():
    return json.loads(FIXTURE.read_text())


def _worker(case, monkeypatch, run):
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(data_jobs, "get_settings", lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024))
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)


def test_both_product_classes_use_same_shared_operational_contract_shape():
    fixture = _fixture()
    assert fixture["contract_version"] == 1
    assert [item["product_code"] for item in fixture["products"]] == ["SIMPA", "ORDO"]
    expected = {"good", "stale", "quality_warning", "quality_rejected", "backfill", "replay", "dead_letter"}
    shapes = []
    for product in fixture["products"]:
        assert {case["scenario"] for case in product["cases"]} == expected
        shapes.append([sorted(case) for case in product["cases"]])
    assert shapes[0] == shapes[1]
    assert fixture["shared_operational_contract"]["backfill_contract"]["cursor_mutation_allowed"] is False


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_accepted_reference_cases_produce_product_correct_governed_output(tmp_path, monkeypatch, product):
    case = build_case(tmp_path, product=product)
    run = create_run(case, observed=datetime.now(timezone.utc))
    _worker(case, monkeypatch, run)
    output = case["db"].scalar(select(DataGovernedIngestionOutput).where(
        DataGovernedIngestionOutput.ingestion_run_id == run.id))
    assert output is not None
    assert (output.product_code, output.organization_id, output.workspace_id, output.source_id) == (
        product, case["organization"].id, case["workspace"].id, case["source"].id)


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_rejected_and_dead_letter_reference_cases_never_produce_output(tmp_path, monkeypatch, product):
    case = build_case(tmp_path, product=product,
        freshness_contract={"missing_evidence_action": "REJECT"},
        dead_letter_contract={"rejected_evaluation_to_dead_letter": True})
    run = create_run(case)
    _worker(case, monkeypatch, run)
    evaluation = case["db"].scalar(select(DataIngestionEvaluation).where(
        DataIngestionEvaluation.ingestion_run_id == run.id))
    assert evaluation.decision == "DEAD_LETTERED"
    assert case["db"].scalar(select(func.count(DataGovernedIngestionOutput.id))) == 0


def test_fixture_is_synthetic_and_contains_no_domain_methodology():
    text = FIXTURE.read_text().casefold()
    assert "synthetic" in text
    for forbidden in ("formula", "prediction", "risk_score", "recommendation", "forecast", "indicator_weight"):
        assert forbidden not in text
