"""Tests for the Orchestrator engine."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from ai_orchestrator.core.context import AgentResult, Context
from ai_orchestrator.core.engine import Orchestrator
from ai_orchestrator.core.event_bus import EventBus
from ai_orchestrator.core.registry import Registry


class TestOrchestrator(unittest.TestCase):
    """Test the core orchestrator engine."""

    def test_init(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=False)
        self.assertIsNotNone(orch.registry)
        self.assertIsNotNone(orch.event_bus)
        self.assertIsNotNone(orch.router)
        self.assertFalse(orch._initialized)

    def test_init_auto_discover(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        self.assertGreater(len(orch._agent_classes), 0)

    def test_list_agents_before_init(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=False)
        agents = orch.list_agents()
        self.assertEqual(agents, [])


class TestOrchestratorAsync(unittest.TestCase):
    """Async tests for the orchestrator."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_initialize(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        self._run(orch.initialize())
        self.assertTrue(orch._initialized)
        self.assertGreater(orch.registry.agent_count, 0)

    def test_initialize_idempotent(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        self._run(orch.initialize())
        count1 = orch.registry.agent_count
        self._run(orch.initialize())
        count2 = orch.registry.agent_count
        self.assertEqual(count1, count2)

    def test_execute_task(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        context = self._run(orch.execute("analyze this project"))
        self.assertIsNotNone(context)
        self.assertGreater(len(context.results), 0)

    def test_execute_single_agent(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        result = self._run(orch.execute_single("context_engine"))
        self.assertIsInstance(result, AgentResult)

    def test_health_check(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        self._run(orch.initialize())
        results = self._run(orch.health_check())
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)

    def test_generate_configs(self):
        orch = Orchestrator(working_dir="/tmp", auto_discover=True)
        self._run(orch.initialize())
        configs = self._run(orch.generate_configs())
        self.assertIn("mcp_servers.json", configs)
        self.assertIn("settings.json", configs)
        self.assertIn("CLAUDE.md", configs)


if __name__ == "__main__":
    unittest.main()
