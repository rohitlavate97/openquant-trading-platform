"""Domain models for AI Advisory Suite (Advisory Code Generator, Log Analyzer, Explainable Risk Advisor)."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class AIReviewStatus(StrEnum):
    """Enforces Non-Negotiable Rule 3: AI code is advisory only and requires human review."""
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    APPROVED_BY_HUMAN = "APPROVED_BY_HUMAN"
    REJECTED_BY_HUMAN = "REJECTED_BY_HUMAN"


class AICodeGenerationRequest(BaseModel):
    """Prompt and context requesting AI strategy generation."""
    prompt: str = Field(..., description="Natural language strategy logic description")
    strategy_name: str = "AI_Generated_Strategy"
    strategy_type: str = "TREND_FOLLOWING"
    symbols: list[str] = Field(default_factory=lambda: ["AAPL"])


class AICodeGenerationResult(BaseModel):
    """Generated strategy code packaged with mandatory human review guardrails and AST verification."""
    generation_id: str
    strategy_name: str
    code: str
    description: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    ast_safety_passed: bool = False
    ast_violations: list[str] = Field(default_factory=list)
    review_status: AIReviewStatus = AIReviewStatus.PENDING_HUMAN_REVIEW
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    advisory_disclaimer: str = (
        "Non-Negotiable Rule 3: AI-generated code is advisory only and must never execute directly. "
        "Explicit human review and 7-stage promotion gate progression is mandatory."
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIAnomalySeverity(StrEnum):
    """Severity classification of detected operational or risk anomalies."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AIAnomalyItem(BaseModel):
    """Identified system or trading performance anomaly with root-cause analysis."""
    anomaly_id: str
    category: str  # e.g., SLIPPAGE_ANOMALY, LATENCY_SPIKE, RISK_REJECTION_CLUSTER, STALE_FEED
    severity: AIAnomalySeverity
    summary: str
    root_cause: str
    recommended_action: str


class AILogAnalysisRequest(BaseModel):
    """Request parameters for AI log and telemetry scanning."""
    timeframe_hours: int = 24
    event_types: list[str] = Field(default_factory=list)


class AILogAnalysisReport(BaseModel):
    """Comprehensive analysis report over platform execution logs and audit telemetry."""
    report_id: str
    total_events_analyzed: int
    health_score: float = 100.0  # 0.0 - 100.0 scale
    anomalies: list[AIAnomalyItem] = Field(default_factory=list)
    summary: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIRiskAdviceRequest(BaseModel):
    """Contextual input for explainable risk rejection diagnostics."""
    risk_rejection_reason: str
    account_id: str = "acc_main"
    symbol: str = "AAPL"
    attempted_quantity: Decimal = Decimal("100")
    current_drawdown_pct: float = 0.0


class AIRiskRecommendation(BaseModel):
    """Actionable risk parameter adjustment recommendation."""
    parameter_name: str
    current_value: Any
    suggested_value: Any
    rationale: str


class AIRiskAdviceReport(BaseModel):
    """Plain-English explainable risk advisor diagnosis and remediation guidance."""
    report_id: str
    plain_english_explanation: str
    breach_category: str
    recommended_actions: list[AIRiskRecommendation] = Field(default_factory=list)
    safety_score_impact: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
