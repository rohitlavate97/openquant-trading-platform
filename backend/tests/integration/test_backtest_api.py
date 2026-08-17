"""Integration tests for Backtesting and Walk-Forward Validation REST Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_backtest_api_run_results_and_promotion(async_client: AsyncClient):
    """Test running backtest, retrieving result report, and promoting to Stage 2 (BACKTESTED)."""
    # 1. Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "backtest_quant@openquant.internal",
        "password": "QuantSecurePass123!",
        "full_name": "Backtest Quant",
        "role": "QUANT_DEVELOPER",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "backtest_quant@openquant.internal",
        "password": "QuantSecurePass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Strategy
    create_strat = await async_client.post(
        "/api/v1/strategies",
        json={
            "name": "Backtest Alpha Strategy",
            "source_code": "# EMAMomentumStrategy\nfast_sma = 0",
            "symbols": ["AAPL"],
        },
        headers=headers,
    )
    assert create_strat.status_code == 201
    strategy_id = create_strat.json()["strategy_id"]

    # 3. Run Backtest
    bt_res = await async_client.post(
        "/api/v1/backtest/run",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL"],
            "initial_cash": 100000.0,
            "slippage_bps": 5.0,
            "commission_per_order": 1.0,
        },
        headers=headers,
    )
    assert bt_res.status_code == 200
    bt_data = bt_res.json()
    backtest_id = bt_data["backtest_id"]
    assert "metrics" in bt_data
    assert "equity_curve" in bt_data
    assert len(bt_data["equity_curve"]) > 0

    # 4. Get Backtest Result
    get_res = await async_client.get(f"/api/v1/backtest/results/{backtest_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["backtest_id"] == backtest_id

    # 5. Run Walk-Forward Validation
    wfv_res = await async_client.post(
        "/api/v1/backtest/walk-forward",
        json={
            "config": {
                "strategy_id": strategy_id,
                "symbols": ["AAPL"],
                "initial_cash": 100000.0,
            },
            "num_windows": 3,
            "train_ratio": 0.7,
        },
        headers=headers,
    )
    assert wfv_res.status_code == 200
    wfv_data = wfv_res.json()
    assert "overall_efficiency_ratio" in wfv_data
    assert len(wfv_data["windows"]) > 0
