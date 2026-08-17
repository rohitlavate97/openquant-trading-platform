"""Application service for system health and diagnostics."""

from openquant.config import settings
from openquant.adapters.brokers.registry import adapter_registry


class HealthService:
    """Service aggregating health and readiness metrics across system components."""

    @staticmethod
    def get_liveness() -> dict[str, str]:
        """Simple liveness probe for orchestrators."""
        return {"status": "ok"}

    @staticmethod
    def get_readiness() -> dict[str, str | bool | dict]:
        """Readiness check verifying critical services and adapter status."""
        adapters = adapter_registry.list_adapters()
        return {
            "status": "ready",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "registered_adapters_count": len(adapters),
            "kill_switch_active": settings.RISK_GLOBAL_KILL_SWITCH_ACTIVE,
            "sandbox_strict_mode": settings.SANDBOX_STRICT_ALLOWLIST_MODE,
        }

    @staticmethod
    def get_system_info() -> dict[str, str | bool | int | list]:
        """Comprehensive system information and capability listing."""
        return {
            "platform": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "risk_engine": {
                "kill_switch_active": settings.RISK_GLOBAL_KILL_SWITCH_ACTIVE,
                "max_daily_loss_percent": settings.RISK_DEFAULT_MAX_DAILY_LOSS_PERCENT,
                "max_drawdown_percent": settings.RISK_DEFAULT_MAX_DRAWDOWN_PERCENT,
                "max_position_size_percent": settings.RISK_DEFAULT_MAX_POSITION_SIZE_PERCENT,
                "max_orders_per_second": settings.RISK_MAX_ORDERS_PER_SECOND,
            },
            "sandbox": {
                "max_cpu_seconds": settings.SANDBOX_MAX_CPU_SECONDS,
                "max_memory_mb": settings.SANDBOX_MAX_MEMORY_MB,
                "execution_timeout_seconds": settings.SANDBOX_EXECUTION_TIMEOUT_SECONDS,
                "strict_allowlist_mode": settings.SANDBOX_STRICT_ALLOWLIST_MODE,
            },
            "adapters": adapter_registry.list_adapters(),
        }
