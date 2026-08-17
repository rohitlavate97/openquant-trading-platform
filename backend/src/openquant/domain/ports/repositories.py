"""Hexagonal Ports: Repository interfaces for persistent storage."""

from abc import ABC, abstractmethod
from typing import Any
from openquant.domain.models.order import Order
from openquant.domain.models.position import Position
from openquant.domain.models.promotion import StrategyEntity, PromotionGateRecord


class IOrderRepository(ABC):
    """Abstract interface for order persistence and idempotency key lookups."""

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Order | None:
        """Fetch order by internal unique order ID."""

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str, account_id: str) -> Order | None:
        """Fetch order by unique idempotency key within an account."""

    @abstractmethod
    async def save(self, order: Order) -> None:
        """Insert or update order entity."""

    @abstractmethod
    async def list_open_orders(self, account_id: str) -> list[Order]:
        """Fetch all currently non-terminal open orders for an account."""


class IPositionRepository(ABC):
    """Abstract interface for position persistence and state querying."""

    @abstractmethod
    async def get_position(self, account_id: str, symbol: str) -> Position | None:
        """Fetch position by account and symbol."""

    @abstractmethod
    async def list_positions(self, account_id: str) -> list[Position]:
        """Fetch all open positions for an account."""

    @abstractmethod
    async def save(self, position: Position) -> None:
        """Insert or update position entity."""


class IStrategyRepository(ABC):
    """Abstract interface for strategy registry and promotion state."""

    @abstractmethod
    async def get_by_id(self, strategy_id: str) -> StrategyEntity | None:
        """Fetch strategy by ID."""

    @abstractmethod
    async def save(self, strategy: StrategyEntity) -> None:
        """Insert or update strategy entity."""

    @abstractmethod
    async def record_promotion_event(self, record: PromotionGateRecord) -> None:
        """Persist immutable promotion audit trail."""


class IAuditLogRepository(ABC):
    """Abstract interface for immutable audit trails and risk check logs."""

    @abstractmethod
    async def record_event(
        self,
        event_type: str,
        actor_id: str,
        entity_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Append an event to the audit log."""
