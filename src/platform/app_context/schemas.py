from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProductCodeValue = Literal["SIMPA", "ORDO"]
RouteMode = Literal["no_access", "selector", "product", "workspace"]


class WorkspaceOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    slug: str
    name: str


class ProductOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ProductCodeValue
    name: str
    role_codes: list[str] = Field(default_factory=list)
    permission_codes: list[str] = Field(default_factory=list)
    workspaces: list[WorkspaceOption] = Field(default_factory=list)


class OrganizationOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    slug: str
    name: str
    membership_id: uuid.UUID | None = None
    products: list[ProductOption] = Field(default_factory=list)


class InitialRoute(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: RouteMode
    organization_id: uuid.UUID | None = None
    product_code: ProductCodeValue | None = None
    workspace_id: uuid.UUID | None = None


class AppContextResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: uuid.UUID
    display_name: str
    email: str
    is_platform_admin: bool
    organizations: list[OrganizationOption] = Field(default_factory=list)
    initial_route: InitialRoute


class SelectionRequest(BaseModel):
    organization_id: uuid.UUID
    product_code: ProductCodeValue
    workspace_id: uuid.UUID | None = None


class SelectionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization: OrganizationOption
    product: ProductOption
    workspace: WorkspaceOption | None = None
