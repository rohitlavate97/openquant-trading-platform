"""Unit tests for Market Data Application Service & Staleness Guard."""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from openquant.domain.models.market_data import Tick
from openquant.domain.exceptions import StaleMarketDataError
from openquant.adapters.market_data.in_memory_feed import InMemoryMarketDataFeed
from openquant.adapters.market_data.candle_aggregator import StreamingCandleAggregator
from openquant.adapters.market_data.synthetic_feed import SyntheticMarketFeed
from openquant.interfaces.api.v1.websocket.connection_manager import WebSocketConnectionManager
from openquant.application.services.streaming_service import StreamingBroadcasterService
from openquant.application.services.market_data_service import MarketDataService


@pytest.mark.asyncio
async def test_market_data_service_staleness_guard_enforcement():
    """Verify assert_not_stale passes on fresh ticks and raises StaleMarketDataError on stale/missing ticks."""
    feed = InMemoryMarketDataFeed()
    aggregator = StreamingCandleAggregator()
    broadcaster = StreamingBroadcasterService(
        market_ws=WebSocketConnectionManager(),
        order_ws=WebSocketConnectionManager(),
        telemetry_ws=WebSocketConnectionManager(),
    )
    service = MarketDataService(
        feed=feed,
        aggregator=aggregator,
        broadcaster=broadcaster,
        syn_feed=SyntheticMarketFeed(),
        default_max_staleness_ms=3000,
    )

    # 1. Missing symbol raises StaleMarketDataError
    with pytest.raises(StaleMarketDataError) as exc_info:
        await service.assert_not_stale("UNKNOWN")
    assert "No market data received" in str(exc_info.value)

    # 2. Fresh tick passes cleanly
    fresh_tick = Tick(
        symbol="NVDA",
        last_price=Decimal("130.00"),
        timestamp=datetime.now(timezone.utc),
    )
    await service.ingest_tick(fresh_tick)
    result = await service.assert_not_stale("NVDA")
    assert result.symbol == "NVDA"

    # 3. Stale tick (> 3000ms) raises StaleMarketDataError
    stale_time = datetime.now(timezone.utc) - timedelta(milliseconds=4500)
    stale_tick = Tick(
        symbol="NVDA",
        last_price=Decimal("129.00"),
        timestamp=stale_time,
    )
    await service.ingest_tick(stale_tick)

    with pytest.raises(StaleMarketDataError) as exc_info:
        await service.assert_not_stale("NVDA")
    assert "is stale" in str(exc_info.value)
