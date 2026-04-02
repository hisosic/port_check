"""CLI entry point for AI Agent Orchestrator.

Usage:
    python -m ai_orchestrator --task "analyze security"
    python -m ai_orchestrator --list-agents
    python -m ai_orchestrator --generate-config
    python -m ai_orchestrator --run-agents security_auditor,code_analyzer
    python -m ai_orchestrator --mcp-server context_engine
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-orchestrator",
        description="AI Agent Orchestrator - 20개 전문 에이전트 동적 자동화 프레임워크",
    )
    parser.add_argument(
        "--task", "-t",
        help="Task to execute (natural language)",
    )
    parser.add_argument(
        "--list-agents", "-l",
        action="store_true",
        help="List all available agents",
    )
    parser.add_argument(
        "--generate-config", "-g",
        action="store_true",
        help="Generate MCP configs, settings.json, and CLAUDE.md",
    )
    parser.add_argument(
        "--run-agents", "-r",
        help="Run specific agents (comma-separated names)",
    )
    parser.add_argument(
        "--mcp-server",
        help="Start as MCP server for a specific agent",
    )
    parser.add_argument(
        "--working-dir", "-w",
        default=os.getcwd(),
        help="Working directory (default: current)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--json-output", "-j",
        action="store_true",
        help="Output results as JSON",
    )
    return parser


async def cmd_list_agents(orchestrator: Any, json_output: bool) -> None:
    """List all registered agents."""
    await orchestrator.initialize()
    agents = orchestrator.list_agents()

    if json_output:
        print(json.dumps(agents, indent=2))
        return

    print(f"\n{'=' * 70}")
    print(f" AI Agent Orchestrator - {len(agents)} Specialized Agents")
    print(f"{'=' * 70}\n")
    print(f"{'Name':<28} {'Priority':>8}  {'Capabilities'}")
    print(f"{'-' * 28} {'-' * 8}  {'-' * 30}")

    for agent in sorted(agents, key=lambda a: a["priority"], reverse=True):
        caps = ", ".join(agent["capabilities"][:4])
        health = "✓" if agent["healthy"] else "✗"
        print(f"{agent['name']:<28} {agent['priority']:>8}  {caps}")

    print(f"\nTotal: {len(agents)} agents registered")


async def cmd_execute_task(
    orchestrator: Any, task: str, json_output: bool
) -> None:
    """Execute a task through the agent pipeline."""
    await orchestrator.initialize()

    print(f"\n▶ Executing: {task}\n")

    context = await orchestrator.execute(task)

    if json_output:
        output = {
            "task": task,
            "context_summary": context.summary(),
            "results": {
                name: {
                    "success": r.success,
                    "data": r.data,
                    "errors": r.errors,
                    "duration_ms": r.duration_ms,
                }
                for name, r in context.results.items()
            },
        }
        print(json.dumps(output, indent=2, default=str))
        return

    print(f"{'=' * 60}")
    print(f" Execution Results")
    print(f"{'=' * 60}\n")

    for name, result in context.results.items():
        status = "✓ SUCCESS" if result.success else "✗ FAILED"
        print(f"  [{status}] {name} ({result.duration_ms:.0f}ms)")
        if result.data:
            for key, value in result.data.items():
                if isinstance(value, (int, float, str, bool)):
                    print(f"           {key}: {value}")
        if result.errors:
            for err in result.errors:
                print(f"           ERROR: {err}")
        print()

    summary = context.summary()
    print(f"{'─' * 60}")
    print(f"  Completed: {len(context.results)} agents")
    print(f"  Language: {summary['primary_language']}")
    print(f"  Framework: {summary['framework']}")
    print()


async def cmd_run_agents(
    orchestrator: Any, agent_names: str, json_output: bool
) -> None:
    """Run specific agents."""
    from ai_orchestrator.core.context import Context

    await orchestrator.initialize()

    names = [n.strip() for n in agent_names.split(",")]
    context = Context(working_dir=orchestrator.working_dir)

    for name in names:
        print(f"  Running: {name}...")
        result = await orchestrator.execute_single(name, context)
        status = "✓" if result.success else "✗"
        print(f"  [{status}] {name} ({result.duration_ms:.0f}ms)")

    if json_output:
        print(json.dumps({
            name: {"success": r.success, "data": r.data}
            for name, r in context.results.items()
        }, indent=2, default=str))


async def cmd_generate_config(orchestrator: Any, working_dir: str) -> None:
    """Generate all configuration files."""
    await orchestrator.initialize()

    from ai_orchestrator.core.context import Context
    from ai_orchestrator.settings.claude_md import write_claude_md
    from ai_orchestrator.settings.claude_settings import write_settings

    # Run context engine first to populate project info
    context = Context(working_dir=working_dir)
    await orchestrator.execute_single("context_engine", context)

    # Generate settings.json
    settings_path = write_settings(orchestrator.registry, working_dir)
    print(f"  ✓ Generated: {settings_path}")

    # Generate CLAUDE.md
    claude_md_path = write_claude_md(orchestrator.registry, working_dir, context)
    print(f"  ✓ Generated: {claude_md_path}")

    # Generate MCP config
    configs = await orchestrator.generate_configs()
    mcp_path = os.path.join(working_dir, "mcp_servers.json")
    with open(mcp_path, "w") as f:
        f.write(configs["mcp_servers.json"])
    print(f"  ✓ Generated: {mcp_path}")

    print(f"\n  All configurations generated successfully!")


async def cmd_mcp_server(agent_name: str, working_dir: str) -> None:
    """Start an MCP server for a specific agent."""
    from ai_orchestrator.mcp.server_template import serve_agent_as_mcp
    await serve_agent_as_mcp(agent_name, working_dir)


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.mcp_server:
        await cmd_mcp_server(args.mcp_server, args.working_dir)
        return

    from ai_orchestrator.core.engine import Orchestrator
    orchestrator = Orchestrator(working_dir=args.working_dir)

    if args.list_agents:
        await cmd_list_agents(orchestrator, args.json_output)
    elif args.generate_config:
        await cmd_generate_config(orchestrator, args.working_dir)
    elif args.run_agents:
        await cmd_run_agents(orchestrator, args.run_agents, args.json_output)
    elif args.task:
        await cmd_execute_task(orchestrator, args.task, args.json_output)
    else:
        # Default: show agents and run basic analysis
        await cmd_list_agents(orchestrator, args.json_output)
        print("\nTip: Use --task to execute a task, or --help for all options")


def entry_point() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    entry_point()
