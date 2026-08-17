"""High-concurrency stress testing for OMS Idempotency, Rate Limiter, and Position Integrity."""

import asyncio
from decimal import Decimal
import time
import uuid
import pytest
from openquant.application.services.order_service import OrderManagementService
from openquant.application.services.risk_service import risk_service
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType
from openquant.domain.models.market_data import Tick
from openquant.domain.models.risk import RiskLimitsConfig
from openquant.domain.exceptions import RiskLimitBreachedError
from openquant.adapters.repositories.in_memory_oms_repo import (
    InMemoryOrderRepository,
    InMemoryPositionRepository,
)
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.adapters.brokers.registry import BrokerAdapterRegistry
from openquant.application.services.market_data_service import market_data_service
from openquant.application.services.streaming_service import streaming_broadcaster
from openquant.application.services.audit_service import audit_log_service


@pytest.fixture
async def clean_oms_service() -> OrderManagementService:
    # Seed live market tick
    await market_data_service.ingest_tick(Tick(
        symbol="AAPL",
        last_price=Decimal("150.00"),
        bid_price=Decimal("149.95"),
        ask_price=Decimal("150.05"),
        volume=Decimal("1000"),
    ))

    order_repo = InMemoryOrderRepository()
    pos_repo = InMemoryPositionRepository()
    broker = PaperBrokerAdapter(adapter_id="stress_paper")
    registry = BrokerAdapterRegistry()
    registry.register(broker)

    return OrderManagementService(
        order_repo=order_repo,
        pos_repo=pos_repo,
        broker_reg=registry,
        mkt_service=market_data_service,
        broadcaster=streaming_broadcaster,
        audit=audit_log_service,
    )


@pytest.mark.asyncio
async def test_concurrent_identical_idempotency_key_race_condition(clean_oms_service: OrderManagementService):
    """Stress test: 20 simultaneous tasks submit the exact same (account_id, idempotency_key).
    Enforces Rule 8: Strict composite idempotency with zero duplicate order routing or double execution.
    """
    idempotency_key = f"idem_stress_{uuid.uuid4().hex[:8]}"
    account_id = "ACC_STRESS_1"

    req = OrderRequest(
        account_id=account_id,
        broker_id="stress_paper",
        strategy_id="strat_concurrency_test",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        price=Decimal("150.00"),
        idempotency_key=idempotency_key,
    )

    # Launch 20 concurrent submissions
    tasks = [clean_oms_service.submit_order(req) for _ in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # All returned orders must have the exact same order_id (or raised idempotent conflict)
    successful_orders = [r for r in results if not isinstance(r, Exception)]
    assert len(successful_orders) == 20

    first_order_id = successful_orders[0].order_id
    for order in successful_orders:
        assert order.order_id == first_order_id
        assert order.idempotency_key == idempotency_key

    # Check that the underlying repository contains exactly ONE order
    all_orders = await clean_oms_service._order_repo.list_all()
    matching = [o for o in all_orders if o.idempotency_key == idempotency_key]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_rate_limiter_blocks_burst_over_threshold(clean_oms_service: OrderManagementService):
    """Stress test: 25 simultaneous orders under 10/sec rate limit -> enforces rate limiter hard stop."""
    risk_service.update_config(RiskLimitsConfig(max_orders_per_second=10))
    risk_service._engine._order_timestamps.clear()
    account_id = "ACC_STRESS_RATE"

    async def submit_unique_order(idx: int):
        req = OrderRequest(
            account_id=account_id,
            broker_id="stress_paper",
            strategy_id="strat_rate_test",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1"),
            price=Decimal("150.00"),
            idempotency_key=f"idem_rate_{idx}_{uuid.uuid4().hex[:6]}",
        )
        return await clean_oms_service.submit_order(req)

    tasks = [submit_unique_order(i) for i in range(25)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if not isinstance(r, Exception)]
    rate_limited = [r for r in results if isinstance(r, RiskLimitBreachedError)]

    assert len(successes) == 10
    assert len(rate_limited) == 15


@pytest.mark.asyncio
async def test_high_concurrency_unique_orders_under_configured_quota(clean_oms_service: OrderManagementService):
    """Stress test: 30 concurrent distinct orders under raised quota (50/sec) verifying position integrity."""
    risk_service.update_config(RiskLimitsConfig(max_orders_per_second=50))
    account_id = "ACC_STRESS_BURST"

    async def submit_unique_order(idx: int):
        req = OrderRequest(
            account_id=account_id,
            broker_id="stress_paper",
            strategy_id="strat_concurrency_test",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1"),
            price=Decimal("150.00"),
            idempotency_key=f"idem_burst_{idx}_{uuid.uuid4().hex[:6]}",
        )
        return await clean_oms_service.submit_order(req)

    tasks = [submit_unique_order(i) for i in range(30)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 30
    all_orders = await clean_oms_service._order_repo.list_all()
    assert len(all_orders) >= 30

    # Verify positions accumulated accurately (30 orders * 1 quantity = 30 quantity)
    pos = await clean_oms_service._pos_repo.get_position(account_id, "AAPL")
    assert pos is not None
    assert pos.quantity == Decimal("30")
