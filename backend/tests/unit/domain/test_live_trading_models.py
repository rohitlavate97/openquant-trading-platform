from decimal import Decimal
import pytest
from openquant.domain.models.live_trading import (
    LiveCapitalAllocation,
    LivePreflightCheckItem,
    LivePreflightReport,
    LiveStrategySession,
    LiveTradingState,
    ScalingTier,
)


def test_live_capital_allocation_scaling_tiers():
    alloc = LiveCapitalAllocation(
        strategy_id="strat_live_1",
        broker_id="zerodha",
        account_id="ACC_123",
        total_authorized_capital=Decimal("100000.00"),
        scaling_tier=ScalingTier.TIER_1_STARTER,
    )
    assert alloc.effective_allocated_capital == Decimal("25000.00")

    alloc.scaling_tier = ScalingTier.TIER_2_INTERMEDIATE
    assert alloc.effective_allocated_capital == Decimal("50000.00")

    alloc.scaling_tier = ScalingTier.TIER_3_FULL
    assert alloc.effective_allocated_capital == Decimal("100000.00")


def test_live_preflight_report_model():
    report = LivePreflightReport(
        strategy_id="strat_live_1",
        broker_id="interactive_brokers",
        account_id="U1234567",
        is_eligible=True,
        checks=[
            LivePreflightCheckItem(
                check_name="PROMOTION_GATE_STAGE_4",
                passed=True,
                description="Verified Stage 4",
            )
        ],
    )
    assert report.is_eligible is True
    assert len(report.checks) == 1
    assert report.checks[0].passed is True


def test_live_strategy_session_defaults():
    alloc = LiveCapitalAllocation(
        strategy_id="strat_live_1",
        broker_id="binance_crypto",
        account_id="binance_main",
    )
    session = LiveStrategySession(
        session_id="live_test_1",
        strategy_id="strat_live_1",
        strategy_name="Crypto Momentum",
        broker_id="binance_crypto",
        account_id="binance_main",
        allocation=alloc,
        activated_by="trader_1",
    )
    assert session.state == LiveTradingState.READY
    assert session.realized_pnl == Decimal("0.00")
    assert session.live_orders_count == 0
