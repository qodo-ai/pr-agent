"""
Comment Formatter with Fix in Cursor Links

Formats review comments and code suggestions with clickable deep links
that open Cursor IDE with the AI agent pre-filled with fix instructions.

URL Schemes:
- cursor://agent/prompt?prompt={encoded} - Opens Agent with pre-filled prompt
- cursor://open?file={path}&line={line} - Opens file at specific line
- https://vscode.dev/github/{org}/{repo}/... - Web fallback
"""

from urllib.parse import quote, urlparse
from typing import Optional, Dict, List, Any
import re
import logging

logger = logging.getLogger(__name__)


class CommentFormatter:
    """Format review comments with Fix in Cursor deep links."""
    
    def __init__(self, org: str, repo: str, branch: str = "main"):
        """
        Initialize the comment formatter.
        
        Args:
            org: GitHub organization name
            repo: Repository name
            branch: Branch name (default: main)
        """
        self.org = org
        self.repo = repo
        self.branch = branch
    
    @classmethod
    def from_pr_url(cls, pr_url: str) -> "CommentFormatter":
        """
        Create a CommentFormatter from a PR URL.
        
        Args:
            pr_url: Full GitHub PR URL (e.g., https://github.com/Workiz/backend/pull/123)
        
        Returns:
            CommentFormatter instance
        """
        org, repo, branch = cls._parse_pr_url(pr_url)
        return cls(org, repo, branch)
    
    @staticmethod
    def _parse_pr_url(pr_url: str) -> tuple[str, str, str]:
        """
        Parse organization and repo from PR URL.
        
        Args:
            pr_url: GitHub PR URL
        
        Returns:
            Tuple of (org, repo, branch)
        """
        try:
            parsed = urlparse(pr_url)
            path_parts = parsed.path.strip("/").split("/")
            
            if len(path_parts) >= 2:
                org = path_parts[0]
                repo = path_parts[1]
                return org, repo, "main"
            
            return "Workiz", "unknown", "main"
        except Exception:
            return "Workiz", "unknown", "main"
    
    def format_finding_with_cursor_link(
        self,
        issue_type: str,
        file_path: str,
        line_number: int,
        code_snippet: str,
        suggestion: str,
        severity: str = "warning",
        rule_id: Optional[str] = None,
        include_open_file: bool = True,
        show_web_fallback: bool = True,
    ) -> str:
        """
        Format a single finding with Fix in Cursor links.
        
        Args:
            issue_type: Type/title of the issue
            file_path: Path to the file
            line_number: Line number where issue occurs
            code_snippet: The problematic code snippet
            suggestion: Suggested fix
            severity: Issue severity (info, warning, error, critical)
            rule_id: Optional rule ID
            include_open_file: Include "Open File" link
            show_web_fallback: Include vscode.dev fallback link
        
        Returns:
            Formatted markdown string with Cursor links
        """
        agent_url = self._build_cursor_agent_url(
            issue_type, file_path, line_number, suggestion, rule_id
        )
        
        links = [f"[🔧 Fix in Cursor]({agent_url})"]
        
        if include_open_file:
            open_url = self._build_cursor_open_url(file_path, line_number)
            links.append(f"[📂 Open File]({open_url})")
        
        if show_web_fallback:
            web_url = self._build_web_url(file_path, line_number)
            links.append(f"[🌐 vscode.dev]({web_url})")
        
        links_str = " | ".join(links)
        
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨",
        }.get(severity.lower(), "⚠️")
        
        rule_str = f" (`{rule_id}`)" if rule_id else ""
        
        return f"""{severity_emoji} **{issue_type}**{rule_str}

📁 `{file_path}` (line {line_number})

```
{code_snippet}
```

💡 {suggestion}

{links_str}
"""
    
    def format_finding_inline(
        self,
        issue_type: str,
        file_path: str,
        line_number: int,
        suggestion: str,
        rule_id: Optional[str] = None,
    ) -> str:
        """
        Format a finding as a compact inline link (for use in lists).
        
        Args:
            issue_type: Type of issue
            file_path: Path to file
            line_number: Line number
            suggestion: Fix suggestion
            rule_id: Optional rule ID
        
        Returns:
            Compact markdown line with Cursor link
        """
        agent_url = self._build_cursor_agent_url(
            issue_type, file_path, line_number, suggestion, rule_id
        )
        
        return f"- `{file_path}:{line_number}` - {issue_type} [🔧 Fix]({agent_url})"
    
    def add_cursor_links_to_findings(
        self,
        findings: List[Dict[str, Any]],
        format_type: str = "full",
    ) -> str:
        """
        Format multiple findings with Cursor links.
        
        Args:
            findings: List of finding dictionaries with keys:
                - file: file path
                - line: line number
                - message: issue description
                - severity: severity level
                - suggestion: fix suggestion (optional)
                - rule_id: rule identifier (optional)
                - code_snippet: code snippet (optional)
            format_type: "full" for detailed format, "inline" for compact list
        
        Returns:
            Formatted markdown string with all findings
        """
        if not findings:
            return ""
        
        formatted_parts = []
        
        for finding in findings:
            file_path = finding.get("file", "unknown")
            line_number = finding.get("line", 1)
            issue_type = finding.get("message", "Issue detected")
            severity = finding.get("severity", "warning")
            suggestion = finding.get("suggestion", "Review and fix this issue")
            rule_id = finding.get("rule_id")
            code_snippet = finding.get("code_snippet", "")
            
            if format_type == "inline":
                formatted = self.format_finding_inline(
                    issue_type=issue_type,
                    file_path=file_path,
                    line_number=line_number,
                    suggestion=suggestion,
                    rule_id=rule_id,
                )
            else:
                formatted = self.format_finding_with_cursor_link(
                    issue_type=issue_type,
                    file_path=file_path,
                    line_number=line_number,
                    code_snippet=code_snippet or f"// Line {line_number}",
                    suggestion=suggestion,
                    severity=severity,
                    rule_id=rule_id,
                )
            
            formatted_parts.append(formatted)
        
        separator = "\n" if format_type == "inline" else "\n---\n\n"
        return separator.join(formatted_parts)
    
    def _build_cursor_agent_url(
        self,
        issue_type: str,
        file_path: str,
        line_number: int,
        suggestion: str,
        rule_id: Optional[str] = None,
    ) -> str:
        """
        Build cursor://agent/prompt URL to open Cursor Agent with pre-filled fix prompt.
        
        This is the key feature that allows one-click fixing with AI assistance!
        """
        rule_info = f"\nRule: {rule_id}" if rule_id else ""
        
        prompt = f"""Fix the following issue in my codebase:

File: {file_path}
Line: {line_number}
Issue: {issue_type}{rule_info}

Suggested fix: {suggestion}

Instructions:
1. First verify the issue still exists at the specified location
2. If it exists, apply the suggested fix
3. Ensure the fix doesn't break existing functionality
4. Follow the project's coding standards"""
        
        encoded_prompt = quote(prompt, safe='')
        return f"cursor://agent/prompt?prompt={encoded_prompt}"
    
    def _build_cursor_open_url(self, file_path: str, line: int) -> str:
        """Build cursor://open URL to just open file at specific line."""
        encoded_path = quote(file_path, safe='')
        return f"cursor://open?file={encoded_path}&line={line}"
    
    def _build_web_url(self, file_path: str, line: int) -> str:
        """Build vscode.dev URL for web-based editing (fallback)."""
        return f"https://vscode.dev/github/{self.org}/{self.repo}/blob/{self.branch}/{file_path}#L{line}"


def add_cursor_links_to_review_text(
    review_text: str,
    org: str,
    repo: str,
    branch: str = "main",
) -> str:
    """
    Post-process review text to add Fix in Cursor links to file references.
    
    This function scans existing review text and adds Cursor links
    where file:line patterns are found.
    
    Args:
        review_text: The original review markdown text
        org: GitHub organization
        repo: Repository name
        branch: Branch name
    
    Returns:
        Review text with Cursor links added
    """
    formatter = CommentFormatter(org, repo, branch)
    
    file_line_pattern = r'`([^`]+\.(ts|tsx|js|jsx|py|php|java|go|rb|rs|cs))`[:\s]+(?:line\s*)?(\d+)'
    
    def add_link(match):
        file_path = match.group(1)
        line_num = int(match.group(3))
        
        open_url = formatter._build_cursor_open_url(file_path, line_num)
        
        return f"{match.group(0)} [📂]({open_url})"
    
    return re.sub(file_line_pattern, add_link, review_text, flags=re.IGNORECASE)
