"""Host-provided tools a model may call while answering.

A tool is a named function with a JSON-schema signature and a host-side handler. The registry
is the single place that decides which tools exist, which of them an operator has enabled, and
how a call is executed - so a tool can never be introduced by repository settings or by text in
a pull request, only by the host.

Nothing is enabled by default: `config.tools.enabled` is false, so the registry reports no
tools and the model is never offered any.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

MAX_TOOL_RESULT_CHARS = 8000


@dataclass(frozen=True)
class Tool:
    """One callable exposed to the model.

    `parameters` is a JSON schema object; `handler` receives the decoded arguments as keyword
    arguments and returns text the model can read.
    """

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    handler: Optional[Callable[..., str]] = None

    def spec(self) -> Dict[str, Any]:
        """The tool as the completion API expects to receive it."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """The set of tools this host offers, and the gate in front of them."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Add a tool. Registering the same tool again is a no-op; a different one raises."""
        if not isinstance(tool, Tool) or not tool.name:
            raise TypeError(f"Not a usable tool: {tool!r}")
        if callable(getattr(tool, "handler", None)) is False:
            raise TypeError(f"Tool {tool.name!r} has no handler")
        existing = self._tools.get(tool.name)
        if existing is not None and existing != tool:
            raise ValueError(f"Tool {tool.name!r} is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def registered_names(self) -> List[str]:
        return sorted(self._tools)

    def enabled_tools(self) -> List[Tool]:
        """The tools the operator has turned on, in a stable order.

        Empty unless `tools.enabled` is true. An `allowed` list further narrows the set; an
        empty `allowed` means every registered tool.
        """
        settings = get_settings()
        if not bool(settings.get("tools.enabled", False)):
            return []
        allowed = settings.get("tools.allowed", []) or []
        if isinstance(allowed, str):
            allowed = [allowed]
        allowed = {str(name).strip() for name in allowed if str(name).strip()}
        unknown = allowed - set(self._tools)
        if unknown:
            get_logger().warning(f"tools.allowed names nothing registered: {sorted(unknown)}")
        return [tool for name, tool in sorted(self._tools.items())
                if not allowed or name in allowed]

    def specs(self) -> List[Dict[str, Any]]:
        return [tool.spec() for tool in self.enabled_tools()]

    def execute(self, name: str, arguments: Any) -> str:
        """Run one tool call and always return text the model can read.

        A tool that is unknown, disabled, called with unreadable arguments, or that raises,
        produces an error string rather than an exception: a failed tool must not fail the
        command that was using it.
        """
        tool = next((candidate for candidate in self.enabled_tools() if candidate.name == name), None)
        if tool is None:
            get_logger().warning(f"The model called an unavailable tool: {name!r}")
            return f"Error: the tool {name!r} is not available."
        try:
            kwargs = self._decode_arguments(arguments)
        except ValueError as error:
            return f"Error: could not read the arguments for {name!r}: {error}"
        try:
            result = tool.handler(**kwargs)
        except Exception as error:
            get_logger().warning(f"The tool {name!r} failed: {error}")
            return f"Error: the tool {name!r} failed: {error}"
        return self._as_text(result)

    @staticmethod
    def _decode_arguments(arguments: Any) -> Dict[str, Any]:
        if arguments is None or arguments == "":
            return {}
        if isinstance(arguments, dict):
            return arguments
        try:
            decoded = json.loads(arguments)
        except (TypeError, ValueError) as error:
            raise ValueError(str(error)) from error
        if not isinstance(decoded, dict):
            raise ValueError("arguments must be a JSON object")
        return decoded

    @staticmethod
    def _as_text(result: Any) -> str:
        if isinstance(result, str):
            text = result
        else:
            try:
                text = json.dumps(result, ensure_ascii=False)
            except (TypeError, ValueError):
                text = str(result)
        if len(text) > MAX_TOOL_RESULT_CHARS:
            text = text[:MAX_TOOL_RESULT_CHARS] + "\n[truncated]"
        return text


_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """The process-wide registry."""
    return _registry


def register_tool(tool: Tool) -> None:
    """Make a tool available to the model, subject to the operator's configuration."""
    _registry.register(tool)


def get_max_tool_iterations() -> int:
    """How many rounds of tool calls one answer may take."""
    value = get_settings().get("tools.max_iterations", 3)
    try:
        iterations = int(value)
    except (TypeError, ValueError):
        get_logger().warning(f"tools.max_iterations is not a number ({value!r}); using 3")
        return 3
    return max(0, iterations)
