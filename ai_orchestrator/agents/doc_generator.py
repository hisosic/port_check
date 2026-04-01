"""Doc Generator - Generates documentation from code analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context


class DocGeneratorAgent(BaseAgent):
    name = "doc_generator"
    capabilities = ["documentation", "docs", "readme", "docstring", "document"]
    input_types = ["project_info", "code_structure", "file_list"]
    output_types = ["generated_docs", "doc_coverage"]
    priority = 55

    async def execute(self, context: Context) -> AgentResult:
        code_structure = await context.get("code_structure", {})
        project_info = await context.get("project_info", {})

        # Analyze documentation coverage
        doc_coverage = self._analyze_coverage(code_structure)

        # Generate project documentation
        docs = self._generate_docs(context, code_structure, project_info)

        # Generate CLAUDE.md content
        claude_md = self._generate_claude_md(context, code_structure, project_info)
        docs["CLAUDE.md"] = claude_md

        await context.set("generated_docs", docs)
        await context.set("doc_coverage", doc_coverage)

        await self.emit("docs.generated", {
            "doc_count": len(docs),
            "coverage": doc_coverage,
        })

        return self._success(
            documents_generated=list(docs.keys()),
            doc_coverage=doc_coverage,
        )

    def _analyze_coverage(self, code_structure: dict) -> dict[str, Any]:
        """Analyze how well the code is documented."""
        total_functions = len(code_structure.get("functions", []))
        total_classes = len(code_structure.get("classes", []))
        return {
            "total_functions": total_functions,
            "total_classes": total_classes,
            "files_analyzed": code_structure.get("files_analyzed", 0),
        }

    def _generate_docs(
        self, context: Context, structure: dict, project_info: dict,
    ) -> dict[str, str]:
        docs: dict[str, str] = {}

        # Project overview
        lang = project_info.get("primary_language", "unknown")
        framework = project_info.get("framework", "unknown")
        classes = structure.get("classes", [])
        functions = structure.get("functions", [])

        overview = [
            f"# Project Documentation",
            f"",
            f"**Language**: {lang}",
            f"**Framework**: {framework}",
            f"**Files**: {project_info.get('file_count', 0)}",
            f"",
        ]

        if classes:
            overview.append("## Classes")
            overview.append("")
            for cls in classes[:20]:
                methods = ", ".join(cls.get("methods", [])[:5])
                overview.append(f"### `{cls['name']}`")
                overview.append(f"- File: `{cls['file']}:{cls['line']}`")
                if methods:
                    overview.append(f"- Methods: {methods}")
                overview.append("")

        if functions:
            overview.append("## Functions")
            overview.append("")
            for func in functions[:30]:
                overview.append(f"- `{func['name']}` ({func['file']}:{func['line']})")

        docs["PROJECT_DOCS.md"] = "\n".join(overview)
        return docs

    def _generate_claude_md(
        self, context: Context, structure: dict, project_info: dict,
    ) -> str:
        """Generate CLAUDE.md tailored to the actual project."""
        lines = [
            "# Project Guide",
            "",
            f"Language: {project_info.get('primary_language', 'unknown')}",
            f"Framework: {project_info.get('framework', 'unknown')}",
            "",
            "## Structure",
            "",
        ]

        classes = structure.get("classes", [])
        if classes:
            lines.append("Key classes:")
            for cls in classes[:10]:
                lines.append(f"- `{cls['name']}` in `{cls['file']}`")
            lines.append("")

        functions = structure.get("functions", [])
        if functions:
            lines.append("Key functions:")
            for func in functions[:15]:
                lines.append(f"- `{func['name']}` in `{func['file']}`")
            lines.append("")

        git = context.git
        if git.is_repo:
            lines.extend([
                "## Git",
                f"- Branch: `{git.branch}`",
                f"- Remote: `{git.remote_url}`",
                "",
            ])

        return "\n".join(lines)
