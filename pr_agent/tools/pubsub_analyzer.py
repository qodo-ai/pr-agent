"""
PubSub Analyzer

Analyzes code for Google Cloud PubSub-related issues:
- Missing @PubSubAsyncAcknowledge decorator
- Synchronous handlers (should be async)
- Missing error handling in event handlers
- Publishing without topic validation
- Large payload serialization
- Missing retry logic for publish failures
- Handler without proper logging
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PubSubFindingSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PubSubFinding:
    rule_id: str
    message: str
    severity: PubSubFindingSeverity
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


class PubSubAnalyzer:
    """
    Analyzer for Google Cloud PubSub-related code patterns.

    Detects:
    - Missing @PubSubAsyncAcknowledge decorator - message loss risk
    - Synchronous handlers - should be async for proper acknowledgment
    - Missing error handling in event handlers
    - Publishing without topic validation
    - Large payload serialization (>1MB warning)
    - Missing retry logic for publish failures
    - Handler without proper logging
    """

    def __init__(self):
        self._findings: list[PubSubFinding] = []

    async def analyze(self, content: str, file_path: str) -> list[PubSubFinding]:
        if not self._is_pubsub_file(content, file_path):
            return []

        self._findings.clear()
        lines = content.split('\n')

        self._check_missing_async_acknowledge(content, file_path, lines)
        self._check_synchronous_handler(content, file_path, lines)
        self._check_missing_error_handling(content, file_path, lines)
        self._check_publish_validation(content, file_path, lines)
        self._check_large_payload(content, file_path, lines)
        self._check_missing_retry_logic(content, file_path, lines)
        self._check_handler_logging(content, file_path, lines)

        return self._findings.copy()

    def _is_pubsub_file(self, content: str, file_path: str) -> bool:
        pubsub_indicators = [
            '@PubSubTopic',
            '@PubSubEvent',
            'PubSubAsyncAcknowledge',
            '@algoan/pubsub',
            '@workiz/pubsub',
            'GCPubSubServer',
            'pubsub-decorator',
            '.publish(',
            'PubSub',
            'EmittedMessage',
        ]
        return any(indicator in content for indicator in pubsub_indicators)

    def _add_finding(
        self,
        rule_id: str,
        message: str,
        severity: PubSubFindingSeverity,
        file_path: str,
        line_start: int,
        line_end: int | None = None,
        code_snippet: str | None = None,
        suggestion: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._findings.append(PubSubFinding(
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

    def _check_missing_async_acknowledge(self, content: str, file_path: str, lines: list[str]) -> None:
        pubsub_event_pattern = re.compile(r'@PubSubEvent\s*\(')
        async_ack_pattern = re.compile(r'@PubSubAsyncAcknowledge')

        for i, line in enumerate(lines, start=1):
            if pubsub_event_pattern.search(line):
                context_before = '\n'.join(lines[max(0, i-5):i])
                if not async_ack_pattern.search(context_before):
                    self._add_finding(
                        rule_id="PUBSUB001",
                        message="Missing @PubSubAsyncAcknowledge decorator - messages may be lost if handler fails",
                        severity=PubSubFindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add @PubSubAsyncAcknowledge decorator before @PubSubEvent to ensure proper message acknowledgment",
                    )

    def _check_synchronous_handler(self, content: str, file_path: str, lines: list[str]) -> None:
        pubsub_decorator_pattern = re.compile(r'@PubSub(Topic|Event|AsyncAcknowledge)')

        i = 0
        while i < len(lines):
            line = lines[i]
            if pubsub_decorator_pattern.search(line):
                for j in range(i + 1, min(len(lines), i + 10)):
                    method_line = lines[j]
                    if re.search(r'(public|private|protected)?\s*(on|handle)\w+\s*\(', method_line):
                        if 'async' not in method_line:
                            self._add_finding(
                                rule_id="PUBSUB002",
                                message="Synchronous PubSub handler - should be async for proper error handling and acknowledgment",
                                severity=PubSubFindingSeverity.HIGH,
                                file_path=file_path,
                                line_start=j + 1,
                                code_snippet=method_line.strip(),
                                suggestion="Change handler to async: public async onEventName(...): Promise<void>",
                            )
                        break
            i += 1

    def _check_missing_error_handling(self, content: str, file_path: str, lines: list[str]) -> None:
        pubsub_handler_pattern = re.compile(r'(public|private)?\s*async\s+(on|handle)\w+.*PubSubPayload')

        for i, line in enumerate(lines, start=1):
            if pubsub_handler_pattern.search(line):
                brace_count = 0
                handler_content = []
                for j in range(i - 1, min(len(lines), i + 50)):
                    handler_content.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count <= 0 and j > i:
                        break

                handler_text = '\n'.join(handler_content)
                if 'try' not in handler_text and 'catch' not in handler_text:
                    self._add_finding(
                        rule_id="PUBSUB003",
                        message="PubSub handler without try/catch - unhandled errors may cause message redelivery loops",
                        severity=PubSubFindingSeverity.MEDIUM,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Wrap handler logic in try/catch with proper error logging",
                    )

    def _check_publish_validation(self, content: str, file_path: str, lines: list[str]) -> None:
        publish_pattern = re.compile(r'\.publish\s*\(')

        for i, line in enumerate(lines, start=1):
            if publish_pattern.search(line):
                context = '\n'.join(lines[max(0, i-5):min(len(lines), i+3)])
                if 'topic' not in context.lower() and 'TOPIC' not in context:
                    if 'validate' not in context.lower() and 'check' not in context.lower():
                        self._add_finding(
                            rule_id="PUBSUB004",
                            message="Publishing without apparent topic validation - may publish to wrong topic",
                            severity=PubSubFindingSeverity.MEDIUM,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Verify topic name from environment variable or config before publishing",
                        )

    def _check_large_payload(self, content: str, file_path: str, lines: list[str]) -> None:
        stringify_publish_pattern = re.compile(r'JSON\.stringify\s*\([^)]*\)\s*.*publish|publish.*JSON\.stringify')
        buffer_pattern = re.compile(r'Buffer\.(from|alloc)\s*\([^)]*\d{6,}')

        for i, line in enumerate(lines, start=1):
            if stringify_publish_pattern.search(line) or buffer_pattern.search(line):
                context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                if 'compress' not in context.lower() and 'gzip' not in context.lower():
                    self._add_finding(
                        rule_id="PUBSUB005",
                        message="Large payload serialization detected - PubSub has 10MB limit, consider compression",
                        severity=PubSubFindingSeverity.LOW,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Consider compressing large payloads or storing in GCS and publishing reference",
                    )

    def _check_missing_retry_logic(self, content: str, file_path: str, lines: list[str]) -> None:
        publish_pattern = re.compile(r'\.publish\s*\(')

        for i, line in enumerate(lines, start=1):
            if publish_pattern.search(line):
                context = '\n'.join(lines[max(0, i-10):min(len(lines), i+10)])
                has_retry = any(kw in context.lower() for kw in ['retry', 'attempt', 'backoff', 'while', 'for'])
                has_error_handling = 'catch' in context or '.catch(' in context

                if not has_retry and not has_error_handling:
                    self._add_finding(
                        rule_id="PUBSUB006",
                        message="Publish without retry logic - transient failures will cause message loss",
                        severity=PubSubFindingSeverity.MEDIUM,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add retry logic with exponential backoff, or use try/catch with error handling",
                    )

    def _check_handler_logging(self, content: str, file_path: str, lines: list[str]) -> None:
        pubsub_handler_pattern = re.compile(r'(public|private)?\s*async\s+(on|handle)\w+.*PubSubPayload')

        for i, line in enumerate(lines, start=1):
            if pubsub_handler_pattern.search(line):
                brace_count = 0
                handler_content = []
                for j in range(i - 1, min(len(lines), i + 30)):
                    handler_content.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count <= 0 and j > i:
                        break

                handler_text = '\n'.join(handler_content)
                has_logging = any(kw in handler_text for kw in ['logger.', 'this.logger', 'console.log', 'log('])

                if not has_logging:
                    self._add_finding(
                        rule_id="PUBSUB007",
                        message="PubSub handler without logging - difficult to debug message processing issues",
                        severity=PubSubFindingSeverity.LOW,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add logging at handler entry: this.logger.log('Received event', { eventData })",
                    )


_analyzer: PubSubAnalyzer | None = None


def get_pubsub_analyzer() -> PubSubAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = PubSubAnalyzer()
    return _analyzer
