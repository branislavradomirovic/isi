from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.platform.app_context.service import AppContextError, resolve_app_context, resolve_selection
from src.platform.app_shell.schemas import AppShellResponse, ShellNavigationItem, ShellSwitcherState


@dataclass(frozen=True)
class NavigationRule:
    code: str
    label_sr: str
    label_en: str
    permission_code: str | None
    implementation_phase: str


NAVIGATION_RULES = (
    NavigationRule("overview", "Pregled", "Overview", None, "ISI-05"),
    NavigationRule("data", "Podaci", "Data", "data.read", "ISI-06"),
    NavigationRule("ai", "AI", "AI", "ai.run", "ISI-07"),
    NavigationRule("indicators", "Indikatori", "Indicators", "indicator.read", "ISI-08/10"),
    NavigationRule("analysis", "Analitika", "Analytics", "analysis.read", "ISI-09/11"),
    NavigationRule("scenarios", "Scenariji", "Scenarios", "scenario.read", "ISI-09/11"),
    NavigationRule("reports", "Izveštaji", "Reports", "report.read", "ISI-12"),
)

ADMIN_PERMISSION_CODES = {
    "organization.manage",
    "members.manage",
    "workspace.manage",
    "audit.read",
}


def _navigation(permission_codes: set[str]) -> list[ShellNavigationItem]:
    items = [
        ShellNavigationItem(
            code=rule.code,
            label_sr=rule.label_sr,
            label_en=rule.label_en,
            permission_code=rule.permission_code,
            enabled=rule.permission_code is None or rule.permission_code in permission_codes,
            implementation_phase=rule.implementation_phase,
        )
        for rule in NAVIGATION_RULES
    ]
    items.append(
        ShellNavigationItem(
            code="administration",
            label_sr="Administracija",
            label_en="Administration",
            permission_code=None,
            enabled=bool(permission_codes & ADMIN_PERMISSION_CODES),
            implementation_phase="ISI-13",
        )
    )
    return items


def resolve_app_shell(
    session: Session,
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    product_code: str,
    workspace_id: uuid.UUID | None = None,
) -> AppShellResponse:
    context = resolve_app_context(session, user_id)
    selection = resolve_selection(
        session,
        user_id=user_id,
        organization_id=organization_id,
        product_code=product_code,
        workspace_id=workspace_id,
    )

    product = selection.product
    permission_codes = set(product.permission_codes)
    if selection.workspace is not None:
        workspace_state = "selected"
    elif product.workspaces:
        workspace_state = "available"
    else:
        workspace_state = "unconfigured"

    return AppShellResponse(
        user_id=str(context.user_id),
        display_name=context.display_name,
        email=context.email,
        is_platform_admin=context.is_platform_admin,
        organization=selection.organization,
        product=product,
        workspace=selection.workspace,
        navigation=_navigation(permission_codes),
        switcher=ShellSwitcherState(
            organization_switching=len(context.organizations) > 1,
            product_switching=len(selection.organization.products) > 1,
            workspace_switching=len(product.workspaces) > 1,
        ),
        workspace_state=workspace_state,
    )


__all__ = [
    "ADMIN_PERMISSION_CODES",
    "NAVIGATION_RULES",
    "AppContextError",
    "resolve_app_shell",
]
