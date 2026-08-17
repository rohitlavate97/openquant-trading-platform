"""Programmatic API Key Management Endpoints."""

from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from openquant.domain.models.auth import Permission, User
from openquant.application.services.api_key_service import api_key_service
from openquant.interfaces.api.dependencies import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    permissions: list[Permission] = Field(default_factory=lambda: [Permission.READ_ONLY])
    expires_at: datetime | None = None


class CreateAPIKeyResponse(BaseModel):
    key_id: str
    name: str
    prefix: str
    raw_api_key: str = Field(..., description="Copy this key now. It will NEVER be shown again.")
    permissions: list[str]
    expires_at: str | None


class APIKeySummaryResponse(BaseModel):
    key_id: str
    name: str
    prefix: str
    permissions: list[str]
    is_active: bool
    last_used_at: str | None
    created_at: str


@router.post("", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED, summary="Create API Key")
async def create_api_key(
    req: CreateAPIKeyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> CreateAPIKeyResponse:
    """Generate a new programmatic API key for algorithmic or CLI automation."""
    # Ensure user only delegates permissions they actually possess
    allowed_perms = set(req.permissions).intersection(current_user.permissions)
    if not allowed_perms:
        allowed_perms = {Permission.READ_ONLY}

    api_key, raw_secret = await api_key_service.create_api_key(
        user_id=current_user.user_id,
        name=req.name,
        permissions=allowed_perms,
        expires_at=req.expires_at,
    )

    return CreateAPIKeyResponse(
        key_id=api_key.key_id,
        name=api_key.name,
        prefix=api_key.prefix,
        raw_api_key=raw_secret,
        permissions=[p.value for p in api_key.permissions],
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


@router.get("", response_model=list[APIKeySummaryResponse], summary="List API Keys")
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[APIKeySummaryResponse]:
    """List active API keys created by the current user."""
    keys = await api_key_service.list_keys_for_user(current_user.user_id)
    return [
        APIKeySummaryResponse(
            key_id=k.key_id,
            name=k.name,
            prefix=k.prefix,
            permissions=[p.value for p in k.permissions],
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.delete("/{key_id}", summary="Revoke API Key")
async def revoke_api_key(
    key_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Revoke and deactivate an API key immediately."""
    keys = await api_key_service.list_keys_for_user(current_user.user_id)
    target = next((k for k in keys if k.key_id == key_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    revoked = await api_key_service.revoke_key(key_id)
    return {"message": "API key revoked successfully", "revoked": revoked}
