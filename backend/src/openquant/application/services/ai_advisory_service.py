"""Application Service coordinating the AI Advisory Suite with Human-in-the-Loop review and Risk/Audit integrations."""

import logging
from datetime import datetime, timezone
from typing import Any

from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AICodeGenerationResult,
    AIReviewStatus,
    AILogAnalysisReport,
    AILogAnalysisRequest,
    AIRiskAdviceRequest,
    AIRiskAdviceReport,
)
from openquant.domain.ports.ai_advisory_port import IAIAdvisoryEngine
from openquant.adapters.ai.ai_advisory_engine import ai_advisory_engine
from openquant.application.services.audit_service import audit_log_service, AuditLogService
from openquant.application.services.strategy_service import strategy_service, StrategyService

logger = logging.getLogger(__name__)


class AIAdvisoryService:
    """Service managing AI strategy synthesis with human review guardrails, log diagnostics, and risk advisory."""

    def __init__(
        self,
        engine: IAIAdvisoryEngine | None = None,
        audit: AuditLogService | None = None,
        strategy_svc: StrategyService | None = None,
    ) -> None:
        self._engine = engine or ai_advisory_engine
        self._audit = audit or audit_log_service
        self._strategy_svc = strategy_svc or strategy_service
        self._generations_store: dict[str, AICodeGenerationResult] = {}

    async def generate_strategy(
        self,
        request: AICodeGenerationRequest,
        actor_id: str = "system",
    ) -> AICodeGenerationResult:
        """Generate strategy code with sandbox AST validation and mandatory human review requirement (Rule 3)."""
        result = await self._engine.generate_strategy_code(request)
        self._generations_store[result.generation_id] = result

        await self._audit.log_event(
            event_type="AI_STRATEGY_GENERATED",
            actor_id=actor_id,
            entity_type="AI_STRATEGY",
            entity_id=result.generation_id,
            action="GENERATE",
            payload={
                "strategy_name": result.strategy_name,
                "ast_safety_passed": result.ast_safety_passed,
                "review_status": result.review_status.value,
            },
        )
        return result

    async def approve_generated_code(
        self,
        generation_id: str,
        reviewer_id: str,
        import_as_draft: bool = True,
    ) -> AICodeGenerationResult:
        """Explicit Human Review & Approval workflow (Non-Negotiable Rule 3)."""
        gen = self._generations_store.get(generation_id)
        if not gen:
            raise ValueError(f"Generation '{generation_id}' not found.")

        if not gen.ast_safety_passed:
            raise ValueError(f"Cannot approve strategy '{gen.strategy_name}': Failed AST security analysis.")

        gen.review_status = AIReviewStatus.APPROVED_BY_HUMAN
        gen.reviewed_by = reviewer_id
        gen.reviewed_at = datetime.now(timezone.utc)

        # Optionally register into strategy management store as a Draft strategy
        if import_as_draft:
            try:
                await self._strategy_svc.create_strategy(
                    name=gen.strategy_name,
                    source_code=gen.code,
                    description=gen.description,
                    author_id=reviewer_id,
                )
            except Exception as e:
                logger.warning("Failed to automatically register strategy draft: %s", e)

        await self._audit.log_event(
            event_type="AI_STRATEGY_APPROVED_BY_HUMAN",
            actor_id=reviewer_id,
            entity_type="AI_STRATEGY",
            entity_id=generation_id,
            action="HUMAN_APPROVAL",
            payload={"strategy_name": gen.strategy_name, "imported_as_draft": import_as_draft},
        )
        return gen

    async def analyze_platform_logs(
        self,
        request: AILogAnalysisRequest | None = None,
    ) -> AILogAnalysisReport:
        """Perform automated audit and telemetry log scanning."""
        req = request or AILogAnalysisRequest()
        events = await self._audit.list_audit_logs(limit=100)
        # Convert event entities/dicts to normalized dictionaries for analysis
        dict_events = [
            {
                "event_id": e.get("log_id", e.get("id", "evt_1")) if isinstance(e, dict) else getattr(e, "log_id", "evt_1"),
                "event_type": e.get("event_type", "UNKNOWN") if isinstance(e, dict) else getattr(e, "event_type", "UNKNOWN"),
                "action": e.get("action", "UNKNOWN") if isinstance(e, dict) else getattr(e, "action", "UNKNOWN"),
                "actor_id": e.get("actor_id", "system") if isinstance(e, dict) else getattr(e, "actor_id", "system"),
                "payload": e.get("payload", {}) if isinstance(e, dict) else getattr(e, "payload", {}),
            }
            for e in events
        ]
        return await self._engine.analyze_logs(dict_events, req.timeframe_hours)

    async def explain_risk_rejection(
        self,
        request: AIRiskAdviceRequest,
    ) -> AIRiskAdviceReport:
        """Provide natural language risk rejection diagnosis and parameter optimization advice."""
        return await self._engine.explain_risk(request)


# Global singleton AI advisory service
ai_advisory_service = AIAdvisoryService()
