"""Domain Port for Real-Time Paper Trading Mode."""

from abc import ABC, abstractmethod
from decimal import Decimal
from openquant.domain.models.market_data import Tick
from openquant.domain.models.paper_trading import (
    PaperAccount,
    PaperOrderExecutionConfig,
    PaperTradingGateStatus,
    PaperTradingSession,
)


class IPaperTradingEngine(ABC):
    """Port defining live paper trading execution and session lifecycle operations."""

    @abstractmethod
    async def create_paper_account(
        self,
        name: str = "Primary Paper Account",
        initial_balance: Decimal = Decimal("100000.00"),
    ) -> PaperAccount:
        """Create a new isolated virtual paper trading account."""
        pass

    @abstractmethod
    async def get_paper_account(self, account_id: str) -> PaperAccount | None:
        """Retrieve paper account status and balances."""
        pass

    @abstractmethod
    async def list_paper_accounts(self) -> list[PaperAccount]:
        """List all virtual paper accounts."""
        pass

    @abstractmethod
    async def start_session(
        self,
        strategy_id: str,
        account_id: str,
        symbols: list[str],
        config: PaperOrderExecutionConfig | None = None,
    ) -> PaperTradingSession:
        """Launch a real-time paper trading session for a strategy."""
        pass

    @abstractmethod
    async def pause_session(self, session_id: str) -> PaperTradingSession | None:
        """Temporarily pause order dispatching for a paper session."""
        pass

    @abstractmethod
    async def stop_session(self, session_id: str) -> PaperTradingSession | None:
        """Stop and tear down a paper trading session."""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> PaperTradingSession | None:
        """Retrieve paper session details."""
        pass

    @abstractmethod
    async def list_sessions(self) -> list[PaperTradingSession]:
        """List all paper trading sessions."""
        pass

    @abstractmethod
    async def process_market_tick(self, tick: Tick) -> None:
        """Ingest live tick and evaluate active paper trading strategies."""
        pass

    @abstractmethod
    async def evaluate_gate_status(self, session_id: str) -> PaperTradingGateStatus | None:
        """Evaluate Stage 5 promotion gate criteria."""
        pass
