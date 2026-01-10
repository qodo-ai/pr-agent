from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class IssueComment:
    body: str
    url: str = ""
    id: Optional[str] = None
    author: Optional[str] = None


@dataclass
class Issue:
    key: str
    title: str
    description: str = ""
    url: str = ""
    created_at: Optional[str] = None
    author: Optional[dict] = None
    comments: List[IssueComment] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)

    @property
    def body(self) -> str:
        return self.description

    @property
    def web_url(self) -> str:
        return self.url


class IssueProvider(ABC):
    @abstractmethod
    def list_issues(self, project_path: Optional[str] = None, state: str = "all") -> Iterable:
        raise NotImplementedError

    @abstractmethod
    def get_issue(self, issue_id: str, project_path: Optional[str] = None):
        raise NotImplementedError

    def get_issue_comments(self, issue) -> List[IssueComment]:
        return []
