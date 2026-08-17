"""Dual Exponential Moving Average (EMA) Momentum Strategy."""

from decimal import Decimal
from openquant.strategies.base import BaseStrategy, StrategyContext
from openquant.domain.models.market_data import Candle, Tick


class EMAMomentumStrategy(BaseStrategy):
    """Generates BUY/SELL signals on fast and slow moving average crossovers."""

    def on_start(self, context: StrategyContext) -> None:
        context.custom_state["history"] = []
        context.custom_state["fast_period"] = int(context.parameters.get("fast_period", 3))
        context.custom_state["slow_period"] = int(context.parameters.get("slow_period", 5))
        context.custom_state["trade_qty"] = Decimal(str(context.parameters.get("trade_quantity", "10")))
        context.log(
            f"Initialized EMA Momentum Strategy: Fast={context.custom_state['fast_period']}, "
            f"Slow={context.custom_state['slow_period']}, Qty={context.custom_state['trade_qty']}"
        )

    def on_bar(self, candle: Candle, context: StrategyContext) -> None:
        history: list[float] = context.custom_state.setdefault("history", [])
        history.append(float(candle.close))

        fast_period: int = context.custom_state["fast_period"]
        slow_period: int = context.custom_state["slow_period"]

        if len(history) < slow_period:
            return

        fast_sma = sum(history[-fast_period:]) / fast_period
        slow_sma = sum(history[-slow_period:]) / slow_period

        last_signal = context.custom_state.get("last_signal")
        trade_qty = context.custom_state["trade_qty"]

        if fast_sma > slow_sma and last_signal != "BUY":
            context.custom_state["last_signal"] = "BUY"
            context.buy(symbol=candle.symbol, quantity=trade_qty)
            context.log(f"Bullish Crossover on {candle.symbol}: Fast {fast_sma:.2f} > Slow {slow_sma:.2f}")

        elif fast_sma < slow_sma and last_signal != "SELL":
            context.custom_state["last_signal"] = "SELL"
            context.sell(symbol=candle.symbol, quantity=trade_qty)
            context.log(f"Bearish Crossover on {candle.symbol}: Fast {fast_sma:.2f} < Slow {slow_sma:.2f}")
