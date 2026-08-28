from __future__ import annotations

from dataclasses import dataclass


class AIPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class EffectivePolicy:
    provider_policy: str
    allow_external: bool
    require_human_review: bool
    max_attempts: int
    forced_local_only: bool = False


def resolve_effective_policy(
    *,
    product_code: str,
    sensitivity: str,
    provider_policy: str,
    allow_external: bool,
    require_human_review: bool,
    max_attempts: int,
) -> EffectivePolicy:
    product = str(product_code).upper()
    sensitivity_value = str(sensitivity).lower()
    policy_value = str(provider_policy).lower()
    if product not in {"SIMPA", "ORDO"}:
        raise AIPolicyError("unsupported_product")
    if sensitivity_value not in {"public", "internal", "sensitive"}:
        raise AIPolicyError("unsupported_sensitivity")
    if policy_value not in {"local_only", "local_preferred", "any"}:
        raise AIPolicyError("unsupported_provider_policy")
    if not 1 <= int(max_attempts) <= 5:
        raise AIPolicyError("invalid_max_attempts")

    forced = product == "SIMPA" and sensitivity_value == "sensitive"
    if forced:
        return EffectivePolicy(
            provider_policy="local_only",
            allow_external=False,
            require_human_review=True,
            max_attempts=max(1, min(int(max_attempts), 5)),
            forced_local_only=True,
        )
    if policy_value == "local_only":
        allow_external = False
    return EffectivePolicy(
        provider_policy=policy_value,
        allow_external=bool(allow_external),
        require_human_review=bool(require_human_review),
        max_attempts=int(max_attempts),
        forced_local_only=False,
    )


def provider_allowed(*, policy: EffectivePolicy, local_provider: bool) -> bool:
    if local_provider:
        return True
    return policy.allow_external and policy.provider_policy in {"local_preferred", "any"}
