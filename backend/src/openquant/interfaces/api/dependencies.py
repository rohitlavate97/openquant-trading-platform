"""FastAPI Security Dependencies for JWT, API Key Auth, and Granular RBAC."""

from typing import Annotated, Callable
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openquant.domain.models.auth import Permission, User, UserRole
from openquant.domain.exceptions import AuthenticationError, PermissionDeniedError
from openquant.adapters.security.jwt_handler import JWTHandler
from openquant.adapters.repositories.in_memory_auth_repo import user_repository
from openquant.application.services.api_key_service import api_key_service

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> User:
    """Resolve authenticated User from either Bearer JWT token or X-API-Key header."""
    # 1. Check Bearer Token
    if credentials and credentials.credentials:
        token = credentials.credentials
        payload = JWTHandler.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        user = await user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return user

    # 2. Check API Key
    if x_api_key:
        try:
            api_key = await api_key_service.authenticate_key(x_api_key)
            user = await user_repository.get_by_id(api_key.user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key owner not found or inactive",
                )
            return user
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials (provide Bearer token or X-API-Key header).",
    )


def require_permissions(*required_perms: Permission) -> Callable:
    """Dependency factory enforcing that the authenticated user possesses all required permissions."""
    async def _permission_checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        user_perms = user.permissions
        for perm in required_perms:
            if perm not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: missing required permission '{perm.value}'",
                )
        return user

    return _permission_checker


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory enforcing that the authenticated user has one of the specified roles."""
    async def _role_checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{user.role.value}' is not authorized for this operation.",
            )
        return user

    return _role_checker
