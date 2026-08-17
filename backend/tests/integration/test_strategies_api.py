"""Integration tests for Strategy Management & Execution Engine REST API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_strategies_api_full_crud_and_lifecycle(async_client: AsyncClient):
    """Test strategy creation, retrieval, updates, start/pause/stop lifecycle via REST endpoints."""
    # 1. Login Quant Dev
    await async_client.post("/api/v1/auth/register", json={
        "email": "quant_trader@openquant.internal",
        "password": "QuantTraderPass123!",
        "full_name": "Quant Trader",
        "role": "QUANT_DEVELOPER",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "quant_trader@openquant.internal",
        "password": "QuantTraderPass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Strategy
    create_res = await async_client.post(
        "/api/v1/strategies",
        json={
            "name": "Live RSI Reversion",
            "description": "RSI mean reversion with 5-period window",
            "source_code": "# RSIMeanReversionStrategy\nrsi = 0\n",
            "symbols": ["TSLA", "AAPL"],
            "parameters": [
                {"name": "period", "param_type": "INT", "default_value": 5, "current_value": 5},
                {"name": "oversold_threshold", "param_type": "FLOAT", "default_value": 30.0, "current_value": 30.0},
            ],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    strat_data = create_res.json()
    strategy_id = strat_data["strategy_id"]
    assert strat_data["name"] == "Live RSI Reversion"
    assert strat_data["state"] == "INITIALIZED"

    # 3. List Strategies
    list_res = await async_client.get("/api/v1/strategies", headers=headers)
    assert list_res.status_code == 200
    assert any(s["strategy_id"] == strategy_id for s in list_res.json())

    # 4. Get Strategy Details
    get_res = await async_client.get(f"/api/v1/strategies/{strategy_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["strategy_id"] == strategy_id

    # 5. Start Strategy
    start_res = await async_client.post(f"/api/v1/strategies/{strategy_id}/start", headers=headers)
    assert start_res.status_code == 200
    assert start_res.json()["state"] == "RUNNING"

    # 6. Pause Strategy
    pause_res = await async_client.post(f"/api/v1/strategies/{strategy_id}/pause", headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["state"] == "PAUSED"

    # 7. Stop Strategy
    stop_res = await async_client.post(f"/api/v1/strategies/{strategy_id}/stop", headers=headers)
    assert stop_res.status_code == 200
    assert stop_res.json()["state"] == "STOPPED"

    # 8. Check Runtime Logs
    logs_res = await async_client.get(f"/api/v1/strategies/{strategy_id}/logs", headers=headers)
    assert logs_res.status_code == 200
    assert "logs" in logs_res.json()


@pytest.mark.asyncio
async def test_strategies_api_rejects_unsafe_code_submission(async_client: AsyncClient):
    """Verify endpoint returns 400 when submitting code with malicious AST."""
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "quant_trader@openquant.internal",
        "password": "QuantTraderPass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await async_client.post(
        "/api/v1/strategies",
        json={
            "name": "Malicious Strategy",
            "source_code": "import os\nos.system('whoami')",
            "symbols": ["AAPL"],
        },
        headers=headers,
    )
    assert create_res.status_code == 400
    assert "AST security validation" in create_res.json()["detail"]
