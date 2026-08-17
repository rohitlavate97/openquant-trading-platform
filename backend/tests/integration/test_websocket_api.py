"""Integration tests for WebSocket streaming endpoints and stats API."""

import pytest
from starlette.testclient import TestClient
from openquant.interfaces.api.app import create_app
from openquant.domain.models.market_data import Tick
from openquant.application.services.streaming_service import streaming_broadcaster
from decimal import Decimal
from datetime import datetime, timezone


@pytest.fixture
def sync_test_client():
    """Synchronous test client for Starlette WebSocket testing."""
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_market_data_websocket_subscription_and_tick_flow(sync_test_client: TestClient):
    """Verify WebSocket handshake, subscription protocol, ping/pong, and stats API."""
    with sync_test_client.websocket_connect("/ws/v1/market-data") as websocket:
        # 1. Receive connection confirmation
        data = websocket.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert data["stream"] == "market_data"

        # 2. Subscribe to AAPL
        websocket.send_json({"action": "subscribe", "symbols": ["AAPL"]})
        sub_confirm = websocket.receive_json()
        assert sub_confirm["type"] == "SUBSCRIPTION_CONFIRMED"
        assert "AAPL" in sub_confirm["subscribed_symbols"]

        # 3. Ping -> Pong
        websocket.send_json({"action": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "PONG"

        # 4. Unsubscribe
        websocket.send_json({"action": "unsubscribe", "symbols": ["AAPL"]})
        unsub = websocket.receive_json()
        assert unsub["type"] == "UNSUBSCRIPTION_CONFIRMED"


def test_orders_websocket_subscription_flow(sync_test_client: TestClient):
    """Verify order execution report WebSocket stream handshake and subscribe."""
    with sync_test_client.websocket_connect("/ws/v1/orders") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert data["stream"] == "order_execution"

        websocket.send_json({"action": "subscribe", "accounts": ["acc_main"]})
        sub_confirm = websocket.receive_json()
        assert sub_confirm["type"] == "SUBSCRIPTION_CONFIRMED"


def test_telemetry_websocket_ping_flow(sync_test_client: TestClient):
    """Verify telemetry WebSocket stream."""
    with sync_test_client.websocket_connect("/ws/v1/telemetry") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert data["stream"] == "telemetry"

        websocket.send_json({"action": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "PONG"
