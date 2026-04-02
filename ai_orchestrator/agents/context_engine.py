"""Context Engine - Bootstrap agent that analyzes the working directory.

Runs first on every task. Detects language, framework, git state,
and populates the Context for all downstream agents.
"""

from __future__ import annotations

import os
import subprocess
from collections import Counter
from pathlib import Path

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, FileInfo, GitState, Language

EXTENSION_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".java": Language.JAVA,
    ".sh": Language.BASH,
    ".bash": Language.BASH,
}

FRAMEWORK_MARKERS: dict[str, str] = {
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "package.json": "node",
    "tsconfig.json": "typescript",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java-maven",
    "build.gradle": "java-gradle",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker-compose",
    ".github/workflows": "github-actions",
    "Makefile": "make",
    "manage.py": "django",
    "app.py": "flask",
    "main.py": "python-app",
}

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", "dist", "build", ".mypy_cache"}


class ContextEngineAgent(BaseAgent):
    name = "context_engine"
    capabilities = ["context", "project_detection", "language_detection", "framework_detection", "scan"]
    input_types = []  # No dependencies - runs first
    output_types = ["project_info", "file_list", "git_state", "language_info"]
    priority = 100  # Always runs first

    async def execute(self, context: Context) -> AgentResult:
        work_dir = Path(context.working_dir)

        if not work_dir.exists():
            return self._failure(f"Working directory not found: {work_dir}")

        # Scan files
        files = self._scan_files(work_dir)
        context.files = files

        # Detect languages
        lang_counts = Counter[Language]()
        for f in files:
            if f.language != Language.UNKNOWN:
                lang_counts[f.language] += 1

        context.languages = [lang for lang, _ in lang_counts.most_common()]
        context.primary_language = context.languages[0] if context.languages else Language.UNKNOWN

        # Detect framework
        context.framework = self._detect_framework(work_dir)

        # Git state
        context.git = self._detect_git(work_dir)

        # Store in shared context
        await context.set("project_info", {
            "primary_language": context.primary_language.value,
            "languages": [l.value for l in context.languages],
            "framework": context.framework,
            "file_count": len(files),
        })
        await context.set("file_list", [f.path for f in files])
        await context.set("git_state", {
            "branch": context.git.branch,
            "is_repo": context.git.is_repo,
            "has_uncommitted": context.git.has_uncommitted,
        })

        await self.emit("context.analyzed", {
            "primary_language": context.primary_language.value,
            "framework": context.framework,
            "file_count": len(files),
        })

        return self._success(
            languages=[l.value for l in context.languages],
            framework=context.framework,
            file_count=len(files),
            git_branch=context.git.branch,
        )

    def _scan_files(self, root: Path, max_files: int = 5000) -> list[FileInfo]:
        files: list[FileInfo] = []
        count = 0
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for fname in filenames:
                if count >= max_files:
                    return files
                fpath = Path(dirpath) / fname
                ext = fpath.suffix.lower()
                lang = EXTENSION_MAP.get(ext, Language.UNKNOWN)
                try:
                    stat = fpath.stat()
                    files.append(FileInfo(
                        path=str(fpath),
                        language=lang,
                        size=stat.st_size,
                        last_modified=stat.st_mtime,
                    ))
                except OSError:
                    pass
                count += 1
        return files

    def _detect_framework(self, root: Path) -> str:
        detected = []
        for marker, framework in FRAMEWORK_MARKERS.items():
            if (root / marker).exists():
                detected.append(framework)
        return ", ".join(detected) if detected else "unknown"

    def _detect_git(self, root: Path) -> GitState:
        state = GitState()
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=root, capture_output=True, text=True, timeout=5,
            )
            state.is_repo = result.returncode == 0

            if state.is_repo:
                branch = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=root, capture_output=True, text=True, timeout=5,
                )
                state.branch = branch.stdout.strip()

                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=root, capture_output=True, text=True, timeout=5,
                )
                state.has_uncommitted = bool(status.stdout.strip())

                remote = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=root, capture_output=True, text=True, timeout=5,
                )
                state.remote_url = remote.stdout.strip()

                log = subprocess.run(
                    ["git", "log", "--oneline", "-5"],
                    cwd=root, capture_output=True, text=True, timeout=5,
                )
                state.recent_commits = log.stdout.strip().split("\n") if log.stdout.strip() else []
        except Exception:
            pass
        return state

    def as_mcp_tools(self) -> list[dict]:
        return [{
            "name": "analyze_project",
            "description": "Analyze project structure, detect languages, frameworks, and git state",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "working_dir": {"type": "string", "description": "Directory to analyze"},
                },
            },
        }]
