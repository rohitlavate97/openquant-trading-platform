"""Unit tests for MT5 ZeroMQ socket bridge adapter."""

from decimal import Decimal
import pytest
from openquant.domain.models.strategy_sources import (
    MT5BridgeCommand,
    MT5BridgeMessage,
    MT5ConnectionState,
)
from openquant.adapters.sources.mt5_bridge import MT5BridgeAdapter
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.application.services.audit_service import AuditLogService


@pytest.fixture
def mt5_adapter():
    audit_repo = InMemoryAuditLogRepository()
    audit_svc = AuditLogService(audit_repo)
    return MT5BridgeAdapter(audit=audit_svc)


@pytest.mark.asyncio
async def test_mt5_lifecycle_and_command_dispatch(mt5_adapter):
    status = await mt5_adapter.get_status()
    assert status.state == MT5ConnectionState.DISCONNECTED

    # Connect
    connected = await mt5_adapter.connect()
    assert connected is True

    status_connected = await mt5_adapter.get_status()
    assert status_connected.state == MT5ConnectionState.CONNECTED
    assert status_connected.connected_eas_count >= 1

    # Dispatch command
    cmd = MT5BridgeCommand(
        command_id="cmd_mt5_1",
        action="BUY",
        symbol="EURUSD",
        volume=Decimal("0.5"),
    )
    result = await mt5_adapter.dispatch_command(cmd)
    assert result["success"] is True
    assert "mt5_ticket" in result

    # Inbound message
    inbound = MT5BridgeMessage(
        message_id="msg_1",
        ea_id="EA_EURUSD_v1",
        event_type="HEARTBEAT",
    )
    ack = await mt5_adapter.process_inbound_message(inbound)
    assert ack["status"] == "ACK"

    # Disconnect
    await mt5_adapter.disconnect()
    status_disc = await mt5_adapter.get_status()
    assert status_disc.state == MT5ConnectionState.DISCONNECTED
