from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.platform.app_context.schemas import AppContextResponse, SelectionRequest, SelectionResponse
from src.platform.app_context.service import AppContextError, resolve_app_context, resolve_selection


router = APIRouter(prefix="/api/v1/app-context", tags=["app-context"])


@router.get("", response_model=AppContextResponse)
def get_app_context(
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AppContextResponse:
    try:
        result = resolve_app_context(db, context.user.id)
        db.commit()  # persist auth last_seen_at update from the auth dependency
        return result
    except AppContextError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="application access unavailable") from None


@router.post("/select", response_model=SelectionResponse)
def select_app_context(
    payload: SelectionRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SelectionResponse:
    try:
        result = resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=payload.organization_id,
            product_code=payload.product_code,
            workspace_id=payload.workspace_id,
        )
        db.commit()  # persist auth last_seen_at update only; selection remains client/session state
        return result
    except AppContextError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="selection not accessible") from None
