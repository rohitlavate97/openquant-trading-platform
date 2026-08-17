"""Domain models for Historical Event-Driven Backtesting and Walk-Forward Validation."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    """Configuration parameters defining a backtest simulation run."""
    strategy_id: str
    symbols: list[str] = Field(default_factory=lambda: ["AAPL"])
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeframe: str = "1m"
    initial_cash: Decimal = Decimal("100000.00")
    slippage_bps: float = Field(default=5.0, ge=0.0, description="Slippage in basis points (1 bp = 0.01%)")
    commission_per_order: Decimal = Decimal("1.00")
    parameters: dict[str, Any] = Field(default_factory=dict)


class BacktestTrade(BaseModel):
    """Historical trade executed during backtest simulation."""
    trade_id: str
    symbol: str
    side: str
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    pnl: Decimal
    return_pct: float
    commission_paid: Decimal = Decimal("0.00")
    holding_duration_seconds: float = 0.0


class EquityPoint(BaseModel):
    """Snapshot point on the portfolio equity curve."""
    timestamp: datetime
    equity: Decimal
    cash: Decimal
    drawdown_pct: float = 0.0


class BacktestPerformanceMetrics(BaseModel):
    """Computed financial performance indicators for strategy evaluation."""
    initial_equity: Decimal = Decimal("100000.00")
    final_equity: Decimal = Decimal("100000.00")
    total_net_profit: Decimal = Decimal("0.00")
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_dollars: Decimal = Decimal("0.00")
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0
    average_trade_pnl: Decimal = Decimal("0.00")
    average_win: Decimal = Decimal("0.00")
    average_loss: Decimal = Decimal("0.00")


class BacktestResult(BaseModel):
    """Comprehensive artifact report produced by a backtesting simulation."""
    backtest_id: str
    strategy_id: str
    config: BacktestConfig
    metrics: BacktestPerformanceMetrics
    equity_curve: list[EquityPoint] = Field(default_factory=list)
    trades: list[BacktestTrade] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WalkForwardWindow(BaseModel):
    """Single In-Sample / Out-of-Sample window in Walk-Forward Validation."""
    window_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    in_sample_metrics: BacktestPerformanceMetrics
    out_of_sample_metrics: BacktestPerformanceMetrics
    efficiency_ratio: float = 0.0


class WalkForwardResult(BaseModel):
    """Multi-window rolling Walk-Forward Optimization & Validation report."""
    validation_id: str
    strategy_id: str
    num_windows: int
    overall_efficiency_ratio: float
    is_robust: bool
    overfitting_risk: str = Field(..., description="LOW | MEDIUM | HIGH")
    windows: list[WalkForwardWindow] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
