"""Base class and context interfaces for Python Quantitative Trading Strategies."""

from abc import ABC
from decimal import Decimal
from typing import Any
import logging
from openquant.domain.models.market_data import Tick, Candle
from openquant.domain.models.order import (
    OrderRequest,
    OrderSide,
    OrderType,
    TimeInForce,
    OrderExecutionReport,
)
from openquant.domain.models.strategy import StrategySignal

logger = logging.getLogger(__name__)


class StrategyContext:
    """Runtime Context provided to strategy lifecycle hooks for accessing data, logging, and dispatching orders."""

    def __init__(
        self,
        strategy_id: str,
        account_id: str,
        broker_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.strategy_id = strategy_id
        self.account_id = account_id
        self.broker_id = broker_id
        self.parameters = parameters or {}
        self.custom_state: dict[str, Any] = {}
        self.signals_generated: list[StrategySignal] = []
        self.orders_submitted: list[OrderRequest] = []
        self.log_messages: list[str] = []

    def log(self, message: str) -> None:
        """Record diagnostic log for the strategy."""
        entry = f"[{self.strategy_id}] {message}"
        self.log_messages.append(entry)
        logger.info(entry)

    def emit_signal(
        self,
        symbol: str,
        signal_type: str,
        confidence: float = 1.0,
        suggested_quantity: Decimal | None = None,
        suggested_price: Decimal | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StrategySignal:
        """Emit a trading signal."""
        sig = StrategySignal(
            symbol=symbol,
            signal_type=signal_type.upper(),
            confidence=confidence,
            suggested_quantity=suggested_quantity,
            suggested_price=suggested_price,
            metadata=metadata or {},
        )
        self.signals_generated.append(sig)
        self.log(f"Signal emitted: {sig.signal_type} {sig.symbol} (confidence: {sig.confidence})")
        return sig

    def buy(
        self,
        symbol: str,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        idempotency_key: str | None = None,
    ) -> OrderRequest:
        """Create a BUY order request."""
        import uuid
        key = idempotency_key or f"strat_buy_{self.strategy_id}_{uuid.uuid4().hex[:8]}"
        req = OrderRequest(
            idempotency_key=key,
            account_id=self.account_id,
            broker_id=self.broker_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            strategy_id=self.strategy_id,
        )
        self.orders_submitted.append(req)
        self.emit_signal(symbol=symbol, signal_type="BUY", suggested_quantity=quantity, suggested_price=price)
        return req

    def sell(
        self,
        symbol: str,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        idempotency_key: str | None = None,
    ) -> OrderRequest:
        """Create a SELL order request."""
        import uuid
        key = idempotency_key or f"strat_sell_{self.strategy_id}_{uuid.uuid4().hex[:8]}"
        req = OrderRequest(
            idempotency_key=key,
            account_id=self.account_id,
            broker_id=self.broker_id,
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            strategy_id=self.strategy_id,
        )
        self.orders_submitted.append(req)
        self.emit_signal(symbol=symbol, signal_type="SELL", suggested_quantity=quantity, suggested_price=price)
        return req


class BaseStrategy(ABC):
    """Abstract Base Class for all quantitative trading strategies."""

    def on_start(self, context: StrategyContext) -> None:
        """Hook called when strategy starts execution."""
        context.log("Strategy starting...")

    def on_tick(self, tick: Tick, context: StrategyContext) -> None:
        """Hook called on every incoming market tick for subscribed symbols."""
        pass

    def on_bar(self, candle: Candle, context: StrategyContext) -> None:
        """Hook called on every completed candle bar for subscribed symbols & timeframes."""
        pass

    def on_order_event(self, report: OrderExecutionReport, context: StrategyContext) -> None:
        """Hook called when an order execution or fill update arrives."""
        context.log(f"Order event update: {report.order_id} -> {report.status}")

    def on_stop(self, context: StrategyContext) -> None:
        """Hook called when strategy stops execution."""
        context.log("Strategy stopped.")
