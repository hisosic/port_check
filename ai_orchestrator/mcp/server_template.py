"""MCP server template - wraps any agent as an MCP-compatible server."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import TYPE_CHECKING, Any

from ai_orchestrator.core.context import Context
from ai_orchestrator.mcp.protocol import MCPMessageHandler

if TYPE_CHECKING:
    from ai_orchestrator.agents.base import BaseAgent


class AgentMCPServer:
    """Wraps a BaseAgent as an MCP server communicating over stdio."""

    def __init__(self, agent: BaseAgent, working_dir: str = ".") -> None:
        self.agent = agent
        self.working_dir = working_dir
        self.tools = agent.as_mcp_tools()
        self.handler = MCPMessageHandler(
            server_name=f"ai-orchestrator-{agent.name}",
            tools=self.tools,
        )

        # Register tool handlers
        for tool in self.tools:
            self.handler.register_tool_handler(
                tool["name"],
                self._make_tool_handler(tool["name"]),
            )

    def _make_tool_handler(self, tool_name: str) -> Any:
        """Create a handler function for a specific tool."""
        agent = self.agent
        working_dir = self.working_dir

        async def handler(arguments: dict[str, Any]) -> Any:
            context = Context(
                working_dir=arguments.get("working_dir", working_dir),
                task=arguments.get("task", tool_name),
            )
            result = await agent.execute(context)
            return {
                "success": result.success,
                "data": result.data,
                "errors": result.errors,
                "warnings": result.warnings,
            }

        return handler

    async def run_stdio(self) -> None:
        """Run the MCP server over stdio (stdin/stdout)."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin.buffer
        )

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                raw = line.decode("utf-8").strip()
                if not raw:
                    continue

                response = await self.handler.handle_message(raw)
                if response:
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()

            except Exception as e:
                error_response = json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": None,
                })
                sys.stdout.write(error_response + "\n")
                sys.stdout.flush()


async def serve_agent_as_mcp(
    agent_name: str, working_dir: str = "."
) -> None:
    """Start an MCP server for a specific agent."""
    from ai_orchestrator.core.engine import Orchestrator

    orchestrator = Orchestrator(working_dir=working_dir)
    await orchestrator.initialize()

    agent_info = orchestrator.registry.get(agent_name)
    if not agent_info:
        print(f"Error: Agent '{agent_name}' not found", file=sys.stderr)
        print(f"Available agents: {[a.name for a in orchestrator.registry.all_agents()]}", file=sys.stderr)
        sys.exit(1)

    server = AgentMCPServer(agent_info.instance, working_dir)
    await server.run_stdio()
