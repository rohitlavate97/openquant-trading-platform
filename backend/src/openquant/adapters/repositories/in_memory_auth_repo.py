"""In-memory repository implementations for User, API Key, and Secrets Vault."""

from openquant.domain.models.auth import User, APIKey, BrokerCredentialVaultItem
from openquant.domain.ports.user_repository import (
    IUserRepository,
    IAPIKeyRepository,
    ICredentialVaultRepository,
)


class InMemoryUserRepository(IUserRepository):
    """In-memory User storage."""

    def __init__(self) -> None:
        self._users_by_id: dict[str, User] = {}
        self._users_by_email: dict[str, User] = {}

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower())

    async def save(self, user: User) -> None:
        self._users_by_id[user.user_id] = user
        self._users_by_email[user.email.lower()] = user

    async def list_users(self) -> list[User]:
        return list(self._users_by_id.values())

    def clear(self) -> None:
        """Reset storage for testing."""
        self._users_by_id.clear()
        self._users_by_email.clear()


class InMemoryAPIKeyRepository(IAPIKeyRepository):
    """In-memory API Key storage."""

    def __init__(self) -> None:
        self._keys_by_id: dict[str, APIKey] = {}
        self._keys_by_hash: dict[str, APIKey] = {}

    async def get_by_id(self, key_id: str) -> APIKey | None:
        return self._keys_by_id.get(key_id)

    async def get_by_hashed_key(self, hashed_key: str) -> APIKey | None:
        return self._keys_by_hash.get(hashed_key)

    async def save(self, api_key: APIKey) -> None:
        self._keys_by_id[api_key.key_id] = api_key
        self._keys_by_hash[api_key.hashed_key] = api_key

    async def list_by_user(self, user_id: str) -> list[APIKey]:
        return [k for k in self._keys_by_id.values() if k.user_id == user_id and k.is_active]

    async def revoke(self, key_id: str) -> bool:
        key = self._keys_by_id.get(key_id)
        if key:
            key.is_active = False
            return True
        return False

    def clear(self) -> None:
        """Reset storage for testing."""
        self._keys_by_id.clear()
        self._keys_by_hash.clear()


class InMemoryCredentialVaultRepository(ICredentialVaultRepository):
    """In-memory Encrypted Broker Credential storage."""

    def __init__(self) -> None:
        # Key: (user_id, broker_id) -> BrokerCredentialVaultItem
        self._vault: dict[tuple[str, str], BrokerCredentialVaultItem] = {}

    async def get_credential(self, user_id: str, broker_id: str) -> BrokerCredentialVaultItem | None:
        return self._vault.get((user_id, broker_id))

    async def save_credential(self, item: BrokerCredentialVaultItem) -> None:
        self._vault[(item.user_id, item.broker_id)] = item

    async def delete_credential(self, user_id: str, broker_id: str) -> bool:
        return self._vault.pop((user_id, broker_id), None) is not None

    async def list_user_credentials(self, user_id: str) -> list[BrokerCredentialVaultItem]:
        return [item for (uid, _), item in self._vault.items() if uid == user_id]

    def clear(self) -> None:
        """Reset storage for testing."""
        self._vault.clear()


# Global in-memory repository singletons
user_repository = InMemoryUserRepository()
api_key_repository = InMemoryAPIKeyRepository()
credential_vault_repository = InMemoryCredentialVaultRepository()
