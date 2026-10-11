"""Customer reachability for existing identity-based ORDO aggregation only."""

from fastapi import APIRouter, Depends, HTTPException
from src.domains.ordo.analytics_schemas import SpatialAggregationRequest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.domains.ordo.analytics_models import OrdoIndicatorMethodology
from src.domains.ordo.models import OrdoIndicatorDefinition

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.api.ordo_analytics_routes import _error, _require_scope
from src.domains.ordo.analytics_service import OrdoAnalyticsError, create_spatial_aggregation_run
from src.platform.ai.service import actor_membership_id

router = APIRouter(prefix="/api/v1/ordo/analytics", tags=["ordo-analytics"])


@router.post("/spatial-aggregations", status_code=201)
def create_aggregation(
    body: SpatialAggregationRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=body.organization_id,
        workspace_id=body.workspace_id,
        permission_code="analysis.run",
    )
    actor = actor_membership_id(db, user_id=context.user.id, organization_id=body.organization_id)
    if actor is None:
        raise HTTPException(status_code=403, detail="ordo_analytics_scope_not_accessible")
    try:
        current = db.scalar(
            select(OrdoIndicatorMethodology)
            .join(OrdoIndicatorDefinition, OrdoIndicatorDefinition.id == OrdoIndicatorMethodology.indicator_id)
            .where(
                OrdoIndicatorDefinition.code == body.indicator_code,
                OrdoIndicatorDefinition.active.is_(True),
                OrdoIndicatorMethodology.status == "validated",
            )
            .order_by(OrdoIndicatorMethodology.version_no.desc())
            .with_for_update()
        )
        if current is None or current.id != body.reviewed_methodology_id:
            raise OrdoAnalyticsError("spatial_reviewed_methodology_changed")
        row = create_spatial_aggregation_run(db, **body.model_dump(exclude={"reviewed_methodology_id"}), actor_id=actor)
        db.commit()
        # Registration metadata only. Numerical truth is revalidated by the existing GIS results endpoint.
        return {
            "id": str(row.id),
            "analytics_run_id": str(row.analytics_run_id),
            "methodology_id": str(row.methodology_id),
            "methodology_version": row.methodology_version,
            "target_spatial_unit_id": str(row.target_spatial_unit_id),
            "aggregation_rule": row.aggregation_rule,
            "schema_version": row.schema_version,
            "run_fingerprint": row.run_fingerprint,
            "current_results": "GIS_REVALIDATION_REQUIRED",
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="spatial_aggregation_already_registered") from None
    except (OrdoAnalyticsError, ValueError) as exc:
        db.rollback()
        raise _error(exc) from None
