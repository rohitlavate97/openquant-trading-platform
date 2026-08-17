"""REST API Endpoints for Portfolio Management, Position Tracking, Asset Allocation, and Performance Analytics."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.portfolio import (
    AssetAllocationItem,
    PortfolioPerformanceSnapshot,
    PortfolioPosition,
    PortfolioSummary,
)
from openquant.application.services.portfolio_service import (
    PortfolioService,
    portfolio_service,
)
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/portfolio", tags=["Portfolio Management & Analytics"])


class ClosePositionResponse(BaseModel):
    symbol: str
    order_id: str
    message: str


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary_endpoint(
    account_id: str = Query(default="acc_main", description="Account identifier"),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PortfolioService = Depends(lambda: portfolio_service),
) -> PortfolioSummary:
    """Fetch aggregate portfolio NAV, cash balance, margin utilization, and drawdown statistics."""
    return await service.get_summary(account_id)


@router.get("/positions", response_model=list[PortfolioPosition])
async def list_portfolio_positions_endpoint(
    account_id: str = Query(default="acc_main", description="Account identifier"),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PortfolioService = Depends(lambda: portfolio_service),
) -> list[PortfolioPosition]:
    """Fetch active mark-to-market valued positions with weights and unrealized PnL."""
    return await service.list_positions(account_id)


@router.get("/allocation", response_model=list[AssetAllocationItem])
async def get_portfolio_allocation_endpoint(
    account_id: str = Query(default="acc_main", description="Account identifier"),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PortfolioService = Depends(lambda: portfolio_service),
) -> list[AssetAllocationItem]:
    """Fetch portfolio asset allocation breakdown."""
    return await service.get_allocation(account_id)


@router.get("/performance", response_model=list[PortfolioPerformanceSnapshot])
async def get_portfolio_performance_endpoint(
    account_id: str = Query(default="acc_main", description="Account identifier"),
    days: int = Query(default=30, ge=1, le=365, description="Number of historical days"),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: PortfolioService = Depends(lambda: portfolio_service),
) -> list[PortfolioPerformanceSnapshot]:
    """Fetch historical equity curve snapshots and drawdown series."""
    return await service.get_performance(account_id, days)


@router.post("/positions/{symbol}/close", response_model=ClosePositionResponse)
async def close_portfolio_position_endpoint(
    symbol: str,
    account_id: str = Query(default="acc_main", description="Account identifier"),
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: PortfolioService = Depends(lambda: portfolio_service),
) -> ClosePositionResponse:
    """Flatten an active position by submitting an opposing market order through the OMS."""
    try:
        order_id = await service.close_position(
            account_id=account_id,
            symbol=symbol,
            actor_id=current_user.user_id,
        )
        return ClosePositionResponse(
            symbol=symbol,
            order_id=order_id,
            message=f"Position for {symbol} closed successfully via OMS.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
