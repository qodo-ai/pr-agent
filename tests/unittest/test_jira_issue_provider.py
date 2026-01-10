import json
from unittest.mock import MagicMock, patch

from pr_agent.issue_providers.jira_issue_provider import JiraIssueProvider


def _mock_response(payload: dict):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    return response


def test_build_jql_prefers_explicit():
    provider = JiraIssueProvider(settings={"JIRA": {"ISSUE_JQL": "project = ABC"}}, project_path="org/repo")
    assert provider._build_jql("org/repo") == "project = ABC"


def test_build_jql_uses_project_map():
    provider = JiraIssueProvider(
        settings={"JIRA": {"ISSUE_PROJECT_MAP": {"org/repo": ["ABC", "DEF"]}}},
        project_path="org/repo",
    )
    assert provider._build_jql("org/repo") == "project in (ABC, DEF) order by created DESC"


def test_list_issues_parses_payload():
    payload = {
        "issues": [
            {
                "key": "ABC-1",
                "id": "10001",
                "fields": {
                    "summary": "Test issue",
                    "description": "Body text",
                    "created": "2025-01-01T00:00:00.000+0000",
                    "reporter": {"displayName": "Alice"},
                },
            }
        ]
    }
    provider = JiraIssueProvider(
        settings={
            "JIRA": {
                "BASE_URL": "https://jira.example.com",
                "API_EMAIL": "user@example.com",
                "API_TOKEN": "token",
                "ISSUE_JQL": "project = ABC",
            }
        },
        project_path="org/repo",
    )
    with patch("pr_agent.issue_providers.jira_issue_provider.urllib.request.urlopen", return_value=_mock_response(payload)):
        issues = list(provider.list_issues())
    assert len(issues) == 1
    assert issues[0].key == "ABC-1"
    assert issues[0].title == "Test issue"
    assert issues[0].description == "Body text"
