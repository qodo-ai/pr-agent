import types

import pytest

from pr_agent.issue_providers.base import Issue
from pr_agent.tools import ticket_pr_compliance_check


class DummyGitProvider:
    def get_user_description(self):
        return "Implements ABC-1 and follow-up work for ABC-2."

    def get_pr_branch(self):
        return "feature/ABC-2-add-tests"

    def get_commit_messages(self):
        return "Refs ABC-1"


class DummyJiraProvider:
    def __init__(self, issues):
        self._issues = issues

    def get_issue(self, issue_id, project_path=None):
        return self._issues.get(issue_id)


@pytest.mark.asyncio
async def test_extract_tickets_uses_jira_provider(monkeypatch):
    issue_one = Issue(
        key="ABC-1",
        title="Issue one",
        description="Body one",
        url="https://jira.example.com/browse/ABC-1",
    )
    issue_two = Issue(
        key="ABC-2",
        title="Issue two",
        description="Body two",
        url="https://jira.example.com/browse/ABC-2",
    )
    dummy_provider = DummyJiraProvider({"ABC-1": issue_one, "ABC-2": issue_two})
    dummy_settings = types.SimpleNamespace(
        config=types.SimpleNamespace(git_provider="gitlab"),
        get=lambda key, default=None: "jira" if key == "CONFIG.ISSUE_PROVIDER" else default,
    )

    monkeypatch.setattr(ticket_pr_compliance_check, "get_issue_provider", lambda *args, **kwargs: dummy_provider)
    monkeypatch.setattr(ticket_pr_compliance_check, "get_settings", lambda: dummy_settings)

    tickets = await ticket_pr_compliance_check.extract_tickets(DummyGitProvider())

    assert [ticket["ticket_id"] for ticket in tickets] == ["ABC-1", "ABC-2"]
    assert tickets[0]["ticket_url"] == "https://jira.example.com/browse/ABC-1"
    assert tickets[1]["title"] == "Issue two"
