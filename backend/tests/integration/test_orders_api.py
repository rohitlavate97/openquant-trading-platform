"""Integration tests for OMS Order placement, listing, cancellation, positions, and reconciliation."""

import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.market_data import Tick
from openquant.application.services.market_data_service import market_data_service
from openquant.adapters.repositories.in_memory_auth_repo import user_repository
from openquant.adapters.repositories.in_memory_oms_repo import order_repository, position_repository


@pytest.fixture(autouse=True)
def clean_oms_repos():
    user_repository.clear()
    order_repository.clear()
    position_repository.clear()


@pytest.mark.asyncio
async def test_orders_api_crud_and_reconciliation_lifecycle(async_client: AsyncClient):
    """Test full API order lifecycle: submit, idempotent resubmit, list, positions, and reconcile."""
    # 1. Register & Login Trader
    await async_client.post("/api/v1/auth/register", json={
        "email": "oms_trader@openquant.internal",
        "password": "OMSSecurePassword123!",
        "full_name": "OMS Trader",
        "role": "SUPER_ADMIN",
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "oms_trader@openquant.internal",
        "password": "OMSSecurePassword123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Feed market data so staleness guard allows order placement
    await market_data_service.ingest_tick(Tick(
        symbol="AAPL",
        exchange="NASDAQ",
        last_price=Decimal("185.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    # 3. Submit Order
    order_payload = {
        "idempotency_key": "api_idemp_key_100",
        "strategy_id": "strat_alpha_1",
        "account_id": "acc_main",
        "broker_id": "paper_broker",
        "symbol": "AAPL",
        "side": "BUY",
        "order_type": "LIMIT",
        "price": "185.00",
        "quantity": "25",
    }
    res_post = await async_client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert res_post.status_code == 201
    order_data = res_post.json()["order"]
    order_id = order_data["order_id"]
    assert order_data["symbol"] == "AAPL"
    assert order_data["quantity"] == "25"

    # 4. Resubmit identical order with same idempotency key -> returns existing order
    res_repost = await async_client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert res_repost.status_code == 201
    assert res_repost.json()["order"]["order_id"] == order_id

    # 5. List orders
    res_list = await async_client.get("/api/v1/orders", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 6. Get order by ID
    res_get = await async_client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["order_id"] == order_id

    # 7. Get positions
    res_pos = await async_client.get("/api/v1/positions?account_id=acc_main", headers=headers)
    assert res_pos.status_code == 200
    assert len(res_pos.json()) >= 1

    # 8. Reconcile positions
    res_rec = await async_client.post("/api/v1/positions/reconcile?account_id=acc_main&broker_id=paper_broker", headers=headers)
    assert res_rec.status_code == 200
    assert res_rec.json()["is_fully_reconciled"] is True
