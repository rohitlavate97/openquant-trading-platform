from decimal import Decimal
from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AICodeGenerationResult,
    AIReviewStatus,
    AILogAnalysisRequest,
    AILogAnalysisReport,
    AIAnomalyItem,
    AIAnomalySeverity,
    AIRiskAdviceRequest,
    AIRiskAdviceReport,
    AIRiskRecommendation,
)


def test_ai_code_generation_models():
    req = AICodeGenerationRequest(
        prompt="Dual EMA breakout strategy for AAPL",
        strategy_name="Dual_EMA_Breakout",
        strategy_type="TREND_FOLLOWING",
        symbols=["AAPL"],
    )
    assert req.strategy_name == "Dual_EMA_Breakout"

    res = AICodeGenerationResult(
        generation_id="gen_101",
        strategy_name="Dual_EMA_Breakout",
        code="# code",
        description="strategy description",
        ast_safety_passed=True,
        review_status=AIReviewStatus.PENDING_HUMAN_REVIEW,
    )
    assert res.review_status == AIReviewStatus.PENDING_HUMAN_REVIEW
    assert "Rule 3" in res.advisory_disclaimer


def test_ai_log_and_risk_models():
    anom = AIAnomalyItem(
        anomaly_id="anom_1",
        category="SLIPPAGE_ANOMALY",
        severity=AIAnomalySeverity.HIGH,
        summary="High slippage detected on TSLA fills.",
        root_cause="Low liquidity during pre-market session.",
        recommended_action="Restrict strategy execution to regular market hours.",
    )
    report = AILogAnalysisReport(
        report_id="rep_1",
        total_events_analyzed=100,
        health_score=85.0,
        anomalies=[anom],
        summary="Minor slippage anomalies detected.",
    )
    assert report.health_score == 85.0
    assert len(report.anomalies) == 1

    risk_req = AIRiskAdviceRequest(
        risk_rejection_reason="Rule 7 Violation: Stale tick detected (>3000ms)",
        symbol="AAPL",
        attempted_quantity=Decimal("50"),
    )
    assert risk_req.attempted_quantity == Decimal("50")

    rec = AIRiskRecommendation(
        parameter_name="feed_check_interval",
        current_value=5000,
        suggested_value=1000,
        rationale="Decrease polling interval",
    )
    risk_rep = AIRiskAdviceReport(
        report_id="r_rep_1",
        plain_english_explanation="Order was blocked due to stale market data.",
        breach_category="MARKET_DATA_STALENESS",
        recommended_actions=[rec],
        safety_score_impact="High",
    )
    assert len(risk_rep.recommended_actions) == 1
