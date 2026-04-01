"""Performance Optimizer - Identifies performance issues and optimization opportunities."""

from __future__ import annotations

import re
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, Language

PERF_PATTERNS: dict[str, list[tuple[str, str, str]]] = {
    "python": [
        (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(', "Use enumerate() instead of range(len())", "efficiency"),
        (r'\.append\s*\(.*\)\s*$.*for\s', "Consider list comprehension instead of append in loop", "efficiency"),
        (r'time\.sleep\s*\(\s*\d+\s*\)', "Blocking sleep detected - consider async", "concurrency"),
        (r'import\s+json.*json\.loads.*for\s', "JSON parsing in loop - parse once outside", "io"),
        (r'open\s*\(.*\)(?!.*with\b)', "File opened without context manager (with statement)", "resource"),
        (r'except\s*:\s*$', "Bare except clause - catches all exceptions silently", "error_handling"),
        (r'\+\s*=\s*.*\bstr\b|\bstr\s*\(.*\)\s*\+', "String concatenation in loop - use join()", "memory"),
        (r'global\s+\w+', "Global variable usage - consider encapsulation", "design"),
    ],
    "bash": [
        (r'cat\s+\w+\s*\|\s*grep', "Useless use of cat - pipe directly to grep", "efficiency"),
        (r'for\s+\w+\s+in\s+\$\(cat\s', "Reading file in for loop - use while read", "efficiency"),
        (r'ls\s+\|\s*grep', "Parsing ls output - use glob or find instead", "reliability"),
        (r'\$\(.*\$\(.*\)\.*\)', "Nested command substitution - consider simplifying", "readability"),
    ],
    "javascript": [
        (r'document\.querySelector.*for\s*\(', "DOM query in loop - cache the selector", "dom"),
        (r'JSON\.parse.*JSON\.stringify', "Parse-stringify cycle - may indicate deep clone need", "efficiency"),
        (r'await\s+.*\bfor\s', "Sequential await in loop - consider Promise.all()", "concurrency"),
        (r'\.forEach\s*\(.*async', "Async in forEach - use for...of or Promise.all()", "concurrency"),
    ],
}


class PerformanceOptimizerAgent(BaseAgent):
    name = "performance_optimizer"
    capabilities = ["performance", "optimization", "profiling", "speed", "efficiency", "benchmark"]
    input_types = ["project_info", "file_list", "code_structure"]
    output_types = ["perf_issues", "optimization_suggestions"]
    priority = 70

    async def execute(self, context: Context) -> AgentResult:
        issues: list[dict[str, Any]] = []
        suggestions: list[dict[str, str]] = []

        for file_info in context.files:
            lang = file_info.language.value
            patterns = PERF_PATTERNS.get(lang, [])
            if not patterns:
                continue

            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            for pattern, desc, category in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    line_num = content[:match.start()].count("\n") + 1
                    issues.append({
                        "file": file_info.path,
                        "line": line_num,
                        "pattern": desc,
                        "category": category,
                        "language": lang,
                    })

        # Analyze code structure for complexity issues
        code_structure = await context.get("code_structure")
        if code_structure:
            for func in code_structure.get("functions", []):
                if func.get("length", 0) > 100:
                    suggestions.append({
                        "type": "complexity",
                        "target": f"{func['name']} in {func['file']}",
                        "suggestion": f"Function is {func['length']} lines - consider splitting",
                    })
                if func.get("args", 0) > 6:
                    suggestions.append({
                        "type": "design",
                        "target": f"{func['name']} in {func['file']}",
                        "suggestion": f"Function has {func['args']} parameters - consider parameter object",
                    })

        await context.set("perf_issues", issues)
        await context.set("optimization_suggestions", suggestions)

        await self.emit("performance.analyzed", {
            "issue_count": len(issues),
            "suggestion_count": len(suggestions),
        })

        return self._success(
            issues_found=len(issues),
            suggestions=len(suggestions),
            by_category=self._group_by_category(issues),
        )

    def _group_by_category(self, issues: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for issue in issues:
            cat = issue.get("category", "other")
            counts[cat] = counts.get(cat, 0) + 1
        return counts
