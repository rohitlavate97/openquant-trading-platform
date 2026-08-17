"""Unit tests for Broker Adapters, Paper Engine, and Certification Harness."""

import pytest
from decimal import Decimal
from openquant.domain.models.order import Order, OrderSide, OrderType, OrderStatus
from openquant.domain.models.position import PositionSide
from openquant.domain.exceptions import BrokerAdapterUncertifiedError, BrokerConnectionError
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.adapters.brokers.zerodha_adapter import ZerodhaKiteAdapter
from openquant.adapters.brokers.certification_harness import BrokerAdapterCertificationHarness


@pytest.mark.asyncio
async def test_paper_broker_adapter_order_and_position_lifecycle():
    """Verify PaperBrokerAdapter executes orders, adjusts cash, and updates positions."""
    adapter = PaperBrokerAdapter(initial_cash=Decimal("50000.00"), slippage_bps=Decimal("0"))
    await adapter.connect({})
    assert await adapter.is_connected() is True

    # 1. Place Buy Order
    order = Order(
        order_id="ord_paper_01",
        idempotency_key="idemp_pap_01",
        strategy_id="strat_test",
        account_id="acc_paper",
        broker_id="paper_broker",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("180.00"),
        quantity=Decimal("10"),
    )
    report = await adapter.place_order(order)
    assert report.status == OrderStatus.FILLED
    assert report.filled_quantity == Decimal("10")
    assert report.average_fill_price == Decimal("180.00")

    # Check Funds: 50,000 - 1,800 = 48,200 cash + 1,800 pos value = 50,000 total
    adapter.set_last_price("AAPL", Decimal("180.00"))
    funds = await adapter.get_funds("acc_paper")
    assert funds.available_cash == Decimal("48200.00")
    assert funds.total_balance == Decimal("50000.00")

    # Check Positions
    positions = await adapter.get_positions("acc_paper")
    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == Decimal("10")
    assert positions[0].side == PositionSide.LONG

    # 2. Place Sell Order to Close Position
    sell_order = Order(
        order_id="ord_paper_02",
        idempotency_key="idemp_pap_02",
        strategy_id="strat_test",
        account_id="acc_paper",
        broker_id="paper_broker",
        symbol="AAPL",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("190.00"),
        quantity=Decimal("10"),
    )
    sell_report = await adapter.place_order(sell_order)
    assert sell_report.status == OrderStatus.FILLED

    # Check Positions (should be flat/closed)
    positions_after = await adapter.get_positions("acc_paper")
    assert len(positions_after) == 0

    # Check Cash: 48,200 + 1,900 = 50,100 (Profit of 100)
    funds_after = await adapter.get_funds("acc_paper")
    assert funds_after.available_cash == Decimal("50100.00")


@pytest.mark.asyncio
async def test_paper_broker_adapter_rejects_insufficient_funds():
    """Verify Paper broker rejects orders exceeding available cash balance."""
    adapter = PaperBrokerAdapter(initial_cash=Decimal("1000.00"))
    await adapter.connect({})

    order = Order(
        order_id="ord_huge",
        idempotency_key="idemp_huge",
        strategy_id="strat_test",
        account_id="acc_paper",
        broker_id="paper_broker",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("200.00"),
        quantity=Decimal("100"),  # 20,000 > 1,000
    )
    report = await adapter.place_order(order)
    assert report.status == OrderStatus.REJECTED
    assert "Insufficient paper funds" in (report.rejection_reason or "")


@pytest.mark.asyncio
async def test_zerodha_adapter_sandbox_lifecycle():
    """Verify Zerodha adapter handles sandbox authentication and order submission."""
    adapter = ZerodhaKiteAdapter(is_sandbox=True)
    connected = await adapter.connect({"mock_auth": "true"})
    assert connected is True
    assert await adapter.is_connected() is True

    order = Order(
        order_id="ord_kite_01",
        idempotency_key="idemp_kt_01",
        strategy_id="strat_test",
        account_id="acc_kite",
        broker_id="zerodha",
        symbol="RELIANCE",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("2950.00"),
        quantity=Decimal("5"),
    )
    report = await adapter.place_order(order)
    assert report.broker_order_id.startswith("kt_")
    assert report.status == OrderStatus.SUBMITTED

    funds = await adapter.get_funds("acc_kite")
    assert funds.currency == "INR"
    assert funds.total_balance > Decimal("0")

    await adapter.disconnect()
    assert await adapter.is_connected() is False


@pytest.mark.asyncio
async def test_broker_adapter_certification_harness():
    """Verify certification harness systematically evaluates and certifies an adapter."""
    adapter = ZerodhaKiteAdapter(is_sandbox=True)
    assert adapter.is_live_trading_eligible is False

    # Run Certification Audit
    report = await BrokerAdapterCertificationHarness.run_certification_audit(
        adapter=adapter,
        certified_by="sec_auditor_admin",
    )

    assert report.is_certified is True
    assert report.live_trading_eligible is True
    assert len(report.checks) == 5
    assert all(c.passed for c in report.checks)
    assert adapter.is_live_trading_eligible is True

    # Calling verify_live_eligible should not raise error now
    adapter.verify_live_eligible()
