"""Shared execution context - the data backbone for all agents."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    BASH = "bash"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    path: str
    language: Language
    size: int = 0
    last_modified: float = 0.0


@dataclass
class GitState:
    branch: str = ""
    is_repo: bool = False
    has_uncommitted: bool = False
    remote_url: str = ""
    recent_commits: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result from a single agent execution."""
    agent_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class Context:
    """Mutable, scoped data bag shared across all agents in a single execution.

    Every agent reads from and writes to the same context,
    so downstream agents benefit from upstream discoveries.
    """

    def __init__(self, working_dir: str | None = None, task: str = ""):
        self.working_dir = working_dir or os.getcwd()
        self.task = task
        self.created_at = time.time()

        # Project detection
        self.languages: list[Language] = []
        self.primary_language: Language = Language.UNKNOWN
        self.framework: str = ""
        self.files: list[FileInfo] = []
        self.git: GitState = GitState()

        # Agent results accumulator
        self.results: dict[str, AgentResult] = {}

        # Shared data store - agents write domain-specific data here
        self._store: dict[str, Any] = {}
        self._lock = asyncio.Lock()

        # Execution metadata
        self.execution_plan: list[str] = []
        self.active_agents: set[str] = set()

    async def set(self, key: str, value: Any) -> None:
        """Thread-safe write to the shared store."""
        async with self._lock:
            self._store[key] = value

    async def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe read from the shared store."""
        async with self._lock:
            return self._store.get(key, default)

    async def append(self, key: str, value: Any) -> None:
        """Append to a list in the shared store."""
        async with self._lock:
            if key not in self._store:
                self._store[key] = []
            self._store[key].append(value)

    def add_result(self, result: AgentResult) -> None:
        """Record an agent's execution result."""
        self.results[result.agent_name] = result

    def get_result(self, agent_name: str) -> AgentResult | None:
        return self.results.get(agent_name)

    def has_completed(self, agent_name: str) -> bool:
        return agent_name in self.results

    @property
    def store_snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the current store."""
        return dict(self._store)

    def summary(self) -> dict[str, Any]:
        """Return a summary of current context state."""
        return {
            "working_dir": self.working_dir,
            "task": self.task,
            "primary_language": self.primary_language.value,
            "languages": [l.value for l in self.languages],
            "framework": self.framework,
            "file_count": len(self.files),
            "completed_agents": list(self.results.keys()),
            "store_keys": list(self._store.keys()),
        }
