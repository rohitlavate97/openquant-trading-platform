"""Market data adapters module."""

from openquant.adapters.market_data.in_memory_feed import (
    InMemoryMarketDataFeed,
    in_memory_market_feed,
)
from openquant.adapters.market_data.candle_aggregator import (
    StreamingCandleAggregator,
    candle_aggregator,
)
from openquant.adapters.market_data.synthetic_feed import (
    SyntheticMarketFeed,
    synthetic_feed,
)

__all__ = [
    "InMemoryMarketDataFeed",
    "in_memory_market_feed",
    "StreamingCandleAggregator",
    "candle_aggregator",
    "SyntheticMarketFeed",
    "synthetic_feed",
]
