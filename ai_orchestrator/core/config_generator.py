"""Configuration artifact generator.

Generates MCP server configs, Claude Code settings.json,
and CLAUDE.md from the live agent registry.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ai_orchestrator.core.registry import Registry

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """Generates configuration files from the agent registry."""

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    async def generate_all(self, working_dir: str) -> dict[str, str]:
        """Generate all config artifacts. Returns {filename: content}."""
        results = {}

        mcp_config = self.generate_mcp_config()
        results["mcp_servers.json"] = json.dumps(mcp_config, indent=2)

        settings = self.generate_claude_settings()
        results["settings.json"] = json.dumps(settings, indent=2)

        claude_md = self.generate_claude_md()
        results["CLAUDE.md"] = claude_md

        hooks_config = self.generate_hooks_config()
        results["hooks.json"] = json.dumps(hooks_config, indent=2)

        return results

    def generate_mcp_config(self) -> dict[str, Any]:
        """Generate MCP server configuration from agents that expose tools."""
        servers: dict[str, Any] = {}

        for info in self.registry.all_agents():
            tools = info.instance.as_mcp_tools()
            if tools:
                server_name = f"ai-orchestrator-{info.name}"
                servers[server_name] = {
                    "command": "python",
                    "args": [
                        "-m", "ai_orchestrator",
                        "--mcp-server", info.name,
                    ],
                    "tools": tools,
                    "metadata": {
                        "agent": info.name,
                        "capabilities": info.capabilities,
                        "priority": info.priority,
                    },
                }

        return {"mcpServers": servers}

    def generate_claude_settings(self) -> dict[str, Any]:
        """Generate Claude Code settings.json."""
        mcp_servers: dict[str, Any] = {}

        for info in self.registry.all_agents():
            tools = info.instance.as_mcp_tools()
            if tools:
                mcp_servers[f"orchestrator-{info.name}"] = {
                    "command": "python",
                    "args": ["-m", "ai_orchestrator", "--mcp-server", info.name],
                    "env": {},
                }

        # Build hooks based on agent capabilities
        hooks: dict[str, list[dict]] = {}

        # Pre-commit hook: run security and test agents
        security_agents = self.registry.find_by_capability("security")
        test_agents = self.registry.find_by_capability("test")
        if security_agents or test_agents:
            hook_agents = []
            if security_agents:
                hook_agents.append(security_agents[0].name)
            if test_agents:
                hook_agents.append(test_agents[0].name)
            hooks["PreCommit"] = [{
                "command": f"python -m ai_orchestrator --run-agents {','.join(hook_agents)}",
                "description": "Run security audit and tests before commit",
            }]

        return {
            "mcpServers": mcp_servers,
            "hooks": hooks,
            "permissions": {
                "allow": [
                    "python -m ai_orchestrator*",
                ],
            },
        }

    def generate_claude_md(self) -> str:
        """Generate CLAUDE.md content from agent registry."""
        lines = [
            "# AI Agent Orchestrator",
            "",
            "이 프로젝트는 20개 전문 에이전트가 협력하는 동적 AI 자동화 프레임워크입니다.",
            "",
            "## Available Agents",
            "",
        ]

        for info in self.registry.all_agents():
            caps = ", ".join(info.capabilities[:5])
            lines.append(f"- **{info.name}** (priority: {info.priority}): {caps}")

        lines.extend([
            "",
            "## Usage",
            "",
            "```bash",
            "# Run with a task",
            'python -m ai_orchestrator --task "analyze security"',
            "",
            "# List all agents",
            "python -m ai_orchestrator --list-agents",
            "",
            "# Generate configs",
            "python -m ai_orchestrator --generate-config",
            "",
            "# Run as MCP server",
            "python -m ai_orchestrator --mcp-server <agent_name>",
            "```",
            "",
            "## Architecture",
            "",
            "- **Core Engine**: Routes tasks to appropriate agents via capability matching",
            "- **Event Bus**: Async pub/sub for decoupled agent communication",
            "- **Registry**: Dynamic agent discovery and health tracking",
            "- **Router**: Scores agents and generates dependency-aware execution plans",
            "- **MCP Bridge**: Exposes agents as MCP-compatible tool servers",
            "",
        ])

        return "\n".join(lines)

    def generate_hooks_config(self) -> dict[str, Any]:
        """Generate Claude Code hooks configuration."""
        hooks: list[dict[str, Any]] = []

        # Auto-analyze on file save
        code_analyzers = self.registry.find_by_capability("code_analysis")
        if code_analyzers:
            hooks.append({
                "event": "on_file_save",
                "pattern": "*.py",
                "command": f"python -m ai_orchestrator --run-agents {code_analyzers[0].name}",
                "description": "Auto-analyze code on save",
            })

        # Pre-push hook
        test_agents = self.registry.find_by_capability("test")
        security_agents = self.registry.find_by_capability("security")
        if test_agents or security_agents:
            agents_to_run = []
            if test_agents:
                agents_to_run.append(test_agents[0].name)
            if security_agents:
                agents_to_run.append(security_agents[0].name)
            hooks.append({
                "event": "pre_push",
                "command": f"python -m ai_orchestrator --run-agents {','.join(agents_to_run)}",
                "description": "Run tests and security audit before push",
            })

        return {"hooks": hooks}
