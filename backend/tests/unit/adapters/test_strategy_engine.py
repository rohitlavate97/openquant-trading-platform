"""Unit tests for Strategy Engine runtime adapter and lifecycle hooks."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from openquant.adapters.strategy.strategy_engine import StrategyEngine
from openquant.domain.models.strategy import Strategy, StrategyState, StrategyParameter
from openquant.domain.models.market_data import Candle, Tick


@pytest.mark.asyncio
async def test_strategy_engine_registration_and_ast_check():
    """Verify strategy engine registers clean code and rejects malicious AST."""
    engine = StrategyEngine()

    clean_strat = Strategy(
        strategy_id="strat_clean",
        name="Clean Strategy",
        source_code="""
# EMAMomentumStrategy
prices = [1, 2, 3]
""",
        symbols=["AAPL"],
    )
    assert await engine.register_strategy(clean_strat) is True

    bad_strat = Strategy(
        strategy_id="strat_bad",
        name="Bad Strategy",
        source_code="import subprocess\nsubprocess.run(['ls'])",
        symbols=["AAPL"],
    )
    assert await engine.register_strategy(bad_strat) is False
    assert bad_strat.state == StrategyState.ERROR


@pytest.mark.asyncio
async def test_strategy_engine_ema_crossover_signal_generation():
    """Verify EMA Momentum Strategy generates signals upon candle bar ingestion."""
    engine = StrategyEngine()

    strat = Strategy(
        strategy_id="strat_ema_test",
        name="EMA Momentum Strategy",
        source_code="""
# EMAMomentumStrategy
fast_sma = 0
""",
        parameters=[
            StrategyParameter(name="fast_period", default_value=3, current_value=3),
            StrategyParameter(name="slow_period", default_value=5, current_value=5),
            StrategyParameter(name="trade_quantity", default_value="10", current_value="10"),
        ],
        symbols=["AAPL"],
    )

    await engine.register_strategy(strat)
    started = await engine.start_strategy(strat.strategy_id)
    assert started is True
    assert await engine.get_strategy_state(strat.strategy_id) == StrategyState.RUNNING

    # Feed increasing candles to trigger bullish crossover
    prices = [100.0, 101.0, 102.0, 104.0, 106.0, 109.0]
    all_signals = []
    for p in prices:
        candle = Candle(
            symbol="AAPL",
            timeframe="1m",
            open=Decimal(str(p - 0.5)),
            high=Decimal(str(p + 1.0)),
            low=Decimal(str(p - 1.0)),
            close=Decimal(str(p)),
            volume=Decimal("1000"),
            timestamp=datetime.now(timezone.utc),
        )
        sigs = await engine.process_bar(candle)
        if sigs:
            all_signals.extend(sigs)

    assert len(all_signals) > 0
    assert all_signals[0].signal_type == "BUY"
    assert all_signals[0].symbol == "AAPL"

    # Stop strategy
    stopped = await engine.stop_strategy(strat.strategy_id)
    assert stopped is True
    assert await engine.get_strategy_state(strat.strategy_id) == StrategyState.STOPPED


@pytest.mark.asyncio
async def test_strategy_engine_rsi_mean_reversion_execution():
    """Verify RSI Strategy triggers BUY on oversold conditions."""
    engine = StrategyEngine()

    strat = Strategy(
        strategy_id="strat_rsi_test",
        name="RSI Mean Reversion Strategy",
        source_code="""
# RSIMeanReversionStrategy
rsi = 0
""",
        parameters=[
            StrategyParameter(name="period", default_value=3, current_value=3),
            StrategyParameter(name="oversold_threshold", default_value=30.0, current_value=30.0),
            StrategyParameter(name="overbought_threshold", default_value=70.0, current_value=70.0),
            StrategyParameter(name="trade_quantity", default_value="5", current_value="5"),
        ],
        symbols=["TSLA"],
    )

    await engine.register_strategy(strat)
    await engine.start_strategy(strat.strategy_id)

    # Sharp price drop -> oversold RSI -> BUY signal
    drop_prices = [200.0, 195.0, 185.0, 170.0, 155.0]
    signals = []
    for p in drop_prices:
        candle = Candle(
            symbol="TSLA",
            timeframe="1m",
            open=Decimal(str(p + 1.0)),
            high=Decimal(str(p + 2.0)),
            low=Decimal(str(p - 2.0)),
            close=Decimal(str(p)),
            volume=Decimal("500"),
            timestamp=datetime.now(timezone.utc),
        )
        sigs = await engine.process_bar(candle)
        if sigs:
            signals.extend(sigs)

    assert any(s.signal_type == "BUY" for s in signals)
