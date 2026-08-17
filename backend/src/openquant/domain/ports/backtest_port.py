"""Domain Port for Event-Driven Backtesting Engine and Walk-Forward Validation."""

from abc import ABC, abstractmethod
from openquant.domain.models.strategy import Strategy
from openquant.domain.models.market_data import Candle
from openquant.domain.models.backtest import (
    BacktestConfig,
    BacktestResult,
    WalkForwardResult,
)


class IBacktestEngine(ABC):
    """Port defining event-driven backtesting simulation and walk-forward validation operations."""

    @abstractmethod
    async def run_backtest(
        self,
        config: BacktestConfig,
        strategy: Strategy,
        historical_candles: list[Candle],
    ) -> BacktestResult:
        """Execute chronological event-driven backtest simulation across historical candle data."""
        pass

    @abstractmethod
    async def run_walk_forward_validation(
        self,
        config: BacktestConfig,
        strategy: Strategy,
        historical_candles: list[Candle],
        num_windows: int = 4,
        train_ratio: float = 0.7,
    ) -> WalkForwardResult:
        """Perform rolling Walk-Forward In-Sample vs Out-of-Sample efficiency validation."""
        pass
