"""Integration tests for Live Trading Mode REST API."""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from openquant.application.services.strategy_service import strategy_service
from openquant.domain.models.promotion import StrategyPromotionStage


@pytest.mark.asyncio
async def test_live_trading_api_endpoints_lifecycle(async_client: AsyncClient):
    """Verify preflight check, session activation, scaling, and emergency halting via API."""
    # 1. Register & Login Super Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "live.trader@openquant.org",
        "password": "LiveTraderAdmin123!",
        "full_name": "Live Trader Admin",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "live.trader@openquant.org",
        "password": "LiveTraderAdmin123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Strategy & set to Stage 4 (LIVE_TRADING)
    strat_res = await async_client.post(
        "/api/v1/strategies",
        json={
            "name": "Live Production Strategy",
            "description": "Production Alpha",
            "source_code": "fast_sma = 0\nslow_sma = 10",
        },
        headers=headers,
    )
    assert strat_res.status_code == 201
    strategy_id = strat_res.json()["strategy_id"]

    # Promote strategy to Stage 4 (LIVE_TRADING)
    strat_obj = await strategy_service.get_strategy(strategy_id)
    assert strat_obj is not None
    strat_obj.promotion_stage = StrategyPromotionStage.LIVE_TRADING

    # 3. Run Preflight Check
    preflight_res = await async_client.post(
        "/api/v1/live-trading/preflight",
        json={
            "strategy_id": strategy_id,
            "broker_id": "paper_broker",
            "account_id": "acc_live_test",
        },
        headers=headers,
    )
    assert preflight_res.status_code == 200
    preflight = preflight_res.json()
    assert preflight["is_eligible"] is True
    assert len(preflight["checks"]) == 5

    # 4. Activate Live Strategy Session
    activate_res = await async_client.post(
        "/api/v1/live-trading/sessions",
        json={
            "strategy_id": strategy_id,
            "broker_id": "paper_broker",
            "account_id": "acc_live_test",
            "allocation": {
                "strategy_id": strategy_id,
                "broker_id": "paper_broker",
                "account_id": "acc_live_test",
                "total_authorized_capital": "100000.00",
                "scaling_tier": "TIER_1_STARTER",
                "max_order_notional": "10000.00",
                "margin_floor_buffer": "15000.00",
                "max_daily_loss": "3000.00",
                "max_drawdown_percent": "5.00",
            },
            "confirmed_by": "secondary_risk_officer",
        },
        headers=headers,
    )
    assert activate_res.status_code == 201
    session = activate_res.json()
    assert session["state"] == "ACTIVE"
    session_id = session["session_id"]

    # 5. List sessions
    list_res = await async_client.get("/api/v1/live-trading/sessions", headers=headers)
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert len(sessions) >= 1

    # 6. Adjust Scaling Tier to 50%
    scale_res = await async_client.post(
        f"/api/v1/live-trading/sessions/{session_id}/scale",
        json={"scaling_tier": "TIER_2_INTERMEDIATE"},
        headers=headers,
    )
    assert scale_res.status_code == 200
    assert scale_res.json()["allocation"]["scaling_tier"] == "TIER_2_INTERMEDIATE"

    # 7. Halt session
    halt_res = await async_client.post(
        f"/api/v1/live-trading/sessions/{session_id}/halt",
        json={"reason": "Scheduled maintenance shutdown"},
        headers=headers,
    )
    assert halt_res.status_code == 200
    assert halt_res.json()["state"] == "HALTED"
