"""Domain models for Multi-Broker Adapter Layer, Certification, and Holdings."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class BrokerSessionState(StrEnum):
    """Lifecycle connection state of a broker adapter session."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHENTICATED = "AUTHENTICATED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class BrokerSecurityAuditCheck(BaseModel):
    """Result of an individual security or sandbox validation check."""
    check_name: str
    passed: bool
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class BrokerSecurityAuditReport(BaseModel):
    """Comprehensive certification report for a broker adapter."""
    adapter_id: str
    is_certified: bool
    live_trading_eligible: bool
    audit_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    certified_by: str | None = None
    checks: list[BrokerSecurityAuditCheck] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)


class BrokerAdapterMetadata(BaseModel):
    """Static and dynamic capabilities of a broker adapter."""
    adapter_id: str
    display_name: str
    version: str = "1.0.0"
    supported_asset_classes: list[str] = Field(default_factory=lambda: ["EQUITY"])
    supported_order_types: list[str] = Field(default_factory=lambda: ["MARKET", "LIMIT"])
    is_certified: bool = False
    is_live_trading_eligible: bool = False
    certification_report: BrokerSecurityAuditReport | None = None


class BrokerAccountInfo(BaseModel):
    """Standardized funds and margin balance from broker."""
    account_id: str
    broker_id: str
    currency: str = "USD"
    total_balance: Decimal = Decimal("0")
    available_cash: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    collateral: Decimal = Decimal("0")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BrokerHolding(BaseModel):
    """Standardized long-term portfolio holding from broker."""
    symbol: str
    exchange: str
    quantity: Decimal
    average_price: Decimal
    last_price: Decimal = Decimal("0")
    pnl: Decimal = Decimal("0")
    pnl_percentage: Decimal = Decimal("0")
