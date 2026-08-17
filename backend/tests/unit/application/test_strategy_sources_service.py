"""Unit tests for StrategySourcesService application layer."""

from decimal import Decimal
from datetime import datetime, timezone
import pytest

from openquant.domain.models.strategy_sources import (
    TradingViewAction,
    TradingViewWebhookPayload,
    MT5BridgeCommand,
)
from openquant.domain.models.market_data import Tick
from openquant.application.services.strategy_sources_service import StrategySourcesService
from openquant.adapters.sources.tradingview_webhook import TradingViewWebhookHandler
from openquant.adapters.sources.mt5_bridge import MT5BridgeAdapter
from openquant.adapters.sources.sheets_parser import StructuredSheetsParser
from openquant.adapters.repositories.in_memory_oms_repo import (
    InMemoryOrderRepository,
    InMemoryPositionRepository,
)
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.adapters.risk.risk_engine import SynchronousRiskEngine
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.application.services.order_service import OrderManagementService
from openquant.application.services.risk_service import risk_service
from openquant.application.services.audit_service import AuditLogService
from openquant.application.services.market_data_service import market_data_service


@pytest.fixture
def sources_svc_setup():
    order_repo = InMemoryOrderRepository()
    pos_repo = InMemoryPositionRepository()
    audit_repo = InMemoryAuditLogRepository()
    audit_svc = AuditLogService(audit_repo)
    oms = OrderManagementService(
        order_repo=order_repo,
        pos_repo=pos_repo,
        mkt_service=market_data_service,
        audit=audit_svc,
    )

    tv_handler = TradingViewWebhookHandler(oms=oms, audit=audit_svc)
    mt5_bridge = MT5BridgeAdapter(audit=audit_svc)
    sheets_parser = StructuredSheetsParser()

    service = StrategySourcesService(
        tv_handler=tv_handler,
        mt5_bridge=mt5_bridge,
        sheets_parser=sheets_parser,
        oms=oms,
        audit=audit_svc,
    )
    return service, mt5_bridge


@pytest.mark.asyncio
async def test_service_sheets_parse_and_batch_execute(sources_svc_setup):
    service, _ = sources_svc_setup
    await risk_service.deactivate_kill_switch()

    # Ingest fresh ticks so 3000ms staleness guard passes
    await market_data_service.ingest_tick(
        Tick(symbol="AAPL", exchange="NASDAQ", last_price=Decimal("150.00"), timestamp=datetime.now(timezone.utc))
    )
    await market_data_service.ingest_tick(
        Tick(symbol="MSFT", exchange="NASDAQ", last_price=Decimal("300.00"), timestamp=datetime.now(timezone.utc))
    )

    csv_data = """Timestamp,Symbol,Signal_Type,Quantity,Limit_Price
2026-08-17T10:00:00Z,AAPL,BUY,10,150.00
2026-08-17T10:05:00Z,MSFT,BUY,5,300.00
"""
    parse_res = service.parse_sheets_csv(csv_data)
    assert parse_res.valid_rows_count == 2

    order_ids = await service.execute_sheets_orders(
        orders=parse_res.parsed_orders,
        account_id="acc_main",
        actor_id="test_trader",
    )
    assert len(order_ids) == 2


@pytest.mark.asyncio
async def test_service_mt5_bridge_flow(sources_svc_setup):
    service, bridge = sources_svc_setup
    await bridge.connect()

    status = await service.get_mt5_status()
    assert status.connected_eas_count >= 1

    cmd = MT5BridgeCommand(
        command_id="cmd_test_1",
        action="BUY",
        symbol="GBPUSD",
        volume=Decimal("1.0"),
    )
    res = await service.dispatch_mt5_command(cmd, actor_id="test_trader")
    assert res["success"] is True
