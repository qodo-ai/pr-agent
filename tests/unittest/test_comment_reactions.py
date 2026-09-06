"""Reactions on the comment that triggered a command are configurable.

The start reaction was hard-coded to `eyes` and nothing marked the outcome, so a user watching
a long command could not tell whether it had finished. `add_reaction` is the provider-level
primitive; `add_eyes_reaction` and `react_to_outcome` are the two policies built on it.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import GitProvider
from pr_agent.git_providers.github_provider import GithubProvider
from pr_agent.git_providers.gitlab_provider import GitLabProvider


class _RecordingProvider(GitProvider):
    """Minimal concrete provider: only the reaction primitive is real."""

    def __init__(self):
        self.reactions = []

    def add_reaction(self, issue_comment_id: int, reaction: str):
        self.reactions.append((issue_comment_id, reaction))
        return len(self.reactions)

    # the abstract surface the base class declares
    def is_supported(self, capability): return True
    def get_files(self): return []
    def get_diff_files(self): return []
    def publish_description(self, pr_title, pr_body): pass
    def publish_comment(self, pr_comment, is_temporary=False): pass
    def publish_inline_comment(self, body, relevant_file, relevant_line_in_file, original_suggestion=None): pass
    def publish_inline_comments(self, comments): pass
    def remove_initial_comment(self): pass
    def remove_comment(self, comment): pass
    def get_languages(self): return {}
    def get_pr_branch(self): return ""
    def get_user_id(self): return ""
    def get_pr_description_full(self): return ""
    def get_issue_comments(self): return []
    def get_repo_settings(self): return b""
    def remove_reaction(self, issue_comment_id, reaction_id): return True
    def get_commit_messages(self) -> str: return ""
    def publish_labels(self, labels): pass
    def get_pr_labels(self, update=False): return []
    def publish_code_suggestions(self, code_suggestions) -> bool: return True


@pytest.fixture
def reactions(monkeypatch):
    def _set(start="eyes", success="", failure=""):
        monkeypatch.setattr(get_settings().config, "reaction_on_start", start, raising=False)
        monkeypatch.setattr(get_settings().config, "reaction_on_success", success, raising=False)
        monkeypatch.setattr(get_settings().config, "reaction_on_failure", failure, raising=False)
    _set()
    return _set


def test_the_start_reaction_defaults_to_eyes(reactions):
    provider = _RecordingProvider()

    provider.add_eyes_reaction(7)

    assert provider.reactions == [(7, "eyes")]


def test_the_start_reaction_is_configurable(reactions):
    reactions(start="rocket")
    provider = _RecordingProvider()

    provider.add_eyes_reaction(7)

    assert provider.reactions == [(7, "rocket")]


@pytest.mark.parametrize("start", ["", "   ", None, 5])
def test_an_empty_start_reaction_adds_nothing(reactions, start):
    reactions(start=start)
    provider = _RecordingProvider()

    assert provider.add_eyes_reaction(7) is None
    assert provider.reactions == []


def test_disable_eyes_still_wins(reactions):
    """Control: the per-call opt-out predates the setting and still applies."""
    provider = _RecordingProvider()

    assert provider.add_eyes_reaction(7, disable_eyes=True) is None
    assert provider.reactions == []


def test_no_outcome_reaction_by_default(reactions):
    provider = _RecordingProvider()

    provider.react_to_outcome(7, succeeded=True)
    provider.react_to_outcome(7, succeeded=False)

    assert provider.reactions == []


def test_the_success_reaction_is_added_when_configured(reactions):
    reactions(success="hooray")
    provider = _RecordingProvider()

    provider.react_to_outcome(7, succeeded=True)

    assert provider.reactions == [(7, "hooray")]


def test_the_failure_reaction_is_added_when_configured(reactions):
    reactions(failure="confused")
    provider = _RecordingProvider()

    provider.react_to_outcome(7, succeeded=False)

    assert provider.reactions == [(7, "confused")]


def test_the_outcome_reaction_needs_a_comment_id(reactions):
    reactions(success="hooray")
    provider = _RecordingProvider()

    assert provider.react_to_outcome(None, succeeded=True) is None
    assert provider.reactions == []


def test_a_provider_without_reactions_is_a_no_op(reactions):
    """Bitbucket, Azure DevOps, Gerrit and CodeCommit have no reaction API."""
    reactions(success="hooray")

    assert GitProvider.add_reaction(object(), 7, "hooray") is None


# --------------------------------------------------------------------------------------
# Provider implementations
# --------------------------------------------------------------------------------------
def _github(monkeypatch):
    monkeypatch.setattr(GithubProvider, "_get_github_client", lambda self: MagicMock())
    provider = GithubProvider(pr_url=None)
    provider.repo = "org/repo"
    provider.pr = MagicMock()
    provider.pr._requester.requestJsonAndCheck.return_value = ({}, {"id": 99})
    return provider


@pytest.mark.parametrize("reaction", ["+1", "-1", "laugh", "confused", "heart", "hooray", "rocket", "eyes"])
def test_github_posts_every_supported_reaction(monkeypatch, reaction):
    provider = _github(monkeypatch)

    assert provider.add_reaction(7, reaction) == 99
    _args, kwargs = provider.pr._requester.requestJsonAndCheck.call_args
    assert kwargs["input"] == {"content": reaction}


def test_github_refuses_a_reaction_it_cannot_send(monkeypatch):
    """GitHub answers 422 for anything outside its set, so the call is not worth making."""
    provider = _github(monkeypatch)

    assert provider.add_reaction(7, "tada") is None
    provider.pr._requester.requestJsonAndCheck.assert_not_called()


def test_github_survives_an_api_failure(monkeypatch):
    provider = _github(monkeypatch)
    provider.pr._requester.requestJsonAndCheck.side_effect = RuntimeError("boom")

    assert provider.add_reaction(7, "eyes") is None


def test_gitlab_awards_the_configured_emoji(monkeypatch):
    provider = GitLabProvider.__new__(GitLabProvider)
    provider.id_mr = 5
    provider.id_project = "group/project"
    note = MagicMock()
    note.awardemojis.create.return_value = SimpleNamespace(id=42)
    provider.gl = MagicMock()
    provider.gl.projects.get.return_value.mergerequests.get.return_value.notes.get.return_value = note

    assert provider.add_reaction(7, "white_check_mark") == 42
    note.awardemojis.create.assert_called_once_with({"name": "white_check_mark"})


# --------------------------------------------------------------------------------------
# End to end: a comment command through the GitHub App handler
# --------------------------------------------------------------------------------------
def _comment_event(body="/review"):
    return {
        "action": "created",
        "comment": {"id": 4242, "body": body},
        "issue": {"pull_request": {"url": "https://api.github.com/repos/org/repo/pulls/1"}},
    }


@pytest.fixture
def comment_handler(monkeypatch):
    """The real handle_comments_on_pr, with only the provider and the agent faked."""
    import pr_agent.servers.github_app as github_app
    from pr_agent.identity_providers.identity_provider import Eligibility

    provider = _RecordingProvider()
    provider.add_eyes_reaction_calls = []
    monkeypatch.setattr(github_app, "get_git_provider_with_context", lambda pr_url: provider)
    monkeypatch.setattr(github_app, "get_identity_provider",
                        lambda: SimpleNamespace(verify_eligibility=lambda *a, **k: Eligibility.ELIGIBLE))
    return github_app, provider


async def test_a_successful_comment_command_is_marked(reactions, comment_handler):
    reactions(success="hooray")
    github_app, provider = comment_handler
    agent = SimpleNamespace()

    async def handle_request(api_url, command, notify=None):
        notify()
        return True

    agent.handle_request = handle_request

    await github_app.handle_comments_on_pr(_comment_event(), "issue_comment", "user", "1", "created", {}, agent)

    assert provider.reactions == [(4242, "eyes"), (4242, "hooray")]


async def test_a_failed_comment_command_is_marked(reactions, comment_handler):
    reactions(failure="confused")
    github_app, provider = comment_handler
    agent = SimpleNamespace()

    async def handle_request(api_url, command, notify=None):
        notify()
        return False

    agent.handle_request = handle_request

    await github_app.handle_comments_on_pr(_comment_event(), "issue_comment", "user", "1", "created", {}, agent)

    assert provider.reactions == [(4242, "eyes"), (4242, "confused")]


async def test_the_default_configuration_adds_only_the_start_reaction(reactions, comment_handler):
    """Control: with no outcome reaction configured the thread looks exactly as it does today."""
    github_app, provider = comment_handler
    agent = SimpleNamespace()

    async def handle_request(api_url, command, notify=None):
        notify()
        return True

    agent.handle_request = handle_request

    await github_app.handle_comments_on_pr(_comment_event(), "issue_comment", "user", "1", "created", {}, agent)

    assert provider.reactions == [(4242, "eyes")]
