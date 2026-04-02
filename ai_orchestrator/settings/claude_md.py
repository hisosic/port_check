"""CLAUDE.md generator - creates project-specific Claude Code guides."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_orchestrator.core.context import Context
from ai_orchestrator.core.registry import Registry


def generate_claude_md(
    registry: Registry,
    context: Context | None = None,
) -> str:
    """Generate a comprehensive CLAUDE.md for the project."""
    sections: list[str] = []

    # Header
    sections.append("# AI Agent Orchestrator - Project Guide\n")
    sections.append(
        "이 프로젝트는 20개 전문 에이전트가 협력하는 동적 AI 자동화 프레임워크입니다.\n"
        "MCP, Skills, Agent, Harness를 상황에 맞게 최적으로 연결하고 동적으로 변동합니다.\n"
    )

    # Project context
    if context:
        sections.append("## Project Info\n")
        sections.append(f"- **Language**: {context.primary_language.value}")
        sections.append(f"- **Framework**: {context.framework}")
        sections.append(f"- **Files**: {len(context.files)}")
        if context.git.is_repo:
            sections.append(f"- **Branch**: `{context.git.branch}`")
            sections.append(f"- **Remote**: `{context.git.remote_url}`")
        sections.append("")

    # Available agents
    sections.append("## Available Agents (20 Specialists)\n")
    sections.append("| Agent | Priority | Capabilities |")
    sections.append("|-------|----------|-------------|")

    for info in sorted(registry.all_agents(), key=lambda a: a.priority, reverse=True):
        caps = ", ".join(info.capabilities[:4])
        sections.append(f"| **{info.name}** | {info.priority} | {caps} |")

    sections.append("")

    # Usage
    sections.append("## Quick Start\n")
    sections.append("```bash")
    sections.append("# Analyze a project")
    sections.append('python -m ai_orchestrator --task "analyze this project"')
    sections.append("")
    sections.append("# Run specific agents")
    sections.append("python -m ai_orchestrator --run-agents security_auditor,code_analyzer")
    sections.append("")
    sections.append("# Generate MCP and Claude configs")
    sections.append("python -m ai_orchestrator --generate-config")
    sections.append("")
    sections.append("# Start as MCP server")
    sections.append("python -m ai_orchestrator --mcp-server context_engine")
    sections.append("")
    sections.append("# List all agents")
    sections.append("python -m ai_orchestrator --list-agents")
    sections.append("```\n")

    # Architecture
    sections.append("## Architecture\n")
    sections.append("```")
    sections.append("Task → Router (capability scoring) → Execution Plan (DAG)")
    sections.append("  ↓")
    sections.append("Context Engine → [Agent Group 1] → [Agent Group 2] → ... → Results")
    sections.append("  ↕                    ↕                    ↕")
    sections.append("         Event Bus (async pub/sub for inter-agent communication)")
    sections.append("```\n")

    sections.append("### Core Components\n")
    sections.append("- **Engine**: Central orchestrator - discovers, registers, and executes agents")
    sections.append("- **Router**: Scores agents by capability match and builds execution plans")
    sections.append("- **Registry**: Dynamic agent store with health tracking")
    sections.append("- **Event Bus**: Async pub/sub for decoupled agent communication")
    sections.append("- **Context**: Shared data bag that flows through the agent pipeline")
    sections.append("- **Plugin Loader**: Auto-discovers agents at startup (supports external plugins)")
    sections.append("")

    # MCP integration
    sections.append("## MCP Integration\n")
    sections.append("Agents that expose `as_mcp_tools()` are automatically available as MCP servers.")
    sections.append("The framework generates `settings.json` with all MCP server entries.\n")

    mcp_agents = [
        info for info in registry.all_agents()
        if info.instance.as_mcp_tools()
    ]
    if mcp_agents:
        sections.append("MCP-enabled agents:")
        for info in mcp_agents:
            tools = info.instance.as_mcp_tools()
            tool_names = ", ".join(t["name"] for t in tools)
            sections.append(f"- **{info.name}**: {tool_names}")
        sections.append("")

    # Extending
    sections.append("## Adding New Agents\n")
    sections.append("1. Create a new file in `ai_orchestrator/agents/`")
    sections.append("2. Subclass `BaseAgent` and implement `execute()`")
    sections.append("3. Declare `name`, `capabilities`, `input_types`, `output_types`, `priority`")
    sections.append("4. The agent is auto-discovered on next startup - zero config needed")
    sections.append("")
    sections.append("For external plugins, set `AI_ORCHESTRATOR_PLUGINS=/path/to/plugins`")
    sections.append("")

    return "\n".join(sections)


def write_claude_md(
    registry: Registry,
    output_dir: str = ".",
    context: Context | None = None,
) -> str:
    """Generate and write CLAUDE.md."""
    content = generate_claude_md(registry, context)
    output_path = Path(output_dir) / "CLAUDE.md"
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)
