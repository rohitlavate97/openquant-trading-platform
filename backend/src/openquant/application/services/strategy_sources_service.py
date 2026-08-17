"""Application Service coordinating External Strategy Sources (TradingView, MT5, Google Sheets)."""

import logging
from decimal import Decimal
from typing import Any

from openquant.domain.models.strategy_sources import (
    TradingViewWebhookPayload,
    TradingViewWebhookResult,
    MT5BridgeCommand,
    MT5BridgeMessage,
    MT5BridgeStatus,
    SheetsParseResult,
)
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType, TimeInForce
from openquant.domain.ports.strategy_sources_port import (
    ITradingViewWebhookHandler,
    IMT5BridgeAdapter,
    IStructuredSheetsParser,
)
from openquant.adapters.sources.tradingview_webhook import (
    tradingview_webhook_handler,
)
from openquant.adapters.sources.mt5_bridge import (
    mt5_bridge_adapter,
)
from openquant.adapters.sources.sheets_parser import (
    structured_sheets_parser,
)
from openquant.application.services.order_service import order_service, OrderManagementService
from openquant.application.services.audit_service import audit_log_service, AuditLogService

logger = logging.getLogger(__name__)


class StrategySourcesService:
    """Application Service managing external webhook alerts, socket bridges, and spreadsheet parsers."""

    def __init__(
        self,
        tv_handler: ITradingViewWebhookHandler | None = None,
        mt5_bridge: IMT5BridgeAdapter | None = None,
        sheets_parser: IStructuredSheetsParser | None = None,
        oms: OrderManagementService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._tv_handler = tv_handler or tradingview_webhook_handler
        self._mt5_bridge = mt5_bridge or mt5_bridge_adapter
        self._sheets_parser = sheets_parser or structured_sheets_parser
        self._oms = oms or order_service
        self._audit = audit or audit_log_service

    async def handle_tradingview_webhook(
        self,
        payload: TradingViewWebhookPayload,
        secret_key: str | None = None,
    ) -> TradingViewWebhookResult:
        """Process an authenticated TradingView webhook alert with replay protection."""
        return await self._tv_handler.verify_and_process_webhook(payload, secret_key)

    async def get_mt5_status(self) -> MT5BridgeStatus:
        """Retrieve telemetry health status of the MT5 bridge."""
        return await self._mt5_bridge.get_status()

    async def dispatch_mt5_command(self, command: MT5BridgeCommand, actor_id: str = "system") -> dict[str, Any]:
        """Dispatch an outbound trade command to MT5 EA."""
        result = await self._mt5_bridge.dispatch_command(command)
        await self._audit.log_event(
            event_type="MT5_COMMAND_DISPATCHED",
            actor_id=actor_id,
            entity_type="MT5_BRIDGE",
            entity_id=command.command_id,
            action="DISPATCH",
            payload={"action": command.action, "symbol": command.symbol, "volume": float(command.volume)},
        )
        return result

    async def process_mt5_message(self, message: MT5BridgeMessage) -> dict[str, Any]:
        """Process inbound heartbeat or telemetry from MT5 EA."""
        return await self._mt5_bridge.process_inbound_message(message)

    def parse_sheets_csv(self, content: str) -> SheetsParseResult:
        """Parse and validate raw spreadsheet CSV signals."""
        return self._sheets_parser.parse_csv_content(content)

    async def execute_sheets_orders(
        self,
        orders: list[dict[str, Any]],
        account_id: str = "acc_main",
        actor_id: str = "system",
    ) -> list[str]:
        """Execute a batch of validated spreadsheet orders through OMS."""
        executed_order_ids: list[str] = []
        for ord_data in orders:
            try:
                side = OrderSide.BUY if ord_data.get("side", "").upper() == "BUY" else OrderSide.SELL
                req = OrderRequest(
                    account_id=account_id,
                    broker_id=ord_data.get("broker_id", "paper_broker"),
                    strategy_id=ord_data.get("strategy_tag", "sheets_batch"),
                    symbol=ord_data["symbol"].upper(),
                    side=side,
                    order_type=OrderType.LIMIT if ord_data.get("limit_price") else OrderType.MARKET,
                    time_in_force=TimeInForce.GTC,
                    quantity=Decimal(str(ord_data["quantity"])),
                    price=Decimal(str(ord_data["limit_price"])) if ord_data.get("limit_price") else None,
                    idempotency_key=f"sheets_{account_id}_{ord_data['symbol']}_{ord_data['quantity']}_{len(executed_order_ids)}",
                )
                order = await self._oms.submit_order(req)
                executed_order_ids.append(order.order_id)
            except Exception as e:
                logger.error("Failed to execute sheets order: %s", e)

        await self._audit.log_event(
            event_type="SHEETS_BATCH_ORDER_EXECUTED",
            actor_id=actor_id,
            entity_type="ORDER_BATCH",
            entity_id=f"batch_{len(executed_order_ids)}",
            action="EXECUTE_BATCH",
            payload={"count": len(executed_order_ids), "order_ids": executed_order_ids},
        )
        return executed_order_ids


# Global singleton strategy sources service
strategy_sources_service = StrategySourcesService()
