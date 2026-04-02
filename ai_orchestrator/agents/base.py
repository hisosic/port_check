"""Base agent - the contract all 20 agents implement."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ai_orchestrator.core.context import AgentResult, Context

if TYPE_CHECKING:
    from ai_orchestrator.core.event_bus import EventBus
    from ai_orchestrator.core.registry import Registry

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all specialized agents.

    Every agent declares:
    - name: unique identifier
    - capabilities: what this agent can do (for router matching)
    - input_types: context keys this agent reads
    - output_types: context keys this agent writes
    - priority: 0-100, higher = preferred when multiple agents match
    """

    name: str = ""
    capabilities: list[str] = []
    input_types: list[str] = []
    output_types: list[str] = []
    priority: int = 50

    def __init__(
        self,
        event_bus: EventBus | None = None,
        registry: Registry | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.registry = registry
        self.logger = logging.getLogger(f"agent.{self.name}")

    @abstractmethod
    async def execute(self, context: Context) -> AgentResult:
        """Execute this agent's task given the shared context.

        Must return an AgentResult with success status and data.
        """
        ...

    async def health_check(self) -> bool:
        """Check if this agent is operational. Override for custom checks."""
        return True

    def as_mcp_tools(self) -> list[dict[str, Any]]:
        """Expose this agent's actions as MCP-compatible tools.

        Override to make this agent available as an MCP server.
        Returns a list of tool schemas following MCP protocol.
        """
        return []

    def _success(self, data: dict[str, Any] | None = None, **kwargs: Any) -> AgentResult:
        """Helper to create a successful result."""
        return AgentResult(
            agent_name=self.name,
            success=True,
            data=data or kwargs,
        )

    def _failure(self, error: str, data: dict[str, Any] | None = None) -> AgentResult:
        """Helper to create a failure result."""
        return AgentResult(
            agent_name=self.name,
            success=False,
            errors=[error],
            data=data or {},
        )

    async def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Publish an event to the bus."""
        if self.event_bus:
            from ai_orchestrator.core.event_bus import Event
            await self.event_bus.publish(Event(
                type=event_type,
                source=self.name,
                payload=payload or {},
            ))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} priority={self.priority}>"
