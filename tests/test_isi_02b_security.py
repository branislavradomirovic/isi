import pytest

from src.platform.auth.security import PasswordPolicyError, hash_password, hash_token, new_opaque_token, verify_password


def test_argon2_password_hash_is_not_plaintext_and_verifies():
    password = "Correct-Horse-Battery-Staple-2026"
    encoded = hash_password(password)
    assert encoded != password
    assert encoded.startswith("$argon2id$")
    assert verify_password(password, encoded)
    assert not verify_password("wrong-password-value", encoded)


def test_password_policy_rejects_short_password():
    with pytest.raises(PasswordPolicyError):
        hash_password("too-short")


def test_opaque_tokens_are_random_and_only_digest_is_storage_safe():
    first = new_opaque_token("isi_test")
    second = new_opaque_token("isi_test")
    assert first != second
    assert len(hash_token(first)) == 64
    assert first not in hash_token(first)
