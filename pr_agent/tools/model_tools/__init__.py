"""Tools the host can offer to the model.

Importing a module here does not enable anything: registration only makes a tool known, and
`[tools]` still decides whether it is offered. `register_builtin_tools()` is the one entry point
a server or the CLI calls at start-up.
"""

from pr_agent.log import get_logger


def register_builtin_tools() -> None:
    """Register the tools that ship with PR-Agent, skipping any that are not configured."""
    from pr_agent.tools.model_tools.web_search import register_web_search_tool

    for register in (register_web_search_tool,):
        try:
            register()
        except Exception as e:
            get_logger().warning(f"Could not register a built-in tool: {e}")
