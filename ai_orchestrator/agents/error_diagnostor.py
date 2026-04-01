"""Error Diagnostor - Diagnoses errors and traces root causes."""

from __future__ import annotations

import re
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

# Common error patterns and their likely causes
ERROR_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"ModuleNotFoundError:\s+No module named '(\w+)'",
        "type": "missing_dependency",
        "suggestion": "Install the missing package: pip install {match}",
    },
    {
        "pattern": r"ImportError:\s+cannot import name '(\w+)'",
        "type": "import_error",
        "suggestion": "Check version compatibility or circular imports for {match}",
    },
    {
        "pattern": r"FileNotFoundError:.*'(.+)'",
        "type": "missing_file",
        "suggestion": "File not found: {match} - check path and permissions",
    },
    {
        "pattern": r"PermissionError:.*'(.+)'",
        "type": "permission",
        "suggestion": "Permission denied for {match} - check file permissions",
    },
    {
        "pattern": r"ConnectionRefusedError",
        "type": "connection",
        "suggestion": "Connection refused - check if the service is running",
    },
    {
        "pattern": r"TimeoutError|timed?\s*out",
        "type": "timeout",
        "suggestion": "Operation timed out - check network or increase timeout",
    },
    {
        "pattern": r"SyntaxError:.*line\s+(\d+)",
        "type": "syntax",
        "suggestion": "Syntax error at line {match} - check for typos",
    },
    {
        "pattern": r"TypeError:.*'(\w+)'.*'(\w+)'",
        "type": "type_mismatch",
        "suggestion": "Type mismatch between {match} - check argument types",
    },
    {
        "pattern": r"KeyError:\s+'(\w+)'",
        "type": "missing_key",
        "suggestion": "Missing key '{match}' - check dict/config contents",
    },
    {
        "pattern": r"ENOENT|no such file or directory",
        "type": "missing_file",
        "suggestion": "File or directory not found - check paths",
    },
    {
        "pattern": r"EACCES|permission denied",
        "type": "permission",
        "suggestion": "Permission denied - check file/directory permissions",
    },
    {
        "pattern": r"EADDRINUSE|address already in use",
        "type": "port_conflict",
        "suggestion": "Port already in use - check for other processes or change port",
    },
]


class ErrorDiagnostorAgent(BaseAgent):
    name = "error_diagnostor"
    capabilities = ["error", "bug", "diagnose", "traceback", "exception", "debug", "fix"]
    input_types = ["project_info", "code_structure"]
    output_types = ["error_diagnosis", "fix_suggestions"]
    priority = 80

    async def execute(self, context: Context) -> AgentResult:
        task = context.task
        diagnoses: list[dict[str, Any]] = []
        suggestions: list[dict[str, str]] = []

        # Analyze the task description for error patterns
        for pattern_info in ERROR_PATTERNS:
            match = re.search(pattern_info["pattern"], task, re.IGNORECASE)
            if match:
                matched_text = match.group(1) if match.lastindex else match.group(0)
                diagnoses.append({
                    "type": pattern_info["type"],
                    "matched": matched_text,
                    "pattern": pattern_info["pattern"],
                })
                suggestions.append({
                    "type": pattern_info["type"],
                    "suggestion": pattern_info["suggestion"].format(match=matched_text),
                })

        # Scan log files for errors
        log_errors = self._scan_logs(context)
        diagnoses.extend(log_errors)

        # Check code for common error-prone patterns
        code_issues = await context.get("code_issues", [])
        for issue in code_issues:
            if issue.get("type") == "syntax_error":
                diagnoses.append({
                    "type": "code_error",
                    "file": issue.get("file", ""),
                    "message": issue.get("message", ""),
                })

        await context.set("error_diagnosis", diagnoses)
        await context.set("fix_suggestions", suggestions)

        await self.emit("errors.diagnosed", {
            "diagnosis_count": len(diagnoses),
            "suggestion_count": len(suggestions),
        })

        return self._success(
            diagnoses=diagnoses,
            suggestions=suggestions,
            errors_found=len(diagnoses),
        )

    def _scan_logs(self, context: Context) -> list[dict[str, Any]]:
        """Scan for log files and extract error patterns."""
        errors = []
        log_extensions = {".log", ".err"}
        for f in context.files:
            if any(f.path.endswith(ext) for ext in log_extensions):
                try:
                    with open(f.path, "r", encoding="utf-8", errors="ignore") as fh:
                        for i, line in enumerate(fh, 1):
                            if re.search(r'(?i)\b(error|fatal|critical|exception)\b', line):
                                errors.append({
                                    "type": "log_error",
                                    "file": f.path,
                                    "line": i,
                                    "message": line.strip()[:200],
                                })
                            if len(errors) > 100:
                                break
                except (OSError, UnicodeDecodeError):
                    pass
        return errors

    def as_mcp_tools(self) -> list[dict]:
        return [{
            "name": "diagnose_error",
            "description": "Diagnose an error message and suggest fixes",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "error_message": {"type": "string", "description": "The error to diagnose"},
                },
                "required": ["error_message"],
            },
        }]
