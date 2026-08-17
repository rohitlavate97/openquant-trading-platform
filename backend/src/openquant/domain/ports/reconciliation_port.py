"""Domain Port for State Reconciliation Engine & Auto-Halt Guard."""

from abc import ABC, abstractmethod
from openquant.domain.models.reconciliation import ReconciliationReport


class IReconciliationEngine(ABC):
    """Port defining OMS vs Broker state reconciliation and discrepancy detection operations."""

    @abstractmethod
    async def reconcile_account(
        self,
        account_id: str,
        broker_id: str = "paper_broker",
    ) -> ReconciliationReport:
        """Reconcile internal OMS positions, cash, and orders against live broker actuals."""
        pass

    @abstractmethod
    async def reconcile_all_accounts(self) -> list[ReconciliationReport]:
        """Reconcile all active trading accounts against their respective brokers."""
        pass

    @abstractmethod
    async def sync_positions_from_broker(
        self,
        account_id: str,
        broker_id: str = "paper_broker",
    ) -> ReconciliationReport:
        """Force synchronize internal OMS positions with broker actuals."""
        pass

    @abstractmethod
    async def get_latest_reports(self, limit: int = 50) -> list[ReconciliationReport]:
        """Retrieve recent reconciliation audit reports."""
        pass

    @abstractmethod
    async def get_report(self, report_id: str) -> ReconciliationReport | None:
        """Retrieve specific reconciliation audit report."""
        pass
