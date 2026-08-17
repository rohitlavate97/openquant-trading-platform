"""Market Data Application Service coordinating ingestion, staleness enforcement, and candle aggregation."""

import logging
from typing import Any
from decimal import Decimal
from openquant.domain.models.market_data import (
    Tick,
    Candle,
    CandleTimeframe,
    MarketDataStalenessReport,
    FeedHealthStatus,
)
from openquant.domain.exceptions import StaleMarketDataError
from openquant.domain.ports.market_data_port import IMarketDataPort, ICandleAggregatorPort
from openquant.adapters.market_data.in_memory_feed import in_memory_market_feed
from openquant.adapters.market_data.candle_aggregator import candle_aggregator
from openquant.adapters.market_data.synthetic_feed import synthetic_feed, SyntheticMarketFeed
from openquant.application.services.streaming_service import streaming_broadcaster, StreamingBroadcasterService

logger = logging.getLogger("openquant.market_data_service")


class MarketDataService:
    """Application Service governing the market data pipeline and staleness threshold."""

    def __init__(
        self,
        feed: IMarketDataPort = in_memory_market_feed,
        aggregator: ICandleAggregatorPort = candle_aggregator,
        broadcaster: StreamingBroadcasterService = streaming_broadcaster,
        syn_feed: SyntheticMarketFeed = synthetic_feed,
        default_max_staleness_ms: int = 3000,
    ) -> None:
        self._feed = feed
        self._aggregator = aggregator
        self._broadcaster = broadcaster
        self._syn_feed = syn_feed
        self._max_staleness_ms = default_max_staleness_ms

        # Wire synthetic feed to self.ingest_tick
        self._syn_feed.register_tick_callback(self.ingest_tick)

    async def ingest_tick(self, tick: Tick) -> None:
        """Ingest tick, aggregate candle, and broadcast to live WebSocket channels."""
        # 1. Update in-memory feed cache & metrics
        await self._feed.ingest_tick(tick)

        # 2. Process candle aggregation
        completed_candles = await self._aggregator.process_tick(tick)

        # 3. Broadcast tick to WebSockets
        await self._broadcaster.broadcast_tick(tick)

        # 4. If any candle closed, broadcast candle update
        for candle in completed_candles:
            candle_payload = {
                "type": "CANDLE_CLOSED",
                "symbol": candle.symbol,
                "timeframe": candle.timeframe.value,
                "timestamp": candle.timestamp.isoformat(),
                "open": str(candle.open),
                "high": str(candle.high),
                "low": str(candle.low),
                "close": str(candle.close),
                "volume": str(candle.volume),
            }
            await self._broadcaster.broadcast_telemetry("CANDLE_CLOSED", candle_payload)

    async def assert_not_stale(self, symbol: str, custom_threshold_ms: int | None = None) -> Tick:
        """Enforce Non-Negotiable Rule 7: Pre-trade staleness guard.
        Raises StaleMarketDataError if market tick age exceeds 3000ms.
        """
        threshold = custom_threshold_ms or self._max_staleness_ms
        tick = await self._feed.get_latest_tick(symbol)
        if not tick:
            raise StaleMarketDataError(f"No market data received for symbol '{symbol}'. Order blocked.")

        if tick.is_stale(threshold):
            raise StaleMarketDataError(
                f"Market tick for '{symbol}' is stale (exceeds {threshold}ms). Order blocked pre-trade."
            )
        return tick

    async def get_staleness_report(self, max_staleness_ms: int | None = None) -> MarketDataStalenessReport:
        """Evaluate feed health report across all instruments."""
        threshold = max_staleness_ms or self._max_staleness_ms
        report = await self._feed.evaluate_staleness(threshold)

        # If feed status is STALE or DISCONNECTED, broadcast risk telemetry alert
        if report.overall_status in [FeedHealthStatus.STALE, FeedHealthStatus.DISCONNECTED]:
            await self._broadcaster.broadcast_telemetry(
                "MARKET_DATA_STALE_ALERT",
                {
                    "overall_status": report.overall_status.value,
                    "is_trading_paused": report.is_trading_paused,
                    "stale_symbols_count": report.stale_symbols_count,
                    "timestamp": report.timestamp.isoformat(),
                },
            )

        return report

    async def get_latest_tick(self, symbol: str) -> Tick | None:
        """Get latest tick for symbol."""
        return await self._feed.get_latest_tick(symbol)

    async def get_all_latest_ticks(self) -> dict[str, Tick]:
        """Get all latest ticks."""
        return await self._feed.get_all_latest_ticks()

    async def get_candles(
        self,
        symbol: str,
        timeframe: CandleTimeframe,
        limit: int = 100,
    ) -> list[Candle]:
        """Retrieve aggregated OHLCV candles."""
        return await self._aggregator.get_candles(symbol, timeframe, limit)

    def start_synthetic_feed(self, interval_sec: float = 0.5) -> None:
        """Start real-time synthetic market replay feed."""
        self._syn_feed.start(interval_sec)

    def stop_synthetic_feed(self) -> None:
        """Stop synthetic market replay feed."""
        self._syn_feed.stop()

    def is_synthetic_feed_running(self) -> bool:
        return self._syn_feed.is_running


# Global singleton instance
market_data_service = MarketDataService()
