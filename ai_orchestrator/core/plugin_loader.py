"""Dynamic agent discovery and loading."""

from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_orchestrator.agents.base import BaseAgent

logger = logging.getLogger(__name__)


def discover_agents(
    extra_dirs: list[str] | None = None,
) -> list[type[BaseAgent]]:
    """Discover all agent classes by scanning the agents package.

    Also scans directories specified in AI_ORCHESTRATOR_PLUGINS env var
    and any explicitly provided extra directories.
    """
    from ai_orchestrator.agents.base import BaseAgent

    agent_classes: list[type[BaseAgent]] = []

    # Scan the built-in agents package
    agents_package = importlib.import_module("ai_orchestrator.agents")
    agents_dir = Path(agents_package.__file__).parent

    for _, module_name, _ in pkgutil.iter_modules([str(agents_dir)]):
        if module_name == "base":
            continue
        try:
            module = importlib.import_module(f"ai_orchestrator.agents.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseAgent)
                    and attr is not BaseAgent
                    and not getattr(attr, "_abstract", False)
                ):
                    agent_classes.append(attr)
                    logger.debug("Discovered agent: %s from %s", attr_name, module_name)
        except Exception as e:
            logger.warning("Failed to load agent module %s: %s", module_name, e)

    # Scan external plugin directories
    plugin_dirs = []
    env_plugins = os.environ.get("AI_ORCHESTRATOR_PLUGINS", "")
    if env_plugins:
        plugin_dirs.extend(env_plugins.split(":"))
    if extra_dirs:
        plugin_dirs.extend(extra_dirs)

    for plugin_dir in plugin_dirs:
        plugin_path = Path(plugin_dir)
        if not plugin_path.is_dir():
            logger.warning("Plugin directory not found: %s", plugin_dir)
            continue
        _scan_directory(plugin_path, agent_classes)

    logger.info("Discovered %d agent classes", len(agent_classes))
    return agent_classes


def _scan_directory(
    directory: Path, agent_classes: list[type],
) -> None:
    """Scan a directory for agent Python files."""
    import sys
    from ai_orchestrator.agents.base import BaseAgent

    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

    for py_file in directory.glob("*.py"):
        module_name = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseAgent)
                        and attr is not BaseAgent
                    ):
                        agent_classes.append(attr)
                        logger.debug("Discovered plugin agent: %s", attr_name)
        except Exception as e:
            logger.warning("Failed to load plugin %s: %s", py_file, e)
