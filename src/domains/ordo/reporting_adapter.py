from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domains.ordo.analytics_models import (
    OrdoAISynthesis,
    OrdoAnalyticsRun,
    OrdoIndicatorResult,
    OrdoScenario,
    OrdoScenarioAssessment,
)
from src.domains.ordo.analytics_service import OrdoAnalyticsError, revalidate_analytics_run
from src.domains.ordo.models import OrdoIndicatorDefinition
from src.platform.ai.models import AIJob


class OrdoReportingError(ValueError):
    pass


def _sha(value) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source(*, kind: str, object_id, organization_id, workspace_id, checksum: str, label: str) -> dict:
    return {
        "kind": kind,
        "id": str(object_id),
        "organization_id": str(organization_id),
        "workspace_id": str(workspace_id),
        "product_code": "ORDO",
        "checksum": checksum,
        "label": label,
    }


def available_sources(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[dict]:
    runs = session.scalars(
        select(OrdoAnalyticsRun)
        .where(OrdoAnalyticsRun.organization_id == organization_id, OrdoAnalyticsRun.workspace_id == workspace_id,
               OrdoAnalyticsRun.status == "completed",
               OrdoAnalyticsRun.analytical_artifact_type.in_(("ANALYTICAL_SNAPSHOT", "ANALYTICAL_FEATURE_VERSION")))
        .order_by(OrdoAnalyticsRun.created_at.desc())
        .limit(50)
    ).all()
    assessments = session.execute(
        select(OrdoScenarioAssessment, OrdoScenario, OrdoAnalyticsRun)
        .join(OrdoScenario, OrdoScenario.id == OrdoScenarioAssessment.scenario_id)
        .join(OrdoAnalyticsRun, OrdoAnalyticsRun.id == OrdoScenarioAssessment.analytics_run_id)
        .where(
            OrdoScenarioAssessment.organization_id == organization_id,
            OrdoScenarioAssessment.workspace_id == workspace_id,
        )
        .order_by(OrdoScenarioAssessment.created_at.desc())
        .limit(50)
    ).all()
    eligible_runs = []
    for row in runs:
        try:
            revalidate_analytics_run(session, run=row, organization_id=organization_id, workspace_id=workspace_id)
        except OrdoAnalyticsError:
            continue
        eligible_runs.append(row)
    eligible_assessments = []
    for assessment, scenario, run in assessments:
        try:
            revalidate_analytics_run(
                session, run=run, organization_id=organization_id, workspace_id=workspace_id)
        except OrdoAnalyticsError:
            continue
        eligible_assessments.append((assessment, scenario))
    items = [
        {
            "kind": "analytics_run",
            "id": str(row.id),
            "label": f"ORDO destination snapshot {str(row.id)[:8]}",
            "created_at": row.created_at,
            "status": row.status,
        }
        for row in eligible_runs
    ]
    items.extend(
        {
            "kind": "scenario_assessment",
            "id": str(assessment.id),
            "label": f"Scenario: {scenario.name} · evidence-only assessment",
            "created_at": assessment.created_at,
            "status": assessment.status,
        }
        for assessment, scenario in eligible_assessments
    )
    return items


def _run_content(
    session: Session,
    *,
    run: OrdoAnalyticsRun,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> tuple[list[dict], list[dict]]:
    try:
        analytical_input = revalidate_analytics_run(
            session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    except OrdoAnalyticsError as exc:
        raise OrdoReportingError(str(exc)) from None
    result_rows = session.execute(
        select(OrdoIndicatorResult, OrdoIndicatorDefinition)
        .join(OrdoIndicatorDefinition, OrdoIndicatorDefinition.id == OrdoIndicatorResult.indicator_id)
        .where(
            OrdoIndicatorResult.analytics_run_id == run.id,
            OrdoIndicatorResult.organization_id == organization_id,
            OrdoIndicatorResult.workspace_id == workspace_id,
            OrdoIndicatorResult.status.in_(("computed", "reviewed")),
        )
        .order_by(OrdoIndicatorDefinition.code)
    ).all()
    indicators = []
    manifest = [
        _source(
            kind=("analytical_snapshot" if analytical_input.artifact_type == "snapshot" else "analytical_feature_version"),
            object_id=analytical_input.artifact_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            checksum=analytical_input.artifact_fingerprint,
            label="ORDO governed analytical source",
        ),
        _source(
            kind="ordo_analytics_run",
            object_id=run.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            checksum=_sha(run.snapshot),
            label="ORDO analytics snapshot",
        )
    ]
    for result, indicator in result_rows:
        indicators.append(
            {
                "indicator": indicator.code,
                "name": indicator.name_sr,
                "value": result.value_numeric if result.value_numeric is not None else result.value_text,
                "unit": result.unit,
                "quality_score": result.quality_score,
                "status": result.status,
            }
        )
        manifest.append(
            _source(
                kind="ordo_indicator_result",
                object_id=result.id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                checksum=_sha(
                    {
                        "indicator_id": str(result.indicator_id),
                        "methodology_id": str(result.methodology_id),
                        "value_numeric": result.value_numeric,
                        "value_text": result.value_text,
                        "unit": result.unit,
                        "quality_score": result.quality_score,
                        "source_observation_ids": result.source_observation_ids,
                        "computation_trace": result.computation_trace,
                    }
                ),
                label=f"ORDO indicator {indicator.code}",
            )
        )
    return indicators, manifest


def _reviewed_ai_section(
    session: Session,
    *,
    run_id: uuid.UUID,
    scenario_id: uuid.UUID | None,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> tuple[dict | None, dict | None]:
    stmt = (
        select(OrdoAISynthesis, AIJob)
        .join(AIJob, AIJob.id == OrdoAISynthesis.ai_job_id)
        .where(
            OrdoAISynthesis.analytics_run_id == run_id,
            OrdoAISynthesis.organization_id == organization_id,
            OrdoAISynthesis.workspace_id == workspace_id,
            OrdoAISynthesis.review_status == "accepted",
            AIJob.human_review_status == "accepted",
        )
        .order_by(OrdoAISynthesis.created_at.desc())
        .limit(1)
    )
    if scenario_id is not None:
        stmt = stmt.where(OrdoAISynthesis.scenario_id == scenario_id)
    row = session.execute(stmt).first()
    if row is None:
        return None, None
    synthesis, job = row
    structured = job.structured_output or {}
    if structured.get("forecast_performed") is True:
        raise OrdoReportingError("ordo_report_ai_forecast_forbidden")
    section = {
        "key": "reviewed_ai_synthesis",
        "title": "AI podrška — human-reviewed",
        "text": "AI izlaz je uključen samo nakon evidentiranog human review-a. Ne predstavlja predviđanje niti razvojnu odluku.",
        "rows": [{"field": key, "value": value} for key, value in structured.items()],
    }
    manifest = _source(
        kind="ordo_ai_synthesis_reviewed",
        object_id=synthesis.id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        checksum=_sha({"structured_output": structured, "review_status": synthesis.review_status}),
        label="ORDO reviewed AI synthesis",
    )
    return section, manifest


def build_report_payload(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    report_type: str,
    source_kind: str,
    source_id: uuid.UUID,
) -> tuple[dict, list[dict]]:
    if report_type == "destination_snapshot" and source_kind == "analytics_run":
        run = session.scalar(
            select(OrdoAnalyticsRun).where(
                OrdoAnalyticsRun.id == source_id,
                OrdoAnalyticsRun.organization_id == organization_id,
                OrdoAnalyticsRun.workspace_id == workspace_id,
                OrdoAnalyticsRun.status == "completed",
            )
        )
        if run is None:
            raise OrdoReportingError("ordo_report_source_not_accessible")
        indicators, manifest = _run_content(session, run=run, organization_id=organization_id, workspace_id=workspace_id)
        sections = [
            {
                "key": "scope",
                "title": "Obuhvat izveštaja",
                "text": "ORDO destination snapshot zasnovan na sačuvanom analytics run-u. Kvalitet evidencije i pokrivenost nisu prognoze razvoja niti ocena destinacije.",
            },
            {
                "key": "evidence_quality",
                "title": "Kvalitet i pokrivenost evidencije",
                "metrics": {
                    "evidence_quality_score": run.evidence_quality_score,
                    "validated_observation_ratio": run.validated_observation_ratio,
                    "provenance_coverage": run.provenance_coverage,
                    "indicator_coverage": run.indicator_coverage,
                    "dimension_coverage": run.dimension_coverage,
                    "pillar_coverage": run.pillar_coverage,
                },
            },
            {"key": "indicators", "title": "Indikatorski rezultati", "rows": indicators},
        ]
        ai_section, ai_manifest = _reviewed_ai_section(
            session,
            run_id=run.id,
            scenario_id=None,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        if ai_section:
            sections.append(ai_section)
            manifest.append(ai_manifest)
        return {
            "schema": "isi.reporting.v1",
            "product_code": "ORDO",
            "report_type": report_type,
            "source_kind": source_kind,
            "source_id": str(source_id),
            "sections": sections,
            "forecast_performed": False,
            "human_accountability": "Razvojna odluka i odgovornost ostaju ljudske.",
        }, manifest

    if report_type == "scenario_review" and source_kind == "scenario_assessment":
        row = session.execute(
            select(OrdoScenarioAssessment, OrdoScenario, OrdoAnalyticsRun)
            .join(OrdoScenario, OrdoScenario.id == OrdoScenarioAssessment.scenario_id)
            .join(OrdoAnalyticsRun, OrdoAnalyticsRun.id == OrdoScenarioAssessment.analytics_run_id)
            .where(
                OrdoScenarioAssessment.id == source_id,
                OrdoScenarioAssessment.organization_id == organization_id,
                OrdoScenarioAssessment.workspace_id == workspace_id,
            )
        ).first()
        if row is None:
            raise OrdoReportingError("ordo_report_source_not_accessible")
        assessment, scenario, run = row
        if assessment.forecast_performed:
            raise OrdoReportingError("ordo_report_forecast_forbidden")
        indicators, manifest = _run_content(session, run=run, organization_id=organization_id, workspace_id=workspace_id)
        manifest.append(
            _source(
                kind="ordo_scenario_assessment",
                object_id=assessment.id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                checksum=_sha(
                    {
                        "scenario_id": str(assessment.scenario_id),
                        "analytics_run_id": str(assessment.analytics_run_id),
                        "evidence_snapshot": assessment.evidence_snapshot,
                        "assessment": assessment.assessment,
                        "forecast_performed": assessment.forecast_performed,
                        "status": assessment.status,
                    }
                ),
                label=f"ORDO scenario assessment: {scenario.name}",
            )
        )
        sections = [
            {
                "key": "scenario",
                "title": "Scenario",
                "text": scenario.description or scenario.name,
                "bullets": [f"Pretpostavka: {value}" for value in (scenario.assumptions or [])]
                + [f"Mera za razmatranje: {value}" for value in (scenario.measures or [])],
            },
            {
                "key": "assessment",
                "title": "Evidence-only procena",
                "text": "Procena je evidenciona i ne sadrži predviđene efekte. forecast_performed=false je hard invariant.",
                "rows": [{"field": key, "value": value} for key, value in (assessment.assessment or {}).items()],
                "metrics": {"forecast_performed": False, "review_status": assessment.status},
            },
            {"key": "indicators", "title": "Indikatorski rezultati povezani sa snapshot-om", "rows": indicators},
        ]
        ai_section, ai_manifest = _reviewed_ai_section(
            session,
            run_id=run.id,
            scenario_id=scenario.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        if ai_section:
            sections.append(ai_section)
            manifest.append(ai_manifest)
        return {
            "schema": "isi.reporting.v1",
            "product_code": "ORDO",
            "report_type": report_type,
            "source_kind": source_kind,
            "source_id": str(source_id),
            "sections": sections,
            "forecast_performed": False,
            "human_accountability": "Scenario review je decision-support artefakt; razvojna odluka ostaje ljudska.",
        }, manifest

    raise OrdoReportingError("ordo_report_source_type_invalid")
