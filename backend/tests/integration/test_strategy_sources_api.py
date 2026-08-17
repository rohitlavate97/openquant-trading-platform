"""Integration tests for Strategy Sources REST endpoints."""

import time
import hmac
import hashlib
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from openquant.domain.models.market_data import Tick
from openquant.application.services.market_data_service import market_data_service


@pytest.mark.asyncio
async def test_tradingview_webhook_endpoint_success_and_failure(async_client: AsyncClient):
    # Ingest fresh tick so 3000ms staleness guard passes
    await market_data_service.ingest_tick(
        Tick(symbol="AAPL", exchange="NASDAQ", last_price=Decimal("150.00"), timestamp=datetime.now(timezone.utc))
    )

    now = int(time.time())
    secret = "openquant_tv_secret_key"
    nonce = f"nonce_api_{now}"
    msg = f"strat_tv_api:AAPL:BUY:10.0:{nonce}:{now}"
    sig = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

    payload = {
        "strategy_id": "strat_tv_api",
        "account_id": "acc_main",
        "ticker": "AAPL",
        "action": "BUY",
        "contracts": "10.0",
        "nonce": nonce,
        "timestamp": now,
        "signature": sig,
    }

    # Successful webhook
    res = await async_client.post("/api/v1/sources/tradingview/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["order_id"] is not None

    # Duplicate nonce replay fails
    res_replay = await async_client.post("/api/v1/sources/tradingview/webhook", json=payload)
    assert res_replay.status_code == 400


@pytest.mark.asyncio
async def test_mt5_and_sheets_endpoints(async_client: AsyncClient):
    # Ingest fresh tick for NVDA
    await market_data_service.ingest_tick(
        Tick(symbol="NVDA", exchange="NASDAQ", last_price=Decimal("120.00"), timestamp=datetime.now(timezone.utc))
    )
    # 1. Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "sources_admin@openquant.internal",
        "password": "SourcesSecurePass123!",
        "full_name": "Sources Admin",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "sources_admin@openquant.internal",
        "password": "SourcesSecurePass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. MT5 Status
    res = await async_client.get("/api/v1/sources/mt5/status", headers=headers)
    assert res.status_code == 200

    # 3. MT5 Command dispatch
    cmd_payload = {
        "command_id": "cmd_api_1",
        "action": "BUY",
        "symbol": "USDJPY",
        "volume": "0.5",
    }
    res_cmd = await async_client.post("/api/v1/sources/mt5/command", json=cmd_payload, headers=headers)
    assert res_cmd.status_code == 200

    # 4. Sheets Parse
    csv_content = """Timestamp,Symbol,Signal_Type,Quantity,Limit_Price
2026-08-17T10:00:00Z,NVDA,BUY,20,120.00
"""
    res_parse = await async_client.post("/api/v1/sources/sheets/parse", json={"csv_content": csv_content}, headers=headers)
    assert res_parse.status_code == 200
    parse_data = res_parse.json()
    assert parse_data["valid_rows_count"] == 1

    # 5. Sheets Execute Batch
    res_exec = await async_client.post(
        "/api/v1/sources/sheets/execute",
        json={"account_id": "acc_main", "orders": parse_data["parsed_orders"]},
        headers=headers,
    )
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["status"] == "success"
    assert exec_data["executed_count"] == 1
