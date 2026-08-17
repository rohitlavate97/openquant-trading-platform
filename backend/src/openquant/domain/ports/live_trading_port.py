"""Domain ports for Live Trading Mode, session repository, and execution service."""

from abc import ABC, abstractmethod
from typing import Protocol
from openquant.domain.models.live_trading import (
    LiveCapitalAllocation,
    LivePreflightReport,
    LiveStrategySession,
    ScalingTier,
)


class ILiveSessionRepository(Protocol):
    """Storage contract for live strategy execution sessions."""

    async def save(self, session: LiveStrategySession) -> None:
        ...

    async def get_by_id(self, session_id: str) -> LiveStrategySession | None:
        ...

    async def get_active_by_strategy_id(self, strategy_id: str) -> LiveStrategySession | None:
        ...

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        strategy_id: str | None = None,
        is_active_only: bool = False,
    ) -> list[LiveStrategySession]:
        ...

    async def delete(self, session_id: str) -> bool:
        ...


class ILiveTradingService(ABC):
    """Service contract orchestrating live trading preflight, activation, scaling, and emergency halts."""

    @abstractmethod
    async def run_preflight_check(
        self,
        strategy_id: str,
        broker_id: str,
        account_id: str,
    ) -> LivePreflightReport:
        pass

    @abstractmethod
    async def activate_live_session(
        self,
        strategy_id: str,
        broker_id: str,
        account_id: str,
        allocation: LiveCapitalAllocation,
        activated_by: str,
        confirmed_by: str | None = None,
    ) -> LiveStrategySession:
        pass

    @abstractmethod
    async def adjust_scaling_tier(
        self,
        session_id: str,
        new_tier: ScalingTier,
        actor_id: str,
    ) -> LiveStrategySession:
        pass

    @abstractmethod
    async def halt_live_session(
        self,
        session_id: str,
        reason: str,
        actor_id: str,
    ) -> LiveStrategySession:
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> LiveStrategySession | None:
        pass

    @abstractmethod
    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        strategy_id: str | None = None,
        is_active_only: bool = False,
    ) -> list[LiveStrategySession]:
        pass
