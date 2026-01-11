"""
TypeScript/JavaScript Analyzer

Analyzes TypeScript and JavaScript files for:
- Functional programming patterns (immutability, pure functions)
- Variable declarations (const vs let)
- Function size and complexity
- Import/export patterns
- Common anti-patterns
"""

import re
import logging
from .base_analyzer import BaseAnalyzer, AnalyzerFinding, FindingSeverity

logger = logging.getLogger(__name__)


class TypeScriptAnalyzer(BaseAnalyzer):
    """
    Analyzer for TypeScript and JavaScript files.
    
    Checks for Workiz coding standards:
    - Prefer const over let
    - Small functions (<10 lines)
    - Functional programming patterns
    - No inline comments
    - Proper error handling
    """
    
    name = "TypeScriptAnalyzer"
    language = "typescript"
    
    # Configuration
    MAX_FUNCTION_LINES = 10
    MAX_FILE_LINES = 300
    
    async def analyze(self, content: str, file_path: str) -> list[AnalyzerFinding]:
        """Analyze TypeScript/JavaScript content."""
        self.clear_findings()
        
        lines = content.split('\n')
        
        self._check_let_usage(content, file_path, lines)
        self._check_function_size(content, file_path, lines)
        self._check_inline_comments(content, file_path, lines)
        self._check_console_logs(content, file_path, lines)
        self._check_any_type(content, file_path, lines)
        self._check_empty_catch(content, file_path, lines)
        self._check_mutation_patterns(content, file_path, lines)
        self._check_file_size(content, file_path, lines)
        
        return self.get_findings()
    
    def _check_let_usage(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for 'let' declarations that could be 'const'."""
        let_pattern = re.compile(r'^\s*let\s+(\w+)')
        
        for i, line in enumerate(lines, start=1):
            match = let_pattern.search(line)
            if match:
                var_name = match.group(1)
                if not self._is_reassigned(content, var_name, i):
                    self.add_finding(
                        rule_id="TS001",
                        message=f"Variable '{var_name}' is declared with 'let' but never reassigned. Use 'const' instead.",
                        severity=FindingSeverity.WARNING,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion=f"Change 'let {var_name}' to 'const {var_name}'",
                    )
    
    def _is_reassigned(self, content: str, var_name: str, declaration_line: int) -> bool:
        """Check if a variable is reassigned after declaration."""
        lines = content.split('\n')
        reassign_pattern = re.compile(rf'\b{re.escape(var_name)}\s*=(?!=)')
        
        for i, line in enumerate(lines[declaration_line:], start=declaration_line + 1):
            if reassign_pattern.search(line):
                return True
        return False
    
    def _check_function_size(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for functions exceeding the line limit."""
        function_patterns = [
            re.compile(r'^\s*(async\s+)?function\s+(\w+)\s*\('),
            re.compile(r'^\s*(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\('),
            re.compile(r'^\s*(const|let|var)\s+(\w+)\s*=\s*(async\s+)?function'),
            re.compile(r'^\s*(public|private|protected)?\s*(async\s+)?(\w+)\s*\([^)]*\)\s*[:{]'),
        ]
        
        in_function = False
        function_start = 0
        function_name = ""
        brace_count = 0
        
        for i, line in enumerate(lines, start=1):
            if not in_function:
                for pattern in function_patterns:
                    match = pattern.search(line)
                    if match:
                        groups = match.groups()
                        function_name = next((g for g in groups if g and g not in ('async', 'const', 'let', 'var', 'public', 'private', 'protected')), 'anonymous')
                        in_function = True
                        function_start = i
                        brace_count = line.count('{') - line.count('}')
                        break
            else:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    function_length = i - function_start + 1
                    if function_length > self.MAX_FUNCTION_LINES:
                        self.add_finding(
                            rule_id="TS002",
                            message=f"Function '{function_name}' is {function_length} lines long (max: {self.MAX_FUNCTION_LINES}). Consider breaking it into smaller functions.",
                            severity=FindingSeverity.WARNING,
                            file_path=file_path,
                            line_start=function_start,
                            line_end=i,
                            suggestion="Break down into smaller, single-purpose functions",
                            metadata={"function_name": function_name, "lines": function_length},
                        )
                    in_function = False
    
    def _check_inline_comments(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for inline comments (code should be self-documenting)."""
        inline_comment_pattern = re.compile(r'[^:\/]\/\/(?!\s*@ts-|eslint-|prettier-)')
        
        for i, line in enumerate(lines, start=1):
            if inline_comment_pattern.search(line) and not line.strip().startswith('//'):
                self.add_finding(
                    rule_id="TS003",
                    message="Inline comment detected. Code should be self-documenting with clear variable and function names.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Remove the comment and make the code more self-explanatory",
                )
    
    def _check_console_logs(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for console.log statements that should use structured logging."""
        console_pattern = re.compile(r'console\.(log|warn|error|info|debug)\s*\(')
        
        for i, line in enumerate(lines, start=1):
            if console_pattern.search(line):
                self.add_finding(
                    rule_id="TS004",
                    message="console.log detected. Use structured logging (e.g., WorkizLogger) instead.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Replace with this.logger.log('message', { context }) or WorkizLogger",
                )
    
    def _check_any_type(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for 'any' type usage in TypeScript."""
        if not file_path.endswith('.ts') and not file_path.endswith('.tsx'):
            return
        
        any_pattern = re.compile(r':\s*any\b|<any>|as\s+any\b')
        
        for i, line in enumerate(lines, start=1):
            if any_pattern.search(line):
                self.add_finding(
                    rule_id="TS005",
                    message="Usage of 'any' type detected. Use specific types for better type safety.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Replace 'any' with a specific type or 'unknown' if the type is truly unknown",
                )
    
    def _check_empty_catch(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for empty catch blocks."""
        empty_catch_pattern = re.compile(r'catch\s*\([^)]*\)\s*{\s*}')
        
        for i, line in enumerate(lines, start=1):
            if empty_catch_pattern.search(line):
                self.add_finding(
                    rule_id="TS006",
                    message="Empty catch block detected. Handle or log the error properly.",
                    severity=FindingSeverity.ERROR,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Add error handling or logging inside the catch block",
                )
    
    def _check_mutation_patterns(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for array/object mutation patterns."""
        mutation_patterns = [
            (re.compile(r'\.push\s*\('), "Array.push() mutates the array. Consider using spread operator [...arr, newItem]"),
            (re.compile(r'\.splice\s*\('), "Array.splice() mutates the array. Consider using filter() or slice()"),
            (re.compile(r'\.pop\s*\('), "Array.pop() mutates the array. Consider using slice(0, -1)"),
            (re.compile(r'\.shift\s*\('), "Array.shift() mutates the array. Consider using slice(1)"),
            (re.compile(r'\.unshift\s*\('), "Array.unshift() mutates the array. Consider using spread operator [newItem, ...arr]"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, message in mutation_patterns:
                if pattern.search(line):
                    self.add_finding(
                        rule_id="TS007",
                        message=message,
                        severity=FindingSeverity.INFO,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Use immutable array operations for functional programming style",
                    )
                    break
    
    def _check_file_size(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check if file exceeds recommended size."""
        if len(lines) > self.MAX_FILE_LINES:
            self.add_finding(
                rule_id="TS008",
                message=f"File has {len(lines)} lines (recommended max: {self.MAX_FILE_LINES}). Consider splitting into smaller modules.",
                severity=FindingSeverity.INFO,
                file_path=file_path,
                line_start=1,
                suggestion="Split the file into smaller, focused modules",
                metadata={"lines": len(lines)},
            )
