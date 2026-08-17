from datetime import datetime, timezone
from decimal import Decimal
import pytest

from openquant.application.services.portfolio_service import PortfolioService
from openquant.adapters.portfolio.portfolio_analytics_engine import PortfolioAnalyticsEngine
from openquant.adapters.repositories.in_memory_oms_repo import (
    InMemoryOrderRepository,
    InMemoryPositionRepository,
)
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.adapters.brokers.registry import BrokerAdapterRegistry
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.application.services.order_service import OrderManagementService
from openquant.application.services.audit_service import AuditLogService
from openquant.application.services.market_data_service import market_data_service
from openquant.application.services.risk_service import risk_service
from openquant.domain.models.market_data import Tick
from openquant.domain.models.position import Position, PositionSide


@pytest.fixture
def portfolio_service_setup():
    pos_repo = InMemoryPositionRepository()
    order_repo = InMemoryOrderRepository()
    audit_repo = InMemoryAuditLogRepository()
    audit_svc = AuditLogService(audit_repo=audit_repo)

    broker_reg = BrokerAdapterRegistry()
    paper_broker = PaperBrokerAdapter(adapter_id="paper_broker", initial_cash=Decimal("100000.00"))
    broker_reg.register(paper_broker)

    oms = OrderManagementService(
        order_repo=order_repo,
        pos_repo=pos_repo,
        broker_reg=broker_reg,
        mkt_service=market_data_service,
        audit=audit_svc,
    )
    engine = PortfolioAnalyticsEngine(
        pos_repo=pos_repo,
        mkt_service=market_data_service,
        base_cash=Decimal("100000.00"),
    )
    service = PortfolioService(analytics_engine=engine, oms=oms, audit=audit_svc)
    return service, pos_repo


@pytest.mark.asyncio
async def test_portfolio_service_summary_and_close(portfolio_service_setup):
    service, pos_repo = portfolio_service_setup
    await risk_service.deactivate_kill_switch()

    # Seed position
    pos_nvda = Position(
        position_id="pos_nvda_1",
        account_id="acc_main",
        broker_id="paper_broker",
        strategy_id="strat_test",
        symbol="NVDA",
        side=PositionSide.LONG,
        quantity=Decimal("10"),
        entry_price=Decimal("120.00"),
    )
    await pos_repo.save(pos_nvda)

    # Ingest fresh tick
    await market_data_service.ingest_tick(
        Tick(symbol="NVDA", exchange="NASDAQ", last_price=Decimal("130.00"), timestamp=datetime.now(timezone.utc))
    )

    summary = await service.get_summary("acc_main")
    assert summary.unrealized_pnl == Decimal("100.00")

    positions = await service.list_positions("acc_main")
    assert len(positions) == 1
    assert positions[0].symbol == "NVDA"

    # Close position
    order_id = await service.close_position(account_id="acc_main", symbol="NVDA", actor_id="lead_trader")
    assert order_id.startswith("ord_")
