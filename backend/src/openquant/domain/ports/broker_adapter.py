"""Hexagonal Port: Abstract Broker Adapter Interface.

The single, unified port through which the OMS and Market Data Engine interact with brokers.
No component in the domain or application layer ever interacts with specific broker SDKs directly.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import AsyncIterator
from openquant.domain.models.order import Order, OrderExecutionReport, OrderStatus
from openquant.domain.models.position import Position
from openquant.domain.models.market_data import Tick, Instrument
from openquant.domain.models.broker import (
    BrokerAccountInfo,
    BrokerAdapterMetadata,
    BrokerHolding,
    BrokerSessionState,
)


class IBrokerAdapter(ABC):
    """Abstract interface defining the complete contract for all broker adapters."""

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique identifier for this broker adapter (e.g. 'paper_broker', 'zerodha')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable display name for the broker."""

    @property
    @abstractmethod
    def is_certified(self) -> bool:
        """Whether this adapter has completed sandbox integration validation and security audit."""

    @property
    @abstractmethod
    def is_live_trading_eligible(self) -> bool:
        """Whether this adapter is permitted for live capital routing."""

    @property
    @abstractmethod
    def session_state(self) -> BrokerSessionState:
        """Current lifecycle connection state of the adapter."""

    @property
    @abstractmethod
    def metadata(self) -> BrokerAdapterMetadata:
        """Capability metadata and supported order types / asset classes."""

    @abstractmethod
    async def connect(self, credentials: dict[str, str]) -> bool:
        """Authenticate and establish session/WebSocket connections with the broker."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully terminate broker sessions and subscriptions."""

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if broker session and real-time streams are currently active."""

    @abstractmethod
    async def place_order(self, order: Order) -> OrderExecutionReport:
        """Submit an order to the broker. Must be idempotent."""

    @abstractmethod
    async def modify_order(
        self,
        broker_order_id: str,
        new_quantity: Decimal,
        new_price: Decimal | None = None,
    ) -> OrderExecutionReport:
        """Modify an existing open order at the broker."""

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        """Cancel an open order at the broker."""

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        """Query current status of an order from the broker."""

    @abstractmethod
    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        """Fetch historical executed/cancelled orders from the broker."""

    @abstractmethod
    async def get_positions(self, account_id: str) -> list[Position]:
        """Fetch actual real-time positions held at the broker for reconciliation."""

    @abstractmethod
    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        """Fetch long-term portfolio holdings and equity deliveries."""

    @abstractmethod
    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        """Fetch available margin, cash, and collateral balance from broker."""

    @abstractmethod
    async def download_instruments(self, exchange: str | None = None) -> list[Instrument]:
        """Fetch tradable instruments catalog from broker."""

    @abstractmethod
    async def subscribe_market_data(self, symbols: list[str]) -> None:
        """Subscribe to live L1/tick feeds for the specified symbols."""

    @abstractmethod
    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        """Unsubscribe from live market data feeds."""

    @abstractmethod
    def stream_ticks(self) -> AsyncIterator[Tick]:
        """Yield live real-time market data ticks from the broker stream."""

    @abstractmethod
    def stream_order_updates(self) -> AsyncIterator[OrderExecutionReport]:
        """Yield real-time order status execution reports as they occur."""
