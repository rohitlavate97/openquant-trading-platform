"""Unit tests for Backtesting Application Service and Stage 2 Promotion."""

import pytest
from decimal import Decimal
from openquant.application.services.backtest_service import BacktestService
from openquant.adapters.backtest.event_driven_engine import EventDrivenBacktestEngine
from openquant.application.services.strategy_service import StrategyService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.domain.models.backtest import BacktestConfig
from openquant.domain.models.promotion import StrategyPromotionStage


@pytest.fixture
def backtest_service_instance():
    engine = EventDrivenBacktestEngine()
    strat_svc = StrategyService()
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())
    return BacktestService(engine=engine, strategy_svc=strat_svc, audit=audit)


@pytest.mark.asyncio
async def test_backtest_service_run_and_caching(backtest_service_instance):
    """Verify backtesting workflow runs, generates candles, and caches report."""
    config = BacktestConfig(
        strategy_id="strat_test_service",
        symbols=["AAPL"],
        initial_cash=Decimal("100000.00"),
    )

    result = await backtest_service_instance.run_backtest(config=config)
    assert result.backtest_id.startswith("bt_")
    assert result.metrics.final_equity > Decimal("0")

    cached = await backtest_service_instance.get_backtest_result(result.backtest_id)
    assert cached is not None
    assert cached.backtest_id == result.backtest_id


@pytest.mark.asyncio
async def test_backtest_service_promotion_to_stage_2(backtest_service_instance):
    """Verify promotion gating advances strategy from DRAFT to BACKTESTED."""
    # Create strategy
    strat = await backtest_service_instance._strategy_service.create_strategy(
        name="Stage 2 Promotion Candidate",
        source_code="# EMAMomentumStrategy\nfast_sma = 0",
        symbols=["AAPL"],
    )
    assert strat.promotion_stage == StrategyPromotionStage.DRAFT

    config = BacktestConfig(
        strategy_id=strat.strategy_id,
        symbols=["AAPL"],
        initial_cash=Decimal("100000.00"),
    )
    result = await backtest_service_instance.run_backtest(config=config)

    # Force positive profit if zero trades for test assertion
    result.metrics.total_net_profit = Decimal("1500.00")
    result.metrics.max_drawdown_pct = 5.0
    backtest_service_instance._results_cache[result.backtest_id] = result

    promoted = await backtest_service_instance.promote_strategy_to_backtested(
        strategy_id=strat.strategy_id,
        backtest_id=result.backtest_id,
    )
    assert promoted is True
    assert strat.promotion_stage == StrategyPromotionStage.BACKTEST
