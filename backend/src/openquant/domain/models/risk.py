from datetime import datetime, timezone
from enum import StrEnum
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class RiskCheckType(StrEnum):
    """Types of pre-trade risk checks enforced synchronously."""
    KILL_SWITCH = "KILL_SWITCH"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    MAX_POSITION_SIZE = "MAX_POSITION_SIZE"
    MAX_SINGLE_TRADE_RISK = "MAX_SINGLE_TRADE_RISK"
    RATE_LIMIT = "RATE_LIMIT"
    SELF_TRADE_PREVENTION = "SELF_TRADE_PREVENTION"
    MAX_OPEN_ORDERS_PER_SYMBOL = "MAX_OPEN_ORDERS_PER_SYMBOL"
    MARKET_DATA_FRESHNESS = "MARKET_DATA_FRESHNESS"
    LIVE_TRADING_PERMISSION = "LIVE_TRADING_PERMISSION"


class RiskSeverity(StrEnum):
    """Severity of a risk finding."""
    BLOCKING = "BLOCKING"  # Hard rejection - pre-trade blocking
    WARNING = "WARNING"    # Informational advisory


class KillSwitchLevel(StrEnum):
    """Scope of emergency trading halt."""
    GLOBAL = "GLOBAL"
    ACCOUNT = "ACCOUNT"
    STRATEGY = "STRATEGY"
    SYMBOL = "SYMBOL"


class KillSwitchState(BaseModel):
    """State of an emergency kill switch."""
    is_active: bool = False
    level: KillSwitchLevel = KillSwitchLevel.GLOBAL
    target_id: str | None = None
    activated_by: str | None = None
    activated_at: datetime | None = None
    reason: str | None = None
    positions_flattened: bool = False


class RiskLimitsConfig(BaseModel):
    """Non-negotiable pre-trade hard-stop risk parameters."""
    max_daily_loss_percent: float = Field(default=3.0, ge=0.1, le=50.0, description="Max daily loss limit %")
    max_drawdown_percent: float = Field(default=5.0, ge=0.5, le=50.0, description="Max peak drawdown %")
    max_single_trade_risk_percent: float = Field(default=1.0, ge=0.1, le=20.0, description="Max risk per single trade %")
    max_position_size_percent: float = Field(default=10.0, ge=0.5, le=100.0, description="Max position size %")
    max_orders_per_second: int = Field(default=10, ge=1, le=100, description="Order rate limit per sec")
    max_open_orders_per_symbol: int = Field(default=10, ge=1, le=100, description="Max open orders per symbol")
    self_trade_prevention: bool = Field(default=True, description="Enforce self-trade crossing prevention")
    kill_switch: KillSwitchState = Field(default_factory=KillSwitchState)


class RiskCheckResult(BaseModel):
    """Result of an individual risk rule evaluation."""
    check_type: RiskCheckType
    passed: bool
    severity: RiskSeverity = RiskSeverity.BLOCKING
    rule_name: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class RiskEvaluationResult(BaseModel):
    """Comprehensive evaluation aggregated across all pre-trade risk checks."""
    allowed: bool
    checks: list[RiskCheckResult] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create_approved(cls, checks: list[RiskCheckResult]) -> "RiskEvaluationResult":
        """Factory for an approved risk evaluation where all blocking checks passed."""
        return cls(allowed=True, checks=checks, rejection_reasons=[])

    @classmethod
    def create_rejected(cls, checks: list[RiskCheckResult]) -> "RiskEvaluationResult":
        """Factory for a rejected risk evaluation with collected reasons."""
        rejection_reasons = [
            c.message for c in checks if not c.passed and c.severity == RiskSeverity.BLOCKING
        ]
        return cls(allowed=False, checks=checks, rejection_reasons=rejection_reasons)
