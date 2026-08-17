"""Integration tests for Paper Trading and Stage 5 Promotion Gate Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_paper_trading_api_endpoints(async_client: AsyncClient):
    """Test full Paper Trading API workflow: create account, launch session, pause, stop, gate-status, promote."""
    # 1. Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "paper_trader@openquant.internal",
        "password": "PaperSecurePass123!",
        "full_name": "Paper Trader",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "paper_trader@openquant.internal",
        "password": "PaperSecurePass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Paper Account
    acc_res = await async_client.post(
        "/api/v1/paper-trading/accounts",
        json={"name": "Alpha Prop Paper Account", "initial_balance": 200000.0},
        headers=headers,
    )
    assert acc_res.status_code == 201
    account_id = acc_res.json()["account_id"]

    # 3. Create Strategy
    strat_res = await async_client.post(
        "/api/v1/strategies",
        json={
            "name": "Paper Alpha Strategy",
            "source_code": "# EMAMomentumStrategy\nfast_sma = 0",
            "symbols": ["AAPL"],
        },
        headers=headers,
    )
    assert strat_res.status_code == 201
    strategy_id = strat_res.json()["strategy_id"]

    # 4. Start Paper Trading Session
    sess_res = await async_client.post(
        "/api/v1/paper-trading/sessions",
        json={
            "strategy_id": strategy_id,
            "account_id": account_id,
            "symbols": ["AAPL"],
            "config": {"latency_ms": 50, "slippage_bps": 1.5},
        },
        headers=headers,
    )
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]
    assert sess_res.json()["status"] == "ACTIVE"

    # 5. List Sessions
    list_res = await async_client.get("/api/v1/paper-trading/sessions", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 6. Check Gate Status
    gate_res = await async_client.get(f"/api/v1/paper-trading/sessions/{session_id}/gate-status", headers=headers)
    assert gate_res.status_code == 200
    assert "eligible_for_promotion" in gate_res.json()

    # 7. Promote with Bypass
    promote_res = await async_client.post(
        f"/api/v1/paper-trading/sessions/{session_id}/promote",
        json={"bypass_criteria": True},
        headers=headers,
    )
    assert promote_res.status_code == 200
    assert promote_res.json()["target_stage"] == "HUMAN_APPROVAL"

    # 8. Pause and Stop Session
    pause_res = await async_client.post(f"/api/v1/paper-trading/sessions/{session_id}/pause", headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    stop_res = await async_client.post(f"/api/v1/paper-trading/sessions/{session_id}/stop", headers=headers)
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "STOPPED"
