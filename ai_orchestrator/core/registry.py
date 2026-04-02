"""Agent registry - dynamic discovery and capability lookup."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ai_orchestrator.agents.base import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Metadata about a registered agent."""
    name: str
    capabilities: list[str]
    input_types: list[str]
    output_types: list[str]
    priority: int
    instance: BaseAgent
    registered_at: float = field(default_factory=time.time)
    is_healthy: bool = True
    execution_count: int = 0
    avg_duration_ms: float = 0.0


class Registry:
    """Agent registry with capability-based lookup.

    Agents self-register on startup. The router queries the registry
    to find agents matching a given task's requirements.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentInfo] = {}
        self._lock = asyncio.Lock()

    async def register(self, agent: BaseAgent) -> None:
        """Register an agent instance."""
        async with self._lock:
            info = AgentInfo(
                name=agent.name,
                capabilities=list(agent.capabilities),
                input_types=list(agent.input_types),
                output_types=list(agent.output_types),
                priority=agent.priority,
                instance=agent,
            )
            self._agents[agent.name] = info
            logger.info("Registered agent: %s (capabilities: %s)", agent.name, agent.capabilities)

    async def unregister(self, name: str) -> None:
        async with self._lock:
            self._agents.pop(name, None)

    def get(self, name: str) -> AgentInfo | None:
        return self._agents.get(name)

    def get_agent(self, name: str) -> BaseAgent | None:
        info = self._agents.get(name)
        return info.instance if info else None

    def find_by_capability(self, capability: str) -> list[AgentInfo]:
        """Find all agents that declare a given capability."""
        results = []
        cap_lower = capability.lower()
        for info in self._agents.values():
            if info.is_healthy and any(cap_lower in c.lower() for c in info.capabilities):
                results.append(info)
        return sorted(results, key=lambda a: a.priority, reverse=True)

    def find_by_output(self, output_type: str) -> list[AgentInfo]:
        """Find agents that produce a given output type."""
        return [
            info for info in self._agents.values()
            if info.is_healthy and output_type in info.output_types
        ]

    def find_by_input(self, input_type: str) -> list[AgentInfo]:
        """Find agents that consume a given input type."""
        return [
            info for info in self._agents.values()
            if info.is_healthy and input_type in info.input_types
        ]

    def all_agents(self) -> list[AgentInfo]:
        return list(self._agents.values())

    def healthy_agents(self) -> list[AgentInfo]:
        return [a for a in self._agents.values() if a.is_healthy]

    async def update_health(self, name: str, healthy: bool) -> None:
        async with self._lock:
            if name in self._agents:
                self._agents[name].is_healthy = healthy

    async def record_execution(self, name: str, duration_ms: float) -> None:
        """Update execution statistics for an agent."""
        async with self._lock:
            if name in self._agents:
                info = self._agents[name]
                total = info.avg_duration_ms * info.execution_count + duration_ms
                info.execution_count += 1
                info.avg_duration_ms = total / info.execution_count

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "name": info.name,
                "capabilities": info.capabilities,
                "priority": info.priority,
                "healthy": info.is_healthy,
                "executions": info.execution_count,
            }
            for info in self._agents.values()
        ]
