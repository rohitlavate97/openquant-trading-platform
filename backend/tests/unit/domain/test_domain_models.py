"""Unit tests for domain entities, value objects, and business invariants."""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from openquant.domain.models.order import (
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from openquant.domain.models.position import Position, PositionSide
from openquant.domain.models.risk import (
    RiskCheckResult,
    RiskCheckType,
    RiskEvaluationResult,
    RiskSeverity,
)
from openquant.domain.models.market_data import Tick


def test_order_request_validation_limit_order():
    """Verify limit order requires positive price."""
    # Valid limit order
    req = OrderRequest(
        idempotency_key="idemp_12345678",
        strategy_id="strat_1",
        account_id="acc_1",
        broker_id="zerodha",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("10"),
        price=Decimal("150.50"),
    )
    assert req.price == Decimal("150.50")

    # Invalid limit order missing price
    with pytest.raises(ValidationError):
        OrderRequest(
            idempotency_key="idemp_12345678",
            strategy_id="strat_1",
            account_id="acc_1",
            broker_id="zerodha",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10"),
            price=None,
        )


def test_order_entity_remaining_quantity_and_terminal_state():
    """Verify remaining quantity computation and terminal status check."""
    order = Order(
        order_id="ord_1",
        idempotency_key="idemp_12345678",
        strategy_id="strat_1",
        account_id="acc_1",
        broker_id="zerodha",
        symbol="TSLA",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("100"),
        filled_quantity=Decimal("40"),
        price=Decimal("250.00"),
        status=OrderStatus.PARTIALLY_FILLED,
    )
    assert order.remaining_quantity == Decimal("60")
    assert not order.is_terminal

    order.status = OrderStatus.FILLED
    order.filled_quantity = Decimal("100")
    assert order.remaining_quantity == Decimal("0")
    assert order.is_terminal


def test_position_pnl_updates():
    """Verify position unrealized PnL calculation for Long and Short."""
    pos = Position(
        position_id="pos_1",
        account_id="acc_1",
        strategy_id="strat_1",
        broker_id="zerodha",
        symbol="MSFT",
        side=PositionSide.LONG,
        quantity=Decimal("10"),
        entry_price=Decimal("400.00"),
        current_price=Decimal("400.00"),
    )
    assert pos.unrealized_pnl == Decimal("0")
    assert pos.market_value == Decimal("4000.00")

    # Price increases by $10
    pos.update_market_price(Decimal("410.00"))
    assert pos.unrealized_pnl == Decimal("100.00")
    assert pos.market_value == Decimal("4100.00")

    # Short position
    pos_short = Position(
        position_id="pos_2",
        account_id="acc_1",
        strategy_id="strat_1",
        broker_id="zerodha",
        symbol="GOOGL",
        side=PositionSide.SHORT,
        quantity=Decimal("5"),
        entry_price=Decimal("200.00"),
        current_price=Decimal("200.00"),
    )
    pos_short.update_market_price(Decimal("190.00"))
    assert pos_short.unrealized_pnl == Decimal("50.00")

    # Flat position
    pos_flat = Position(
        position_id="pos_3",
        account_id="acc_1",
        strategy_id="strat_1",
        broker_id="zerodha",
        symbol="GOOGL",
        side=PositionSide.FLAT,
    )
    pos_flat.update_market_price(Decimal("190.00"))
    assert pos_flat.unrealized_pnl == Decimal("0")


def test_risk_evaluation_result_factories():
    """Verify risk evaluation aggregation."""
    check_pass = RiskCheckResult(
        check_type=RiskCheckType.KILL_SWITCH,
        passed=True,
        severity=RiskSeverity.BLOCKING,
        rule_name="KillSwitchCheck",
        message="Kill switch inactive",
    )
    check_fail = RiskCheckResult(
        check_type=RiskCheckType.DAILY_LOSS_LIMIT,
        passed=False,
        severity=RiskSeverity.BLOCKING,
        rule_name="DailyLossCheck",
        message="Daily loss limit 3.0% breached: current drawdown 3.5%",
    )

    approved = RiskEvaluationResult.create_approved([check_pass])
    assert approved.allowed is True
    assert len(approved.rejection_reasons) == 0

    rejected = RiskEvaluationResult.create_rejected([check_pass, check_fail])
    assert rejected.allowed is False
    assert len(rejected.rejection_reasons) == 1
    assert "Daily loss limit" in rejected.rejection_reasons[0]


def test_tick_staleness():
    """Verify tick staleness detection."""
    tick = Tick(
        symbol="NVDA",
        last_price=Decimal("125.00"),
    )
    assert not tick.is_stale(max_staleness_ms=5000)
