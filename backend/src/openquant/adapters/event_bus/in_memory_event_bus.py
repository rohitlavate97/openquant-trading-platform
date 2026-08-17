"""In-memory asynchronous Publish-Subscribe Event Bus implementation."""

import asyncio
from collections import defaultdict
import logging
from typing import Any
from openquant.domain.ports.event_bus import EventHandler, IEventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(IEventBus):
    """Thread-safe in-memory publish-subscribe domain event dispatcher."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_subscribers: list[EventHandler] = []
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, event_data: dict[str, Any]) -> None:
        """Publish an event payload to matching topic subscribers."""
        handlers_to_run: list[EventHandler] = []
        async with self._lock:
            # Exact topic subscribers
            handlers_to_run.extend(self._subscribers.get(topic, []))
            # Global / wildcard subscribers
            handlers_to_run.extend(self._wildcard_subscribers)

        for handler in handlers_to_run:
            try:
                res = handler(event_data)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"Error in event handler for topic '{topic}': {e}", exc_info=True)

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe a callback to a specific topic or '*' wildcard."""
        async with self._lock:
            if topic == "*":
                if handler not in self._wildcard_subscribers:
                    self._wildcard_subscribers.append(handler)
            else:
                if handler not in self._subscribers[topic]:
                    self._subscribers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from a topic."""
        async with self._lock:
            if topic == "*":
                if handler in self._wildcard_subscribers:
                    self._wildcard_subscribers.remove(handler)
            else:
                if topic in self._subscribers and handler in self._subscribers[topic]:
                    self._subscribers[topic].remove(handler)

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._subscribers.clear()
        self._wildcard_subscribers.clear()


# Global event bus singleton
event_bus = InMemoryEventBus()
