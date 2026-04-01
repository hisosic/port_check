"""Resource Monitor - Monitors system resources during execution."""

from __future__ import annotations

import os
import time
from typing import Any

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context


class ResourceMonitorAgent(BaseAgent):
    name = "resource_monitor"
    capabilities = ["resource", "memory", "cpu", "disk", "monitor", "usage", "load"]
    input_types = ["project_info"]
    output_types = ["resource_usage", "system_info"]
    priority = 40

    async def execute(self, context: Context) -> AgentResult:
        resource_info: dict[str, Any] = {}

        # Disk usage of working directory
        disk = self._get_disk_usage(context.working_dir)
        resource_info["disk"] = disk

        # Process info
        resource_info["process"] = {
            "pid": os.getpid(),
            "cpu_count": os.cpu_count(),
        }

        # Memory info (Linux)
        mem = self._get_memory_info()
        resource_info["memory"] = mem

        # Project size
        total_size = sum(f.size for f in context.files)
        resource_info["project"] = {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": len(context.files),
        }

        # Load average (Unix)
        try:
            load = os.getloadavg()
            resource_info["load_average"] = {
                "1min": load[0],
                "5min": load[1],
                "15min": load[2],
            }
        except (OSError, AttributeError):
            resource_info["load_average"] = None

        await context.set("resource_usage", resource_info)
        await context.set("system_info", {
            "cpu_count": os.cpu_count(),
            "platform": os.name,
        })

        await self.emit("resources.monitored", resource_info)

        return self._success(**resource_info)

    def _get_disk_usage(self, path: str) -> dict[str, Any]:
        try:
            stat = os.statvfs(path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            used = total - free
            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 1) if total > 0 else 0,
            }
        except (OSError, AttributeError):
            return {}

    def _get_memory_info(self) -> dict[str, Any]:
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            info = {}
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    info[key] = int(val)  # in KB

            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", 0)
            return {
                "total_mb": round(total / 1024, 0),
                "available_mb": round(available / 1024, 0),
                "usage_percent": round(((total - available) / total) * 100, 1) if total > 0 else 0,
            }
        except (OSError, KeyError, ValueError):
            return {}
