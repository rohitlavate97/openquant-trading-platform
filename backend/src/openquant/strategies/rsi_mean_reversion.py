"""Relative Strength Index (RSI) Mean Reversion Strategy."""

from decimal import Decimal
from openquant.strategies.base import BaseStrategy, StrategyContext
from openquant.domain.models.market_data import Candle, Tick


class RSIMeanReversionStrategy(BaseStrategy):
    """Generates BUY on oversold (< oversold_threshold) and SELL on overbought (> overbought_threshold)."""

    def on_start(self, context: StrategyContext) -> None:
        context.custom_state["prices"] = []
        context.custom_state["period"] = int(context.parameters.get("period", 5))
        context.custom_state["oversold"] = float(context.parameters.get("oversold_threshold", 30.0))
        context.custom_state["overbought"] = float(context.parameters.get("overbought_threshold", 70.0))
        context.custom_state["trade_qty"] = Decimal(str(context.parameters.get("trade_quantity", "10")))
        context.log(
            f"Initialized RSI Strategy: Period={context.custom_state['period']}, "
            f"Oversold={context.custom_state['oversold']}, Overbought={context.custom_state['overbought']}"
        )

    def on_bar(self, candle: Candle, context: StrategyContext) -> None:
        prices: list[float] = context.custom_state.setdefault("prices", [])
        prices.append(float(candle.close))

        period: int = context.custom_state["period"]
        if len(prices) < period + 1:
            return

        # Calculate RSI
        gains, losses = [], []
        for i in range(len(prices) - period, len(prices)):
            change = prices[i] - prices[i - 1]
            if change >= 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        oversold = context.custom_state["oversold"]
        overbought = context.custom_state["overbought"]
        trade_qty = context.custom_state["trade_qty"]
        last_action = context.custom_state.get("last_action")

        if rsi < oversold and last_action != "BUY":
            context.custom_state["last_action"] = "BUY"
            context.buy(symbol=candle.symbol, quantity=trade_qty)
            context.log(f"RSI Oversold ({rsi:.1f} < {oversold}) on {candle.symbol} -> BUY triggered")

        elif rsi > overbought and last_action != "SELL":
            context.custom_state["last_action"] = "SELL"
            context.sell(symbol=candle.symbol, quantity=trade_qty)
            context.log(f"RSI Overbought ({rsi:.1f} > {overbought}) on {candle.symbol} -> SELL triggered")
