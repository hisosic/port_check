"""Security Auditor - Scans for vulnerabilities and security issues."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

# Patterns for secret detection
SECRET_PATTERNS: list[tuple[str, str]] = [
    (r'(?i)(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']', "Hardcoded password"),
    (r'(?i)(?:api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{8,}["\']', "API key in source"),
    (r'(?i)(?:secret|token)\s*[=:]\s*["\'][^"\']{8,}["\']', "Secret/token in source"),
    (r'(?i)(?:aws_access_key_id)\s*[=:]\s*["\']?AKI[A-Z0-9]{16}', "AWS access key"),
    (r'(?i)(?:private[_-]?key)\s*[=:]\s*["\'][^"\']+["\']', "Private key reference"),
    (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----', "Embedded private key"),
    (r'(?i)(?:mysql|postgres|mongodb)://[^\s]+:[^\s]+@', "Database connection string with credentials"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub personal access token"),
    (r'sk-[A-Za-z0-9]{48}', "OpenAI/Anthropic API key pattern"),
]

# Insecure code patterns
INSECURE_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "python": [
        (r'\beval\s*\(', "Use of eval() - potential code injection"),
        (r'\bexec\s*\(', "Use of exec() - potential code injection"),
        (r'pickle\.loads?\s*\(', "Use of pickle - potential deserialization attack"),
        (r'subprocess\.(?:call|Popen|run)\s*\([^)]*shell\s*=\s*True', "Shell=True in subprocess - command injection risk"),
        (r'yaml\.load\s*\([^)]*(?!Loader)', "yaml.load without SafeLoader"),
        (r'__import__\s*\(', "Dynamic import - potential code injection"),
        (r'os\.system\s*\(', "os.system - use subprocess instead"),
    ],
    "bash": [
        (r'\beval\b', "Use of eval in bash - potential injection"),
        (r'\$\{.*:-.*\}.*\beval\b', "Variable expansion with eval"),
        (r'curl.*\|\s*(?:bash|sh)', "Piping curl to shell - unsafe"),
        (r'chmod\s+777\b', "chmod 777 - overly permissive"),
    ],
    "javascript": [
        (r'\beval\s*\(', "eval() usage - code injection risk"),
        (r'innerHTML\s*=', "innerHTML assignment - XSS risk"),
        (r'document\.write\s*\(', "document.write - XSS risk"),
        (r'new\s+Function\s*\(', "Dynamic Function constructor"),
    ],
}


class SecurityAuditorAgent(BaseAgent):
    name = "security_auditor"
    capabilities = ["security", "vulnerability", "audit", "secrets", "owasp", "secure"]
    input_types = ["project_info", "file_list", "code_structure"]
    output_types = ["security_findings", "secret_scan", "vulnerability_report"]
    priority = 85

    async def execute(self, context: Context) -> AgentResult:
        findings: list[dict[str, Any]] = []
        secrets_found: list[dict[str, str]] = []

        for file_info in context.files:
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            # Secret scanning
            for pattern, desc in SECRET_PATTERNS:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    secrets_found.append({
                        "file": file_info.path,
                        "line": str(line_num),
                        "type": desc,
                        "severity": "critical",
                    })

            # Language-specific insecure patterns
            lang = file_info.language.value
            patterns = INSECURE_PATTERNS.get(lang, [])
            for pattern, desc in patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    findings.append({
                        "file": file_info.path,
                        "line": str(line_num),
                        "type": "insecure_pattern",
                        "description": desc,
                        "severity": "high",
                        "language": lang,
                    })

        # Check for security-related files
        work_dir = Path(context.working_dir)
        security_files = self._check_security_files(work_dir)

        # Dependency vulnerability check
        dep_vulns = self._check_dependency_vulns(work_dir)
        findings.extend(dep_vulns)

        all_findings = findings + secrets_found
        await context.set("security_findings", all_findings)
        await context.set("secret_scan", secrets_found)
        await context.set("vulnerability_report", {
            "total_findings": len(all_findings),
            "critical": len([f for f in all_findings if f.get("severity") == "critical"]),
            "high": len([f for f in all_findings if f.get("severity") == "high"]),
            "security_files": security_files,
        })

        await self.emit("security.audited", {
            "findings": len(all_findings),
            "secrets": len(secrets_found),
        })

        return self._success(
            total_findings=len(all_findings),
            secrets_found=len(secrets_found),
            insecure_patterns=len(findings),
            security_files=security_files,
        )

    def _check_security_files(self, root: Path) -> dict[str, bool]:
        return {
            ".gitignore": (root / ".gitignore").exists(),
            ".env.example": (root / ".env.example").exists(),
            "SECURITY.md": (root / "SECURITY.md").exists(),
            ".npmrc": (root / ".npmrc").exists(),
        }

    def _check_dependency_vulns(self, root: Path) -> list[dict]:
        """Try to run dependency vulnerability scanners."""
        findings = []
        # pip-audit for Python
        if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
            try:
                result = subprocess.run(
                    ["pip-audit", "--format=json"],
                    cwd=root, capture_output=True, text=True, timeout=60,
                )
                if result.returncode != 0 and result.stdout:
                    import json
                    vulns = json.loads(result.stdout)
                    for vuln in vulns:
                        findings.append({
                            "type": "dependency_vulnerability",
                            "description": f"{vuln.get('name', 'unknown')}: {vuln.get('description', '')}",
                            "severity": "high",
                        })
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                pass
        return findings

    def as_mcp_tools(self) -> list[dict]:
        return [{
            "name": "security_audit",
            "description": "Run security audit including secret scanning and vulnerability detection",
            "inputSchema": {"type": "object", "properties": {}},
        }]
