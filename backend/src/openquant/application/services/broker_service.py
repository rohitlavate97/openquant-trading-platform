"""Application Service managing Broker Adapter interactions and certification."""

from decimal import Decimal
from typing import Any
from openquant.domain.models.broker import (
    BrokerAccountInfo,
    BrokerAdapterMetadata,
    BrokerHolding,
    BrokerSecurityAuditReport,
)
from openquant.domain.models.position import Position
from openquant.domain.exceptions import BrokerAdapterNotFoundError
from openquant.adapters.brokers.registry import BrokerAdapterRegistry, broker_registry
from openquant.adapters.brokers.certification_harness import BrokerAdapterCertificationHarness
from openquant.application.services.secrets_service import secrets_service
from openquant.application.services.audit_service import audit_log_service


class BrokerService:
    """Orchestrates broker connections, portfolio introspection, and security certification."""

    def __init__(self, registry: BrokerAdapterRegistry = broker_registry) -> None:
        self._registry = registry

    def list_adapters(self) -> list[BrokerAdapterMetadata]:
        """List all registered broker adapters."""
        return self._registry.list_adapters()

    def get_adapter_metadata(self, adapter_id: str) -> BrokerAdapterMetadata:
        """Get capability and certification metadata for a specific adapter."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")
        return adapter.metadata

    async def connect_user_broker(self, adapter_id: str, user_id: str) -> bool:
        """Authenticate adapter session using encrypted credentials stored in vault."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")

        # In Paper broker or sandbox mock mode, empty credentials or mock is fine
        if adapter_id == "paper_broker":
            await adapter.connect({})
            await audit_log_service.log_event(
                event_type="BROKER_CONNECTED",
                actor_id=user_id,
                entity_type="BROKER",
                entity_id=adapter_id,
                action="SESSION_ESTABLISHED",
                payload={"adapter_id": adapter_id, "mode": "paper"},
            )
            return True

        # Fetch decrypted credentials from vault
        creds = await secrets_service.get_decrypted_broker_credentials(user_id, adapter_id)
        if not creds:
            # Fallback to sandbox mock if testing
            creds = {"mock_auth": "true"}

        connected = await adapter.connect(creds)
        await audit_log_service.log_event(
            event_type="BROKER_CONNECTED",
            actor_id=user_id,
            entity_type="BROKER",
            entity_id=adapter_id,
            action="SESSION_ESTABLISHED",
            payload={"adapter_id": adapter_id, "connected": connected},
        )
        return connected

    async def disconnect_broker(self, adapter_id: str, user_id: str = "system") -> None:
        """Terminate broker connection."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")
        await adapter.disconnect()
        await audit_log_service.log_event(
            event_type="BROKER_DISCONNECTED",
            actor_id=user_id,
            entity_type="BROKER",
            entity_id=adapter_id,
            action="SESSION_TERMINATED",
            payload={"adapter_id": adapter_id},
        )

    async def get_funds(self, adapter_id: str, account_id: str) -> BrokerAccountInfo:
        """Fetch real-time funds and margin from adapter."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")
        return await adapter.get_funds(account_id)

    async def get_positions(self, adapter_id: str, account_id: str) -> list[Position]:
        """Fetch actual real-time positions from adapter."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")
        return await adapter.get_positions(account_id)

    async def get_holdings(self, adapter_id: str, account_id: str) -> list[BrokerHolding]:
        """Fetch portfolio holdings from adapter."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")
        return await adapter.get_holdings(account_id)

    async def run_adapter_certification(
        self,
        adapter_id: str,
        certified_by: str,
    ) -> BrokerSecurityAuditReport:
        """Execute automated sandbox validation harness and security audit on adapter."""
        adapter = self._registry.get(adapter_id)
        if not adapter:
            raise BrokerAdapterNotFoundError(f"Broker adapter '{adapter_id}' not found.")

        report = await BrokerAdapterCertificationHarness.run_certification_audit(
            adapter=adapter,
            certified_by=certified_by,
        )

        await audit_log_service.log_event(
            event_type="BROKER_CERTIFICATION_AUDIT",
            actor_id=certified_by,
            entity_type="BROKER",
            entity_id=adapter_id,
            action="CERTIFICATION_EVALUATION",
            payload={
                "adapter_id": adapter_id,
                "is_certified": report.is_certified,
                "live_eligible": report.live_trading_eligible,
                "checks_passed": sum(1 for c in report.checks if c.passed),
                "total_checks": len(report.checks),
            },
            severity="INFO" if report.is_certified else "WARNING",
        )

        return report


# Global broker service singleton instance
broker_service = BrokerService()
