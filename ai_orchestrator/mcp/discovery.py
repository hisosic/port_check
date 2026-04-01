"""MCP server discovery - finds available MCP servers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ai_orchestrator.mcp.protocol import MCPServerInfo, MCPToolSchema


def discover_mcp_servers(
    working_dir: str, scan_home: bool = True
) -> list[MCPServerInfo]:
    """Discover all available MCP servers from configs and conventions."""
    servers: list[MCPServerInfo] = []

    # 1. Check project-level configs
    project_configs = [
        Path(working_dir) / ".claude" / "settings.json",
        Path(working_dir) / ".mcp" / "config.json",
        Path(working_dir) / "mcp.json",
    ]
    for config_path in project_configs:
        servers.extend(_parse_config_file(config_path))

    # 2. Check user-level configs
    if scan_home:
        home = Path.home()
        user_configs = [
            home / ".config" / "claude" / "settings.json",
            home / ".claude" / "settings.json",
            home / ".claude.json",
        ]
        for config_path in user_configs:
            servers.extend(_parse_config_file(config_path))

    # 3. Check for well-known MCP server executables
    servers.extend(_discover_executables())

    # Deduplicate by name
    seen: set[str] = set()
    unique: list[MCPServerInfo] = []
    for server in servers:
        if server.name not in seen:
            seen.add(server.name)
            unique.append(server)

    return unique


def _parse_config_file(config_path: Path) -> list[MCPServerInfo]:
    """Parse an MCP config file and return server info."""
    if not config_path.exists():
        return []

    try:
        with open(config_path) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    servers: list[MCPServerInfo] = []
    mcp_section = config.get("mcpServers", {})

    for name, server_config in mcp_section.items():
        server = MCPServerInfo(
            name=name,
            command=server_config.get("command", ""),
            args=server_config.get("args", []),
            env=server_config.get("env", {}),
        )
        servers.append(server)

    return servers


def _discover_executables() -> list[MCPServerInfo]:
    """Check PATH for known MCP server executables."""
    known_executables = [
        ("mcp-server-filesystem", "Filesystem MCP server"),
        ("mcp-server-github", "GitHub MCP server"),
        ("mcp-server-memory", "Memory MCP server"),
        ("mcp-server-postgres", "PostgreSQL MCP server"),
        ("mcp-server-slack", "Slack MCP server"),
    ]

    servers: list[MCPServerInfo] = []
    for exe_name, description in known_executables:
        if _which(exe_name):
            servers.append(MCPServerInfo(
                name=exe_name,
                command=exe_name,
            ))

    return servers


def _which(name: str) -> str | None:
    """Simple which() implementation."""
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(path_dir, name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None


def generate_mcp_config(
    servers: list[MCPServerInfo],
    additional_servers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a complete MCP configuration."""
    config: dict[str, Any] = {"mcpServers": {}}

    for server in servers:
        config["mcpServers"][server.name] = server.to_config()

    if additional_servers:
        config["mcpServers"].update(additional_servers)

    return config
