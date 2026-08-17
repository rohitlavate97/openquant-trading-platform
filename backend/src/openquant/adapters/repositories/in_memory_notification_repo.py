"""In-memory thread-safe repositories for alert channel configurations and notification logs."""

import asyncio
from openquant.domain.models.notification import (
    NotificationChannelConfig,
    NotificationChannelType,
    NotificationMessage,
    NotificationSeverity,
)
from openquant.domain.ports.notification_port import (
    INotificationChannelRepository,
    INotificationLogRepository,
)


class InMemoryNotificationChannelRepository(INotificationChannelRepository):
    """In-memory storage for notification channel configurations."""

    def __init__(self) -> None:
        self._channels: dict[str, NotificationChannelConfig] = {}
        self._lock = asyncio.Lock()

    async def save(self, config: NotificationChannelConfig) -> None:
        async with self._lock:
            self._channels[config.channel_id] = config

    async def get_by_id(self, channel_id: str) -> NotificationChannelConfig | None:
        async with self._lock:
            return self._channels.get(channel_id)

    async def list_all(self, only_enabled: bool = False) -> list[NotificationChannelConfig]:
        async with self._lock:
            channels = list(self._channels.values())
            if only_enabled:
                return [c for c in channels if c.is_enabled]
            return channels

    async def delete(self, channel_id: str) -> bool:
        async with self._lock:
            if channel_id in self._channels:
                del self._channels[channel_id]
                return True
            return False

    def clear(self) -> None:
        self._channels.clear()


class InMemoryNotificationLogRepository(INotificationLogRepository):
    """In-memory ring buffer storage for dispatched notification history and in-app alerts."""

    def __init__(self, max_capacity: int = 1000) -> None:
        self._logs: list[NotificationMessage] = []
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def save(self, message: NotificationMessage) -> None:
        async with self._lock:
            # Check if updating existing
            for idx, item in enumerate(self._logs):
                if item.notification_id == message.notification_id:
                    self._logs[idx] = message
                    return
            self._logs.insert(0, message)
            if len(self._logs) > self._max_capacity:
                self._logs = self._logs[: self._max_capacity]

    async def get_by_id(self, notification_id: str) -> NotificationMessage | None:
        async with self._lock:
            return next((m for m in self._logs if m.notification_id == notification_id), None)

    async def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        channel_type: NotificationChannelType | None = None,
        severity: NotificationSeverity | None = None,
    ) -> list[NotificationMessage]:
        async with self._lock:
            filtered = self._logs
            if channel_type:
                filtered = [m for m in filtered if m.channel_type == channel_type]
            if severity:
                filtered = [m for m in filtered if m.severity == severity]
            return filtered[offset : offset + limit]

    async def mark_as_read(self, notification_id: str) -> bool:
        async with self._lock:
            for item in self._logs:
                if item.notification_id == notification_id:
                    item.is_read = True
                    return True
            return False

    async def get_unread_in_app_count(self) -> int:
        async with self._lock:
            return sum(
                1
                for m in self._logs
                if m.channel_type == NotificationChannelType.IN_APP and not m.is_read
            )

    def clear(self) -> None:
        self._logs.clear()


# Global repository singletons
notification_channel_repository = InMemoryNotificationChannelRepository()
notification_log_repository = InMemoryNotificationLogRepository()
