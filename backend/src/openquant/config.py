"""Global application configuration management using Pydantic Settings."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration parameters with safe defaults for development."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Environment
    PROJECT_NAME: str = "OpenQuant Algorithmic Trading Platform"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "openquant_insecure_development_secret_key_must_change_in_production"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://openquant:openquant_dev_password@localhost:5432/openquant_db"

    # Redis Cache & Message Broker
    REDIS_URL: str = "redis://localhost:6379/0"

    # Sandbox Quotas & Safety Policies
    SANDBOX_MAX_CPU_SECONDS: int = Field(default=30, description="Max CPU time in seconds per strategy run")
    SANDBOX_MAX_MEMORY_MB: int = Field(default=512, description="Max RAM allocation in MB per strategy run")
    SANDBOX_EXECUTION_TIMEOUT_SECONDS: int = Field(default=60, description="Hard timeout per strategy execution")
    SANDBOX_STRICT_ALLOWLIST_MODE: bool = Field(default=True, description="Strict AST allowlist enforcement")

    # Risk Engine Hard-Stop Defaults
    RISK_GLOBAL_KILL_SWITCH_ACTIVE: bool = Field(default=False, description="Global emergency order block")
    RISK_DEFAULT_MAX_DAILY_LOSS_PERCENT: float = Field(default=3.0, description="Max daily drawdown before auto-halt")
    RISK_DEFAULT_MAX_DRAWDOWN_PERCENT: float = Field(default=5.0, description="Max peak-to-trough drawdown")
    RISK_DEFAULT_MAX_POSITION_SIZE_PERCENT: float = Field(default=10.0, description="Max single position allocation")
    RISK_MAX_ORDERS_PER_SECOND: int = Field(default=10, description="Rate limit on live order dispatches")

    # Market Data Freshness
    MARKET_DATA_STALENESS_THRESHOLD_MS: int = Field(default=3000, description="Max age in ms before price is stale")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated origin strings into a list for FastAPI CORS."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


# Singleton instance
settings = Settings()
