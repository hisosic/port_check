"""CI/CD Integrator - Reads, validates, and suggests CI/CD pipeline improvements."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

CI_CONFIGS: dict[str, list[str]] = {
    "github_actions": [".github/workflows"],
    "gitlab_ci": [".gitlab-ci.yml"],
    "jenkins": ["Jenkinsfile"],
    "circleci": [".circleci/config.yml"],
    "travis": [".travis.yml"],
    "azure_devops": ["azure-pipelines.yml"],
}


class CICDIntegratorAgent(BaseAgent):
    name = "cicd_integrator"
    capabilities = ["ci", "cd", "pipeline", "github_actions", "workflow", "build", "automation"]
    input_types = ["project_info", "file_list"]
    output_types = ["ci_config", "ci_suggestions", "pipeline_analysis"]
    priority = 60

    async def execute(self, context: Context) -> AgentResult:
        work_dir = Path(context.working_dir)
        detected_ci: list[dict[str, Any]] = []
        suggestions: list[dict[str, str]] = []

        # Detect existing CI configs
        for ci_type, paths in CI_CONFIGS.items():
            for path in paths:
                full_path = work_dir / path
                if full_path.exists():
                    config_content = self._read_ci_config(full_path)
                    detected_ci.append({
                        "type": ci_type,
                        "path": str(full_path),
                        "content_preview": config_content[:500] if config_content else "",
                    })

        # Generate suggestions based on project
        if not detected_ci:
            suggestions.append({
                "type": "missing_ci",
                "message": "No CI/CD configuration detected",
                "recommendation": self._suggest_ci(context),
            })
        else:
            for ci in detected_ci:
                ci_issues = self._analyze_ci(ci)
                suggestions.extend(ci_issues)

        # Suggest GitHub Actions workflow if on GitHub
        if context.git.remote_url and "github" in context.git.remote_url:
            if not any(ci["type"] == "github_actions" for ci in detected_ci):
                suggestions.append({
                    "type": "suggestion",
                    "message": "GitHub repository detected but no GitHub Actions workflow found",
                    "recommendation": "Add .github/workflows/ci.yml for automated testing",
                })

        await context.set("ci_config", detected_ci)
        await context.set("ci_suggestions", suggestions)

        await self.emit("cicd.analyzed", {
            "detected": [ci["type"] for ci in detected_ci],
            "suggestions": len(suggestions),
        })

        return self._success(
            detected_ci=[ci["type"] for ci in detected_ci],
            suggestion_count=len(suggestions),
            suggestions=suggestions,
        )

    def _read_ci_config(self, path: Path) -> str:
        if path.is_dir():
            contents = []
            for f in path.iterdir():
                if f.suffix in (".yml", ".yaml"):
                    try:
                        contents.append(f.read_text(encoding="utf-8"))
                    except OSError:
                        pass
            return "\n---\n".join(contents)
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _suggest_ci(self, context: Context) -> str:
        lang = context.primary_language.value
        if lang == "python":
            return "GitHub Actions with pytest, black, mypy"
        elif lang in ("javascript", "typescript"):
            return "GitHub Actions with jest, eslint, build"
        elif lang == "go":
            return "GitHub Actions with go test, golint"
        elif lang == "rust":
            return "GitHub Actions with cargo test, clippy"
        return "GitHub Actions with basic test/lint/build steps"

    def _analyze_ci(self, ci: dict) -> list[dict[str, str]]:
        issues = []
        content = ci.get("content_preview", "").lower()

        if "cache" not in content:
            issues.append({
                "type": "optimization",
                "message": f"No caching detected in {ci['type']} config",
                "recommendation": "Add dependency caching to speed up CI runs",
            })

        if "security" not in content and "audit" not in content:
            issues.append({
                "type": "security",
                "message": f"No security scanning step in {ci['type']}",
                "recommendation": "Add a security audit step to the pipeline",
            })

        return issues
