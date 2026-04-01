"""Task router - capability-based scoring and execution plan generation."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_orchestrator.core.registry import AgentInfo, Registry

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """A single step in an execution plan."""
    agent_name: str
    input_mapping: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    parallel_group: int = 0  # Steps in the same group can run in parallel


@dataclass
class Plan:
    """An ordered execution plan as a DAG of steps."""
    steps: list[Step] = field(default_factory=list)
    task: str = ""
    total_groups: int = 0

    def groups(self) -> dict[int, list[Step]]:
        """Group steps by parallel execution group."""
        result: dict[int, list[Step]] = {}
        for step in self.steps:
            result.setdefault(step.parallel_group, []).append(step)
        return result

    def agent_names(self) -> list[str]:
        return [s.agent_name for s in self.steps]


class Router:
    """Routes tasks to agents by scoring capability matches.

    The router never uses hardcoded agent names. It matches
    capabilities to task keywords dynamically.
    """

    # Words to strip from task for capability matching
    STOP_WORDS = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "this", "that", "these", "those", "my", "your", "our",
        "and", "or", "but", "for", "with", "from", "to", "of", "in",
        "on", "at", "by", "it", "do", "does", "did", "will", "would",
        "can", "could", "should", "may", "might", "i", "we", "you",
        "please", "help", "me", "want", "need", "like",
    })

    # Capability synonyms for better matching
    SYNONYMS: dict[str, list[str]] = {
        "test": ["testing", "test", "unittest", "pytest", "jest", "spec"],
        "security": ["security", "vulnerability", "cve", "audit", "secure", "owasp"],
        "performance": ["performance", "speed", "optimize", "profiling", "slow", "fast", "benchmark"],
        "documentation": ["documentation", "docs", "readme", "docstring", "comment", "document"],
        "dependency": ["dependency", "dependencies", "package", "library", "module", "import", "npm", "pip"],
        "ci": ["ci", "cd", "pipeline", "github_actions", "workflow", "deploy", "build"],
        "code_analysis": ["analyze", "analysis", "structure", "ast", "parse", "inspect", "static"],
        "review": ["review", "quality", "convention", "lint", "style", "clean"],
        "refactor": ["refactor", "restructure", "simplify", "extract", "dedup", "improve"],
        "api": ["api", "endpoint", "rest", "graphql", "route", "controller", "openapi"],
        "data_flow": ["dataflow", "data_flow", "trace", "flow", "propagation", "mutation"],
        "resource": ["resource", "memory", "cpu", "disk", "monitor", "usage", "load"],
        "deploy": ["deploy", "deployment", "release", "rollout", "kubernetes", "docker", "terraform"],
        "log": ["log", "logging", "error_log", "trace", "debug", "monitor"],
        "config": ["config", "configuration", "settings", "env", "environment", "setup"],
        "mcp": ["mcp", "server", "tool", "protocol", "connect", "integration"],
        "skill": ["skill", "chain", "compose", "pipeline", "workflow", "automate"],
        "context": ["context", "project", "detect", "discover", "understand", "scan"],
        "error": ["error", "bug", "fix", "diagnose", "traceback", "exception", "crash", "debug"],
        "workflow": ["workflow", "orchestrate", "coordinate", "plan", "multi_step", "complex"],
    }

    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        self._build_synonym_index()

    def _build_synonym_index(self) -> None:
        """Build a reverse index: synonym word -> canonical capability."""
        self._synonym_index: dict[str, str] = {}
        for canonical, synonyms in self.SYNONYMS.items():
            for syn in synonyms:
                self._synonym_index[syn] = canonical

    def _extract_keywords(self, task: str) -> list[str]:
        """Extract meaningful keywords from a task description."""
        words = re.findall(r'[a-z_]+', task.lower())
        return [w for w in words if w not in self.STOP_WORDS and len(w) > 1]

    def _score_agent(self, agent: AgentInfo, keywords: list[str]) -> float:
        """Score an agent's relevance to the given keywords."""
        score = 0.0
        agent_caps = {c.lower() for c in agent.capabilities}

        for keyword in keywords:
            # Direct capability match
            if any(keyword in cap for cap in agent_caps):
                score += 10.0

            # Synonym match
            canonical = self._synonym_index.get(keyword)
            if canonical and any(canonical in cap for cap in agent_caps):
                score += 7.0

        # Priority bonus (0-100 mapped to 0-2)
        score += agent.priority / 50.0

        # Penalize overloaded agents
        if agent.execution_count > 10:
            score *= 0.95

        return score

    def route(self, task: str, required_agents: list[str] | None = None) -> Plan:
        """Generate an execution plan for a task.

        Args:
            task: Natural language task description
            required_agents: Optional list of agent names to force-include
        """
        keywords = self._extract_keywords(task)
        logger.info("Task keywords: %s", keywords)

        # Score all healthy agents
        scored: list[tuple[AgentInfo, float]] = []
        for agent in self.registry.healthy_agents():
            s = self._score_agent(agent, keywords)
            if s > 0:
                scored.append((agent, s))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Always include context_engine first if available
        context_engine = self.registry.get("context_engine")
        selected_names: list[str] = []
        if context_engine and context_engine.is_healthy:
            selected_names.append("context_engine")

        # Add force-included agents
        if required_agents:
            for name in required_agents:
                if name not in selected_names:
                    selected_names.append(name)

        # Add top scored agents (limit to reasonable number)
        max_agents = min(len(scored), 8)
        for agent, score in scored[:max_agents]:
            if agent.name not in selected_names:
                selected_names.append(agent.name)
                logger.debug("Selected %s (score: %.1f)", agent.name, score)

        # Build execution plan with dependency resolution
        plan = self._build_plan(task, selected_names)
        logger.info("Plan: %s", [s.agent_name for s in plan.steps])
        return plan

    def _build_plan(self, task: str, agent_names: list[str]) -> Plan:
        """Build an execution plan with dependency-based ordering."""
        steps: list[Step] = []
        group = 0

        # Group 0: Context engine always first
        if "context_engine" in agent_names:
            steps.append(Step(agent_name="context_engine", parallel_group=0))
            agent_names = [n for n in agent_names if n != "context_engine"]
            group = 1

        # Resolve dependencies: agents that produce outputs consumed by others go first
        remaining = list(agent_names)
        while remaining:
            # Find agents whose inputs are already satisfied
            current_group: list[str] = []
            next_remaining: list[str] = []

            available_outputs = set()
            for step in steps:
                info = self.registry.get(step.agent_name)
                if info:
                    available_outputs.update(info.output_types)

            for name in remaining:
                info = self.registry.get(name)
                if not info:
                    continue
                # Agent can run if it has no unmet input dependencies
                unmet = [i for i in info.input_types if i not in available_outputs]
                if not unmet or group == 0:
                    current_group.append(name)
                else:
                    next_remaining.append(name)

            if not current_group:
                # Break cycle: just add remaining agents
                current_group = next_remaining
                next_remaining = []

            for name in current_group:
                deps = []
                if group > 0:
                    # Depend on all agents in the previous group
                    deps = [s.agent_name for s in steps if s.parallel_group == group - 1]
                steps.append(Step(
                    agent_name=name,
                    depends_on=deps,
                    parallel_group=group,
                ))

            remaining = next_remaining
            group += 1

        return Plan(steps=steps, task=task, total_groups=group)

    def route_single(self, capability: str) -> str | None:
        """Find the single best agent for a capability."""
        agents = self.registry.find_by_capability(capability)
        return agents[0].name if agents else None
