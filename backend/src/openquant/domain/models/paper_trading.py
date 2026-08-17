"""Domain models for Real-Time Paper Trading Mode and Stage 5 Promotion Gate."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field


class PaperTradingSessionStatus(StrEnum):
    """Lifecycle status of a live paper trading session."""
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class PaperOrderExecutionConfig(BaseModel):
    """Realistic fill simulation parameters for paper trading orders."""
    latency_ms: int = Field(default=100, ge=0, description="Simulated order placement latency in milliseconds")
    slippage_bps: float = Field(default=2.0, ge=0.0, description="Simulated execution slippage in basis points")
    partial_fills_enabled: bool = Field(default=False, description="Whether orders can partially fill")
    fill_ratio: float = Field(default=1.0, ge=0.1, le=1.0, description="Portion of order filled on first match")


class PaperAccount(BaseModel):
    """Virtual paper account tracking virtual cash, margin, and marked-to-market balances."""
    account_id: str
    name: str = "Primary Paper Account"
    initial_balance: Decimal = Decimal("100000.00")
    current_cash: Decimal = Decimal("100000.00")
    margin_used: Decimal = Decimal("0.00")
    portfolio_value: Decimal = Decimal("100000.00")
    currency: str = "USD"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaperTradingSession(BaseModel):
    """Active live paper trading session for a quantitative strategy."""
    session_id: str
    strategy_id: str
    account_id: str
    status: PaperTradingSessionStatus = PaperTradingSessionStatus.INITIALIZED
    execution_config: PaperOrderExecutionConfig = Field(default_factory=PaperOrderExecutionConfig)
    symbols: list[str] = Field(default_factory=lambda: ["AAPL"])
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stopped_at: datetime | None = None
    total_trades: int = 0
    winning_trades: int = 0
    realized_pnl: Decimal = Decimal("0.00")
    unrealized_pnl: Decimal = Decimal("0.00")
    peak_portfolio_value: Decimal = Decimal("100000.00")
    max_drawdown_pct: float = 0.0


class PaperTradingGateStatus(BaseModel):
    """Evaluation of Stage 5 (PAPER_TRADING) criteria for advancing to Stage 6 (HUMAN_APPROVAL)."""
    session_id: str
    strategy_id: str
    days_active: int
    required_days: int = 14
    trades_count: int
    required_trades: int = 30
    current_drawdown_pct: float
    max_allowed_drawdown_pct: float = 10.0
    eligible_for_promotion: bool
    requirements_met: list[str] = Field(default_factory=list)
    requirements_pending: list[str] = Field(default_factory=list)
