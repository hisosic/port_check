"""MCP JSON-RPC protocol types and message handling."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MCPRequest:
    """JSON-RPC 2.0 request."""
    method: str
    params: dict[str, Any] = field(default_factory=dict)
    id: int | str = 1
    jsonrpc: str = "2.0"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> MCPRequest:
        parsed = json.loads(data)
        return cls(
            method=parsed["method"],
            params=parsed.get("params", {}),
            id=parsed.get("id", 1),
        )


@dataclass
class MCPResponse:
    """JSON-RPC 2.0 response."""
    result: Any = None
    error: dict[str, Any] | None = None
    id: int | str = 1
    jsonrpc: str = "2.0"

    def to_json(self) -> str:
        d: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return json.dumps(d)

    @classmethod
    def success(cls, result: Any, request_id: int | str = 1) -> MCPResponse:
        return cls(result=result, id=request_id)

    @classmethod
    def error(cls, code: int, message: str, request_id: int | str = 1) -> MCPResponse:
        return cls(error={"code": code, "message": message}, id=request_id)


@dataclass
class MCPToolSchema:
    """Schema for an MCP tool."""
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPServerInfo:
    """Information about a discovered MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    tools: list[MCPToolSchema] = field(default_factory=list)
    transport: str = "stdio"  # stdio or http
    url: str = ""

    def to_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "command": self.command,
            "args": self.args,
        }
        if self.env:
            config["env"] = self.env
        return config


class MCPMessageHandler:
    """Handles MCP protocol messages for a server."""

    def __init__(self, server_name: str, tools: list[dict[str, Any]]) -> None:
        self.server_name = server_name
        self.tools = tools
        self._tool_handlers: dict[str, Any] = {}

    def register_tool_handler(self, tool_name: str, handler: Any) -> None:
        self._tool_handlers[tool_name] = handler

    async def handle_message(self, raw_message: str) -> str:
        """Process an incoming MCP message and return response."""
        try:
            request = MCPRequest.from_json(raw_message)
        except (json.JSONDecodeError, KeyError) as e:
            return MCPResponse.error(-32700, f"Parse error: {e}").to_json()

        if request.method == "initialize":
            return MCPResponse.success({
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": self.server_name,
                    "version": "1.0.0",
                },
            }, request.id).to_json()

        elif request.method == "tools/list":
            return MCPResponse.success({
                "tools": self.tools,
            }, request.id).to_json()

        elif request.method == "tools/call":
            tool_name = request.params.get("name", "")
            arguments = request.params.get("arguments", {})
            handler = self._tool_handlers.get(tool_name)
            if not handler:
                return MCPResponse.error(
                    -32601, f"Tool not found: {tool_name}", request.id
                ).to_json()
            try:
                result = await handler(arguments)
                return MCPResponse.success({
                    "content": [{"type": "text", "text": json.dumps(result)}],
                }, request.id).to_json()
            except Exception as e:
                return MCPResponse.error(
                    -32000, f"Tool execution error: {e}", request.id
                ).to_json()

        elif request.method == "notifications/initialized":
            return ""  # No response for notifications

        else:
            return MCPResponse.error(
                -32601, f"Method not found: {request.method}", request.id
            ).to_json()
