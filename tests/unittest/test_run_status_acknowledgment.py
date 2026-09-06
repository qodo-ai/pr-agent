"""An automatic command should say it started before it has anything to publish.

Automatic commands suppress the "Preparing review..." progress comment, so between opening a
pull request and the model answering there is no sign PR-Agent picked it up. A commit status
is the least intrusive signal: it appears immediately and adds nothing to the conversation.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import pr_agent.servers.github_app as github_app
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import GitProvider
from pr_agent.git_providers.github_provider import GithubProvider
from pr_agent.git_providers.gitlab_provider import GitLabProvider

API_URL = "https://api.github.com/repos/org/repo/pulls/1"


@pytest.fixture
def run_status(monkeypatch):
    def _set(enabled=True, context="pr-agent"):
        monkeypatch.setattr(get_settings().config, "publish_run_status", enabled, raising=False)
        monkeypatch.setattr(get_settings().config, "run_status_context", context, raising=False)
    _set()
    return _set


def _github(monkeypatch, sha="abc123"):
    monkeypatch.setattr(GithubProvider, "_get_github_client", lambda self: MagicMock())
    provider = GithubProvider(pr_url=None)
    provider.repo = "org/repo"
    provider.last_commit_id = SimpleNamespace(sha=sha) if sha else None
    provider.repo_obj = MagicMock()
    provider.repo_obj.full_name = "org/repo"
    return provider


def test_a_provider_without_statuses_reports_it(run_status):
    """Bitbucket, Gerrit, CodeCommit and the local provider have no status API."""
    assert GitProvider.publish_run_status(object(), "pending", "working") is False


@pytest.mark.parametrize("state", ["pending", "success", "failure"])
def test_github_publishes_each_state(monkeypatch, run_status, state):
    provider = _github(monkeypatch)

    assert provider.publish_run_status(state, "PR-Agent is running") is True
    provider.repo_obj.get_commit.assert_called_once_with("abc123")
    _args, kwargs = provider.repo_obj.get_commit.return_value.create_status.call_args
    assert kwargs["state"] == state
    assert kwargs["context"] == "pr-agent"
    assert kwargs["description"] == "PR-Agent is running"


def test_github_uses_the_configured_context(monkeypatch, run_status):
    run_status(context="ci/pr-agent")
    provider = _github(monkeypatch)

    provider.publish_run_status("pending", "working")

    _args, kwargs = provider.repo_obj.get_commit.return_value.create_status.call_args
    assert kwargs["context"] == "ci/pr-agent"


def test_github_truncates_a_long_description(monkeypatch, run_status):
    provider = _github(monkeypatch)

    provider.publish_run_status("pending", "x" * 300)

    _args, kwargs = provider.repo_obj.get_commit.return_value.create_status.call_args
    assert len(kwargs["description"]) == GithubProvider.MAX_STATUS_DESCRIPTION


def test_github_without_a_commit_sha_reports_failure(monkeypatch, run_status):
    provider = _github(monkeypatch, sha=None)

    assert provider.publish_run_status("pending", "working") is False


def test_github_survives_an_api_failure(monkeypatch, run_status):
    provider = _github(monkeypatch)
    provider.repo_obj.get_commit.side_effect = RuntimeError("boom")

    assert provider.publish_run_status("pending", "working") is False


def test_gitlab_maps_failure_to_failed(run_status):
    provider = GitLabProvider.__new__(GitLabProvider)
    provider.id_project = "group/project"
    provider.mr = SimpleNamespace(sha="abc123")
    provider.gl = MagicMock()

    assert provider.publish_run_status("failure", "could not finish") is True
    payload = provider.gl.projects.get.return_value.commits.get.return_value.statuses.create.call_args.args[0]
    assert payload["state"] == "failed"
    assert payload["name"] == "pr-agent"


# --------------------------------------------------------------------------------------
# Wiring: the automatic-command runner
# --------------------------------------------------------------------------------------
@pytest.fixture
def auto_commands(monkeypatch):
    provider = MagicMock()
    monkeypatch.setattr(github_app, "get_git_provider_with_context", lambda pr_url: provider)
    monkeypatch.setattr(github_app, "get_pr_commands", lambda name: ["/review"])
    monkeypatch.setattr(github_app, "should_process_pr_logic", lambda body: True)
    monkeypatch.setattr(github_app, "prepare_command", lambda command: command)
    monkeypatch.setattr(get_settings().github_app, "feedback_on_draft_pr", True, raising=False)
    monkeypatch.setattr(get_settings().config, "disable_auto_feedback", False, raising=False)
    return provider


def _states(provider):
    return [call.args[0] for call in provider.publish_run_status.call_args_list]


async def test_a_successful_run_is_marked_pending_then_success(run_status, auto_commands):
    agent = MagicMock()

    async def handle_request(api_url, command, notify=None):
        return True

    agent.handle_request = handle_request

    await github_app._perform_auto_commands_github("pr_commands", agent, {}, API_URL, {})

    assert _states(auto_commands) == ["pending", "success"]


async def test_a_failed_command_is_marked_failure(run_status, auto_commands):
    agent = MagicMock()

    async def handle_request(api_url, command, notify=None):
        return False

    agent.handle_request = handle_request

    await github_app._perform_auto_commands_github("pr_commands", agent, {}, API_URL, {})

    assert _states(auto_commands) == ["pending", "failure"]


async def test_a_raising_command_is_marked_failure(run_status, auto_commands):
    agent = MagicMock()

    async def handle_request(api_url, command, notify=None):
        raise RuntimeError("boom")

    agent.handle_request = handle_request

    await github_app._perform_auto_commands_github("pr_commands", agent, {}, API_URL, {})

    assert _states(auto_commands) == ["pending", "failure"]


async def test_nothing_is_published_when_the_setting_is_off(run_status, auto_commands):
    """Control: the shipped default changes nothing."""
    run_status(enabled=False)
    agent = MagicMock()

    async def handle_request(api_url, command, notify=None):
        return True

    agent.handle_request = handle_request

    await github_app._perform_auto_commands_github("pr_commands", agent, {}, API_URL, {})

    auto_commands.publish_run_status.assert_not_called()
