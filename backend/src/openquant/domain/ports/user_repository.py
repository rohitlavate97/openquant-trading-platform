"""Hexagonal Ports: User, API Key, and Secrets Vault repository interfaces."""

from abc import ABC, abstractmethod
from openquant.domain.models.auth import User, APIKey, BrokerCredentialVaultItem


class IUserRepository(ABC):
    """Abstract interface for user persistence."""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        """Fetch user by unique user ID."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Insert or update user record."""

    @abstractmethod
    async def list_users(self) -> list[User]:
        """Fetch all user records."""


class IAPIKeyRepository(ABC):
    """Abstract interface for API key persistence."""

    @abstractmethod
    async def get_by_id(self, key_id: str) -> APIKey | None:
        """Fetch API key record by ID."""

    @abstractmethod
    async def get_by_hashed_key(self, hashed_key: str) -> APIKey | None:
        """Fetch API key by its SHA-256 hash."""

    @abstractmethod
    async def save(self, api_key: APIKey) -> None:
        """Insert or update API key."""

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[APIKey]:
        """Fetch all API keys for a specific user."""

    @abstractmethod
    async def revoke(self, key_id: str) -> bool:
        """Mark API key as inactive/revoked."""


class ICredentialVaultRepository(ABC):
    """Abstract interface for storing encrypted broker credential items."""

    @abstractmethod
    async def get_credential(self, user_id: str, broker_id: str) -> BrokerCredentialVaultItem | None:
        """Fetch encrypted credential for a user and broker."""

    @abstractmethod
    async def save_credential(self, item: BrokerCredentialVaultItem) -> None:
        """Insert or update encrypted credential record."""

    @abstractmethod
    async def delete_credential(self, user_id: str, broker_id: str) -> bool:
        """Delete stored encrypted credential for a broker."""

    @abstractmethod
    async def list_user_credentials(self, user_id: str) -> list[BrokerCredentialVaultItem]:
        """List all encrypted credential items owned by a user."""
