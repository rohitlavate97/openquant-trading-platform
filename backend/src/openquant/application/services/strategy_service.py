"""Application Service orchestrating Quantitative Strategy lifecycle, promotion stages, and engine execution."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import uuid

from openquant.domain.models.strategy import (
    Strategy,
    StrategyParameter,
    StrategySignal,
    StrategyState,
)
from openquant.domain.models.promotion import StrategyPromotionStage
from openquant.domain.models.market_data import Tick, Candle
from openquant.domain.ports.strategy_engine_port import IStrategyEngine
from openquant.domain.ports.strategy_sandbox import IStrategySandbox
from openquant.domain.ports.repositories import IStrategyRepository
from openquant.domain.ports.event_bus import IEventBus
from openquant.adapters.strategy.strategy_engine import strategy_engine
from openquant.adapters.sandbox.runner import strategy_sandbox_runner
from openquant.application.services.audit_service import AuditLogService, audit_log_service
from openquant.application.services.order_service import OrderManagementService, order_service

logger = logging.getLogger(__name__)


class StrategyService:
    """Application service for strategy registration, promotion gating, and execution."""

    def __init__(
        self,
        engine: IStrategyEngine | None = None,
        sandbox: IStrategySandbox | None = None,
        strategy_repo: IStrategyRepository | None = None,
        audit: AuditLogService | None = None,
        oms: OrderManagementService | None = None,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._engine: IStrategyEngine = engine or strategy_engine
        self._sandbox: IStrategySandbox = sandbox or strategy_sandbox_runner
        self._strategy_repo = strategy_repo
        self._audit: AuditLogService = audit or audit_log_service
        self._oms: OrderManagementService = oms or order_service
        self._event_bus = event_bus
        self._in_memory_strategies: dict[str, Strategy] = {}

    async def create_strategy(
        self,
        name: str,
        source_code: str,
        description: str = "",
        author_id: str = "system",
        parameters: list[StrategyParameter] | None = None,
        symbols: list[str] | None = None,
        account_id: str = "acc_main",
        broker_id: str = "paper_broker",
    ) -> Strategy:
        """Create and validate a new strategy entity."""
        # 1. AST Validation
        sec_check = self._sandbox.validate_code_ast(source_code)
        if not sec_check.is_safe:
            raise ValueError(f"Strategy source code failed AST security validation: {'; '.join(sec_check.violations)}")

        strategy_id = f"strat_{uuid.uuid4().hex[:10]}"
        strat = Strategy(
            strategy_id=strategy_id,
            name=name,
            description=description,
            author_id=author_id,
            source_code=source_code,
            parameters=parameters or [],
            symbols=symbols or ["AAPL"],
            account_id=account_id,
            broker_id=broker_id,
            promotion_stage=StrategyPromotionStage.DRAFT,
            state=StrategyState.INITIALIZED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self._in_memory_strategies[strategy_id] = strat
        await self._engine.register_strategy(strat)

        await self._audit.log_event(
            event_type="STRATEGY_CREATE",
            actor_id=author_id,
            entity_type="STRATEGY",
            entity_id=strategy_id,
            action="CREATE",
            payload={"name": name, "symbols": strat.symbols},
        )
        return strat

    async def get_strategy(self, strategy_id: str) -> Strategy | None:
        """Retrieve strategy by unique identifier."""
        return self._in_memory_strategies.get(strategy_id)

    async def list_strategies(self) -> list[Strategy]:
        """List all strategies."""
        return list(self._in_memory_strategies.values())

    async def update_strategy(
        self,
        strategy_id: str,
        name: str | None = None,
        description: str | None = None,
        source_code: str | None = None,
        parameters: list[StrategyParameter] | None = None,
        symbols: list[str] | None = None,
    ) -> Strategy | None:
        """Update strategy source code, configuration, or parameters."""
        strat = self._in_memory_strategies.get(strategy_id)
        if not strat:
            return None

        if source_code is not None:
            sec_check = self._sandbox.validate_code_ast(source_code)
            if not sec_check.is_safe:
                raise ValueError(f"Updated code failed AST security validation: {'; '.join(sec_check.violations)}")
            strat.source_code = source_code

        if name is not None:
            strat.name = name
        if description is not None:
            strat.description = description
        if parameters is not None:
            strat.parameters = parameters
        if symbols is not None:
            strat.symbols = symbols

        strat.updated_at = datetime.now(timezone.utc)
        await self._engine.register_strategy(strat)
        return strat

    async def start_strategy(self, strategy_id: str, actor_id: str = "system") -> bool:
        """Start strategy execution."""
        strat = self._in_memory_strategies.get(strategy_id)
        if not strat:
            return False

        success = await self._engine.start_strategy(strategy_id)
        if success:
            strat.state = StrategyState.RUNNING
            await self._audit.log_event(
                event_type="STRATEGY_START",
                actor_id=actor_id,
                entity_type="STRATEGY",
                entity_id=strategy_id,
                action="START",
                payload={"strategy_id": strategy_id},
            )
        return success

    async def stop_strategy(self, strategy_id: str, actor_id: str = "system") -> bool:
        """Stop strategy execution."""
        strat = self._in_memory_strategies.get(strategy_id)
        if not strat:
            return False

        success = await self._engine.stop_strategy(strategy_id)
        if success:
            strat.state = StrategyState.STOPPED
            await self._audit.log_event(
                event_type="STRATEGY_STOP",
                actor_id=actor_id,
                entity_type="STRATEGY",
                entity_id=strategy_id,
                action="STOP",
                payload={"strategy_id": strategy_id},
            )
        return success

    async def pause_strategy(self, strategy_id: str, actor_id: str = "system") -> bool:
        """Pause strategy execution."""
        strat = self._in_memory_strategies.get(strategy_id)
        if not strat:
            return False

        success = await self._engine.pause_strategy(strategy_id)
        if success:
            strat.state = StrategyState.PAUSED
        return success

    async def feed_market_tick(self, tick: Tick) -> list[StrategySignal]:
        """Dispatch tick to strategy engine and forward actionable signals."""
        signals = await self._engine.process_tick(tick)
        return signals

    async def feed_market_bar(self, candle: Candle) -> list[StrategySignal]:
        """Dispatch candle bar to strategy engine and forward actionable signals."""
        signals = await self._engine.process_bar(candle)
        return signals


# Global singleton strategy service
strategy_service = StrategyService()
