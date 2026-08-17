"""Domain port for Quantitative Strategy Execution Engine."""

from abc import ABC, abstractmethod
from openquant.domain.models.strategy import Strategy, StrategySignal, StrategyState
from openquant.domain.models.market_data import Tick, Candle


class IStrategyEngine(ABC):
    """Port defining runtime execution operations for quantitative strategies."""

    @abstractmethod
    async def register_strategy(self, strategy: Strategy) -> bool:
        """Register a strategy instance into the runtime engine."""
        pass

    @abstractmethod
    async def start_strategy(self, strategy_id: str) -> bool:
        """Initialize and start strategy real-time event listener."""
        pass

    @abstractmethod
    async def stop_strategy(self, strategy_id: str) -> bool:
        """Halt strategy execution gracefully."""
        pass

    @abstractmethod
    async def pause_strategy(self, strategy_id: str) -> bool:
        """Temporarily pause strategy signal generation."""
        pass

    @abstractmethod
    async def process_tick(self, tick: Tick) -> list[StrategySignal]:
        """Dispatch incoming market tick to active subscribed strategies."""
        pass

    @abstractmethod
    async def process_bar(self, candle: Candle) -> list[StrategySignal]:
        """Dispatch candle close bar event to active subscribed strategies."""
        pass

    @abstractmethod
    async def get_strategy_state(self, strategy_id: str) -> StrategyState | None:
        """Retrieve current runtime execution state of a strategy."""
        pass

    @abstractmethod
    async def get_active_strategies(self) -> list[Strategy]:
        """List all strategies currently registered and active in runtime."""
        pass
