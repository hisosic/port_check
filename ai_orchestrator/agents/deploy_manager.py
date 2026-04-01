"""Deploy Manager - Orchestrates deployment and validates configs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

DEPLOY_FILES: dict[str, str] = {
    "Dockerfile": "docker",
    "docker-compose.yml": "docker-compose",
    "docker-compose.yaml": "docker-compose",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "helm": "helm",
    "terraform": "terraform",
    "serverless.yml": "serverless",
    "Procfile": "heroku",
    "app.yaml": "gcp-app-engine",
    "fly.toml": "fly.io",
    "render.yaml": "render",
    "vercel.json": "vercel",
    "netlify.toml": "netlify",
}


class DeployManagerAgent(BaseAgent):
    name = "deploy_manager"
    capabilities = ["deploy", "deployment", "release", "kubernetes", "docker", "terraform", "infrastructure"]
    input_types = ["project_info", "file_list"]
    output_types = ["deploy_config", "deploy_issues", "deploy_readiness"]
    priority = 55

    async def execute(self, context: Context) -> AgentResult:
        work_dir = Path(context.working_dir)
        detected_platforms: list[dict[str, Any]] = []
        issues: list[dict[str, str]] = []

        # Detect deployment configurations
        for name, platform in DEPLOY_FILES.items():
            path = work_dir / name
            if path.exists():
                content = ""
                if path.is_file():
                    try:
                        content = path.read_text(encoding="utf-8")[:2000]
                    except OSError:
                        pass
                detected_platforms.append({
                    "platform": platform,
                    "file": str(path),
                    "content_size": len(content),
                })

                # Validate specific configs
                if platform == "docker":
                    issues.extend(self._validate_dockerfile(content, str(path)))
                elif platform == "docker-compose":
                    issues.extend(self._validate_compose(content, str(path)))

        # Check for missing deployment essentials
        readiness = self._check_readiness(work_dir, detected_platforms)

        await context.set("deploy_config", detected_platforms)
        await context.set("deploy_issues", issues)
        await context.set("deploy_readiness", readiness)

        await self.emit("deploy.analyzed", {
            "platforms": [d["platform"] for d in detected_platforms],
            "issues": len(issues),
        })

        return self._success(
            platforms=[d["platform"] for d in detected_platforms],
            issues=issues,
            readiness=readiness,
        )

    def _validate_dockerfile(self, content: str, path: str) -> list[dict]:
        issues = []
        if "FROM" not in content:
            issues.append({"file": path, "message": "Dockerfile missing FROM instruction"})
        if "latest" in content:
            issues.append({"file": path, "message": "Using 'latest' tag - pin to specific version"})
        if "COPY . ." in content and ".dockerignore" not in str(Path(path).parent.iterdir()):
            issues.append({"file": path, "message": "COPY . . without .dockerignore may include unnecessary files"})
        if "USER" not in content:
            issues.append({"file": path, "message": "No USER instruction - container runs as root"})
        if re.search(r'RUN.*&&.*&&.*&&.*&&', content):
            issues.append({"file": path, "message": "Very long RUN chain - consider multi-stage build"})
        return issues

    def _validate_compose(self, content: str, path: str) -> list[dict]:
        issues = []
        if "restart:" not in content:
            issues.append({"file": path, "message": "No restart policy defined"})
        if "healthcheck" not in content:
            issues.append({"file": path, "message": "No healthcheck defined"})
        return issues

    def _check_readiness(self, root: Path, platforms: list[dict]) -> dict[str, Any]:
        checks = {
            "has_deployment_config": len(platforms) > 0,
            "has_gitignore": (root / ".gitignore").exists(),
            "has_readme": (root / "README.md").exists(),
            "has_env_example": (root / ".env.example").exists() or (root / ".env.sample").exists(),
            "has_health_endpoint": False,  # Would need deeper analysis
        }
        score = sum(1 for v in checks.values() if v) * 20
        checks["readiness_score"] = min(score, 100)
        return checks
