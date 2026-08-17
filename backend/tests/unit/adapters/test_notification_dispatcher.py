import pytest
from openquant.adapters.notifications.notification_dispatcher import NotificationDispatcher
from openquant.domain.models.notification import (
    NotificationChannelConfig,
    NotificationChannelType,
    NotificationMessage,
    NotificationSeverity,
    NotificationStatus,
)


@pytest.mark.asyncio
async def test_notification_dispatcher_channels_and_test_ping():
    dispatcher = NotificationDispatcher()

    # 1. In-App channel
    in_app_chn = NotificationChannelConfig(
        channel_type=NotificationChannelType.IN_APP,
        name="In App Channel",
    )
    msg_in_app = NotificationMessage(
        channel_type=NotificationChannelType.IN_APP,
        severity=NotificationSeverity.INFO,
        title="Info Alert",
        content="System operational",
    )
    status = await dispatcher.dispatch(msg_in_app, in_app_chn)
    assert status == NotificationStatus.DELIVERED
    assert msg_in_app.status == NotificationStatus.DELIVERED

    # 2. Telegram test channel
    tg_chn = NotificationChannelConfig(
        channel_type=NotificationChannelType.TELEGRAM,
        name="Telegram Test",
        config={"bot_token": "mock_token_123", "chat_id": "999"},
    )
    msg_tg = NotificationMessage(
        channel_type=NotificationChannelType.TELEGRAM,
        severity=NotificationSeverity.CRITICAL,
        title="Critical Stop",
        content="Kill Switch Active",
    )
    status_tg = await dispatcher.dispatch(msg_tg, tg_chn)
    assert status_tg == NotificationStatus.DELIVERED

    # 3. Discord test channel
    dc_chn = NotificationChannelConfig(
        channel_type=NotificationChannelType.DISCORD,
        name="Discord Test",
        config={"webhook_url": "https://discord.mock/webhook/123"},
    )
    msg_dc = NotificationMessage(
        channel_type=NotificationChannelType.DISCORD,
        severity=NotificationSeverity.ERROR,
        title="Risk Breach",
        content="Daily loss cap exceeded",
    )
    status_dc = await dispatcher.dispatch(msg_dc, dc_chn)
    assert status_dc == NotificationStatus.DELIVERED

    # 4. Webhook test channel
    wh_chn = NotificationChannelConfig(
        channel_type=NotificationChannelType.WEBHOOK,
        name="Custom Webhook Test",
        config={"endpoint_url": "https://webhook.mock/alerts"},
    )
    msg_wh = NotificationMessage(
        channel_type=NotificationChannelType.WEBHOOK,
        severity=NotificationSeverity.WARNING,
        title="Warning Alert",
        content="Market staleness threshold breached",
    )
    status_wh = await dispatcher.dispatch(msg_wh, wh_chn)
    assert status_wh == NotificationStatus.DELIVERED

    # 5. Email test channel
    em_chn = NotificationChannelConfig(
        channel_type=NotificationChannelType.EMAIL,
        name="Email Ops",
        config={"recipient_email": "ops@openquant.internal"},
    )
    msg_em = NotificationMessage(
        channel_type=NotificationChannelType.EMAIL,
        severity=NotificationSeverity.INFO,
        title="Daily Report",
        content="Daily trading summary",
    )
    status_em = await dispatcher.dispatch(msg_em, em_chn)
    assert status_em == NotificationStatus.DELIVERED

    # 6. Test ping
    ok, test_feedback = await dispatcher.test_channel(tg_chn)
    assert ok is True
    assert "Successfully" in test_feedback
