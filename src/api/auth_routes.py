from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.auth.delivery import AuthDelivery, get_auth_delivery
from src.platform.auth.schemas import (
    EmailVerificationRequest,
    InvitationAcceptRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordAssuranceRequest,
    PasswordAssuranceResponse,
    RevokeOtherSessionsResponse,
    SessionInventoryResponse,
    TokenConfirmRequest,
)
from src.platform.auth.security import PasswordPolicyError
from src.platform.auth.service import (
    AuthError,
    accept_invitation,
    authenticate_user,
    confirm_email_verification,
    create_email_verification_token,
    create_password_reset_token,
    create_session,
    list_user_sessions,
    refresh_password_assurance,
    reset_password_with_token,
    revoke_other_user_sessions,
    revoke_session,
    revoke_user_session,
)
from src.platform.security.service import (
    check_login_allowed,
    clear_login_failures,
    record_security_event,
    register_login_failure,
    resolve_client_ip,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _require_email_available() -> None:
    if get_settings().auth_delivery_mode.strip().casefold() == "pending":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication email delivery is temporarily unavailable",
        )


def _me(user) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified_at is not None,
        is_platform_admin=user.is_platform_admin,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    remote_ip = resolve_client_ip(request)
    user_agent = request.headers.get("user-agent")
    decision = check_login_allowed(db, email=str(payload.email), remote_ip=remote_ip)
    if not decision.allowed:
        record_security_event(
            db,
            event_type="auth.login",
            outcome="throttled",
            subject=str(payload.email),
            remote_ip=remote_ip,
            user_agent=user_agent,
            metadata={"retry_after_seconds": decision.retry_after_seconds},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="authentication temporarily unavailable",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    user = authenticate_user(db, str(payload.email), payload.password)
    if user is None:
        register_login_failure(db, email=str(payload.email), remote_ip=remote_ip)
        record_security_event(
            db,
            event_type="auth.login",
            outcome="failure",
            subject=str(payload.email),
            remote_ip=remote_ip,
            user_agent=user_agent,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    clear_login_failures(db, email=str(payload.email), remote_ip=remote_ip)
    issued = create_session(
        db,
        user,
        password_verified=True,
        remote_ip=remote_ip,
        user_agent=user_agent,
    )
    record_security_event(
        db,
        event_type="auth.login",
        outcome="success",
        user_id=user.id,
        subject=str(payload.email),
        remote_ip=remote_ip,
        user_agent=user_agent,
    )
    db.commit()
    return LoginResponse(access_token=issued.token, expires_at=issued.expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> None:
    revoke_session(db, context.token)
    record_security_event(
        db,
        event_type="auth.logout",
        outcome="success",
        user_id=context.user.id,
        metadata={"session_id": str(context.auth_session.id)},
    )
    db.commit()
    return None


@router.get("/me", response_model=MeResponse)
def me(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> MeResponse:
    db.commit()  # persist last_seen_at update
    return _me(context.user)


@router.get("/sessions", response_model=list[SessionInventoryResponse])
def sessions(
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[SessionInventoryResponse]:
    inventory = list_user_sessions(
        db,
        user_id=context.user.id,
        current_session_id=context.auth_session.id,
    )
    db.commit()  # persist the authenticated session's last_seen_at update
    return [SessionInventoryResponse(**vars(item)) for item in inventory]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> None:
    if not revoke_user_session(db, user_id=context.user.id, session_id=session_id):
        db.rollback()
        record_security_event(
            db,
            event_type="auth.session.revoke_self",
            outcome="not_found",
            user_id=context.user.id,
            metadata={"session_id": str(session_id)},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    record_security_event(
        db,
        event_type="auth.session.revoke_self",
        outcome="success",
        user_id=context.user.id,
        metadata={"session_id": str(session_id)},
    )
    db.commit()
    return None


@router.post("/sessions/revoke-others", response_model=RevokeOtherSessionsResponse)
def revoke_other_sessions(
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RevokeOtherSessionsResponse:
    revoked_count = revoke_other_user_sessions(
        db,
        user_id=context.user.id,
        current_session_id=context.auth_session.id,
    )
    record_security_event(
        db,
        event_type="auth.session.revoke_others",
        outcome="success",
        user_id=context.user.id,
        metadata={"revoked_count": revoked_count, "current_session_id": str(context.auth_session.id)},
    )
    db.commit()
    return RevokeOtherSessionsResponse(revoked_count=revoked_count)


@router.post("/assurance/password", response_model=PasswordAssuranceResponse)
def refresh_password_step_up(
    payload: PasswordAssuranceRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PasswordAssuranceResponse:
    try:
        refresh_password_assurance(
            db,
            user_id=context.user.id,
            session_id=context.auth_session.id,
            password=payload.password,
        )
    except AuthError as exc:
        db.rollback()
        record_security_event(
            db,
            event_type="auth.assurance.password",
            outcome="failure",
            user_id=context.user.id,
            metadata={"reason": exc.code, "session_id": str(context.auth_session.id)},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="password re-verification failed") from None
    record_security_event(
        db,
        event_type="auth.assurance.password",
        outcome="success",
        user_id=context.user.id,
        metadata={"session_id": str(context.auth_session.id), "method": "password"},
    )
    db.commit()
    return PasswordAssuranceResponse()


@router.post("/email-verification/request", response_model=MessageResponse,
             status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(_require_email_available)])
def request_email_verification(
    payload: EmailVerificationRequest,
    db: Session = Depends(get_db),
    delivery: AuthDelivery = Depends(get_auth_delivery),
) -> MessageResponse:
    from sqlalchemy import select
    from src.platform.auth.service import normalize_email
    from src.platform.identity.models import User

    try:
        normalized = normalize_email(str(payload.email))
        user = db.scalar(select(User).where(User.email == normalized, User.is_active.is_(True)))
    except AuthError:
        user = None
    if user is not None and user.email_verified_at is None:
        issued = create_email_verification_token(db, user)
        delivery.send_email_verification(email=user.email, token=issued.token)
        db.commit()
    else:
        db.rollback()
    # Deliberately identical response for existing, verified and unknown accounts.
    return MessageResponse()


@router.post("/email-verification/confirm", response_model=MeResponse)
def confirm_verification(payload: TokenConfirmRequest, db: Session = Depends(get_db)) -> MeResponse:
    try:
        user = confirm_email_verification(db, payload.token)
        db.commit()
        return _me(user)
    except AuthError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired token") from None


@router.post("/password-reset/request", response_model=MessageResponse,
             status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(_require_email_available)])
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    delivery: AuthDelivery = Depends(get_auth_delivery),
) -> MessageResponse:
    result = create_password_reset_token(db, str(payload.email))
    if result is not None:
        user, issued = result
        delivery.send_password_reset(email=user.email, token=issued.token)
        db.commit()
    else:
        db.rollback()
    # Deliberately identical response for existing and unknown accounts.
    return MessageResponse()


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)) -> MessageResponse:
    try:
        user = reset_password_with_token(db, payload.token, payload.new_password)
        record_security_event(
            db,
            event_type="auth.password_reset.confirm",
            outcome="success",
            user_id=user.id,
        )
        db.commit()
        return MessageResponse(status="completed")
    except (AuthError, PasswordPolicyError):
        db.rollback()
        record_security_event(db, event_type="auth.password_reset.confirm", outcome="failure")
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid reset request") from None


@router.post("/invitations/accept", response_model=LoginResponse)
def accept_invite(payload: InvitationAcceptRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    remote_ip = resolve_client_ip(request)
    user_agent = request.headers.get("user-agent")
    try:
        user, _membership = accept_invitation(
            db,
            raw_token=payload.token,
            display_name=payload.display_name,
            password=payload.password,
        )
        issued = create_session(
            db,
            user,
            remote_ip=remote_ip,
            user_agent=user_agent,
        )
        record_security_event(
            db,
            event_type="auth.invitation.accept",
            outcome="success",
            user_id=user.id,
            remote_ip=remote_ip,
            user_agent=user_agent,
        )
        db.commit()
        return LoginResponse(access_token=issued.token, expires_at=issued.expires_at)
    except (AuthError, PasswordPolicyError):
        db.rollback()
        record_security_event(
            db,
            event_type="auth.invitation.accept",
            outcome="failure",
            remote_ip=remote_ip,
            user_agent=user_agent,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid invitation") from None
