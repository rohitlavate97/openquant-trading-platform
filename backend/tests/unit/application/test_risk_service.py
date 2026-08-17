"""Unit tests for Synchronous Risk Engine and Emergency Kill Switch controls."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType, Order, OrderStatus
from openquant.domain.models.risk import (
    RiskLimitsConfig,
    KillSwitchLevel,
    RiskSeverity,
    RiskCheckType,
)
from openquant.domain.models.market_data import Tick
from openquant.domain.exceptions import RiskLimitBreachedError, KillSwitchActiveError
from openquant.adapters.risk.risk_engine import SynchronousRiskEngine
from openquant.adapters.market_data.in_memory_feed import InMemoryMarketDataFeed
from openquant.adapters.market_data.candle_aggregator import StreamingCandleAggregator
from openquant.adapters.market_data.synthetic_feed import SyntheticMarketFeed
from openquant.interfaces.api.v1.websocket.connection_manager import WebSocketConnectionManager
from openquant.application.services.streaming_service import StreamingBroadcasterService
from openquant.application.services.market_data_service import MarketDataService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.application.services.risk_service import RiskService


@pytest.fixture
def risk_test_setup():
    config = RiskLimitsConfig(
        max_daily_loss_percent=3.0,
        max_drawdown_percent=5.0,
        max_position_size_percent=10.0,
        max_orders_per_second=5,
        max_open_orders_per_symbol=3,
        self_trade_prevention=True,
    )
    engine = SynchronousRiskEngine(config=config)
    mkt_feed = InMemoryMarketDataFeed()
    aggregator = StreamingCandleAggregator()
    broadcaster = StreamingBroadcasterService(
        market_ws=WebSocketConnectionManager(),
        order_ws=WebSocketConnectionManager(),
        telemetry_ws=WebSocketConnectionManager(),
    )
    mkt_service = MarketDataService(
        feed=mkt_feed,
        aggregator=aggregator,
        broadcaster=broadcaster,
        syn_feed=SyntheticMarketFeed(),
    )
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())

    service = RiskService(
        engine=engine,
        mkt_service=mkt_service,
        broadcaster=broadcaster,
        audit=audit,
    )
    return service, engine, mkt_service


@pytest.mark.asyncio
async def test_risk_kill_switch_blocks_order_execution(risk_test_setup):
    """Verify Kill Switch halts all orders synchronously (Non-Negotiable Rule 2 & 4)."""
    service, engine, mkt_service = risk_test_setup

    await mkt_service.ingest_tick(Tick(
        symbol="AAPL",
        exchange="NASDAQ",
        last_price=Decimal("180.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    req = OrderRequest(
        idempotency_key="risk_test_1",
        strategy_id="strat_1",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("180.00"),
        quantity=Decimal("10"),
    )

    # 1. First evaluation when Kill Switch is inactive -> Passes
    res = await service.evaluate_pre_trade(req)
    assert res.allowed is True

    # 2. Activate Kill Switch
    await service.activate_kill_switch(
        level=KillSwitchLevel.GLOBAL,
        reason="Manual Risk Test Halt",
    )

    # 3. Subsequent evaluation must raise KillSwitchActiveError
    with pytest.raises(KillSwitchActiveError):
        await service.evaluate_pre_trade(req)

    # 4. Deactivate Kill Switch -> Execution restored
    await service.deactivate_kill_switch()
    res2 = await service.evaluate_pre_trade(req)
    assert res2.allowed is True


@pytest.mark.asyncio
async def test_risk_position_sizing_and_notional_cap(risk_test_setup):
    """Verify order value exceeding 10% equity is rejected."""
    service, engine, mkt_service = risk_test_setup

    await mkt_service.ingest_tick(Tick(
        symbol="GOOGL",
        exchange="NASDAQ",
        last_price=Decimal("175.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    # Total capital default = $100,000, 10% cap = $10,000.
    # Quantity 1000 @ $175 = $175,000 (breaches limit)
    huge_req = OrderRequest(
        idempotency_key="huge_order_1",
        strategy_id="strat_1",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="GOOGL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("175.00"),
        quantity=Decimal("1000"),
    )

    with pytest.raises(RiskLimitBreachedError) as exc_info:
        await service.evaluate_pre_trade(huge_req)
    assert "Position Sizing" in str(exc_info.value) or "exceeds max single position" in str(exc_info.value)


@pytest.mark.asyncio
async def test_risk_rate_limiter(risk_test_setup):
    """Verify sliding-window order rate limiter rejects orders exceeding limit."""
    service, engine, mkt_service = risk_test_setup

    await mkt_service.ingest_tick(Tick(
        symbol="NVDA",
        exchange="NASDAQ",
        last_price=Decimal("120.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    req = OrderRequest(
        idempotency_key="rate_test",
        strategy_id="strat_1",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="NVDA",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("120.00"),
        quantity=Decimal("1"),
    )

    # Config max_orders_per_second = 5
    for i in range(5):
        req.idempotency_key = f"rate_test_{i}"
        res = await service.evaluate_pre_trade(req)
        assert res.allowed is True

    # 6th order in same second must be rejected by Rate Limiter
    req.idempotency_key = "rate_test_overflow"
    with pytest.raises(RiskLimitBreachedError) as exc_info:
        await service.evaluate_pre_trade(req)
    assert "rate limit exceeded" in str(exc_info.value).lower()
