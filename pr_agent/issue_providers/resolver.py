from __future__ import annotations

from typing import Optional

from pr_agent.config_loader import get_settings
from pr_agent.issue_providers.github_issue_provider import GithubIssueProvider
from pr_agent.issue_providers.gitlab_issue_provider import GitlabIssueProvider
from pr_agent.issue_providers.jira_issue_provider import JiraIssueProvider


def resolve_issue_provider_name(config_value: Optional[str], git_provider_name: Optional[str]) -> str:
    value = (config_value or "auto").strip().lower()
    if value == "auto":
        return (git_provider_name or "gitlab").strip().lower()
    return value


def get_issue_provider(
    provider_name: Optional[str],
    git_provider=None,
    repo_obj=None,
    project_path: Optional[str] = None,
    settings=None,
):
    resolved = resolve_issue_provider_name(provider_name, getattr(git_provider, "provider_name", None))
    if resolved == "jira":
        return JiraIssueProvider(settings=settings or get_settings(), project_path=project_path)
    if resolved == "github":
        if repo_obj is None:
            raise ValueError("GithubIssueProvider requires repo_obj")
        return GithubIssueProvider(git_provider, repo_obj)
    if resolved == "gitlab":
        if git_provider is None:
            raise ValueError("GitlabIssueProvider requires git_provider")
        return GitlabIssueProvider(git_provider)
    raise ValueError(f"Unsupported issue provider '{resolved}'")
