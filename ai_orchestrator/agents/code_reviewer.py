"""Code Reviewer - Automated code review for quality and conventions."""

from __future__ import annotations

import re
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, Language

NAMING_RULES: dict[str, dict[str, str]] = {
    "python": {
        "class": r'^[A-Z][a-zA-Z0-9]+$',  # PascalCase
        "function": r'^[a-z_][a-z0-9_]*$',  # snake_case
    },
    "javascript": {
        "class": r'^[A-Z][a-zA-Z0-9]+$',
        "function": r'^[a-z][a-zA-Z0-9]*$',  # camelCase
    },
}


class CodeReviewerAgent(BaseAgent):
    name = "code_reviewer"
    capabilities = ["review", "quality", "convention", "lint", "style", "clean"]
    input_types = ["project_info", "code_structure", "code_issues"]
    output_types = ["review_findings", "quality_score"]
    priority = 70

    async def execute(self, context: Context) -> AgentResult:
        code_structure = await context.get("code_structure", {})
        findings: list[dict[str, Any]] = []
        quality_metrics: dict[str, Any] = {}

        lang = context.primary_language.value

        # Naming convention checks
        naming_findings = self._check_naming(code_structure, lang)
        findings.extend(naming_findings)

        # Complexity checks
        complexity_findings = self._check_complexity(code_structure)
        findings.extend(complexity_findings)

        # Code smell checks
        smell_findings = self._check_code_smells(context)
        findings.extend(smell_findings)

        # Calculate quality score (0-100)
        total_items = max(
            len(code_structure.get("functions", [])) + len(code_structure.get("classes", [])),
            1,
        )
        issue_penalty = min(len(findings) * 5, 70)
        quality_score = max(100 - issue_penalty, 10)

        quality_metrics = {
            "score": quality_score,
            "total_findings": len(findings),
            "naming_issues": len(naming_findings),
            "complexity_issues": len(complexity_findings),
            "code_smells": len(smell_findings),
        }

        await context.set("review_findings", findings)
        await context.set("quality_score", quality_metrics)

        await self.emit("code.reviewed", {
            "quality_score": quality_score,
            "findings": len(findings),
        })

        return self._success(
            quality_score=quality_score,
            total_findings=len(findings),
            breakdown=quality_metrics,
        )

    def _check_naming(self, structure: dict, lang: str) -> list[dict]:
        findings = []
        rules = NAMING_RULES.get(lang, {})

        if "class" in rules:
            for cls in structure.get("classes", []):
                if not re.match(rules["class"], cls["name"]):
                    findings.append({
                        "type": "naming",
                        "item": cls["name"],
                        "file": cls["file"],
                        "line": cls["line"],
                        "message": f"Class '{cls['name']}' doesn't follow PascalCase convention",
                    })

        if "function" in rules:
            for func in structure.get("functions", []):
                name = func["name"]
                if name.startswith("_"):
                    name = name.lstrip("_")
                if name and not re.match(rules["function"], name):
                    findings.append({
                        "type": "naming",
                        "item": func["name"],
                        "file": func["file"],
                        "line": func["line"],
                        "message": f"Function '{func['name']}' doesn't follow naming convention",
                    })

        return findings

    def _check_complexity(self, structure: dict) -> list[dict]:
        findings = []
        for func in structure.get("functions", []):
            length = func.get("length", 0)
            args = func.get("args", 0)

            if length > 50:
                findings.append({
                    "type": "complexity",
                    "item": func["name"],
                    "file": func["file"],
                    "line": func["line"],
                    "message": f"Function '{func['name']}' is {length} lines (max recommended: 50)",
                })

            if args > 5:
                findings.append({
                    "type": "complexity",
                    "item": func["name"],
                    "file": func["file"],
                    "line": func["line"],
                    "message": f"Function '{func['name']}' has {args} parameters (max recommended: 5)",
                })

        return findings

    def _check_code_smells(self, context: Context) -> list[dict]:
        findings = []
        for f in context.files:
            if f.size > 500_000:  # 500KB
                findings.append({
                    "type": "code_smell",
                    "file": f.path,
                    "line": 0,
                    "message": f"File is very large ({f.size // 1024}KB) - consider splitting",
                })
        return findings
