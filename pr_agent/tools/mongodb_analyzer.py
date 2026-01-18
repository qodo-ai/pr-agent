"""
MongoDB Analyzer

Analyzes code for MongoDB-related issues:
- Missing index hints
- Regex patterns without anchors (full collection scans)
- Unbounded queries without limit
- Dangerous $where usage
- Missing projections
- Inefficient aggregation pipelines
- findAndModify error handling
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MongoDBFindingSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class MongoDBFinding:
    rule_id: str
    message: str
    severity: MongoDBFindingSeverity
    file_path: str
    line_start: int
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "metadata": self.metadata or {},
        }


class MongoDBAnalyzer:
    """
    Analyzer for MongoDB-related code patterns.

    Detects:
    - Missing index hints on large collection queries
    - $regex without anchor (^) causing full collection scans
    - Unbounded find() without limit()
    - Dangerous $where with JavaScript execution
    - Missing projections (fetching entire documents)
    - Aggregation pipelines without $match first
    - findAndModify without error handling
    """

    def __init__(self):
        self._findings: list[MongoDBFinding] = []

    async def analyze(self, content: str, file_path: str) -> list[MongoDBFinding]:
        if not self._is_mongodb_file(content, file_path):
            return []

        self._findings.clear()
        lines = content.split('\n')

        self._check_missing_index_hint(content, file_path, lines)
        self._check_regex_without_anchor(content, file_path, lines)
        self._check_unbounded_find(content, file_path, lines)
        self._check_where_usage(content, file_path, lines)
        self._check_missing_projection(content, file_path, lines)
        self._check_aggregation_without_match(content, file_path, lines)
        self._check_find_and_modify(content, file_path, lines)

        return self._findings.copy()

    def _is_mongodb_file(self, content: str, file_path: str) -> bool:
        mongodb_indicators = [
            'mongoose',
            'mongodb',
            'MongoClient',
            'Collection',
            '.find(',
            '.findOne(',
            '.aggregate(',
            '.insertOne(',
            '.updateOne(',
            '.deleteOne(',
            '@InjectModel',
            'Model<',
        ]
        return any(indicator in content for indicator in mongodb_indicators)

    def _add_finding(
        self,
        rule_id: str,
        message: str,
        severity: MongoDBFindingSeverity,
        file_path: str,
        line_start: int,
        line_end: int | None = None,
        code_snippet: str | None = None,
        suggestion: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._findings.append(MongoDBFinding(
            rule_id=rule_id,
            message=message,
            severity=severity,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            code_snippet=code_snippet,
            suggestion=suggestion,
            metadata=metadata,
        ))

    def _check_missing_index_hint(self, content: str, file_path: str, lines: list[str]) -> None:
        large_collection_patterns = [
            re.compile(r'\.find\s*\(\s*\{[^}]{50,}\}'),
            re.compile(r'\.find\s*\(\s*\{[^}]*\$or[^}]*\}'),
            re.compile(r'\.find\s*\(\s*\{[^}]*\$and[^}]*\}'),
        ]

        for i, line in enumerate(lines, start=1):
            context = '\n'.join(lines[max(0, i-2):min(len(lines), i+5)])
            for pattern in large_collection_patterns:
                if pattern.search(context) and '.hint(' not in context:
                    self._add_finding(
                        rule_id="MONGO001",
                        message="Complex query without index hint - may cause slow performance on large collections",
                        severity=MongoDBFindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add .hint({ fieldName: 1 }) to use specific index, or verify index exists with explain()",
                    )
                    break

    def _check_regex_without_anchor(self, content: str, file_path: str, lines: list[str]) -> None:
        regex_patterns = [
            re.compile(r'\$regex\s*:\s*[\'"][^\'"\^]'),
            re.compile(r'\$regex\s*:\s*/[^/\^]'),
            re.compile(r'new\s+RegExp\s*\(\s*[\'"][^\'"\^]'),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in regex_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="MONGO002",
                        message="$regex without anchor (^) - causes full collection scan",
                        severity=MongoDBFindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add ^ anchor at start: { $regex: '^pattern' } or use text index for full-text search",
                    )
                    break

    def _check_unbounded_find(self, content: str, file_path: str, lines: list[str]) -> None:
        find_pattern = re.compile(r'\.(find|findMany)\s*\(')

        for i, line in enumerate(lines, start=1):
            if find_pattern.search(line):
                context = '\n'.join(lines[i-1:min(len(lines), i+10)])
                if '.limit(' not in context and '.take(' not in context:
                    if 'findOne' not in line and 'findById' not in line:
                        self._add_finding(
                            rule_id="MONGO003",
                            message="find() without limit() - may return excessive documents",
                            severity=MongoDBFindingSeverity.MEDIUM,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Add .limit(N) to prevent unbounded result sets",
                        )

    def _check_where_usage(self, content: str, file_path: str, lines: list[str]) -> None:
        where_pattern = re.compile(r'\$where\s*:')

        for i, line in enumerate(lines, start=1):
            if where_pattern.search(line):
                self._add_finding(
                    rule_id="MONGO004",
                    message="$where with JavaScript execution - security risk and performance impact",
                    severity=MongoDBFindingSeverity.CRITICAL,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Replace $where with native MongoDB operators ($expr, $match, etc.) for better security and performance",
                )

    def _check_missing_projection(self, content: str, file_path: str, lines: list[str]) -> None:
        find_with_empty_projection = re.compile(r'\.(find|findOne)\s*\(\s*\{[^}]*\}\s*\)')

        for i, line in enumerate(lines, start=1):
            if find_with_empty_projection.search(line):
                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+3)])
                if '.select(' not in context and '.project(' not in context:
                    if ', {' not in line and ',{' not in line:
                        self._add_finding(
                            rule_id="MONGO005",
                            message="Query without projection - fetches entire documents unnecessarily",
                            severity=MongoDBFindingSeverity.LOW,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Add projection to fetch only needed fields: .find(query, { field1: 1, field2: 1 }) or .select('field1 field2')",
                        )

    def _check_aggregation_without_match(self, content: str, file_path: str, lines: list[str]) -> None:
        aggregate_pattern = re.compile(r'\.aggregate\s*\(\s*\[')

        for i, line in enumerate(lines, start=1):
            if aggregate_pattern.search(line):
                context = '\n'.join(lines[i-1:min(len(lines), i+5)])
                pipeline_start = context.find('[')
                if pipeline_start != -1:
                    first_stage = context[pipeline_start:pipeline_start+100]
                    if '$match' not in first_stage and '$geoNear' not in first_stage:
                        self._add_finding(
                            rule_id="MONGO006",
                            message="Aggregation pipeline without $match as first stage - processes entire collection",
                            severity=MongoDBFindingSeverity.MEDIUM,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Add $match as the first pipeline stage to filter documents early and improve performance",
                        )

    def _check_find_and_modify(self, content: str, file_path: str, lines: list[str]) -> None:
        fam_patterns = [
            re.compile(r'\.findAndModify\s*\('),
            re.compile(r'\.findOneAndUpdate\s*\('),
            re.compile(r'\.findOneAndDelete\s*\('),
            re.compile(r'\.findOneAndReplace\s*\('),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in fam_patterns:
                if pattern.search(line):
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+10)])
                    if 'try' not in context and 'catch' not in context and '.catch(' not in context:
                        self._add_finding(
                            rule_id="MONGO007",
                            message="findAndModify/findOneAndUpdate without error handling - race conditions may cause silent failures",
                            severity=MongoDBFindingSeverity.MEDIUM,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Wrap in try/catch or use .catch() to handle potential race condition errors",
                        )
                    break


_analyzer: MongoDBAnalyzer | None = None


def get_mongodb_analyzer() -> MongoDBAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = MongoDBAnalyzer()
    return _analyzer
