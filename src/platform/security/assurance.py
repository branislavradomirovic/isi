from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from src.platform.auth.models import AuthSession


ASSURANCE_FRESHNESS_SECONDS = 600


class AssuranceRequirement(str, Enum):
    PASSWORD_OR_MFA = "password_or_mfa"
    MFA = "mfa"


class AssuranceMethod(str, Enum):
    PASSWORD = "password"
    MFA = "mfa"


class PrivilegedOperation(str, Enum):
    PLATFORM_ADMIN_GRANT = "platform_admin.grant"
    PLATFORM_ADMIN_REVOKE = "platform_admin.revoke"
    PLATFORM_ADMIN_CHANGE = "platform_admin.change"
    ORGANIZATION_MEMBER_STATUS_CHANGE = "organization.member_status.change"
    ROLE_ASSIGNMENT_CHANGE = "organization.role_assignment.change"
    MEMBERSHIP_PRODUCT_ACCESS_CHANGE = "organization.membership_product_access.change"
    INVITATION_PRIVILEGE_GRANT = "organization.invitation_privilege.grant"
    INVITATION_REVOKE = "organization.invitation.revoke"
    ORGANIZATION_ENTITLEMENT_CHANGE = "organization.entitlement.change"
    OTHER_USER_SESSION_REVOCATION = "security.other_user_session.revoke"
    SECURITY_CONTROL_CHANGE = "security.control.change"
    DESTRUCTIVE_ADMINISTRATION = "administration.destructive"
    SENSITIVE_EXPORT_ADMINISTRATION = "administration.sensitive_export"


class AssuranceDecisionReason(str, Enum):
    ALLOWED = "allowed"
    UNKNOWN_OPERATION = "unknown_operation"
    SESSION_REVOKED = "session_revoked"
    SESSION_EXPIRED = "session_expired"
    ASSURANCE_MISSING = "assurance_missing"
    ASSURANCE_STALE = "assurance_stale"
    ASSURANCE_INVALID = "assurance_invalid"
    ASSURANCE_INSUFFICIENT = "assurance_insufficient"


@dataclass(frozen=True)
class PrivilegedOperationPolicy:
    operation: PrivilegedOperation
    required_assurance: AssuranceRequirement
    freshness_seconds: int = ASSURANCE_FRESHNESS_SECONDS


@dataclass(frozen=True)
class AssuranceDecision:
    operation_code: str
    allowed: bool
    reason: AssuranceDecisionReason
    required_assurance: AssuranceRequirement
    satisfied_by: AssuranceMethod | None = None


def _policy(
    operation: PrivilegedOperation,
    required_assurance: AssuranceRequirement,
) -> PrivilegedOperationPolicy:
    return PrivilegedOperationPolicy(operation=operation, required_assurance=required_assurance)


PRIVILEGED_OPERATION_CATALOG: Mapping[PrivilegedOperation, PrivilegedOperationPolicy] = MappingProxyType(
    {
        operation: _policy(operation, requirement)
        for operation, requirement in {
            PrivilegedOperation.PLATFORM_ADMIN_GRANT: AssuranceRequirement.MFA,
            PrivilegedOperation.PLATFORM_ADMIN_REVOKE: AssuranceRequirement.MFA,
            PrivilegedOperation.PLATFORM_ADMIN_CHANGE: AssuranceRequirement.MFA,
            PrivilegedOperation.ORGANIZATION_MEMBER_STATUS_CHANGE: AssuranceRequirement.PASSWORD_OR_MFA,
            PrivilegedOperation.ROLE_ASSIGNMENT_CHANGE: AssuranceRequirement.PASSWORD_OR_MFA,
            PrivilegedOperation.MEMBERSHIP_PRODUCT_ACCESS_CHANGE: AssuranceRequirement.PASSWORD_OR_MFA,
            PrivilegedOperation.INVITATION_PRIVILEGE_GRANT: AssuranceRequirement.PASSWORD_OR_MFA,
            PrivilegedOperation.INVITATION_REVOKE: AssuranceRequirement.PASSWORD_OR_MFA,
            PrivilegedOperation.ORGANIZATION_ENTITLEMENT_CHANGE: AssuranceRequirement.MFA,
            PrivilegedOperation.OTHER_USER_SESSION_REVOCATION: AssuranceRequirement.PASSWORD_OR_MFA,
            PrivilegedOperation.SECURITY_CONTROL_CHANGE: AssuranceRequirement.MFA,
            PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION: AssuranceRequirement.MFA,
            PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION: AssuranceRequirement.MFA,
        }.items()
    }
)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _freshness(timestamp: datetime | None, *, now: datetime, freshness_seconds: int) -> str:
    if timestamp is None:
        return "missing"
    checked = _aware(timestamp)
    if checked > now:
        return "invalid"
    if checked + timedelta(seconds=freshness_seconds) < now:
        return "stale"
    return "fresh"


def evaluate_privileged_operation(
    auth_session: AuthSession,
    operation_code: PrivilegedOperation | str,
    *,
    now: datetime,
) -> AssuranceDecision:
    """Evaluate step-up only; authorization remains the caller's separate obligation."""
    normalized_code = operation_code.value if isinstance(operation_code, PrivilegedOperation) else str(operation_code)
    try:
        operation = PrivilegedOperation(normalized_code)
    except ValueError:
        return AssuranceDecision(
            operation_code=normalized_code,
            allowed=False,
            reason=AssuranceDecisionReason.UNKNOWN_OPERATION,
            required_assurance=AssuranceRequirement.MFA,
        )

    policy = PRIVILEGED_OPERATION_CATALOG[operation]
    decision_kwargs = {
        "operation_code": operation.value,
        "required_assurance": policy.required_assurance,
    }
    evaluated_at = _aware(now)
    if auth_session.revoked_at is not None:
        return AssuranceDecision(
            **decision_kwargs,
            allowed=False,
            reason=AssuranceDecisionReason.SESSION_REVOKED,
        )
    if _aware(auth_session.expires_at) <= evaluated_at:
        return AssuranceDecision(
            **decision_kwargs,
            allowed=False,
            reason=AssuranceDecisionReason.SESSION_EXPIRED,
        )

    mfa_state = _freshness(
        auth_session.mfa_verified_at,
        now=evaluated_at,
        freshness_seconds=policy.freshness_seconds,
    )
    if mfa_state == "fresh":
        return AssuranceDecision(
            **decision_kwargs,
            allowed=True,
            reason=AssuranceDecisionReason.ALLOWED,
            satisfied_by=AssuranceMethod.MFA,
        )

    password_state = _freshness(
        auth_session.password_verified_at,
        now=evaluated_at,
        freshness_seconds=policy.freshness_seconds,
    )
    if policy.required_assurance is AssuranceRequirement.PASSWORD_OR_MFA and password_state == "fresh":
        return AssuranceDecision(
            **decision_kwargs,
            allowed=True,
            reason=AssuranceDecisionReason.ALLOWED,
            satisfied_by=AssuranceMethod.PASSWORD,
        )

    states = {mfa_state, password_state}
    if "invalid" in states:
        reason = AssuranceDecisionReason.ASSURANCE_INVALID
    elif policy.required_assurance is AssuranceRequirement.MFA and password_state == "fresh":
        reason = AssuranceDecisionReason.ASSURANCE_INSUFFICIENT
    elif "stale" in states:
        reason = AssuranceDecisionReason.ASSURANCE_STALE
    else:
        reason = AssuranceDecisionReason.ASSURANCE_MISSING
    return AssuranceDecision(**decision_kwargs, allowed=False, reason=reason)
