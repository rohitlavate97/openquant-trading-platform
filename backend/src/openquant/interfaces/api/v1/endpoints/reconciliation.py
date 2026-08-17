"""REST Endpoints for State Reconciliation Engine & Mismatch Guard (Rule 5)."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.reconciliation import (
    ReconciliationReport,
)
from openquant.application.services.reconciliation_service import (
    ReconciliationService,
    reconciliation_service,
)
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/reconciliation", tags=["State Reconciliation & Mismatch Guard (Rule 5)"])


@router.post("/run", response_model=list[ReconciliationReport], status_code=status.HTTP_200_OK)
async def run_global_reconciliation_endpoint(
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: ReconciliationService = Depends(lambda: reconciliation_service),
) -> list[ReconciliationReport]:
    """Execute full state reconciliation across all trading accounts."""
    return await service.reconcile_all_accounts(actor_id=current_user.user_id)


@router.post("/accounts/{account_id}/run", response_model=ReconciliationReport, status_code=status.HTTP_200_OK)
async def run_account_reconciliation_endpoint(
    account_id: str,
    broker_id: str = "paper_broker",
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: ReconciliationService = Depends(lambda: reconciliation_service),
) -> ReconciliationReport:
    """Run state reconciliation for a specific account against broker actuals."""
    return await service.reconcile_account(
        account_id=account_id,
        broker_id=broker_id,
        actor_id=current_user.user_id,
    )


@router.get("/reports", response_model=list[ReconciliationReport])
async def list_reconciliation_reports_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ReconciliationService = Depends(lambda: reconciliation_service),
) -> list[ReconciliationReport]:
    """List recent state reconciliation reports."""
    return await service.get_latest_reports(limit=limit)


@router.get("/reports/{report_id}", response_model=ReconciliationReport)
async def get_reconciliation_report_endpoint(
    report_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ReconciliationService = Depends(lambda: reconciliation_service),
) -> ReconciliationReport:
    """Retrieve detailed state reconciliation audit report."""
    report = await service.get_report(report_id=report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation report '{report_id}' not found")
    return report


@router.post("/accounts/{account_id}/sync", response_model=ReconciliationReport, status_code=status.HTTP_200_OK)
async def sync_positions_endpoint(
    account_id: str,
    broker_id: str = "paper_broker",
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: ReconciliationService = Depends(lambda: reconciliation_service),
) -> ReconciliationReport:
    """Force synchronize internal OMS positions with broker actuals."""
    return await service.sync_positions_from_broker(
        account_id=account_id,
        broker_id=broker_id,
        actor_id=current_user.user_id,
    )
