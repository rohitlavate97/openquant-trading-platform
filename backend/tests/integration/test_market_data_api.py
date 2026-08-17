"""Integration tests for Market Data REST endpoints & Staleness Report."""

import pytest
from httpx import AsyncClient
from openquant.adapters.repositories.in_memory_auth_repo import user_repository


@pytest.fixture(autouse=True)
def clean_repos():
    user_repository.clear()


@pytest.mark.asyncio
async def test_market_data_endpoints_lifecycle(async_client: AsyncClient):
    """Test tick ingestion, latest ticks query, candles query, staleness report, and replay controls."""
    # 1. Register and Login a Super Admin / Trader user
    await async_client.post("/api/v1/auth/register", json={
        "email": "mkt_trader@openquant.internal",
        "password": "TraderSecurePassword123!",
        "full_name": "Quant Trader",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "mkt_trader@openquant.internal",
        "password": "TraderSecurePassword123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest a tick
    tick_payload = {
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "last_price": "188.50",
        "last_quantity": "100",
        "bid_price": "188.45",
        "ask_price": "188.55",
        "volume": "50000",
    }
    res_ingest = await async_client.post("/api/v1/market-data/ticks", json=tick_payload, headers=headers)
    assert res_ingest.status_code == 201
    assert res_ingest.json()["status"] == "success"

    # 3. Get latest ticks
    res_ticks = await async_client.get("/api/v1/market-data/ticks/latest", headers=headers)
    assert res_ticks.status_code == 200
    assert "AAPL" in res_ticks.json()["ticks"]

    # 4. Query candles
    res_candles = await async_client.get("/api/v1/market-data/candles?symbol=AAPL&timeframe=1m", headers=headers)
    assert res_candles.status_code == 200
    assert len(res_candles.json()) >= 1

    # 5. Get staleness report
    res_staleness = await async_client.get("/api/v1/market-data/staleness?max_staleness_ms=3000", headers=headers)
    assert res_staleness.status_code == 200
    assert res_staleness.json()["overall_status"] == "HEALTHY"

    # 6. Start / Stop replay
    res_start = await async_client.post("/api/v1/market-data/replay/start?interval_sec=1.0", headers=headers)
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "started"

    res_stop = await async_client.post("/api/v1/market-data/replay/stop", headers=headers)
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "stopped"
