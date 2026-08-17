"""Domain port for Portfolio Management and Performance Analytics Engine."""

from abc import ABC, abstractmethod
from openquant.domain.models.portfolio import (
    AssetAllocationItem,
    PortfolioPerformanceSnapshot,
    PortfolioPosition,
    PortfolioSummary,
)


class IPortfolioAnalyticsEngine(ABC):
    """Port defining multi-account position aggregation, mark-to-market PnL, allocation, and drawdown metrics."""

    @abstractmethod
    async def get_portfolio_summary(
        self,
        account_id: str = "acc_main",
    ) -> PortfolioSummary:
        """Calculate aggregate portfolio NAV, cash balance, margin used, realized/unrealized PnL, and drawdown."""
        pass

    @abstractmethod
    async def get_active_positions(
        self,
        account_id: str = "acc_main",
    ) -> list[PortfolioPosition]:
        """Fetch all mark-to-market valued active positions with percentage allocations."""
        pass

    @abstractmethod
    async def get_asset_allocation(
        self,
        account_id: str = "acc_main",
    ) -> list[AssetAllocationItem]:
        """Compute portfolio exposure percentages grouped by symbol and asset category."""
        pass

    @abstractmethod
    async def get_performance_snapshots(
        self,
        account_id: str = "acc_main",
        days: int = 30,
    ) -> list[PortfolioPerformanceSnapshot]:
        """Retrieve historical equity and drawdown time-series snapshots."""
        pass
