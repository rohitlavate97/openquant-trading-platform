"""Application Service for Real-Time Paper Trading Mode and Stage 5 Promotion Gate."""

import logging
from decimal import Decimal
from typing import Any

from openquant.domain.models.market_data import Tick
from openquant.domain.models.promotion import StrategyPromotionStage
from openquant.domain.models.paper_trading import (
    PaperAccount,
    PaperOrderExecutionConfig,
    PaperTradingGateStatus,
    PaperTradingSession,
)
from openquant.domain.ports.paper_trading_port import IPaperTradingEngine
from openquant.adapters.paper.paper_trading_engine import paper_trading_engine
from openquant.application.services.strategy_service import StrategyService, strategy_service
from openquant.application.services.audit_service import AuditLogService, audit_log_service

logger = logging.getLogger(__name__)


class PaperTradingService:
    """Application Service managing live simulated paper trading sessions."""

    def __init__(
        self,
        engine: IPaperTradingEngine | None = None,
        strat_svc: StrategyService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._engine: IPaperTradingEngine = engine or paper_trading_engine
        self._strategy_service: StrategyService = strat_svc or strategy_service
        self._audit: AuditLogService = audit or audit_log_service

    async def create_account(
        self,
        name: str = "Virtual Paper Account",
        initial_balance: Decimal = Decimal("100000.00"),
        actor_id: str = "system",
    ) -> PaperAccount:
        """Create a new virtual paper account."""
        account = await self._engine.create_paper_account(name=name, initial_balance=initial_balance)
        await self._audit.log_event(
            event_type="PAPER_ACCOUNT_CREATED",
            actor_id=actor_id,
            entity_type="PAPER_ACCOUNT",
            entity_id=account.account_id,
            action="CREATE",
            payload={"initial_balance": str(initial_balance), "name": name},
        )
        return account

    async def get_account(self, account_id: str) -> PaperAccount | None:
        """Retrieve paper account."""
        return await self._engine.get_paper_account(account_id)

    async def list_accounts(self) -> list[PaperAccount]:
        """List all paper accounts."""
        return await self._engine.list_paper_accounts()

    async def start_session(
        self,
        strategy_id: str,
        account_id: str,
        symbols: list[str],
        config: PaperOrderExecutionConfig | None = None,
        actor_id: str = "system",
    ) -> PaperTradingSession:
        """Start a live paper trading session for a strategy."""
        session = await self._engine.start_session(
            strategy_id=strategy_id,
            account_id=account_id,
            symbols=symbols,
            config=config,
        )

        # Update strategy promotion stage to PAPER_TRADING
        strat = await self._strategy_service.get_strategy(strategy_id)
        if strat:
            strat.promotion_stage = StrategyPromotionStage.PAPER_TRADING

        await self._audit.log_event(
            event_type="PAPER_SESSION_START",
            actor_id=actor_id,
            entity_type="STRATEGY",
            entity_id=strategy_id,
            action="START_PAPER_SESSION",
            payload={"session_id": session.session_id, "account_id": account_id, "symbols": symbols},
        )
        return session

    async def pause_session(self, session_id: str, actor_id: str = "system") -> PaperTradingSession | None:
        """Pause a paper trading session."""
        session = await self._engine.pause_session(session_id)
        if session:
            await self._audit.log_event(
                event_type="PAPER_SESSION_PAUSE",
                actor_id=actor_id,
                entity_type="PAPER_SESSION",
                entity_id=session_id,
                action="PAUSE",
                payload={"status": "PAUSED"},
            )
        return session

    async def stop_session(self, session_id: str, actor_id: str = "system") -> PaperTradingSession | None:
        """Stop a paper trading session."""
        session = await self._engine.stop_session(session_id)
        if session:
            await self._audit.log_event(
                event_type="PAPER_SESSION_STOP",
                actor_id=actor_id,
                entity_type="PAPER_SESSION",
                entity_id=session_id,
                action="STOP",
                payload={"status": "STOPPED"},
            )
        return session

    async def get_session(self, session_id: str) -> PaperTradingSession | None:
        """Retrieve paper session."""
        return await self._engine.get_session(session_id)

    async def list_sessions(self) -> list[PaperTradingSession]:
        """List all paper sessions."""
        return await self._engine.list_sessions()

    async def process_market_tick(self, tick: Tick) -> None:
        """Ingest live tick and trigger active paper strategies."""
        await self._engine.process_market_tick(tick)

    async def evaluate_gate_status(self, session_id: str) -> PaperTradingGateStatus | None:
        """Evaluate Stage 5 gate criteria."""
        return await self._engine.evaluate_gate_status(session_id)

    async def promote_to_human_approval(
        self,
        session_id: str,
        actor_id: str = "system",
        bypass_criteria: bool = False,
    ) -> bool:
        """Promote strategy from Stage 5 (PAPER_TRADING) to Stage 6 (HUMAN_APPROVAL)."""
        session = await self._engine.get_session(session_id)
        if not session:
            return False

        gate_status = await self._engine.evaluate_gate_status(session_id)
        if not gate_status:
            return False

        if not bypass_criteria and not gate_status.eligible_for_promotion:
            return False

        strat = await self._strategy_service.get_strategy(session.strategy_id)
        if strat:
            strat.promotion_stage = StrategyPromotionStage.HUMAN_APPROVAL
            await self._audit.log_event(
                event_type="PROMOTION_GATE_ADVANCE",
                actor_id=actor_id,
                entity_type="STRATEGY",
                entity_id=session.strategy_id,
                action="PROMOTE",
                payload={"target_stage": StrategyPromotionStage.HUMAN_APPROVAL, "session_id": session_id},
            )
            return True
        return False


# Global singleton paper trading service
paper_trading_service = PaperTradingService()
