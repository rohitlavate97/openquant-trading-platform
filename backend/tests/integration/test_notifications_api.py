import pytest
from httpx import AsyncClient
from openquant.application.services.risk_service import risk_service


@pytest.mark.asyncio
async def test_notifications_api_endpoints_full_lifecycle(async_client: AsyncClient):
    await risk_service.deactivate_kill_switch()

    # 1. Register & Login as Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "notif_admin@openquant.internal",
        "password": "NotifAdminPass123!",
        "full_name": "Notification Admin",
        "role": "ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "notif_admin@openquant.internal",
        "password": "NotifAdminPass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. GET /api/v1/notifications/channels (Seeds In-App default)
    res_list = await async_client.get("/api/v1/notifications/channels", headers=headers)
    assert res_list.status_code == 200
    channels = res_list.json()
    assert len(channels) >= 1

    # 3. POST /api/v1/notifications/channels (Create Telegram channel)
    create_res = await async_client.post(
        "/api/v1/notifications/channels",
        json={
            "name": "Quant Alert Telegram",
            "channel_type": "TELEGRAM",
            "config": {"bot_token": "mock_token", "chat_id": "123456"},
            "subscribed_severities": ["CRITICAL", "ERROR", "WARNING"],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    created_channel = create_res.json()
    channel_id = created_channel["channel_id"]
    assert created_channel["name"] == "Quant Alert Telegram"

    # 4. POST /api/v1/notifications/channels/{channel_id}/test
    test_res = await async_client.post(
        f"/api/v1/notifications/channels/{channel_id}/test",
        headers=headers,
    )
    assert test_res.status_code == 200
    assert test_res.json()["success"] is True

    # 5. POST /api/v1/notifications/broadcast
    broadcast_res = await async_client.post(
        "/api/v1/notifications/broadcast",
        json={
            "title": "Strategy Margin Alert",
            "content": "Margin buffer approaching 80% limit.",
            "severity": "WARNING",
        },
        headers=headers,
    )
    assert broadcast_res.status_code == 200
    dispatched = broadcast_res.json()
    assert len(dispatched) >= 1

    # 6. GET /api/v1/notifications/logs
    logs_res = await async_client.get("/api/v1/notifications/logs?limit=10", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) >= 1

    # 7. GET /api/v1/notifications/in-app
    in_app_res = await async_client.get("/api/v1/notifications/in-app", headers=headers)
    assert in_app_res.status_code == 200
    in_app_data = in_app_res.json()
    assert in_app_data["unread_count"] >= 1
    notif_id = in_app_data["notifications"][0]["notification_id"]

    # 8. POST /api/v1/notifications/in-app/{notification_id}/read
    read_res = await async_client.post(
        f"/api/v1/notifications/in-app/{notif_id}/read",
        headers=headers,
    )
    assert read_res.status_code == 200
    assert read_res.json()["success"] is True

    # 9. DELETE /api/v1/notifications/channels/{channel_id}
    del_res = await async_client.delete(
        f"/api/v1/notifications/channels/{channel_id}",
        headers=headers,
    )
    assert del_res.status_code == 204
