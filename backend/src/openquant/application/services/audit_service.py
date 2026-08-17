"""Application service for Enterprise Audit Logging and Compliance Tracking."""

from typing import Any
from openquant.domain.ports.repositories import IAuditLogRepository
from openquant.adapters.repositories.in_memory_auth_repo import audit_log_repository as default_audit_repo


class AuditLogService:
    """Service capturing immutable structured audit trails for risk and compliance."""

    def __init__(self, audit_repo: IAuditLogRepository = default_audit_repo) -> None:
        self._audit_repo = audit_repo

    async def log_event(
        self,
        event_type: str,
        actor_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict[str, Any],
        severity: str = "INFO",
        client_ip: str | None = None,
        status: str = "SUCCESS",
        reason: str | None = None,
    ) -> str:
        """Record an immutable compliance event to the audit log."""
        return await self._audit_repo.record_event(
            event_type=event_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            payload=payload,
            severity=severity,
            client_ip=client_ip,
            status=status,
            reason=reason,
        )

    async def list_audit_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: str | None = None,
        actor_id: str | None = None,
        severity: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query historical audit logs with filtering."""
        return await self._audit_repo.list_logs(
            limit=limit,
            offset=offset,
            event_type=event_type,
            actor_id=actor_id,
            severity=severity,
        )


# Global singleton instance
audit_log_service = AuditLogService()
