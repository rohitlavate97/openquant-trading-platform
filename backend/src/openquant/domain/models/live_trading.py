"""Domain models for Live Trading Mode, capital allocation, and preflight verification."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class LiveTradingState(StrEnum):
    """Lifecycle state of a live trading execution session."""
    IDLE = "IDLE"
    PREFLIGHT_CHECKING = "PREFLIGHT_CHECKING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    HALTED = "HALTED"
    TERMINATED = "TERMINATED"


class ScalingTier(StrEnum):
    """Gradual capital scaling tiers for live strategy deployment."""
    TIER_1_STARTER = "TIER_1_STARTER"         # 25% allocation
    TIER_2_INTERMEDIATE = "TIER_2_INTERMEDIATE" # 50% allocation
    TIER_3_FULL = "TIER_3_FULL"                 # 100% allocation

    @property
    def multiplier(self) -> Decimal:
        if self == ScalingTier.TIER_1_STARTER:
            return Decimal("0.25")
        if self == ScalingTier.TIER_2_INTERMEDIATE:
            return Decimal("0.50")
        return Decimal("1.00")


class LiveCapitalAllocation(BaseModel):
    """Capital controls and allocation parameters for a live strategy."""
    strategy_id: str
    broker_id: str
    account_id: str
    total_authorized_capital: Decimal = Field(default=Decimal("100000.00"))
    scaling_tier: ScalingTier = Field(default=ScalingTier.TIER_1_STARTER)
    max_order_notional: Decimal = Field(default=Decimal("10000.00"))
    margin_floor_buffer: Decimal = Field(default=Decimal("15000.00"))
    max_daily_loss: Decimal = Field(default=Decimal("3000.00"))
    max_drawdown_percent: Decimal = Field(default=Decimal("5.00"))

    @property
    def effective_allocated_capital(self) -> Decimal:
        """Calculate effective trading capital based on current scaling tier."""
        return self.total_authorized_capital * self.scaling_tier.multiplier


class LivePreflightCheckItem(BaseModel):
    """Individual verification check result in the live preflight checklist."""
    check_name: str
    passed: bool
    description: str
    details: dict[str, Any] = Field(default_factory=dict)
    is_blocking: bool = True


class LivePreflightReport(BaseModel):
    """Comprehensive readiness report evaluated before live execution authorization."""
    strategy_id: str
    broker_id: str
    account_id: str
    is_eligible: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checks: list[LivePreflightCheckItem] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)


class LiveStrategySession(BaseModel):
    """Active or historical live execution session entity."""
    session_id: str
    strategy_id: str
    strategy_name: str
    broker_id: str
    account_id: str
    allocation: LiveCapitalAllocation
    state: LiveTradingState = LiveTradingState.READY
    activated_by: str
    confirmed_by: str | None = None
    activated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deactivated_at: datetime | None = None
    realized_pnl: Decimal = Decimal("0.00")
    unrealized_pnl: Decimal = Decimal("0.00")
    live_orders_count: int = 0
    halt_reason: str | None = None
    preflight_report: LivePreflightReport | None = None
