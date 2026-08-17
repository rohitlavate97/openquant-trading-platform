"""Domain port for AI Advisory Engine (Strategy Generator, Log Analyzer, Explainable Risk Advisor)."""

from abc import ABC, abstractmethod
from typing import Any
from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AICodeGenerationResult,
    AILogAnalysisReport,
    AIRiskAdviceRequest,
    AIRiskAdviceReport,
)


class IAIAdvisoryEngine(ABC):
    """Port defining advisory AI code generation, audit pattern analysis, and risk explanation."""

    @abstractmethod
    async def generate_strategy_code(
        self,
        request: AICodeGenerationRequest,
    ) -> AICodeGenerationResult:
        """Generate quant strategy code adhering to BaseStrategy lifecycle with AST validation."""
        pass

    @abstractmethod
    async def analyze_logs(
        self,
        audit_events: list[dict[str, Any]],
        timeframe_hours: int = 24,
    ) -> AILogAnalysisReport:
        """Scan system and trading telemetry logs to isolate performance and execution anomalies."""
        pass

    @abstractmethod
    async def explain_risk(
        self,
        request: AIRiskAdviceRequest,
    ) -> AIRiskAdviceReport:
        """Translate risk check hard-stop breaches into plain-English diagnostics and suggestions."""
        pass
