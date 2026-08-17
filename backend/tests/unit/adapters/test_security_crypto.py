"""Unit tests for password hashing and JWT lifecycle."""

import pytest
from openquant.adapters.security.password import PasswordHasher
from openquant.adapters.security.jwt_handler import JWTHandler
from openquant.domain.exceptions import InvalidTokenError


def test_password_hasher_hash_and_verify():
    """Verify password hashing creates non-reversible hash and validates properly."""
    raw_password = "SecureTradingPassword123!"
    hashed = PasswordHasher.hash_password(raw_password)

    assert hashed != raw_password
    assert PasswordHasher.verify_password(raw_password, hashed) is True
    assert PasswordHasher.verify_password("WrongPassword999", hashed) is False


def test_jwt_handler_access_and_refresh_token_lifecycle():
    """Verify JWT access and refresh token encoding, claim retrieval, and type distinction."""
    claims = {
        "sub": "usr_test123",
        "email": "trader@openquant.org",
        "role": "TRADER",
    }

    access_token = JWTHandler.create_access_token(claims)
    decoded_access = JWTHandler.decode_token(access_token)
    assert decoded_access["sub"] == "usr_test123"
    assert decoded_access["email"] == "trader@openquant.org"
    assert decoded_access["type"] == "access"

    refresh_token = JWTHandler.create_refresh_token(claims)
    decoded_refresh = JWTHandler.decode_token(refresh_token)
    assert decoded_refresh["sub"] == "usr_test123"
    assert decoded_refresh["type"] == "refresh"


def test_jwt_handler_rejects_tampered_token():
    """Verify invalid or tampered token raises InvalidTokenError."""
    claims = {"sub": "usr_test123"}
    valid_token = JWTHandler.create_access_token(claims)

    tampered_token = valid_token[:-4] + "fake"
    with pytest.raises(InvalidTokenError):
        JWTHandler.decode_token(tampered_token)
