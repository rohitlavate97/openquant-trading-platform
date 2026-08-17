"""Domain models for real-time and historical market data."""

from datetime import datetime, timezone
from enum import StrEnum
from decimal import Decimal
from pydantic import BaseModel, Field


class InstrumentType(StrEnum):
    """Financial asset class."""
    EQUITY = "EQUITY"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    COMMODITY = "COMMODITY"


class CandleTimeframe(StrEnum):
    """Standardized OHLCV aggregation timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class FeedHealthStatus(StrEnum):
    """Real-time market data feed health state."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    DISCONNECTED = "DISCONNECTED"


class Instrument(BaseModel):
    """Financial instrument metadata."""
    symbol: str
    broker_symbol: str
    name: str
    instrument_type: InstrumentType
    exchange: str
    currency: str = "USD"
    tick_size: Decimal = Decimal("0.01")
    lot_size: Decimal = Decimal("1.0")
    min_order_quantity: Decimal = Decimal("1.0")
    max_order_quantity: Decimal = Decimal("100000.0")
    is_tradable: bool = True


class Tick(BaseModel):
    """Atomic market price update (L1 market data)."""
    symbol: str
    exchange: str = "NSE"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_price: Decimal
    last_quantity: Decimal = Decimal("0")
    bid_price: Decimal | None = None
    bid_quantity: Decimal | None = None
    ask_price: Decimal | None = None
    ask_quantity: Decimal | None = None
    volume: Decimal = Decimal("0")

    def is_stale(self, max_staleness_ms: int) -> bool:
        """Check if market tick age exceeds maximum staleness limit."""
        now = datetime.now(timezone.utc)
        age_ms = (now - self.timestamp).total_seconds() * 1000.0
        return age_ms > max_staleness_ms


class Candle(BaseModel):
    """Aggregated OHLCV bar."""
    symbol: str
    timeframe: CandleTimeframe
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class SymbolFeedMetrics(BaseModel):
    """Staleness and throughput metrics for a single market instrument."""
    symbol: str
    feed_status: FeedHealthStatus
    last_tick_timestamp: datetime
    age_ms: float
    is_stale: bool
    total_ticks_received: int = 0
    tick_frequency_per_sec: float = 0.0


class MarketDataStalenessReport(BaseModel):
    """System-wide market data staleness evaluation report."""
    overall_status: FeedHealthStatus
    max_staleness_ms: int = 3000
    is_trading_paused: bool = False
    stale_symbols_count: int = 0
    symbols: dict[str, SymbolFeedMetrics] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
