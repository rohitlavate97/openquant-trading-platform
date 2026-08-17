import pytest
from openquant.application.services.notification_service import NotificationService
from openquant.adapters.event_bus.in_memory_event_bus import InMemoryEventBus
from openquant.adapters.notifications.notification_dispatcher import NotificationDispatcher
from openquant.adapters.repositories.in_memory_notification_repo import (
    InMemoryNotificationChannelRepository,
    InMemoryNotificationLogRepository,
)
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.application.services.audit_service import AuditLogService
from openquant.domain.models.notification import (
    NotificationChannelType,
    NotificationSeverity,
    PlatformEvent,
)


@pytest.fixture
def notification_service_setup():
    bus = InMemoryEventBus()
    dispatcher = NotificationDispatcher()
    channel_repo = InMemoryNotificationChannelRepository()
    log_repo = InMemoryNotificationLogRepository()
    audit_repo = InMemoryAuditLogRepository()
    audit_svc = AuditLogService(audit_repo=audit_repo)

    service = NotificationService(
        event_bus_port=bus,
        dispatcher=dispatcher,
        channel_repo=channel_repo,
        log_repo=log_repo,
        audit=audit_svc,
    )
    return service, bus, channel_repo, log_repo


@pytest.mark.asyncio
async def test_notification_service_channel_crud_and_broadcast(notification_service_setup):
    service, bus, channel_repo, log_repo = notification_service_setup

    # Register Discord channel
    chn = await service.register_channel(
        name="Quant Discord Alerts",
        channel_type=NotificationChannelType.DISCORD,
        config={"webhook_url": "https://discord.mock/alerts"},
        subscribed_severities=[NotificationSeverity.CRITICAL, NotificationSeverity.ERROR],
    )
    assert chn.name == "Quant Discord Alerts"

    channels = await service.list_channels()
    assert len(channels) >= 2  # In-App + Discord

    # Test channel
    ok, msg = await service.test_channel(chn.channel_id)
    assert ok is True

    # Broadcast Critical Alert
    dispatched = await service.broadcast_alert(
        title="EMERGENCY HALT",
        content="Drawdown threshold breached",
        severity=NotificationSeverity.CRITICAL,
    )
    assert len(dispatched) >= 2  # Delivered to In-App + Discord

    # Unread in-app count
    unread_count = await service.get_unread_in_app_count()
    assert unread_count >= 1

    in_app_list = await service.list_in_app_notifications()
    assert len(in_app_list) >= 1
    first_notif = in_app_list[0]

    # Mark as read
    marked = await service.mark_notification_read(first_notif.notification_id)
    assert marked is True
    assert await service.get_unread_in_app_count() == unread_count - 1

    # Test event bus integration
    await bus.publish("risk.kill_switch", {"actor_id": "admin", "reason": "Self-trade detected"})
    logs = await service.list_notification_logs(limit=10)
    assert any("GLOBAL KILL SWITCH ENGAGED" in l.title for l in logs)

    # Delete channel
    deleted = await service.delete_channel(chn.channel_id)
    assert deleted is True
