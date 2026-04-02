"""Tests for the async event bus."""

from __future__ import annotations

import asyncio
import unittest

from ai_orchestrator.core.event_bus import Event, EventBus


class TestEventBus(unittest.TestCase):
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("test_event", handler)
        self._run(bus.publish(Event(type="test_event", source="test", payload={"key": "value"})))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].type, "test_event")

    def test_subscribe_all(self):
        bus = EventBus()
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe_all(handler)
        self._run(bus.publish(Event(type="event_a", source="test")))
        self._run(bus.publish(Event(type="event_b", source="test")))
        self.assertEqual(len(received), 2)

    def test_no_subscribers(self):
        bus = EventBus()
        # Should not raise
        self._run(bus.publish(Event(type="no_one_listens", source="test")))

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("test", handler)
        bus.unsubscribe("test", handler)
        self._run(bus.publish(Event(type="test", source="test")))
        self.assertEqual(len(received), 0)

    def test_error_isolation(self):
        bus = EventBus()
        good_received = []

        async def bad_handler(event: Event):
            raise ValueError("handler error")

        async def good_handler(event: Event):
            good_received.append(event)

        bus.subscribe("test", bad_handler)
        bus.subscribe("test", good_handler)
        self._run(bus.publish(Event(type="test", source="test")))
        # Good handler should still receive despite bad handler
        self.assertEqual(len(good_received), 1)

    def test_history(self):
        bus = EventBus()
        self._run(bus.publish(Event(type="a", source="test")))
        self._run(bus.publish(Event(type="b", source="test")))
        self._run(bus.publish(Event(type="a", source="test")))

        all_history = bus.get_history()
        self.assertEqual(len(all_history), 3)

        a_history = bus.get_history("a")
        self.assertEqual(len(a_history), 2)

    def test_clear(self):
        bus = EventBus()
        async def noop(e): pass
        bus.subscribe("test", noop)
        self._run(bus.publish(Event(type="test", source="test")))
        bus.clear()
        self.assertEqual(bus.subscriber_count, {})
        self.assertEqual(bus.get_history(), [])


if __name__ == "__main__":
    unittest.main()
