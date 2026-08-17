"""In-memory thread-safe implementation of Order and Position repositories."""

import asyncio
from openquant.domain.models.order import Order
from openquant.domain.models.position import Position
from openquant.domain.ports.repositories import IOrderRepository, IPositionRepository


class InMemoryOrderRepository(IOrderRepository):
    """In-memory storage for orders."""

    def __init__(self) -> None:
        self._orders_by_id: dict[str, Order] = {}
        self._orders_by_idempotency_key: dict[tuple[str, str], Order] = {}
        self._lock = asyncio.Lock()

    async def get_by_id(self, order_id: str) -> Order | None:
        async with self._lock:
            return self._orders_by_id.get(order_id)

    async def get_by_idempotency_key(self, idempotency_key: str, account_id: str) -> Order | None:
        async with self._lock:
            return self._orders_by_idempotency_key.get((account_id, idempotency_key))

    async def save(self, order: Order) -> None:
        async with self._lock:
            self._orders_by_id[order.order_id] = order
            self._orders_by_idempotency_key[(order.account_id, order.idempotency_key)] = order

    async def list_open_orders(self, account_id: str) -> list[Order]:
        async with self._lock:
            return [
                o for o in self._orders_by_id.values()
                if o.account_id == account_id and not o.is_terminal
            ]

    async def list_all(self, account_id: str | None = None) -> list[Order]:
        async with self._lock:
            if account_id:
                return [o for o in self._orders_by_id.values() if o.account_id == account_id]
            return list(self._orders_by_id.values())

    def clear(self) -> None:
        self._orders_by_id.clear()
        self._orders_by_idempotency_key.clear()


class InMemoryPositionRepository(IPositionRepository):
    """In-memory storage for positions."""

    def __init__(self) -> None:
        self._positions: dict[tuple[str, str], Position] = {}
        self._lock = asyncio.Lock()

    async def get_position(self, account_id: str, symbol: str) -> Position | None:
        async with self._lock:
            return self._positions.get((account_id, symbol.upper()))

    async def list_positions(self, account_id: str) -> list[Position]:
        async with self._lock:
            return [p for p in self._positions.values() if p.account_id == account_id and p.quantity != 0]

    async def list_all(self) -> list[Position]:
        async with self._lock:
            return list(self._positions.values())

    async def save(self, position: Position) -> None:
        async with self._lock:
            self._positions[(position.account_id, position.symbol.upper())] = position

    def clear(self) -> None:
        self._positions.clear()


# Global singletons
order_repository = InMemoryOrderRepository()
position_repository = InMemoryPositionRepository()
