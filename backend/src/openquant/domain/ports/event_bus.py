"""Hexagonal Port: Event Bus interface for internal publish-subscribe communication."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class IEventBus(ABC):
    """Abstract interface for publishing domain events and subscribing handlers."""

    @abstractmethod
    async def publish(self, topic: str, event_data: dict[str, Any]) -> None:
        """Publish an event payload to a given topic."""

    @abstractmethod
    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Register an asynchronous callback for events on a topic."""

    @abstractmethod
    async def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        """Remove a previously registered callback."""
