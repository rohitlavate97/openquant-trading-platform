"""REST Endpoints for AI Advisory Suite (Strategy Generator, Mandatory Human Review, Log Analyzer, Explainable Risk Advisor)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AICodeGenerationResult,
    AILogAnalysisReport,
    AILogAnalysisRequest,
    AIRiskAdviceReport,
    AIRiskAdviceRequest,
)
from openquant.application.services.ai_advisory_service import (
    AIAdvisoryService,
    ai_advisory_service,
)
from openquant.interfaces.api.dependencies import require_permissions, get_current_user

router = APIRouter(prefix="/ai", tags=["AI Advisory Suite (Advisory Only)"])


class ApproveCodeRequest(BaseModel):
    import_as_draft: bool = True


@router.post("/generate-strategy", response_model=AICodeGenerationResult, status_code=status.HTTP_200_OK)
async def generate_strategy_endpoint(
    request: AICodeGenerationRequest,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: AIAdvisoryService = Depends(lambda: ai_advisory_service),
) -> AICodeGenerationResult:
    """Generate Python strategy code with AST security verification. Mandatory human review required (Rule 3)."""
    return await service.generate_strategy(request, actor_id=current_user.user_id)


@router.post("/approve/{generation_id}", response_model=AICodeGenerationResult)
async def approve_strategy_code_endpoint(
    generation_id: str,
    req: ApproveCodeRequest = ApproveCodeRequest(),
    current_user: User = Depends(require_permissions(Permission.STRATEGY_APPROVE)),
    service: AIAdvisoryService = Depends(lambda: ai_advisory_service),
) -> AICodeGenerationResult:
    """Explicit Human Review & Approval workflow (Non-Negotiable Rule 3)."""
    try:
        return await service.approve_generated_code(
            generation_id=generation_id,
            reviewer_id=current_user.user_id,
            import_as_draft=req.import_as_draft,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/analyze-logs", response_model=AILogAnalysisReport)
async def analyze_logs_endpoint(
    request: AILogAnalysisRequest = AILogAnalysisRequest(),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: AIAdvisoryService = Depends(lambda: ai_advisory_service),
) -> AILogAnalysisReport:
    """Perform automated audit and telemetry log scanning to isolate operational anomalies."""
    return await service.analyze_platform_logs(request)


@router.post("/explain-risk", response_model=AIRiskAdviceReport)
async def explain_risk_endpoint(
    request: AIRiskAdviceRequest,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: AIAdvisoryService = Depends(lambda: ai_advisory_service),
) -> AIRiskAdviceReport:
    """Explain pre-trade risk blocks in plain English with actionable parameter recommendations."""
    return await service.explain_risk_rejection(request)
