"""FastAPI Application Factory with clean error handling, middleware, and lifecycle hooks."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from openquant.config import settings
from openquant.domain.exceptions import (
    CapitalSafetyViolationError,
    KillSwitchActiveError,
    RiskLimitBreachedError,
    SandboxSecurityViolationError,
    SandboxResourceExceededError,
    BrokerAdapterUncertifiedError,
    IdempotencyConflictError,
    PromotionGateViolationError,
    StaleMarketDataError,
    AuthenticationError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    SecretsDecryptionError,
    OpenQuantDomainError,
)
from openquant.interfaces.api.v1.router import api_v1_router

logger = logging.getLogger("openquant")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and graceful shutdown lifecycle manager."""
    logger.info("Initializing OpenQuant Trading Platform (Version: %s)...", settings.VERSION)
    logger.info("Operating Mode: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)
    yield
    logger.info("Shutting down OpenQuant Trading Platform gracefully...")


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Enterprise Open-Source Algorithmic Trading Platform Core API",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # Custom Domain Exception Handlers
    # --------------------------------------------------------------------------
    @app.exception_handler(KillSwitchActiveError)
    async def kill_switch_exception_handler(request: Request, exc: KillSwitchActiveError) -> JSONResponse:
        logger.error("Order blocked: Global Kill Switch is ACTIVE: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "KILL_SWITCH_ACTIVE",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RiskLimitBreachedError)
    async def risk_limit_exception_handler(request: Request, exc: RiskLimitBreachedError) -> JSONResponse:
        logger.warning("Order blocked: Risk limit breached: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "RISK_LIMIT_BREACHED",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(SandboxSecurityViolationError)
    async def sandbox_security_exception_handler(request: Request, exc: SandboxSecurityViolationError) -> JSONResponse:
        logger.error("Strategy code rejected by sandbox static analysis: %s", exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "SANDBOX_SECURITY_VIOLATION",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(IdempotencyConflictError)
    async def idempotency_exception_handler(request: Request, exc: IdempotencyConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "IDEMPOTENCY_CONFLICT",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(BrokerAdapterUncertifiedError)
    async def adapter_uncertified_exception_handler(request: Request, exc: BrokerAdapterUncertifiedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "BROKER_UNCERTIFIED",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "AUTHENTICATION_FAILED",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_exception_handler(request: Request, exc: PermissionDeniedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "PERMISSION_DENIED",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_exception_handler(request: Request, exc: UserAlreadyExistsError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "USER_ALREADY_EXISTS",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(SecretsDecryptionError)
    async def secrets_decryption_exception_handler(request: Request, exc: SecretsDecryptionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "SECRETS_DECRYPTION_FAILED",
                "message": "Failed to decrypt stored credentials.",
            },
        )

    @app.exception_handler(OpenQuantDomainError)
    async def generic_domain_exception_handler(request: Request, exc: OpenQuantDomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "DOMAIN_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Mount API v1 routes
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app
