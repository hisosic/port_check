"""API Architect - Validates API designs and endpoint consistency."""

from __future__ import annotations

import re
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, Language

# Framework-specific route patterns
ROUTE_PATTERNS: dict[str, list[str]] = {
    "python": [
        r'@app\.(?:route|get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',  # Flask/FastAPI
        r'path\s*\(["\']([^"\']+)["\']',  # Django
        r'@router\.(?:get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',  # FastAPI router
    ],
    "javascript": [
        r'(?:app|router)\.(?:get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',  # Express
        r'@(?:Get|Post|Put|Delete|Patch)\s*\(["\']([^"\']+)["\']',  # NestJS
    ],
    "typescript": [
        r'(?:app|router)\.(?:get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',
        r'@(?:Get|Post|Put|Delete|Patch)\s*\(["\']([^"\']+)["\']',
    ],
}


class APIArchitectAgent(BaseAgent):
    name = "api_architect"
    capabilities = ["api", "endpoint", "rest", "route", "controller", "openapi"]
    input_types = ["project_info", "file_list", "code_structure"]
    output_types = ["api_endpoints", "api_issues", "api_report"]
    priority = 55

    async def execute(self, context: Context) -> AgentResult:
        endpoints: list[dict[str, Any]] = []
        issues: list[dict[str, str]] = []

        for file_info in context.files:
            lang = file_info.language.value
            patterns = ROUTE_PATTERNS.get(lang, [])
            if not patterns:
                continue

            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            for pattern in patterns:
                for match in re.finditer(pattern, content):
                    route = match.group(1)
                    # Detect HTTP method from context
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line = content[line_start:match.end()]
                    method = "GET"
                    for m in ["post", "put", "delete", "patch"]:
                        if m in line.lower():
                            method = m.upper()
                            break

                    endpoints.append({
                        "route": route,
                        "method": method,
                        "file": file_info.path,
                        "line": content[:match.start()].count("\n") + 1,
                    })

        # Analyze endpoint consistency
        if endpoints:
            issues.extend(self._check_consistency(endpoints))

        # Check for OpenAPI spec
        openapi_found = self._check_openapi(context)

        await context.set("api_endpoints", endpoints)
        await context.set("api_issues", issues)
        await context.set("api_report", {
            "endpoint_count": len(endpoints),
            "issue_count": len(issues),
            "openapi_found": openapi_found,
        })

        await self.emit("api.analyzed", {
            "endpoints": len(endpoints),
            "issues": len(issues),
        })

        return self._success(
            endpoints_found=len(endpoints),
            issues=len(issues),
            openapi_present=openapi_found,
        )

    def _check_consistency(self, endpoints: list[dict]) -> list[dict[str, str]]:
        issues = []
        routes = [e["route"] for e in endpoints]

        # Check for inconsistent naming
        has_kebab = any("-" in r for r in routes)
        has_snake = any("_" in r.split("/")[-1] for r in routes)
        if has_kebab and has_snake:
            issues.append({
                "type": "naming_inconsistency",
                "message": "Mixed kebab-case and snake_case in route names",
            })

        # Check for missing trailing slashes consistency
        with_slash = sum(1 for r in routes if r.endswith("/") and r != "/")
        without_slash = sum(1 for r in routes if not r.endswith("/") and r != "/")
        if with_slash > 0 and without_slash > 0:
            issues.append({
                "type": "trailing_slash_inconsistency",
                "message": "Inconsistent trailing slash usage in routes",
            })

        # Check for versioning
        versioned = [r for r in routes if re.match(r'/v\d+/', r)]
        unversioned = [r for r in routes if not re.match(r'/v\d+/', r)]
        if versioned and unversioned:
            issues.append({
                "type": "versioning_inconsistency",
                "message": "Some routes are versioned (e.g., /v1/) while others are not",
            })

        return issues

    def _check_openapi(self, context: Context) -> bool:
        for f in context.files:
            basename = f.path.lower()
            if any(name in basename for name in ["openapi", "swagger"]):
                return True
        return False
