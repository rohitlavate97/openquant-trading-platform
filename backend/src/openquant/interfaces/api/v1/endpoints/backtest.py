"""REST Endpoints for Event-Driven Backtesting, Walk-Forward Validation, and Stage 2 Promotion."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.backtest import (
    BacktestConfig,
    BacktestResult,
    WalkForwardResult,
)
from openquant.application.services.backtest_service import BacktestService, backtest_service
from openquant.interfaces.api.dependencies import require_permissions, get_current_user

router = APIRouter(prefix="/backtest", tags=["Backtesting & Walk-Forward Validation"])


class WalkForwardRequest(BaseModel):
    config: BacktestConfig
    num_windows: int = Field(default=4, ge=2, le=10)
    train_ratio: float = Field(default=0.7, ge=0.5, le=0.9)


class PromoteBacktestRequest(BaseModel):
    strategy_id: str


@router.post("/run", response_model=BacktestResult, status_code=status.HTTP_200_OK)
async def run_backtest_endpoint(
    config: BacktestConfig,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: BacktestService = Depends(lambda: backtest_service),
) -> BacktestResult:
    """Execute historical event-driven backtesting simulation for a quantitative strategy."""
    try:
        return await service.run_backtest(config=config, actor_id=current_user.user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/walk-forward", response_model=WalkForwardResult, status_code=status.HTTP_200_OK)
async def run_walk_forward_endpoint(
    req: WalkForwardRequest,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: BacktestService = Depends(lambda: backtest_service),
) -> WalkForwardResult:
    """Perform multi-window Walk-Forward Out-of-Sample efficiency validation."""
    try:
        return await service.run_walk_forward_validation(
            config=req.config,
            num_windows=req.num_windows,
            train_ratio=req.train_ratio,
            actor_id=current_user.user_id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/results/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result_endpoint(
    backtest_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: BacktestService = Depends(lambda: backtest_service),
) -> BacktestResult:
    """Retrieve detailed backtesting report, metrics, and equity curve."""
    result = await service.get_backtest_result(backtest_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backtest '{backtest_id}' not found")
    return result


@router.post("/{backtest_id}/promote")
async def promote_backtest_endpoint(
    backtest_id: str,
    req: PromoteBacktestRequest,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: BacktestService = Depends(lambda: backtest_service),
) -> dict[str, Any]:
    """Promote strategy to Stage 2 (BACKTESTED) after verifying minimum performance criteria."""
    success = await service.promote_strategy_to_backtested(
        strategy_id=req.strategy_id,
        backtest_id=backtest_id,
        actor_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy promotion to BACKTESTED failed. Criteria: Positive Net Profit and Max Drawdown <= 30%.",
        )
    return {
        "status": "promoted",
        "strategy_id": req.strategy_id,
        "target_stage": "BACKTEST",
        "backtest_id": backtest_id,
    }
