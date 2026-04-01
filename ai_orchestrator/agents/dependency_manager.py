"""Dependency Manager - Analyzes dependency trees, outdated packages, license conflicts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context


class DependencyManagerAgent(BaseAgent):
    name = "dependency_manager"
    capabilities = ["dependency", "dependencies", "package", "library", "module", "npm", "pip"]
    input_types = ["project_info"]
    output_types = ["dependency_tree", "outdated_packages", "dependency_issues"]
    priority = 65

    async def execute(self, context: Context) -> AgentResult:
        work_dir = Path(context.working_dir)
        deps: dict[str, Any] = {}
        issues: list[dict[str, str]] = []

        # Python dependencies
        deps["python"] = self._scan_python_deps(work_dir)

        # Node.js dependencies
        deps["node"] = self._scan_node_deps(work_dir)

        # Go dependencies
        deps["go"] = self._scan_go_deps(work_dir)

        # Check for common dependency issues
        issues.extend(self._check_issues(work_dir, deps))

        total_deps = sum(len(d.get("packages", [])) for d in deps.values() if d)

        await context.set("dependency_tree", deps)
        await context.set("dependency_issues", issues)

        await self.emit("dependencies.analyzed", {
            "total_deps": total_deps,
            "issues": len(issues),
        })

        return self._success(
            total_dependencies=total_deps,
            ecosystems=[k for k, v in deps.items() if v],
            issues=issues,
        )

    def _scan_python_deps(self, root: Path) -> dict[str, Any] | None:
        reqs_file = root / "requirements.txt"
        pyproject = root / "pyproject.toml"

        packages: list[dict[str, str]] = []

        if reqs_file.exists():
            try:
                with open(reqs_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("-"):
                            parts = line.split("==")
                            name = parts[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else "unspecified"
                            packages.append({"name": name, "version": version})
            except OSError:
                pass

        if pyproject.exists():
            try:
                with open(pyproject) as f:
                    content = f.read()
                # Simple TOML parsing for dependencies
                in_deps = False
                for line in content.split("\n"):
                    if "dependencies" in line and "[" in line:
                        in_deps = True
                        continue
                    if in_deps and line.strip().startswith("["):
                        in_deps = False
                    if in_deps and "=" in line:
                        parts = line.strip().strip('"').strip("'").split(">=")
                        if parts:
                            packages.append({"name": parts[0].strip().strip('"'), "version": "from pyproject"})
            except OSError:
                pass

        return {"packages": packages, "source": "requirements.txt/pyproject.toml"} if packages else None

    def _scan_node_deps(self, root: Path) -> dict[str, Any] | None:
        pkg_json = root / "package.json"
        if not pkg_json.exists():
            return None
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
            packages = []
            for name, version in pkg.get("dependencies", {}).items():
                packages.append({"name": name, "version": version, "type": "runtime"})
            for name, version in pkg.get("devDependencies", {}).items():
                packages.append({"name": name, "version": version, "type": "dev"})
            return {"packages": packages, "source": "package.json"}
        except (json.JSONDecodeError, OSError):
            return None

    def _scan_go_deps(self, root: Path) -> dict[str, Any] | None:
        go_mod = root / "go.mod"
        if not go_mod.exists():
            return None
        try:
            with open(go_mod) as f:
                content = f.read()
            packages = []
            in_require = False
            for line in content.split("\n"):
                if line.strip().startswith("require ("):
                    in_require = True
                    continue
                if in_require and line.strip() == ")":
                    in_require = False
                if in_require:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        packages.append({"name": parts[0], "version": parts[1]})
            return {"packages": packages, "source": "go.mod"}
        except OSError:
            return None

    def _check_issues(self, root: Path, deps: dict) -> list[dict[str, str]]:
        issues = []

        # Check for lock file consistency
        if (root / "package.json").exists() and not (root / "package-lock.json").exists() and not (root / "yarn.lock").exists():
            issues.append({"type": "missing_lockfile", "message": "No package-lock.json or yarn.lock found"})

        if (root / "requirements.txt").exists():
            with open(root / "requirements.txt") as f:
                for line in f:
                    if line.strip() and "==" not in line and not line.startswith("#") and not line.startswith("-"):
                        name = line.strip().split(">=")[0].split("<=")[0]
                        issues.append({
                            "type": "unpinned_dependency",
                            "message": f"Dependency '{name}' is not pinned to a specific version",
                        })

        return issues
