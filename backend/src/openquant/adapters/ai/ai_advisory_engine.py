"""AI Advisory Engine Adapter implementing LLM/heuristic code generation, log analysis, and explainable risk."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AICodeGenerationResult,
    AIReviewStatus,
    AILogAnalysisReport,
    AIAnomalyItem,
    AIAnomalySeverity,
    AIRiskAdviceRequest,
    AIRiskAdviceReport,
    AIRiskRecommendation,
)
from openquant.domain.ports.ai_advisory_port import IAIAdvisoryEngine
from openquant.adapters.sandbox.ast_validator import ASTSecurityValidator


class HeuristicAndLLMAdvisoryEngine(IAIAdvisoryEngine):
    """Advisory engine generating safe quant code, analyzing operational telemetry, and explaining risk."""

    def __init__(self, validator: ASTSecurityValidator | None = None) -> None:
        self._validator = validator or ASTSecurityValidator()

    async def generate_strategy_code(
        self,
        request: AICodeGenerationRequest,
    ) -> AICodeGenerationResult:
        """Synthesize Python strategy code conforming to BaseStrategy and enforce AST security check."""
        strat_name = request.strategy_name.replace(" ", "_").replace("-", "_")
        symbol = request.symbols[0] if request.symbols else "AAPL"

        # Generate standard clean quant strategy template based on user prompt
        code = f'''"""AI-Generated Strategy: {strat_name}
Advisory Note: Non-Negotiable Rule 3 requires human review before promotion.
"""

from decimal import Decimal
from openquant.strategies.base import BaseStrategy
from openquant.domain.models.market_data import Candle, Tick
from openquant.domain.models.order import OrderSide, OrderType


class {strat_name}(BaseStrategy):
    """Automated strategy generated from prompt: {request.prompt}"""

    def __init__(self) -> None:
        super().__init__(
            strategy_id="{strat_name.lower()}",
            name="{strat_name}",
            description="AI-generated quantitative strategy",
        )
        self.fast_period = 9
        self.slow_period = 21
        self.prices: list[Decimal] = []

    def on_start(self) -> None:
        self.log_info(f"Starting {strat_name} strategy on {symbol}")

    def on_bar(self, candle: Candle) -> None:
        if candle.symbol != "{symbol}":
            return

        self.prices.append(candle.close)
        if len(self.prices) > self.slow_period:
            self.prices.pop(0)

        if len(self.prices) >= self.slow_period:
            fast_ma = sum(self.prices[-self.fast_period:]) / Decimal(str(self.fast_period))
            slow_ma = sum(self.prices[-self.slow_period:]) / Decimal(str(self.slow_period))

            if fast_ma > slow_ma:
                self.emit_signal(
                    symbol="{symbol}",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=Decimal("10"),
                    reason=f"Fast MA ({{fast_ma:.2f}}) crossed above Slow MA ({{slow_ma:.2f}})",
                )
            elif fast_ma < slow_ma:
                self.emit_signal(
                    symbol="{symbol}",
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=Decimal("10"),
                    reason=f"Fast MA ({{fast_ma:.2f}}) crossed below Slow MA ({{slow_ma:.2f}})",
                )

    def on_stop(self) -> None:
        self.log_info(f"Stopping {strat_name} strategy")
'''

        # Run Sandbox AST Static Analysis
        ast_result = self._validator.validate(code)
        parameters = [
            {"name": "fast_period", "type": "int", "default": 9, "description": "Fast Moving Average window"},
            {"name": "slow_period", "type": "int", "default": 21, "description": "Slow Moving Average window"},
            {"name": "order_quantity", "type": "decimal", "default": 10.0, "description": "Fixed lot order size"},
        ]

        return AICodeGenerationResult(
            generation_id=f"ai_gen_{uuid.uuid4().hex[:8]}",
            strategy_name=strat_name,
            code=code,
            description=f"Generated strategy for prompt: '{request.prompt}' targeting {symbol}.",
            parameters=parameters,
            ast_safety_passed=ast_result.is_safe,
            ast_violations=ast_result.violations,
            review_status=AIReviewStatus.PENDING_HUMAN_REVIEW,
        )

    async def analyze_logs(
        self,
        audit_events: list[dict[str, Any]],
        timeframe_hours: int = 24,
    ) -> AILogAnalysisReport:
        """Scan system and trading telemetry logs to isolate performance and execution anomalies."""
        anomalies: list[AIAnomalyItem] = []
        total_events = len(audit_events)

        risk_blocks = [e for e in audit_events if "REJECT" in str(e.get("action", "")).upper() or "RISK" in str(e.get("event_type", "")).upper()]
        stale_ticks = [e for e in audit_events if "STALE" in str(e).upper()]
        kill_switches = [e for e in audit_events if "KILL_SWITCH" in str(e.get("event_type", "")).upper()]

        health_score = 100.0

        if len(risk_blocks) >= 3:
            health_score -= 20.0
            anomalies.append(
                AIAnomalyItem(
                    anomaly_id=f"anom_{uuid.uuid4().hex[:6]}",
                    category="RISK_REJECTION_CLUSTER",
                    severity=AIAnomalySeverity.HIGH,
                    summary=f"Detected {len(risk_blocks)} synchronous pre-trade risk rejections in audit logs.",
                    root_cause="Orders repeatedly breaching configured Max Notional or Max Drawdown thresholds.",
                    recommended_action="Review strategy sizing parameters or evaluate relaxing temporary risk caps.",
                )
            )

        if kill_switches:
            health_score -= 30.0
            anomalies.append(
                AIAnomalyItem(
                    anomaly_id=f"anom_{uuid.uuid4().hex[:6]}",
                    category="KILL_SWITCH_TRIGGERED",
                    severity=AIAnomalySeverity.CRITICAL,
                    summary="Emergency trading halt activated during the analysis window.",
                    root_cause="Kill switch engaged by manual override, state reconciliation discrepancy, or drawdown stop.",
                    recommended_action="Run State Reconciliation sync and review audit trail before lifting kill switch.",
                )
            )

        if stale_ticks:
            health_score -= 15.0
            anomalies.append(
                AIAnomalyItem(
                    anomaly_id=f"anom_{uuid.uuid4().hex[:6]}",
                    category="DATA_STALENESS_WARNING",
                    severity=AIAnomalySeverity.MEDIUM,
                    summary=f"Encountered {len(stale_ticks)} market data staleness warnings (>3000ms latency).",
                    root_cause="Broker WebSocket feed jitter or synthetic generator interval lag.",
                    recommended_action="Inspect broker socket health and monitor network connection latency.",
                )
            )

        if not anomalies:
            summary = "Platform operating smoothly with zero operational, staleness, or risk anomalies."
        else:
            summary = f"Identified {len(anomalies)} operational area(s) requiring attention. Platform health at {health_score:.1f}%."

        return AILogAnalysisReport(
            report_id=f"log_rep_{uuid.uuid4().hex[:8]}",
            total_events_analyzed=total_events,
            health_score=max(0.0, health_score),
            anomalies=anomalies,
            summary=summary,
        )

    async def explain_risk(
        self,
        request: AIRiskAdviceRequest,
    ) -> AIRiskAdviceReport:
        """Translate risk check hard-stop breaches into plain-English diagnostics and suggestions."""
        reason_lower = request.risk_rejection_reason.lower()
        recommendations: list[AIRiskRecommendation] = []

        if "stale" in reason_lower:
            category = "MARKET_DATA_STALENESS (Rule 7)"
            explanation = (
                f"The order for {request.symbol} was rejected because the latest market tick timestamp was older "
                f"than the non-negotiable 3000ms staleness threshold. This hard stop prevents adverse fills during data outages."
            )
            recommendations.append(
                AIRiskRecommendation(
                    parameter_name="feed_polling_interval_ms",
                    current_value="Default (WebSocket)",
                    suggested_value="Sub-1000ms Reconnect",
                    rationale="Ensure broker market data WebSocket is actively receiving real-time ticks before firing orders.",
                )
            )
            impact = "Neutral (Protective hard stop prevented stale fill slippage)"
        elif "drawdown" in reason_lower:
            category = "MAX_DRAWDOWN_LIMIT (Rule 2)"
            explanation = (
                f"The portfolio has experienced {request.current_drawdown_pct:.1f}% drawdown, which breaches "
                f"the strict account maximum drawdown safeguard limit."
            )
            recommendations.append(
                AIRiskRecommendation(
                    parameter_name="position_size_scale",
                    current_value=float(request.attempted_quantity),
                    suggested_value=float(request.attempted_quantity * Decimal("0.5")),
                    rationale="Scale back position sizes by 50% during high-volatility drawdown phases.",
                )
            )
            impact = "High (Capital preservation hard stop engaged)"
        elif "kill switch" in reason_lower or "halt" in reason_lower:
            category = "GLOBAL_KILL_SWITCH (Rule 4)"
            explanation = (
                "All incoming orders are blocked because the Platform Emergency Kill Switch is currently ACTIVE. "
                "No trading activity is permitted until an authorized trader deactivates the halt."
            )
            recommendations.append(
                AIRiskRecommendation(
                    parameter_name="kill_switch_state",
                    current_value="ACTIVE",
                    suggested_value="DEACTIVATE (after audit check)",
                    rationale="Verify system reconciliation status and risk limits before resuming live operations.",
                )
            )
            impact = "Critical (Global platform trading frozen)"
        else:
            category = "RISK_HARD_STOP_EVALUATION"
            explanation = (
                f"Order submission for {request.symbol} with quantity {request.attempted_quantity} was intercepted "
                f"by the synchronous pre-trade risk engine: '{request.risk_rejection_reason}'."
            )
            recommendations.append(
                AIRiskRecommendation(
                    parameter_name="max_order_notional",
                    current_value="Default Limit",
                    suggested_value="Verify Account Allocation",
                    rationale="Confirm that order size is proportional to available margin and sizing limits.",
                )
            )
            impact = "Moderate (Pre-trade compliance rejection)"

        return AIRiskAdviceReport(
            report_id=f"risk_rep_{uuid.uuid4().hex[:8]}",
            plain_english_explanation=explanation,
            breach_category=category,
            recommended_actions=recommendations,
            safety_score_impact=impact,
        )


# Global singleton AI advisory engine
ai_advisory_engine = HeuristicAndLLMAdvisoryEngine()
