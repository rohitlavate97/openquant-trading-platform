"""Domain port interfaces for market data ingestion, staleness detection, and candle aggregation."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from openquant.domain.models.market_data import (
    Tick,
    Candle,
    CandleTimeframe,
    MarketDataStalenessReport,
    SymbolFeedMetrics,
)


class IMarketDataPort(ABC):
    """Abstract interface for market data ingestion and realtime cache."""

    @abstractmethod
    async def ingest_tick(self, tick: Tick) -> None:
        """Process incoming raw market tick, validate timestamp, and update cache."""
        pass

    @abstractmethod
    async def get_latest_tick(self, symbol: str) -> Tick | None:
        """Retrieve most recent tick for a given instrument symbol."""
        pass

    @abstractmethod
    async def get_all_latest_ticks(self) -> dict[str, Tick]:
        """Retrieve latest ticks for all tracked instruments."""
        pass

    @abstractmethod
    async def evaluate_staleness(self, max_staleness_ms: int = 3000) -> MarketDataStalenessReport:
        """Evaluate feed health and check if any symbol exceeds staleness threshold."""
        pass

    @abstractmethod
    async def is_symbol_stale(self, symbol: str, max_staleness_ms: int = 3000) -> bool:
        """Check if an individual symbol's latest tick is stale."""
        pass


class ICandleAggregatorPort(ABC):
    """Abstract interface for streaming tick-to-candle OHLCV bar aggregation."""

    @abstractmethod
    async def process_tick(self, tick: Tick) -> list[Candle]:
        """Aggregate tick into open bars; return newly completed candles if bar closed."""
        pass

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: CandleTimeframe,
        limit: int = 100,
    ) -> list[Candle]:
        """Retrieve completed and in-progress historical candles."""
        pass
