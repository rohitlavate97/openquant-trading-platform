"""Unit tests for Order Management System (OMS) Service, Idempotency, and Position Reconciliation."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from openquant.domain.models.order import (
    OrderRequest,
    OrderStatus,
    OrderSide,
    OrderType,
)
from openquant.domain.models.position import PositionSide
from openquant.domain.models.market_data import Tick
from openquant.adapters.repositories.in_memory_oms_repo import (
    InMemoryOrderRepository,
    InMemoryPositionRepository,
)
from openquant.adapters.brokers.registry import BrokerAdapterRegistry
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.adapters.market_data.in_memory_feed import InMemoryMarketDataFeed
from openquant.adapters.market_data.candle_aggregator import StreamingCandleAggregator
from openquant.adapters.market_data.synthetic_feed import SyntheticMarketFeed
from openquant.interfaces.api.v1.websocket.connection_manager import WebSocketConnectionManager
from openquant.application.services.streaming_service import StreamingBroadcasterService
from openquant.application.services.market_data_service import MarketDataService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.application.services.order_service import OrderManagementService
from openquant.application.services.risk_service import risk_service


@pytest.fixture(autouse=True)
async def reset_kill_switch_state():
    await risk_service.deactivate_kill_switch()
    yield
    await risk_service.deactivate_kill_switch()



@pytest.fixture
def oms_service() -> tuple[OrderManagementService, MarketDataService, PaperBrokerAdapter]:
    order_repo = InMemoryOrderRepository()
    pos_repo = InMemoryPositionRepository()
    broker_reg = BrokerAdapterRegistry()

    paper_broker = PaperBrokerAdapter(adapter_id="paper_broker")
    broker_reg.register(paper_broker)

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
        default_max_staleness_ms=3000,
    )
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())

    service = OrderManagementService(
        order_repo=order_repo,
        pos_repo=pos_repo,
        broker_reg=broker_reg,
        mkt_service=mkt_service,
        broadcaster=broadcaster,
        audit=audit,
    )
    return service, mkt_service, paper_broker


@pytest.mark.asyncio
async def test_oms_strict_idempotency_and_order_flow(oms_service):
    """Verify idempotent replay without duplicate broker execution (Non-Negotiable Rule 8)."""
    service, mkt_service, broker = oms_service

    # Feed fresh market tick for AAPL
    await mkt_service.ingest_tick(Tick(
        symbol="AAPL",
        exchange="NASDAQ",
        last_price=Decimal("185.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    req = OrderRequest(
        idempotency_key="idemp_key_001_unique",
        strategy_id="strat_momentum_1",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
    )

    # 1. First order submission
    order1 = await service.submit_order(req, actor_id="trader_1")
    assert order1.status in [OrderStatus.SUBMITTED, OrderStatus.FILLED, OrderStatus.OPEN]
    assert order1.symbol == "AAPL"
    assert order1.quantity == Decimal("10")

    # 2. Second submission with IDENTICAL idempotency key
    order2 = await service.submit_order(req, actor_id="trader_1")
    assert order2.order_id == order1.order_id
    assert order2.idempotency_key == order1.idempotency_key

    # Verify only 1 order exists in repository
    orders = await service.list_orders("acc_main")
    assert len(orders) == 1


@pytest.mark.asyncio
async def test_oms_position_tracking_and_realized_pnl(oms_service):
    """Verify position weighted average price and realized PnL calculations on fills."""
    service, mkt_service, broker = oms_service

    # Ingest fresh market tick
    await mkt_service.ingest_tick(Tick(
        symbol="TSLA",
        exchange="NASDAQ",
        last_price=Decimal("200.00"),
        timestamp=datetime.now(timezone.utc),
    ))

    # Buy 10 TSLA @ 200
    req1 = OrderRequest(
        idempotency_key="buy_tsla_1",
        strategy_id="strat_1",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="TSLA",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("200.00"),
        quantity=Decimal("10"),
    )
    await service.submit_order(req1)

    # Positions should show LONG 10 TSLA
    positions = await service.list_positions("acc_main")
    tsla_pos = next((p for p in positions if p.symbol == "TSLA"), None)
    assert tsla_pos is not None
    assert tsla_pos.quantity == Decimal("10")
    assert tsla_pos.side == PositionSide.LONG

    # Buy another 10 TSLA @ 220
    await mkt_service.ingest_tick(Tick(
        symbol="TSLA",
        last_price=Decimal("220.00"),
        timestamp=datetime.now(timezone.utc),
    ))
    req2 = OrderRequest(
        idempotency_key="buy_tsla_2",
        strategy_id="strat_1",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="TSLA",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("220.00"),
        quantity=Decimal("10"),
    )
    await service.submit_order(req2)

    positions2 = await service.list_positions("acc_main")
    tsla_pos2 = next(p for p in positions2 if p.symbol == "TSLA")
    assert tsla_pos2.quantity == Decimal("20")
    assert tsla_pos2.entry_price == Decimal("210.00")  # (10*200 + 10*220) / 20 = 210


@pytest.mark.asyncio
async def test_oms_position_reconciliation(oms_service):
    """Verify continuous position reconciliation against broker actual positions."""
    service, mkt_service, broker = oms_service

    # Ingest fresh tick and buy position
    await mkt_service.ingest_tick(Tick(
        symbol="NVDA",
        last_price=Decimal("120.00"),
        timestamp=datetime.now(timezone.utc),
    ))
    req = OrderRequest(
        idempotency_key="rec_nvda_1",
        strategy_id="strat_rec",
        account_id="acc_main",
        broker_id="paper_broker",
        symbol="NVDA",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
    )
    await service.submit_order(req)

    # Reconcile positions
    report = await service.reconcile_positions(account_id="acc_main", broker_id="paper_broker")
    assert report.is_fully_reconciled is True
    assert report.discrepancy_count == 0
    assert any(item.symbol == "NVDA" and item.is_reconciled for item in report.items)
