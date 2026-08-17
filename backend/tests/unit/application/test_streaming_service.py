"""Unit tests for WebSocket Connection Manager and Streaming Broadcaster Service."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from openquant.domain.models.market_data import Tick
from openquant.domain.models.order import OrderExecutionReport, OrderStatus
from openquant.interfaces.api.v1.websocket.connection_manager import WebSocketConnectionManager
from openquant.application.services.streaming_service import StreamingBroadcasterService


class DummyWebSocket:
    """Mock WebSocket for unit testing broadcasts."""

    def __init__(self) -> None:
        self.sent_messages: list[dict] = []
        self.accepted: bool = False
        self.closed: bool = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict) -> None:
        if self.closed:
            raise RuntimeError("WebSocket closed")
        self.sent_messages.append(data)


@pytest.mark.asyncio
async def test_websocket_connection_manager_lifecycle():
    """Verify connect, subscribe, broadcast, unsubscribe, and disconnect."""
    manager = WebSocketConnectionManager()
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()

    await manager.connect(ws1, "client_1", "user_1")
    await manager.connect(ws2, "client_2", "user_2")

    assert ws1.accepted is True
    assert manager.get_stats()["active_connections"] == 2

    # Subscribe ws1 to ticks:AAPL and ws2 to ticks:RELIANCE
    await manager.subscribe(ws1, ["ticks:AAPL", "ticks:ALL"])
    await manager.subscribe(ws2, ["ticks:RELIANCE", "ticks:ALL"])

    # Broadcast to ticks:AAPL (only ws1 should receive)
    delivered = await manager.broadcast_to_channel("ticks:AAPL", {"symbol": "AAPL", "price": 185.0})
    assert delivered == 1
    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 0

    # Broadcast to ticks:ALL (both should receive)
    delivered_all = await manager.broadcast_to_channel("ticks:ALL", {"msg": "broadcast"})
    assert delivered_all == 2
    assert len(ws1.sent_messages) == 2
    assert len(ws2.sent_messages) == 1

    # Unsubscribe ws1
    await manager.unsubscribe(ws1, ["ticks:AAPL"])
    delivered_after = await manager.broadcast_to_channel("ticks:AAPL", {"msg": "test"})
    assert delivered_after == 0

    # Disconnect
    await manager.disconnect(ws1)
    assert manager.get_stats()["active_connections"] == 1


@pytest.mark.asyncio
async def test_streaming_broadcaster_service():
    """Verify StreamingBroadcasterService packages and dispatches domain models."""
    market_ws = WebSocketConnectionManager()
    order_ws = WebSocketConnectionManager()
    telemetry_ws = WebSocketConnectionManager()

    broadcaster = StreamingBroadcasterService(market_ws=market_ws, order_ws=order_ws, telemetry_ws=telemetry_ws)

    ws_client = DummyWebSocket()
    await market_ws.connect(ws_client, "mkt_1", "usr_1")
    await market_ws.subscribe(ws_client, ["ticks:NVDA", "ticks:ALL"])

    tick = Tick(
        symbol="NVDA",
        exchange="NASDAQ",
        last_price=Decimal("128.50"),
        last_quantity=Decimal("100"),
        volume=500000,
        timestamp=datetime.now(timezone.utc),
    )

    delivered = await broadcaster.broadcast_tick(tick)
    assert delivered == 2  # Received via ticks:NVDA and ticks:ALL
    assert len(ws_client.sent_messages) == 2
    assert ws_client.sent_messages[0]["type"] == "TICK"
    assert ws_client.sent_messages[0]["symbol"] == "NVDA"
