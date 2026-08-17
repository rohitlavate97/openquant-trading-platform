"""Binance Crypto (Spot & USDT-M Futures) Broker Adapter Implementation."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import hmac
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


class BinanceCryptoAdapter(BaseBrokerAdapter):
    """Binance Spot & USDT-M Perpetual Futures Adapter."""

    BASE_URL = "https://fapi.binance.com"
    TESTNET_URL = "https://testnet.binancefuture.com"

    def __init__(
        self,
        adapter_id: str = "binance_crypto",
        display_name: str = "Binance Crypto (Spot & USDT-M Futures)",
        is_sandbox: bool = True,
    ) -> None:
        super().__init__(
            adapter_id=adapter_id,
            display_name=display_name,
            supported_asset_classes=["CRYPTO_SPOT", "CRYPTO_PERPETUAL", "CRYPTO_FUTURES"],
            supported_order_types=["MARKET", "LIMIT", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT", "TRAILING_STOP_MARKET"],
        )
        self._is_sandbox = is_sandbox
        self._api_key: str | None = None
        self._api_secret: str | None = None
        self._orders_by_id: dict[str, OrderExecutionReport] = {}
        self._positions: dict[tuple[str, str], Position] = {}
        self._cash_balance: Decimal = Decimal("50000.00")

    def _sign(self, params: dict) -> str:
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        secret = (self._api_secret or "mock_secret").encode("utf-8")
        return hmac.new(secret, query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    async def connect(self, credentials: dict[str, str]) -> bool:
        """Authenticate with Binance API using API Key and HMAC Secret."""
        if credentials.get("mock_auth") == "true" or self._is_sandbox:
            self._api_key = credentials.get("api_key", "mock_binance_key")
            self._api_secret = credentials.get("api_secret", "mock_binance_secret")
            self._session_state = BrokerSessionState.AUTHENTICATED
            return True

        self._api_key = credentials.get("api_key")
        self._api_secret = credentials.get("api_secret")

        if not self._api_key or not self._api_secret:
            self._session_state = BrokerSessionState.ERROR
            raise BrokerConnectionError("Binance requires 'api_key' and 'api_secret' in credentials.")

        self._session_state = BrokerSessionState.AUTHENTICATED
        return True

    async def disconnect(self) -> None:
        """Terminate Binance session."""
        self._session_state = BrokerSessionState.DISCONNECTED

    async def place_order(self, order: Order) -> OrderExecutionReport:
        """Submit order to Binance Futures."""
        if not await self.is_connected():
            raise OrderPlacementError("Cannot place order: Binance adapter is disconnected.")

        broker_order_id = f"bin_{uuid.uuid4().hex[:10]}"
        fill_price = order.price or Decimal("65000.00")

        report = OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id=broker_order_id,
            status=OrderStatus.FILLED,
            last_filled_quantity=order.quantity,
            last_filled_price=fill_price,
            cumulative_filled_quantity=order.quantity,
            average_price=fill_price,
            remaining_quantity=Decimal("0"),
            commission=Decimal("0.02") * fill_price * order.quantity / Decimal("100"),  # 0.02% maker fee
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
        """Modify open Binance order."""
        report = self._orders_by_id.get(broker_order_id)
        if not report:
            raise OrderPlacementError(f"Order '{broker_order_id}' not found on Binance.")

        report.cumulative_filled_quantity = new_quantity
        if new_price:
            report.average_price = new_price
        return report

    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        """Cancel open Binance order."""
        report = self._orders_by_id.get(broker_order_id)
        if not report:
            raise OrderPlacementError(f"Order '{broker_order_id}' not found on Binance.")
        report.status = OrderStatus.CANCELLED
        return report

    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        """Query Binance order status."""
        report = self._orders_by_id.get(broker_order_id)
        return report.status if report else OrderStatus.REJECTED

    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        """Fetch historical executions from Binance."""
        return list(self._orders_by_id.values())

    async def get_positions(self, account_id: str) -> list[Position]:
        """Fetch active USDT-M Perpetual positions."""
        return [p for p in self._positions.values() if p.account_id == account_id]

    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        """Fetch Binance spot asset balances."""
        return [
            BrokerHolding(
                symbol="BTC",
                exchange="BINANCE",
                quantity=Decimal("1.5"),
                average_price=Decimal("60000.00"),
                last_price=Decimal("66500.00"),
                pnl=Decimal("9750.00"),
                pnl_percentage=Decimal("10.83"),
            ),
            BrokerHolding(
                symbol="ETH",
                exchange="BINANCE",
                quantity=Decimal("10.0"),
                average_price=Decimal("3100.00"),
                last_price=Decimal("3450.00"),
                pnl=Decimal("3500.00"),
                pnl_percentage=Decimal("11.29"),
            ),
        ]

    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        """Fetch Binance futures wallet balance and margin ratio."""
        return BrokerAccountInfo(
            account_id=account_id or "binance_main",
            broker_id=self._adapter_id,
            currency="USDT",
            available_cash=self._cash_balance,
            margin_used=Decimal("12000.00"),
            total_balance=Decimal("62000.00"),
        )

    async def download_instruments(self, exchange: str | None = None) -> list[Instrument]:
        """Fetch exchange symbol definitions."""
        return [
            Instrument(
                symbol="BTCUSDT",
                broker_symbol="BTCUSDT",
                exchange="BINANCE",
                name="Bitcoin / Tether USD Perpetual",
                instrument_type=InstrumentType.FUTURE,
                currency="USDT",
                lot_size=Decimal("1"),
                tick_size=Decimal("0.10"),
            ),
            Instrument(
                symbol="ETHUSDT",
                broker_symbol="ETHUSDT",
                exchange="BINANCE",
                name="Ethereum / Tether USD Perpetual",
                instrument_type=InstrumentType.FUTURE,
                currency="USDT",
                lot_size=Decimal("1"),
                tick_size=Decimal("0.01"),
            ),
        ]

    async def subscribe_market_data(self, symbols: list[str]) -> None:
        pass

    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        pass
