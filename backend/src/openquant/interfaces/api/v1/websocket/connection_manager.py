"""WebSocket Connection Manager managing client lifecycles, channel subscriptions, and broadcasts."""

import asyncio
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("openquant.websocket")


class WebSocketConnectionManager:
    """Manages concurrent client WebSocket connections with channel-based topic subscriptions."""

    def __init__(self) -> None:
        # Client map: websocket -> metadata dict
        self._active_connections: dict[WebSocket, dict[str, Any]] = {}
        # Channel map: channel_name -> set[WebSocket]
        self._channel_subscriptions: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str) -> None:
        """Accept connection and register metadata."""
        await websocket.accept()
        async with self._lock:
            self._active_connections[websocket] = {
                "client_id": client_id,
                "user_id": user_id,
                "subscriptions": set(),
            }
        logger.info(f"WebSocket client connected: {client_id} (User: {user_id})")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection and clean up all topic subscriptions."""
        async with self._lock:
            if websocket in self._active_connections:
                subs = self._active_connections[websocket].get("subscriptions", set())
                for channel in subs:
                    if channel in self._channel_subscriptions:
                        self._channel_subscriptions[channel].discard(websocket)
                        if not self._channel_subscriptions[channel]:
                            del self._channel_subscriptions[channel]
                del self._active_connections[websocket]
        logger.info("WebSocket client disconnected.")

    async def subscribe(self, websocket: WebSocket, channels: list[str]) -> None:
        """Subscribe client to specific topics/channels."""
        async with self._lock:
            if websocket not in self._active_connections:
                return
            for ch in channels:
                self._active_connections[websocket]["subscriptions"].add(ch)
                if ch not in self._channel_subscriptions:
                    self._channel_subscriptions[ch] = set()
                self._channel_subscriptions[ch].add(websocket)

    async def unsubscribe(self, websocket: WebSocket, channels: list[str]) -> None:
        """Unsubscribe client from specific topics/channels."""
        async with self._lock:
            if websocket not in self._active_connections:
                return
            for ch in channels:
                self._active_connections[websocket]["subscriptions"].discard(ch)
                if ch in self._channel_subscriptions:
                    self._channel_subscriptions[ch].discard(websocket)
                    if not self._channel_subscriptions[ch]:
                        del self._channel_subscriptions[ch]

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send message directly to a single client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Error sending message to client: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_channel(self, channel: str, message: dict[str, Any]) -> int:
        """Broadcast payload to all clients subscribed to the channel."""
        async with self._lock:
            recipients = list(self._channel_subscriptions.get(channel, set()))

        if not recipients:
            return 0

        stale_clients = []
        delivered = 0
        for ws in recipients:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                stale_clients.append(ws)

        for ws in stale_clients:
            await self.disconnect(ws)

        return delivered

    async def broadcast_global(self, message: dict[str, Any]) -> int:
        """Broadcast payload to all connected clients."""
        async with self._lock:
            recipients = list(self._active_connections.keys())

        stale_clients = []
        delivered = 0
        for ws in recipients:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                stale_clients.append(ws)

        for ws in stale_clients:
            await self.disconnect(ws)

        return delivered

    def get_stats(self) -> dict[str, Any]:
        """Return active connection count and subscription stats."""
        return {
            "active_connections": len(self._active_connections),
            "channels_count": len(self._channel_subscriptions),
            "channels": {ch: len(subscribers) for ch, subscribers in self._channel_subscriptions.items()},
        }


# Global singleton connection managers for dedicated stream domains
market_data_ws_manager = WebSocketConnectionManager()
order_stream_ws_manager = WebSocketConnectionManager()
telemetry_ws_manager = WebSocketConnectionManager()
