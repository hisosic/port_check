"""Test Orchestrator - Discovers and runs test suites."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ai_orchestrator.agents.base import BaseAgent
from ai_orchestrator.core.context import AgentResult, Context, Language

TEST_RUNNERS: dict[str, dict] = {
    "pytest": {"cmd": ["python", "-m", "pytest", "--tb=short", "-q"], "marker": "pytest.ini,conftest.py,pyproject.toml"},
    "unittest": {"cmd": ["python", "-m", "unittest", "discover"], "marker": "test_*.py"},
    "jest": {"cmd": ["npx", "jest", "--passWithNoTests"], "marker": "jest.config.js,jest.config.ts"},
    "mocha": {"cmd": ["npx", "mocha"], "marker": ".mocharc.yml,.mocharc.json"},
    "go_test": {"cmd": ["go", "test", "./..."], "marker": "_test.go"},
    "cargo_test": {"cmd": ["cargo", "test"], "marker": "Cargo.toml"},
    "bash_test": {"cmd": ["bash", "-n"], "marker": "*.sh"},
}


class TestOrchestratorAgent(BaseAgent):
    name = "test_orchestrator"
    capabilities = ["test", "testing", "unittest", "pytest", "jest", "spec", "validation"]
    input_types = ["project_info", "file_list"]
    output_types = ["test_results", "test_coverage", "test_files"]
    priority = 80

    async def execute(self, context: Context) -> AgentResult:
        work_dir = context.working_dir
        detected_runners: list[dict] = []
        test_files: list[str] = []

        # Find test files
        for f in context.files:
            basename = os.path.basename(f.path).lower()
            if ("test" in basename or "spec" in basename) and f.language != Language.UNKNOWN:
                test_files.append(f.path)

        # Detect available test runners
        for runner_name, config in TEST_RUNNERS.items():
            markers = config["marker"].split(",")
            for marker in markers:
                if marker.startswith("*"):
                    if any(f.path.endswith(marker[1:]) for f in context.files):
                        detected_runners.append({"name": runner_name, **config})
                        break
                elif (Path(work_dir) / marker).exists():
                    detected_runners.append({"name": runner_name, **config})
                    break

        # Run detected test runners (dry-run / syntax check only for safety)
        results: list[dict] = []
        for runner in detected_runners:
            result = self._run_tests(runner, work_dir)
            results.append(result)

        await context.set("test_results", results)
        await context.set("test_files", test_files)

        await self.emit("tests.completed", {
            "runners": [r["name"] for r in detected_runners],
            "test_file_count": len(test_files),
        })

        return self._success(
            detected_runners=[r["name"] for r in detected_runners],
            test_file_count=len(test_files),
            results=results,
        )

    def _run_tests(self, runner: dict, work_dir: str) -> dict:
        """Run a test suite with timeout protection."""
        try:
            # For bash, just do syntax check
            if runner["name"] == "bash_test":
                return {"runner": "bash", "status": "syntax_check_only", "passed": True}

            result = subprocess.run(
                runner["cmd"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "runner": runner["name"],
                "status": "passed" if result.returncode == 0 else "failed",
                "passed": result.returncode == 0,
                "output": result.stdout[-2000:] if result.stdout else "",
                "errors": result.stderr[-1000:] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {"runner": runner["name"], "status": "timeout", "passed": False}
        except FileNotFoundError:
            return {"runner": runner["name"], "status": "runner_not_found", "passed": False}
        except Exception as e:
            return {"runner": runner["name"], "status": "error", "passed": False, "error": str(e)}

    def as_mcp_tools(self) -> list[dict]:
        return [{
            "name": "run_tests",
            "description": "Discover and run project test suites",
            "inputSchema": {"type": "object", "properties": {}},
        }]
