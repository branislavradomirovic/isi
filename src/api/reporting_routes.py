from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.domains.ordo.reporting_adapter import OrdoReportingError, available_sources as ordo_sources, build_report_payload as build_ordo_report
from src.domains.simpa.reporting_adapter import SimpaReportingError, available_sources as simpa_sources, build_report_payload as build_simpa_report
from src.platform.reporting import linked_evidence
from src.platform.reporting.schemas import EvidenceLink, ReportingScope
from src.platform.access.service import has_permission
from src.platform.app_context.service import AppContextError, resolve_selection
from src.platform.identity.models import Membership
from src.platform.reporting.schemas import (
    ReportExportRequest,
    ReportGenerateRequest,
    ReportLifecycleRequest,
    ReportReviewRequest,
    ReportVersionGenerateRequest,
)
from src.platform.reporting.service import (
    ReportingError,
    create_export,
    create_new_version,
    create_report,
    get_export_scoped,
    get_report_scoped,
    get_version_scoped,
    list_reports,
    list_reviews,
    list_versions,
    publish_version,
    review_version,
    submit_version,
)


router = APIRouter(prefix="/api/v1/reporting", tags=["reporting"])


def _require_scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    permission_code: str,
) -> None:
    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
        )
    except AppContextError:
        raise HTTPException(status_code=403, detail="reporting_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, product_code):
        raise HTTPException(status_code=403, detail="reporting_permission_denied")


def _actor_id(db: Session, *, user_id: uuid.UUID, organization_id: uuid.UUID) -> uuid.UUID | None:
    return db.scalar(
        select(Membership.id).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
    )


def _error(exc: Exception) -> HTTPException:
    code = str(exc)
    if code.startswith("linked_evidence_"):
        return HTTPException(status_code=409, detail="linked_evidence_no_longer_available")
    if code.endswith("not_accessible") or code.endswith("source_not_accessible"):
        return HTTPException(status_code=404, detail=code)
    if code in {
        "report_version_not_submittable",
        "report_version_not_reviewable",
        "report_version_not_publishable",
        "report_export_requires_approved_version",
        "report_provenance_required",
        "ordo_report_forecast_forbidden",
        "ordo_report_ai_forecast_forbidden",
    }:
        return HTTPException(status_code=409, detail=code)
    return HTTPException(status_code=400, detail=code)


def _build_domain_payload(
    db: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    report_type: str,
    source_kind: str,
    source_id: uuid.UUID,
    user_id: uuid.UUID,
    evidence_link=None,
):
    if source_kind == "extraction_request":
        if report_type != "linked_evidence" or evidence_link is None:
            raise ReportingError("linked_evidence_binding_required")
        return linked_evidence.build(db, user_id=user_id, organization_id=organization_id,
                                     workspace_id=workspace_id, product_code=product_code,
                                     request_id=source_id, link=evidence_link)
    if evidence_link is not None:
        raise ReportingError("linked_evidence_source_type_invalid")
    if product_code == "SIMPA":
        return build_simpa_report(
            db,
            organization_id=organization_id,
            workspace_id=workspace_id,
            report_type=report_type,
            source_kind=source_kind,
            source_id=source_id,
        )
    if product_code == "ORDO":
        return build_ordo_report(
            db,
            organization_id=organization_id,
            workspace_id=workspace_id,
            report_type=report_type,
            source_kind=source_kind,
            source_id=source_id,
        )
    raise ReportingError("report_product_invalid")


def _version_dict(version):
    return {
        "id": str(version.id),
        "version_no": version.version_no,
        "status": version.status,
        "content": version.content,
        "source_manifest": version.source_manifest,
        "content_sha256": version.content_sha256,
        "source_manifest_sha256": version.source_manifest_sha256,
        "created_at": version.created_at,
        "submitted_at": version.submitted_at,
        "approved_at": version.approved_at,
        "published_at": version.published_at,
    }


def _report_dict(db: Session, report, *, include_versions: bool = False, user_id=None):
    data = {
        "id": str(report.id),
        "organization_id": str(report.organization_id),
        "workspace_id": str(report.workspace_id),
        "product_code": report.product_code,
        "report_type": report.report_type,
        "title": report.title,
        "status": report.status,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
    if include_versions:
        versions = list_versions(db, report.id)
        for version in versions:
            linked_evidence.validate_version(db, user_id=user_id, report=report, version=version)
        data["versions"] = [
            {
                **_version_dict(version),
                "reviews": [
                    {
                        "id": str(review.id),
                        "decision": review.decision,
                        "note": review.note,
                        "reviewer_membership_id": str(review.reviewer_membership_id) if review.reviewer_membership_id else None,
                        "created_at": review.created_at,
                    }
                    for review in list_reviews(db, version.id)
                ],
            }
            for version in versions
        ]
    return data


@router.get("/sources")
def get_sources(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    product_code = product_code.upper()
    _require_scope(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="report.read",
    )
    if product_code == "SIMPA":
        return simpa_sources(db, organization_id=organization_id, workspace_id=workspace_id) + linked_evidence.sources(db, user_id=context.user.id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    if product_code == "ORDO":
        return ordo_sources(db, organization_id=organization_id, workspace_id=workspace_id) + linked_evidence.sources(db, user_id=context.user.id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    raise HTTPException(status_code=400, detail="report_product_invalid")


@router.get("/reports")
def get_reports(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    product_code = product_code.upper()
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, permission_code="report.read")
    return [
        _report_dict(db, report)
        for report in list_reports(db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    ]


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def post_report(
    payload: ReportGenerateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="analysis.run",
    )
    try:
        content, manifest = _build_domain_payload(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            report_type=payload.report_type,
            source_kind=payload.source_kind,
            source_id=payload.source_id,
            user_id=context.user.id,
            evidence_link=payload.evidence_link,
        )
        actor_id = _actor_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        report, version = create_report(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            report_type=payload.report_type,
            title=payload.title,
            content=content,
            source_manifest=manifest,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(report)
        db.refresh(version)
        return {**_report_dict(db, report), "version": _version_dict(version)}
    except (ReportingError, SimpaReportingError, OrdoReportingError) as exc:
        db.rollback()
        raise _error(exc) from None


@router.get("/reports/{report_id}")
def get_report(
    report_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    product_code = product_code.upper()
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, permission_code="report.read")
    try:
        report = get_report_scoped(db, report_id=report_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
        return _report_dict(db, report, include_versions=True, user_id=context.user.id)
    except ReportingError as exc:
        raise _error(exc) from None


@router.post("/reports/{report_id}/versions", status_code=status.HTTP_201_CREATED)
def post_report_version(
    report_id: uuid.UUID,
    payload: ReportVersionGenerateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code, permission_code="analysis.run")
    try:
        report = get_report_scoped(db, report_id=report_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code)
        content, manifest = _build_domain_payload(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            report_type=report.report_type,
            source_kind=payload.source_kind,
            source_id=payload.source_id,
            user_id=context.user.id,
            evidence_link=payload.evidence_link,
        )
        actor_id = _actor_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        version = create_new_version(db, report=report, content=content, source_manifest=manifest, actor_id=actor_id)
        db.commit()
        db.refresh(version)
        return _version_dict(version)
    except (ReportingError, SimpaReportingError, OrdoReportingError) as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/versions/{version_id}/submit")
def post_submit(
    version_id: uuid.UUID,
    payload: ReportLifecycleRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code, permission_code="analysis.run")
    try:
        version, report = get_version_scoped(db, version_id=version_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code)
        linked_evidence.validate_version(db, user_id=context.user.id, report=report, version=version)
        submit_version(db, version)
        db.commit()
        db.refresh(version)
        return _version_dict(version)
    except ReportingError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/versions/{version_id}/review")
def post_review(
    version_id: uuid.UUID,
    payload: ReportReviewRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code, permission_code="organization.manage")
    try:
        version, report = get_version_scoped(db, version_id=version_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code)
        actor_id = _actor_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        linked_evidence.validate_version(db, user_id=context.user.id, report=report, version=version)
        review = review_version(db, version=version, reviewer_id=actor_id, decision=payload.decision, note=payload.note)
        db.commit()
        db.refresh(version)
        db.refresh(review)
        return {"version": _version_dict(version), "review": {"id": str(review.id), "decision": review.decision, "note": review.note}}
    except ReportingError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/versions/{version_id}/publish")
def post_publish(
    version_id: uuid.UUID,
    payload: ReportLifecycleRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code, permission_code="organization.manage")
    try:
        version, report = get_version_scoped(db, version_id=version_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code)
        linked_evidence.validate_version(db, user_id=context.user.id, report=report, version=version)
        publish_version(db, version=version, report=report)
        db.commit()
        db.refresh(version)
        return _version_dict(version)
    except ReportingError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/versions/{version_id}/exports", status_code=status.HTTP_201_CREATED)
def post_export(
    version_id: uuid.UUID,
    payload: ReportExportRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code, permission_code="report.read")
    try:
        version, report = get_version_scoped(db, version_id=version_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code)
        actor_id = _actor_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        linked_evidence.validate_version(db, user_id=context.user.id, report=report, version=version)
        export = create_export(db, report=report, version=version, export_format=payload.format, actor_id=actor_id)
        db.commit()
        db.refresh(export)
        return {
            "id": str(export.id),
            "format": export.format,
            "filename": export.filename,
            "mime_type": export.mime_type,
            "sha256": export.sha256,
            "content_text": export.content_text,
        }
    except ReportingError as exc:
        db.rollback()
        raise _error(exc) from None


@router.get("/exports/{export_id}/download")
def get_export_download(
    export_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    product_code = product_code.upper()
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, permission_code="report.read")
    try:
        export, version, report = get_export_scoped(db, export_id=export_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
        linked_evidence.validate_version(db, user_id=context.user.id, report=report, version=version)
        if version.content.get("schema") == linked_evidence.SCHEMA:
            import hashlib
            if hashlib.sha256(export.content_text.encode("utf-8")).hexdigest() != export.sha256:
                raise ReportingError("linked_evidence_export_changed")
        return Response(
            content=export.content_text,
            media_type=export.mime_type,
            headers={"Content-Disposition": f'attachment; filename="{export.filename}"', "X-Content-SHA256": export.sha256},
        )
    except ReportingError as exc:
        raise _error(exc) from None


class LinkedPreviewRequest(ReportingScope):
    request_id: uuid.UUID
    evidence_link: EvidenceLink


@router.post("/linked-preview")
def post_linked_preview(payload: LinkedPreviewRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="report.read")
    try:
        content, manifest = linked_evidence.build(db, user_id=context.user.id, organization_id=payload.organization_id,
                                                  workspace_id=payload.workspace_id, product_code=payload.product_code,
                                                  request_id=payload.request_id, link=payload.evidence_link)
        return {"content": content, "source_manifest": manifest}
    except ReportingError:
        raise HTTPException(status_code=409, detail="linked_evidence_no_longer_available") from None
