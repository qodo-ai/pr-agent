"""
Check Run Builder for GitHub Checks API

Utility class to construct GitHub Check Runs with annotations and action buttons
for the "Fix in Cursor" feature.

GitHub Check Runs API Documentation:
- Max 50 annotations per API request
- Max 3 action buttons per check run
- Action button label max 20 characters
- Action button description max 40 characters
- Action button identifier max 20 characters
"""

import base64
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from urllib.parse import quote

from pr_agent.log import get_logger


class AnnotationLevel(str, Enum):
    """GitHub annotation levels."""
    NOTICE = "notice"
    WARNING = "warning"
    FAILURE = "failure"


@dataclass
class Annotation:
    """Represents a single check run annotation."""
    path: str
    start_line: int
    end_line: int
    message: str
    annotation_level: AnnotationLevel = AnnotationLevel.WARNING
    title: str = ""
    raw_details: str = ""
    
    def to_dict(self) -> dict:
        """Convert to GitHub API format."""
        result = {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "annotation_level": self.annotation_level.value,
            "message": self.message[:65535],
        }
        if self.title:
            result["title"] = self.title[:255]
        if self.raw_details:
            result["raw_details"] = self.raw_details[:65535]
        return result


@dataclass 
class ActionButton:
    """Represents a check run action button."""
    label: str
    description: str
    identifier: str
    
    def to_dict(self) -> dict:
        """Convert to GitHub API format."""
        return {
            "label": self.label[:20],
            "description": self.description[:40],
            "identifier": self.identifier[:20],
        }


@dataclass
class CheckRunOutput:
    """Represents the output section of a check run."""
    title: str
    summary: str
    text: str = ""
    annotations: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to GitHub API format."""
        result = {
            "title": self.title[:255],
            "summary": self.summary[:65535],
        }
        if self.text:
            result["text"] = self.text[:65535]
        if self.annotations:
            result["annotations"] = [
                a.to_dict() if isinstance(a, Annotation) else a 
                for a in self.annotations[:50]
            ]
        return result


class CheckRunBuilder:
    """
    Builder class for constructing GitHub Check Runs.
    
    Usage:
        builder = CheckRunBuilder("Workiz PR Review", head_sha)
        builder.set_output("Review Results", "Found 3 issues")
        builder.add_annotation("src/file.ts", 42, "Use const instead of let")
        builder.add_action("Fix in Cursor", "fix_cursor_abc123")
        check_run = builder.build()
        
        # Create the check run
        github_provider.create_check_run(**check_run)
    """
    
    def __init__(self, name: str, head_sha: str):
        """
        Initialize check run builder.
        
        Args:
            name: Name of the check run (e.g., "Workiz PR Review")
            head_sha: SHA of the commit to attach check to
        """
        self.name = name
        self.head_sha = head_sha
        self.status = "completed"
        self.conclusion = "neutral"
        self.output: Optional[CheckRunOutput] = None
        self.actions: list[ActionButton] = []
        self.details_url: Optional[str] = None
        
    def set_status(self, status: str, conclusion: str = None) -> "CheckRunBuilder":
        """Set check run status and conclusion."""
        self.status = status
        if conclusion:
            self.conclusion = conclusion
        return self
        
    def set_output(self, title: str, summary: str, text: str = "") -> "CheckRunBuilder":
        """Set the output section."""
        self.output = CheckRunOutput(title=title, summary=summary, text=text)
        return self
        
    def add_annotation(
        self,
        path: str,
        start_line: int,
        message: str,
        end_line: int = None,
        level: AnnotationLevel = AnnotationLevel.WARNING,
        title: str = "",
        raw_details: str = "",
    ) -> "CheckRunBuilder":
        """
        Add an annotation to the check run.
        
        Args:
            path: File path relative to repo root
            start_line: Starting line number
            message: Annotation message
            end_line: End line (defaults to start_line)
            level: Annotation level (notice, warning, failure)
            title: Short title for the annotation
            raw_details: Additional details
        """
        if not self.output:
            self.set_output("Review Results", "Code review annotations")
            
        annotation = Annotation(
            path=path,
            start_line=start_line,
            end_line=end_line or start_line,
            message=message,
            annotation_level=level,
            title=title,
            raw_details=raw_details,
        )
        self.output.annotations.append(annotation)
        return self
        
    def add_action(
        self,
        label: str,
        identifier: str,
        description: str = "Click to fix",
    ) -> "CheckRunBuilder":
        """
        Add an action button to the check run.
        
        Args:
            label: Button label (max 20 chars)
            identifier: Unique identifier for webhook handling (max 20 chars)
            description: Button description (max 40 chars)
        """
        if len(self.actions) >= 3:
            get_logger().warning("Maximum 3 actions per check run, ignoring additional action")
            return self
            
        action = ActionButton(
            label=label,
            description=description,
            identifier=identifier,
        )
        self.actions.append(action)
        return self
        
    def set_details_url(self, url: str) -> "CheckRunBuilder":
        """Set the details URL for the check run."""
        self.details_url = url
        return self
        
    def build(self) -> dict:
        """
        Build the check run payload for GitHub API.
        
        Returns:
            Dict ready to pass to github_provider.create_check_run()
        """
        result = {
            "name": self.name,
            "head_sha": self.head_sha,
            "status": self.status,
            "conclusion": self.conclusion,
        }
        
        if self.output:
            result["output"] = self.output.to_dict()
            
        if self.actions:
            result["actions"] = [a.to_dict() for a in self.actions]
            
        if self.details_url:
            result["details_url"] = self.details_url
            
        return result


def encode_action_identifier(
    file_path: str,
    line: int,
    issue_type: str = "",
) -> str:
    """
    Encode file/line/issue info into a short identifier for action buttons.
    
    GitHub limits identifiers to 20 characters, so we use a hash.
    
    Args:
        file_path: Path to the file
        line: Line number
        issue_type: Type of issue (optional)
        
    Returns:
        Short identifier string (max 20 chars)
    """
    data = f"{file_path}:{line}:{issue_type}"
    hash_bytes = hashlib.md5(data.encode()).digest()[:6]
    short_hash = base64.urlsafe_b64encode(hash_bytes).decode().rstrip("=")
    return f"fix_{short_hash}"


def decode_action_identifier(identifier: str, context_store: dict) -> Optional[dict]:
    """
    Decode an action identifier back to file/line/issue info.
    
    Since we use hashing, we need a context store to map back.
    The context store should be populated when creating the check run.
    
    Args:
        identifier: The action identifier from the webhook
        context_store: Dict mapping identifiers to context
        
    Returns:
        Dict with file_path, line, issue_type, or None if not found
    """
    return context_store.get(identifier)


def build_cursor_prompt(
    issue_type: str,
    file_path: str,
    line_number: int,
    message: str,
    suggestion: str = "",
    code_context: str = "",
) -> str:
    """
    Build a prompt for Cursor AI to fix an issue.
    
    Args:
        issue_type: Type of issue (e.g., "Use const instead of let")
        file_path: Path to the file
        line_number: Line number of the issue
        message: Description of the issue
        suggestion: Suggested fix
        code_context: Surrounding code context
        
    Returns:
        Formatted prompt string for Cursor AI
    """
    prompt_parts = [
        f"Fix the following code issue:",
        f"",
        f"## Issue: {issue_type}",
        f"",
        f"**File:** {file_path}",
        f"**Line:** {line_number}",
        f"",
        f"**Problem:** {message}",
    ]
    
    if suggestion:
        prompt_parts.extend([
            f"",
            f"**Suggested Fix:** {suggestion}",
        ])
        
    if code_context:
        prompt_parts.extend([
            f"",
            f"**Code Context:**",
            f"```",
            code_context,
            f"```",
        ])
        
    prompt_parts.extend([
        f"",
        f"## Instructions:",
        f"1. First verify this issue still exists at the specified location",
        f"2. Apply the suggested fix or an appropriate solution",
        f"3. Ensure the fix follows the project's coding standards",
        f"4. Check that the fix doesn't break existing functionality",
    ])
    
    return "\n".join(prompt_parts)


def build_cursor_redirect_url(
    base_url: str,
    prompt: str,
    file_path: str = None,
    line: int = None,
) -> str:
    """
    Build a URL that redirects to cursor:// scheme.
    
    Args:
        base_url: Base URL of the PR Agent server
        prompt: The prompt to pass to Cursor
        file_path: Optional file path
        line: Optional line number
        
    Returns:
        HTTPS URL that will redirect to cursor://
    """
    encoded_prompt = quote(prompt, safe="")
    url = f"{base_url}/api/v1/cursor-redirect?prompt={encoded_prompt}"
    
    if file_path:
        url += f"&file={quote(file_path, safe='')}"
    if line:
        url += f"&line={line}"
        
    return url
