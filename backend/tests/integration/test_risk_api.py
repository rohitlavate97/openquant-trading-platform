"""Integration tests for Risk Engine and Kill Switch endpoints."""

import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.market_data import Tick
from openquant.application.services.market_data_service import market_data_service
from openquant.adapters.repositories.in_memory_auth_repo import user_repository
from openquant.application.services.risk_service import risk_service


@pytest.fixture(autouse=True)
async def clean_risk_test_state():
    user_repository.clear()
    await risk_service.deactivate_kill_switch()
    yield
    await risk_service.deactivate_kill_switch()


@pytest.mark.asyncio
async def test_risk_api_lifecycle_and_kill_switch_intervention(async_client: AsyncClient):
    """Test full Risk API flow: query config, dry-run check, activate kill switch, verify order placement is rejected."""
    # 1. Register & Login Super Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "risk_admin@openquant.internal",
        "password": "RiskSecurePassword123!",
        "full_name": "Risk Officer",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "risk_admin@openquant.internal",
        "password": "RiskSecurePassword123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Query Risk Config
    res_cfg = await async_client.get("/api/v1/risk/config", headers=headers)
    assert res_cfg.status_code == 200
    cfg_data = res_cfg.json()
    assert cfg_data["max_daily_loss_percent"] == 3.0
    assert cfg_data["kill_switch"]["is_active"] is False

    # 3. Feed market data
    await market_data_service.ingest_tick(Tick(
        symbol="MSFT",
        exchange="NASDAQ",
        last_price=Decimal("400.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    # 4. Dry-run pre-trade risk evaluation
    order_payload = {
        "idempotency_key": "risk_api_dry_run_1",
        "strategy_id": "strat_1",
        "account_id": "acc_main",
        "broker_id": "paper_broker",
        "symbol": "MSFT",
        "side": "BUY",
        "order_type": "LIMIT",
        "price": "400.00",
        "quantity": "5",
    }
    res_dry = await async_client.post("/api/v1/risk/evaluate-pre-trade", json=order_payload, headers=headers)
    assert res_dry.status_code == 200
    assert res_dry.json()["allowed"] is True

    # 5. Activate Emergency Kill Switch
    res_ks = await async_client.post("/api/v1/risk/kill-switch/activate", json={
        "level": "GLOBAL",
        "reason": "Flash Crash Warning",
        "flatten_positions": False,
    }, headers=headers)
    assert res_ks.status_code == 200
    assert res_ks.json()["kill_switch"]["is_active"] is True

    # 6. Attempting to place order via /api/v1/orders MUST be rejected by Kill Switch (403 Forbidden)
    res_order = await async_client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert res_order.status_code == 403

    # 7. Deactivate Kill Switch
    res_deact = await async_client.post("/api/v1/risk/kill-switch/deactivate", headers=headers)
    assert res_deact.status_code == 200
    assert res_deact.json()["kill_switch"]["is_active"] is False
