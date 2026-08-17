"""In-memory repository for Live Trading execution sessions."""

import asyncio
from openquant.domain.models.live_trading import LiveStrategySession, LiveTradingState
from openquant.domain.ports.live_trading_port import ILiveSessionRepository


class InMemoryLiveSessionRepository(ILiveSessionRepository):
    """Thread-safe in-memory store for live strategy sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, LiveStrategySession] = {}
        self._lock = asyncio.Lock()

    async def save(self, session: LiveStrategySession) -> None:
        async with self._lock:
            self._sessions[session.session_id] = session

    async def get_by_id(self, session_id: str) -> LiveStrategySession | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def get_active_by_strategy_id(self, strategy_id: str) -> LiveStrategySession | None:
        async with self._lock:
            for s in self._sessions.values():
                if s.strategy_id == strategy_id and s.state == LiveTradingState.ACTIVE:
                    return s
            return None

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        strategy_id: str | None = None,
        is_active_only: bool = False,
    ) -> list[LiveStrategySession]:
        async with self._lock:
            res = list(self._sessions.values())
            if strategy_id:
                res = [s for s in res if s.strategy_id == strategy_id]
            if is_active_only:
                res = [s for s in res if s.state == LiveTradingState.ACTIVE]
            res.sort(key=lambda s: s.activated_at, reverse=True)
            return res[offset : offset + limit]

    async def delete(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
