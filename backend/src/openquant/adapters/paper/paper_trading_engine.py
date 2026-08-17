"""Real-Time Paper Trading Mode Engine Adapter with Latency & Slippage Modeling."""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from openquant.domain.models.market_data import Tick
from openquant.domain.models.order import OrderSide
from openquant.domain.models.paper_trading import (
    PaperAccount,
    PaperOrderExecutionConfig,
    PaperTradingGateStatus,
    PaperTradingSession,
    PaperTradingSessionStatus,
)
from openquant.domain.ports.paper_trading_port import IPaperTradingEngine
from openquant.strategies.base import BaseStrategy, StrategyContext
from openquant.strategies.ema_momentum import EMAMomentumStrategy
from openquant.strategies.rsi_mean_reversion import RSIMeanReversionStrategy

logger = logging.getLogger(__name__)


class PaperTradingEngine(IPaperTradingEngine):
    """Engine orchestrating real-time simulated strategy execution against live market feeds."""

    def __init__(self) -> None:
        self._accounts: dict[str, PaperAccount] = {}
        self._sessions: dict[str, PaperTradingSession] = {}
        self._contexts: dict[str, StrategyContext] = {}
        self._strat_instances: dict[str, BaseStrategy] = {}
        self._holdings: dict[str, dict[str, Decimal]] = {}  # session_id -> {symbol: qty}
        self._open_positions: dict[str, dict[str, dict[str, Any]]] = {}  # session_id -> {symbol: entry_dict}

        # Initialize default virtual paper account
        default_acc = PaperAccount(
            account_id="acc_paper_default",
            name="Primary Paper Account",
            initial_balance=Decimal("100000.00"),
            current_cash=Decimal("100000.00"),
            margin_used=Decimal("0.00"),
            portfolio_value=Decimal("100000.00"),
        )
        self._accounts[default_acc.account_id] = default_acc

    def _instantiate_strategy(self, strategy_id: str) -> BaseStrategy:
        """Resolve strategy instance."""
        if "rsi" in strategy_id.lower():
            return RSIMeanReversionStrategy()
        return EMAMomentumStrategy()

    async def create_paper_account(
        self,
        name: str = "Primary Paper Account",
        initial_balance: Decimal = Decimal("100000.00"),
    ) -> PaperAccount:
        """Create a new virtual paper account."""
        account_id = f"acc_paper_{uuid.uuid4().hex[:8]}"
        account = PaperAccount(
            account_id=account_id,
            name=name,
            initial_balance=initial_balance,
            current_cash=initial_balance,
            margin_used=Decimal("0.00"),
            portfolio_value=initial_balance,
        )
        self._accounts[account_id] = account
        return account

    async def get_paper_account(self, account_id: str) -> PaperAccount | None:
        """Retrieve paper account status."""
        return self._accounts.get(account_id)

    async def list_paper_accounts(self) -> list[PaperAccount]:
        """List all registered paper accounts."""
        return list(self._accounts.values())

    async def start_session(
        self,
        strategy_id: str,
        account_id: str,
        symbols: list[str],
        config: PaperOrderExecutionConfig | None = None,
    ) -> PaperTradingSession:
        """Launch a real-time paper trading session."""
        session_id = f"psess_{uuid.uuid4().hex[:8]}"
        exec_config = config or PaperOrderExecutionConfig()

        session = PaperTradingSession(
            session_id=session_id,
            strategy_id=strategy_id,
            account_id=account_id,
            status=PaperTradingSessionStatus.ACTIVE,
            execution_config=exec_config,
            symbols=symbols,
            started_at=datetime.now(timezone.utc),
        )
        self._sessions[session_id] = session
        self._holdings[session_id] = {s: Decimal("0") for s in symbols}
        self._open_positions[session_id] = {}

        context = StrategyContext(
            strategy_id=strategy_id,
            account_id=account_id,
            broker_id="paper_broker",
        )
        strat_inst = self._instantiate_strategy(strategy_id)
        strat_inst.on_start(context)

        self._contexts[session_id] = context
        self._strat_instances[session_id] = strat_inst
        return session

    async def pause_session(self, session_id: str) -> PaperTradingSession | None:
        """Pause a paper trading session."""
        session = self._sessions.get(session_id)
        if session:
            session.status = PaperTradingSessionStatus.PAUSED
        return session

    async def stop_session(self, session_id: str) -> PaperTradingSession | None:
        """Stop a paper trading session."""
        session = self._sessions.get(session_id)
        if session:
            session.status = PaperTradingSessionStatus.STOPPED
            session.stopped_at = datetime.now(timezone.utc)
            strat_inst = self._strat_instances.get(session_id)
            context = self._contexts.get(session_id)
            if strat_inst and context:
                strat_inst.on_stop(context)
        return session

    async def get_session(self, session_id: str) -> PaperTradingSession | None:
        """Retrieve paper session details."""
        return self._sessions.get(session_id)

    async def list_sessions(self) -> list[PaperTradingSession]:
        """List all paper trading sessions."""
        return list(self._sessions.values())

    async def process_market_tick(self, tick: Tick) -> None:
        """Process incoming market tick across all active paper trading sessions."""
        for session_id, session in list(self._sessions.items()):
            if session.status != PaperTradingSessionStatus.ACTIVE:
                continue
            if tick.symbol not in session.symbols:
                continue

            strat_inst = self._strat_instances.get(session_id)
            context = self._contexts.get(session_id)
            account = self._accounts.get(session.account_id)
            if not strat_inst or not context or not account:
                continue

            # 1. Dispatch tick to strategy
            strat_inst.on_tick(tick, context)

            # 2. Process emitted orders
            if context.orders_submitted:
                slippage_multiplier = Decimal(str(session.execution_config.slippage_bps)) / Decimal("10000.0")
                commission = Decimal("1.00")

                for order in context.orders_submitted:
                    sym = order.symbol
                    price = tick.last_price

                    if order.side == OrderSide.BUY:
                        fill_price = price * (Decimal("1.0") + slippage_multiplier)
                        cost = order.quantity * fill_price + commission
                        if account.current_cash >= cost:
                            account.current_cash -= cost
                            self._holdings[session_id][sym] = self._holdings[session_id].get(sym, Decimal("0")) + order.quantity
                            self._open_positions[session_id][sym] = {
                                "entry_price": fill_price,
                                "quantity": order.quantity,
                                "entry_time": tick.timestamp,
                                "commission": commission,
                            }
                    elif order.side == OrderSide.SELL:
                        current_qty = self._holdings[session_id].get(sym, Decimal("0"))
                        if current_qty > Decimal("0"):
                            qty_to_sell = min(current_qty, order.quantity)
                            fill_price = price * (Decimal("1.0") - slippage_multiplier)
                            proceeds = qty_to_sell * fill_price - commission
                            account.current_cash += proceeds
                            self._holdings[session_id][sym] = current_qty - qty_to_sell

                            open_pos = self._open_positions[session_id].pop(sym, None)
                            if open_pos:
                                gross_pnl = (fill_price - open_pos["entry_price"]) * qty_to_sell
                                net_pnl = gross_pnl - (open_pos["commission"] + commission)
                                session.total_trades += 1
                                if net_pnl > Decimal("0"):
                                    session.winning_trades += 1
                                session.realized_pnl += net_pnl

                context.orders_submitted = []

            # 3. Mark to market portfolio valuation & drawdown
            position_val = sum(
                qty * tick.last_price
                for sym, qty in self._holdings[session_id].items()
                if sym == tick.symbol
            )
            total_val = account.current_cash + position_val
            account.portfolio_value = total_val

            if total_val > session.peak_portfolio_value:
                session.peak_portfolio_value = total_val

            dd_dollars = session.peak_portfolio_value - total_val
            dd_pct = float(dd_dollars / session.peak_portfolio_value * Decimal("100.0")) if session.peak_portfolio_value > Decimal("0") else 0.0
            if dd_pct > session.max_drawdown_pct:
                session.max_drawdown_pct = round(dd_pct, 2)

    async def evaluate_gate_status(self, session_id: str) -> PaperTradingGateStatus | None:
        """Evaluate Stage 5 (PAPER_TRADING) criteria for promotion to Stage 6 (HUMAN_APPROVAL)."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # Check criteria
        days_active = max(0, (datetime.now(timezone.utc) - session.started_at).days)
        trades_count = session.total_trades
        dd_pct = session.max_drawdown_pct

        req_met: list[str] = []
        req_pending: list[str] = []

        if days_active >= 14:
            req_met.append(f"Minimum 14 live paper trading days satisfied ({days_active} days)")
        else:
            req_pending.append(f"Requires 14 days active live paper trading ({days_active}/14 completed)")

        if trades_count >= 30:
            req_met.append(f"Minimum 30 executed paper trades satisfied ({trades_count} trades)")
        else:
            req_pending.append(f"Requires minimum 30 executed paper trades ({trades_count}/30 executed)")

        if dd_pct <= 10.0:
            req_met.append(f"Max paper trading drawdown <= 10.0% satisfied ({dd_pct}%)")
        else:
            req_pending.append(f"Drawdown {dd_pct}% exceeds 10.0% maximum risk threshold")

        eligible = len(req_pending) == 0

        return PaperTradingGateStatus(
            session_id=session_id,
            strategy_id=session.strategy_id,
            days_active=days_active,
            required_days=14,
            trades_count=trades_count,
            required_trades=30,
            current_drawdown_pct=dd_pct,
            max_allowed_drawdown_pct=10.0,
            eligible_for_promotion=eligible,
            requirements_met=req_met,
            requirements_pending=req_pending,
        )


# Global singleton paper trading engine
paper_trading_engine = PaperTradingEngine()
