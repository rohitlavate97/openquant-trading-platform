"""Broker Adapter Registry managing certified adapters and runtime routing."""

import logging
from openquant.domain.ports.broker_adapter import IBrokerAdapter

logger = logging.getLogger(__name__)


class BrokerAdapterRegistry:
    """Central registry for broker adapters, tracking certification and live trading eligibility."""

    def __init__(self) -> None:
        self._adapters: dict[str, IBrokerAdapter] = {}

    def register(self, adapter: IBrokerAdapter) -> None:
        """Register a broker adapter instance."""
        self._adapters[adapter.adapter_id] = adapter
        logger.info(
            "Registered broker adapter: id=%s display=%s certified=%s live_eligible=%s",
            adapter.adapter_id,
            adapter.display_name,
            adapter.is_certified,
            adapter.is_live_trading_eligible,
        )

    def get(self, adapter_id: str) -> IBrokerAdapter | None:
        """Retrieve registered adapter by identifier."""
        return self._adapters.get(adapter_id)

    def list_adapters(self) -> list[dict[str, str | bool]]:
        """List metadata for all registered broker adapters."""
        return [
            {
                "adapter_id": adapter.adapter_id,
                "display_name": adapter.display_name,
                "is_certified": adapter.is_certified,
                "is_live_trading_eligible": adapter.is_live_trading_eligible,
            }
            for adapter in self._adapters.values()
        ]


# Global adapter registry singleton
adapter_registry = BrokerAdapterRegistry()
