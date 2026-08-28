from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domains.simpa.analytics_models import SimpaAISynthesis, SimpaAnalyticsRun, SimpaIndicatorResult
from src.domains.simpa.models import SimpaIndicatorDefinition
from src.platform.ai.models import AIJob


class SimpaReportingError(ValueError):
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
        "product_code": "SIMPA",
        "checksum": checksum,
        "label": label,
    }


def available_sources(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> list[dict]:
    rows = session.scalars(
        select(SimpaAnalyticsRun)
        .where(SimpaAnalyticsRun.organization_id == organization_id, SimpaAnalyticsRun.workspace_id == workspace_id, SimpaAnalyticsRun.status == "completed")
        .order_by(SimpaAnalyticsRun.created_at.desc())
        .limit(50)
    ).all()
    return [
        {
            "kind": "analytics_run",
            "id": str(row.id),
            "label": f"SIMPA monitoring snapshot {str(row.id)[:8]}",
            "created_at": row.created_at,
            "status": row.status,
        }
        for row in rows
    ]


def build_report_payload(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    report_type: str,
    source_kind: str,
    source_id: uuid.UUID,
) -> tuple[dict, list[dict]]:
    if report_type != "monitoring_summary" or source_kind != "analytics_run":
        raise SimpaReportingError("simpa_report_source_type_invalid")
    run = session.scalar(
        select(SimpaAnalyticsRun).where(
            SimpaAnalyticsRun.id == source_id,
            SimpaAnalyticsRun.organization_id == organization_id,
            SimpaAnalyticsRun.workspace_id == workspace_id,
            SimpaAnalyticsRun.status == "completed",
        )
    )
    if run is None:
        raise SimpaReportingError("simpa_report_source_not_accessible")

    result_rows = session.execute(
        select(SimpaIndicatorResult, SimpaIndicatorDefinition)
        .join(SimpaIndicatorDefinition, SimpaIndicatorDefinition.id == SimpaIndicatorResult.indicator_id)
        .where(
            SimpaIndicatorResult.analytics_run_id == run.id,
            SimpaIndicatorResult.organization_id == organization_id,
            SimpaIndicatorResult.workspace_id == workspace_id,
            SimpaIndicatorResult.status.in_(("computed", "reviewed")),
        )
        .order_by(SimpaIndicatorDefinition.code)
    ).all()

    indicators = []
    manifest = [
        _source(
            kind="simpa_analytics_run",
            object_id=run.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            checksum=_sha(run.snapshot),
            label="SIMPA analytics snapshot",
        )
    ]
    for result, indicator in result_rows:
        row = {
            "indicator": indicator.code,
            "name": indicator.name_sr,
            "value": result.value_numeric if result.value_numeric is not None else result.value_text,
            "unit": result.unit,
            "quality_score": result.quality_score,
            "status": result.status,
        }
        indicators.append(row)
        manifest.append(
            _source(
                kind="simpa_indicator_result",
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
                label=f"SIMPA indicator {indicator.code}",
            )
        )

    accepted_ai = session.execute(
        select(SimpaAISynthesis, AIJob)
        .join(AIJob, AIJob.id == SimpaAISynthesis.ai_job_id)
        .where(
            SimpaAISynthesis.analytics_run_id == run.id,
            SimpaAISynthesis.organization_id == organization_id,
            SimpaAISynthesis.workspace_id == workspace_id,
            SimpaAISynthesis.review_status == "accepted",
            AIJob.human_review_status == "accepted",
        )
        .order_by(SimpaAISynthesis.created_at.desc())
        .limit(1)
    ).first()
    ai_section = None
    if accepted_ai:
        synthesis, job = accepted_ai
        ai_section = {
            "key": "reviewed_ai_synthesis",
            "title": "AI podrška — human-reviewed",
            "text": "Ova sekcija prenosi samo AI izlaz koji je prethodno prihvaćen kroz human review. Ne predstavlja institucionalnu odluku.",
            "rows": [{"field": key, "value": value} for key, value in (job.structured_output or {}).items()],
        }
        manifest.append(
            _source(
                kind="simpa_ai_synthesis_reviewed",
                object_id=synthesis.id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                checksum=_sha({"structured_output": job.structured_output, "review_status": synthesis.review_status}),
                label="SIMPA reviewed AI synthesis",
            )
        )

    sections = [
        {
            "key": "scope",
            "title": "Obuhvat izveštaja",
            "text": "SIMPA monitoring izveštaj zasnovan na sačuvanom analytics snapshot-u i evidentiranim indikatorskim rezultatima. Evidence-quality metrike ne predstavljaju skor socijalnog rizika niti ocenu lokalne samouprave.",
        },
        {
            "key": "evidence_quality",
            "title": "Kvalitet i pokrivenost evidencije",
            "metrics": {
                "evidence_quality_score": run.evidence_quality_score,
                "validated_observation_ratio": run.validated_observation_ratio,
                "provenance_coverage": run.provenance_coverage,
                "indicator_coverage": run.indicator_coverage,
            },
        },
        {
            "key": "indicators",
            "title": "Indikatorski rezultati",
            "rows": indicators,
            "text": "Prikazani su samo rezultati koji zaista postoje u izabranom analytics snapshot-u. Konceptualni indikatori bez validirane metodologije ne proizvode izmišljene vrednosti.",
        },
    ]
    if ai_section:
        sections.append(ai_section)
    content = {
        "schema": "isi.reporting.v1",
        "product_code": "SIMPA",
        "report_type": report_type,
        "source_kind": source_kind,
        "source_id": str(source_id),
        "sections": sections,
        "human_accountability": "Stručna i institucionalna odgovornost ostaje na ljudima; reporting engine ne donosi odluke.",
    }
    return content, manifest
