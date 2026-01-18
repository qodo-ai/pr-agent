"""
Elasticsearch Analyzer

Analyzes code for Elasticsearch-related issues:
- Leading wildcard queries (slow)
- Deep pagination (from > 10000)
- Missing size parameter
- match_all without size limit
- Script queries with user input
- Wildcard index patterns in production
- Missing timeout on search requests
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ESFindingSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ESFinding:
    rule_id: str
    message: str
    severity: ESFindingSeverity
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


class ElasticsearchAnalyzer:
    """
    Analyzer for Elasticsearch-related code patterns.

    Detects:
    - Leading wildcard queries (*term) - very slow
    - Deep pagination (from > 10000) - hits max_result_window
    - Missing size parameter - may not return expected results
    - match_all without size limit - returns entire index
    - Script queries with user input - security risk
    - Wildcard index patterns in production
    - Missing timeout on search requests
    """

    def __init__(self):
        self._findings: list[ESFinding] = []

    async def analyze(self, content: str, file_path: str) -> list[ESFinding]:
        if not self._is_elasticsearch_file(content, file_path):
            return []

        self._findings.clear()
        lines = content.split('\n')

        self._check_leading_wildcard(content, file_path, lines)
        self._check_deep_pagination(content, file_path, lines)
        self._check_missing_size(content, file_path, lines)
        self._check_match_all_without_size(content, file_path, lines)
        self._check_script_queries(content, file_path, lines)
        self._check_wildcard_index(content, file_path, lines)
        self._check_missing_timeout(content, file_path, lines)

        return self._findings.copy()

    def _is_elasticsearch_file(self, content: str, file_path: str) -> bool:
        es_indicators = [
            'elasticsearch',
            'ElasticsearchService',
            '@elastic/elasticsearch',
            'Client',
            '.search(',
            '.index(',
            '.bulk(',
            '.msearch(',
            'SearchRequest',
            'QueryBuilder',
            'bool_query',
            'must_match',
        ]
        return any(indicator in content for indicator in es_indicators)

    def _add_finding(
        self,
        rule_id: str,
        message: str,
        severity: ESFindingSeverity,
        file_path: str,
        line_start: int,
        line_end: int | None = None,
        code_snippet: str | None = None,
        suggestion: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._findings.append(ESFinding(
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

    def _check_leading_wildcard(self, content: str, file_path: str, lines: list[str]) -> None:
        wildcard_patterns = [
            re.compile(r'wildcard\s*:\s*[\'"]?\*'),
            re.compile(r'query_string\s*.*\*\w+'),
            re.compile(r'value\s*:\s*[\'\"]\*'),
            re.compile(r'prefix\s*:\s*[\'\"]\*'),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in wildcard_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="ES001",
                        message="Leading wildcard query (*term) - causes full index scan, extremely slow",
                        severity=ESFindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Use prefix query without leading wildcard, or consider ngram tokenizer for partial matching",
                    )
                    break

    def _check_deep_pagination(self, content: str, file_path: str, lines: list[str]) -> None:
        from_patterns = [
            re.compile(r'from\s*:\s*(\d+)'),
            re.compile(r'[\'"]from[\'"]\s*:\s*(\d+)'),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in from_patterns:
                match = pattern.search(line)
                if match:
                    from_value = int(match.group(1))
                    if from_value > 10000:
                        self._add_finding(
                            rule_id="ES002",
                            message=f"Deep pagination (from: {from_value}) - exceeds default max_result_window (10000)",
                            severity=ESFindingSeverity.HIGH,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Use search_after for deep pagination, or scroll API for bulk exports",
                            metadata={"from_value": from_value},
                        )
                        break

    def _check_missing_size(self, content: str, file_path: str, lines: list[str]) -> None:
        search_pattern = re.compile(r'\.search\s*\(')

        for i, line in enumerate(lines, start=1):
            if search_pattern.search(line):
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+10)])
                if 'size' not in context and 'limit' not in context:
                    self._add_finding(
                        rule_id="ES003",
                        message="Search query without explicit size - defaults to 10, may not be intended",
                        severity=ESFindingSeverity.LOW,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add explicit size parameter to clarify intent: { size: 100 }",
                    )

    def _check_match_all_without_size(self, content: str, file_path: str, lines: list[str]) -> None:
        match_all_patterns = [
            re.compile(r'match_all\s*:\s*\{\s*\}'),
            re.compile(r'[\'"]match_all[\'"]\s*:\s*\{\s*\}'),
            re.compile(r'matchAll\s*\(\s*\)'),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in match_all_patterns:
                if pattern.search(line):
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+10)])
                    if 'size' not in context:
                        self._add_finding(
                            rule_id="ES004",
                            message="match_all query without size limit - may attempt to return entire index",
                            severity=ESFindingSeverity.MEDIUM,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Add size limit to match_all queries: { size: 1000, query: { match_all: {} } }",
                        )
                    break

    def _check_script_queries(self, content: str, file_path: str, lines: list[str]) -> None:
        script_patterns = [
            re.compile(r'script\s*:\s*\{[^}]*source\s*:'),
            re.compile(r'script_score\s*:'),
            re.compile(r'script_fields\s*:'),
        ]

        user_input_patterns = [
            re.compile(r'\$\{'),
            re.compile(r'\+\s*\w+'),
            re.compile(r'params\.\w+'),
            re.compile(r'req\.(body|query|params)'),
        ]

        for i, line in enumerate(lines, start=1):
            for script_pattern in script_patterns:
                if script_pattern.search(line):
                    context = '\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
                    for user_pattern in user_input_patterns:
                        if user_pattern.search(context):
                            self._add_finding(
                                rule_id="ES005",
                                message="Script query with potential user input - script injection vulnerability",
                                severity=ESFindingSeverity.CRITICAL,
                                file_path=file_path,
                                line_start=i,
                                code_snippet=line.strip(),
                                suggestion="Use parameterized scripts with params object, never concatenate user input into scripts",
                            )
                            break

    def _check_wildcard_index(self, content: str, file_path: str, lines: list[str]) -> None:
        index_wildcard_patterns = [
            re.compile(r'index\s*:\s*[\'"][^\'"]*\*[^\'"]*[\'"]'),
            re.compile(r'indices\s*:\s*\[[^\]]*\*[^\]]*\]'),
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in index_wildcard_patterns:
                if pattern.search(line):
                    context = '\n'.join(lines[max(0, i-5):min(len(lines), i+5)])
                    if 'test' not in context.lower() and 'dev' not in context.lower():
                        self._add_finding(
                            rule_id="ES006",
                            message="Wildcard index pattern (index-*) - may query unintended indices in production",
                            severity=ESFindingSeverity.MEDIUM,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Use explicit index names in production, or aliases for controlled multi-index access",
                        )
                        break

    def _check_missing_timeout(self, content: str, file_path: str, lines: list[str]) -> None:
        search_pattern = re.compile(r'\.search\s*\(')

        search_count = 0
        for i, line in enumerate(lines, start=1):
            if search_pattern.search(line):
                search_count += 1
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+10)])
                if 'timeout' not in context and 'requestTimeout' not in context:
                    if search_count <= 2:
                        self._add_finding(
                            rule_id="ES007",
                            message="Search request without timeout - long-running queries may block resources",
                            severity=ESFindingSeverity.LOW,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Add timeout parameter: { timeout: '30s' } to prevent runaway queries",
                        )


_analyzer: ElasticsearchAnalyzer | None = None


def get_elasticsearch_analyzer() -> ElasticsearchAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = ElasticsearchAnalyzer()
    return _analyzer
