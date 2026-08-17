"""Audit Logs and Compliance Inspection API endpoints."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query
from openquant.domain.models.auth import Permission, User
from openquant.application.services.audit_service import audit_log_service
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs & Compliance"])


@router.get("", summary="List Audit Logs")
async def list_audit_logs(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Fetch immutable audit trail entries with filtering."""
    return await audit_log_service.list_audit_logs(
        limit=limit,
        offset=offset,
        event_type=event_type,
        actor_id=actor_id,
        severity=severity,
    )
