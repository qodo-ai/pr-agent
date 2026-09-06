"""Host-provided tools: registration, the operator's gate, and call execution.

A tool reaches the network or the host filesystem, so the registry is the boundary: nothing is
offered unless the host registered it *and* the operator enabled it, and a failing tool returns
text rather than failing the command.
"""
import json

import pytest

from pr_agent.algo.tool_registry import (
    MAX_TOOL_RESULT_CHARS,
    Tool,
    ToolRegistry,
    get_max_tool_iterations,
)
from pr_agent.config_loader import get_settings
from pr_agent.config_security import REPO_OVERRIDABLE_KEYS_BY_HOST_SECTION

ECHO = Tool(
    name="echo",
    description="Repeat the given text.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    handler=lambda text: f"echo: {text}",
)
CLOCK = Tool(name="clock", description="Return a fixed time.", handler=lambda: "12:00")


@pytest.fixture
def tools_config(monkeypatch):
    def _set(enabled=True, allowed=None, max_iterations=3):
        get_settings().set("tools.enabled", enabled)
        get_settings().set("tools.allowed", allowed if allowed is not None else [])
        get_settings().set("tools.max_iterations", max_iterations)
    _set()
    yield _set
    get_settings().set("tools.enabled", False)


@pytest.fixture
def registry():
    registry = ToolRegistry()
    registry.register(ECHO)
    registry.register(CLOCK)
    return registry


def test_nothing_is_offered_until_the_operator_says_so(registry, tools_config):
    tools_config(enabled=False)

    assert registry.enabled_tools() == []
    assert registry.specs() == []


def test_every_registered_tool_is_offered_by_default(registry, tools_config):
    assert [tool.name for tool in registry.enabled_tools()] == ["clock", "echo"]


def test_an_allowlist_narrows_the_set(registry, tools_config):
    tools_config(allowed=["echo"])

    assert [tool.name for tool in registry.enabled_tools()] == ["echo"]


def test_an_allowlist_naming_nothing_registered_offers_nothing(registry, tools_config):
    tools_config(allowed=["nope"])

    assert registry.enabled_tools() == []


def test_the_spec_matches_the_completion_api(registry, tools_config):
    tools_config(allowed=["echo"])

    assert registry.specs() == [{
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Repeat the given text.",
            "parameters": ECHO.parameters,
        },
    }]


def test_registering_the_same_tool_twice_is_allowed(registry):
    registry.register(ECHO)

    assert registry.registered_names() == ["clock", "echo"]


def test_registering_a_different_tool_under_a_taken_name_raises(registry):
    with pytest.raises(ValueError):
        registry.register(Tool(name="echo", description="Something else", handler=lambda: ""))


@pytest.mark.parametrize("bad", [None, "echo", 42, Tool(name="", description="", handler=lambda: "")])
def test_registering_something_that_is_not_a_tool_raises(registry, bad):
    with pytest.raises(TypeError):
        registry.register(bad)


# --------------------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------------------
def test_a_call_runs_the_handler(registry, tools_config):
    assert registry.execute("echo", json.dumps({"text": "hi"})) == "echo: hi"


def test_arguments_may_arrive_already_decoded(registry, tools_config):
    assert registry.execute("echo", {"text": "hi"}) == "echo: hi"


def test_a_tool_without_arguments_is_callable(registry, tools_config):
    assert registry.execute("clock", "") == "12:00"
    assert registry.execute("clock", None) == "12:00"


def test_an_unknown_tool_is_reported_to_the_model(registry, tools_config):
    assert "not available" in registry.execute("rm_rf", "{}")


def test_a_disabled_tool_cannot_be_called(registry, tools_config):
    """The gate is enforced at call time, not only when the specs are built."""
    tools_config(allowed=["clock"])

    assert "not available" in registry.execute("echo", json.dumps({"text": "hi"}))


def test_a_call_with_no_tools_enabled_is_refused(registry, tools_config):
    tools_config(enabled=False)

    assert "not available" in registry.execute("echo", json.dumps({"text": "hi"}))


@pytest.mark.parametrize("arguments", ["{not json", "[1, 2]", '"a string"'])
def test_unreadable_arguments_are_reported_not_raised(registry, tools_config, arguments):
    assert registry.execute("echo", arguments).startswith("Error: could not read the arguments")


def test_a_raising_tool_is_reported_not_raised(tools_config):
    registry = ToolRegistry()
    registry.register(Tool(name="boom", description="Always fails.",
                           handler=lambda: (_ for _ in ()).throw(RuntimeError("no"))))

    assert registry.execute("boom", "{}").startswith("Error: the tool 'boom' failed")


def test_a_wrong_argument_name_is_reported_not_raised(registry, tools_config):
    assert registry.execute("echo", json.dumps({"wrong": "hi"})).startswith("Error: the tool 'echo' failed")


def test_a_non_string_result_is_serialised(tools_config):
    registry = ToolRegistry()
    registry.register(Tool(name="data", description="Returns a mapping.",
                           handler=lambda: {"a": 1}))

    assert registry.execute("data", "{}") == '{"a": 1}'


def test_a_long_result_is_truncated(tools_config):
    registry = ToolRegistry()
    registry.register(Tool(name="long", description="Returns a lot.",
                           handler=lambda: "x" * (MAX_TOOL_RESULT_CHARS + 500)))

    result = registry.execute("long", "{}")

    assert len(result) == MAX_TOOL_RESULT_CHARS + len("\n[truncated]")
    assert result.endswith("[truncated]")


# --------------------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("value, expected", [(5, 5), ("4", 4), (0, 0), (-1, 0), ("nope", 3), (None, 3)])
def test_the_iteration_budget_is_read_defensively(tools_config, value, expected):
    tools_config(max_iterations=value)

    assert get_max_tool_iterations() == expected


def test_a_repository_cannot_enable_tools():
    """`[tools]` decides what the model may reach, so it is host-only."""
    assert REPO_OVERRIDABLE_KEYS_BY_HOST_SECTION["tools"] == frozenset()
