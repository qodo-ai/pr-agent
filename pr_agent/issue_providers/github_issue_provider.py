from __future__ import annotations

from typing import Optional

from pr_agent.issue_providers.base import IssueProvider


class GithubIssueProvider(IssueProvider):
    def __init__(self, git_provider, repo_obj):
        self.git_provider = git_provider
        self.repo_obj = repo_obj

    def list_issues(self, project_path: Optional[str] = None, state: str = "all"):
        return self.repo_obj.get_issues(state=state)

    def get_issue(self, issue_id, project_path: Optional[str] = None):
        issue_number = int(issue_id)
        return self.repo_obj.get_issue(issue_number)

    def get_issue_comments(self, issue):
        return list(issue.get_comments())
