"""
Inline Comment Formatter for Bugbot-Style Review Comments

Formats individual review comments in the style of Cursor Bugbot:
- Bold title
- Severity badge
- Detailed description
- Suggested fix (optional)
- "Fix in Cursor" and "Fix in Web" action buttons

These comments appear inline on specific code lines in both the
"Conversation" tab and "Files Changed" tab of GitHub PRs.
"""

from urllib.parse import quote
from typing import Optional


def format_inline_comment(
    title: str,
    severity: str,
    description: str,
    file_path: str,
    line: int,
    suggestion: str = "",
    code_snippet: str = "",
    cursor_redirect_url: str = "",
    org: str = "",
    repo: str = "",
    branch: str = "main",
    rule_id: str = "",
    pr_number: Optional[int] = None,
    pr_url: Optional[str] = None,
    finding_id: Optional[str] = None,
) -> str:
    """
    Format a single inline review comment matching the AI suggestion style.
    
    This produces the same visual format as format_suggestion_comment() for
    consistency across all inline comments (static analyzer and AI suggestions).
    
    Args:
        title: Issue title (e.g., "Use const instead of let")
        severity: Severity level - "High", "Medium", or "Low"
        description: Detailed explanation of the issue
        file_path: Path to the file relative to repo root
        line: Line number where the issue was found
        suggestion: Suggested fix text (optional)
        code_snippet: Problematic code snippet (optional)
        cursor_redirect_url: Base URL for cursor redirect service
        org: GitHub organization name
        repo: Repository name
        branch: Branch name (default: "main")
        rule_id: Rule identifier (e.g., "TS001", "NEST002")
        pr_number: PR number (for tracking)
        pr_url: Full PR URL (for tracking)
        finding_id: Unique finding ID (for tracking)
    
    Returns:
        Formatted markdown string for the comment body
    """
    body_parts = []
    
    title_text = f"[{rule_id}] {title}" if rule_id else title
    body_parts.append(f"**{title_text}**")
    
    severity_normalized = _normalize_severity(severity)
    body_parts.append(f"\n*{severity_normalized} Severity*")
    
    body_parts.append(f"\n{description}")
    
    if code_snippet or suggestion:
        ext = file_path.split(".")[-1] if "." in file_path else ""
        lang = _get_language_for_extension(ext)
        
        body_parts.append("\n<details>")
        body_parts.append("<summary>Show suggested change</summary>")
        body_parts.append("")
        
        if code_snippet:
            body_parts.append("**Current:**")
            body_parts.append(f"```{lang}")
            body_parts.append(code_snippet.strip())
            body_parts.append("```")
            body_parts.append("")
        
        if suggestion:
            body_parts.append("**Suggested:**")
            body_parts.append(f"```{lang}")
            body_parts.append(suggestion.strip())
            body_parts.append("```")
        
        body_parts.append("</details>")
    
    buttons = _build_action_buttons(
        title=title,
        file_path=file_path,
        line=line,
        description=description,
        suggestion=suggestion,
        cursor_redirect_url=cursor_redirect_url,
        org=org,
        repo=repo,
        branch=branch,
        rule_id=rule_id,
        comment_type="static_analyzer",
        severity=severity_normalized,
        pr_number=pr_number,
        pr_url=pr_url,
        finding_id=finding_id,
    )
    if buttons:
        body_parts.append(f"\n{' | '.join(buttons.split(' | '))}")
    
    return "\n".join(body_parts)


def _normalize_severity(severity: str) -> str:
    """Normalize severity string to proper case."""
    severity_lower = severity.lower().strip()
    severity_map = {
        "high": "High",
        "critical": "High",
        "error": "High",
        "failure": "High",
        "medium": "Medium",
        "warning": "Medium",
        "low": "Low",
        "notice": "Low",
        "info": "Low",
    }
    return severity_map.get(severity_lower, "Medium")


def _build_action_buttons(
    title: str,
    file_path: str,
    line: int,
    description: str,
    suggestion: str,
    cursor_redirect_url: str,
    org: str,
    repo: str,
    branch: str,
    rule_id: str,
    comment_type: str = "static_analyzer",
    severity: str = "Medium",
    pr_number: Optional[int] = None,
    pr_url: Optional[str] = None,
    finding_id: Optional[str] = None,
) -> str:
    """Build the action buttons markdown."""
    buttons = []
    
    if cursor_redirect_url:
        prompt = _build_cursor_prompt(
            title=title,
            file_path=file_path,
            line=line,
            description=description,
            suggestion=suggestion,
            rule_id=rule_id,
        )
        encoded_prompt = quote(prompt, safe="")
        cursor_url = f"{cursor_redirect_url}?prompt={encoded_prompt}&file={quote(file_path, safe='')}&line={line}"
        
        if org and repo:
            cursor_url += f"&repository={quote(f'{org}/{repo}', safe='')}"
        if pr_number:
            cursor_url += f"&pr_number={pr_number}"
        if pr_url:
            cursor_url += f"&pr_url={quote(pr_url, safe='')}"
        cursor_url += f"&comment_type={quote(comment_type, safe='')}"
        cursor_url += f"&severity={quote(severity, safe='')}"
        if finding_id:
            cursor_url += f"&finding_id={quote(finding_id, safe='')}"
        
        buttons.append(f"[🔧 Fix in Cursor]({cursor_url})")
    
    if org and repo:
        vscode_url = f"https://vscode.dev/github/{org}/{repo}/blob/{branch}/{file_path}#L{line}"
        buttons.append(f"[↗ Fix in Web]({vscode_url})")
    
    return " | ".join(buttons)


def _build_cursor_prompt(
    title: str,
    file_path: str,
    line: int,
    description: str,
    suggestion: str,
    rule_id: str = "",
) -> str:
    """Build the prompt text for Cursor AI agent."""
    rule_info = f" [{rule_id}]" if rule_id else ""
    
    prompt_parts = [
        f"Fix the following code review issue:{rule_info}",
        "",
        f"## Issue: {title}",
        "",
        f"**File:** {file_path}",
        f"**Line:** {line}",
        "",
        f"**Problem:** {description}",
    ]
    
    if suggestion:
        prompt_parts.extend([
            "",
            f"**Suggested Fix:** {suggestion}",
        ])
    
    prompt_parts.extend([
        "",
        "## Instructions:",
        "1. First verify this issue exists at the specified location",
        "2. Apply the suggested fix or an appropriate solution",
        "3. Ensure the fix follows project coding standards",
        "4. Check that the fix doesn't break existing functionality",
    ])
    
    return "\n".join(prompt_parts)


def format_suggestion_comment(
    summary: str,
    description: str,
    file_path: str,
    line_start: int,
    line_end: int,
    existing_code: str = "",
    improved_code: str = "",
    label: str = "",
    cursor_redirect_url: str = "",
    org: str = "",
    repo: str = "",
    branch: str = "main",
    pr_number: Optional[int] = None,
    pr_url: Optional[str] = None,
    suggestion_id: Optional[str] = None,
) -> str:
    """
    Format a code suggestion as an inline comment.
    
    Args:
        summary: One-sentence summary of the suggestion
        description: Detailed explanation
        file_path: Path to the file
        line_start: Starting line number
        line_end: Ending line number
        existing_code: Current code snippet
        improved_code: Suggested improved code
        label: Category label (e.g., "enhancement", "best_practice")
        cursor_redirect_url: Base URL for cursor redirect service
        org: GitHub organization name
        repo: Repository name
        branch: Branch name
        pr_number: PR number (for tracking)
        pr_url: Full PR URL (for tracking)
        suggestion_id: Unique suggestion ID (for tracking)
    
    Returns:
        Formatted markdown string for the suggestion comment
    """
    body_parts = []
    
    body_parts.append(f"**{summary}**")
    
    if label:
        label_display = label.replace("_", " ").title()
        body_parts.append(f"\n*{label_display}*")
    
    body_parts.append(f"\n{description}")
    
    if existing_code and improved_code:
        ext = file_path.split(".")[-1] if "." in file_path else ""
        lang = _get_language_for_extension(ext)
        
        body_parts.append("\n<details>")
        body_parts.append("<summary>Show suggested change</summary>")
        body_parts.append("")
        body_parts.append("**Current:**")
        body_parts.append(f"```{lang}")
        body_parts.append(existing_code.strip())
        body_parts.append("```")
        body_parts.append("")
        body_parts.append("**Suggested:**")
        body_parts.append(f"```{lang}")
        body_parts.append(improved_code.strip())
        body_parts.append("```")
        body_parts.append("</details>")
    
    buttons = []
    if cursor_redirect_url:
        prompt = _build_suggestion_prompt(
            summary=summary,
            description=description,
            file_path=file_path,
            line_start=line_start,
            existing_code=existing_code,
            improved_code=improved_code,
        )
        encoded_prompt = quote(prompt, safe="")
        cursor_url = f"{cursor_redirect_url}?prompt={encoded_prompt}&file={quote(file_path, safe='')}&line={line_start}"
        
        if org and repo:
            cursor_url += f"&repository={quote(f'{org}/{repo}', safe='')}"
        if pr_number:
            cursor_url += f"&pr_number={pr_number}"
        if pr_url:
            cursor_url += f"&pr_url={quote(pr_url, safe='')}"
        cursor_url += "&comment_type=ai_suggestion"
        severity = _label_to_severity(label)
        cursor_url += f"&severity={quote(severity, safe='')}"
        if suggestion_id:
            cursor_url += f"&finding_id={quote(suggestion_id, safe='')}"
        
        buttons.append(f"[🔧 Fix in Cursor]({cursor_url})")
    
    if org and repo:
        vscode_url = f"https://vscode.dev/github/{org}/{repo}/blob/{branch}/{file_path}#L{line_start}"
        buttons.append(f"[↗ Fix in Web]({vscode_url})")
    
    if buttons:
        body_parts.append(f"\n{' | '.join(buttons)}")
    
    return "\n".join(body_parts)


def _label_to_severity(label: str) -> str:
    """Map suggestion label to severity level."""
    label_lower = label.lower() if label else ""
    if "security" in label_lower or "bug" in label_lower or "error" in label_lower:
        return "High"
    if "performance" in label_lower or "best_practice" in label_lower:
        return "Medium"
    return "Low"


def _build_suggestion_prompt(
    summary: str,
    description: str,
    file_path: str,
    line_start: int,
    existing_code: str,
    improved_code: str,
) -> str:
    """Build the prompt for a code suggestion."""
    prompt_parts = [
        "Apply the following code suggestion from a PR review:",
        "",
        f"## Suggestion: {summary}",
        "",
        f"**File:** {file_path}",
        f"**Line:** {line_start}",
        "",
        f"**Description:** {description}",
    ]
    
    if existing_code:
        prompt_parts.extend([
            "",
            "**Current code:**",
            "```",
            existing_code.strip(),
            "```",
        ])
    
    if improved_code:
        prompt_parts.extend([
            "",
            "**Suggested improvement:**",
            "```",
            improved_code.strip(),
            "```",
        ])
    
    prompt_parts.extend([
        "",
        "## Instructions:",
        "1. First verify this code location is correct",
        "2. Review the suggested changes carefully",
        "3. Apply the changes if they make sense",
        "4. Ensure the fix doesn't break existing functionality",
        "5. Follow the project's coding standards",
    ])
    
    return "\n".join(prompt_parts)


def _get_language_for_extension(ext: str) -> str:
    """Map file extension to language for code blocks."""
    extension_map = {
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "py": "python",
        "php": "php",
        "rb": "ruby",
        "go": "go",
        "java": "java",
        "cs": "csharp",
        "cpp": "cpp",
        "c": "c",
        "rs": "rust",
        "sql": "sql",
        "sh": "bash",
        "bash": "bash",
        "yaml": "yaml",
        "yml": "yaml",
        "json": "json",
        "md": "markdown",
        "html": "html",
        "css": "css",
        "scss": "scss",
    }
    return extension_map.get(ext.lower(), "")
