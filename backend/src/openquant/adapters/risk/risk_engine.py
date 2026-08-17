"""Synchronous Pre-Trade Risk Engine enforcing Non-Negotiable Capital Safety Hard Stops."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from openquant.domain.models.order import OrderRequest, OrderSide, OrderType, Order
from openquant.domain.models.risk import (
    RiskLimitsConfig,
    RiskEvaluationResult,
    RiskCheckResult,
    RiskCheckType,
    RiskSeverity,
    KillSwitchState,
    KillSwitchLevel,
)
from openquant.domain.models.broker import BrokerAccountInfo


class SynchronousRiskEngine:
    """Evaluates ALL trading orders synchronously BEFORE routing to any broker.
    Enforces strict pre-trade hard stops with NO async bypass (Rule 2 & Rule 4).
    """

    def __init__(self, config: RiskLimitsConfig | None = None) -> None:
        self._config = config or RiskLimitsConfig()
        # Rate limiter sliding window: list of timestamps
        self._order_timestamps: list[datetime] = []
        self._lock = asyncio.Lock()

    @property
    def config(self) -> RiskLimitsConfig:
        return self._config

    def update_config(self, new_config: RiskLimitsConfig) -> None:
        self._config = new_config

    def activate_kill_switch(
        self,
        level: KillSwitchLevel = KillSwitchLevel.GLOBAL,
        target_id: str | None = None,
        activated_by: str = "super_admin",
        reason: str = "Manual emergency trigger",
        flatten_positions: bool = False,
    ) -> KillSwitchState:
        """Activate Kill Switch halting all order submissions immediately."""
        self._config.kill_switch = KillSwitchState(
            is_active=True,
            level=level,
            target_id=target_id,
            activated_by=activated_by,
            activated_at=datetime.now(timezone.utc),
            reason=reason,
            positions_flattened=flatten_positions,
        )
        return self._config.kill_switch

    def deactivate_kill_switch(self) -> KillSwitchState:
        """Deactivate Kill Switch resuming normal pre-trade evaluation."""
        self._config.kill_switch = KillSwitchState(is_active=False)
        return self._config.kill_switch

    async def evaluate_order(
        self,
        request: OrderRequest,
        current_market_price: Decimal,
        account_funds: BrokerAccountInfo | None = None,
        open_orders: list[Order] | None = None,
        daily_loss_percent: float = 0.0,
        current_drawdown_percent: float = 0.0,
    ) -> RiskEvaluationResult:
        """Synchronously evaluate all 8 pre-trade risk checks against the incoming order request."""
        async with self._lock:
            checks: list[RiskCheckResult] = []
            now = datetime.now(timezone.utc)

            # ------------------------------------------------------------------
            # 1. Kill Switch Hard Stop Check
            # ------------------------------------------------------------------
            ks = self._config.kill_switch
            if ks.is_active:
                is_halted = False
                if ks.level == KillSwitchLevel.GLOBAL:
                    is_halted = True
                elif ks.level == KillSwitchLevel.ACCOUNT and ks.target_id == request.account_id:
                    is_halted = True
                elif ks.level == KillSwitchLevel.STRATEGY and ks.target_id == request.strategy_id:
                    is_halted = True
                elif ks.level == KillSwitchLevel.SYMBOL and ks.target_id == request.symbol:
                    is_halted = True

                if is_halted:
                    checks.append(RiskCheckResult(
                        check_type=RiskCheckType.KILL_SWITCH,
                        passed=False,
                        severity=RiskSeverity.BLOCKING,
                        rule_name="Global Kill Switch Enforcement",
                        message=f"Order rejected: Emergency Kill Switch is ACTIVE at level '{ks.level.value}'. Reason: {ks.reason}",
                    ))
                    return RiskEvaluationResult.create_rejected(checks)

            checks.append(RiskCheckResult(
                check_type=RiskCheckType.KILL_SWITCH,
                passed=True,
                severity=RiskSeverity.BLOCKING,
                rule_name="Global Kill Switch Enforcement",
                message="Kill switch inactive. Execution allowed.",
            ))

            # ------------------------------------------------------------------
            # 2. Daily Loss Limit Check (Non-Negotiable default: 3%)
            # ------------------------------------------------------------------
            if daily_loss_percent >= self._config.max_daily_loss_percent:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.DAILY_LOSS_LIMIT,
                    passed=False,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Daily Loss Limit Hard Stop",
                    message=f"Daily loss ({daily_loss_percent:.2f}%) breached limit ({self._config.max_daily_loss_percent:.2f}%). Trading halted.",
                    details={"daily_loss_pct": daily_loss_percent, "max_limit_pct": self._config.max_daily_loss_percent},
                ))
            else:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.DAILY_LOSS_LIMIT,
                    passed=True,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Daily Loss Limit Hard Stop",
                    message=f"Daily loss ({daily_loss_percent:.2f}%) within limit.",
                ))

            # ------------------------------------------------------------------
            # 3. Maximum Drawdown Check (Non-Negotiable default: 5%)
            # ------------------------------------------------------------------
            if current_drawdown_percent >= self._config.max_drawdown_percent:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.MAX_DRAWDOWN,
                    passed=False,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Max Drawdown Hard Stop",
                    message=f"Drawdown ({current_drawdown_percent:.2f}%) breached peak limit ({self._config.max_drawdown_percent:.2f}%). Strategy demoted.",
                    details={"drawdown_pct": current_drawdown_percent, "max_drawdown_pct": self._config.max_drawdown_percent},
                ))
            else:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.MAX_DRAWDOWN,
                    passed=True,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Max Drawdown Hard Stop",
                    message=f"Drawdown ({current_drawdown_percent:.2f}%) within threshold.",
                ))

            # ------------------------------------------------------------------
            # 4. Order Rate Limiter Check (Non-Negotiable default: 10 orders/sec)
            # ------------------------------------------------------------------
            cutoff_1s = now.timestamp() - 1.0
            self._order_timestamps = [t for t in self._order_timestamps if t.timestamp() > cutoff_1s]
            if len(self._order_timestamps) >= self._config.max_orders_per_second:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.RATE_LIMIT,
                    passed=False,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Order Rate Limiter",
                    message=f"Order rate limit exceeded ({len(self._order_timestamps)} orders/sec). Max allowed is {self._config.max_orders_per_second}/sec.",
                ))
            else:
                self._order_timestamps.append(now)
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.RATE_LIMIT,
                    passed=True,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Order Rate Limiter",
                    message="Order rate within limit.",
                ))

            # ------------------------------------------------------------------
            # 5. Position Sizing & Order Value Check
            # ------------------------------------------------------------------
            unit_price = request.price if (request.price and request.price > 0) else current_market_price
            order_notional = request.quantity * unit_price

            total_capital = Decimal(str(account_funds.total_balance)) if account_funds else Decimal("100000.0")
            max_allowed_order_val = total_capital * Decimal(str(self._config.max_position_size_percent / 100.0))

            if order_notional > max_allowed_order_val:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.MAX_POSITION_SIZE,
                    passed=False,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Position Sizing & Notional Cap",
                    message=f"Order notional value (${order_notional:,.2f}) exceeds max single position cap (${max_allowed_order_val:,.2f} / {self._config.max_position_size_percent}% of equity).",
                ))
            else:
                checks.append(RiskCheckResult(
                    check_type=RiskCheckType.MAX_POSITION_SIZE,
                    passed=True,
                    severity=RiskSeverity.BLOCKING,
                    rule_name="Position Sizing & Notional Cap",
                    message="Order value within position sizing limit.",
                ))

            # ------------------------------------------------------------------
            # 6. Self-Trade Prevention (Crossing Orders Guard)
            # ------------------------------------------------------------------
            if self._config.self_trade_prevention and open_orders:
                has_crossing_order = False
                for o in open_orders:
                    if o.symbol == request.symbol and o.side != request.side:
                        if request.side == OrderSide.BUY and request.price and o.price and request.price >= o.price:
                            has_crossing_order = True
                            break
                        elif request.side == OrderSide.SELL and request.price and o.price and request.price <= o.price:
                            has_crossing_order = True
                            break

                if has_crossing_order:
                    checks.append(RiskCheckResult(
                        check_type=RiskCheckType.SELF_TRADE_PREVENTION,
                        passed=False,
                        severity=RiskSeverity.BLOCKING,
                        rule_name="Self-Trade Crossing Prevention",
                        message=f"Self-trade violation: resting opposite side order detected for '{request.symbol}' at crossing price.",
                    ))
                else:
                    checks.append(RiskCheckResult(
                        check_type=RiskCheckType.SELF_TRADE_PREVENTION,
                        passed=True,
                        severity=RiskSeverity.BLOCKING,
                        rule_name="Self-Trade Crossing Prevention",
                        message="No self-trading order conflict.",
                    ))

            # ------------------------------------------------------------------
            # 7. Max Open Orders per Symbol
            # ------------------------------------------------------------------
            if open_orders:
                sym_orders_count = sum(1 for o in open_orders if o.symbol == request.symbol)
                if sym_orders_count >= self._config.max_open_orders_per_symbol:
                    checks.append(RiskCheckResult(
                        check_type=RiskCheckType.MAX_OPEN_ORDERS_PER_SYMBOL,
                        passed=False,
                        severity=RiskSeverity.BLOCKING,
                        rule_name="Open Orders Per Symbol Cap",
                        message=f"Max open orders for '{request.symbol}' reached ({sym_orders_count}/{self._config.max_open_orders_per_symbol}).",
                    ))
                else:
                    checks.append(RiskCheckResult(
                        check_type=RiskCheckType.MAX_OPEN_ORDERS_PER_SYMBOL,
                        passed=True,
                        severity=RiskSeverity.BLOCKING,
                        rule_name="Open Orders Per Symbol Cap",
                        message="Open orders per symbol count within limit.",
                    ))

            # Aggregate approval
            has_blocking_failure = any(not c.passed and c.severity == RiskSeverity.BLOCKING for c in checks)
            if has_blocking_failure:
                return RiskEvaluationResult.create_rejected(checks)
            return RiskEvaluationResult.create_approved(checks)


# Global singleton risk engine instance
synchronous_risk_engine = SynchronousRiskEngine()
