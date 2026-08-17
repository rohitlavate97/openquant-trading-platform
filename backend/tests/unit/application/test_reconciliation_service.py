"""Unit tests for Reconciliation Application Service and Pre-Order Hook."""

import pytest
from decimal import Decimal
from openquant.application.services.reconciliation_service import ReconciliationService
from openquant.adapters.reconciliation.state_reconciliation_engine import StateReconciliationEngine
from openquant.adapters.repositories.in_memory_oms_repo import InMemoryPositionRepository, InMemoryOrderRepository
from openquant.adapters.brokers.registry import BrokerAdapterRegistry
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.application.services.risk_service import RiskService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.domain.models.position import Position, PositionSide


@pytest.fixture
def recon_service():
    pos_repo = InMemoryPositionRepository()
    order_repo = InMemoryOrderRepository()
    registry = BrokerAdapterRegistry()
    broker = PaperBrokerAdapter(initial_cash=Decimal("100000.00"))
    registry.register(broker)
    risk_svc = RiskService()
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())

    engine = StateReconciliationEngine(
        pos_repo=pos_repo,
        order_repo=order_repo,
        brokers=registry,
        risk=risk_svc,
    )
    svc = ReconciliationService(engine=engine, audit=audit)
    return svc, pos_repo


@pytest.mark.asyncio
async def test_reconciliation_service_and_pre_order_check(recon_service):
    """Verify pre-order check allows clean states and blocks discrepant states."""
    svc, pos_repo = recon_service

    # Clean state -> allowed
    allowed = await svc.pre_order_reconciliation_check("acc_clean", "AAPL")
    assert allowed is True

    # Inject discrepancy -> blocked
    await pos_repo.save(
        Position(
            position_id="pos_test_clean_1",
            account_id="acc_clean",
            strategy_id="strat_1",
            broker_id="paper_broker",
            symbol="AAPL",
            side=PositionSide.LONG,
            quantity=Decimal("500"),
            entry_price=Decimal("150.00"),
        )
    )

    allowed_after_mismatch = await svc.pre_order_reconciliation_check("acc_clean", "AAPL")
    assert allowed_after_mismatch is False
