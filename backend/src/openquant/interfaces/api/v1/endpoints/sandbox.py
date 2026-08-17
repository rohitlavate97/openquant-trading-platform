"""Strategy Execution Sandbox and AST Security Validation Endpoints."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from openquant.domain.models.auth import Permission, User
from openquant.interfaces.api.dependencies import require_permissions
from openquant.application.services.sandbox_service import sandbox_service

router = APIRouter(prefix="/sandbox", tags=["Strategy Execution Sandbox"])


class ValidateCodeRequest(BaseModel):
    """Payload for static AST analysis."""
    source_code: str = Field(..., min_length=1, description="Raw Python strategy code")


class ExecuteStrategyRequest(BaseModel):
    """Payload for sandboxed strategy execution."""
    source_code: str = Field(..., min_length=1, description="Raw Python strategy code")
    strategy_id: str | None = Field(default=None, description="Strategy identifier")
    context: dict[str, Any] = Field(default_factory=dict, description="Input variables / market prices")
    timeout_seconds: int = Field(default=10, ge=1, le=60, description="Execution timeout limit")


@router.post("/validate", summary="Static AST Security Analysis")
async def validate_strategy_code(
    request: ValidateCodeRequest,
    current_user: Annotated[User, Depends(require_permissions(Permission.STRATEGY_CREATE))],
) -> dict[str, Any]:
    """Perform static AST security analysis checking for forbidden operations and imports."""
    result = sandbox_service.validate_code(request.source_code)
    return result.model_dump()


@router.post("/execute", summary="Execute Strategy in Isolated Sandbox")
async def execute_strategy_sandbox(
    request: ExecuteStrategyRequest,
    current_user: Annotated[User, Depends(require_permissions(Permission.STRATEGY_CREATE))],
) -> dict[str, Any]:
    """Execute user-provided or AI-generated Python strategy in an isolated sandbox with resource quotas."""
    result = await sandbox_service.execute_strategy(
        source_code=request.source_code,
        context=request.context,
        strategy_id=request.strategy_id,
        timeout_seconds=request.timeout_seconds,
        actor_id=current_user.email,
    )
    return result.model_dump()


@router.get("/templates", summary="Get Strategy Starter Templates")
async def get_strategy_templates(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> dict[str, Any]:
    """Retrieve pre-built validated starter strategy templates."""
    return sandbox_service.get_templates()
