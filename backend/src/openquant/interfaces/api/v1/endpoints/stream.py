"""WebSocket Streaming and Telemetry Endpoints for Market Data, Orders, and Health."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from openquant.domain.models.auth import Permission, User
from openquant.interfaces.api.dependencies import get_current_user_ws, require_permissions
from openquant.interfaces.api.v1.websocket.connection_manager import (
    market_data_ws_manager,
    order_stream_ws_manager,
    telemetry_ws_manager,
)
from openquant.application.services.streaming_service import streaming_broadcaster

logger = logging.getLogger("openquant.api.stream")

router = APIRouter(tags=["Real-Time Streaming & WebSockets"])


@router.get("/stream/stats", summary="Get Streaming Engine Statistics")
async def get_stream_stats(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> dict[str, Any]:
    """Retrieve active WebSocket connection and channel subscription metrics."""
    return streaming_broadcaster.get_streaming_stats()


@router.websocket("/ws/v1/market-data")
async def market_data_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """Real-time market data L1 tick stream supporting dynamic symbol subscriptions."""
    client_id = f"mkt_cli_{uuid.uuid4().hex[:8]}"
    user = await get_current_user_ws(websocket, token)
    user_id = user.user_id if user else "anonymous"

    await market_data_ws_manager.connect(websocket, client_id, user_id)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "stream": "market_data",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                await websocket.send_json({"type": "ERROR", "message": "Invalid JSON format"})
                continue

            action = data.get("action", "").lower()

            if action == "subscribe":
                symbols = data.get("symbols", [])
                channels = [f"ticks:{sym.upper()}" for sym in symbols]
                if "ALL" in [s.upper() for s in symbols]:
                    channels.append("ticks:ALL")
                await market_data_ws_manager.subscribe(websocket, channels)
                await websocket.send_json({
                    "type": "SUBSCRIPTION_CONFIRMED",
                    "subscribed_symbols": symbols,
                    "channels": channels,
                })

            elif action == "unsubscribe":
                symbols = data.get("symbols", [])
                channels = [f"ticks:{sym.upper()}" for sym in symbols]
                await market_data_ws_manager.unsubscribe(websocket, channels)
                await websocket.send_json({
                    "type": "UNSUBSCRIPTION_CONFIRMED",
                    "unsubscribed_symbols": symbols,
                })

            elif action == "ping":
                await websocket.send_json({
                    "type": "PONG",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    except WebSocketDisconnect:
        await market_data_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"Market data WebSocket error: {e}")
        await market_data_ws_manager.disconnect(websocket)


@router.websocket("/ws/v1/orders")
async def orders_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """Real-time order execution report stream for authenticated accounts."""
    client_id = f"ord_cli_{uuid.uuid4().hex[:8]}"
    user = await get_current_user_ws(websocket, token)
    user_id = user.user_id if user else "anonymous"

    await order_stream_ws_manager.connect(websocket, client_id, user_id)
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "stream": "order_execution",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                await websocket.send_json({"type": "ERROR", "message": "Invalid JSON format"})
                continue

            action = data.get("action", "").lower()

            if action == "subscribe":
                accounts = data.get("accounts", ["acc_main"])
                channels = [f"orders:{acc}" for acc in accounts]
                channels.append("orders:ALL")
                await order_stream_ws_manager.subscribe(websocket, channels)
                await websocket.send_json({
                    "type": "SUBSCRIPTION_CONFIRMED",
                    "subscribed_accounts": accounts,
                })

            elif action == "ping":
                await websocket.send_json({
                    "type": "PONG",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    except WebSocketDisconnect:
        await order_stream_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"Order stream WebSocket error: {e}")
        await order_stream_ws_manager.disconnect(websocket)


@router.websocket("/ws/v1/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
):
    """Real-time platform telemetry, latency, risk halts, and kill switch status."""
    client_id = f"tel_cli_{uuid.uuid4().hex[:8]}"
    await telemetry_ws_manager.connect(websocket, client_id, "telemetry_viewer")
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "stream": "telemetry",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                if data.get("action", "").lower() == "ping":
                    await websocket.send_json({
                        "type": "PONG",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            except Exception:
                pass

    except WebSocketDisconnect:
        await telemetry_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"Telemetry WebSocket error: {e}")
        await telemetry_ws_manager.disconnect(websocket)
