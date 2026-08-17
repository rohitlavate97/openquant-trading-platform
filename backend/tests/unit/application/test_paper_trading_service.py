"""Unit tests for Paper Trading Application Service and Stage 6 Promotion."""

import pytest
from decimal import Decimal
from openquant.application.services.paper_trading_service import PaperTradingService
from openquant.adapters.paper.paper_trading_engine import PaperTradingEngine
from openquant.application.services.strategy_service import StrategyService
from openquant.application.services.audit_service import AuditLogService
from openquant.adapters.repositories.in_memory_auth_repo import InMemoryAuditLogRepository
from openquant.domain.models.promotion import StrategyPromotionStage


@pytest.fixture
def paper_service_instance():
    engine = PaperTradingEngine()
    strat_svc = StrategyService()
    audit = AuditLogService(audit_repo=InMemoryAuditLogRepository())
    return PaperTradingService(engine=engine, strat_svc=strat_svc, audit=audit)


@pytest.mark.asyncio
async def test_paper_trading_service_flow_and_promotion(paper_service_instance):
    """Verify paper trading session management and promotion to Stage 6."""
    # 1. Create Strategy
    strat = await paper_service_instance._strategy_service.create_strategy(
        name="Paper Strategy Candidate",
        source_code="# EMAMomentumStrategy\nfast_sma = 0",
        symbols=["AAPL"],
    )

    # 2. Create Paper Account & Start Session
    acc = await paper_service_instance.create_account("Quant Alpha Paper", Decimal("150000.00"))
    session = await paper_service_instance.start_session(
        strategy_id=strat.strategy_id,
        account_id=acc.account_id,
        symbols=["AAPL"],
    )
    assert session.session_id.startswith("psess_")
    assert strat.promotion_stage == StrategyPromotionStage.PAPER_TRADING

    # 3. Test Promotion Bypass
    promoted = await paper_service_instance.promote_to_human_approval(
        session_id=session.session_id,
        bypass_criteria=True,
    )
    assert promoted is True
    assert strat.promotion_stage == StrategyPromotionStage.HUMAN_APPROVAL
