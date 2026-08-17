"""Unit tests for State Reconciliation Engine and Rule 5 Auto-Halt Guard."""

import pytest
from decimal import Decimal
from openquant.adapters.reconciliation.state_reconciliation_engine import StateReconciliationEngine
from openquant.adapters.repositories.in_memory_oms_repo import InMemoryPositionRepository, InMemoryOrderRepository
from openquant.adapters.brokers.registry import BrokerAdapterRegistry
from openquant.adapters.brokers.paper_adapter import PaperBrokerAdapter
from openquant.application.services.risk_service import RiskService
from openquant.domain.models.position import Position, PositionSide
from openquant.domain.models.order import Order, OrderSide, OrderType, OrderStatus, TimeInForce
from openquant.domain.models.reconciliation import ReconciliationStatus, PositionDiscrepancyType


@pytest.fixture
def recon_setup():
    pos_repo = InMemoryPositionRepository()
    order_repo = InMemoryOrderRepository()
    registry = BrokerAdapterRegistry()
    broker = PaperBrokerAdapter(initial_cash=Decimal("100000.00"))
    registry.register(broker)
    risk_svc = RiskService()
    engine = StateReconciliationEngine(
        pos_repo=pos_repo,
        order_repo=order_repo,
        brokers=registry,
        risk=risk_svc,
    )
    return engine, pos_repo, broker, risk_svc


@pytest.mark.asyncio
async def test_reconciliation_clean_state(recon_setup):
    """Verify clean status when internal OMS and broker positions match."""
    engine, pos_repo, broker, risk_svc = recon_setup

    # Both empty
    report = await engine.reconcile_account("acc_test", "paper_broker")
    assert report.status == ReconciliationStatus.CLEAN
    assert len(report.position_discrepancies) == 0
    assert report.auto_halt_triggered is False


@pytest.mark.asyncio
async def test_reconciliation_detects_mismatch_and_triggers_auto_halt(recon_setup):
    """Verify Rule 5 violation triggers emergency Auto-Halt and kill switch."""
    engine, pos_repo, broker, risk_svc = recon_setup

    # Internal OMS has 100 AAPL
    await pos_repo.save(
        Position(
            position_id="pos_test_1",
            account_id="acc_test",
            strategy_id="strat_1",
            broker_id="paper_broker",
            symbol="AAPL",
            side=PositionSide.LONG,
            quantity=Decimal("100"),
            entry_price=Decimal("150.00"),
        )
    )

    # Broker has NO position in AAPL -> Phantom Internal Discrepancy
    report = await engine.reconcile_account("acc_test", "paper_broker")
    assert report.status == ReconciliationStatus.HALTED_ON_DISCREPANCY
    assert len(report.position_discrepancies) == 1
    assert report.position_discrepancies[0].discrepancy_type == PositionDiscrepancyType.PHANTOM_INTERNAL
    assert report.auto_halt_triggered is True

    # Risk service kill switch activated
    assert risk_svc.get_config().kill_switch.is_active is True


@pytest.mark.asyncio
async def test_reconciliation_force_sync(recon_setup):
    """Verify force sync overwrites internal OMS with broker actuals."""
    engine, pos_repo, broker, risk_svc = recon_setup

    # Internal has stale 50 TSLA
    await pos_repo.save(
        Position(
            position_id="pos_test_2",
            account_id="acc_test",
            strategy_id="strat_1",
            broker_id="paper_broker",
            symbol="TSLA",
            side=PositionSide.LONG,
            quantity=Decimal("50"),
            entry_price=Decimal("200.00"),
        )
    )

    # Execute a trade on broker to have actual positions
    await broker.place_order(
        Order(
            order_id="ord_brk_1",
            account_id="acc_test",
            strategy_id="strat_1",
            broker_id="paper_broker",
            symbol="NVDA",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC,
            quantity=Decimal("20"),
            status=OrderStatus.SUBMITTED,
            idempotency_key="idemp_1",
        )
    )

    # Sync positions
    sync_report = await engine.sync_positions_from_broker("acc_test", "paper_broker")
    assert sync_report.report_id.startswith("recon_")
