"""Tools contributed by other installed packages.

A package advertises a tool through a `pr_agent.tools` entry point:

    [project.entry-points."pr_agent.tools"]
    jira_lookup = "my_package.tools:JIRA_LOOKUP"

Loading one imports third-party code into the PR-Agent process, so this is off by default and,
when enabled, restricted to distributions the operator named. Discovery is separate from the
registry itself: a discovered tool is registered like any other, and `[tools]` still decides
whether the model is offered it.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Iterable, List

from pr_agent.algo.tool_registry import Tool, get_tool_registry
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

ENTRY_POINT_GROUP = "pr_agent.tools"


def plugins_enabled() -> bool:
    return bool(get_settings().get("tools.plugins_enabled", False))


def allowed_distributions() -> set:
    """Distribution names the operator is willing to load tools from."""
    configured = get_settings().get("tools.plugin_allowlist", []) or []
    if isinstance(configured, str):
        configured = [configured]
    return {str(name).strip().lower() for name in configured if str(name).strip()}


def _tools_from(loaded) -> List[Tool]:
    """An entry point may point at a Tool, or at a callable producing one or several."""
    if isinstance(loaded, Tool):
        return [loaded]
    if callable(loaded):
        produced = loaded()
        if isinstance(produced, Tool):
            return [produced]
        if isinstance(produced, Iterable):
            return [tool for tool in produced if isinstance(tool, Tool)]
    if isinstance(loaded, Iterable):
        return [tool for tool in loaded if isinstance(tool, Tool)]
    return []


def _distribution_of(entry_point) -> str:
    distribution = getattr(entry_point, "dist", None)
    name = getattr(distribution, "name", "") or getattr(distribution, "metadata", {}).get("Name", "")
    return str(name).strip().lower()


def load_tool_plugins() -> List[str]:
    """Register every allowed plugin tool; return the names actually registered.

    One failing plugin never stops the others, and never fails the command that triggered the
    load: a broken third-party package is a warning, not an outage.
    """
    if not plugins_enabled():
        return []
    allowlist = allowed_distributions()
    if not allowlist:
        get_logger().warning(
            "tools.plugins_enabled is on but tools.plugin_allowlist is empty; "
            "no plugin will be loaded")
        return []

    registry = get_tool_registry()
    registered: List[str] = []
    try:
        discovered = list(entry_points(group=ENTRY_POINT_GROUP))
    except Exception as e:
        get_logger().warning(f"Could not read the {ENTRY_POINT_GROUP} entry points: {e}")
        return []

    for entry_point in discovered:
        distribution = _distribution_of(entry_point)
        if distribution not in allowlist:
            get_logger().info(
                f"Skipping the tool {entry_point.name!r}: {distribution or 'an unnamed distribution'} "
                f"is not in tools.plugin_allowlist")
            continue
        try:
            tools = _tools_from(entry_point.load())
        except Exception as e:
            get_logger().warning(f"Could not load the tool plugin {entry_point.name!r}: {e}")
            continue
        if not tools:
            get_logger().warning(f"The entry point {entry_point.name!r} produced no tool")
            continue
        for tool in tools:
            try:
                registry.register(tool)
            except Exception as e:
                get_logger().warning(f"Could not register the plugin tool {tool.name!r}: {e}")
                continue
            registered.append(tool.name)
    if registered:
        get_logger().info(f"Registered plugin tools: {', '.join(registered)}")
    return registered
