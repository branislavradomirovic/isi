from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class MeResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    email_verified: bool
    is_platform_admin: bool


class SessionInventoryResponse(BaseModel):
    session_id: UUID
    created_at: datetime
    last_seen_at: datetime | None
    expires_at: datetime
    is_current: bool
    is_revoked: bool
    revoked_at: datetime | None
    revocation_reason: str | None
    device_label: str = Field(max_length=80)


class RevokeOtherSessionsResponse(BaseModel):
    revoked_count: int = Field(ge=0)


class MessageResponse(BaseModel):
    status: str = "accepted"


class TokenConfirmRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(TokenConfirmRequest):
    new_password: str = Field(min_length=12, max_length=256)


class InvitationAcceptRequest(TokenConfirmRequest):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    password: str | None = Field(default=None, min_length=12, max_length=256)
