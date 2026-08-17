"""Central API v1 router mounting all sub-resources."""

from fastapi import APIRouter
from openquant.interfaces.api.v1.endpoints.health import router as health_router
from openquant.interfaces.api.v1.endpoints.system import router as system_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(system_router)
