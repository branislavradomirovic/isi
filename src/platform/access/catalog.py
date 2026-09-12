from __future__ import annotations

from enum import StrEnum


class ProductCode(StrEnum):
    SIMPA = "SIMPA"
    ORDO = "ORDO"


class RoleCode(StrEnum):
    ORGANIZATION_ADMIN = "organization_admin"
    DOMAIN_MANAGER = "domain_manager"
    ANALYST = "analyst"
    DATA_MANAGER = "data_manager"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class PermissionCode(StrEnum):
    ORGANIZATION_READ = "organization.read"
    ORGANIZATION_MANAGE = "organization.manage"
    MEMBERS_READ = "members.read"
    MEMBERS_MANAGE = "members.manage"
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_MANAGE = "workspace.manage"
    DATA_READ = "data.read"
    DATA_UPLOAD = "data.upload"
    DATA_VALIDATE = "data.validate"
    DATA_GOVERNANCE_MANAGE = "data.governance.manage"
    DATA_EXPORT = "data.export"
    INDICATOR_READ = "indicator.read"
    INDICATOR_MANAGE = "indicator.manage"
    ANALYSIS_READ = "analysis.read"
    ANALYSIS_RUN = "analysis.run"
    SCENARIO_READ = "scenario.read"
    SCENARIO_CREATE = "scenario.create"
    REPORT_READ = "report.read"
    REPORT_GENERATE = "report.generate"
    REPORT_PUBLISH = "report.publish"
    AUDIT_READ = "audit.read"
    AI_RUN = "ai.run"


ROLE_PERMISSION_MAP: dict[RoleCode, set[PermissionCode]] = {
    RoleCode.ORGANIZATION_ADMIN: set(PermissionCode),
    RoleCode.DOMAIN_MANAGER: {
        PermissionCode.ORGANIZATION_READ,
        PermissionCode.MEMBERS_READ,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.WORKSPACE_MANAGE,
        PermissionCode.DATA_READ,
        PermissionCode.DATA_UPLOAD,
        PermissionCode.DATA_VALIDATE,
        PermissionCode.DATA_GOVERNANCE_MANAGE,
        PermissionCode.DATA_EXPORT,
        PermissionCode.INDICATOR_READ,
        PermissionCode.INDICATOR_MANAGE,
        PermissionCode.ANALYSIS_READ,
        PermissionCode.ANALYSIS_RUN,
        PermissionCode.SCENARIO_READ,
        PermissionCode.SCENARIO_CREATE,
        PermissionCode.REPORT_READ,
        PermissionCode.REPORT_GENERATE,
        PermissionCode.REPORT_PUBLISH,
        PermissionCode.AI_RUN,
    },
    RoleCode.ANALYST: {
        PermissionCode.ORGANIZATION_READ,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.DATA_READ,
        PermissionCode.DATA_UPLOAD,
        PermissionCode.DATA_EXPORT,
        PermissionCode.INDICATOR_READ,
        PermissionCode.ANALYSIS_READ,
        PermissionCode.ANALYSIS_RUN,
        PermissionCode.SCENARIO_READ,
        PermissionCode.SCENARIO_CREATE,
        PermissionCode.REPORT_READ,
        PermissionCode.REPORT_GENERATE,
        PermissionCode.AI_RUN,
    },
    RoleCode.DATA_MANAGER: {
        PermissionCode.ORGANIZATION_READ,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.DATA_READ,
        PermissionCode.DATA_UPLOAD,
        PermissionCode.DATA_VALIDATE,
        PermissionCode.DATA_GOVERNANCE_MANAGE,
        PermissionCode.DATA_EXPORT,
        PermissionCode.INDICATOR_READ,
        PermissionCode.INDICATOR_MANAGE,
    },
    RoleCode.REVIEWER: {
        PermissionCode.ORGANIZATION_READ,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.DATA_READ,
        PermissionCode.INDICATOR_READ,
        PermissionCode.ANALYSIS_READ,
        PermissionCode.SCENARIO_READ,
        PermissionCode.REPORT_READ,
        PermissionCode.REPORT_GENERATE,
        PermissionCode.REPORT_PUBLISH,
    },
    RoleCode.VIEWER: {
        PermissionCode.ORGANIZATION_READ,
        PermissionCode.WORKSPACE_READ,
        PermissionCode.DATA_READ,
        PermissionCode.INDICATOR_READ,
        PermissionCode.ANALYSIS_READ,
        PermissionCode.SCENARIO_READ,
        PermissionCode.REPORT_READ,
    },
}
