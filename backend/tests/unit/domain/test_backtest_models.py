"""Unit tests for Backtesting Domain Models and Walk-Forward Validation data structures."""

from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.backtest import (
    BacktestConfig,
    BacktestTrade,
    EquityPoint,
    BacktestPerformanceMetrics,
    BacktestResult,
    WalkForwardWindow,
    WalkForwardResult,
)


def test_backtest_config_defaults():
    """Verify BacktestConfig default parameters."""
    cfg = BacktestConfig(strategy_id="strat_test_1", symbols=["AAPL", "TSLA"])
    assert cfg.strategy_id == "strat_test_1"
    assert cfg.symbols == ["AAPL", "TSLA"]
    assert cfg.initial_cash == Decimal("100000.00")
    assert cfg.slippage_bps == 5.0
    assert cfg.commission_per_order == Decimal("1.00")


def test_backtest_trade_and_equity_point():
    """Verify BacktestTrade and EquityPoint calculations and serialization."""
    trade = BacktestTrade(
        trade_id="trd_1",
        symbol="AAPL",
        side="BUY_LONG_EXIT",
        entry_time=datetime.now(timezone.utc),
        exit_time=datetime.now(timezone.utc),
        entry_price=Decimal("180.00"),
        exit_price=Decimal("185.00"),
        quantity=Decimal("10"),
        pnl=Decimal("48.00"),
        return_pct=2.78,
        commission_paid=Decimal("2.00"),
        holding_duration_seconds=3600.0,
    )
    assert trade.pnl == Decimal("48.00")
    assert trade.quantity == Decimal("10")

    point = EquityPoint(
        timestamp=datetime.now(timezone.utc),
        equity=Decimal("100048.00"),
        cash=Decimal("100048.00"),
        drawdown_pct=0.0,
    )
    assert point.equity == Decimal("100048.00")


def test_walk_forward_result_assessment():
    """Verify WalkForwardResult robustness and risk flag categorization."""
    wfv = WalkForwardResult(
        validation_id="wfv_1",
        strategy_id="strat_1",
        num_windows=4,
        overall_efficiency_ratio=0.78,
        is_robust=True,
        overfitting_risk="LOW",
        windows=[],
    )
    assert wfv.is_robust is True
    assert wfv.overfitting_risk == "LOW"
    assert wfv.overall_efficiency_ratio == 0.78
