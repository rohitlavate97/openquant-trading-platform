from datetime import datetime, timezone
from decimal import Decimal
import pytest

from openquant.adapters.portfolio.portfolio_analytics_engine import PortfolioAnalyticsEngine
from openquant.adapters.repositories.in_memory_oms_repo import InMemoryPositionRepository
from openquant.application.services.market_data_service import market_data_service
from openquant.domain.models.market_data import Tick
from openquant.domain.models.position import Position, PositionSide


@pytest.fixture
def portfolio_engine_setup():
    pos_repo = InMemoryPositionRepository()
    engine = PortfolioAnalyticsEngine(
        pos_repo=pos_repo,
        mkt_service=market_data_service,
        base_cash=Decimal("100000.00"),
    )
    return engine, pos_repo


@pytest.mark.asyncio
async def test_portfolio_positions_and_pnl_calculation(portfolio_engine_setup):
    engine, pos_repo = portfolio_engine_setup

    # Seed positions
    pos_aapl = Position(
        position_id="pos_aapl_1",
        account_id="acc_test",
        broker_id="paper_broker",
        strategy_id="strat_test",
        symbol="AAPL",
        side=PositionSide.LONG,
        quantity=Decimal("10"),
        entry_price=Decimal("150.00"),
    )
    pos_msft = Position(
        position_id="pos_msft_1",
        account_id="acc_test",
        broker_id="paper_broker",
        strategy_id="strat_test",
        symbol="MSFT",
        side=PositionSide.SHORT,
        quantity=Decimal("5"),
        entry_price=Decimal("300.00"),
    )
    await pos_repo.save(pos_aapl)
    await pos_repo.save(pos_msft)

    # Ingest market ticks
    await market_data_service.ingest_tick(
        Tick(symbol="AAPL", exchange="NASDAQ", last_price=Decimal("160.00"), timestamp=datetime.now(timezone.utc))
    )
    await market_data_service.ingest_tick(
        Tick(symbol="MSFT", exchange="NASDAQ", last_price=Decimal("290.00"), timestamp=datetime.now(timezone.utc))
    )

    positions = await engine.get_active_positions("acc_test")
    assert len(positions) == 2

    aapl = next(p for p in positions if p.symbol == "AAPL")
    assert aapl.unrealized_pnl == Decimal("100.00")  # (160 - 150) * 10
    assert aapl.market_value == Decimal("1600.00")

    msft = next(p for p in positions if p.symbol == "MSFT")
    assert msft.unrealized_pnl == Decimal("50.00")  # (300 - 290) * 5
    assert msft.market_value == Decimal("1450.00")

    # Summary
    summary = await engine.get_portfolio_summary("acc_test")
    assert summary.unrealized_pnl == Decimal("150.00")
    assert summary.total_equity == Decimal("100150.00")
    assert summary.active_positions_count == 2

    # Allocation
    alloc = await engine.get_asset_allocation("acc_test")
    assert len(alloc) == 3  # AAPL, MSFT, Cash
    symbols = [a.symbol_or_class for a in alloc]
    assert "AAPL" in symbols
    assert "USD_CASH" in symbols

    # Performance
    snapshots = await engine.get_performance_snapshots("acc_test", days=7)
    assert len(snapshots) == 8
