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
