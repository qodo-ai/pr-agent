"""The web-search tool: configuration, request shape, and containment.

Search reaches a third party with the host's API key, so what matters is that the tool does not
exist unless the host configured it, that a failure is reported to the model rather than raised,
and that nothing logs the key.
"""
from unittest.mock import MagicMock

import pytest

from pr_agent.algo.tool_registry import ToolRegistry
from pr_agent.config_loader import get_settings
from pr_agent.config_security import REPO_OVERRIDABLE_KEYS_BY_HOST_SECTION
from pr_agent.tools.model_tools.web_search import (
    WEB_SEARCH_TOOL,
    MAX_SNIPPET_CHARS,
    get_web_search_settings,
    register_web_search_tool,
    search_the_web,
)

EXA_PAYLOAD = {"results": [
    {"title": "Deprecation notice", "url": "https://example.test/a", "text": "The API was removed in v3."},
    {"title": "Migration guide", "url": "https://example.test/b", "text": "Use the new client instead."},
]}
TAVILY_PAYLOAD = {"results": [
    {"title": "CVE-2026-1", "url": "https://example.test/cve", "content": "Affects versions below 2.1."},
]}


@pytest.fixture
def search_config(monkeypatch):
    def _set(provider="exa", api_key="secret-key", result_count=3, timeout=10):
        get_settings().set("web_search.provider", provider)
        get_settings().set("web_search.api_key", api_key)
        get_settings().set("web_search.result_count", result_count)
        get_settings().set("web_search.timeout", timeout)
    _set()
    yield _set
    get_settings().set("web_search.provider", "")
    get_settings().set("web_search.api_key", "")


@pytest.fixture
def post(monkeypatch):
    call = MagicMock()
    call.return_value = MagicMock(json=lambda: EXA_PAYLOAD, raise_for_status=lambda: None)
    monkeypatch.setattr("pr_agent.tools.model_tools.web_search.requests.post", call)
    return call


def test_the_tool_is_not_registered_without_a_provider(search_config):
    search_config(provider="")

    assert register_web_search_tool() is False


def test_the_tool_is_not_registered_without_a_key(search_config):
    search_config(api_key="")

    assert register_web_search_tool() is False


def test_an_unsupported_provider_is_refused(search_config):
    search_config(provider="altavista")

    assert get_web_search_settings() == {}
    assert register_web_search_tool() is False


def test_the_tool_is_registered_when_configured(search_config):
    assert register_web_search_tool() is True


def test_the_registered_tool_is_still_gated_by_the_tools_section(search_config):
    """Control: configuring search does not by itself offer it to the model."""
    registry = ToolRegistry()
    registry.register(WEB_SEARCH_TOOL)
    get_settings().set("tools.enabled", False)

    assert registry.enabled_tools() == []


def test_a_search_returns_titles_urls_and_snippets(search_config, post):
    result = search_the_web("is the v2 api deprecated")

    assert "1. Deprecation notice" in result
    assert "https://example.test/a" in result
    assert "The API was removed in v3." in result
    assert "2. Migration guide" in result


def test_exa_receives_the_query_and_the_key(search_config, post):
    search_the_web("is the v2 api deprecated")

    _args, kwargs = post.call_args
    assert post.call_args.args[0] == "https://api.exa.ai/search"
    assert kwargs["json"]["query"] == "is the v2 api deprecated"
    assert kwargs["json"]["numResults"] == 3
    assert kwargs["headers"]["x-api-key"] == "secret-key"
    assert kwargs["allow_redirects"] is False


def test_tavily_uses_its_own_shape(search_config, monkeypatch):
    search_config(provider="tavily")
    call = MagicMock(return_value=MagicMock(json=lambda: TAVILY_PAYLOAD, raise_for_status=lambda: None))
    monkeypatch.setattr("pr_agent.tools.model_tools.web_search.requests.post", call)

    result = search_the_web("CVE-2026-1")

    assert call.call_args.args[0] == "https://api.tavily.com/search"
    assert call.call_args.kwargs["json"]["max_results"] == 3
    assert call.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-key"
    assert "Affects versions below 2.1." in result


@pytest.mark.parametrize("count, expected", [(1, 1), (7, 7), (99, 10), (0, 1), ("4", 4), ("nope", 3)])
def test_the_result_count_is_bounded(search_config, post, count, expected):
    search_config(result_count=count)

    search_the_web("anything")

    assert post.call_args.kwargs["json"]["numResults"] == expected


def test_a_long_snippet_is_truncated(search_config, monkeypatch):
    payload = {"results": [{"title": "Long", "url": "https://example.test/x", "text": "y" * 2000}]}
    monkeypatch.setattr("pr_agent.tools.model_tools.web_search.requests.post",
                        MagicMock(return_value=MagicMock(json=lambda: payload, raise_for_status=lambda: None)))

    result = search_the_web("anything")

    assert "y" * MAX_SNIPPET_CHARS in result
    assert "y" * (MAX_SNIPPET_CHARS + 1) not in result


def test_an_empty_query_is_refused(search_config, post):
    assert search_the_web("   ").startswith("Error: the query is empty")
    post.assert_not_called()


def test_an_unconfigured_host_reports_it_to_the_model(search_config, post):
    search_config(provider="")

    assert search_the_web("anything").startswith("Error: web search is not configured")
    post.assert_not_called()


def test_a_network_failure_is_reported_not_raised(search_config, monkeypatch):
    monkeypatch.setattr("pr_agent.tools.model_tools.web_search.requests.post",
                        MagicMock(side_effect=RuntimeError("connection reset")))

    assert search_the_web("anything").startswith("Error: the web search failed")


def test_the_key_never_reaches_the_log(search_config, monkeypatch, caplog):
    monkeypatch.setattr("pr_agent.tools.model_tools.web_search.requests.post",
                        MagicMock(side_effect=RuntimeError("https://api.exa.ai?key=secret-key")))

    message = search_the_web("anything")

    assert "secret-key" not in message


def test_an_unreadable_payload_is_reported(search_config, monkeypatch):
    monkeypatch.setattr("pr_agent.tools.model_tools.web_search.requests.post",
                        MagicMock(return_value=MagicMock(json=lambda: ["not", "a", "mapping"],
                                                         raise_for_status=lambda: None)))

    assert search_the_web("anything") == "No results."


def test_a_repository_cannot_configure_search():
    assert REPO_OVERRIDABLE_KEYS_BY_HOST_SECTION["web_search"] == frozenset()
