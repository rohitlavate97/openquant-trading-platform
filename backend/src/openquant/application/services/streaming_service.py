"""Application Service orchestrating real-time WebSocket stream broadcasts."""

from decimal import Decimal
from typing import Any
from openquant.domain.models.market_data import Tick
from openquant.domain.models.order import OrderExecutionReport
from openquant.interfaces.api.v1.websocket.connection_manager import (
    market_data_ws_manager,
    order_stream_ws_manager,
    telemetry_ws_manager,
)


class StreamingBroadcasterService:
    """Dispatches low-latency domain events to subscribed WebSocket channels."""

    def __init__(
        self,
        market_ws=market_data_ws_manager,
        order_ws=order_stream_ws_manager,
        telemetry_ws=telemetry_ws_manager,
    ) -> None:
        self._market_ws = market_ws
        self._order_ws = order_ws
        self._telemetry_ws = telemetry_ws

    async def broadcast_tick(self, tick: Tick) -> int:
        """Broadcast live market tick to symbol-specific and global tick channels."""
        payload = {
            "type": "TICK",
            "symbol": tick.symbol,
            "exchange": tick.exchange,
            "last_price": str(tick.last_price),
            "last_quantity": str(tick.last_quantity),
            "bid_price": str(tick.bid_price) if tick.bid_price else None,
            "ask_price": str(tick.ask_price) if tick.ask_price else None,
            "volume": tick.volume,
            "timestamp": tick.timestamp.isoformat(),
        }
        # Broadcast to specific symbol topic e.g. "ticks:AAPL" and "ticks:ALL"
        count1 = await self._market_ws.broadcast_to_channel(f"ticks:{tick.symbol}", payload)
        count2 = await self._market_ws.broadcast_to_channel("ticks:ALL", payload)
        return count1 + count2

    async def broadcast_execution_report(self, report: OrderExecutionReport, account_id: str = "acc_main") -> int:
        """Broadcast real-time order fill/status update to user account channel."""
        payload = {
            "type": "ORDER_EXECUTION",
            "order_id": report.order_id,
            "broker_order_id": report.broker_order_id,
            "execution_id": report.execution_id,
            "status": report.status.value,
            "filled_quantity": str(report.cumulative_filled_quantity),
            "average_price": str(report.average_price),
            "remaining_quantity": str(report.remaining_quantity),
            "rejection_reason": report.rejection_reason,
            "timestamp": report.timestamp.isoformat(),
        }
        count1 = await self._order_ws.broadcast_to_channel(f"orders:{account_id}", payload)
        count2 = await self._order_ws.broadcast_to_channel("orders:ALL", payload)
        return count1 + count2

    async def broadcast_telemetry(self, event_type: str, data: dict[str, Any]) -> int:
        """Broadcast system health, risk threshold alert, or kill switch status."""
        payload = {
            "type": event_type,
            "data": data,
        }
        return await self._telemetry_ws.broadcast_global(payload)

    def get_streaming_stats(self) -> dict[str, Any]:
        """Aggregate connection statistics across all streaming domains."""
        return {
            "market_data": self._market_ws.get_stats(),
            "order_stream": self._order_ws.get_stats(),
            "telemetry": self._telemetry_ws.get_stats(),
        }


# Global streaming broadcaster singleton instance
streaming_broadcaster = StreamingBroadcasterService()
