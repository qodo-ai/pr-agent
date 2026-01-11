"""
Base Analyzer Framework

Provides the abstract base class for all language-specific analyzers.
Each analyzer should extend BaseAnalyzer and implement the analyze() method.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FindingSeverity(Enum):
    """Severity levels for analyzer findings."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class AnalyzerFinding:
    """
    Represents a single finding from an analyzer.
    
    Attributes:
        rule_id: Unique identifier for the rule that triggered this finding
        message: Human-readable description of the finding
        severity: Severity level of the finding
        file_path: Path to the file where the finding was detected
        line_start: Starting line number (1-indexed)
        line_end: Ending line number (1-indexed, optional)
        code_snippet: Relevant code snippet (optional)
        suggestion: Suggested fix or improvement (optional)
        metadata: Additional context data (optional)
    """
    rule_id: str
    message: str
    severity: FindingSeverity
    file_path: str
    line_start: int
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary for serialization."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }
    
    def to_review_comment(self) -> str:
        """Format finding as a review comment."""
        severity_emoji = {
            FindingSeverity.ERROR: "🔴",
            FindingSeverity.WARNING: "🟡",
            FindingSeverity.INFO: "🔵",
            FindingSeverity.SUGGESTION: "💡",
        }
        
        emoji = severity_emoji.get(self.severity, "")
        comment = f"{emoji} **{self.rule_id}**: {self.message}"
        
        if self.suggestion:
            comment += f"\n\n**Suggestion**: {self.suggestion}"
        
        return comment


class BaseAnalyzer(ABC):
    """
    Abstract base class for language-specific analyzers.
    
    Each analyzer should:
    1. Detect relevant patterns in code
    2. Check for anti-patterns and violations
    3. Return findings with actionable suggestions
    
    Attributes:
        name: Human-readable name of the analyzer
        language: Target language/framework
        enabled: Whether the analyzer is enabled
    """
    
    name: str = "BaseAnalyzer"
    language: str = "unknown"
    enabled: bool = True
    
    def __init__(self):
        self._findings: list[AnalyzerFinding] = []
    
    @abstractmethod
    async def analyze(self, content: str, file_path: str) -> list[AnalyzerFinding]:
        """
        Analyze file content and return findings.
        
        Args:
            content: File content as string
            file_path: Path to the file being analyzed
            
        Returns:
            List of AnalyzerFinding objects
        """
        pass
    
    def add_finding(
        self,
        rule_id: str,
        message: str,
        severity: FindingSeverity,
        file_path: str,
        line_start: int,
        line_end: int | None = None,
        code_snippet: str | None = None,
        suggestion: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a finding to the internal list.
        
        Args:
            rule_id: Unique rule identifier
            message: Description of the finding
            severity: Severity level
            file_path: File path
            line_start: Starting line number
            line_end: Ending line number (optional)
            code_snippet: Code snippet (optional)
            suggestion: Suggested fix (optional)
            metadata: Additional data (optional)
        """
        finding = AnalyzerFinding(
            rule_id=rule_id,
            message=message,
            severity=severity,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            code_snippet=code_snippet,
            suggestion=suggestion,
            metadata=metadata or {},
        )
        self._findings.append(finding)
        logger.debug(
            "Analyzer finding added",
            extra={"context": {
                "analyzer": self.name,
                "rule_id": rule_id,
                "severity": severity.value,
                "file": file_path,
                "line": line_start,
            }}
        )
    
    def get_findings(self) -> list[AnalyzerFinding]:
        """Get all findings from this analyzer."""
        return self._findings.copy()
    
    def clear_findings(self) -> None:
        """Clear all findings."""
        self._findings.clear()
    
    def get_findings_by_severity(self, severity: FindingSeverity) -> list[AnalyzerFinding]:
        """Get findings filtered by severity."""
        return [f for f in self._findings if f.severity == severity]
    
    def has_errors(self) -> bool:
        """Check if there are any error-level findings."""
        return any(f.severity == FindingSeverity.ERROR for f in self._findings)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning-level findings."""
        return any(f.severity == FindingSeverity.WARNING for f in self._findings)
    
    @staticmethod
    def find_line_number(content: str, pattern: str, start_from: int = 0) -> int | None:
        """
        Find the line number where a pattern first appears.
        
        Args:
            content: File content
            pattern: Pattern to search for
            start_from: Line to start searching from (0-indexed)
            
        Returns:
            Line number (1-indexed) or None if not found
        """
        lines = content.split('\n')
        for i, line in enumerate(lines[start_from:], start=start_from + 1):
            if pattern in line:
                return i
        return None
    
    @staticmethod
    def extract_code_snippet(content: str, line_start: int, line_end: int | None = None, context: int = 2) -> str:
        """
        Extract a code snippet with context lines.
        
        Args:
            content: File content
            line_start: Starting line (1-indexed)
            line_end: Ending line (1-indexed, optional)
            context: Number of context lines before/after
            
        Returns:
            Code snippet as string
        """
        lines = content.split('\n')
        end = line_end or line_start
        
        start_idx = max(0, line_start - 1 - context)
        end_idx = min(len(lines), end + context)
        
        return '\n'.join(lines[start_idx:end_idx])
