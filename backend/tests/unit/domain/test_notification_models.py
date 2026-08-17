from openquant.domain.models.notification import (
    NotificationChannelConfig,
    NotificationChannelType,
    NotificationMessage,
    NotificationSeverity,
    NotificationStatus,
    PlatformEvent,
)


def test_notification_models_and_enums():
    chn = NotificationChannelConfig(
        channel_type=NotificationChannelType.TELEGRAM,
        name="Quant Ops Telegram",
        config={"bot_token": "mock_token", "chat_id": "12345"},
        subscribed_severities=[NotificationSeverity.CRITICAL, NotificationSeverity.ERROR],
    )
    assert chn.channel_type == NotificationChannelType.TELEGRAM
    assert NotificationSeverity.CRITICAL in chn.subscribed_severities
    assert chn.is_enabled is True

    msg = NotificationMessage(
        channel_type=NotificationChannelType.DISCORD,
        severity=NotificationSeverity.WARNING,
        title="Margin Warning",
        content="Margin utilization at 82%",
    )
    assert msg.status == NotificationStatus.PENDING
    assert msg.severity == NotificationSeverity.WARNING
    assert msg.is_read is False

    evt = PlatformEvent(
        event_type="KILL_SWITCH_TRIGGERED",
        severity=NotificationSeverity.CRITICAL,
        source="RiskEngine",
        payload={"actor_id": "admin", "reason": "Max Drawdown Breached"},
    )
    assert evt.event_type == "KILL_SWITCH_TRIGGERED"
    assert evt.severity == NotificationSeverity.CRITICAL
