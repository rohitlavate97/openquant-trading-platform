"""Unit tests for Event-Driven Backtest Engine and Walk-Forward Validator."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from openquant.adapters.backtest.event_driven_engine import EventDrivenBacktestEngine
from openquant.domain.models.strategy import Strategy, StrategyParameter
from openquant.domain.models.market_data import Candle
from openquant.domain.models.backtest import BacktestConfig


@pytest.fixture
def sample_candles():
    now = datetime.now(timezone.utc) - timedelta(minutes=60)
    candles = []
    # Up-trend followed by mean-reversion
    prices = [100.0 + (i * 0.5 if i < 30 else 30 * 0.5 - (i - 30) * 0.3) for i in range(60)]
    for i, p in enumerate(prices):
        candles.append(
            Candle(
                symbol="AAPL",
                timeframe="1m",
                open=Decimal(str(p)),
                high=Decimal(str(p + 0.5)),
                low=Decimal(str(p - 0.5)),
                close=Decimal(str(p)),
                volume=Decimal("1000"),
                timestamp=now + timedelta(minutes=i),
            )
        )
    return candles


@pytest.mark.asyncio
async def test_event_driven_backtest_simulation(sample_candles):
    """Verify event-driven backtesting generates equity curve, trades, and metrics."""
    engine = EventDrivenBacktestEngine()

    strat = Strategy(
        strategy_id="strat_bt_test",
        name="EMA Momentum",
        source_code="# EMAMomentumStrategy\nfast_sma = 0",
        parameters=[
            StrategyParameter(name="fast_period", default_value=3, current_value=3),
            StrategyParameter(name="slow_period", default_value=5, current_value=5),
        ],
        symbols=["AAPL"],
    )

    config = BacktestConfig(
        strategy_id="strat_bt_test",
        symbols=["AAPL"],
        initial_cash=Decimal("50000.00"),
        slippage_bps=2.0,
        commission_per_order=Decimal("0.50"),
    )

    result = await engine.run_backtest(
        config=config,
        strategy=strat,
        historical_candles=sample_candles,
    )

    assert result.backtest_id.startswith("bt_")
    assert result.strategy_id == "strat_bt_test"
    assert len(result.equity_curve) == len(sample_candles)
    assert result.metrics.initial_equity == Decimal("50000.00")
    assert result.metrics.total_trades >= 0
    assert result.metrics.sharpe_ratio != 0.0


@pytest.mark.asyncio
async def test_walk_forward_validation_windows(sample_candles):
    """Verify rolling Walk-Forward In-Sample vs Out-of-Sample analysis."""
    engine = EventDrivenBacktestEngine()

    strat = Strategy(
        strategy_id="strat_wfv_test",
        name="EMA Momentum",
        source_code="# EMAMomentumStrategy\nfast_sma = 0",
        symbols=["AAPL"],
    )

    config = BacktestConfig(
        strategy_id="strat_wfv_test",
        symbols=["AAPL"],
        initial_cash=Decimal("100000.00"),
    )

    wfv = await engine.run_walk_forward_validation(
        config=config,
        strategy=strat,
        historical_candles=sample_candles,
        num_windows=3,
        train_ratio=0.7,
    )

    assert wfv.validation_id.startswith("wfv_")
    assert len(wfv.windows) > 0
    assert wfv.overfitting_risk in ["LOW", "MEDIUM", "HIGH"]
    assert wfv.overall_efficiency_ratio >= 0.0
