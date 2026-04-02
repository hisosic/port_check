"""Log Analyzer - Parses logs and detects error patterns."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context

LOG_LEVELS = ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"]
LOG_PATTERN = re.compile(
    r'(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2}:\d{2}[.\d]*)?'
    r'.*?(?P<level>' + '|'.join(LOG_LEVELS) + r')'
    r'.*?(?P<message>.+)',
    re.IGNORECASE,
)

LOG_EXTENSIONS = {".log", ".err", ".out"}


class LogAnalyzerAgent(BaseAgent):
    name = "log_analyzer"
    capabilities = ["log", "logging", "error_log", "monitor", "trace"]
    input_types = ["project_info", "file_list"]
    output_types = ["log_analysis", "error_patterns", "log_summary"]
    priority = 45

    async def execute(self, context: Context) -> AgentResult:
        log_files: list[str] = []
        analysis: dict[str, Any] = {
            "level_counts": Counter(),
            "error_messages": [],
            "patterns": [],
            "total_lines": 0,
        }

        # Find log files
        for f in context.files:
            if any(f.path.endswith(ext) for ext in LOG_EXTENSIONS):
                log_files.append(f.path)

        # Also check common log directories
        common_log_dirs = ["logs", "log", "var/log"]
        import os
        for log_dir in common_log_dirs:
            full_path = os.path.join(context.working_dir, log_dir)
            if os.path.isdir(full_path):
                for fname in os.listdir(full_path):
                    fpath = os.path.join(full_path, fname)
                    if os.path.isfile(fpath) and any(fname.endswith(ext) for ext in LOG_EXTENSIONS):
                        if fpath not in log_files:
                            log_files.append(fpath)

        # Analyze each log file
        for log_file in log_files[:20]:  # Limit to 20 files
            self._analyze_log_file(log_file, analysis)

        # Detect recurring patterns
        error_counter = Counter(
            msg["message"][:100] for msg in analysis["error_messages"]
        )
        recurring = [
            {"message": msg, "count": count}
            for msg, count in error_counter.most_common(20)
            if count > 1
        ]
        analysis["patterns"] = recurring

        summary = {
            "log_files_found": len(log_files),
            "total_lines": analysis["total_lines"],
            "level_counts": dict(analysis["level_counts"]),
            "error_count": len(analysis["error_messages"]),
            "recurring_patterns": len(recurring),
        }

        await context.set("log_analysis", analysis)
        await context.set("error_patterns", recurring)
        await context.set("log_summary", summary)

        await self.emit("logs.analyzed", summary)

        return self._success(**summary)

    def _analyze_log_file(self, filepath: str, analysis: dict) -> None:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if line_num > 50000:  # Safety limit
                        break
                    analysis["total_lines"] += 1

                    match = LOG_PATTERN.match(line)
                    if match:
                        level = match.group("level").upper()
                        if level == "WARNING":
                            level = "WARN"
                        analysis["level_counts"][level] += 1

                        if level in ("ERROR", "CRITICAL", "FATAL"):
                            analysis["error_messages"].append({
                                "file": filepath,
                                "line": line_num,
                                "level": level,
                                "message": match.group("message").strip()[:500],
                            })
        except (OSError, UnicodeDecodeError):
            pass
