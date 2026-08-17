"""Observability, Prometheus metrics, and distributed tracing API Endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, Query, Response
from openquant.domain.models.auth import Permission, User
from openquant.application.services.observability_service import ObservabilityService, observability_service
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(tags=["Observability & Metrics"])


@router.get(
    "/metrics",
    summary="Scrape OpenQuant Prometheus metrics",
    response_class=Response,
)
def scrape_prometheus_metrics(
    service: ObservabilityService = Depends(lambda: observability_service),
) -> Response:
    """Standard Prometheus scraping endpoint exposing OMS, Risk Engine, Market Data, and System metrics."""
    metrics_text = service.get_raw_prometheus_metrics()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get(
    "/api/v1/observability/summary",
    summary="Retrieve high-level system telemetry summary",
)
async def get_observability_summary(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ObservabilityService = Depends(lambda: observability_service),
) -> dict[str, Any]:
    """Retrieve operational telemetry counts and metrics summary."""
    return service.get_metrics_summary()


@router.get(
    "/api/v1/observability/traces",
    summary="Inspect recent distributed trace spans",
)
async def get_recent_traces(
    limit: int = Query(default=50, ge=1, le=500),
    trace_id: str | None = None,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ObservabilityService = Depends(lambda: observability_service),
) -> list[dict[str, Any]]:
    """Retrieve in-memory OpenTelemetry-compatible trace spans and latency breakdowns."""
    return service.get_recent_traces(limit=limit, trace_id=trace_id)


@router.get(
    "/api/v1/observability/dashboards",
    summary="List available Grafana dashboard definitions",
)
async def get_grafana_dashboards(
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: ObservabilityService = Depends(lambda: observability_service),
) -> list[dict[str, Any]]:
    """Retrieve pre-built Grafana JSON dashboard definitions for trading, risk, and feeds."""
    return service.get_grafana_dashboards()
