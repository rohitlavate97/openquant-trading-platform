"""REST Endpoints for Additional Strategy Sources (TradingView Webhooks, MT5 Bridge, Google Sheets)."""

from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.strategy_sources import (
    MT5BridgeCommand,
    MT5BridgeStatus,
    SheetsParseResult,
    TradingViewWebhookPayload,
    TradingViewWebhookResult,
)
from openquant.application.services.strategy_sources_service import (
    StrategySourcesService,
    strategy_sources_service,
)
from openquant.interfaces.api.dependencies import require_permissions, get_current_user

router = APIRouter(prefix="/sources", tags=["Additional Strategy Sources (TradingView, MT5, Sheets)"])


class ParseSheetsRequest(BaseModel):
    csv_content: str = Field(..., description="Raw CSV or tab-separated string with trade signals")


class ExecuteSheetsBatchRequest(BaseModel):
    account_id: str = "acc_main"
    orders: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/tradingview/webhook", response_model=TradingViewWebhookResult, status_code=status.HTTP_200_OK)
async def handle_tradingview_webhook_endpoint(
    payload: TradingViewWebhookPayload,
    x_tradingview_signature: str | None = Header(default=None, alias="X-TradingView-Signature"),
    service: StrategySourcesService = Depends(lambda: strategy_sources_service),
) -> TradingViewWebhookResult:
    """Ingest TradingView alert with HMAC-SHA256 signature verification & replay protection."""
    # If signature was provided in header, populate payload signature
    if x_tradingview_signature and not payload.signature:
        payload.signature = x_tradingview_signature

    result = await service.handle_tradingview_webhook(payload)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )
    return result


@router.get("/mt5/status", response_model=MT5BridgeStatus)
async def get_mt5_bridge_status_endpoint(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: StrategySourcesService = Depends(lambda: strategy_sources_service),
) -> MT5BridgeStatus:
    """Retrieve telemetry health status of the MT5 socket bridge."""
    return await service.get_mt5_status()


@router.post("/mt5/command")
async def dispatch_mt5_command_endpoint(
    command: MT5BridgeCommand,
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: StrategySourcesService = Depends(lambda: strategy_sources_service),
) -> dict[str, Any]:
    """Dispatch an outbound trade command to MT5 EA."""
    return await service.dispatch_mt5_command(command, actor_id=current_user.user_id)


@router.post("/sheets/parse", response_model=SheetsParseResult)
async def parse_sheets_signals_endpoint(
    req: ParseSheetsRequest,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: StrategySourcesService = Depends(lambda: strategy_sources_service),
) -> SheetsParseResult:
    """Parse and validate raw CSV spreadsheet signals."""
    return service.parse_sheets_csv(req.csv_content)


@router.post("/sheets/execute")
async def execute_sheets_batch_endpoint(
    req: ExecuteSheetsBatchRequest,
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: StrategySourcesService = Depends(lambda: strategy_sources_service),
) -> dict[str, Any]:
    """Execute a batch of validated spreadsheet orders."""
    order_ids = await service.execute_sheets_orders(
        orders=req.orders,
        account_id=req.account_id,
        actor_id=current_user.user_id,
    )
    return {
        "status": "success",
        "executed_count": len(order_ids),
        "order_ids": order_ids,
    }
