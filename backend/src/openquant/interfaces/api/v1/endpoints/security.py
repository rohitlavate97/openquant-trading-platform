"""Security Hardening, Penetration Testing Diagnostics, and Security Audit API Endpoints."""

from typing import Any
from fastapi import APIRouter, Depends
from openquant.domain.models.auth import Permission, User
from openquant.application.services.security_audit_service import (
    SecurityAuditService,
    security_audit_service,
)
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/security", tags=["Security & Penetration Audit"])


@router.get(
    "/audit-report",
    summary="Retrieve automated security hardening audit report",
)
async def get_security_audit_report(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: SecurityAuditService = Depends(lambda: security_audit_service),
) -> dict[str, Any]:
    """Retrieve on-demand automated penetration test report and hardening status."""
    report = await service.run_penetration_diagnostics()
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at.isoformat(),
        "overall_status": report.overall_status,
        "total_checks": report.total_checks,
        "passed_checks": report.passed_checks,
        "failed_checks": report.failed_checks,
        "security_score_percent": report.security_score_percent,
        "total_duration_ms": report.total_duration_ms,
        "checks": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "category": c.category,
                "status": c.status,
                "latency_ms": c.latency_ms,
                "details": c.details,
            }
            for c in report.checks
        ],
    }


@router.post(
    "/run-penetration-test",
    summary="Trigger live penetration and security stress diagnostics",
)
async def run_live_penetration_test(
    current_user: User = Depends(require_permissions(Permission.SYSTEM_ADMIN)),
    service: SecurityAuditService = Depends(lambda: security_audit_service),
) -> dict[str, Any]:
    """Execute live adversarial penetration tests across AST sandbox, secrets, idempotency locks, and webhooks."""
    report = await service.run_penetration_diagnostics()
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at.isoformat(),
        "overall_status": report.overall_status,
        "total_checks": report.total_checks,
        "passed_checks": report.passed_checks,
        "failed_checks": report.failed_checks,
        "security_score_percent": report.security_score_percent,
        "total_duration_ms": report.total_duration_ms,
        "checks": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "category": c.category,
                "status": c.status,
                "latency_ms": c.latency_ms,
                "details": c.details,
            }
            for c in report.checks
        ],
    }
