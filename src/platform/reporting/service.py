from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.platform.reporting.models import Report, ReportExport, ReportReview, ReportVersion
from src.platform.reporting.render import EXTENSIONS, MIME_TYPES, render_html, render_json, render_markdown, safe_slug


class ReportingError(ValueError):
    pass


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _now():
    return datetime.now(timezone.utc)


def validate_source_manifest(
    source_manifest: list[dict],
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> None:
    if not source_manifest:
        raise ReportingError("report_provenance_required")
    for item in source_manifest:
        required = {"kind", "id", "organization_id", "workspace_id", "product_code", "checksum"}
        if not required.issubset(item):
            raise ReportingError("report_source_manifest_invalid")
        if str(item["organization_id"]) != str(organization_id):
            raise ReportingError("report_source_cross_tenant")
        if str(item["workspace_id"]) != str(workspace_id):
            raise ReportingError("report_source_cross_workspace")
        if str(item["product_code"]).upper() != product_code:
            raise ReportingError("report_source_cross_product")
        checksum = str(item.get("checksum", ""))
        if len(checksum) != 64 or any(ch not in "0123456789abcdef" for ch in checksum.casefold()):
            raise ReportingError("report_source_checksum_invalid")


def create_report(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    report_type: str,
    title: str,
    content: dict,
    source_manifest: list[dict],
    actor_id: uuid.UUID | None,
) -> tuple[Report, ReportVersion]:
    product_code = product_code.upper()
    if product_code not in {"SIMPA", "ORDO"}:
        raise ReportingError("report_product_invalid")
    validate_source_manifest(
        source_manifest,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    report = Report(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        report_type=report_type,
        title=title.strip(),
        status="active",
        created_by_membership_id=actor_id,
    )
    session.add(report)
    session.flush()
    version = _create_version(
        session,
        report=report,
        version_no=1,
        content=content,
        source_manifest=source_manifest,
        actor_id=actor_id,
    )
    return report, version


def _create_version(
    session: Session,
    *,
    report: Report,
    version_no: int,
    content: dict,
    source_manifest: list[dict],
    actor_id: uuid.UUID | None,
) -> ReportVersion:
    validate_source_manifest(
        source_manifest,
        organization_id=report.organization_id,
        workspace_id=report.workspace_id,
        product_code=report.product_code,
    )
    version = ReportVersion(
        report_id=report.id,
        version_no=version_no,
        status="draft",
        content=content,
        source_manifest=source_manifest,
        content_sha256=sha256_json(content),
        source_manifest_sha256=sha256_json(source_manifest),
        created_by_membership_id=actor_id,
    )
    session.add(version)
    session.flush()
    return version


def create_new_version(
    session: Session,
    *,
    report: Report,
    content: dict,
    source_manifest: list[dict],
    actor_id: uuid.UUID | None,
) -> ReportVersion:
    current = session.scalar(select(func.max(ReportVersion.version_no)).where(ReportVersion.report_id == report.id)) or 0
    report.updated_at = _now()
    return _create_version(
        session,
        report=report,
        version_no=int(current) + 1,
        content=content,
        source_manifest=source_manifest,
        actor_id=actor_id,
    )


def get_report_scoped(
    session: Session,
    *,
    report_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> Report:
    row = session.scalar(
        select(Report).where(
            Report.id == report_id,
            Report.organization_id == organization_id,
            Report.workspace_id == workspace_id,
            Report.product_code == product_code.upper(),
        )
    )
    if row is None:
        raise ReportingError("report_not_accessible")
    return row


def get_version_scoped(
    session: Session,
    *,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> tuple[ReportVersion, Report]:
    row = session.execute(
        select(ReportVersion, Report)
        .join(Report, Report.id == ReportVersion.report_id)
        .where(
            ReportVersion.id == version_id,
            Report.organization_id == organization_id,
            Report.workspace_id == workspace_id,
            Report.product_code == product_code.upper(),
        )
    ).first()
    if row is None:
        raise ReportingError("report_version_not_accessible")
    return row[0], row[1]


def list_reports(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[Report]:
    return list(
        session.scalars(
            select(Report)
            .where(
                Report.organization_id == organization_id,
                Report.workspace_id == workspace_id,
                Report.product_code == product_code.upper(),
            )
            .order_by(Report.updated_at.desc(), Report.created_at.desc())
        ).all()
    )


def list_versions(session: Session, report_id: uuid.UUID) -> list[ReportVersion]:
    return list(
        session.scalars(
            select(ReportVersion)
            .where(ReportVersion.report_id == report_id)
            .order_by(ReportVersion.version_no.desc())
        ).all()
    )


def list_reviews(session: Session, version_id: uuid.UUID) -> list[ReportReview]:
    return list(
        session.scalars(
            select(ReportReview)
            .where(ReportReview.report_version_id == version_id)
            .order_by(ReportReview.created_at.desc())
        ).all()
    )


def submit_version(session: Session, version: ReportVersion) -> ReportVersion:
    if version.status != "draft":
        raise ReportingError("report_version_not_submittable")
    if not version.content or not version.source_manifest:
        raise ReportingError("report_version_incomplete")
    version.status = "in_review"
    version.submitted_at = _now()
    return version


def review_version(
    session: Session,
    *,
    version: ReportVersion,
    reviewer_id: uuid.UUID | None,
    decision: str,
    note: str,
) -> ReportReview:
    if version.status != "in_review":
        raise ReportingError("report_version_not_reviewable")
    if decision not in {"approved", "rejected"}:
        raise ReportingError("report_review_decision_invalid")
    review = ReportReview(
        report_version_id=version.id,
        reviewer_membership_id=reviewer_id,
        decision=decision,
        note=note.strip(),
    )
    session.add(review)
    version.status = decision
    if decision == "approved":
        version.approved_at = _now()
    return review


def publish_version(session: Session, *, version: ReportVersion, report: Report) -> ReportVersion:
    if version.status != "approved":
        raise ReportingError("report_version_not_publishable")
    session.execute(
        update(ReportVersion)
        .where(
            ReportVersion.report_id == report.id,
            ReportVersion.status == "published",
            ReportVersion.id != version.id,
        )
        .values(status="superseded")
    )
    version.status = "published"
    version.published_at = _now()
    report.status = "active"
    report.updated_at = _now()
    return version


def _metadata(report: Report, version: ReportVersion) -> dict:
    return {
        "report_id": str(report.id),
        "version_id": str(version.id),
        "version_no": version.version_no,
        "title": report.title,
        "report_type": report.report_type,
        "product_code": report.product_code,
        "organization_id": str(report.organization_id),
        "workspace_id": str(report.workspace_id),
        "status": version.status,
        "content_sha256": version.content_sha256,
        "source_manifest_sha256": version.source_manifest_sha256,
        "published_at": version.published_at.isoformat() if version.published_at else None,
    }


def create_export(
    session: Session,
    *,
    report: Report,
    version: ReportVersion,
    export_format: str,
    actor_id: uuid.UUID | None,
) -> ReportExport:
    if version.status not in {"approved", "published", "superseded"}:
        raise ReportingError("report_export_requires_approved_version")
    if export_format not in {"json", "markdown", "html"}:
        raise ReportingError("report_export_format_invalid")
    metadata = _metadata(report, version)
    if export_format == "json":
        text = render_json(metadata=metadata, content=version.content, source_manifest=version.source_manifest)
    elif export_format == "markdown":
        text = render_markdown(metadata=metadata, content=version.content, source_manifest=version.source_manifest)
    else:
        text = render_html(metadata=metadata, content=version.content, source_manifest=version.source_manifest)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing = session.scalar(
        select(ReportExport).where(
            ReportExport.report_version_id == version.id,
            ReportExport.format == export_format,
            ReportExport.sha256 == digest,
        )
    )
    if existing is not None:
        return existing
    filename = f"{safe_slug(report.title)}-v{version.version_no}.{EXTENSIONS[export_format]}"
    row = ReportExport(
        report_version_id=version.id,
        format=export_format,
        filename=filename,
        mime_type=MIME_TYPES[export_format],
        content_text=text,
        sha256=digest,
        generated_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def get_export_scoped(
    session: Session,
    *,
    export_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> tuple[ReportExport, ReportVersion, Report]:
    row = session.execute(
        select(ReportExport, ReportVersion, Report)
        .join(ReportVersion, ReportVersion.id == ReportExport.report_version_id)
        .join(Report, Report.id == ReportVersion.report_id)
        .where(
            ReportExport.id == export_id,
            Report.organization_id == organization_id,
            Report.workspace_id == workspace_id,
            Report.product_code == product_code.upper(),
        )
    ).first()
    if row is None:
        raise ReportingError("report_export_not_accessible")
    return row[0], row[1], row[2]
