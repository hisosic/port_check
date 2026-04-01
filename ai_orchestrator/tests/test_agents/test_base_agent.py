"""Tests for the BaseAgent contract."""

from __future__ import annotations

import asyncio
import unittest

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context
from ai_orchestrator.core.event_bus import EventBus


class ConcreteAgent(BaseAgent):
    name = "concrete"
    capabilities = ["test"]
    input_types = []
    output_types = ["test_output"]
    priority = 50

    async def execute(self, context: Context) -> AgentResult:
        await context.set("test_output", "hello")
        return self._success(message="done")


class FailingAgent(BaseAgent):
    name = "failing"
    capabilities = ["test"]
    input_types = []
    output_types = []
    priority = 50

    async def execute(self, context: Context) -> AgentResult:
        return self._failure("something went wrong")


class TestBaseAgent(unittest.TestCase):
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            BaseAgent()

    def test_concrete_agent_success(self):
        agent = ConcreteAgent()
        ctx = Context(working_dir="/tmp")
        result = self._run(agent.execute(ctx))
        self.assertTrue(result.success)
        self.assertEqual(result.agent_name, "concrete")
        self.assertEqual(result.data["message"], "done")

    def test_concrete_agent_writes_context(self):
        agent = ConcreteAgent()
        ctx = Context(working_dir="/tmp")
        self._run(agent.execute(ctx))
        value = self._run(ctx.get("test_output"))
        self.assertEqual(value, "hello")

    def test_failing_agent(self):
        agent = FailingAgent()
        ctx = Context(working_dir="/tmp")
        result = self._run(agent.execute(ctx))
        self.assertFalse(result.success)
        self.assertIn("something went wrong", result.errors)

    def test_agent_repr(self):
        agent = ConcreteAgent()
        self.assertIn("ConcreteAgent", repr(agent))
        self.assertIn("concrete", repr(agent))

    def test_health_check_default(self):
        agent = ConcreteAgent()
        result = self._run(agent.health_check())
        self.assertTrue(result)

    def test_mcp_tools_default(self):
        agent = ConcreteAgent()
        tools = agent.as_mcp_tools()
        self.assertEqual(tools, [])

    def test_emit_with_bus(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("test.event", handler)

        agent = ConcreteAgent(event_bus=bus)
        self._run(agent.emit("test.event", {"key": "value"}))
        self.assertEqual(len(received), 1)

    def test_emit_without_bus(self):
        agent = ConcreteAgent()
        # Should not raise even without a bus
        self._run(agent.emit("test.event"))


if __name__ == "__main__":
    unittest.main()
