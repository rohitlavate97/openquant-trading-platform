"""Unit tests for API Key creation, hashing, and authentication."""

from datetime import datetime, timedelta, timezone
import pytest
from openquant.domain.models.auth import Permission
from openquant.domain.exceptions import APIKeyRevokedError, AuthenticationError
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAPIKeyRepository
from openquant.application.services.api_key_service import APIKeyService


@pytest.mark.asyncio
async def test_api_key_lifecycle_create_auth_revoke():
    """Verify API key creation returns raw secret, authenticates, and handles revocation."""
    repo = InMemoryAPIKeyRepository()
    service = APIKeyService(key_repo=repo)

    api_key, raw_key = await service.create_api_key(
        user_id="usr_test",
        name="Algo Bot 1",
        permissions={Permission.ORDER_MANAGE, Permission.READ_ONLY},
    )

    assert raw_key.startswith("oq_live_")
    assert api_key.prefix == raw_key[:12]
    assert api_key.hashed_key != raw_key

    # Authenticate valid key
    authenticated = await service.authenticate_key(raw_key)
    assert authenticated.key_id == api_key.key_id
    assert Permission.ORDER_MANAGE in authenticated.permissions

    # Revoke key
    revoked = await service.revoke_key(api_key.key_id)
    assert revoked is True

    # Authenticate revoked key raises error
    with pytest.raises(APIKeyRevokedError):
        await service.authenticate_key(raw_key)


@pytest.mark.asyncio
async def test_api_key_expired_rejection():
    """Verify expired API key is rejected."""
    repo = InMemoryAPIKeyRepository()
    service = APIKeyService(key_repo=repo)

    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    api_key, raw_key = await service.create_api_key(
        user_id="usr_test",
        name="Expired Key",
        permissions={Permission.READ_ONLY},
        expires_at=past_time,
    )

    with pytest.raises(APIKeyRevokedError):
        await service.authenticate_key(raw_key)


@pytest.mark.asyncio
async def test_api_key_invalid_format_rejection():
    """Verify invalid format string raises AuthenticationError."""
    repo = InMemoryAPIKeyRepository()
    service = APIKeyService(key_repo=repo)

    with pytest.raises(AuthenticationError):
        await service.authenticate_key("invalid_key_format_123")
