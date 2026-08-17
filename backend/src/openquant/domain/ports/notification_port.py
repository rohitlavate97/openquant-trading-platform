"""Domain ports for Notification Dispatcher, Channel Repository, and Notification Log Storage."""

from abc import ABC, abstractmethod
from openquant.domain.models.notification import (
    NotificationChannelConfig,
    NotificationChannelType,
    NotificationMessage,
    NotificationSeverity,
    NotificationStatus,
)


class INotificationDispatcher(ABC):
    """Abstract interface for multi-channel message dispatchers (Telegram, Discord, Email, Webhook)."""

    @abstractmethod
    async def dispatch(
        self,
        message: NotificationMessage,
        channel_config: NotificationChannelConfig,
    ) -> NotificationStatus:
        """Deliver a formatted notification payload to a configured channel."""

    @abstractmethod
    async def test_channel(
        self,
        channel_config: NotificationChannelConfig,
    ) -> tuple[bool, str]:
        """Send a test ping message to verify recipient credentials and reachability."""


class INotificationChannelRepository(ABC):
    """Abstract storage interface for alert channel configurations."""

    @abstractmethod
    async def save(self, config: NotificationChannelConfig) -> None:
        """Create or update a channel configuration."""

    @abstractmethod
    async def get_by_id(self, channel_id: str) -> NotificationChannelConfig | None:
        """Fetch channel configuration by ID."""

    @abstractmethod
    async def list_all(self, only_enabled: bool = False) -> list[NotificationChannelConfig]:
        """List all registered channel configurations."""

    @abstractmethod
    async def delete(self, channel_id: str) -> bool:
        """Remove a channel configuration."""


class INotificationLogRepository(ABC):
    """Abstract storage interface for dispatched alerts and in-app notifications."""

    @abstractmethod
    async def save(self, message: NotificationMessage) -> None:
        """Save a dispatched or queued notification record."""

    @abstractmethod
    async def get_by_id(self, notification_id: str) -> NotificationMessage | None:
        """Fetch a notification record by ID."""

    @abstractmethod
    async def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        channel_type: NotificationChannelType | None = None,
        severity: NotificationSeverity | None = None,
    ) -> list[NotificationMessage]:
        """List recent notifications matching criteria."""

    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark an in-app notification as read."""

    @abstractmethod
    async def get_unread_in_app_count(self) -> int:
        """Return the count of unread in-app alerts."""
