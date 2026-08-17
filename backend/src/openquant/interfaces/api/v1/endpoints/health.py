"""Health and liveness endpoints."""

from fastapi import APIRouter
from openquant.application.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="General Health Status")
async def get_health() -> dict:
    """Return platform readiness and health diagnostics."""
    return HealthService.get_readiness()


@router.get("/live", summary="Liveness Probe")
async def get_liveness() -> dict:
    """Return basic liveness status for container orchestrators."""
    return HealthService.get_liveness()


@router.get("/ready", summary="Readiness Probe")
async def get_readiness() -> dict:
    """Return full readiness state including adapter connectivity."""
    return HealthService.get_readiness()
