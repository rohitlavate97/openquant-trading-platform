"""Domain models for pre-trade risk evaluation and kill switch management."""

from datetime import datetime, timezone
from enum import StrEnum
from decimal import Decimal
from pydantic import BaseModel, Field


class RiskCheckType(StrEnum):
    """Types of pre-trade risk checks enforced synchronously."""
    KILL_SWITCH = "KILL_SWITCH"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    MAX_POSITION_SIZE = "MAX_POSITION_SIZE"
    MAX_ORDER_VALUE = "MAX_ORDER_VALUE"
    MARGIN_REQUIREMENT = "MARGIN_REQUIREMENT"
    RATE_LIMIT = "RATE_LIMIT"
    MARKET_DATA_FRESHNESS = "MARKET_DATA_FRESHNESS"
    LIVE_TRADING_PERMISSION = "LIVE_TRADING_PERMISSION"


class RiskSeverity(StrEnum):
    """Severity of a risk finding."""
    BLOCKING = "BLOCKING"  # Hard rejection - cannot proceed
    WARNING = "WARNING"    # Informational / advisory only


class RiskCheckResult(BaseModel):
    """Result of an individual risk rule evaluation."""
    check_type: RiskCheckType
    passed: bool
    severity: RiskSeverity = RiskSeverity.BLOCKING
    rule_name: str
    message: str
    details: dict[str, str | float | int | bool] = Field(default_factory=dict)


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
