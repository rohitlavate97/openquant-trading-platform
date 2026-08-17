"""Cryptographic password hashing and verification using standard bcrypt."""

import bcrypt


class PasswordHasher:
    """Utility class for hashing and verifying user passwords using direct bcrypt."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Generate secure bcrypt cryptographic hash with automatic random salt."""
        # bcrypt handles up to 72 bytes; enforce length guard
        password_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain password against stored bcrypt hash."""
        try:
            password_bytes = plain_password.encode("utf-8")[:72]
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
