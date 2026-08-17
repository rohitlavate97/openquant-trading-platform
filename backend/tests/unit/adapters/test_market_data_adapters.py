"""Unit tests for Market Data Adapters (InMemoryFeed, CandleAggregator, SyntheticFeed)."""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from openquant.domain.models.market_data import (
    Tick,
    CandleTimeframe,
    FeedHealthStatus,
)
from openquant.adapters.market_data.in_memory_feed import InMemoryMarketDataFeed
from openquant.adapters.market_data.candle_aggregator import StreamingCandleAggregator
from openquant.adapters.market_data.synthetic_feed import SyntheticMarketFeed


@pytest.mark.asyncio
async def test_in_memory_market_feed_ingest_and_staleness():
    """Verify tick ingestion, retrieval, and staleness threshold evaluation."""
    feed = InMemoryMarketDataFeed()

    # 1. Ingest fresh tick
    now = datetime.now(timezone.utc)
    fresh_tick = Tick(
        symbol="AAPL",
        exchange="NASDAQ",
        last_price=Decimal("185.50"),
        last_quantity=Decimal("50"),
        timestamp=now,
    )
    await feed.ingest_tick(fresh_tick)

    retrieved = await feed.get_latest_tick("AAPL")
    assert retrieved is not None
    assert retrieved.last_price == Decimal("185.50")
    assert await feed.is_symbol_stale("AAPL", max_staleness_ms=3000) is False

    # 2. Evaluate staleness with fresh tick
    report = await feed.evaluate_staleness(max_staleness_ms=3000)
    assert report.overall_status == FeedHealthStatus.HEALTHY
    assert report.is_trading_paused is False
    assert report.stale_symbols_count == 0

    # 3. Ingest stale tick (5000ms old)
    old_time = now - timedelta(milliseconds=5000)
    stale_tick = Tick(
        symbol="STALE_SYM",
        exchange="NASDAQ",
        last_price=Decimal("50.00"),
        timestamp=old_time,
    )
    await feed.ingest_tick(stale_tick)

    assert await feed.is_symbol_stale("STALE_SYM", max_staleness_ms=3000) is True
    report_stale = await feed.evaluate_staleness(max_staleness_ms=3000)
    assert report_stale.overall_status == FeedHealthStatus.STALE
    assert report_stale.is_trading_paused is True
    assert report_stale.stale_symbols_count == 1


@pytest.mark.asyncio
async def test_candle_aggregator_ohlcv_computation():
    """Verify tick aggregation into OHLCV bars across timeframes."""
    aggregator = StreamingCandleAggregator()
    base_time = datetime(2026, 8, 17, 10, 0, 0, tzinfo=timezone.utc)

    # Ingest 3 ticks within the same 1m bar: 100 -> 105 -> 98 -> 102
    t1 = Tick(symbol="MSFT", last_price=Decimal("100.00"), last_quantity=Decimal("10"), timestamp=base_time)
    t2 = Tick(symbol="MSFT", last_price=Decimal("105.00"), last_quantity=Decimal("20"), timestamp=base_time + timedelta(seconds=10))
    t3 = Tick(symbol="MSFT", last_price=Decimal("98.00"), last_quantity=Decimal("15"), timestamp=base_time + timedelta(seconds=25))
    t4 = Tick(symbol="MSFT", last_price=Decimal("102.00"), last_quantity=Decimal("5"), timestamp=base_time + timedelta(seconds=40))

    await aggregator.process_tick(t1)
    await aggregator.process_tick(t2)
    await aggregator.process_tick(t3)
    completed = await aggregator.process_tick(t4)
    assert len(completed) == 0  # Bar still open

    # Verify in-progress live bar values
    candles = await aggregator.get_candles("MSFT", CandleTimeframe.M1)
    assert len(candles) == 1
    bar = candles[0]
    assert bar.open == Decimal("100.00")
    assert bar.high == Decimal("105.00")
    assert bar.low == Decimal("98.00")
    assert bar.close == Decimal("102.00")
    assert bar.volume == Decimal("50")

    # Ingest tick in the NEXT minute -> should close the previous 1m bar
    next_bar_tick = Tick(
        symbol="MSFT",
        last_price=Decimal("103.00"),
        last_quantity=Decimal("10"),
        timestamp=base_time + timedelta(seconds=65),
    )
    closed = await aggregator.process_tick(next_bar_tick)
    assert any(c.timeframe == CandleTimeframe.M1 for c in closed)


def test_synthetic_feed_generator():
    """Verify synthetic market feed produces valid random walk ticks."""
    syn = SyntheticMarketFeed()
    tick = syn.generate_next_tick("AAPL")

    assert tick.symbol == "AAPL"
    assert tick.last_price > Decimal("0")
    assert tick.bid_price is not None and tick.ask_price is not None
    assert tick.bid_price < tick.ask_price
