"""Unit tests for State Reconciliation Domain Models."""

from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.reconciliation import (
    ReconciliationSeverity,
    ReconciliationStatus,
    PositionDiscrepancyType,
    PositionDiscrepancy,
    CashDiscrepancy,
    ReconciliationReport,
)


def test_position_discrepancy_model():
    """Verify position discrepancy structure and severities."""
    disc = PositionDiscrepancy(
        symbol="AAPL",
        internal_quantity=Decimal("100"),
        broker_quantity=Decimal("150"),
        quantity_diff=Decimal("50"),
        internal_avg_price=Decimal("180.00"),
        broker_avg_price=Decimal("181.00"),
        price_diff=Decimal("1.00"),
        discrepancy_type=PositionDiscrepancyType.QUANTITY_MISMATCH,
        severity=ReconciliationSeverity.CRITICAL_MISMATCH,
    )
    assert disc.symbol == "AAPL"
    assert disc.quantity_diff == Decimal("50")
    assert disc.severity == ReconciliationSeverity.CRITICAL_MISMATCH


def test_reconciliation_report_model():
    """Verify ReconciliationReport attributes and defaults."""
    report = ReconciliationReport(
        report_id="recon_1",
        account_id="acc_main",
        status=ReconciliationStatus.CLEAN,
        position_discrepancies=[],
        auto_halt_triggered=False,
    )
    assert report.report_id == "recon_1"
    assert report.status == ReconciliationStatus.CLEAN
    assert report.auto_halt_triggered is False
