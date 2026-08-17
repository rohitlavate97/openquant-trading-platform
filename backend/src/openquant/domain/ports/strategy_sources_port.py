"""Domain Ports for Additional Strategy Sources (TradingView, MT5, Structured Sheets)."""

from abc import ABC, abstractmethod
from typing import Any
from openquant.domain.models.strategy_sources import (
    TradingViewWebhookPayload,
    TradingViewWebhookResult,
    MT5BridgeCommand,
    MT5BridgeMessage,
    MT5BridgeStatus,
    SheetsParseResult,
    SheetsStrategyRow,
)


class ITradingViewWebhookHandler(ABC):
    """Port for verifying HMAC signatures, enforcing replay protection nonces, and submitting orders."""

    @abstractmethod
    async def verify_and_process_webhook(
        self,
        payload: TradingViewWebhookPayload,
        secret_key: str | None = None,
    ) -> TradingViewWebhookResult:
        """Verify HMAC signature & nonce TTL, then submit order via OMS."""
        pass


class IMT5BridgeAdapter(ABC):
    """Port defining ZeroMQ socket command dispatch and EA message ingestion for MT5."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish bridge sockets or simulated channels."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close active sockets."""
        pass

    @abstractmethod
    async def dispatch_command(self, command: MT5BridgeCommand) -> dict[str, Any]:
        """Send outbound order or modify command to connected MT5 EA."""
        pass

    @abstractmethod
    async def process_inbound_message(self, message: MT5BridgeMessage) -> dict[str, Any]:
        """Ingest tick, heartbeat, or execution report from MT5 EA."""
        pass

    @abstractmethod
    async def get_status(self) -> MT5BridgeStatus:
        """Get bridge health and connection telemetry."""
        pass


class IStructuredSheetsParser(ABC):
    """Port for parsing and validating CSV/Google Sheet order strategy rows."""

    @abstractmethod
    def parse_csv_content(self, content: str) -> SheetsParseResult:
        """Parse raw CSV content into typed strategy rows."""
        pass

    @abstractmethod
    def validate_row(self, row_data: dict[str, str], row_index: int) -> SheetsStrategyRow:
        """Validate an individual signal row against data rules."""
        pass
