"""Unit tests for Broker Adapter Registry and Certification Enforcement."""

from decimal import Decimal
from typing import AsyncIterator
import pytest

from openquant.domain.models.order import Order, OrderExecutionReport, OrderStatus
from openquant.domain.models.position import Position
from openquant.domain.models.market_data import Tick
from openquant.domain.models.broker import BrokerAccountInfo, BrokerHolding
from openquant.adapters.brokers.base import BaseBrokerAdapter
from openquant.adapters.brokers.registry import BrokerAdapterRegistry
from openquant.domain.exceptions import BrokerAdapterUncertifiedError


class MockBrokerAdapter(BaseBrokerAdapter):
    """Concrete mock adapter for testing registry behavior."""

    async def connect(self, credentials: dict[str, str]) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def place_order(self, order: Order) -> OrderExecutionReport:
        return OrderExecutionReport(
            order_id=order.order_id,
            broker_order_id="mock_b_123",
            execution_id="mock_exec_1",
            status=OrderStatus.SUBMITTED,
            last_filled_quantity=Decimal("0"),
            last_filled_price=Decimal("0"),
            cumulative_filled_quantity=Decimal("0"),
            average_price=Decimal("0"),
        )

    async def modify_order(
        self, broker_order_id: str, new_quantity: Decimal, new_price: Decimal | None = None
    ) -> OrderExecutionReport:
        raise NotImplementedError

    async def cancel_order(self, broker_order_id: str) -> OrderExecutionReport:
        raise NotImplementedError

    async def get_order_status(self, broker_order_id: str) -> OrderStatus:
        return OrderStatus.OPEN

    async def get_positions(self, account_id: str) -> list[Position]:
        return []

    async def get_funds(self, account_id: str) -> BrokerAccountInfo:
        return BrokerAccountInfo(
            account_id=account_id,
            broker_id="mock_broker",
            total_balance=Decimal("100000.00"),
            available_cash=Decimal("100000.00"),
        )

    async def get_holdings(self, account_id: str) -> list[BrokerHolding]:
        return []

    async def get_order_history(self, account_id: str) -> list[OrderExecutionReport]:
        return []

    async def download_instruments(self, exchange: str | None = None) -> list:
        return []

    async def subscribe_market_data(self, symbols: list[str]) -> None:
        pass

    async def unsubscribe_market_data(self, symbols: list[str]) -> None:
        pass

    async def stream_ticks(self) -> AsyncIterator[Tick]:
        return
        yield  # make it a generator



def test_broker_registry_and_certification_guard():
    """Verify uncertified broker adapter throws error when checked for live trading."""
    registry = BrokerAdapterRegistry()
    adapter = MockBrokerAdapter(adapter_id="mock_broker", display_name="Mock Brokerage")

    assert adapter.is_certified is False
    assert adapter.is_live_trading_eligible is False

    # Attempting to verify live trading without certification raises error
    with pytest.raises(BrokerAdapterUncertifiedError):
        adapter.verify_live_eligible()

    registry.register(adapter)
    assert registry.get("mock_broker") == adapter

    # Certify adapter
    adapter.mark_certified(live_eligible=True)
    assert adapter.is_certified is True
    assert adapter.is_live_trading_eligible is True
    # Should now pass without raising
    adapter.verify_live_eligible()
