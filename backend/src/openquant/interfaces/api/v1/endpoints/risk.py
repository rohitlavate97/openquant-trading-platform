"""Risk Engine, Pre-Trade Checks & Global Kill Switch Endpoints."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from openquant.domain.models.auth import Permission, User
from openquant.domain.models.risk import (
    RiskLimitsConfig,
    KillSwitchLevel,
    KillSwitchState,
    RiskEvaluationResult,
)
from openquant.domain.models.order import OrderRequest
from openquant.interfaces.api.dependencies import require_permissions
from openquant.application.services.risk_service import risk_service

router = APIRouter(prefix="/risk", tags=["Risk Engine & Emergency Controls"])


class KillSwitchTriggerRequest(BaseModel):
    """Payload for triggering emergency Kill Switch."""
    level: KillSwitchLevel = Field(default=KillSwitchLevel.GLOBAL, description="Scope of the trading halt")
    target_id: str | None = Field(default=None, description="Specific account/strategy/symbol ID if not global")
    reason: str = Field(default="Manual Emergency Intervention", description="Operational rationale")
    flatten_positions: bool = Field(default=False, description="Optionally market close all active positions")


@router.get("/config", summary="Get Current Risk Limits & Kill Switch Status")
async def get_risk_configuration(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> dict[str, Any]:
    """Retrieve active pre-trade risk rules and kill switch status."""
    return risk_service.get_config().model_dump()


@router.put("/config", summary="Update Pre-Trade Risk Limits")
async def update_risk_configuration(
    config: RiskLimitsConfig,
    current_user: Annotated[User, Depends(require_permissions(Permission.SYSTEM_ADMIN))],
) -> dict[str, Any]:
    """Update risk limits parameters (Super Admin / Admin only)."""
    updated = risk_service.update_config(config)
    return {"status": "success", "config": updated.model_dump()}


@router.post("/kill-switch/activate", summary="Activate Emergency Kill Switch")
async def activate_kill_switch(
    payload: KillSwitchTriggerRequest,
    current_user: Annotated[User, Depends(require_permissions(Permission.KILL_SWITCH_TRIGGER))],
) -> dict[str, Any]:
    """1-Click Emergency Kill Switch: immediately halts order routing and cancels open orders."""
    state = await risk_service.activate_kill_switch(
        level=payload.level,
        target_id=payload.target_id,
        activated_by=current_user.email,
        reason=payload.reason,
        flatten_positions=payload.flatten_positions,
    )
    return {
        "status": "success",
        "message": f"Kill Switch ACTIVATED at {payload.level.value} level.",
        "kill_switch": state.model_dump(),
    }


@router.post("/kill-switch/deactivate", summary="Deactivate Emergency Kill Switch")
async def deactivate_kill_switch(
    current_user: Annotated[User, Depends(require_permissions(Permission.KILL_SWITCH_TRIGGER))],
) -> dict[str, Any]:
    """Resume platform trading by resetting the Kill Switch."""
    state = await risk_service.deactivate_kill_switch(actor_id=current_user.email)
    return {
        "status": "success",
        "message": "Kill Switch deactivated. Trading resumed.",
        "kill_switch": state.model_dump(),
    }


@router.post("/evaluate-pre-trade", summary="Dry-Run Pre-Trade Risk Checks")
async def dry_run_pre_trade_risk(
    request: OrderRequest,
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> dict[str, Any]:
    """Dry-run test of all 8 pre-trade hard stops without executing order."""
    from openquant.domain.exceptions import RiskLimitBreachedError, KillSwitchActiveError
    try:
        result = await risk_service.evaluate_pre_trade(request)
        return {
            "allowed": True,
            "rejection_reasons": [],
            "checks": [c.model_dump() for c in result.checks],
        }
    except (RiskLimitBreachedError, KillSwitchActiveError) as e:
        return {
            "allowed": False,
            "rejection_reasons": [str(e)],
            "checks": [],
        }
