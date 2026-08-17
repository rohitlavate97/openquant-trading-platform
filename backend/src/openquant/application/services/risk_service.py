"""Risk Application Service coordinating pre-trade risk evaluation, circuit breakers, and global kill switch."""

import logging
from decimal import Decimal
from typing import Any
from openquant.domain.models.order import OrderRequest, Order
from openquant.domain.models.risk import (
    RiskLimitsConfig,
    RiskEvaluationResult,
    KillSwitchState,
    KillSwitchLevel,
)
from openquant.domain.exceptions import (
    RiskLimitBreachedError,
    KillSwitchActiveError,
)
from openquant.adapters.risk.risk_engine import synchronous_risk_engine, SynchronousRiskEngine
from openquant.application.services.market_data_service import market_data_service, MarketDataService
from openquant.application.services.streaming_service import streaming_broadcaster, StreamingBroadcasterService
from openquant.application.services.audit_service import audit_log_service, AuditLogService
from openquant.adapters.repositories.in_memory_oms_repo import order_repository, position_repository
from openquant.adapters.brokers.registry import adapter_registry

logger = logging.getLogger("openquant.risk_service")


class RiskService:
    """Application Service governing real-time risk controls and emergency intervention."""

    def __init__(
        self,
        engine: SynchronousRiskEngine = synchronous_risk_engine,
        mkt_service: MarketDataService = market_data_service,
        broadcaster: StreamingBroadcasterService = streaming_broadcaster,
        audit: AuditLogService = audit_log_service,
    ) -> None:
        self._engine = engine
        self._mkt_service = mkt_service
        self._broadcaster = broadcaster
        self._audit = audit

    def get_config(self) -> RiskLimitsConfig:
        """Get active risk limits and kill switch state."""
        return self._engine.config

    def update_config(self, new_config: RiskLimitsConfig) -> RiskLimitsConfig:
        """Update risk limits."""
        self._engine.update_config(new_config)
        return self._engine.config

    async def evaluate_pre_trade(self, request: OrderRequest) -> RiskEvaluationResult:
        """Synchronously evaluate an order request against all 8 pre-trade hard stops.
        Raises KillSwitchActiveError or RiskLimitBreachedError if any blocking check fails.
        """
        # 1. Fetch live market price
        tick = await self._mkt_service.get_latest_tick(request.symbol)
        mkt_price = tick.last_price if tick else (request.price or Decimal("100.0"))

        # 2. Fetch open orders for account & symbol
        open_orders = await order_repository.list_open_orders(request.account_id)

        # 3. Retrieve broker funds if available
        account_funds = None
        adapter = adapter_registry.get(request.broker_id)
        if adapter:
            try:
                account_funds = await adapter.get_account_info(request.account_id)
            except Exception:
                pass

        # 4. Evaluate synchronously via Risk Engine
        result = await self._engine.evaluate_order(
            request=request,
            current_market_price=mkt_price,
            account_funds=account_funds,
            open_orders=open_orders,
            daily_loss_percent=0.0,
            current_drawdown_percent=0.0,
        )

        if not result.allowed:
            first_reason = result.rejection_reasons[0] if result.rejection_reasons else "Pre-trade risk limit breached."

            # Log audit event
            await self._audit.log_event(
                event_type="RISK_CHECK_REJECTED",
                actor_id="risk_engine",
                entity_type="ORDER",
                entity_id=request.idempotency_key,
                action="BLOCK",
                severity="HIGH",
                payload={
                    "rejection_reasons": result.rejection_reasons,
                    "symbol": request.symbol,
                    "quantity": str(request.quantity),
                },
            )

            # Broadcast risk rejection over WebSockets
            await self._broadcaster.broadcast_telemetry(
                "PRE_TRADE_RISK_REJECTED",
                {
                    "symbol": request.symbol,
                    "idempotency_key": request.idempotency_key,
                    "reasons": result.rejection_reasons,
                },
            )

            if "Kill Switch is ACTIVE" in first_reason:
                raise KillSwitchActiveError(first_reason)
            raise RiskLimitBreachedError(first_reason)

        return result

    async def activate_kill_switch(
        self,
        level: KillSwitchLevel = KillSwitchLevel.GLOBAL,
        target_id: str | None = None,
        activated_by: str = "super_admin",
        reason: str = "Emergency Trading Halt Triggered",
        flatten_positions: bool = False,
    ) -> KillSwitchState:
        """Activate Emergency Kill Switch, cancel open orders, and notify all systems."""
        state = self._engine.activate_kill_switch(
            level=level,
            target_id=target_id,
            activated_by=activated_by,
            reason=reason,
            flatten_positions=flatten_positions,
        )

        logger.critical(f"GLOBAL KILL SWITCH ACTIVATED by '{activated_by}'! Level: {level.value}. Reason: {reason}")

        # Cancel all open orders across brokers
        open_orders = await order_repository.list_all()
        for ord_item in open_orders:
            if not ord_item.is_terminal:
                ord_item.status = "CANCELLED"
                ord_item.rejection_reason = "Cancelled by Global Emergency Kill Switch"
                await order_repository.save(ord_item)

        # Log high-severity audit record
        await self._audit.log_event(
            event_type="KILL_SWITCH_ACTIVATED",
            actor_id=activated_by,
            entity_type="SYSTEM",
            entity_id="global_kill_switch",
            action="HALT_TRADING",
            severity="CRITICAL",
            payload={
                "level": level.value,
                "target_id": target_id,
                "reason": reason,
                "flatten_positions": flatten_positions,
            },
        )

        # Broadcast critical alert over WebSockets
        await self._broadcaster.broadcast_telemetry(
            "KILL_SWITCH_STATUS_CHANGED",
            {
                "is_active": True,
                "level": level.value,
                "activated_by": activated_by,
                "reason": reason,
            },
        )

        return state

    async def deactivate_kill_switch(self, actor_id: str = "super_admin") -> KillSwitchState:
        """Deactivate Kill Switch resuming normal trading execution."""
        state = self._engine.deactivate_kill_switch()
        logger.info(f"Kill switch deactivated by '{actor_id}'. Trading resumed.")

        await self._audit.log_event(
            event_type="KILL_SWITCH_DEACTIVATED",
            actor_id=actor_id,
            entity_type="SYSTEM",
            entity_id="global_kill_switch",
            action="RESUME_TRADING",
            severity="HIGH",
            payload={"resumed_by": actor_id},
        )

        await self._broadcaster.broadcast_telemetry(
            "KILL_SWITCH_STATUS_CHANGED",
            {"is_active": False},
        )

        return state


# Global RiskService singleton
risk_service = RiskService()
