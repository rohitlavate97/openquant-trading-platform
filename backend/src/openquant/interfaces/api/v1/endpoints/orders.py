"""Order Management System & Position Reconciliation Endpoints."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from openquant.domain.models.auth import Permission, User
from openquant.domain.models.order import Order, OrderRequest
from openquant.domain.models.position import Position
from openquant.interfaces.api.dependencies import require_permissions
from openquant.application.services.order_service import (
    order_service,
    PositionReconciliationReport,
)

router = APIRouter(tags=["Order Management System (OMS)"])


@router.post("/orders", status_code=status.HTTP_201_CREATED, summary="Submit New Order")
async def place_order(
    request: OrderRequest,
    current_user: Annotated[User, Depends(require_permissions(Permission.ORDER_MANAGE))],
    idempotency_key_header: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    """Submit a new trading order with strict idempotency and pre-trade validations."""
    # Use header if supplied to override request payload idempotency key
    if idempotency_key_header:
        request.idempotency_key = idempotency_key_header

    order = await order_service.submit_order(request, actor_id=current_user.user_id)
    return {
        "status": "success",
        "order": order.model_dump(),
        "is_idempotent_replay": order.status != "PENDING_SUBMISSION",
    }


@router.get("/orders", summary="List Orders")
async def list_orders(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    account_id: str | None = Query(default=None, description="Filter by account ID"),
) -> list[dict[str, Any]]:
    """List historical and active orders."""
    orders = await order_service.list_orders(account_id)
    return [o.model_dump() for o in orders]


@router.get("/orders/{order_id}", summary="Get Order Details")
async def get_order(
    order_id: str,
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> dict[str, Any]:
    """Retrieve details and execution state for a specific order."""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )
    return order.model_dump()


@router.delete("/orders/{order_id}", summary="Cancel Order")
async def cancel_order(
    order_id: str,
    current_user: Annotated[User, Depends(require_permissions(Permission.ORDER_MANAGE))],
) -> dict[str, Any]:
    """Cancel an active order with the broker."""
    order = await order_service.cancel_order(order_id, actor_id=current_user.user_id)
    return {"status": "success", "order": order.model_dump()}


@router.get("/positions", summary="List Active Positions & PnL")
async def list_positions(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    account_id: str = Query(default="acc_main", description="Trading account ID"),
) -> list[dict[str, Any]]:
    """List real-time positions with realized and unrealized PnL."""
    positions = await order_service.list_positions(account_id)
    return [p.model_dump() for p in positions]


@router.post("/positions/reconcile", summary="Reconcile Positions Against Broker")
async def reconcile_positions(
    current_user: Annotated[User, Depends(require_permissions(Permission.ORDER_MANAGE))],
    account_id: str = Query(default="acc_main", description="Trading account ID"),
    broker_id: str = Query(default="paper_broker", description="Broker adapter identifier"),
) -> dict[str, Any]:
    """Execute continuous position reconciliation against broker actual positions."""
    report = await order_service.reconcile_positions(
        account_id=account_id,
        broker_id=broker_id,
        actor_id=current_user.user_id,
    )
    return report.model_dump()
