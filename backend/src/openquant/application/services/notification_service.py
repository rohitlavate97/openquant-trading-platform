"""Application service managing notification channels, multi-channel dispatching, and event bus routing."""

from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from openquant.domain.models.notification import (
    NotificationChannelConfig,
    NotificationChannelType,
    NotificationMessage,
    NotificationSeverity,
    NotificationStatus,
    PlatformEvent,
)
from openquant.domain.ports.event_bus import IEventBus
from openquant.domain.ports.notification_port import (
    INotificationChannelRepository,
    INotificationDispatcher,
    INotificationLogRepository,
)
from openquant.adapters.event_bus.in_memory_event_bus import event_bus
from openquant.adapters.repositories.in_memory_notification_repo import (
    notification_channel_repository,
    notification_log_repository,
)
from openquant.adapters.notifications.notification_dispatcher import notification_dispatcher
from openquant.application.services.audit_service import audit_log_service, AuditLogService

logger = logging.getLogger(__name__)


class NotificationService:
    """Coordinates channel management, multi-channel dispatch, in-app storage, and event-driven alerting."""

    def __init__(
        self,
        event_bus_port: IEventBus | None = None,
        dispatcher: INotificationDispatcher | None = None,
        channel_repo: INotificationChannelRepository | None = None,
        log_repo: INotificationLogRepository | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._bus = event_bus_port or event_bus
        self._dispatcher = dispatcher or notification_dispatcher
        self._channels = channel_repo or notification_channel_repository
        self._logs = log_repo or notification_log_repository
        self._audit = audit or audit_log_service
        self._initialized = False

    async def initialize(self) -> None:
        """Seed default In-App channel and register event bus subscriptions."""
        if self._initialized:
            return

        # Ensure default in-app channel exists
        existing = await self._channels.list_all()
        if not any(c.channel_type == NotificationChannelType.IN_APP for c in existing):
            in_app = NotificationChannelConfig(
                channel_id="chn_in_app_system",
                channel_type=NotificationChannelType.IN_APP,
                name="System In-App Notification Center",
                is_enabled=True,
                subscribed_severities=[
                    NotificationSeverity.INFO,
                    NotificationSeverity.WARNING,
                    NotificationSeverity.ERROR,
                    NotificationSeverity.CRITICAL,
                ],
            )
            await self._channels.save(in_app)

        # Subscribe to critical platform events
        await self._bus.subscribe("risk.kill_switch", self._on_kill_switch_event)
        await self._bus.subscribe("risk.breach", self._on_risk_breach_event)
        await self._bus.subscribe("reconciliation.mismatch", self._on_reconciliation_event)
        await self._bus.subscribe("market_data.stale", self._on_market_data_stale_event)
        self._initialized = True

    async def register_channel(
        self,
        name: str,
        channel_type: NotificationChannelType,
        config: dict[str, Any],
        subscribed_severities: list[NotificationSeverity] | None = None,
    ) -> NotificationChannelConfig:
        """Register a new notification channel."""
        severities = subscribed_severities or [
            NotificationSeverity.INFO,
            NotificationSeverity.WARNING,
            NotificationSeverity.ERROR,
            NotificationSeverity.CRITICAL,
        ]
        chn = NotificationChannelConfig(
            channel_type=channel_type,
            name=name,
            config=config,
            subscribed_severities=severities,
        )
        await self._channels.save(chn)
        await self._audit.log_event(
            event_type="NOTIFICATION_CHANNEL_CREATED",
            actor_id="system",
            entity_type="NOTIFICATION_CHANNEL",
            entity_id=chn.channel_id,
            action="CREATE",
            payload={"name": name, "type": channel_type},
        )
        return chn

    async def update_channel(
        self,
        channel_id: str,
        is_enabled: bool | None = None,
        config: dict[str, Any] | None = None,
        subscribed_severities: list[NotificationSeverity] | None = None,
    ) -> NotificationChannelConfig:
        """Update an existing channel configuration."""
        existing = await self._channels.get_by_id(channel_id)
        if not existing:
            raise ValueError(f"Notification channel '{channel_id}' not found.")

        if is_enabled is not None:
            existing.is_enabled = is_enabled
        if config is not None:
            existing.config = config
        if subscribed_severities is not None:
            existing.subscribed_severities = subscribed_severities
        existing.updated_at = datetime.now(timezone.utc)

        await self._channels.save(existing)
        return existing

    async def delete_channel(self, channel_id: str) -> bool:
        """Delete an alert channel."""
        res = await self._channels.delete(channel_id)
        if res:
            await self._audit.log_event(
                event_type="NOTIFICATION_CHANNEL_DELETED",
                actor_id="system",
                entity_type="NOTIFICATION_CHANNEL",
                entity_id=channel_id,
                action="DELETE",
                payload={"channel_id": channel_id},
            )
        return res

    async def list_channels(self, only_enabled: bool = False) -> list[NotificationChannelConfig]:
        """List configured channels."""
        await self.initialize()
        return await self._channels.list_all(only_enabled=only_enabled)

    async def get_channel(self, channel_id: str) -> NotificationChannelConfig | None:
        """Fetch channel configuration by ID."""
        return await self._channels.get_by_id(channel_id)

    async def test_channel(self, channel_id: str) -> tuple[bool, str]:
        """Trigger an automated ping test message to verify connectivity."""
        chn = await self._channels.get_by_id(channel_id)
        if not chn:
            raise ValueError(f"Notification channel '{channel_id}' not found.")
        return await self._dispatcher.test_channel(chn)

    async def broadcast_alert(
        self,
        title: str,
        content: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        target_channel_type: NotificationChannelType | None = None,
        metadata: dict[str, Any] | None = None,
        actor_id: str = "system",
    ) -> list[NotificationMessage]:
        """Broadcast an alert across all eligible configured notification channels."""
        await self.initialize()
        channels = await self._channels.list_all(only_enabled=True)
        meta = metadata or {}
        dispatched_messages: list[NotificationMessage] = []

        for chn in channels:
            if target_channel_type and chn.channel_type != target_channel_type:
                continue

            if severity not in chn.subscribed_severities:
                continue

            msg = NotificationMessage(
                channel_type=chn.channel_type,
                severity=severity,
                title=title,
                content=content,
                metadata=meta,
            )
            await self._dispatcher.dispatch(msg, chn)
            await self._logs.save(msg)
            dispatched_messages.append(msg)

        return dispatched_messages

    async def list_notification_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        channel_type: NotificationChannelType | None = None,
        severity: NotificationSeverity | None = None,
    ) -> list[NotificationMessage]:
        """List recently dispatched alerts."""
        return await self._logs.list_recent(
            limit=limit,
            offset=offset,
            channel_type=channel_type,
            severity=severity,
        )

    async def list_in_app_notifications(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NotificationMessage]:
        """List recent in-app notifications."""
        return await self._logs.list_recent(
            limit=limit,
            offset=offset,
            channel_type=NotificationChannelType.IN_APP,
        )

    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark an in-app alert as read."""
        return await self._logs.mark_as_read(notification_id)

    async def get_unread_in_app_count(self) -> int:
        """Get the count of unread in-app alerts."""
        return await self._logs.get_unread_in_app_count()

    async def handle_platform_event(self, event: PlatformEvent) -> list[NotificationMessage]:
        """Dispatch notifications corresponding to a platform event."""
        title = f"Platform Event: {event.event_type}"
        content = f"Event from source '{event.source}' at {event.timestamp.isoformat()}.\nDetails: {event.payload}"
        return await self.broadcast_alert(
            title=title,
            content=content,
            severity=event.severity,
            metadata={"event_id": event.event_id, "event_type": event.event_type, **event.payload},
        )

    # Event bus callbacks
    async def _on_kill_switch_event(self, data: dict[str, Any]) -> None:
        await self.broadcast_alert(
            title="GLOBAL KILL SWITCH ENGAGED",
            content=f"Global Kill Switch activated by {data.get('actor_id', 'system')}. Reason: {data.get('reason', 'N/A')}",
            severity=NotificationSeverity.CRITICAL,
            metadata=data,
        )

    async def _on_risk_breach_event(self, data: dict[str, Any]) -> None:
        await self.broadcast_alert(
            title="Pre-Trade Risk Engine Hard Stop",
            content=f"Order rejected due to risk violation: {data.get('reason', 'Risk rule triggered')}",
            severity=NotificationSeverity.ERROR,
            metadata=data,
        )

    async def _on_reconciliation_event(self, data: dict[str, Any]) -> None:
        await self.broadcast_alert(
            title="Broker State Reconciliation Mismatch Detected",
            content=f"Reconciliation check identified discrepancy on account {data.get('account_id', 'unknown')}.",
            severity=NotificationSeverity.CRITICAL,
            metadata=data,
        )

    async def _on_market_data_stale_event(self, data: dict[str, Any]) -> None:
        await self.broadcast_alert(
            title="Market Feed Staleness Alert",
            content=f"Market data stream for {data.get('symbol', 'unknown')} exceeded 3000ms threshold (Rule 7).",
            severity=NotificationSeverity.WARNING,
            metadata=data,
        )


# Global notification service singleton
notification_service = NotificationService()
