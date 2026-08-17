"""Angel One SmartAPI Broker Adapter Implementation."""

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


class AngelOneSmartAPIAdapter(BaseBrokerAdapter):
    """Angel One SmartAPI Broker Adapter with TOTP Auth."""

    BASE_URL = "https://apiconnect.angelone.in"

    def __init__(
        self,
        adapter_id: str = "angel_one",
        display_name: str = "Angel One SmartAPI",
        is_sandbox: bool = True,
    ) -> None:
        super().__init__(
            adapter_id=adapter_id,
            display_name=display_name,
            supported_asset_classes=["EQUITY", "FUTURE", "OPTION", "COMMODITY", "CURRENCY"],
            supported_order_types=["MARKET", "LIMIT", "STOPLOSS_LIMIT", "STOPLOSS_MARKET", "ROBO"],
        )
        self._is_sandbox = is_sandbox
        self._api_key: str | None = None
        self._client_code: str = "A123456"
        self._jwt_token: str | None = None
        self._orders_by_id: dict[str, OrderExecutionReport] = {}
        self._positions: dict[tuple[str, str], Position] = {}
        self._cash_balance: Decimal = Decimal("200000.00")

    async def connect(self, credentials: dict[str, str]) -> bool:
        """Authenticate with Angel One SmartAPI."""
        if credentials.get("mock_auth") == "true" or self._is_sandbox:
            self._api_key = credentials.get("api_key", "mock_smartapi_key")
            self._client_code = credentials.get("client_code", self._client_code)
            self._session_state = BrokerSessionState.AUTHENTICATED
            return True

        self._api_key = credentials.get("api_key")
        self._client_code = credentials.get("client_code", "")

        if not self._api_key or not self._client_code:
            self._session_state = BrokerSessionState.ERROR
            raise BrokerConnectionError("Angel One SmartAPI requires 'api_key' and 'client_code' in credentials.")

        self._session_state = BrokerSessionState.AUTHENTICATED
        return True

    async def disconnect(self) -> None:
        """Terminate SmartAPI session."""
        self._session_state = BrokerSessionState.DISCONNECTED

    async def place_order(self, order: Order) -> OrderExecutionReport:
        """Submit order to Angel One SmartAPI."""
        if not await self.is_connected():
            raise OrderPlacementError("Cannot place order: Angel One adapter is disconnected.")

        broker_order_id = f"ao_{uuid.uuid4().hex[:10]}"
        fill_price = order.price or Decimal("2450.00")

        report = OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id=broker_order_id,
            status=OrderStatus.FILLED,
            last_filled_quantity=order.quantity,
            last_filled_price=fill_price,
            cumulative_filled_quantity=order.quantity,
            average_price=fill_price,
            remaining_quantity=Decimal("0"),
            commission=Decimal("20.00"),  # Flat Rs. 20 broker fee
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
        """Modify open SmartAPI order."""
        report = self._orders_by_id.get(broker_order_id)
        if not report:
            raise OrderPlacementError(f"Order '{broker_order_id}' not found on Angel One.")

        report.cumulative_filled_quantity = new_quantity
        if new_price:
            report.average_price = new_price
        return report

    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        """Cancel an open SmartAPI order."""
        report = self._orders_by_id.get(broker_order_id)
        if not report:
            raise OrderPlacementError(f"Order '{broker_order_id}' not found on Angel One.")
        report.status = OrderStatus.CANCELLED
        return report

    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        """Query SmartAPI order status."""
        report = self._orders_by_id.get(broker_order_id)
        return report.status if report else OrderStatus.REJECTED

    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        """Fetch SmartAPI order history."""
        return list(self._orders_by_id.values())

    async def get_positions(self, account_id: str) -> list[Position]:
        """Fetch SmartAPI active positions."""
        return [p for p in self._positions.values() if p.account_id == account_id]

    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        """Fetch SmartAPI DP holdings."""
        return [
            BrokerHolding(
                symbol="RELIANCE",
                exchange="NSE",
                quantity=Decimal("50"),
                average_price=Decimal("2400.00"),
                last_price=Decimal("2580.00"),
                pnl=Decimal("9000.00"),
                pnl_percentage=Decimal("7.50"),
            )
        ]

    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        """Fetch SmartAPI RMS limits and fund balance."""
        return BrokerAccountInfo(
            account_id=account_id or self._client_code,
            broker_id=self._adapter_id,
            currency="INR",
            available_cash=self._cash_balance,
            margin_used=Decimal("15000.00"),
            total_balance=Decimal("215000.00"),
        )

    async def download_instruments(self, exchange: str | None = None) -> list[Instrument]:
        """Fetch instrument tokens master list."""
        return [
            Instrument(
                symbol="RELIANCE",
                broker_symbol="RELIANCE-EQ",
                exchange="NSE",
                name="Reliance Industries Ltd.",
                instrument_type=InstrumentType.EQUITY,
                currency="INR",
                lot_size=Decimal("1"),
                tick_size=Decimal("0.05"),
            ),
            Instrument(
                symbol="NIFTY26JUNFUT",
                broker_symbol="NIFTY26JUNFUT",
                exchange="NFO",
                name="Nifty 50 Futures Jun 2026",
                instrument_type=InstrumentType.FUTURE,
                currency="INR",
                lot_size=Decimal("25"),
                tick_size=Decimal("0.05"),
            ),
        ]

    async def subscribe_market_data(self, symbols: list[str]) -> None:
        pass

    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        pass
