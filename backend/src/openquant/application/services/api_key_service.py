"""Application service for Programmatic API Key Lifecycle Management."""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from openquant.domain.models.auth import APIKey, Permission
from openquant.domain.ports.user_repository import IAPIKeyRepository
from openquant.domain.exceptions import APIKeyRevokedError, AuthenticationError
from openquant.adapters.repositories.in_memory_auth_repo import api_key_repository as default_key_repo


class APIKeyService:
    """Manages high-entropy API key generation, secure SHA-256 storage, and validation."""

    def __init__(self, key_repo: IAPIKeyRepository = default_key_repo) -> None:
        self._key_repo = key_repo

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        """Compute SHA-256 hash of API key for storage."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: set[Permission],
        expires_at: datetime | None = None,
    ) -> tuple[APIKey, str]:
        """Generate a new cryptographic API key.

        Returns a tuple of (APIKey entity, raw_secret_key).
        The raw secret key is presented ONLY ONCE to the user.
        """
        # Format: oq_live_<32 random hex characters>
        random_suffix = secrets.token_hex(20)
        raw_key = f"oq_live_{random_suffix}"
        prefix = raw_key[:12]
        hashed_key = self._hash_key(raw_key)

        api_key = APIKey(
            key_id=f"key_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
            permissions=permissions,
            is_active=True,
            expires_at=expires_at,
        )

        await self._key_repo.save(api_key)
        return api_key, raw_key

    async def authenticate_key(self, raw_key: str) -> APIKey:
        """Validate an incoming raw API key string against stored hashes."""
        if not raw_key.startswith("oq_"):
            raise AuthenticationError("Invalid API key format.")

        hashed_key = self._hash_key(raw_key)
        api_key = await self._key_repo.get_by_hashed_key(hashed_key)

        if not api_key:
            raise AuthenticationError("Invalid or unknown API key.")

        if not api_key.is_valid():
            raise APIKeyRevokedError("API key has expired or been revoked.")

        api_key.last_used_at = datetime.now(timezone.utc)
        await self._key_repo.save(api_key)
        return api_key

    async def list_keys_for_user(self, user_id: str) -> list[APIKey]:
        """List all active API keys for a user."""
        return await self._key_repo.list_by_user(user_id)

    async def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        return await self._key_repo.revoke(key_id)


# Global singleton instance
api_key_service = APIKeyService()
