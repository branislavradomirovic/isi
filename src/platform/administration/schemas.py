from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


ProductCode = Literal["SIMPA", "ORDO"]


class InvitationCreateRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    email: EmailStr
    role_code: str = Field(min_length=1, max_length=80)


class MemberStatusRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    status: Literal["active", "suspended"]


class ProductAccessRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    active: bool


class RoleAssignmentRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    role_code: str = Field(min_length=1, max_length=80)
    scope: Literal["product", "organization"] = "product"


class WorkspaceCreateRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    name: str = Field(min_length=2, max_length=240)
    slug: str = Field(min_length=2, max_length=120)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()


class WorkspaceStatusRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    status: Literal["active", "archived"]


class OrganizationNameRequest(BaseModel):
    organization_id: UUID
    product_code: ProductCode
    name: str = Field(min_length=2, max_length=240)


class AdminSessionInventoryResponse(BaseModel):
    session_id: UUID
    created_at: datetime
    last_seen_at: datetime | None
    expires_at: datetime
    is_current: bool
    is_revoked: bool
    revoked_at: datetime | None
    revocation_reason: str | None
    device_label: str = Field(max_length=80)
