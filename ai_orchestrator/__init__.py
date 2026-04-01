"""AI Agent Orchestrator - Dynamic AI Tool Automation Framework.

20개 전문 에이전트가 협력하여 MCP, Skills, Agent, Harness를
상황에 맞게 최적으로 연결하고 동적으로 변동하는 자동화 프레임워크.
"""

__version__ = "1.0.0"

from ai_orchestrator.core.engine import Orchestrator
from ai_orchestrator.core.context import Context
from ai_orchestrator.core.registry import Registry
from ai_orchestrator.core.event_bus import EventBus

__all__ = ["Orchestrator", "Context", "Registry", "EventBus", "__version__"]
