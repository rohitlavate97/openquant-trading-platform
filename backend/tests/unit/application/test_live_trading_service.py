from decimal import Decimal
import pytest

from openquant.domain.models.live_trading import (
    LiveCapitalAllocation,
    LiveTradingState,
    ScalingTier,
)
from openquant.domain.models.promotion import StrategyPromotionStage
from openquant.domain.models.strategy import Strategy, StrategyState
from openquant.application.services.strategy_service import StrategyService
from openquant.application.services.live_trading_service import LiveTradingService
from openquant.adapters.strategy.strategy_engine import StrategyEngine
from openquant.adapters.sandbox.runner import StrategySandboxRunner
from openquant.adapters.repositories.in_memory_live_session_repo import InMemoryLiveSessionRepository
from openquant.adapters.brokers.registry import create_default_registry
from openquant.application.services.risk_service import RiskService
from openquant.application.services.market_data_service import MarketDataService
from openquant.adapters.market_data.in_memory_feed import InMemoryMarketDataFeed
from openquant.adapters.market_data.candle_aggregator import StreamingCandleAggregator
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.adapters.event_bus.in_memory_event_bus import InMemoryEventBus


@pytest.fixture
def live_trading_setup():
    audit_repo = InMemoryAuditLogRepository()
    audit_serv = AuditLogService(audit_repo)
    strat_serv = StrategyService(
        engine=StrategyEngine(sandbox=StrategySandboxRunner()),
        sandbox=StrategySandboxRunner(),
        audit=audit_serv,
    )
    broker_reg = create_default_registry()
    risk_serv = RiskService()
    feed = InMemoryMarketDataFeed()
    agg = StreamingCandleAggregator()
    bus = InMemoryEventBus()
    md_serv = MarketDataService(feed=feed, aggregator=agg)
    live_repo = InMemoryLiveSessionRepository()

    service = LiveTradingService(
        strategy_service=strat_serv,
        broker_registry=broker_reg,
        risk_service=risk_serv,
        market_data_service=md_serv,
        live_repo=live_repo,
        event_bus=bus,
        audit_service=audit_serv,
    )
    return service, strat_serv, broker_reg, risk_serv


@pytest.mark.asyncio
async def test_live_trading_preflight_blocks_non_stage_4(live_trading_setup):
    service, strat_serv, broker_reg, _ = live_trading_setup

    # Create Draft Strategy (Stage 1)
    strat = await strat_serv.create_strategy(
        name="Draft EMA",
        source_code="fast_sma = 0",
        description="Testing preflight block",
    )

    report = await service.run_preflight_check(
        strategy_id=strat.strategy_id,
        broker_id="paper_broker",
        account_id="acc_1",
    )
    assert report.is_eligible is False
    assert any("requires Stage 4" in r for r in report.rejection_reasons)


@pytest.mark.asyncio
async def test_live_trading_full_lifecycle(live_trading_setup):
    service, strat_serv, broker_reg, _ = live_trading_setup

    # Create Strategy & manually set to Stage 4 for test
    strat = await strat_serv.create_strategy(
        name="Live Momentum Alpha",
        source_code="fast_sma = 0",
        description="Live strategy",
    )
    strat.promotion_stage = StrategyPromotionStage.LIVE_TRADING

    # 1. Preflight Check
    report = await service.run_preflight_check(
        strategy_id=strat.strategy_id,
        broker_id="paper_broker",
        account_id="acc_1",
    )
    assert report.is_eligible is True

    # 2. Activate Session
    alloc = LiveCapitalAllocation(
        strategy_id=strat.strategy_id,
        broker_id="paper_broker",
        account_id="acc_1",
        total_authorized_capital=Decimal("100000.00"),
        scaling_tier=ScalingTier.TIER_1_STARTER,
    )
    session = await service.activate_live_session(
        strategy_id=strat.strategy_id,
        broker_id="paper_broker",
        account_id="acc_1",
        allocation=alloc,
        activated_by="trader_admin",
        confirmed_by="risk_officer",
    )
    assert session.state == LiveTradingState.ACTIVE
    assert session.allocation.effective_allocated_capital == Decimal("25000.00")

    # 3. Adjust Scaling Tier to 50%
    scaled = await service.adjust_scaling_tier(
        session_id=session.session_id,
        new_tier=ScalingTier.TIER_2_INTERMEDIATE,
        actor_id="risk_officer",
    )
    assert scaled.allocation.effective_allocated_capital == Decimal("50000.00")

    # 4. Emergency Halt
    halted = await service.halt_live_session(
        session_id=session.session_id,
        reason="Abnormal market volatility detected",
        actor_id="risk_officer",
    )
    assert halted.state == LiveTradingState.HALTED
    assert halted.halt_reason == "Abnormal market volatility detected"
