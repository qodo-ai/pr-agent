"""
SQL Analyzer

Analyzes code for SQL-related issues:
- SQL injection vulnerabilities
- N+1 query patterns
- Missing indexes hints
- Transaction usage
- TypeORM best practices
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SQLFindingSeverity(Enum):
    """Severity levels for SQL findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SQLFinding:
    """Represents a SQL-related finding."""
    rule_id: str
    message: str
    severity: SQLFindingSeverity
    file_path: str
    line_start: int
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion: str | None = None
    metadata: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
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


class SQLAnalyzer:
    """
    Analyzer for SQL-related code patterns.
    
    Detects:
    - SQL injection vulnerabilities
    - N+1 query patterns
    - Missing transaction usage
    - Inefficient query patterns
    - TypeORM anti-patterns
    """
    
    def __init__(self):
        self._findings: list[SQLFinding] = []
    
    async def analyze(self, content: str, file_path: str) -> list[SQLFinding]:
        """
        Analyze file content for SQL issues.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            List of SQL findings
        """
        self._findings.clear()
        lines = content.split('\n')
        
        self._check_sql_injection(content, file_path, lines)
        self._check_n_plus_one(content, file_path, lines)
        self._check_raw_queries(content, file_path, lines)
        self._check_transaction_usage(content, file_path, lines)
        self._check_typeorm_patterns(content, file_path, lines)
        self._check_query_complexity(content, file_path, lines)
        
        return self._findings.copy()
    
    def _add_finding(
        self,
        rule_id: str,
        message: str,
        severity: SQLFindingSeverity,
        file_path: str,
        line_start: int,
        line_end: int | None = None,
        code_snippet: str | None = None,
        suggestion: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a finding to the list."""
        self._findings.append(SQLFinding(
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
    
    def _check_sql_injection(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for SQL injection vulnerabilities."""
        injection_patterns = [
            (re.compile(r'query\s*\(\s*[`\'"].*\$\{'), "Template literal with variable interpolation in query"),
            (re.compile(r'query\s*\(.*\+\s*\w+'), "String concatenation in query"),
            (re.compile(r'execute\s*\(.*\+\s*\w+'), "String concatenation in execute"),
            (re.compile(r'raw\s*\(\s*[`\'"].*\$\{'), "Raw query with variable interpolation"),
            (re.compile(r'createQueryBuilder.*where\s*\(.*\+'), "QueryBuilder with string concatenation"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in injection_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SQL001",
                        message=f"Potential SQL injection: {description}",
                        severity=SQLFindingSeverity.CRITICAL,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Use parameterized queries: query('SELECT * FROM users WHERE id = $1', [userId])",
                    )
                    break
    
    def _check_n_plus_one(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for N+1 query patterns."""
        n_plus_one_patterns = [
            (re.compile(r'for\s*\([^)]+\)\s*\{[^}]*\.find'), "Database query inside for loop"),
            (re.compile(r'\.forEach\s*\([^)]*=>[^}]*\.find'), "Database query inside forEach"),
            (re.compile(r'\.map\s*\([^)]*=>[^}]*\.find'), "Database query inside map"),
            (re.compile(r'for\s*\([^)]+\)\s*\{[^}]*await.*repository'), "Repository call inside for loop"),
            (re.compile(r'\.map\s*\(async[^}]*\.findOne'), "findOne inside async map"),
        ]
        
        for i, line in enumerate(lines, start=1):
            context = '\n'.join(lines[max(0, i-3):min(len(lines), i+5)])
            for pattern, description in n_plus_one_patterns:
                if pattern.search(context):
                    self._add_finding(
                        rule_id="SQL002",
                        message=f"Potential N+1 query: {description}",
                        severity=SQLFindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Use eager loading (relations), batch queries, or QueryBuilder with joins",
                    )
                    break
    
    def _check_raw_queries(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for raw SQL queries that might need attention."""
        raw_query_pattern = re.compile(r'\.query\s*\(\s*[`\'"]')
        
        for i, line in enumerate(lines, start=1):
            if raw_query_pattern.search(line):
                if 'migration' not in file_path.lower():
                    self._add_finding(
                        rule_id="SQL003",
                        message="Raw SQL query detected outside of migrations",
                        severity=SQLFindingSeverity.MEDIUM,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Consider using TypeORM QueryBuilder or repository methods for type safety",
                    )
    
    def _check_transaction_usage(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for missing transaction usage in multi-operation scenarios."""
        save_count = len(re.findall(r'\.save\s*\(', content))
        update_count = len(re.findall(r'\.update\s*\(', content))
        delete_count = len(re.findall(r'\.delete\s*\(', content))
        
        total_writes = save_count + update_count + delete_count
        
        if total_writes >= 2 and 'transaction' not in content.lower() and 'queryRunner' not in content:
            first_write = None
            for i, line in enumerate(lines, start=1):
                if re.search(r'\.(save|update|delete)\s*\(', line):
                    first_write = i
                    break
            
            if first_write:
                self._add_finding(
                    rule_id="SQL004",
                    message=f"Multiple database write operations ({total_writes}) without explicit transaction",
                    severity=SQLFindingSeverity.HIGH,
                    file_path=file_path,
                    line_start=first_write,
                    suggestion="Wrap multiple writes in a transaction: await dataSource.transaction(async (manager) => { ... })",
                    metadata={"write_operations": total_writes},
                )
    
    def _check_typeorm_patterns(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for TypeORM-specific anti-patterns."""
        if 'typeorm' not in content.lower() and '@Entity' not in content:
            return
        
        find_without_relations = re.compile(r'\.find\s*\(\s*\{[^}]*\}\s*\)')
        for i, line in enumerate(lines, start=1):
            if find_without_relations.search(line):
                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+3)])
                if 'relations' not in context and 'select' not in context:
                    self._add_finding(
                        rule_id="SQL005",
                        message="find() without explicit relations or select - may cause lazy loading issues",
                        severity=SQLFindingSeverity.INFO,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Specify relations: find({ relations: ['user', 'orders'] }) or use QueryBuilder",
                    )
        
        synchronize_pattern = re.compile(r'synchronize\s*:\s*true')
        for i, line in enumerate(lines, start=1):
            if synchronize_pattern.search(line):
                self._add_finding(
                    rule_id="SQL006",
                    message="TypeORM synchronize: true detected - dangerous in production",
                    severity=SQLFindingSeverity.CRITICAL,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Use migrations instead of synchronize. Set synchronize: false in production.",
                )
    
    def _check_query_complexity(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for overly complex queries."""
        join_count_pattern = re.compile(r'\.(leftJoin|innerJoin|join)\s*\(')
        
        join_count = len(join_count_pattern.findall(content))
        if join_count > 4:
            first_join = None
            for i, line in enumerate(lines, start=1):
                if join_count_pattern.search(line):
                    first_join = i
                    break
            
            if first_join:
                self._add_finding(
                    rule_id="SQL007",
                    message=f"Complex query with {join_count} joins - may impact performance",
                    severity=SQLFindingSeverity.MEDIUM,
                    file_path=file_path,
                    line_start=first_join,
                    suggestion="Consider breaking into multiple queries or using database views",
                    metadata={"join_count": join_count},
                )
        
        subquery_pattern = re.compile(r'\.subQuery\s*\(')
        nested_count = len(subquery_pattern.findall(content))
        if nested_count > 2:
            self._add_finding(
                rule_id="SQL008",
                message=f"Query with {nested_count} subqueries - consider simplification",
                severity=SQLFindingSeverity.MEDIUM,
                file_path=file_path,
                line_start=1,
                suggestion="Consider using CTEs (WITH clause) or breaking into separate queries",
                metadata={"subquery_count": nested_count},
            )


_analyzer: SQLAnalyzer | None = None


def get_sql_analyzer() -> SQLAnalyzer:
    """Get the global SQL analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SQLAnalyzer()
    return _analyzer
