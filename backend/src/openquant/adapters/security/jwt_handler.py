"""JWT generation, decoding, and cryptographic signature validation."""

from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from openquant.config import settings
from openquant.domain.exceptions import InvalidTokenError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


class JWTHandler:
    """Utility for signing and verifying JSON Web Tokens."""

    @staticmethod
    def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Encode JWT access token with expiration claims."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": now,
            "type": "access",
        })
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Encode JWT refresh token with extended expiration."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({
            "exp": expire,
            "iat": now,
            "type": "refresh",
        })
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """Decode and verify token signature. Raises InvalidTokenError on failure or expiration."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise InvalidTokenError(f"Invalid or expired authentication token: {e}") from e
