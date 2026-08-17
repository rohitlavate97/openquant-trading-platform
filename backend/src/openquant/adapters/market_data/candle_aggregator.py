"""Real-Time Tick to OHLCV Candle Aggregator Adapter."""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from openquant.domain.models.market_data import (
    Tick,
    Candle,
    CandleTimeframe,
)
from openquant.domain.ports.market_data_port import ICandleAggregatorPort

# Map timeframes to seconds duration
TIMEFRAME_SECONDS: dict[CandleTimeframe, int] = {
    CandleTimeframe.M1: 60,
    CandleTimeframe.M5: 300,
    CandleTimeframe.M15: 900,
    CandleTimeframe.H1: 3600,
    CandleTimeframe.H4: 14400,
    CandleTimeframe.D1: 86400,
}


class StreamingCandleAggregator(ICandleAggregatorPort):
    """Aggregates streaming ticks into multi-timeframe OHLCV bars in memory."""

    def __init__(self, max_history_per_timeframe: int = 500) -> None:
        self._max_history = max_history_per_timeframe
        # Completed candles: (symbol, timeframe) -> list[Candle]
        self._completed_candles: dict[tuple[str, CandleTimeframe], list[Candle]] = {}
        # In-progress bar: (symbol, timeframe) -> dict
        self._active_bars: dict[tuple[str, CandleTimeframe], dict] = {}
        self._lock = asyncio.Lock()

    def _get_bar_start_time(self, timestamp: datetime, timeframe: CandleTimeframe) -> datetime:
        """Align timestamp to the start of the timeframe bucket."""
        seconds = TIMEFRAME_SECONDS[timeframe]
        epoch_seconds = int(timestamp.timestamp())
        bucket_seconds = (epoch_seconds // seconds) * seconds
        return datetime.fromtimestamp(bucket_seconds, tz=timezone.utc)

    async def process_tick(self, tick: Tick) -> list[Candle]:
        """Aggregate tick across all supported timeframes. Return completed candles."""
        completed: list[Candle] = []
        sym = tick.symbol.upper()

        async with self._lock:
            for tf in CandleTimeframe:
                key = (sym, tf)
                bar_start = self._get_bar_start_time(tick.timestamp, tf)

                active = self._active_bars.get(key)
                if active is None:
                    # Initialize new open bar
                    self._active_bars[key] = {
                        "symbol": sym,
                        "timeframe": tf,
                        "timestamp": bar_start,
                        "open": tick.last_price,
                        "high": tick.last_price,
                        "low": tick.last_price,
                        "close": tick.last_price,
                        "volume": tick.last_quantity or Decimal("0"),
                    }
                elif active["timestamp"] == bar_start:
                    # Update current in-progress bar
                    active["high"] = max(active["high"], tick.last_price)
                    active["low"] = min(active["low"], tick.last_price)
                    active["close"] = tick.last_price
                    active["volume"] += (tick.last_quantity or Decimal("0"))
                else:
                    # Bar has closed! Finalize previous bar
                    closed_candle = Candle(
                        symbol=active["symbol"],
                        timeframe=active["timeframe"],
                        timestamp=active["timestamp"],
                        open=active["open"],
                        high=active["high"],
                        low=active["low"],
                        close=active["close"],
                        volume=active["volume"],
                    )
                    completed.append(closed_candle)

                    # Save to historical list
                    if key not in self._completed_candles:
                        self._completed_candles[key] = []
                    self._completed_candles[key].append(closed_candle)
                    if len(self._completed_candles[key]) > self._max_history:
                        self._completed_candles[key].pop(0)

                    # Start new bar with the new tick
                    self._active_bars[key] = {
                        "symbol": sym,
                        "timeframe": tf,
                        "timestamp": bar_start,
                        "open": tick.last_price,
                        "high": tick.last_price,
                        "low": tick.last_price,
                        "close": tick.last_price,
                        "volume": tick.last_quantity or Decimal("0"),
                    }

        return completed

    async def get_candles(
        self,
        symbol: str,
        timeframe: CandleTimeframe,
        limit: int = 100,
    ) -> list[Candle]:
        """Retrieve completed candles + current live in-progress candle if available."""
        sym = symbol.upper()
        key = (sym, timeframe)

        async with self._lock:
            history = list(self._completed_candles.get(key, []))
            active = self._active_bars.get(key)
            if active:
                live_bar = Candle(
                    symbol=active["symbol"],
                    timeframe=active["timeframe"],
                    timestamp=active["timestamp"],
                    open=active["open"],
                    high=active["high"],
                    low=active["low"],
                    close=active["close"],
                    volume=active["volume"],
                )
                history.append(live_bar)

            return history[-limit:]


# Global singleton candle aggregator
candle_aggregator = StreamingCandleAggregator()
