"""Core orchestration engine - the central coordinator."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ai_orchestrator.core.context import AgentResult, Context
from ai_orchestrator.core.event_bus import Event, EventBus
from ai_orchestrator.core.plugin_loader import discover_agents
from ai_orchestrator.core.registry import Registry
from ai_orchestrator.core.router import Plan, Router

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central orchestration engine.

    On init:
    1. Discovers all agent classes via plugin_loader
    2. Registers them in the registry
    3. Boots the event bus
    4. Creates the router

    Exposes execute() as the primary API.
    """

    def __init__(
        self,
        working_dir: str | None = None,
        extra_plugin_dirs: list[str] | None = None,
        auto_discover: bool = True,
    ) -> None:
        self.working_dir = working_dir
        self.registry = Registry()
        self.event_bus = EventBus()
        self.router = Router(self.registry)
        self._initialized = False
        self._extra_plugin_dirs = extra_plugin_dirs

        if auto_discover:
            self._agent_classes = discover_agents(extra_plugin_dirs)
        else:
            self._agent_classes = []

    async def initialize(self) -> None:
        """Boot up: instantiate and register all discovered agents."""
        if self._initialized:
            return

        for agent_class in self._agent_classes:
            try:
                agent = agent_class(
                    event_bus=self.event_bus,
                    registry=self.registry,
                )
                await self.registry.register(agent)
            except Exception as e:
                logger.error("Failed to initialize agent %s: %s", agent_class.__name__, e)

        self._initialized = True
        logger.info(
            "Orchestrator initialized with %d agents", self.registry.agent_count
        )

        await self.event_bus.publish(Event(
            type="orchestrator.initialized",
            source="orchestrator",
            payload={"agent_count": self.registry.agent_count},
        ))

    async def execute(
        self,
        task: str,
        context: Context | None = None,
        required_agents: list[str] | None = None,
    ) -> Context:
        """Execute a task through the agent pipeline.

        Args:
            task: Natural language task description
            context: Optional pre-populated context
            required_agents: Optional list of agents to force-include

        Returns:
            The context with all agent results
        """
        if not self._initialized:
            await self.initialize()

        if context is None:
            context = Context(working_dir=self.working_dir, task=task)
        else:
            context.task = task

        await self.event_bus.publish(Event(
            type="task.started",
            source="orchestrator",
            payload={"task": task},
        ))

        # Generate execution plan
        plan = self.router.route(task, required_agents)
        context.execution_plan = plan.agent_names()

        logger.info("Executing plan with %d steps across %d groups",
                     len(plan.steps), plan.total_groups)

        # Execute plan group by group
        for group_id, steps in sorted(plan.groups().items()):
            agent_names = [s.agent_name for s in steps]
            logger.info("Executing group %d: %s", group_id, agent_names)

            if len(steps) == 1:
                await self._execute_agent(steps[0].agent_name, context)
            else:
                # Run parallel group concurrently
                tasks = [
                    self._execute_agent(step.agent_name, context)
                    for step in steps
                ]
                await asyncio.gather(*tasks)

        await self.event_bus.publish(Event(
            type="task.completed",
            source="orchestrator",
            payload={
                "task": task,
                "results": {
                    name: result.success
                    for name, result in context.results.items()
                },
            },
        ))

        return context

    async def _execute_agent(self, agent_name: str, context: Context) -> None:
        """Execute a single agent with error handling and metrics."""
        info = self.registry.get(agent_name)
        if not info:
            logger.warning("Agent not found: %s", agent_name)
            return

        agent = info.instance
        context.active_agents.add(agent_name)

        start_time = time.time()
        try:
            logger.info("Starting agent: %s", agent_name)
            result = await agent.execute(context)
            result.duration_ms = (time.time() - start_time) * 1000
            context.add_result(result)
            await self.registry.record_execution(agent_name, result.duration_ms)

            await self.event_bus.publish(Event(
                type="agent.completed",
                source=agent_name,
                payload={
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                    "data_keys": list(result.data.keys()),
                },
            ))

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("Agent %s failed: %s", agent_name, e, exc_info=True)
            context.add_result(AgentResult(
                agent_name=agent_name,
                success=False,
                errors=[str(e)],
                duration_ms=duration_ms,
            ))
            await self.registry.update_health(agent_name, False)

            await self.event_bus.publish(Event(
                type="agent.failed",
                source=agent_name,
                payload={"error": str(e)},
            ))
        finally:
            context.active_agents.discard(agent_name)

    async def execute_single(
        self, agent_name: str, context: Context | None = None, task: str = ""
    ) -> AgentResult:
        """Execute a single agent directly (bypass routing)."""
        if not self._initialized:
            await self.initialize()

        if context is None:
            context = Context(working_dir=self.working_dir, task=task)

        await self._execute_agent(agent_name, context)
        return context.get_result(agent_name) or AgentResult(
            agent_name=agent_name, success=False, errors=["Agent not found"]
        )

    async def health_check(self) -> dict[str, bool]:
        """Run health checks on all agents."""
        results = {}
        for info in self.registry.all_agents():
            try:
                healthy = await info.instance.health_check()
                await self.registry.update_health(info.name, healthy)
                results[info.name] = healthy
            except Exception:
                results[info.name] = False
                await self.registry.update_health(info.name, False)
        return results

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents and their capabilities."""
        return self.registry.summary()

    async def generate_configs(self) -> dict[str, str]:
        """Generate all configuration artifacts."""
        from ai_orchestrator.core.config_generator import ConfigGenerator
        generator = ConfigGenerator(self.registry)
        return await generator.generate_all(self.working_dir or ".")
