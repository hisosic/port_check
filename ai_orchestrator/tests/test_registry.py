"""Tests for the agent registry."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import MagicMock

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context
from ai_orchestrator.core.registry import Registry


class MockAgent(BaseAgent):
    name = "mock_agent"
    capabilities = ["test", "mock"]
    input_types = ["project_info"]
    output_types = ["test_results"]
    priority = 50

    async def execute(self, context: Context) -> AgentResult:
        return self._success(message="mock executed")


class TestRegistry(unittest.TestCase):
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_register(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        self.assertEqual(reg.agent_count, 1)

    def test_get(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        info = reg.get("mock_agent")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "mock_agent")

    def test_get_nonexistent(self):
        reg = Registry()
        self.assertIsNone(reg.get("nonexistent"))

    def test_find_by_capability(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        results = reg.find_by_capability("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "mock_agent")

    def test_find_by_capability_no_match(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        results = reg.find_by_capability("nonexistent_capability")
        self.assertEqual(len(results), 0)

    def test_find_by_output(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        results = reg.find_by_output("test_results")
        self.assertEqual(len(results), 1)

    def test_unregister(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        self._run(reg.unregister("mock_agent"))
        self.assertEqual(reg.agent_count, 0)

    def test_health_tracking(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        self._run(reg.update_health("mock_agent", False))
        info = reg.get("mock_agent")
        self.assertFalse(info.is_healthy)

    def test_execution_stats(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        self._run(reg.record_execution("mock_agent", 100.0))
        self._run(reg.record_execution("mock_agent", 200.0))
        info = reg.get("mock_agent")
        self.assertEqual(info.execution_count, 2)
        self.assertAlmostEqual(info.avg_duration_ms, 150.0)

    def test_summary(self):
        reg = Registry()
        agent = MockAgent()
        self._run(reg.register(agent))
        summary = reg.summary()
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["name"], "mock_agent")


if __name__ == "__main__":
    unittest.main()
