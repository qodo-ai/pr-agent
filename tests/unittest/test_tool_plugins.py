"""Loading tools from other installed packages.

An entry point imports third-party code into the PR-Agent process, so the questions are: is it
off by default, is it limited to distributions the operator named, and does one broken package
leave the rest working.
"""
from types import SimpleNamespace

import pytest

from pr_agent.algo.tool_plugins import allowed_distributions, load_tool_plugins, plugins_enabled
from pr_agent.algo.tool_registry import Tool, get_tool_registry
from pr_agent.config_loader import get_settings

LOOKUP = Tool(name="jira_lookup", description="Look up a Jira issue.", handler=lambda: "PROJ-1")
OTHER = Tool(name="pager", description="Page the on-call engineer.", handler=lambda: "paged")


class _EntryPoint:
    def __init__(self, name, value, distribution="pr-agent-jira"):
        self.name = name
        self._value = value
        self.dist = SimpleNamespace(name=distribution)

    def load(self):
        if isinstance(self._value, Exception):
            raise self._value
        return self._value


@pytest.fixture
def plugin_config(monkeypatch):
    def _set(enabled=True, allowlist=("pr-agent-jira",)):
        get_settings().set("tools.plugins_enabled", enabled)
        # a bare string is a valid configured value, so it must not be split into characters here
        get_settings().set("tools.plugin_allowlist",
                           allowlist if isinstance(allowlist, str) else list(allowlist))
    _set()
    yield _set
    get_settings().set("tools.plugins_enabled", False)
    get_settings().set("tools.plugin_allowlist", [])
    for name in ("jira_lookup", "pager"):
        get_tool_registry().unregister(name)


@pytest.fixture
def discovered(monkeypatch):
    def _set(*entry_points):
        monkeypatch.setattr("pr_agent.algo.tool_plugins.entry_points", lambda group=None: list(entry_points))
    return _set


def test_nothing_is_loaded_by_default(discovered, plugin_config):
    plugin_config(enabled=False)
    discovered(_EntryPoint("jira_lookup", LOOKUP))

    assert load_tool_plugins() == []
    assert plugins_enabled() is False


def test_nothing_is_loaded_without_an_allowlist(discovered, plugin_config):
    plugin_config(allowlist=())
    discovered(_EntryPoint("jira_lookup", LOOKUP))

    assert load_tool_plugins() == []


def test_an_allowed_distribution_is_loaded(discovered, plugin_config):
    discovered(_EntryPoint("jira_lookup", LOOKUP))

    assert load_tool_plugins() == ["jira_lookup"]
    assert get_tool_registry().get("jira_lookup") is LOOKUP


def test_a_distribution_outside_the_allowlist_is_skipped(discovered, plugin_config):
    discovered(_EntryPoint("pager", OTHER, distribution="somebody-elses-package"))

    assert load_tool_plugins() == []
    assert get_tool_registry().get("pager") is None


def test_the_allowlist_is_matched_case_insensitively(discovered, plugin_config):
    plugin_config(allowlist=("PR-Agent-Jira",))
    discovered(_EntryPoint("jira_lookup", LOOKUP))

    assert load_tool_plugins() == ["jira_lookup"]


def test_an_entry_point_may_be_a_factory(discovered, plugin_config):
    discovered(_EntryPoint("jira_lookup", lambda: LOOKUP))

    assert load_tool_plugins() == ["jira_lookup"]


def test_an_entry_point_may_produce_several_tools(discovered, plugin_config):
    discovered(_EntryPoint("bundle", lambda: [LOOKUP, OTHER]))

    assert load_tool_plugins() == ["jira_lookup", "pager"]


def test_a_failing_plugin_does_not_stop_the_others(discovered, plugin_config):
    discovered(_EntryPoint("broken", ImportError("no module named x")),
               _EntryPoint("jira_lookup", LOOKUP))

    assert load_tool_plugins() == ["jira_lookup"]


def test_an_entry_point_producing_nothing_is_reported(discovered, plugin_config):
    discovered(_EntryPoint("empty", lambda: "not a tool"))

    assert load_tool_plugins() == []


def test_a_name_already_taken_is_refused(discovered, plugin_config):
    get_tool_registry().register(LOOKUP)
    impostor = Tool(name="jira_lookup", description="Something else", handler=lambda: "")
    discovered(_EntryPoint("jira_lookup", impostor))

    assert load_tool_plugins() == []
    assert get_tool_registry().get("jira_lookup") is LOOKUP


def test_unreadable_entry_points_are_not_fatal(monkeypatch, plugin_config):
    def explode(group=None):
        raise RuntimeError("metadata is corrupt")

    monkeypatch.setattr("pr_agent.algo.tool_plugins.entry_points", explode)

    assert load_tool_plugins() == []


def test_a_loaded_tool_is_still_gated_by_the_tools_section(discovered, plugin_config):
    """Control: loading a plugin does not by itself offer it to the model."""
    discovered(_EntryPoint("jira_lookup", LOOKUP))
    load_tool_plugins()
    get_settings().set("tools.enabled", False)

    assert get_tool_registry().enabled_tools() == []


@pytest.mark.parametrize("configured, expected", [
    ("pr-agent-jira", {"pr-agent-jira"}),
    (["A", "b "], {"a", "b"}),
    ([], set()),
    (None, set()),
])
def test_the_allowlist_is_read_defensively(plugin_config, configured, expected):
    plugin_config(allowlist=configured if configured is not None else [])

    assert allowed_distributions() == expected
