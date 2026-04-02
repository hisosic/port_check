"""Data Flow Tracer - Traces how data moves through the application."""

from __future__ import annotations

import ast
import re
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, Language


class DataFlowTracerAgent(BaseAgent):
    name = "data_flow_tracer"
    capabilities = ["dataflow", "data_flow", "trace", "flow", "propagation", "mutation"]
    input_types = ["project_info", "code_structure", "file_list"]
    output_types = ["data_flows", "mutation_points", "flow_graph"]
    priority = 45

    async def execute(self, context: Context) -> AgentResult:
        flows: list[dict[str, Any]] = []
        mutations: list[dict[str, Any]] = []
        call_graph: dict[str, list[str]] = {}

        for file_info in context.files:
            if file_info.language == Language.PYTHON:
                file_flows, file_mutations, file_calls = self._trace_python(file_info.path)
                flows.extend(file_flows)
                mutations.extend(file_mutations)
                call_graph.update(file_calls)
            elif file_info.language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
                file_flows = self._trace_js(file_info.path)
                flows.extend(file_flows)

        await context.set("data_flows", flows)
        await context.set("mutation_points", mutations)
        await context.set("flow_graph", call_graph)

        await self.emit("dataflow.traced", {
            "flow_count": len(flows),
            "mutation_count": len(mutations),
        })

        return self._success(
            flows_detected=len(flows),
            mutation_points=len(mutations),
            call_graph_size=len(call_graph),
        )

    def _trace_python(self, filepath: str) -> tuple[list, list, dict]:
        flows: list[dict] = []
        mutations: list[dict] = []
        call_graph: dict[str, list[str]] = {}

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, OSError):
            return flows, mutations, call_graph

        for node in ast.walk(tree):
            # Track function calls (call graph)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                callee_names = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            callee_names.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            callee_names.append(child.func.attr)
                call_graph[f"{filepath}:{node.name}"] = callee_names

                # Track assignments (data mutations)
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Subscript):
                                mutations.append({
                                    "file": filepath,
                                    "function": node.name,
                                    "line": child.lineno,
                                    "type": "subscript_mutation",
                                })
                            elif isinstance(target, ast.Attribute):
                                mutations.append({
                                    "file": filepath,
                                    "function": node.name,
                                    "line": child.lineno,
                                    "type": "attribute_mutation",
                                })

            # Track global variable usage
            if isinstance(node, ast.Global):
                for name in node.names:
                    flows.append({
                        "file": filepath,
                        "line": node.lineno,
                        "type": "global_access",
                        "variable": name,
                    })

            # Track file I/O
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name in ("open", "read", "write", "readlines"):
                    flows.append({
                        "file": filepath,
                        "line": node.lineno,
                        "type": "file_io",
                        "operation": func_name,
                    })

        return flows, mutations, call_graph

    def _trace_js(self, filepath: str) -> list[dict]:
        flows: list[dict] = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return flows

        # Detect fetch/API calls
        for match in re.finditer(r'(?:fetch|axios|http)\s*[.(]', content):
            line_num = content[:match.start()].count("\n") + 1
            flows.append({
                "file": filepath,
                "line": line_num,
                "type": "api_call",
            })

        # Detect state mutations
        for match in re.finditer(r'(?:setState|dispatch|commit|\.push|\.splice)\s*\(', content):
            line_num = content[:match.start()].count("\n") + 1
            flows.append({
                "file": filepath,
                "line": line_num,
                "type": "state_mutation",
            })

        return flows
