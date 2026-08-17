"""REST Endpoints for Real-Time Paper Trading Mode and Stage 5 Promotion Gate."""

from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.paper_trading import (
    PaperAccount,
    PaperOrderExecutionConfig,
    PaperTradingGateStatus,
    PaperTradingSession,
)
from openquant.application.services.paper_trading_service import (
    PaperTradingService,
    paper_trading_service,
)
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/paper-trading", tags=["Paper Trading Mode & Stage 5 Promotion"])


class CreatePaperAccountRequest(BaseModel):
    name: str = "Virtual Paper Account"
    initial_balance: Decimal = Decimal("100000.00")


class StartPaperSessionRequest(BaseModel):
    strategy_id: str
    account_id: str = "acc_paper_default"
    symbols: list[str] = Field(default_factory=lambda: ["AAPL"])
    config: PaperOrderExecutionConfig | None = None


class PromotePaperSessionRequest(BaseModel):
    bypass_criteria: bool = False


@router.post("/accounts", response_model=PaperAccount, status_code=status.HTTP_201_CREATED)
async def create_paper_account_endpoint(
    req: CreatePaperAccountRequest,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> PaperAccount:
    """Create a new virtual paper trading account."""
    return await service.create_account(
        name=req.name,
        initial_balance=req.initial_balance,
        actor_id=current_user.user_id,
    )


@router.get("/accounts", response_model=list[PaperAccount])
async def list_paper_accounts_endpoint(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> list[PaperAccount]:
    """List all registered virtual paper accounts."""
    return await service.list_accounts()


@router.post("/sessions", response_model=PaperTradingSession, status_code=status.HTTP_201_CREATED)
async def start_paper_session_endpoint(
    req: StartPaperSessionRequest,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> PaperTradingSession:
    """Launch a live paper trading session for a strategy."""
    return await service.start_session(
        strategy_id=req.strategy_id,
        account_id=req.account_id,
        symbols=req.symbols,
        config=req.config,
        actor_id=current_user.user_id,
    )


@router.get("/sessions", response_model=list[PaperTradingSession])
async def list_paper_sessions_endpoint(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> list[PaperTradingSession]:
    """List all active and historical paper trading sessions."""
    return await service.list_sessions()


@router.get("/sessions/{session_id}", response_model=PaperTradingSession)
async def get_paper_session_endpoint(
    session_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> PaperTradingSession:
    """Retrieve details for a paper trading session."""
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper session '{session_id}' not found")
    return session


@router.post("/sessions/{session_id}/pause", response_model=PaperTradingSession)
async def pause_paper_session_endpoint(
    session_id: str,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> PaperTradingSession:
    """Pause a running paper trading session."""
    session = await service.pause_session(session_id, actor_id=current_user.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper session '{session_id}' not found")
    return session


@router.post("/sessions/{session_id}/stop", response_model=PaperTradingSession)
async def stop_paper_session_endpoint(
    session_id: str,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> PaperTradingSession:
    """Stop a running paper trading session."""
    session = await service.stop_session(session_id, actor_id=current_user.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper session '{session_id}' not found")
    return session


@router.get("/sessions/{session_id}/gate-status", response_model=PaperTradingGateStatus)
async def get_paper_gate_status_endpoint(
    session_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> PaperTradingGateStatus:
    """Evaluate Stage 5 criteria for advancing to Stage 6 (HUMAN_APPROVAL)."""
    status_report = await service.evaluate_gate_status(session_id)
    if not status_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper session '{session_id}' not found")
    return status_report


@router.post("/sessions/{session_id}/promote")
async def promote_paper_session_endpoint(
    session_id: str,
    req: PromotePaperSessionRequest = PromotePaperSessionRequest(),
    current_user: User = Depends(require_permissions(Permission.STRATEGY_APPROVE)),
    service: PaperTradingService = Depends(lambda: paper_trading_service),
) -> dict[str, Any]:
    """Promote strategy to Stage 6 (HUMAN_APPROVAL) upon satisfying paper trading criteria."""
    success = await service.promote_to_human_approval(
        session_id=session_id,
        actor_id=current_user.user_id,
        bypass_criteria=req.bypass_criteria,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy promotion to HUMAN_APPROVAL failed. Minimum 14 days active, 30 trades, and max drawdown <= 10.0% required.",
        )
    return {
        "status": "promoted",
        "session_id": session_id,
        "target_stage": "HUMAN_APPROVAL",
    }
