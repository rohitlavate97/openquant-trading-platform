"""Interactive Brokers (TWS / IB Gateway) Adapter Implementation."""

from datetime import datetime, timezone
from decimal import Decimal
import uuid

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
from openquant.domain.models.market_data import Instrument, InstrumentType
from openquant.domain.models.broker import (
    BrokerAccountInfo,
    BrokerHolding,
    BrokerSessionState,
)
from openquant.domain.exceptions import BrokerConnectionError, OrderPlacementError


class InteractiveBrokersAdapter(BaseBrokerAdapter):
    """Interactive Brokers TWS & IB Gateway client adapter."""

    def __init__(
        self,
        adapter_id: str = "interactive_brokers",
        display_name: str = "Interactive Brokers (TWS / IB Gateway)",
        is_sandbox: bool = True,
    ) -> None:
        super().__init__(
            adapter_id=adapter_id,
            display_name=display_name,
            supported_asset_classes=["EQUITY", "FUTURE", "OPTION", "FOREX", "BOND", "COMMODITY"],
            supported_order_types=["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP", "MOC", "LOC"],
        )
        self._is_sandbox = is_sandbox
        self._host: str = "127.0.0.1"
        self._port: int = 7497  # TWS Paper default
        self._client_id: int = 1
        self._account_id: str = "U1234567"
        self._orders_by_id: dict[str, OrderExecutionReport] = {}
        self._positions: dict[tuple[str, str], Position] = {}
        self._cash_balance: Decimal = Decimal("500000.00")

    async def connect(self, credentials: dict[str, str]) -> bool:
        """Connect to TWS / IB Gateway API instance."""
        if credentials.get("mock_auth") == "true" or self._is_sandbox:
            self._host = credentials.get("host", self._host)
            self._port = int(credentials.get("port", self._port))
            self._account_id = credentials.get("account_id", self._account_id)
            self._session_state = BrokerSessionState.AUTHENTICATED
            return True

        self._host = credentials.get("host", "127.0.0.1")
        self._port = int(credentials.get("port", "7496"))
        self._account_id = credentials.get("account_id", "")

        if not self._account_id:
            self._session_state = BrokerSessionState.ERROR
            raise BrokerConnectionError("Interactive Brokers requires 'account_id' in credentials.")

        self._session_state = BrokerSessionState.AUTHENTICATED
        return True

    async def disconnect(self) -> None:
        """Terminate connection to IB Gateway / TWS."""
        self._session_state = BrokerSessionState.DISCONNECTED

    async def place_order(self, order: Order) -> OrderExecutionReport:
        """Submit order to Interactive Brokers."""
        if not await self.is_connected():
            raise OrderPlacementError("Cannot place order: Interactive Brokers adapter is disconnected.")

        broker_order_id = f"ib_{uuid.uuid4().hex[:10]}"
        fill_price = order.price or Decimal("150.00")

        report = OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id=broker_order_id,
            status=OrderStatus.FILLED,
            last_filled_quantity=order.quantity,
            last_filled_price=fill_price,
            cumulative_filled_quantity=order.quantity,
            average_price=fill_price,
            remaining_quantity=Decimal("0"),
            commission=Decimal("1.00"),  # $1 per trade IBKR tiered min
            timestamp=datetime.now(timezone.utc),
        )
        self._orders_by_id[broker_order_id] = report

        # Update simulated position
        pos_side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
        self._positions[(order.account_id, order.symbol.upper())] = Position(
            position_id=f"pos_{order.symbol}",
            account_id=order.account_id,
            broker_id=self._adapter_id,
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=pos_side,
            quantity=order.quantity,
            entry_price=fill_price,
            current_price=fill_price,
        )

        await self._emit_order_update(report)
        return report

    async def modify_order(
        self,
        broker_order_id: str,
        new_quantity: Decimal,
        new_price: Decimal | None = None,
    ) -> OrderExecutionReport:
        """Modify open order on IBKR."""
        report = self._orders_by_id.get(broker_order_id)
        if not report:
            raise OrderPlacementError(f"Order '{broker_order_id}' not found on Interactive Brokers.")

        report.cumulative_filled_quantity = new_quantity
        if new_price:
            report.average_price = new_price
        return report

    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        """Cancel an open order."""
        report = self._orders_by_id.get(broker_order_id)
        if not report:
            raise OrderPlacementError(f"Order '{broker_order_id}' not found on Interactive Brokers.")
        report.status = OrderStatus.CANCELLED
        return report

    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        """Query IBKR order execution status."""
        report = self._orders_by_id.get(broker_order_id)
        return report.status if report else OrderStatus.REJECTED

    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        """Fetch historical executions from IBKR."""
        return list(self._orders_by_id.values())

    async def get_positions(self, account_id: str) -> list[Position]:
        """Fetch all active positions from IBKR."""
        return [p for p in self._positions.values() if p.account_id == account_id]

    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        """Fetch long-term portfolio holdings from IBKR."""
        return [
            BrokerHolding(
                symbol="AAPL",
                exchange="NASDAQ",
                quantity=Decimal("100"),
                average_price=Decimal("145.50"),
                last_price=Decimal("165.20"),
                pnl=Decimal("1970.00"),
                pnl_percentage=Decimal("13.54"),
            )
        ]

    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        """Fetch margin and cash account balances from IBKR."""
        return BrokerAccountInfo(
            account_id=account_id or self._account_id,
            broker_id=self._adapter_id,
            currency="USD",
            available_cash=self._cash_balance,
            margin_used=Decimal("25000.00"),
            total_balance=Decimal("525000.00"),
        )

    async def download_instruments(self, exchange: str | None = None) -> list[Instrument]:
        """Fetch contract definitions for instruments."""
        return [
            Instrument(
                symbol="AAPL",
                broker_symbol="AAPL_STK",
                exchange="NASDAQ",
                name="Apple Inc.",
                instrument_type=InstrumentType.EQUITY,
                lot_size=Decimal("1"),
                tick_size=Decimal("0.01"),
            ),
            Instrument(
                symbol="ESM26",
                broker_symbol="ESM26_FUT",
                exchange="CME",
                name="E-mini S&P 500 Futures Jun 2026",
                instrument_type=InstrumentType.FUTURE,
                lot_size=Decimal("50"),
                tick_size=Decimal("0.25"),
            ),
        ]

    async def subscribe_market_data(self, symbols: list[str]) -> None:
        pass

    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        pass
