import pytest
from openquant.application.services.ai_advisory_service import AIAdvisoryService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.domain.models.ai_advisory import (
    AICodeGenerationRequest,
    AIReviewStatus,
    AIRiskAdviceRequest,
)


@pytest.fixture
def advisory_svc():
    audit_repo = InMemoryAuditLogRepository()
    audit_svc = AuditLogService(audit_repo=audit_repo)
    return AIAdvisoryService(audit=audit_svc)


@pytest.mark.asyncio
async def test_ai_advisory_service_generate_and_approve_workflow(advisory_svc):
    req = AICodeGenerationRequest(
        prompt="RSI mean reversion with Bollinger Bands on AAPL",
        strategy_name="RSI_BB_Reversion",
        symbols=["AAPL"],
    )

    # 1. Generate code - initially PENDING_HUMAN_REVIEW
    gen_result = await advisory_svc.generate_strategy(req, actor_id="quant_dev_1")
    assert gen_result.review_status == AIReviewStatus.PENDING_HUMAN_REVIEW
    assert gen_result.ast_safety_passed is True

    # 2. Approve code - sets APPROVED_BY_HUMAN
    approved = await advisory_svc.approve_generated_code(
        generation_id=gen_result.generation_id,
        reviewer_id="head_trader_1",
        import_as_draft=False,
    )
    assert approved.review_status == AIReviewStatus.APPROVED_BY_HUMAN
    assert approved.reviewed_by == "head_trader_1"
    assert approved.reviewed_at is not None


@pytest.mark.asyncio
async def test_ai_advisory_service_log_and_risk_analysis(advisory_svc):
    # Log analysis
    report = await advisory_svc.analyze_platform_logs()
    assert report.total_events_analyzed >= 0

    # Risk explanation
    risk_req = AIRiskAdviceRequest(
        risk_rejection_reason="Rule 4 Violation: Emergency Kill Switch is ACTIVE",
        symbol="SPY",
    )
    risk_rep = await advisory_svc.explain_risk_rejection(risk_req)
    assert "Rule 4" in risk_rep.breach_category
    assert "ACTIVE" in risk_rep.plain_english_explanation
