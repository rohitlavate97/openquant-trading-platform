"""Live Trading Mode REST API Endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.live_trading import (
    LiveCapitalAllocation,
    LivePreflightReport,
    LiveStrategySession,
    ScalingTier,
)
from openquant.domain.ports.live_trading_port import ILiveTradingService
from openquant.application.services.live_trading_service import LiveTradingService
from openquant.application.services.strategy_service import strategy_service
from openquant.adapters.brokers.registry import broker_registry
from openquant.application.services.risk_service import risk_service
from openquant.application.services.market_data_service import market_data_service
from openquant.adapters.repositories.in_memory_live_session_repo import InMemoryLiveSessionRepository
from openquant.adapters.event_bus.in_memory_event_bus import event_bus
from openquant.application.services.audit_service import audit_log_service
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/live-trading", tags=["Live Trading"])

_live_session_repo = InMemoryLiveSessionRepository()
live_trading_service = LiveTradingService(
    strategy_service=strategy_service,
    broker_registry=broker_registry,
    risk_service=risk_service,
    market_data_service=market_data_service,
    live_repo=_live_session_repo,
    event_bus=event_bus,
    audit_service=audit_log_service,
)


class PreflightCheckRequest(BaseModel):
    strategy_id: str
    broker_id: str
    account_id: str


class ActivateSessionRequest(BaseModel):
    strategy_id: str
    broker_id: str
    account_id: str
    allocation: LiveCapitalAllocation
    confirmed_by: str | None = None


class AdjustScalingRequest(BaseModel):
    scaling_tier: ScalingTier


class HaltSessionRequest(BaseModel):
    reason: str = "Operator manual halt"


@router.post(
    "/preflight",
    response_model=LivePreflightReport,
    summary="Run live trading readiness preflight check",
)
async def run_preflight(
    req: PreflightCheckRequest,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ILiveTradingService = Depends(lambda: live_trading_service),
) -> LivePreflightReport:
    """Run all 5 mandatory Non-Negotiable preflight verification checks."""
    return await service.run_preflight_check(
        strategy_id=req.strategy_id,
        broker_id=req.broker_id,
        account_id=req.account_id,
    )


@router.post(
    "/sessions",
    response_model=LiveStrategySession,
    status_code=status.HTTP_201_CREATED,
    summary="Activate live strategy execution session",
)
async def activate_session(
    req: ActivateSessionRequest,
    current_user: User = Depends(require_permissions(Permission.LIVE_TRADING_ENABLE)),
    service: ILiveTradingService = Depends(lambda: live_trading_service),
) -> LiveStrategySession:
    """Activate live execution session after verifying preflight readiness and dual confirmation."""
    try:
        return await service.activate_live_session(
            strategy_id=req.strategy_id,
            broker_id=req.broker_id,
            account_id=req.account_id,
            allocation=req.allocation,
            activated_by=current_user.user_id,
            confirmed_by=req.confirmed_by or current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/sessions",
    response_model=list[LiveStrategySession],
    summary="List live strategy execution sessions",
)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    strategy_id: str | None = None,
    is_active_only: bool = False,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ILiveTradingService = Depends(lambda: live_trading_service),
) -> list[LiveStrategySession]:
    """Retrieve history of live sessions and current active deployments."""
    return await service.list_sessions(
        limit=limit,
        offset=offset,
        strategy_id=strategy_id,
        is_active_only=is_active_only,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=LiveStrategySession,
    summary="Get live session details",
)
async def get_session(
    session_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ILiveTradingService = Depends(lambda: live_trading_service),
) -> LiveStrategySession:
    """Query live trading session telemetry and preflight checklist."""
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Live session '{session_id}' not found.")
    return session


@router.post(
    "/sessions/{session_id}/scale",
    response_model=LiveStrategySession,
    summary="Adjust live capital scaling tier",
)
async def adjust_scaling(
    session_id: str,
    req: AdjustScalingRequest,
    current_user: User = Depends(require_permissions(Permission.LIVE_TRADING_ENABLE)),
    service: ILiveTradingService = Depends(lambda: live_trading_service),
) -> LiveStrategySession:
    """Adjust live position sizing and capital scaling tier."""
    try:
        return await service.adjust_scaling_tier(
            session_id=session_id,
            new_tier=req.scaling_tier,
            actor_id=current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/{session_id}/halt",
    response_model=LiveStrategySession,
    summary="Emergency halt live strategy session",
)
async def halt_session(
    session_id: str,
    req: HaltSessionRequest,
    current_user: User = Depends(require_permissions(Permission.KILL_SWITCH_TRIGGER)),
    service: ILiveTradingService = Depends(lambda: live_trading_service),
) -> LiveStrategySession:
    """Emergency halt or stop live strategy session."""
    try:
        return await service.halt_live_session(
            session_id=session_id,
            reason=req.reason,
            actor_id=current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
