"""In-memory repository implementations for User, API Key, and Secrets Vault."""

from datetime import datetime, timezone
from openquant.domain.models.auth import User, APIKey, BrokerCredentialVaultItem
from openquant.domain.ports.user_repository import (
    IUserRepository,
    IAPIKeyRepository,
    ICredentialVaultRepository,
)
from openquant.domain.ports.repositories import IAuditLogRepository


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


class InMemoryAuditLogRepository(IAuditLogRepository):
    """In-memory append-only Audit Log storage."""

    def __init__(self) -> None:
        self._logs: list[dict] = []

    async def record_event(
        self,
        event_type: str,
        actor_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
        severity: str = "INFO",
        client_ip: str | None = None,
        status: str = "SUCCESS",
        reason: str | None = None,
    ) -> str:
        log_id = f"aud_{len(self._logs) + 1}_{event_type.lower()}"
        entry = {
            "log_id": log_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "severity": severity,
            "actor_id": actor_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "payload": payload,
            "client_ip": client_ip,
            "status": status,
            "reason": reason,
        }
        self._logs.append(entry)
        return log_id

    async def list_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: str | None = None,
        actor_id: str | None = None,
        severity: str | None = None,
    ) -> list[dict]:
        results = list(reversed(self._logs))
        if event_type:
            results = [l for l in results if l["event_type"] == event_type]
        if actor_id:
            results = [l for l in results if l["actor_id"] == actor_id]
        if severity:
            results = [l for l in results if l["severity"] == severity]
        return results[offset : offset + limit]

    def clear(self) -> None:
        self._logs.clear()


# Global in-memory repository singletons
user_repository = InMemoryUserRepository()
api_key_repository = InMemoryAPIKeyRepository()
credential_vault_repository = InMemoryCredentialVaultRepository()
audit_log_repository = InMemoryAuditLogRepository()
