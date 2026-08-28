import pytest

from src.platform.ai.policy import AIPolicyError, provider_allowed, resolve_effective_policy


def test_sensitive_simpa_forces_local_only_and_review():
    policy = resolve_effective_policy(
        product_code="SIMPA",
        sensitivity="sensitive",
        provider_policy="any",
        allow_external=True,
        require_human_review=False,
        max_attempts=3,
    )
    assert policy.provider_policy == "local_only"
    assert policy.allow_external is False
    assert policy.require_human_review is True
    assert policy.forced_local_only is True
    assert provider_allowed(policy=policy, local_provider=True)
    assert not provider_allowed(policy=policy, local_provider=False)


def test_ordo_internal_keeps_explicit_policy():
    policy = resolve_effective_policy(
        product_code="ORDO",
        sensitivity="internal",
        provider_policy="local_preferred",
        allow_external=True,
        require_human_review=True,
        max_attempts=2,
    )
    assert policy.provider_policy == "local_preferred"
    assert policy.allow_external is True
    assert policy.forced_local_only is False


def test_invalid_policy_is_rejected():
    with pytest.raises(AIPolicyError):
        resolve_effective_policy(
            product_code="SIMPA",
            sensitivity="internal",
            provider_policy="unknown",
            allow_external=False,
            require_human_review=True,
            max_attempts=2,
        )
