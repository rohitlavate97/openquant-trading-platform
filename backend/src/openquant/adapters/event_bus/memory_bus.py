"""In-memory Event Bus implementation for domain events and internal messaging."""

import asyncio
import logging
from collections import defaultdict
from typing import Any
from openquant.domain.ports.event_bus import IEventBus, EventHandler

logger = logging.getLogger(__name__)


class InMemoryEventBus(IEventBus):
    """Asynchronous in-memory event bus with isolated error handling per subscriber."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    async def publish(self, topic: str, event_data: dict[str, Any]) -> None:
        """Broadcast event to all topic subscribers concurrently."""
        handlers = list(self._subscribers.get(topic, []))
        if not handlers:
            return

        async def _safe_handle(h: EventHandler) -> None:
            try:
                await h(event_data)
            except Exception as e:
                logger.error("Error in event handler for topic '%s': %s", topic, e, exc_info=True)

        await asyncio.gather(*(_safe_handle(h) for h in handlers))

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Add subscriber callback to topic."""
        if handler not in self._subscribers[topic]:
            self._subscribers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        """Remove subscriber callback from topic."""
        if handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)


# Global event bus instance
event_bus = InMemoryEventBus()
