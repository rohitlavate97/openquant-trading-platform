"""Broker Adapter endpoints for multi-broker routing, funds, and certification."""

from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query
from openquant.domain.models.auth import Permission, User
from openquant.domain.models.broker import (
    BrokerAccountInfo,
    BrokerAdapterMetadata,
    BrokerHolding,
    BrokerSecurityAuditReport,
)
from openquant.domain.models.position import Position
from openquant.application.services.broker_service import broker_service
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/brokers", tags=["Broker Adapters & Certification"])


@router.get("", summary="List Registered Broker Adapters")
async def list_brokers(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> list[BrokerAdapterMetadata]:
    """Retrieve metadata and certification status for all registered broker adapters."""
    return broker_service.list_adapters()


@router.get("/{adapter_id}/metadata", summary="Get Broker Adapter Metadata")
async def get_broker_metadata(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
) -> BrokerAdapterMetadata:
    """Retrieve capabilities, supported order types, and certification status for a specific adapter."""
    return broker_service.get_adapter_metadata(adapter_id)


@router.post("/{adapter_id}/connect", summary="Connect Broker Adapter")
async def connect_broker(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.BROKER_MANAGE))],
) -> dict[str, str | bool]:
    """Authenticate and establish session using user's encrypted vault credentials."""
    connected = await broker_service.connect_user_broker(adapter_id, current_user.user_id)
    return {"adapter_id": adapter_id, "connected": connected, "status": "AUTHENTICATED" if connected else "FAILED"}


@router.post("/{adapter_id}/disconnect", summary="Disconnect Broker Adapter")
async def disconnect_broker(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.BROKER_MANAGE))],
) -> dict[str, str]:
    """Gracefully terminate adapter session."""
    await broker_service.disconnect_broker(adapter_id, current_user.user_id)
    return {"adapter_id": adapter_id, "status": "DISCONNECTED"}


@router.get("/{adapter_id}/funds", summary="Get Broker Account Funds & Margin")
async def get_broker_funds(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    account_id: str = Query(default="acc_main", description="Broker trading account ID"),
) -> BrokerAccountInfo:
    """Fetch real-time funds, available cash, and utilized margin."""
    return await broker_service.get_funds(adapter_id, account_id)


@router.get("/{adapter_id}/positions", summary="Get Broker Positions")
async def get_broker_positions(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    account_id: str = Query(default="acc_main", description="Broker trading account ID"),
) -> list[Position]:
    """Fetch actual real-time positions directly from broker adapter."""
    return await broker_service.get_positions(adapter_id, account_id)


@router.get("/{adapter_id}/holdings", summary="Get Broker Portfolio Holdings")
async def get_broker_holdings(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    account_id: str = Query(default="acc_main", description="Broker trading account ID"),
) -> list[BrokerHolding]:
    """Fetch equity deliveries and long-term portfolio holdings."""
    return await broker_service.get_holdings(adapter_id, account_id)


@router.post("/{adapter_id}/certify", summary="Run Certification Audit Harness")
async def certify_broker_adapter(
    adapter_id: Annotated[str, Path(description="Broker adapter identifier")],
    current_user: Annotated[User, Depends(require_permissions(Permission.SYSTEM_ADMIN))],
) -> BrokerSecurityAuditReport:
    """Execute automated sandbox validation harness and issue live-trading certification."""
    return await broker_service.run_adapter_certification(
        adapter_id=adapter_id,
        certified_by=current_user.user_id,
    )
