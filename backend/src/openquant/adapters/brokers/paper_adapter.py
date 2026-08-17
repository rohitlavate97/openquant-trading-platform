"""High-Fidelity Paper Trading Broker Adapter for sandbox validation and simulation."""

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from openquant.adapters.brokers.base import BaseBrokerAdapter
from openquant.domain.models.order import (
    Order,
    OrderExecutionReport,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from openquant.domain.models.position import Position, PositionSide
from openquant.domain.models.market_data import Tick, Instrument, InstrumentType
from openquant.domain.models.broker import (
    BrokerAccountInfo,
    BrokerHolding,
    BrokerSessionState,
)


class PaperBrokerAdapter(BaseBrokerAdapter):
    """Simulated Paper Broker Adapter for backtest execution and paper trading stages."""

    def __init__(
        self,
        adapter_id: str = "paper_broker",
        display_name: str = "OpenQuant Paper Engine",
        initial_cash: Decimal = Decimal("100000.00"),
        slippage_bps: Decimal = Decimal("5"),  # 5 basis points = 0.05%
    ) -> None:
        super().__init__(
            adapter_id=adapter_id,
            display_name=display_name,
            supported_asset_classes=["EQUITY", "FUTURE", "OPTION", "CRYPTO"],
            supported_order_types=["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        )
        self._initial_cash = initial_cash
        self._available_cash = initial_cash
        self._slippage_bps = slippage_bps
        self._orders: dict[str, Order] = {}
        self._positions: dict[str, Position] = {}  # symbol -> Position
        self._holdings: dict[str, BrokerHolding] = {}
        self._subscribed_symbols: set[str] = set()
        self._last_prices: dict[str, Decimal] = {
            "AAPL": Decimal("185.50"),
            "MSFT": Decimal("420.00"),
            "NVDA": Decimal("130.00"),
            "RELIANCE": Decimal("2950.00"),
            "INFY": Decimal("1550.00"),
        }
        # Paper adapter is self-certified for paper sandbox
        self.mark_certified(audit_report=None, live_eligible=False)

    async def connect(self, credentials: dict[str, str]) -> bool:
        self._session_state = BrokerSessionState.CONNECTED
        await asyncio.sleep(0.01)  # Simulate network handshake
        self._session_state = BrokerSessionState.AUTHENTICATED
        return True

    async def disconnect(self) -> None:
        self._session_state = BrokerSessionState.DISCONNECTED

    def set_last_price(self, symbol: str, price: Decimal) -> None:
        """Inject current market price for testing or simulated ticks."""
        self._last_prices[symbol] = price

    async def place_order(self, order: Order) -> OrderExecutionReport:
        broker_order_id = f"pap_ord_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)

        # Look up price or default
        ref_price = self._last_prices.get(order.symbol, Decimal("100.00"))
        if order.order_type == OrderType.LIMIT and order.price is not None:
            exec_price = order.price
        else:
            # Apply slippage
            slippage_factor = (Decimal("1") + (self._slippage_bps / Decimal("10000"))) if order.side == OrderSide.BUY else (Decimal("1") - (self._slippage_bps / Decimal("10000")))
            exec_price = (ref_price * slippage_factor).quantize(Decimal("0.01"))

        # For market and matching limit orders, fill immediately in paper sandbox
        filled_qty = order.quantity
        order_cost = exec_price * filled_qty

        # Validate cash for BUY
        if order.side == OrderSide.BUY and self._available_cash < order_cost:
            report = OrderExecutionReport(
                order_id=order.order_id,
                broker_order_id=broker_order_id,
                status=OrderStatus.REJECTED,
                last_filled_quantity=Decimal("0"),
                last_filled_price=Decimal("0"),
                cumulative_filled_quantity=Decimal("0"),
                average_price=Decimal("0"),
                remaining_quantity=order.quantity,
                rejection_reason="Insufficient paper funds",
                timestamp=now,
            )
            await self._emit_order_update(report)
            return report

        # Update cash
        if order.side == OrderSide.BUY:
            self._available_cash -= order_cost
        else:
            self._available_cash += order_cost

        # Update or create Position
        existing_pos = self._positions.get(order.symbol)
        if not existing_pos:
            new_pos_side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
            self._positions[order.symbol] = Position(
                position_id=f"pos_{order.symbol.lower()}",
                account_id=order.account_id,
                strategy_id=order.strategy_id,
                broker_id=self._adapter_id,
                symbol=order.symbol,
                side=new_pos_side,
                quantity=filled_qty,
                entry_price=exec_price,
                current_price=exec_price,
            )
        else:
            # Reconcile existing position
            if (existing_pos.side == PositionSide.LONG and order.side == OrderSide.BUY) or (
                existing_pos.side == PositionSide.SHORT and order.side == OrderSide.SELL
            ):
                total_qty = existing_pos.quantity + filled_qty
                avg_price = ((existing_pos.entry_price * existing_pos.quantity) + (exec_price * filled_qty)) / total_qty
                existing_pos.quantity = total_qty
                existing_pos.entry_price = avg_price.quantize(Decimal("0.01"))
            else:
                # Reducing or closing position
                if filled_qty >= existing_pos.quantity:
                    # Flipped or flat
                    rem = filled_qty - existing_pos.quantity
                    if rem == Decimal("0"):
                        existing_pos.side = PositionSide.FLAT
                        existing_pos.quantity = Decimal("0")
                    else:
                        existing_pos.side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
                        existing_pos.quantity = rem
                        existing_pos.entry_price = exec_price
                else:
                    existing_pos.quantity -= filled_qty

        # Store order
        order.broker_order_id = broker_order_id
        order.status = OrderStatus.FILLED
        order.filled_quantity = filled_qty
        order.average_fill_price = exec_price
        order.updated_at = now
        self._orders[broker_order_id] = order

        report = OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id=broker_order_id,
            status=OrderStatus.FILLED,
            last_filled_quantity=filled_qty,
            last_filled_price=exec_price,
            cumulative_filled_quantity=filled_qty,
            average_price=exec_price,
            remaining_quantity=Decimal("0"),
            timestamp=now,
        )
        await self._emit_order_update(report)
        return report

    async def modify_order(
        self,
        broker_order_id: str,
        new_quantity: Decimal,
        new_price: Decimal | None = None,
    ) -> OrderExecutionReport:
        order = self._orders.get(broker_order_id)
        if not order or order.status != OrderStatus.OPEN:
            return OrderExecutionReport(
                order_id=order.order_id if order else "unknown",
                broker_order_id=broker_order_id,
                status=OrderStatus.REJECTED,
                last_filled_quantity=Decimal("0"),
                last_filled_price=Decimal("0"),
                cumulative_filled_quantity=Decimal("0"),
                average_price=Decimal("0"),
                remaining_quantity=Decimal("0"),
                rejection_reason="Order cannot be modified in current state",
            )
        order.quantity = new_quantity
        if new_price:
            order.price = new_price
        return OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id=broker_order_id,
            status=OrderStatus.OPEN,
            last_filled_quantity=Decimal("0"),
            last_filled_price=Decimal("0"),
            cumulative_filled_quantity=order.filled_quantity,
            average_price=order.average_fill_price or Decimal("0"),
            remaining_quantity=order.quantity - order.filled_quantity,
        )

    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        order = self._orders.get(broker_order_id)
        if not order:
            return OrderExecutionReport(
                order_id="unknown",
                broker_order_id=broker_order_id,
                status=OrderStatus.REJECTED,
                last_filled_quantity=Decimal("0"),
                last_filled_price=Decimal("0"),
                cumulative_filled_quantity=Decimal("0"),
                average_price=Decimal("0"),
                remaining_quantity=Decimal("0"),
                rejection_reason="Order not found",
            )
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(timezone.utc)
        return OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id=broker_order_id,
            status=OrderStatus.CANCELLED,
            last_filled_quantity=Decimal("0"),
            last_filled_price=Decimal("0"),
            cumulative_filled_quantity=order.filled_quantity,
            average_price=order.average_fill_price or Decimal("0"),
            remaining_quantity=Decimal("0"),
        )

    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        order = self._orders.get(broker_order_id)
        return order.status if order else OrderStatus.REJECTED

    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        return [
            OrderExecutionReport(
                order_id=o.order_id,
                broker_order_id=o.broker_order_id or "unknown",
                status=o.status,
                last_filled_quantity=Decimal("0"),
                last_filled_price=Decimal("0"),
                cumulative_filled_quantity=o.filled_quantity,
                average_price=o.average_fill_price or Decimal("0"),
                remaining_quantity=o.quantity - o.filled_quantity,
                timestamp=o.updated_at,
            )
            for o in self._orders.values()
            if o.account_id == account_id
        ]

    async def get_positions(self, account_id: str) -> list[Position]:
        return [p for p in self._positions.values() if p.account_id == account_id and p.quantity > Decimal("0")]

    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        return list(self._holdings.values())

    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        # Calculate total portfolio value
        positions_val = sum(
            (p.quantity * self._last_prices.get(p.symbol, p.entry_price) for p in self._positions.values()),
            Decimal("0"),
        )
        total_balance = self._available_cash + positions_val
        return BrokerAccountInfo(
            account_id=account_id,
            broker_id=self._adapter_id,
            currency="USD",
            total_balance=total_balance.quantize(Decimal("0.01")),
            available_cash=self._available_cash.quantize(Decimal("0.01")),
            margin_used=positions_val.quantize(Decimal("0.01")),
            collateral=Decimal("0"),
        )

    async def download_instruments(self, exchange: str | None = None) -> list[Instrument]:
        return [
            Instrument(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", instrument_type=InstrumentType.EQUITY, tick_size=Decimal("0.01"), lot_size=1),
            Instrument(symbol="MSFT", name="Microsoft Corp.", exchange="NASDAQ", instrument_type=InstrumentType.EQUITY, tick_size=Decimal("0.01"), lot_size=1),
            Instrument(symbol="NVDA", name="NVIDIA Corp.", exchange="NASDAQ", instrument_type=InstrumentType.EQUITY, tick_size=Decimal("0.01"), lot_size=1),
            Instrument(symbol="RELIANCE", name="Reliance Industries Ltd.", exchange="NSE", instrument_type=InstrumentType.EQUITY, tick_size=Decimal("0.05"), lot_size=1),
            Instrument(symbol="INFY", name="Infosys Ltd.", exchange="NSE", instrument_type=InstrumentType.EQUITY, tick_size=Decimal("0.05"), lot_size=1),
        ]

    async def subscribe_market_data(self, symbols: list[str]) -> None:
        self._subscribed_symbols.update(symbols)

    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        self._subscribed_symbols.difference_update(symbols)
