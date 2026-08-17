"""Application service for User Authentication and Token Management."""

import uuid
from typing import Any
from openquant.domain.models.auth import User, UserRole
from openquant.domain.ports.user_repository import IUserRepository
from openquant.domain.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
    InvalidTokenError,
)
from openquant.adapters.security.password import PasswordHasher
from openquant.adapters.security.jwt_handler import JWTHandler
from openquant.adapters.repositories.in_memory_auth_repo import user_repository as default_user_repo


class AuthService:
    """Orchestrates user registration, authentication, password verification, and JWT issuance."""

    def __init__(self, user_repo: IUserRepository = default_user_repo) -> None:
        self._user_repo = user_repo

    async def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.TRADER,
    ) -> User:
        """Register a new platform user with hashed password."""
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"User with email '{email}' is already registered.")

        if len(password) < 8:
            raise AuthenticationError("Password must be at least 8 characters long.")

        user = User(
            user_id=f"usr_{uuid.uuid4().hex[:12]}",
            email=email,
            hashed_password=PasswordHasher.hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        await self._user_repo.save(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any]:
        """Verify user credentials and issue access + refresh JWT tokens."""
        user = await self._user_repo.get_by_email(email)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid email or password.")

        if not PasswordHasher.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        token_claims = {
            "sub": user.user_id,
            "email": str(user.email),
            "role": user.role.value,
        }

        access_token = JWTHandler.create_access_token(token_claims)
        refresh_token = JWTHandler.create_refresh_token(token_claims)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions],
            },
        }

    async def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        """Issue new access token from valid refresh token."""
        payload = JWTHandler.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type. Expected refresh token.")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token claims: missing subject.")

        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User account not found or deactivated.")

        token_claims = {
            "sub": user.user_id,
            "email": str(user.email),
            "role": user.role.value,
        }

        new_access_token = JWTHandler.create_access_token(token_claims)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }


# Global singleton instance
auth_service = AuthService()
