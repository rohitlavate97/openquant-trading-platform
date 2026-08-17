"""Strategy Execution Engine Runtime managing strategy lifecycle and event dispatching."""

import asyncio
import logging
from typing import Any
from openquant.domain.models.strategy import Strategy, StrategySignal, StrategyState
from openquant.domain.models.market_data import Tick, Candle
from openquant.domain.models.order import OrderExecutionReport
from openquant.domain.ports.strategy_engine_port import IStrategyEngine
from openquant.domain.ports.strategy_sandbox import IStrategySandbox
from openquant.adapters.sandbox.runner import strategy_sandbox_runner
from openquant.strategies.base import BaseStrategy, StrategyContext
from openquant.strategies.ema_momentum import EMAMomentumStrategy
from openquant.strategies.rsi_mean_reversion import RSIMeanReversionStrategy

logger = logging.getLogger(__name__)


class StrategyRuntimeInstance:
    """Active runtime wrapper for a strategy instance."""

    def __init__(
        self,
        strategy: Strategy,
        instance: BaseStrategy | None,
        context: StrategyContext,
    ) -> None:
        self.strategy = strategy
        self.instance = instance
        self.context = context


class StrategyEngine(IStrategyEngine):
    """Runtime Engine coordinating strategy compilation, isolated execution, and market event ingestion."""

    def __init__(self, sandbox: IStrategySandbox | None = None) -> None:
        self._sandbox: IStrategySandbox = sandbox or strategy_sandbox_runner
        self._strategies: dict[str, Strategy] = {}
        self._instances: dict[str, StrategyRuntimeInstance] = {}
        self._lock = asyncio.Lock()

    async def register_strategy(self, strategy: Strategy) -> bool:
        """Register a strategy into the runtime engine."""
        async with self._lock:
            # 1. AST Validation
            sec = self._sandbox.validate_code_ast(strategy.source_code)
            if not sec.is_safe:
                logger.warning("Strategy %s rejected: %s", strategy.strategy_id, sec.violations)
                strategy.state = StrategyState.ERROR
                self._strategies[strategy.strategy_id] = strategy
                return False

            self._strategies[strategy.strategy_id] = strategy
            return True

    def _instantiate_strategy(self, strategy: Strategy) -> BaseStrategy:
        """Instantiate strategy instance from code or known classes."""
        # Builtin fast-path
        if "EMAMomentumStrategy" in strategy.source_code or "fast_sma" in strategy.source_code:
            return EMAMomentumStrategy()
        if "RSIMeanReversionStrategy" in strategy.source_code or "rsi" in strategy.source_code:
            return RSIMeanReversionStrategy()

        # Dynamic script executor strategy
        class DynamicScriptStrategy(BaseStrategy):
            def on_start(self, context: StrategyContext) -> None:
                context.log(f"Dynamic Strategy {strategy.name} started.")

            def on_bar(self, candle: Candle, context: StrategyContext) -> None:
                # Dynamic sandbox execution
                script_context = {
                    "prices": [float(candle.open), float(candle.high), float(candle.low), float(candle.close)],
                    "symbol": candle.symbol,
                    "candle": {"close": float(candle.close), "volume": float(candle.volume)},
                    **strategy.get_parameter_dict(),
                }
                # Run isolated
                try:
                    res = asyncio.run_coroutine_threadsafe(
                        strategy_sandbox_runner.execute_isolated(
                            strategy_id=strategy.strategy_id,
                            source_code=strategy.source_code,
                            context=script_context,
                            timeout_seconds=5,
                        ),
                        asyncio.get_running_loop(),
                    ).result(timeout=6.0)

                    if res.success and res.output and isinstance(res.output, dict):
                        sig = res.output.get("signal")
                        if sig in ["BUY", "SELL"]:
                            context.emit_signal(symbol=candle.symbol, signal_type=sig)
                except Exception as e:
                    context.log(f"Dynamic execution error: {e}")

        return DynamicScriptStrategy()

    async def start_strategy(self, strategy_id: str) -> bool:
        """Initialize and start strategy real-time event listener."""
        async with self._lock:
            strat = self._strategies.get(strategy_id)
            if not strat:
                return False

            # Create context and instance
            context = StrategyContext(
                strategy_id=strat.strategy_id,
                account_id=strat.account_id,
                broker_id=strat.broker_id,
                parameters=strat.get_parameter_dict(),
            )
            instance = self._instantiate_strategy(strat)

            try:
                instance.on_start(context)
                strat.state = StrategyState.RUNNING
                self._instances[strategy_id] = StrategyRuntimeInstance(
                    strategy=strat,
                    instance=instance,
                    context=context,
                )
                logger.info("Strategy %s started successfully", strategy_id)
                return True
            except Exception as e:
                logger.error("Failed to start strategy %s: %s", strategy_id, e)
                strat.state = StrategyState.ERROR
                return False

    async def stop_strategy(self, strategy_id: str) -> bool:
        """Halt strategy execution gracefully."""
        async with self._lock:
            strat = self._strategies.get(strategy_id)
            runtime = self._instances.get(strategy_id)
            if not strat:
                return False

            if runtime and runtime.instance:
                try:
                    runtime.instance.on_stop(runtime.context)
                except Exception as e:
                    logger.error("Error during strategy stop %s: %s", strategy_id, e)

            strat.state = StrategyState.STOPPED
            self._instances.pop(strategy_id, None)
            logger.info("Strategy %s stopped", strategy_id)
            return True

    async def pause_strategy(self, strategy_id: str) -> bool:
        """Temporarily pause strategy signal generation."""
        async with self._lock:
            strat = self._strategies.get(strategy_id)
            if not strat:
                return False
            strat.state = StrategyState.PAUSED
            return True

    async def process_tick(self, tick: Tick) -> list[StrategySignal]:
        """Dispatch incoming market tick to active subscribed strategies."""
        signals: list[StrategySignal] = []
        for strat_id, runtime in list(self._instances.items()):
            if runtime.strategy.state != StrategyState.RUNNING:
                continue
            if tick.symbol in runtime.strategy.symbols:
                try:
                    runtime.instance.on_tick(tick, runtime.context)
                    # Collect any new signals
                    if runtime.context.signals_generated:
                        signals.extend(runtime.context.signals_generated)
                        runtime.context.signals_generated = []
                except Exception as e:
                    logger.error("Error in on_tick for %s: %s", strat_id, e)
                    runtime.strategy.state = StrategyState.ERROR
        return signals

    async def process_bar(self, candle: Candle) -> list[StrategySignal]:
        """Dispatch candle close bar event to active subscribed strategies."""
        signals: list[StrategySignal] = []
        for strat_id, runtime in list(self._instances.items()):
            if runtime.strategy.state != StrategyState.RUNNING:
                continue
            if candle.symbol in runtime.strategy.symbols:
                try:
                    runtime.instance.on_bar(candle, runtime.context)
                    if runtime.context.signals_generated:
                        signals.extend(runtime.context.signals_generated)
                        runtime.context.signals_generated = []
                except Exception as e:
                    logger.error("Error in on_bar for %s: %s", strat_id, e)
                    runtime.strategy.state = StrategyState.ERROR
        return signals

    async def process_order_event(self, report: OrderExecutionReport) -> None:
        """Dispatch order execution updates to strategy instance."""
        if not report.strategy_id:
            return
        runtime = self._instances.get(report.strategy_id)
        if runtime and runtime.instance:
            try:
                runtime.instance.on_order_event(report, runtime.context)
            except Exception as e:
                logger.error("Error in on_order_event for %s: %s", report.strategy_id, e)

    async def get_strategy_state(self, strategy_id: str) -> StrategyState | None:
        """Retrieve current runtime execution state of a strategy."""
        strat = self._strategies.get(strategy_id)
        return strat.state if strat else None

    async def get_active_strategies(self) -> list[Strategy]:
        """List all strategies currently registered."""
        return list(self._strategies.values())

    async def get_strategy_runtime_logs(self, strategy_id: str) -> list[str]:
        """Retrieve collected runtime log messages from context."""
        runtime = self._instances.get(strategy_id)
        if runtime:
            return list(runtime.context.log_messages)
        return []


# Global singleton engine
strategy_engine = StrategyEngine()
