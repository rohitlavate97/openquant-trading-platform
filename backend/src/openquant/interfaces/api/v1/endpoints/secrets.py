"""Encrypted Broker Credentials Vault API endpoints."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from openquant.domain.models.auth import Permission, User
from openquant.application.services.secrets_service import secrets_service
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/secrets", tags=["Secrets Vault"])


class StoreBrokerCredentialsRequest(BaseModel):
    broker_id: str = Field(..., description="Broker identifier e.g. zerodha, interactive_brokers")
    account_id: str = Field(..., description="Broker trading account ID")
    credentials: dict[str, str] = Field(..., description="API key, secret, and auth tokens to encrypt")


@router.post(
    "/broker-credentials",
    status_code=status.HTTP_201_CREATED,
    summary="Store Encrypted Broker Credentials",
)
async def store_credentials(
    req: StoreBrokerCredentialsRequest,
    current_user: Annotated[User, Depends(require_permissions(Permission.BROKER_MANAGE))],
) -> dict:
    """Store encrypted credentials for a broker connection. Requires BROKER_MANAGE permission."""
    if not req.credentials:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credentials payload cannot be empty")

    item = await secrets_service.store_broker_credentials(
        user_id=current_user.user_id,
        broker_id=req.broker_id,
        account_id=req.account_id,
        credentials=req.credentials,
    )

    return {
        "message": f"Credentials for broker '{req.broker_id}' securely encrypted and saved to vault.",
        "credential_id": item.credential_id,
        "broker_id": item.broker_id,
        "account_id": item.account_id,
        "key_version": item.key_version,
    }


@router.get(
    "/broker-credentials",
    summary="List Masked Broker Credentials",
)
async def list_credentials(
    current_user: Annotated[User, Depends(require_permissions(Permission.BROKER_MANAGE))],
) -> list[dict[str, Any]]:
    """List all configured broker credentials with sensitive values masked."""
    return await secrets_service.list_masked_credentials(current_user.user_id)


@router.delete(
    "/broker-credentials/{broker_id}",
    summary="Revoke Broker Credentials",
)
async def delete_credentials(
    broker_id: str,
    current_user: Annotated[User, Depends(require_permissions(Permission.BROKER_MANAGE))],
) -> dict:
    """Revoke and purge encrypted credentials for a broker connection."""
    deleted = await secrets_service.delete_credential(current_user.user_id, broker_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker credentials not found")
    return {"message": f"Credentials for broker '{broker_id}' revoked and deleted from vault."}
