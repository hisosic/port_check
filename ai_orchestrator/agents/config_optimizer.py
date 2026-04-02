"""Config Optimizer - Reviews and optimizes configuration files."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

CONFIG_FILES: dict[str, str] = {
    ".env": "environment",
    ".env.local": "environment",
    ".env.production": "environment",
    "config.json": "json_config",
    "config.yaml": "yaml_config",
    "config.yml": "yaml_config",
    "settings.json": "json_config",
    ".eslintrc": "eslint",
    ".eslintrc.json": "eslint",
    ".prettierrc": "prettier",
    "tsconfig.json": "typescript",
    "pyproject.toml": "python",
    "setup.cfg": "python",
    ".flake8": "python_lint",
    "mypy.ini": "python_typecheck",
    ".editorconfig": "editor",
    ".gitignore": "git",
}


class ConfigOptimizerAgent(BaseAgent):
    name = "config_optimizer"
    capabilities = ["config", "configuration", "settings", "env", "environment", "setup", "optimize"]
    input_types = ["project_info", "file_list"]
    output_types = ["config_analysis", "config_issues", "config_suggestions"]
    priority = 55

    async def execute(self, context: Context) -> AgentResult:
        work_dir = Path(context.working_dir)
        configs_found: list[dict[str, Any]] = []
        issues: list[dict[str, str]] = []
        suggestions: list[dict[str, str]] = []

        # Scan for config files
        for filename, config_type in CONFIG_FILES.items():
            filepath = work_dir / filename
            if filepath.exists():
                configs_found.append({
                    "file": filename,
                    "type": config_type,
                    "path": str(filepath),
                })

                # Analyze specific config types
                if config_type == "environment":
                    env_issues = self._analyze_env(filepath)
                    issues.extend(env_issues)
                elif config_type == "json_config":
                    json_issues = self._analyze_json_config(filepath)
                    issues.extend(json_issues)
                elif config_type == "git":
                    git_issues = self._analyze_gitignore(filepath, context)
                    issues.extend(git_issues)

        # Check for missing recommended configs
        missing = self._check_missing_configs(work_dir, context)
        suggestions.extend(missing)

        # Claude Code specific suggestions
        claude_suggestions = self._suggest_claude_config(work_dir, context)
        suggestions.extend(claude_suggestions)

        await context.set("config_analysis", configs_found)
        await context.set("config_issues", issues)
        await context.set("config_suggestions", suggestions)

        await self.emit("config.optimized", {
            "configs_found": len(configs_found),
            "issues": len(issues),
            "suggestions": len(suggestions),
        })

        return self._success(
            configs_found=len(configs_found),
            issues=issues,
            suggestions=suggestions,
        )

    def _analyze_env(self, filepath: Path) -> list[dict]:
        issues = []
        try:
            content = filepath.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    # Check for potentially exposed secrets
                    if any(s in key.lower() for s in ["password", "secret", "key", "token"]):
                        if value.strip() and value.strip() not in ("", '""', "''", "changeme", "xxx"):
                            issues.append({
                                "file": str(filepath),
                                "line": str(i),
                                "type": "potential_secret",
                                "message": f"Potential secret in {key} - ensure .env is in .gitignore",
                            })
        except OSError:
            pass
        return issues

    def _analyze_json_config(self, filepath: Path) -> list[dict]:
        issues = []
        try:
            with open(filepath) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append({
                "file": str(filepath),
                "type": "invalid_json",
                "message": f"Invalid JSON: {e}",
            })
        except OSError:
            pass
        return issues

    def _analyze_gitignore(self, filepath: Path, context: Context) -> list[dict]:
        issues = []
        try:
            content = filepath.read_text(encoding="utf-8")
            patterns = content.strip().split("\n")

            # Check for important patterns
            important_patterns = {
                ".env": "Environment files with secrets",
                "node_modules": "Node.js dependencies",
                "__pycache__": "Python cache",
                ".venv": "Python virtual environment",
                "*.pyc": "Python compiled files",
                ".DS_Store": "macOS metadata",
            }

            for pattern, desc in important_patterns.items():
                if not any(pattern in p for p in patterns):
                    lang = context.primary_language.value
                    # Only suggest relevant patterns
                    if pattern in (".env",) or \
                       (lang == "python" and pattern in ("__pycache__", ".venv", "*.pyc")) or \
                       (lang in ("javascript", "typescript") and pattern == "node_modules"):
                        issues.append({
                            "file": str(filepath),
                            "type": "missing_pattern",
                            "message": f"Missing '{pattern}' ({desc}) in .gitignore",
                        })
        except OSError:
            pass
        return issues

    def _check_missing_configs(self, root: Path, context: Context) -> list[dict]:
        suggestions = []
        if not (root / ".editorconfig").exists():
            suggestions.append({
                "type": "missing_config",
                "file": ".editorconfig",
                "message": "Add .editorconfig for consistent coding style across editors",
            })
        if not (root / ".gitignore").exists():
            suggestions.append({
                "type": "missing_config",
                "file": ".gitignore",
                "message": "Add .gitignore to exclude build artifacts and secrets",
            })
        return suggestions

    def _suggest_claude_config(self, root: Path, context: Context) -> list[dict]:
        suggestions = []
        if not (root / "CLAUDE.md").exists():
            suggestions.append({
                "type": "claude_config",
                "file": "CLAUDE.md",
                "message": "Add CLAUDE.md to provide project context to Claude Code",
            })
        if not (root / ".claude" / "settings.json").exists():
            suggestions.append({
                "type": "claude_config",
                "file": ".claude/settings.json",
                "message": "Add Claude Code settings with MCP servers and hooks",
            })
        return suggestions

    def as_mcp_tools(self) -> list[dict]:
        return [{
            "name": "optimize_config",
            "description": "Analyze and optimize project configuration files",
            "inputSchema": {"type": "object", "properties": {}},
        }]
