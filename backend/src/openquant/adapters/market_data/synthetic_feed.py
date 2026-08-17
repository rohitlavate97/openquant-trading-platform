"""Synthetic Market Data Generator & Historical Replay Simulator."""

import asyncio
import logging
import random
from datetime import datetime, timezone
from decimal import Decimal
from openquant.domain.models.market_data import Tick

logger = logging.getLogger("openquant.synthetic_feed")


class SyntheticMarketFeed:
    """Simulates realistic market tick streams using geometric Brownian random walks."""

    DEFAULT_BASE_PRICES: dict[str, float] = {
        "AAPL": 185.0,
        "MSFT": 420.0,
        "NVDA": 130.0,
        "RELIANCE": 2950.0,
        "INFY": 1820.0,
        "BTC-USD": 65000.0,
    }

    def __init__(self) -> None:
        self._current_prices: dict[str, float] = dict(self.DEFAULT_BASE_PRICES)
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._on_tick_callbacks: list = []

    def register_tick_callback(self, callback) -> None:
        """Register async or sync callback to receive generated ticks."""
        self._on_tick_callbacks.append(callback)

    def generate_next_tick(self, symbol: str) -> Tick:
        """Generate next tick with random walk, bid/ask spread, and realistic volume."""
        sym = symbol.upper()
        curr_price = self._current_prices.get(sym, 100.0)

        # Brownian random walk step (-0.15% to +0.15%)
        pct_change = random.gauss(0.0001, 0.0012)
        new_price = round(curr_price * (1.0 + pct_change), 2)
        self._current_prices[sym] = new_price

        spread = round(new_price * 0.0002, 2)
        bid = round(new_price - spread, 2)
        ask = round(new_price + spread, 2)
        qty = Decimal(str(random.randint(10, 500)))
        vol = Decimal(str(random.randint(5000, 200000)))

        return Tick(
            symbol=sym,
            exchange="NASDAQ" if sym in ["AAPL", "MSFT", "NVDA"] else "NSE" if sym in ["RELIANCE", "INFY"] else "CRYPTO",
            timestamp=datetime.now(timezone.utc),
            last_price=Decimal(str(new_price)),
            last_quantity=qty,
            bid_price=Decimal(str(bid)),
            bid_quantity=qty * Decimal("2"),
            ask_price=Decimal(str(ask)),
            ask_quantity=qty * Decimal("2"),
            volume=vol,
        )

    async def _run_feed_loop(self, interval_sec: float = 0.5) -> None:
        """Continuous background tick generation loop."""
        symbols = list(self._current_prices.keys())
        while self._running:
            try:
                sym = random.choice(symbols)
                tick = self.generate_next_tick(sym)

                for cb in self._on_tick_callbacks:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(tick)
                    else:
                        cb(tick)

                await asyncio.sleep(interval_sec)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in synthetic feed loop: {e}")
                await asyncio.sleep(1.0)

    def start(self, interval_sec: float = 0.5) -> None:
        """Start background synthetic feed task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_feed_loop(interval_sec))
        logger.info("Synthetic market feed started.")

    def stop(self) -> None:
        """Stop background synthetic feed."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Synthetic market feed stopped.")

    @property
    def is_running(self) -> bool:
        return self._running


# Global singleton synthetic feed
synthetic_feed = SyntheticMarketFeed()
