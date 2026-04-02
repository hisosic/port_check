"""Async event bus for decoupled inter-agent communication."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[["Event"], Coroutine[Any, Any, None]]


@dataclass
class Event:
    """An event published by an agent."""
    type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Async pub/sub event bus for agent communication.

    Agents publish events without knowing who subscribes.
    This ensures zero coupling between agents.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._history: list[Event] = []
        self._lock = asyncio.Lock()
        self._max_history = 1000

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug("Subscribed handler to event type: %s", event_type)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to ALL event types (used by WorkflowCoordinator)."""
        self.subscribe("*", handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching subscribers."""
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        handlers = list(self._subscribers.get(event.type, []))
        handlers.extend(self._subscribers.get("*", []))

        if not handlers:
            logger.debug("No handlers for event type: %s", event.type)
            return

        tasks = []
        for handler in handlers:
            tasks.append(self._safe_call(handler, event))

        await asyncio.gather(*tasks)

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """Call a handler with error isolation."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                "Event handler error for %s: %s", event.type, e, exc_info=True
            )

    def get_history(
        self, event_type: str | None = None, limit: int = 50
    ) -> list[Event]:
        """Get recent event history, optionally filtered by type."""
        if event_type:
            filtered = [e for e in self._history if e.type == event_type]
        else:
            filtered = list(self._history)
        return filtered[-limit:]

    @property
    def subscriber_count(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._subscribers.items()}

    def clear(self) -> None:
        """Reset the bus."""
        self._subscribers.clear()
        self._history.clear()
