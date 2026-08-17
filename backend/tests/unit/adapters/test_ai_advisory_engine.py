import pytest
from decimal import Decimal
from openquant.adapters.ai.ai_advisory_engine import HeuristicAndLLMAdvisoryEngine
from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AIReviewStatus,
    AIRiskAdviceRequest,
)


@pytest.mark.asyncio
async def test_ai_engine_generate_strategy_code_passes_ast():
    engine = HeuristicAndLLMAdvisoryEngine()
    req = AICodeGenerationRequest(
        prompt="Dual Moving Average Crossover for MSFT",
        strategy_name="Dual_MA_Cross",
        symbols=["MSFT"],
    )

    result = await engine.generate_strategy_code(req)
    assert result.strategy_name == "Dual_MA_Cross"
    assert result.ast_safety_passed is True
    assert len(result.ast_violations) == 0
    assert result.review_status == AIReviewStatus.PENDING_HUMAN_REVIEW
    assert "class Dual_MA_Cross" in result.code


@pytest.mark.asyncio
async def test_ai_engine_analyze_logs_detects_risk_and_staleness_anomalies():
    engine = HeuristicAndLLMAdvisoryEngine()

    mock_events = [
        {"action": "REJECT_ORDER", "event_type": "RISK_BREACH", "payload": {}},
        {"action": "REJECT_ORDER", "event_type": "RISK_BREACH", "payload": {}},
        {"action": "REJECT_ORDER", "event_type": "RISK_BREACH", "payload": {}},
        {"action": "KILL_SWITCH_ENGAGED", "event_type": "KILL_SWITCH", "payload": {}},
        {"action": "TICK_DROPPED_STALE", "event_type": "MARKET_DATA", "payload": {}},
    ]

    report = await engine.analyze_logs(mock_events, timeframe_hours=12)
    assert report.total_events_analyzed == 5
    assert report.health_score < 100.0
    assert len(report.anomalies) >= 2

    categories = [a.category for a in report.anomalies]
    assert "RISK_REJECTION_CLUSTER" in categories
    assert "KILL_SWITCH_TRIGGERED" in categories


@pytest.mark.asyncio
async def test_ai_engine_explain_risk_rejections():
    engine = HeuristicAndLLMAdvisoryEngine()

    # Staleness test
    stale_req = AIRiskAdviceRequest(
        risk_rejection_reason="Market data staleness threshold breached (>3000ms)",
        symbol="AAPL",
        attempted_quantity=Decimal("20"),
    )
    stale_rep = await engine.explain_risk(stale_req)
    assert "Rule 7" in stale_rep.breach_category
    assert len(stale_rep.recommended_actions) > 0

    # Drawdown test
    dd_req = AIRiskAdviceRequest(
        risk_rejection_reason="Max Drawdown stop breached (12.5% vs 10.0% max limit)",
        symbol="TSLA",
        attempted_quantity=Decimal("50"),
        current_drawdown_pct=12.5,
    )
    dd_rep = await engine.explain_risk(dd_req)
    assert "Rule 2" in dd_rep.breach_category
