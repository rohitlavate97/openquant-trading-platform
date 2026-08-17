"""REST Endpoints for Quantitative Strategy Management, Compilation, and Engine Lifecycle."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.strategy import (
    Strategy,
    StrategyParameter,
    StrategyState,
)
from openquant.application.services.strategy_service import StrategyService, strategy_service
from openquant.adapters.strategy.strategy_engine import strategy_engine
from openquant.interfaces.api.dependencies import require_permissions, get_current_user

router = APIRouter(prefix="/strategies", tags=["Strategies & Execution Engine"])


class CreateStrategyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    source_code: str = Field(..., min_length=10)
    description: str = ""
    parameters: list[StrategyParameter] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=lambda: ["AAPL"])
    account_id: str = "acc_main"
    broker_id: str = "paper_broker"


class UpdateStrategyRequest(BaseModel):
    name: str | None = None
    source_code: str | None = None
    description: str | None = None
    parameters: list[StrategyParameter] | None = None
    symbols: list[str] | None = None


@router.post("", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def create_strategy_endpoint(
    req: CreateStrategyRequest,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> Strategy:
    """Create and validate a new Python strategy against AST security checks."""
    try:
        strat = await service.create_strategy(
            name=req.name,
            source_code=req.source_code,
            description=req.description,
            author_id=current_user.user_id,
            parameters=req.parameters,
            symbols=req.symbols,
            account_id=req.account_id,
            broker_id=req.broker_id,
        )
        return strat
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[Strategy])
async def list_strategies_endpoint(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> list[Strategy]:
    """List all registered quantitative strategies."""
    return await service.list_strategies()


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy_endpoint(
    strategy_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> Strategy:
    """Get strategy details by strategy ID."""
    strat = await service.get_strategy(strategy_id)
    if not strat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy '{strategy_id}' not found")
    return strat


@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy_endpoint(
    strategy_id: str,
    req: UpdateStrategyRequest,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> Strategy:
    """Update strategy source code, configuration, or parameters."""
    try:
        strat = await service.update_strategy(
            strategy_id=strategy_id,
            name=req.name,
            description=req.description,
            source_code=req.source_code,
            parameters=req.parameters,
            symbols=req.symbols,
        )
        if not strat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy '{strategy_id}' not found")
        return strat
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{strategy_id}/start")
async def start_strategy_endpoint(
    strategy_id: str,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> dict[str, Any]:
    """Start strategy execution in the runtime engine."""
    success = await service.start_strategy(strategy_id, actor_id=current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start strategy '{strategy_id}'. Verify strategy exists and AST is valid.",
        )
    return {"status": "started", "strategy_id": strategy_id, "state": StrategyState.RUNNING}


@router.post("/{strategy_id}/stop")
async def stop_strategy_endpoint(
    strategy_id: str,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> dict[str, Any]:
    """Stop strategy execution gracefully."""
    success = await service.stop_strategy(strategy_id, actor_id=current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found or cannot be stopped.",
        )
    return {"status": "stopped", "strategy_id": strategy_id, "state": StrategyState.STOPPED}


@router.post("/{strategy_id}/pause")
async def pause_strategy_endpoint(
    strategy_id: str,
    current_user: User = Depends(require_permissions(Permission.STRATEGY_CREATE)),
    service: StrategyService = Depends(lambda: strategy_service),
) -> dict[str, Any]:
    """Pause strategy execution."""
    success = await service.pause_strategy(strategy_id, actor_id=current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found.",
        )
    return {"status": "paused", "strategy_id": strategy_id, "state": StrategyState.PAUSED}


@router.get("/{strategy_id}/logs")
async def get_strategy_logs_endpoint(
    strategy_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
) -> dict[str, Any]:
    """Retrieve runtime log messages from active strategy context."""
    logs = await strategy_engine.get_strategy_runtime_logs(strategy_id)
    return {"strategy_id": strategy_id, "logs": logs}
