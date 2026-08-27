from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.platform.app_context.schemas import OrganizationOption, ProductOption, WorkspaceOption


ShellNavCode = Literal[
    "overview",
    "data",
    "indicators",
    "analysis",
    "scenarios",
    "reports",
    "administration",
]


class ShellNavigationItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ShellNavCode
    label_sr: str
    label_en: str
    permission_code: str | None = None
    enabled: bool
    implementation_phase: str


class ShellSwitcherState(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_switching: bool
    product_switching: bool
    workspace_switching: bool


class AppShellResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    display_name: str
    email: str
    is_platform_admin: bool
    organization: OrganizationOption
    product: ProductOption
    workspace: WorkspaceOption | None = None
    navigation: list[ShellNavigationItem] = Field(default_factory=list)
    switcher: ShellSwitcherState
    workspace_state: Literal["selected", "available", "unconfigured"]
