"""Order Management System (OMS) Application Service governing order lifecycle, idempotency, and position tracking."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field

from openquant.domain.models.order import (
    Order,
    OrderRequest,
    OrderStatus,
    OrderSide,
    OrderType,
    OrderExecutionReport,
)
from openquant.domain.models.position import Position, PositionSide
from openquant.domain.exceptions import (
    OrderPlacementError,
    OrderCancellationError,
    StaleMarketDataError,
    BrokerAdapterNotFoundError,
)
from openquant.domain.ports.repositories import IOrderRepository, IPositionRepository
from openquant.adapters.repositories.in_memory_oms_repo import order_repository, position_repository
from openquant.adapters.brokers.registry import adapter_registry, BrokerAdapterRegistry
from openquant.application.services.market_data_service import market_data_service, MarketDataService
from openquant.application.services.streaming_service import streaming_broadcaster, StreamingBroadcasterService
from openquant.application.services.audit_service import audit_log_service, AuditLogService

logger = logging.getLogger("openquant.oms")


class PositionReconciliationItem(BaseModel):
    """Reconciliation status for an individual position."""
    symbol: str
    internal_quantity: Decimal
    broker_quantity: Decimal
    quantity_delta: Decimal
    is_reconciled: bool
    status: str


class PositionReconciliationReport(BaseModel):
    """Aggregate position reconciliation report comparing OMS database vs broker actuals."""
    account_id: str
    broker_id: str
    is_fully_reconciled: bool
    discrepancy_count: int
    items: list[PositionReconciliationItem]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrderManagementService:
    """Core OMS Service enforcing strict idempotency, pre-trade checks, and position reconciliation."""

    def __init__(
        self,
        order_repo: IOrderRepository = order_repository,
        pos_repo: IPositionRepository = position_repository,
        broker_reg: BrokerAdapterRegistry = adapter_registry,
        mkt_service: MarketDataService = market_data_service,
        broadcaster: StreamingBroadcasterService = streaming_broadcaster,
        audit: AuditLogService = audit_log_service,
    ) -> None:
        self._order_repo = order_repo
        self._pos_repo = pos_repo
        self._broker_reg = broker_reg
        self._mkt_service = mkt_service
        self._broadcaster = broadcaster
        self._audit = audit

    async def submit_order(self, request: OrderRequest, actor_id: str = "system") -> Order:
        """Process inbound order request with strict idempotency and pre-trade validations."""
        # 1. Strict Idempotency Check (Non-Negotiable Rule 8)
        existing_order = await self._order_repo.get_by_idempotency_key(
            request.idempotency_key, request.account_id
        )
        if existing_order:
            logger.info(
                f"Idempotent order duplicate detected: key '{request.idempotency_key}' (Order ID: {existing_order.order_id}). Returning existing order without re-executing."
            )
            return existing_order

        # 2. Pre-Trade Staleness Hard Stop (Non-Negotiable Rule 7: 3000ms limit)
        await self._mkt_service.assert_not_stale(request.symbol)

        # 3. Synchronous Pre-Trade Risk Checks (Non-Negotiable Rule 2: Hard-Stop Evaluation)
        from openquant.application.services.risk_service import risk_service
        await risk_service.evaluate_pre_trade(request)

        # 4. Retrieve target Broker Adapter
        adapter = self._broker_reg.get(request.broker_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{request.broker_id}' is not registered.")

        # 4. Instantiate Order in PENDING_SUBMISSION state
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        order = Order(
            order_id=order_id,
            idempotency_key=request.idempotency_key,
            strategy_id=request.strategy_id,
            account_id=request.account_id,
            broker_id=request.broker_id,
            symbol=request.symbol.upper(),
            side=request.side,
            order_type=request.order_type,
            status=OrderStatus.PENDING_SUBMISSION,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            tag=request.tag,
            created_at=now,
            updated_at=now,
        )

        # Persist initial order
        await self._order_repo.save(order)

        # Record audit event
        await self._audit.log_event(
            event_type="ORDER_SUBMITTED",
            actor_id=actor_id,
            entity_type="ORDER",
            entity_id=order.order_id,
            action="SUBMIT",
            payload={
                "idempotency_key": order.idempotency_key,
                "account_id": order.account_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": str(order.quantity),
                "order_type": order.order_type.value,
                "broker_id": order.broker_id,
            },
        )

        # 5. Dispatch order to Broker Adapter
        try:
            report = await adapter.place_order(order)
            await self._process_execution_report(order, report)
        except Exception as e:
            logger.error(f"Broker order dispatch error for order {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            order.rejection_reason = str(e)
            order.updated_at = datetime.now(timezone.utc)
            await self._order_repo.save(order)
            raise OrderPlacementError(f"Failed to place order with broker: {str(e)}")

        return order

    async def _process_execution_report(self, order: Order, report: OrderExecutionReport) -> None:
        """Update order lifecycle state, reconcile position, and broadcast execution report."""
        order.broker_order_id = report.broker_order_id
        order.status = report.status
        order.filled_quantity = report.cumulative_filled_quantity
        order.average_fill_price = report.average_price
        order.rejection_reason = report.rejection_reason
        order.updated_at = report.timestamp

        await self._order_repo.save(order)

        # If fills occurred, update internal position
        if report.cumulative_filled_quantity > 0:
            await self._update_position_from_fill(order, report)

        # Broadcast live execution update to WebSockets
        await self._broadcaster.broadcast_execution_report(report, order.account_id)

    async def _update_position_from_fill(self, order: Order, report: OrderExecutionReport) -> None:
        """Update position state, average entry price, and realized PnL on fill."""
        pos = await self._pos_repo.get_position(order.account_id, order.symbol)
        now = datetime.now(timezone.utc)
        fill_qty = report.last_filled_quantity if report.last_filled_quantity > 0 else report.cumulative_filled_quantity
        fill_price = report.average_price

        if pos is None:
            # Create brand new position
            side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
            pos = Position(
                position_id=f"pos_{uuid.uuid4().hex[:8]}",
                account_id=order.account_id,
                strategy_id=order.strategy_id,
                broker_id=order.broker_id,
                symbol=order.symbol,
                side=side,
                quantity=fill_qty,
                entry_price=fill_price,
                current_price=fill_price,
                unrealized_pnl=Decimal("0"),
                realized_pnl=Decimal("0"),
                updated_at=now,
            )
        else:
            # Update existing position
            if (pos.side == PositionSide.LONG and order.side == OrderSide.BUY) or \
               (pos.side == PositionSide.SHORT and order.side == OrderSide.SELL):
                # Increasing position size: compute weighted average entry price
                new_qty = pos.quantity + fill_qty
                if new_qty > 0:
                    pos.entry_price = ((pos.quantity * pos.entry_price) + (fill_qty * fill_price)) / new_qty
                pos.quantity = new_qty
                pos.current_price = fill_price
                pos.update_market_price(fill_price)
            else:
                # Reducing or flipping position: compute realized PnL
                realized = Decimal("0")
                if pos.side == PositionSide.LONG:
                    realized = (fill_price - pos.entry_price) * fill_qty
                elif pos.side == PositionSide.SHORT:
                    realized = (pos.entry_price - fill_price) * fill_qty

                pos.realized_pnl += realized
                remaining_qty = pos.quantity - fill_qty

                if remaining_qty > 0:
                    pos.quantity = remaining_qty
                    pos.current_price = fill_price
                    pos.update_market_price(fill_price)
                elif remaining_qty == 0:
                    pos.quantity = Decimal("0")
                    pos.side = PositionSide.FLAT
                    pos.unrealized_pnl = Decimal("0")
                else:
                    # Flipped position
                    pos.side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
                    pos.quantity = abs(remaining_qty)
                    pos.entry_price = fill_price
                    pos.current_price = fill_price
                    pos.unrealized_pnl = Decimal("0")

            pos.updated_at = now

        await self._pos_repo.save(pos)

    async def cancel_order(self, order_id: str, actor_id: str = "system") -> Order:
        """Cancel an open order with broker and update lifecycle state."""
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise OrderCancellationError(f"Order '{order_id}' not found.")

        if order.is_terminal:
            logger.info(f"Order '{order_id}' is already in terminal state '{order.status.value}'.")
            return order

        adapter = self._broker_reg.get(order.broker_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker '{order.broker_id}' not available for cancellation.")

        if order.broker_order_id:
            try:
                report = await adapter.cancel_order(order.broker_order_id)
                order.status = report.status
            except Exception as e:
                logger.warning(f"Broker cancel failed for order {order_id}: {e}")
                order.status = OrderStatus.CANCELLED
        else:
            order.status = OrderStatus.CANCELLED

        order.updated_at = datetime.now(timezone.utc)
        await self._order_repo.save(order)

        await self._audit.log_event(
            event_type="ORDER_CANCELLED",
            actor_id=actor_id,
            entity_type="ORDER",
            entity_id=order.order_id,
            action="CANCEL",
            payload={"order_id": order.order_id, "account_id": order.account_id},
        )

        return order

    async def get_order(self, order_id: str) -> Order | None:
        """Get order by ID."""
        return await self._order_repo.get_by_id(order_id)

    async def list_orders(self, account_id: str | None = None) -> list[Order]:
        """List all orders."""
        if hasattr(self._order_repo, "list_all"):
            return await self._order_repo.list_all(account_id)
        if account_id:
            return await self._order_repo.list_open_orders(account_id)
        return []

    async def list_positions(self, account_id: str = "acc_main") -> list[Position]:
        """List active positions for account."""
        positions = await self._pos_repo.list_positions(account_id)

        # Update latest market price from live market data feed
        for p in positions:
            tick = await self._mkt_service.get_latest_tick(p.symbol)
            if tick:
                p.update_market_price(tick.last_price)
                await self._pos_repo.save(p)

        return positions

    async def reconcile_positions(
        self,
        account_id: str,
        broker_id: str,
        actor_id: str = "system",
    ) -> PositionReconciliationReport:
        """Continuous Reconciliation Engine: Compare internal OMS position actuals against Broker."""
        adapter = self._broker_reg.get(broker_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker '{broker_id}' not found for reconciliation.")

        # 1. Fetch internal DB positions
        internal_positions = {p.symbol.upper(): p for p in await self._pos_repo.list_positions(account_id)}

        # 2. Fetch broker actual positions
        broker_positions_list = await adapter.get_positions(account_id)
        broker_positions = {p.symbol.upper(): p for p in broker_positions_list}

        all_symbols = set(internal_positions.keys()).union(set(broker_positions.keys()))
        reconciliation_items: list[PositionReconciliationItem] = []
        discrepancies = 0

        for sym in all_symbols:
            int_qty = internal_positions[sym].quantity if sym in internal_positions else Decimal("0")
            brok_qty = broker_positions[sym].quantity if sym in broker_positions else Decimal("0")
            delta = abs(int_qty - brok_qty)
            is_matched = delta == Decimal("0")

            if not is_matched:
                discrepancies += 1

            reconciliation_items.append(
                PositionReconciliationItem(
                    symbol=sym,
                    internal_quantity=int_qty,
                    broker_quantity=brok_qty,
                    quantity_delta=delta,
                    is_reconciled=is_matched,
                    status="MATCHED" if is_matched else "MISMATCH_DETECTED",
                )
            )

        report = PositionReconciliationReport(
            account_id=account_id,
            broker_id=broker_id,
            is_fully_reconciled=(discrepancies == 0),
            discrepancy_count=discrepancies,
            items=reconciliation_items,
        )

        # Record audit log
        await self._audit.log_event(
            event_type="POSITION_RECONCILIATION_COMPLETED",
            actor_id=actor_id,
            entity_type="POSITION",
            entity_id=f"rec_{account_id}_{broker_id}",
            action="RECONCILE",
            payload={
                "account_id": account_id,
                "broker_id": broker_id,
                "is_fully_reconciled": report.is_fully_reconciled,
                "discrepancy_count": discrepancies,
            },
        )

        return report


# Global OMS Service singleton
order_service = OrderManagementService()
