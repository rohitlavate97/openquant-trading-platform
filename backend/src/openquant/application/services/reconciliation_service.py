"""Application Service managing State Reconciliation workflows and Rule 5 Auto-Halt Guard."""

import logging
from typing import Any

from openquant.domain.models.reconciliation import (
    ReconciliationReport,
    ReconciliationStatus,
)
from openquant.domain.ports.reconciliation_port import IReconciliationEngine
from openquant.adapters.reconciliation.state_reconciliation_engine import (
    state_reconciliation_engine,
)
from openquant.application.services.audit_service import AuditLogService, audit_log_service

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Application Service coordinating OMS vs Broker State Reconciliation and drift detection."""

    def __init__(
        self,
        engine: IReconciliationEngine | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._engine: IReconciliationEngine = engine or state_reconciliation_engine
        self._audit: AuditLogService = audit or audit_log_service

    async def reconcile_account(
        self,
        account_id: str,
        broker_id: str = "paper_broker",
        actor_id: str = "system",
    ) -> ReconciliationReport:
        """Run state reconciliation for a specific account."""
        report = await self._engine.reconcile_account(account_id=account_id, broker_id=broker_id)

        if report.auto_halt_triggered:
            await self._audit.log_event(
                event_type="RECONCILIATION_AUTO_HALT",
                actor_id=actor_id,
                entity_type="ACCOUNT",
                entity_id=account_id,
                action="HALT_ON_DISCREPANCY",
                payload={"report_id": report.report_id, "reason": report.halt_reason},
            )
        else:
            await self._audit.log_event(
                event_type="RECONCILIATION_RUN",
                actor_id=actor_id,
                entity_type="ACCOUNT",
                entity_id=account_id,
                action="RECONCILE",
                payload={"report_id": report.report_id, "status": report.status},
            )

        return report

    async def reconcile_all_accounts(self, actor_id: str = "system") -> list[ReconciliationReport]:
        """Run full state reconciliation across all active accounts."""
        reports = await self._engine.reconcile_all_accounts()
        return reports

    async def pre_order_reconciliation_check(self, account_id: str, symbol: str) -> bool:
        """Pre-order hook verifying account state is clean before order placement (Rule 5)."""
        report = await self._engine.reconcile_account(account_id=account_id)
        # Block order if this symbol has an active discrepancy or if account is halted
        if report.status == ReconciliationStatus.HALTED_ON_DISCREPANCY:
            return False
        discrepant_symbols = {d.symbol for d in report.position_discrepancies}
        return symbol not in discrepant_symbols

    async def sync_positions_from_broker(
        self,
        account_id: str,
        broker_id: str = "paper_broker",
        actor_id: str = "system",
    ) -> ReconciliationReport:
        """Force overwrite internal OMS positions with broker actuals."""
        report = await self._engine.sync_positions_from_broker(account_id=account_id, broker_id=broker_id)
        await self._audit.log_event(
            event_type="RECONCILIATION_FORCE_SYNC",
            actor_id=actor_id,
            entity_type="ACCOUNT",
            entity_id=account_id,
            action="SYNC_FROM_BROKER",
            payload={"report_id": report.report_id, "status": report.status},
        )
        return report

    async def get_latest_reports(self, limit: int = 50) -> list[ReconciliationReport]:
        """List historical reconciliation reports."""
        return await self._engine.get_latest_reports(limit=limit)

    async def get_report(self, report_id: str) -> ReconciliationReport | None:
        """Retrieve specific reconciliation report."""
        return await self._engine.get_report(report_id=report_id)


# Global singleton reconciliation service
reconciliation_service = ReconciliationService()
