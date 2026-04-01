"""Skill Composer - Chains agent capabilities into compound skills.

Creates execution chains by matching output_types of one agent
to input_types of the next, forming automated skill pipelines.
"""

from __future__ import annotations

from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

# Pre-defined skill chains for common tasks
SKILL_CHAINS: dict[str, dict[str, Any]] = {
    "full_analysis": {
        "description": "Complete code analysis pipeline",
        "agents": ["code_analyzer", "code_reviewer", "security_auditor", "performance_optimizer"],
        "trigger_keywords": ["analyze", "full", "complete", "comprehensive"],
    },
    "review_and_fix": {
        "description": "Review code and suggest fixes",
        "agents": ["code_analyzer", "code_reviewer", "refactor_advisor"],
        "trigger_keywords": ["review", "fix", "improve", "clean"],
    },
    "security_pipeline": {
        "description": "Full security audit pipeline",
        "agents": ["dependency_manager", "security_auditor", "config_optimizer"],
        "trigger_keywords": ["security", "audit", "vulnerability", "secure"],
    },
    "deploy_pipeline": {
        "description": "Deployment readiness pipeline",
        "agents": ["test_orchestrator", "security_auditor", "deploy_manager", "config_optimizer"],
        "trigger_keywords": ["deploy", "release", "production", "ship"],
    },
    "documentation_pipeline": {
        "description": "Auto-documentation pipeline",
        "agents": ["code_analyzer", "api_architect", "doc_generator"],
        "trigger_keywords": ["document", "docs", "readme", "api_docs"],
    },
    "debug_pipeline": {
        "description": "Error investigation pipeline",
        "agents": ["error_diagnostor", "log_analyzer", "data_flow_tracer", "code_analyzer"],
        "trigger_keywords": ["debug", "error", "crash", "investigate"],
    },
    "setup_tools": {
        "description": "AI tool setup and optimization",
        "agents": ["mcp_connector", "config_optimizer", "skill_composer"],
        "trigger_keywords": ["setup", "tools", "mcp", "configure", "automate"],
    },
    "performance_pipeline": {
        "description": "Performance optimization pipeline",
        "agents": ["resource_monitor", "performance_optimizer", "code_analyzer", "refactor_advisor"],
        "trigger_keywords": ["performance", "speed", "optimize", "slow"],
    },
}


class SkillComposerAgent(BaseAgent):
    name = "skill_composer"
    capabilities = ["skill", "chain", "compose", "pipeline", "automate", "workflow"]
    input_types = ["project_info"]
    output_types = ["skill_chains", "recommended_skills", "dynamic_chain"]
    priority = 75

    async def execute(self, context: Context) -> AgentResult:
        task = context.task.lower()

        # Find matching skill chains
        matched_chains = self._match_chains(task)

        # Build dynamic chain from agent capabilities
        dynamic_chain = self._build_dynamic_chain(task, context)

        # Generate recommended skills based on project
        recommendations = self._recommend_skills(context)

        await context.set("skill_chains", matched_chains)
        await context.set("recommended_skills", recommendations)
        if dynamic_chain:
            await context.set("dynamic_chain", dynamic_chain)

        await self.emit("skills.composed", {
            "matched_chains": len(matched_chains),
            "dynamic_chain_length": len(dynamic_chain.get("agents", [])) if dynamic_chain else 0,
        })

        return self._success(
            matched_chains=[
                {"name": name, "agents": chain["agents"]}
                for name, chain in matched_chains.items()
            ],
            dynamic_chain=dynamic_chain,
            recommendations=recommendations,
        )

    def _match_chains(self, task: str) -> dict[str, Any]:
        """Find pre-defined chains matching the task."""
        matched = {}
        for name, chain in SKILL_CHAINS.items():
            score = sum(1 for kw in chain["trigger_keywords"] if kw in task)
            if score > 0:
                matched[name] = {**chain, "score": score}
        return dict(sorted(matched.items(), key=lambda x: x[1]["score"], reverse=True))

    def _build_dynamic_chain(self, task: str, context: Context) -> dict[str, Any] | None:
        """Build a dynamic chain by matching agent inputs/outputs."""
        if not self.registry:
            return None

        # Start from agents that need no special input
        available_outputs: set[str] = {"project_info", "file_list", "git_state"}
        chain: list[str] = []
        remaining = [
            info for info in self.registry.healthy_agents()
            if info.name not in ("context_engine", "workflow_coordinator", "skill_composer")
        ]

        for _ in range(len(remaining)):
            best = None
            best_score = -1
            for info in remaining:
                if info.name in chain:
                    continue
                # Check if inputs are satisfied
                unmet = [i for i in info.input_types if i not in available_outputs]
                if not unmet:
                    # Score by how many new outputs this agent provides
                    new_outputs = len(set(info.output_types) - available_outputs)
                    relevance = sum(1 for cap in info.capabilities if cap in task)
                    score = new_outputs + relevance * 3
                    if score > best_score:
                        best_score = score
                        best = info

            if best and best_score > 0:
                chain.append(best.name)
                available_outputs.update(best.output_types)
            else:
                break

        if chain:
            return {
                "agents": chain,
                "type": "dynamic",
                "outputs": list(available_outputs),
            }
        return None

    def _recommend_skills(self, context: Context) -> list[dict[str, str]]:
        """Recommend skill chains based on project state."""
        recs = []
        framework = context.framework.lower() if context.framework else ""

        if context.git.has_uncommitted:
            recs.append({
                "skill": "review_and_fix",
                "reason": "Uncommitted changes detected - review before commit",
            })

        if "docker" in framework or "kubernetes" in framework:
            recs.append({
                "skill": "deploy_pipeline",
                "reason": "Container/orchestration configs detected",
            })

        if context.primary_language.value != "unknown":
            recs.append({
                "skill": "full_analysis",
                "reason": f"Comprehensive analysis for {context.primary_language.value} project",
            })

        recs.append({
            "skill": "setup_tools",
            "reason": "Optimize AI tool connections for this project",
        })

        return recs

    def as_mcp_tools(self) -> list[dict]:
        return [
            {
                "name": "compose_skill",
                "description": "Create a skill chain for a given task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task to compose skills for"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "list_skills",
                "description": "List all available pre-defined skill chains",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
