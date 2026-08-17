from datetime import datetime, timezone
from decimal import Decimal
import pytest
from httpx import AsyncClient

from openquant.application.services.market_data_service import market_data_service
from openquant.application.services.risk_service import risk_service
from openquant.adapters.repositories.in_memory_oms_repo import position_repository
from openquant.domain.models.market_data import Tick
from openquant.domain.models.position import Position, PositionSide


@pytest.mark.asyncio
async def test_portfolio_api_endpoints_and_close(async_client: AsyncClient):
    await risk_service.deactivate_kill_switch()

    # 1. Register & Login as Admin
    await async_client.post("/api/v1/auth/register", json={
        "email": "portfolio_mgr@openquant.internal",
        "password": "PortfolioPass123!",
        "full_name": "Portfolio Manager",
        "role": "ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "portfolio_mgr@openquant.internal",
        "password": "PortfolioPass123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed a position
    pos = Position(
        position_id="pos_aapl_int_1",
        account_id="acc_main",
        broker_id="paper_broker",
        strategy_id="strat_test",
        symbol="AAPL",
        side=PositionSide.LONG,
        quantity=Decimal("20"),
        entry_price=Decimal("150.00"),
    )
    await position_repository.save(pos)

    # Ingest fresh tick
    await market_data_service.ingest_tick(
        Tick(symbol="AAPL", exchange="NASDAQ", last_price=Decimal("155.00"), timestamp=datetime.now(timezone.utc))
    )

    # 3. GET /api/v1/portfolio/summary
    res_sum = await async_client.get("/api/v1/portfolio/summary?account_id=acc_main", headers=headers)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["account_id"] == "acc_main"
    assert "total_equity" in sum_data

    # 4. GET /api/v1/portfolio/positions
    res_pos = await async_client.get("/api/v1/portfolio/positions?account_id=acc_main", headers=headers)
    assert res_pos.status_code == 200
    pos_data = res_pos.json()
    assert len(pos_data) >= 1

    # 5. GET /api/v1/portfolio/allocation
    res_alloc = await async_client.get("/api/v1/portfolio/allocation?account_id=acc_main", headers=headers)
    assert res_alloc.status_code == 200
    alloc_data = res_alloc.json()
    assert len(alloc_data) >= 2

    # 6. GET /api/v1/portfolio/performance
    res_perf = await async_client.get("/api/v1/portfolio/performance?account_id=acc_main&days=14", headers=headers)
    assert res_perf.status_code == 200
    perf_data = res_perf.json()
    assert len(perf_data) == 15

    # 7. POST /api/v1/portfolio/positions/AAPL/close
    res_close = await async_client.post("/api/v1/portfolio/positions/AAPL/close?account_id=acc_main", headers=headers)
    assert res_close.status_code == 200
    close_data = res_close.json()
    assert close_data["symbol"] == "AAPL"
    assert "order_id" in close_data
