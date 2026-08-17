"""In-Memory Market Data Feed & Staleness Engine Adapter."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from openquant.domain.models.market_data import (
    Tick,
    FeedHealthStatus,
    SymbolFeedMetrics,
    MarketDataStalenessReport,
)
from openquant.domain.ports.market_data_port import IMarketDataPort


class InMemoryMarketDataFeed(IMarketDataPort):
    """High-performance in-memory market data cache and staleness detector."""

    def __init__(self) -> None:
        self._ticks: dict[str, Tick] = {}
        self._tick_counts: dict[str, int] = {}
        self._first_tick_times: dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def ingest_tick(self, tick: Tick) -> None:
        """Ingest tick into cache with thread-safe atomic lock."""
        async with self._lock:
            sym = tick.symbol.upper()
            now = datetime.now(timezone.utc)
            self._ticks[sym] = tick
            self._tick_counts[sym] = self._tick_counts.get(sym, 0) + 1
            if sym not in self._first_tick_times:
                self._first_tick_times[sym] = now

    async def get_latest_tick(self, symbol: str) -> Tick | None:
        """Get latest tick for symbol."""
        async with self._lock:
            return self._ticks.get(symbol.upper())

    async def get_all_latest_ticks(self) -> dict[str, Tick]:
        """Get all latest ticks."""
        async with self._lock:
            return dict(self._ticks)

    async def is_symbol_stale(self, symbol: str, max_staleness_ms: int = 3000) -> bool:
        """Check if single symbol is stale."""
        async with self._lock:
            tick = self._ticks.get(symbol.upper())
            if not tick:
                return True
            return tick.is_stale(max_staleness_ms)

    async def evaluate_staleness(self, max_staleness_ms: int = 3000) -> MarketDataStalenessReport:
        """Evaluate staleness for all tracked symbols against the hard-stop limit (Rule: 3000ms)."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            symbol_metrics: dict[str, SymbolFeedMetrics] = {}
            stale_count = 0

            for sym, tick in self._ticks.items():
                age_ms = (now - tick.timestamp).total_seconds() * 1000.0
                is_stale = age_ms > max_staleness_ms
                if is_stale:
                    stale_count += 1

                # Calculate tick frequency
                total_ticks = self._tick_counts.get(sym, 1)
                first_time = self._first_tick_times.get(sym, now)
                elapsed_sec = max((now - first_time).total_seconds(), 1.0)
                freq = round(total_ticks / elapsed_sec, 2)

                if age_ms > max_staleness_ms * 3:
                    feed_status = FeedHealthStatus.DISCONNECTED
                elif is_stale:
                    feed_status = FeedHealthStatus.STALE
                elif age_ms > (max_staleness_ms * 0.6):
                    feed_status = FeedHealthStatus.DEGRADED
                else:
                    feed_status = FeedHealthStatus.HEALTHY

                symbol_metrics[sym] = SymbolFeedMetrics(
                    symbol=sym,
                    feed_status=feed_status,
                    last_tick_timestamp=tick.timestamp,
                    age_ms=round(age_ms, 2),
                    is_stale=is_stale,
                    total_ticks_received=total_ticks,
                    tick_frequency_per_sec=freq,
                )

            # Determine overall system feed health
            if not self._ticks:
                overall_status = FeedHealthStatus.DISCONNECTED
                is_trading_paused = True
            elif stale_count > 0:
                overall_status = FeedHealthStatus.STALE
                is_trading_paused = True
            else:
                overall_status = FeedHealthStatus.HEALTHY
                is_trading_paused = False

            return MarketDataStalenessReport(
                overall_status=overall_status,
                max_staleness_ms=max_staleness_ms,
                is_trading_paused=is_trading_paused,
                stale_symbols_count=stale_count,
                symbols=symbol_metrics,
                timestamp=now,
            )


# Global singleton feed
in_memory_market_feed = InMemoryMarketDataFeed()
