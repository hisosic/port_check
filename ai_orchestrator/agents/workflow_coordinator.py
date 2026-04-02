"""Workflow Coordinator - The master orchestrator agent.

Can decompose complex multi-step tasks into sub-tasks,
route each through the system, and aggregate results.
Subscribes to ALL events for global state awareness.
"""

from __future__ import annotations

from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context
from ai_orchestrator.core.event_bus import Event

# Task decomposition patterns
TASK_PATTERNS: dict[str, list[str]] = {
    "production_ready": [
        "context_engine", "code_analyzer", "test_orchestrator",
        "security_auditor", "dependency_manager", "cicd_integrator",
        "config_optimizer", "doc_generator",
    ],
    "full_review": [
        "context_engine", "code_analyzer", "code_reviewer",
        "refactor_advisor", "security_auditor", "performance_optimizer",
    ],
    "setup_automation": [
        "context_engine", "mcp_connector", "skill_composer",
        "config_optimizer", "cicd_integrator",
    ],
    "debug_issue": [
        "context_engine", "error_diagnostor", "log_analyzer",
        "data_flow_tracer", "code_analyzer",
    ],
    "optimize": [
        "context_engine", "performance_optimizer", "code_analyzer",
        "refactor_advisor", "resource_monitor",
    ],
    "secure": [
        "context_engine", "security_auditor", "dependency_manager",
        "config_optimizer", "code_reviewer",
    ],
    "document": [
        "context_engine", "code_analyzer", "api_architect",
        "doc_generator",
    ],
    "deploy": [
        "context_engine", "test_orchestrator", "security_auditor",
        "deploy_manager", "config_optimizer",
    ],
}

PATTERN_KEYWORDS: dict[str, list[str]] = {
    "production_ready": ["production", "release", "ship", "launch", "ready", "prepare"],
    "full_review": ["review", "quality", "check", "audit", "inspect"],
    "setup_automation": ["setup", "automate", "automation", "configure", "mcp", "tool"],
    "debug_issue": ["debug", "error", "bug", "fix", "crash", "issue", "broken"],
    "optimize": ["optimize", "performance", "speed", "slow", "fast", "improve"],
    "secure": ["security", "secure", "vulnerability", "cve", "hack", "protect"],
    "document": ["document", "docs", "readme", "api", "describe"],
    "deploy": ["deploy", "release", "kubernetes", "docker", "ci", "cd"],
}


class WorkflowCoordinatorAgent(BaseAgent):
    name = "workflow_coordinator"
    capabilities = ["workflow", "orchestration", "multi_step", "coordination", "planning", "complex_task"]
    input_types = ["project_info"]
    output_types = ["workflow_plan", "aggregated_results"]
    priority = 95

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._global_events: list[Event] = []

    async def execute(self, context: Context) -> AgentResult:
        task = context.task.lower()

        # Detect which workflow pattern matches
        matched_pattern = self._match_pattern(task)
        agent_sequence = TASK_PATTERNS.get(matched_pattern, [])

        if not agent_sequence:
            # Fallback: let the router handle it
            return self._success(
                pattern="auto_routed",
                message="Task delegated to dynamic router",
            )

        # Store the workflow plan
        await context.set("workflow_plan", {
            "pattern": matched_pattern,
            "agents": agent_sequence,
            "task": context.task,
        })

        await self.emit("workflow.planned", {
            "pattern": matched_pattern,
            "agents": agent_sequence,
        })

        # Check which agents have already run
        already_done = set(context.results.keys())
        pending = [a for a in agent_sequence if a not in already_done]

        return self._success(
            pattern=matched_pattern,
            total_agents=len(agent_sequence),
            already_completed=list(already_done),
            pending_agents=pending,
        )

    def _match_pattern(self, task: str) -> str:
        """Find the best matching workflow pattern for a task."""
        best_pattern = ""
        best_score = 0

        for pattern, keywords in PATTERN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in task)
            if score > best_score:
                best_score = score
                best_pattern = pattern

        return best_pattern if best_score > 0 else "full_review"

    async def _on_global_event(self, event: Event) -> None:
        """Track all events for global awareness."""
        self._global_events.append(event)
        if len(self._global_events) > 500:
            self._global_events = self._global_events[-500:]

    def as_mcp_tools(self) -> list[dict]:
        return [
            {
                "name": "plan_workflow",
                "description": "Decompose a complex task into an agent workflow plan",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task to decompose"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "list_patterns",
                "description": "List available workflow patterns and their agent sequences",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
