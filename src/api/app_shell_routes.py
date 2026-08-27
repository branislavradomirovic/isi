from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.platform.app_context.schemas import ProductCodeValue
from src.platform.app_context.service import AppContextError
from src.platform.app_shell.schemas import AppShellResponse
from src.platform.app_shell.service import resolve_app_shell


router = APIRouter(prefix="/api/v1/app-shell", tags=["app-shell"])


@router.get("", response_model=AppShellResponse)
def get_app_shell(
    organization_id: uuid.UUID = Query(...),
    product_code: ProductCodeValue = Query(...),
    workspace_id: uuid.UUID | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AppShellResponse:
    try:
        result = resolve_app_shell(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
        )
        db.commit()  # persist auth-session last_seen_at update
        return result
    except AppContextError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="app shell selection not accessible",
        ) from None
