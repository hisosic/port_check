"""Code Analyzer - Static code analysis agent.

Analyzes code structure, complexity, and patterns.
Many other agents depend on its output.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, Language


class CodeAnalyzerAgent(BaseAgent):
    name = "code_analyzer"
    capabilities = ["code_analysis", "static_analysis", "ast", "complexity", "structure", "inspect"]
    input_types = ["project_info", "file_list"]
    output_types = ["code_structure", "code_issues", "complexity_report"]
    priority = 85

    async def execute(self, context: Context) -> AgentResult:
        files = context.files
        if not files:
            return self._failure("No files to analyze")

        structure: dict[str, Any] = {
            "classes": [],
            "functions": [],
            "imports": [],
            "total_lines": 0,
            "files_analyzed": 0,
        }
        issues: list[dict[str, str]] = []

        for file_info in files:
            if file_info.language == Language.PYTHON:
                self._analyze_python(file_info.path, structure, issues)
            elif file_info.language == Language.BASH:
                self._analyze_bash(file_info.path, structure, issues)
            elif file_info.language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
                self._analyze_js(file_info.path, structure, issues)

        # Calculate complexity metrics
        complexity = {
            "total_classes": len(structure["classes"]),
            "total_functions": len(structure["functions"]),
            "total_lines": structure["total_lines"],
            "avg_function_length": (
                structure["total_lines"] / max(len(structure["functions"]), 1)
            ),
            "issue_count": len(issues),
        }

        await context.set("code_structure", structure)
        await context.set("code_issues", issues)
        await context.set("complexity_report", complexity)

        await self.emit("code.analyzed", {
            "files_analyzed": structure["files_analyzed"],
            "issue_count": len(issues),
        })

        return self._success(
            files_analyzed=structure["files_analyzed"],
            total_lines=structure["total_lines"],
            classes=len(structure["classes"]),
            functions=len(structure["functions"]),
            issues=len(issues),
        )

    def _analyze_python(
        self, filepath: str, structure: dict, issues: list,
    ) -> None:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            lines = source.count("\n") + 1
            structure["total_lines"] += lines
            structure["files_analyzed"] += 1

            tree = ast.parse(source, filename=filepath)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [
                        n.name for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    structure["classes"].append({
                        "name": node.name,
                        "file": filepath,
                        "line": node.lineno,
                        "methods": methods,
                    })
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body_lines = (node.end_lineno or node.lineno) - node.lineno
                    structure["functions"].append({
                        "name": node.name,
                        "file": filepath,
                        "line": node.lineno,
                        "length": body_lines,
                        "args": len(node.args.args),
                    })
                    if body_lines > 50:
                        issues.append({
                            "type": "complexity",
                            "file": filepath,
                            "line": str(node.lineno),
                            "message": f"Function '{node.name}' is {body_lines} lines long (>50)",
                        })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = ""
                    if isinstance(node, ast.ImportFrom) and node.module:
                        module = node.module
                    elif isinstance(node, ast.Import):
                        module = ", ".join(a.name for a in node.names)
                    structure["imports"].append({
                        "module": module,
                        "file": filepath,
                    })

        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "file": filepath,
                "line": str(e.lineno or 0),
                "message": str(e),
            })
        except Exception:
            pass

    def _analyze_bash(
        self, filepath: str, structure: dict, issues: list,
    ) -> None:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            lines = source.count("\n") + 1
            structure["total_lines"] += lines
            structure["files_analyzed"] += 1

            # Detect functions
            for match in re.finditer(r'^(\w+)\s*\(\)\s*\{', source, re.MULTILINE):
                structure["functions"].append({
                    "name": match.group(1),
                    "file": filepath,
                    "line": source[:match.start()].count("\n") + 1,
                    "length": 0,
                    "args": 0,
                })

            # Check for common issues
            if "eval " in source:
                issues.append({
                    "type": "security",
                    "file": filepath,
                    "line": "0",
                    "message": "Use of 'eval' detected - potential security risk",
                })

            if not source.startswith("#!"):
                issues.append({
                    "type": "convention",
                    "file": filepath,
                    "line": "1",
                    "message": "Missing shebang line",
                })

        except Exception:
            pass

    def _analyze_js(
        self, filepath: str, structure: dict, issues: list,
    ) -> None:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            lines = source.count("\n") + 1
            structure["total_lines"] += lines
            structure["files_analyzed"] += 1

            # Simple regex-based JS analysis
            for match in re.finditer(
                r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>)',
                source,
            ):
                name = match.group(1) or match.group(2)
                if name:
                    structure["functions"].append({
                        "name": name,
                        "file": filepath,
                        "line": source[:match.start()].count("\n") + 1,
                        "length": 0,
                        "args": 0,
                    })

            for match in re.finditer(r'class\s+(\w+)', source):
                structure["classes"].append({
                    "name": match.group(1),
                    "file": filepath,
                    "line": source[:match.start()].count("\n") + 1,
                    "methods": [],
                })

        except Exception:
            pass

    def as_mcp_tools(self) -> list[dict]:
        return [{
            "name": "analyze_code",
            "description": "Perform static analysis on code files",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "File or directory to analyze"},
                },
            },
        }]
