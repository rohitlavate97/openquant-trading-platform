"""Base Broker Adapter implementation providing common lifecycle and validation safeguards."""

from abc import abstractmethod
from decimal import Decimal
from typing import AsyncIterator
from openquant.domain.models.order import Order, OrderExecutionReport, OrderStatus
from openquant.domain.models.position import Position
from openquant.domain.models.market_data import Tick
from openquant.domain.ports.broker_adapter import IBrokerAdapter
from openquant.domain.exceptions import BrokerAdapterUncertifiedError


class BaseBrokerAdapter(IBrokerAdapter):
    """Abstract base class for broker adapters with standard safety guard rails."""

    def __init__(self, adapter_id: str, display_name: str) -> None:
        self._adapter_id = adapter_id
        self._display_name = display_name
        self._certified: bool = False
        self._live_eligible: bool = False
        self._connected: bool = False

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def is_certified(self) -> bool:
        return self._certified

    @property
    def is_live_trading_eligible(self) -> bool:
        return self._live_eligible

    def mark_certified(self, live_eligible: bool = False) -> None:
        """Mark adapter as having passed sandbox integration and security audit."""
        self._certified = True
        self._live_eligible = live_eligible

    def verify_live_eligible(self) -> None:
        """Raise error if adapter is not certified for live trading."""
        if not self._live_eligible:
            raise BrokerAdapterUncertifiedError(
                f"Broker adapter '{self._adapter_id}' is not certified for Live Trading. "
                "All adapters must pass sandbox validation and security audit."
            )

    async def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def connect(self, credentials: dict[str, str]) -> bool:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def place_order(self, order: Order) -> OrderExecutionReport:
        pass

    @abstractmethod
    async def modify_order(
        self,
        broker_order_id: str,
        new_quantity: Decimal,
        new_price: Decimal | None = None,
    ) -> OrderExecutionReport:
        pass

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        pass

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        pass

    @abstractmethod
    async def get_positions(self, account_id: str) -> list[Position]:
        pass

    @abstractmethod
    async def get_funds(self, account_id: str) -> dict[str, Decimal]:
        pass

    @abstractmethod
    async def subscribe_market_data(self, symbols: list[str]) -> None:
        pass

    @abstractmethod
    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        pass

    @abstractmethod
    def stream_ticks(self) -> AsyncIterator[Tick]:
        pass
