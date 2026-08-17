"""Base Broker Adapter implementation providing common lifecycle, tick streaming, and validation safeguards."""

import asyncio
from abc import abstractmethod
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
    BrokerSecurityAuditReport,
)
from openquant.domain.ports.broker_adapter import IBrokerAdapter
from openquant.domain.exceptions import BrokerAdapterUncertifiedError


class BaseBrokerAdapter(IBrokerAdapter):
    """Abstract base class for broker adapters with standard safety guard rails and queues."""

    def __init__(
        self,
        adapter_id: str,
        display_name: str,
        supported_asset_classes: list[str] | None = None,
        supported_order_types: list[str] | None = None,
    ) -> None:
        self._adapter_id = adapter_id
        self._display_name = display_name
        self._supported_asset_classes = supported_asset_classes or ["EQUITY", "FUTURE", "OPTION"]
        self._supported_order_types = supported_order_types or ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
        self._certified: bool = False
        self._live_eligible: bool = False
        self._session_state: BrokerSessionState = BrokerSessionState.DISCONNECTED
        self._tick_queue: asyncio.Queue[Tick] = asyncio.Queue(maxsize=10000)
        self._order_update_queue: asyncio.Queue[OrderExecutionReport] = asyncio.Queue(maxsize=10000)
        self._audit_report: BrokerSecurityAuditReport | None = None

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

    @property
    def session_state(self) -> BrokerSessionState:
        return self._session_state

    @property
    def metadata(self) -> BrokerAdapterMetadata:
        return BrokerAdapterMetadata(
            adapter_id=self._adapter_id,
            display_name=self._display_name,
            supported_asset_classes=self._supported_asset_classes,
            supported_order_types=self._supported_order_types,
            is_certified=self._certified,
            is_live_trading_eligible=self._live_eligible,
            certification_report=self._audit_report,
        )

    def mark_certified(self, audit_report: BrokerSecurityAuditReport | None = None, live_eligible: bool = False) -> None:
        """Mark adapter as having passed sandbox integration and security audit."""
        self._certified = True
        self._live_eligible = live_eligible
        self._audit_report = audit_report

    def verify_live_eligible(self) -> None:
        """Raise error if adapter is not certified for live trading."""
        if not self._live_eligible:
            raise BrokerAdapterUncertifiedError(
                f"Broker adapter '{self._adapter_id}' is not certified for Live Trading. "
                "All adapters must pass sandbox validation and security audit."
            )

    async def is_connected(self) -> bool:
        return self._session_state in (BrokerSessionState.CONNECTED, BrokerSessionState.AUTHENTICATED)

    async def _emit_tick(self, tick: Tick) -> None:
        """Internal helper to push tick into streaming queue without blocking."""
        try:
            self._tick_queue.put_nowait(tick)
        except asyncio.QueueFull:
            # Drop oldest tick to preserve fresh real-time throughput
            try:
                self._tick_queue.get_nowait()
                self._tick_queue.put_nowait(tick)
            except Exception:
                pass

    async def _emit_order_update(self, report: OrderExecutionReport) -> None:
        """Internal helper to push order update into execution queue."""
        await self._order_update_queue.put(report)

    async def stream_ticks(self) -> AsyncIterator[Tick]:
        """Yield live real-time market data ticks from queue."""
        while True:
            tick = await self._tick_queue.get()
            yield tick

    async def stream_order_updates(self) -> AsyncIterator[OrderExecutionReport]:
        """Yield real-time order status execution reports."""
        while True:
            report = await self._order_update_queue.get()
            yield report

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
    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        pass

    @abstractmethod
    async def get_positions(self, account_id: str) -> list[Position]:
        pass

    @abstractmethod
    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        pass

    @abstractmethod
    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        pass

    @abstractmethod
    async def download_instruments(self, exchange: str | None = None) -> list[Instrument]:
        pass

    @abstractmethod
    async def subscribe_market_data(self, symbols: list[str]) -> None:
        pass

    @abstractmethod
    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        pass
