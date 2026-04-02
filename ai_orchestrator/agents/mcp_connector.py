"""MCP Connector - Auto-discovers and connects MCP servers.

Scans for existing MCP configurations, probes for servers,
and registers discovered tools in the context.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

# Well-known MCP config locations
MCP_CONFIG_PATHS = [
    "~/.config/claude/settings.json",
    "~/.claude/settings.json",
    ".claude/settings.json",
    ".mcp/config.json",
    "mcp.json",
    ".cursor/mcp.json",
]

# Common MCP server packages
KNOWN_MCP_SERVERS: dict[str, dict[str, Any]] = {
    "@anthropic-ai/claude-code": {
        "type": "claude_code",
        "description": "Claude Code CLI integration",
    },
    "@modelcontextprotocol/server-filesystem": {
        "type": "filesystem",
        "description": "File system access MCP server",
    },
    "@modelcontextprotocol/server-github": {
        "type": "github",
        "description": "GitHub API MCP server",
    },
    "@modelcontextprotocol/server-slack": {
        "type": "slack",
        "description": "Slack integration MCP server",
    },
    "@modelcontextprotocol/server-memory": {
        "type": "memory",
        "description": "Persistent memory MCP server",
    },
    "@modelcontextprotocol/server-puppeteer": {
        "type": "puppeteer",
        "description": "Browser automation MCP server",
    },
    "@modelcontextprotocol/server-postgres": {
        "type": "postgres",
        "description": "PostgreSQL MCP server",
    },
}


class MCPConnectorAgent(BaseAgent):
    name = "mcp_connector"
    capabilities = ["mcp", "server_discovery", "tool_discovery", "integration", "connect"]
    input_types = ["project_info"]
    output_types = ["mcp_servers", "mcp_tools", "mcp_config"]
    priority = 80

    async def execute(self, context: Context) -> AgentResult:
        discovered_servers: list[dict[str, Any]] = []
        discovered_tools: list[dict[str, Any]] = []

        # 1. Scan existing MCP configurations
        config_servers = self._scan_configs(context.working_dir)
        discovered_servers.extend(config_servers)

        # 2. Detect MCP server packages in project dependencies
        dep_servers = self._scan_dependencies(context.working_dir)
        discovered_servers.extend(dep_servers)

        # 3. Scan for framework-specific MCP opportunities
        framework_suggestions = self._suggest_mcp_servers(context)

        # 4. Generate recommended MCP configuration
        recommended_config = self._generate_config(
            discovered_servers, framework_suggestions
        )

        await context.set("mcp_servers", discovered_servers)
        await context.set("mcp_tools", discovered_tools)
        await context.set("mcp_config", recommended_config)

        await self.emit("mcp.discovered", {
            "server_count": len(discovered_servers),
            "suggestions": len(framework_suggestions),
        })

        return self._success(
            discovered_servers=len(discovered_servers),
            existing_configs=[s["source"] for s in config_servers],
            suggestions=framework_suggestions,
            recommended_config=recommended_config,
        )

    def _scan_configs(self, working_dir: str) -> list[dict[str, Any]]:
        """Scan well-known locations for existing MCP configs."""
        servers = []
        for config_path in MCP_CONFIG_PATHS:
            full_path = Path(os.path.expanduser(config_path))
            if not full_path.is_absolute():
                full_path = Path(working_dir) / config_path

            if full_path.exists():
                try:
                    with open(full_path) as f:
                        config = json.load(f)
                    mcp_servers = config.get("mcpServers", {})
                    for name, server_config in mcp_servers.items():
                        servers.append({
                            "name": name,
                            "source": str(full_path),
                            "config": server_config,
                            "type": "existing",
                        })
                except (json.JSONDecodeError, OSError):
                    pass
        return servers

    def _scan_dependencies(self, working_dir: str) -> list[dict[str, Any]]:
        """Check project dependencies for known MCP server packages."""
        servers = []
        pkg_json = Path(working_dir) / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    pkg = json.load(f)
                all_deps = {}
                all_deps.update(pkg.get("dependencies", {}))
                all_deps.update(pkg.get("devDependencies", {}))

                for dep_name in all_deps:
                    if dep_name in KNOWN_MCP_SERVERS:
                        info = KNOWN_MCP_SERVERS[dep_name]
                        servers.append({
                            "name": dep_name,
                            "source": "package.json",
                            "type": info["type"],
                            "description": info["description"],
                        })
            except (json.JSONDecodeError, OSError):
                pass
        return servers

    def _suggest_mcp_servers(self, context: Context) -> list[dict[str, str]]:
        """Suggest MCP servers based on project context."""
        suggestions = []
        framework = context.framework.lower() if context.framework else ""

        # Always suggest filesystem server
        suggestions.append({
            "server": "filesystem",
            "reason": "Basic file system access for AI tools",
            "package": "@modelcontextprotocol/server-filesystem",
        })

        if context.git.is_repo:
            suggestions.append({
                "server": "github",
                "reason": "GitHub integration for repository management",
                "package": "@modelcontextprotocol/server-github",
            })

        if "docker" in framework:
            suggestions.append({
                "server": "docker",
                "reason": "Docker container management",
                "package": "mcp-server-docker",
            })

        if any(lang.value in ("python", "javascript", "typescript")
               for lang in context.languages):
            suggestions.append({
                "server": "memory",
                "reason": "Persistent memory for cross-session context",
                "package": "@modelcontextprotocol/server-memory",
            })

        return suggestions

    def _generate_config(
        self,
        discovered: list[dict],
        suggestions: list[dict],
    ) -> dict[str, Any]:
        """Generate a recommended MCP configuration."""
        servers: dict[str, Any] = {}

        # Include discovered servers
        for server in discovered:
            if "config" in server:
                servers[server["name"]] = server["config"]

        # Add orchestrator's own agents as MCP servers
        if self.registry:
            for info in self.registry.all_agents():
                tools = info.instance.as_mcp_tools()
                if tools:
                    servers[f"orchestrator-{info.name}"] = {
                        "command": "python",
                        "args": ["-m", "ai_orchestrator", "--mcp-server", info.name],
                    }

        return {"mcpServers": servers}

    def as_mcp_tools(self) -> list[dict]:
        return [
            {
                "name": "discover_mcp_servers",
                "description": "Scan for available MCP servers and suggest new ones",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "generate_mcp_config",
                "description": "Generate optimized MCP server configuration",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
