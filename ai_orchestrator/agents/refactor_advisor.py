"""Refactor Advisor - Suggests refactoring opportunities."""

from __future__ import annotations

import re
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context


class RefactorAdvisorAgent(BaseAgent):
    name = "refactor_advisor"
    capabilities = ["refactor", "restructure", "simplify", "extract", "dedup", "improve"]
    input_types = ["code_structure", "code_issues", "review_findings"]
    output_types = ["refactor_suggestions"]
    priority = 60

    async def execute(self, context: Context) -> AgentResult:
        code_structure = await context.get("code_structure", {})
        code_issues = await context.get("code_issues", [])
        review_findings = await context.get("review_findings", [])
        suggestions: list[dict[str, Any]] = []

        # Extract Method opportunities
        for func in code_structure.get("functions", []):
            if func.get("length", 0) > 30:
                suggestions.append({
                    "type": "extract_method",
                    "target": func["name"],
                    "file": func["file"],
                    "line": func["line"],
                    "reason": f"Function is {func['length']} lines - extract sub-functions",
                    "priority": "high" if func["length"] > 80 else "medium",
                })

        # Detect potential duplication
        functions = code_structure.get("functions", [])
        seen_signatures: dict[str, list] = {}
        for func in functions:
            key = f"{func.get('args', 0)}_{func.get('length', 0)}"
            seen_signatures.setdefault(key, []).append(func)

        for key, funcs in seen_signatures.items():
            if len(funcs) > 2:
                names = [f["name"] for f in funcs[:5]]
                suggestions.append({
                    "type": "deduplication",
                    "target": ", ".join(names),
                    "reason": f"Functions with similar signatures may have duplicated logic",
                    "priority": "medium",
                })

        # Consolidate from code issues
        for issue in code_issues:
            if issue.get("type") == "complexity":
                suggestions.append({
                    "type": "simplify",
                    "target": issue.get("file", ""),
                    "line": issue.get("line", 0),
                    "reason": issue.get("message", ""),
                    "priority": "medium",
                })

        # Consolidate from review findings
        complexity_files: dict[str, int] = {}
        for finding in review_findings:
            if finding.get("type") == "complexity":
                f = finding.get("file", "")
                complexity_files[f] = complexity_files.get(f, 0) + 1

        for f, count in complexity_files.items():
            if count > 3:
                suggestions.append({
                    "type": "file_restructure",
                    "target": f,
                    "reason": f"File has {count} complexity issues - consider restructuring",
                    "priority": "high",
                })

        await context.set("refactor_suggestions", suggestions)

        await self.emit("refactor.suggested", {
            "suggestion_count": len(suggestions),
        })

        return self._success(
            total_suggestions=len(suggestions),
            by_type={
                t: len([s for s in suggestions if s["type"] == t])
                for t in set(s["type"] for s in suggestions)
            } if suggestions else {},
        )
