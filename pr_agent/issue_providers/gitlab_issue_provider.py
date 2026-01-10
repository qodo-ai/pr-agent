from __future__ import annotations

from typing import Optional

from pr_agent.issue_providers.base import IssueProvider


class GitlabIssueProvider(IssueProvider):
    def __init__(self, git_provider):
        self.git_provider = git_provider

    def list_issues(self, project_path: Optional[str] = None, state: str = "all"):
        return self.git_provider.list_issues(project_path, state=state)

    def get_issue(self, issue_id, project_path: Optional[str] = None):
        issue_iid = int(issue_id)
        return self.git_provider.get_issue(issue_iid, project_path)

    def get_issue_comments(self, issue):
        return self.git_provider.get_issue_comments(issue)
