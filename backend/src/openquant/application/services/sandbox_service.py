"""Application service for Strategy Execution Sandbox and AST Security Validation."""

import uuid
from typing import Any
from openquant.domain.ports.strategy_sandbox import (
    IStrategySandbox,
    SandboxExecutionResult,
    SandboxSecurityCheckResult,
)
from openquant.adapters.sandbox.runner import strategy_sandbox_runner, StrategySandboxRunner
from openquant.application.services.audit_service import audit_log_service, AuditLogService


STRATEGY_TEMPLATES = {
    "momentum": {
        "name": "Exponential Moving Average Momentum",
        "description": "Calculates 9-period and 21-period EMAs and emits BUY/SELL trading signals.",
        "code": '''# Exponential Moving Average Momentum Strategy
# Input context contains: context['prices'], context['symbol']

prices = context.get('prices', [180.0, 181.5, 183.0, 182.5, 184.0, 185.5, 187.0])
symbol = context.get('symbol', 'AAPL')

def calculate_sma(data, period):
    if len(data) < period:
        return sum(data) / len(data)
    return sum(data[-period:]) / period

fast_ma = calculate_sma(prices, 3)
slow_ma = calculate_sma(prices, 5)

signal = "HOLD"
if fast_ma > slow_ma:
    signal = "BUY"
elif fast_ma < slow_ma:
    signal = "SELL"

print(f"Evaluated {symbol}: Fast SMA={fast_ma:.2f}, Slow SMA={slow_ma:.2f} -> Signal={signal}")

result = {
    "symbol": symbol,
    "fast_ma": round(fast_ma, 2),
    "slow_ma": round(slow_ma, 2),
    "signal": signal,
    "confidence": 0.85
}
''',
    },
    "mean_reversion": {
        "name": "RSI Mean Reversion",
        "description": "Calculates Relative Strength Index (RSI) to capture overbought (>70) and oversold (<30) reversals.",
        "code": '''# RSI Mean Reversion Strategy
prices = context.get('prices', [150.0, 148.5, 147.0, 146.0, 145.5, 145.0, 144.5, 146.0, 147.5])
symbol = context.get('symbol', 'TSLA')

gains = []
losses = []
for i in range(1, len(prices)):
    diff = prices[i] - prices[i - 1]
    if diff >= 0:
        gains.append(diff)
        losses.append(0.0)
    else:
        gains.append(0.0)
        losses.append(abs(diff))

avg_gain = sum(gains) / len(gains) if gains else 0.0
avg_loss = sum(losses) / len(losses) if losses else 0.0001
rs = avg_gain / avg_loss
rsi = 100.0 - (100.0 / (1.0 + rs))

signal = "HOLD"
if rsi < 30.0:
    signal = "BUY" # Oversold
elif rsi > 70.0:
    signal = "SELL" # Overbought

print(f"RSI for {symbol} is {rsi:.2f} -> Signal: {signal}")

result = {
    "symbol": symbol,
    "rsi": round(rsi, 2),
    "signal": signal,
    "action": "ENTER_LONG" if signal == "BUY" else "EXIT_LONG"
}
''',
    },
    "breakout": {
        "name": "Donchian Channel Breakout",
        "description": "Identifies 20-period price breakout channels for trend-following entries.",
        "code": '''# Donchian Channel Breakout Strategy
prices = context.get('prices', [100.0, 102.0, 101.5, 103.0, 104.5, 106.0, 108.0])
current_price = prices[-1]
symbol = context.get('symbol', 'NVDA')

channel_high = max(prices[:-1])
channel_low = min(prices[:-1])

signal = "HOLD"
if current_price > channel_high:
    signal = "BUY" # Breakout above resistance
elif current_price < channel_low:
    signal = "SELL" # Breakdown below support

print(f"{symbol} Price={current_price} vs High={channel_high}, Low={channel_low} -> Signal={signal}")

result = {
    "symbol": symbol,
    "channel_high": channel_high,
    "channel_low": channel_low,
    "current_price": current_price,
    "signal": signal
}
''',
    },
}


class StrategySandboxService:
    """Application Service governing strategy static analysis and isolated execution."""

    def __init__(
        self,
        runner: IStrategySandbox = strategy_sandbox_runner,
        audit: AuditLogService = audit_log_service,
    ) -> None:
        self._runner = runner
        self._audit = audit

    def validate_code(self, source_code: str) -> SandboxSecurityCheckResult:
        """Perform static AST security validation on strategy Python code."""
        return self._runner.validate_code_ast(source_code)

    async def execute_strategy(
        self,
        source_code: str,
        context: dict[str, Any] | None = None,
        strategy_id: str | None = None,
        timeout_seconds: int = 10,
        actor_id: str = "system",
    ) -> SandboxExecutionResult:
        """Validate and execute strategy source code inside isolated sandbox."""
        strat_id = strategy_id or f"strat_{uuid.uuid4().hex[:8]}"
        ctx = context or {}

        # 1. Static AST analysis
        sec_result = self.validate_code(source_code)
        if not sec_result.is_safe:
            await self._audit.log_event(
                event_type="SANDBOX_SECURITY_VIOLATION",
                actor_id=actor_id,
                entity_type="STRATEGY",
                entity_id=strat_id,
                action="BLOCK",
                severity="HIGH",
                payload={"violations": sec_result.violations},
            )
            return SandboxExecutionResult(
                success=False,
                execution_time_seconds=0.0,
                memory_used_mb=0.0,
                cpu_time_seconds=0.0,
                output=None,
                error_message=f"AST Security Violation: {'; '.join(sec_result.violations)}",
                resource_limit_exceeded=False,
            )

        # 2. Execute isolated
        exec_res = await self._runner.execute_isolated(
            strategy_id=strat_id,
            source_code=source_code,
            context=ctx,
            timeout_seconds=timeout_seconds,
        )

        await self._audit.log_event(
            event_type="STRATEGY_SANDBOX_EXECUTED",
            actor_id=actor_id,
            entity_type="STRATEGY",
            entity_id=strat_id,
            action="EXECUTE",
            status="SUCCESS" if exec_res.success else "FAILED",
            payload={
                "success": exec_res.success,
                "execution_time_seconds": exec_res.execution_time_seconds,
                "error_message": exec_res.error_message,
            },
        )

        return exec_res

    def get_templates(self) -> dict[str, Any]:
        """Return library of standard strategy starter templates."""
        return STRATEGY_TEMPLATES


# Global SandboxService singleton
sandbox_service = StrategySandboxService()
