"""Tests for the task router."""

from __future__ import annotations

import asyncio
import unittest

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context
from ai_orchestrator.core.registry import Registry
from ai_orchestrator.core.router import Router


class SecurityAgent(BaseAgent):
    name = "security_auditor"
    capabilities = ["security", "vulnerability", "audit"]
    input_types = ["project_info"]
    output_types = ["security_findings"]
    priority = 85

    async def execute(self, context: Context) -> AgentResult:
        return self._success()


class TestAgent(BaseAgent):
    name = "test_orchestrator"
    capabilities = ["test", "testing", "unittest"]
    input_types = ["project_info"]
    output_types = ["test_results"]
    priority = 80

    async def execute(self, context: Context) -> AgentResult:
        return self._success()


class ContextAgent(BaseAgent):
    name = "context_engine"
    capabilities = ["context", "project_detection"]
    input_types = []
    output_types = ["project_info"]
    priority = 100

    async def execute(self, context: Context) -> AgentResult:
        return self._success()


class TestRouter(unittest.TestCase):
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _setup_registry(self) -> Registry:
        reg = Registry()
        self._run(reg.register(ContextAgent()))
        self._run(reg.register(SecurityAgent()))
        self._run(reg.register(TestAgent()))
        return reg

    def test_route_security_task(self):
        reg = self._setup_registry()
        router = Router(reg)
        plan = router.route("check security vulnerabilities")
        names = plan.agent_names()
        self.assertIn("context_engine", names)
        self.assertIn("security_auditor", names)

    def test_route_test_task(self):
        reg = self._setup_registry()
        router = Router(reg)
        plan = router.route("run tests")
        names = plan.agent_names()
        self.assertIn("context_engine", names)
        self.assertIn("test_orchestrator", names)

    def test_context_engine_always_first(self):
        reg = self._setup_registry()
        router = Router(reg)
        plan = router.route("anything")
        if plan.steps:
            self.assertEqual(plan.steps[0].agent_name, "context_engine")

    def test_required_agents(self):
        reg = self._setup_registry()
        router = Router(reg)
        plan = router.route("do something", required_agents=["security_auditor"])
        self.assertIn("security_auditor", plan.agent_names())

    def test_empty_task(self):
        reg = self._setup_registry()
        router = Router(reg)
        plan = router.route("")
        # Should still include context_engine
        self.assertIn("context_engine", plan.agent_names())

    def test_route_single(self):
        reg = self._setup_registry()
        router = Router(reg)
        result = router.route_single("security")
        self.assertEqual(result, "security_auditor")

    def test_route_single_no_match(self):
        reg = self._setup_registry()
        router = Router(reg)
        result = router.route_single("nonexistent_xyz_capability")
        self.assertIsNone(result)

    def test_plan_groups(self):
        reg = self._setup_registry()
        router = Router(reg)
        plan = router.route("test security")
        groups = plan.groups()
        self.assertGreater(len(groups), 0)


if __name__ == "__main__":
    unittest.main()
