from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from typing import Iterable, List, Optional

from pr_agent.config_loader import get_settings
from pr_agent.issue_providers.base import Issue, IssueComment, IssueProvider
from pr_agent.log import get_logger


class JiraIssueProvider(IssueProvider):
    def __init__(self, settings=None, project_path: Optional[str] = None, timeout_seconds: int = 15):
        settings = settings or get_settings()
        jira_settings = _get_section(settings, "JIRA")
        self.base_url = (jira_settings.get("BASE_URL") or "").rstrip("/")
        self.api_email = jira_settings.get("API_EMAIL") or ""
        self.api_token = jira_settings.get("API_TOKEN") or ""
        self.api_version = _coerce_int(jira_settings.get("API_VERSION", 2), default=2)
        self.issue_jql = (jira_settings.get("ISSUE_JQL") or "").strip()
        self.issue_projects = _normalize_list(jira_settings.get("ISSUE_PROJECTS", []))
        self.issue_project_map = jira_settings.get("ISSUE_PROJECT_MAP", {}) or {}
        self.issue_max_results = int(jira_settings.get("ISSUE_MAX_RESULTS") or 200)
        self.valid_project_keys = set(_normalize_list(jira_settings.get("VALID_PROJECT_KEYS", [])))
        self.project_path = project_path
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_email and self.api_token)

    def list_issues(self, project_path: Optional[str] = None, state: str = "all") -> Iterable[Issue]:
        jql = self._build_jql(project_path or self.project_path)
        if not jql:
            get_logger().warning("Jira issue provider has no JQL or project keys; skipping issue listing.")
            return []
        params = {
            "jql": jql,
            "maxResults": self.issue_max_results,
            "fields": "summary,description,created,reporter,labels,subtasks",
        }
        data = self._request_json("search", params, api_version=self.api_version, suppress_warning=True)
        issues = data.get("issues", []) if isinstance(data, dict) else []
        if not issues and self.api_version < 3:
            data = self._request_json("search/jql", params, api_version=3, suppress_warning=False)
            issues = data.get("issues", []) if isinstance(data, dict) else []
        return [self._issue_from_payload(item) for item in issues]

    def get_issue(self, issue_id: str, project_path: Optional[str] = None) -> Optional[Issue]:
        issue_key = (issue_id or "").strip().upper()
        if not issue_key:
            return None
        data = self._request_json(
            f"issue/{urllib.parse.quote(issue_key)}",
            {"fields": "summary,description,created,reporter,labels,subtasks"},
            api_version=self.api_version,
        )
        if not data:
            return None
        return self._issue_from_payload(data)

    def _build_jql(self, project_path: Optional[str]) -> str:
        if self.issue_jql:
            return self.issue_jql
        project_keys = self._resolve_project_keys(project_path)
        if not project_keys:
            return ""
        return f"project in ({', '.join(project_keys)}) order by created DESC"

    def _resolve_project_keys(self, project_path: Optional[str]) -> List[str]:
        project_map = _normalize_project_map(self.issue_project_map)
        keys = []
        if project_path and project_path in project_map:
            keys = project_map[project_path]
        elif self.issue_projects:
            keys = self.issue_projects
        if self.valid_project_keys:
            keys = [key for key in keys if key in self.valid_project_keys]
        return keys

    def _request_json(self, path: str, params: dict, api_version: Optional[int] = None, suppress_warning: bool = False) -> dict:
        if not self.is_configured():
            get_logger().warning("Jira client is not configured; skipping issue fetch")
            return {}
        query = urllib.parse.urlencode(params)
        version = api_version or self.api_version
        url = f"{self.base_url}/rest/api/{version}/{path}"
        if query:
            url = f"{url}?{query}"
        auth_token = base64.b64encode(f"{self.api_email}:{self.api_token}".encode("utf-8")).decode("utf-8")
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Basic {auth_token}")
        request.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload)
        except Exception as exc:
            if not suppress_warning:
                get_logger().warning("Failed to fetch Jira issues", artifact={"error": str(exc), "url": url})
            return {}

    def _issue_from_payload(self, issue: dict) -> Issue:
        fields = issue.get("fields", {}) if isinstance(issue, dict) else {}
        key = issue.get("key", "UNKNOWN")
        summary = fields.get("summary") or ""
        description = JiraIssueProvider._normalize_description(fields.get("description"))
        created_at = fields.get("created") or ""
        reporter = fields.get("reporter") or {}
        author = {"username": reporter.get("displayName") or reporter.get("name") or reporter.get("emailAddress") or ""}
        labels = fields.get("labels") or []
        labels = labels if isinstance(labels, list) else []
        return Issue(
            key=key,
            title=summary,
            description=description,
            url=f"{self.base_url}/browse/{key}" if self.base_url else "",
            created_at=created_at,
            author=author,
            labels=labels,
        )

    def get_issue_comments(self, issue) -> List[IssueComment]:
        issue_key = getattr(issue, "key", None) or getattr(issue, "id", None)
        if not issue_key:
            return []
        data = self._request_json(
            f"issue/{urllib.parse.quote(str(issue_key))}/comment",
            {},
            api_version=self.api_version,
        )
        comments = data.get("comments", []) if isinstance(data, dict) else []
        results = []
        for comment in comments:
            body = comment.get("body") or ""
            if not body:
                continue
            author_obj = comment.get("author") or {}
            author = ""
            if isinstance(author_obj, dict):
                author = author_obj.get("displayName") or author_obj.get("name") or author_obj.get("emailAddress") or ""
            cid = str(comment.get("id") or "")
            results.append(
                IssueComment(
                    body=body,
                    url=self._build_comment_url(issue_key, cid),
                    id=cid,
                    author=author,
                )
            )
        return results

    def _build_comment_url(self, issue_key: str, comment_id: str) -> str:
        if not self.base_url or not issue_key or not comment_id:
            return ""
        return f"{self.base_url}/browse/{issue_key}?focusedCommentId={comment_id}"

    @staticmethod
    def _normalize_description(description: object) -> str:
        if description is None:
            return ""
        if isinstance(description, str):
            return description
        try:
            return str(description)
        except Exception:
            return ""


def _get_section(settings, key: str) -> dict:
    if settings is None:
        return {}
    if hasattr(settings, "get"):
        return settings.get(key, {}) or {}
    return settings.get(key, {}) if isinstance(settings, dict) else {}


def _normalize_list(value: object) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip().upper() for item in value.split(",") if item.strip()]
    return [str(item).strip().upper() for item in value if str(item).strip()]


def _coerce_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_project_map(value: object) -> dict:
    if not value:
        return {}
    try:
        mapping = dict(value)
    except Exception:
        return {}
    normalized = {}
    for project_path, keys in mapping.items():
        normalized[project_path] = _normalize_list(keys)
    return normalized
