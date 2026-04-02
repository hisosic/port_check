"""Claude Code settings.json generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_orchestrator.core.registry import Registry


def generate_settings(
    registry: Registry,
    working_dir: str = ".",
    include_hooks: bool = True,
) -> dict[str, Any]:
    """Generate a complete Claude Code settings.json."""
    settings: dict[str, Any] = {}

    # MCP Servers
    mcp_servers: dict[str, Any] = {}
    for info in registry.all_agents():
        tools = info.instance.as_mcp_tools()
        if tools:
            mcp_servers[f"orchestrator-{info.name}"] = {
                "command": "python",
                "args": ["-m", "ai_orchestrator", "--mcp-server", info.name],
                "env": {},
            }

    settings["mcpServers"] = mcp_servers

    # Hooks
    if include_hooks:
        settings["hooks"] = _generate_hooks(registry)

    # Permissions
    settings["permissions"] = {
        "allow": [
            "python -m ai_orchestrator*",
        ],
    }

    return settings


def _generate_hooks(registry: Registry) -> dict[str, list[dict]]:
    """Generate hook configurations based on available agents."""
    hooks: dict[str, list[dict]] = {}

    # Pre-commit: security + tests
    pre_commit_agents = []
    for cap in ["security", "test"]:
        agents = registry.find_by_capability(cap)
        if agents:
            pre_commit_agents.append(agents[0].name)

    if pre_commit_agents:
        hooks["PreCommit"] = [{
            "command": f"python -m ai_orchestrator --run-agents {','.join(pre_commit_agents)}",
            "description": "Auto-audit before commit",
        }]

    return hooks


def write_settings(
    registry: Registry,
    output_dir: str = ".",
    include_hooks: bool = True,
) -> str:
    """Generate and write settings.json."""
    settings = generate_settings(registry, output_dir, include_hooks)
    output_path = Path(output_dir) / ".claude" / "settings.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return str(output_path)
