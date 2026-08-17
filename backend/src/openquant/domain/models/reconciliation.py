"""Domain models for State Reconciliation Engine & Mismatch Auto-Halt Guard (Rule 5)."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field


class ReconciliationSeverity(StrEnum):
    """Severity classification for detected state discrepancies."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL_MISMATCH = "CRITICAL_MISMATCH"


class ReconciliationStatus(StrEnum):
    """Overall outcome status of a reconciliation evaluation."""
    CLEAN = "CLEAN"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    HALTED_ON_DISCREPANCY = "HALTED_ON_DISCREPANCY"


class PositionDiscrepancyType(StrEnum):
    """Categorization of position discrepancies between OMS and Broker."""
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PHANTOM_INTERNAL = "PHANTOM_INTERNAL"
    PHANTOM_BROKER = "PHANTOM_BROKER"
    PRICE_MISMATCH = "PRICE_MISMATCH"


class PositionDiscrepancy(BaseModel):
    """Granular comparison discrepancy for an individual asset position."""
    symbol: str
    internal_quantity: Decimal
    broker_quantity: Decimal
    quantity_diff: Decimal
    internal_avg_price: Decimal = Decimal("0.00")
    broker_avg_price: Decimal = Decimal("0.00")
    price_diff: Decimal = Decimal("0.00")
    discrepancy_type: PositionDiscrepancyType
    severity: ReconciliationSeverity = ReconciliationSeverity.WARNING


class CashDiscrepancy(BaseModel):
    """Cash balance discrepancy between Internal OMS ledger and Broker cash actuals."""
    internal_cash: Decimal
    broker_cash: Decimal
    cash_diff: Decimal
    diff_pct: float
    severity: ReconciliationSeverity = ReconciliationSeverity.WARNING


class OrderDiscrepancy(BaseModel):
    """Pending or completed order state discrepancy between OMS and Broker order book."""
    order_id: str
    symbol: str
    internal_status: str
    broker_status: str
    discrepancy_type: str = "STATUS_MISMATCH"


class ReconciliationReport(BaseModel):
    """Immutable audit report of a full account state reconciliation run."""
    report_id: str
    account_id: str
    broker_id: str = "paper_broker"
    status: ReconciliationStatus = ReconciliationStatus.CLEAN
    position_discrepancies: list[PositionDiscrepancy] = Field(default_factory=list)
    cash_discrepancy: CashDiscrepancy | None = None
    order_discrepancies: list[OrderDiscrepancy] = Field(default_factory=list)
    auto_halt_triggered: bool = False
    halt_reason: str | None = None
    reconciled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
