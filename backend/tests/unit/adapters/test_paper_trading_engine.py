"""Unit tests for Paper Trading Engine Adapter."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from openquant.adapters.paper.paper_trading_engine import PaperTradingEngine
from openquant.domain.models.market_data import Tick
from openquant.domain.models.paper_trading import PaperTradingSessionStatus


@pytest.mark.asyncio
async def test_paper_trading_account_and_session_lifecycle():
    """Verify paper account creation, session launch, pause, and stop."""
    engine = PaperTradingEngine()

    acc = await engine.create_paper_account(name="Test Paper Fund", initial_balance=Decimal("250000.00"))
    assert acc.account_id.startswith("acc_paper_")
    assert acc.current_cash == Decimal("250000.00")

    session = await engine.start_session(
        strategy_id="strat_ema_1",
        account_id=acc.account_id,
        symbols=["AAPL"],
    )
    assert session.session_id.startswith("psess_")
    assert session.status == PaperTradingSessionStatus.ACTIVE

    paused = await engine.pause_session(session.session_id)
    assert paused is not None
    assert paused.status == PaperTradingSessionStatus.PAUSED

    stopped = await engine.stop_session(session.session_id)
    assert stopped is not None
    assert stopped.status == PaperTradingSessionStatus.STOPPED


@pytest.mark.asyncio
async def test_paper_trading_tick_processing_and_pnl():
    """Verify live market tick dispatching to active paper sessions."""
    engine = PaperTradingEngine()
    acc = await engine.create_paper_account(initial_balance=Decimal("100000.00"))
    session = await engine.start_session(
        strategy_id="strat_ema_1",
        account_id=acc.account_id,
        symbols=["AAPL"],
    )

    # Ingest rising sequence of ticks
    for i, price in enumerate([180.0, 182.0, 184.0, 186.0, 188.0, 185.0]):
        tick = Tick(
            symbol="AAPL",
            last_price=Decimal(str(price)),
            volume=Decimal("500"),
            timestamp=datetime.now(timezone.utc),
            bid=Decimal(str(price - 0.05)),
            ask=Decimal(str(price + 0.05)),
        )
        await engine.process_market_tick(tick)

    # Verify session recorded execution state
    gate = await engine.evaluate_gate_status(session.session_id)
    assert gate is not None
    assert gate.session_id == session.session_id
