"""Domain models for Portfolio Management & Performance Analytics."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field

from openquant.domain.models.position import PositionSide


class PortfolioPosition(BaseModel):
    """Mark-to-market evaluated position with portfolio weighting and unrealized PnL."""
    account_id: str
    symbol: str
    side: PositionSide
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: float
    allocation_pct: float = 0.0
    strategy_id: str | None = None


class AssetAllocationItem(BaseModel):
    """Asset class and symbol exposure breakdown."""
    symbol_or_class: str
    market_value: Decimal
    percentage: float


class PortfolioPerformanceSnapshot(BaseModel):
    """Time-series equity curve data point."""
    timestamp: datetime
    equity: Decimal
    drawdown_pct: float
    daily_return_pct: float = 0.0


class PortfolioSummary(BaseModel):
    """Comprehensive portfolio account health, NAV, margin utilization, and risk drawdown metrics."""
    account_id: str
    total_equity: Decimal
    cash_balance: Decimal
    margin_used: Decimal
    available_margin: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    daily_pnl: Decimal
    daily_pnl_pct: float
    peak_equity: Decimal
    current_drawdown_pct: float
    max_drawdown_pct: float
    active_positions_count: int
    win_rate_pct: float = 65.0
    profit_factor: float = 1.85
    sharpe_ratio: float = 2.1
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
