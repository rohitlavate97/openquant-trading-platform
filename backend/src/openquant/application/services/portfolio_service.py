"""Application Service coordinating Portfolio Management, Position Tracking, and OMS Close Orders."""

import uuid
from decimal import Decimal
from openquant.domain.models.portfolio import (
    AssetAllocationItem,
    PortfolioPerformanceSnapshot,
    PortfolioPosition,
    PortfolioSummary,
)
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType, TimeInForce
from openquant.domain.models.position import PositionSide
from openquant.domain.ports.portfolio_port import IPortfolioAnalyticsEngine
from openquant.adapters.portfolio.portfolio_analytics_engine import (
    portfolio_analytics_engine,
    PortfolioAnalyticsEngine,
)
from openquant.application.services.order_service import order_service, OrderManagementService
from openquant.application.services.audit_service import audit_log_service, AuditLogService


class PortfolioService:
    """Service managing multi-account position aggregation, mark-to-market PnL, allocation, and close execution."""

    def __init__(
        self,
        analytics_engine: IPortfolioAnalyticsEngine | None = None,
        oms: OrderManagementService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._engine = analytics_engine or portfolio_analytics_engine
        self._oms = oms or order_service
        self._audit = audit or audit_log_service

    async def get_summary(self, account_id: str = "acc_main") -> PortfolioSummary:
        """Fetch aggregated portfolio NAV, cash balance, and drawdown metrics."""
        return await self._engine.get_portfolio_summary(account_id)

    async def list_positions(self, account_id: str = "acc_main") -> list[PortfolioPosition]:
        """Fetch active positions with mark-to-market valuation and allocation weights."""
        return await self._engine.get_active_positions(account_id)

    async def get_allocation(self, account_id: str = "acc_main") -> list[AssetAllocationItem]:
        """Fetch portfolio asset allocation breakdown."""
        return await self._engine.get_asset_allocation(account_id)

    async def get_performance(
        self,
        account_id: str = "acc_main",
        days: int = 30,
    ) -> list[PortfolioPerformanceSnapshot]:
        """Fetch historical equity curve snapshots and drawdown time series."""
        return await self._engine.get_performance_snapshots(account_id, days)

    async def close_position(
        self,
        account_id: str,
        symbol: str,
        actor_id: str = "trader",
    ) -> str:
        """Submit an opposing market order through OMS to completely flatten a position."""
        positions = await self._engine.get_active_positions(account_id)
        target_pos = next((p for p in positions if p.symbol == symbol), None)
        if not target_pos:
            raise ValueError(f"No active position found for symbol '{symbol}' on account '{account_id}'.")

        close_side = OrderSide.SELL if target_pos.side == PositionSide.LONG else OrderSide.BUY

        req = OrderRequest(
            account_id=account_id,
            broker_id="paper_broker",
            strategy_id=target_pos.strategy_id or "manual_portfolio_close",
            symbol=symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            quantity=target_pos.quantity,
            idempotency_key=f"close_{symbol}_{uuid.uuid4().hex[:8]}",
        )

        res = await self._oms.submit_order(req)
        await self._audit.log_event(
            event_type="PORTFOLIO_POSITION_CLOSED",
            actor_id=actor_id,
            entity_type="PORTFOLIO_POSITION",
            entity_id=f"{account_id}:{symbol}",
            action="CLOSE_POSITION",
            payload={"symbol": symbol, "quantity": str(target_pos.quantity), "order_id": res.order_id},
        )
        return res.order_id


# Global singleton portfolio service
portfolio_service = PortfolioService()
