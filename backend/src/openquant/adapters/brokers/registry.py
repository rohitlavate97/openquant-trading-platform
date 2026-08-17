"""Broker Adapter Registry managing discovery, lifecycle, and certification."""

from openquant.domain.ports.broker_adapter import IBrokerAdapter
from openquant.domain.models.broker import BrokerAdapterMetadata
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.adapters.brokers.zerodha_adapter import ZerodhaKiteAdapter


class BrokerAdapterRegistry:
    """Central registry holding configured broker adapters and managing certification states."""

    def __init__(self) -> None:
        self._adapters: dict[str, IBrokerAdapter] = {}

    def register(self, adapter: IBrokerAdapter) -> None:
        """Register a broker adapter into the platform."""
        self._adapters[adapter.adapter_id] = adapter

    def get(self, adapter_id: str) -> IBrokerAdapter | None:
        """Retrieve adapter by ID."""
        return self._adapters.get(adapter_id)

    def list_adapters(self) -> list[BrokerAdapterMetadata]:
        """List metadata and certification status of all registered adapters."""
        return [adapter.metadata for adapter in self._adapters.values()]

    def list_certified_adapters(self) -> list[BrokerAdapterMetadata]:
        """List only adapters certified for live trading."""
        return [adapter.metadata for adapter in self._adapters.values() if adapter.is_live_trading_eligible]


def create_default_registry() -> BrokerAdapterRegistry:
    """Factory creating registry populated with standard first-party broker adapters."""
    registry = BrokerAdapterRegistry()
    registry.register(PaperBrokerAdapter())
    registry.register(ZerodhaKiteAdapter(is_sandbox=True))
    return registry


# Global default broker registry instance
broker_registry = create_default_registry()
adapter_registry = broker_registry

