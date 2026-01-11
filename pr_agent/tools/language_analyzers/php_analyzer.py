"""
PHP Analyzer

Analyzes PHP code for:
- Code style and patterns
- Security issues
- Common anti-patterns
- Best practices
"""

import re
import logging
from .base_analyzer import BaseAnalyzer, AnalyzerFinding, FindingSeverity

logger = logging.getLogger(__name__)


class PHPAnalyzer(BaseAnalyzer):
    """
    Analyzer for PHP files.
    
    Checks for:
    - SQL injection vulnerabilities
    - Deprecated functions
    - Error handling
    - Code style
    """
    
    name = "PHPAnalyzer"
    language = "php"
    
    async def analyze(self, content: str, file_path: str) -> list[AnalyzerFinding]:
        """Analyze PHP content."""
        self.clear_findings()
        
        if not file_path.endswith('.php'):
            return []
        
        lines = content.split('\n')
        
        self._check_sql_injection(content, file_path, lines)
        self._check_deprecated_functions(content, file_path, lines)
        self._check_error_suppression(content, file_path, lines)
        self._check_eval_usage(content, file_path, lines)
        self._check_global_variables(content, file_path, lines)
        self._check_empty_catch(content, file_path, lines)
        self._check_var_dump(content, file_path, lines)
        
        return self.get_findings()
    
    def _check_sql_injection(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for potential SQL injection vulnerabilities."""
        unsafe_patterns = [
            (re.compile(r'mysql_query\s*\(\s*["\'].*\$'), "mysql_query with variable interpolation"),
            (re.compile(r'mysqli_query\s*\([^,]+,\s*["\'].*\$'), "mysqli_query with variable interpolation"),
            (re.compile(r'\$\w+->query\s*\(\s*["\'].*\$'), "PDO/mysqli query with variable interpolation"),
            (re.compile(r'->execute\s*\(\s*\[\s*\$_'), "execute() with unsanitized superglobal"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in unsafe_patterns:
                if pattern.search(line):
                    self.add_finding(
                        rule_id="PHP001",
                        message=f"Potential SQL injection: {description}",
                        severity=FindingSeverity.ERROR,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Use prepared statements with parameterized queries",
                    )
                    break
    
    def _check_deprecated_functions(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for deprecated PHP functions."""
        deprecated = {
            'mysql_connect': 'Use mysqli or PDO instead',
            'mysql_query': 'Use mysqli or PDO instead',
            'mysql_fetch_array': 'Use mysqli or PDO instead',
            'mysql_real_escape_string': 'Use prepared statements instead',
            'ereg': 'Use preg_match instead',
            'eregi': 'Use preg_match with i modifier instead',
            'split': 'Use preg_split or explode instead',
            'create_function': 'Use anonymous functions instead',
            'each': 'Use foreach instead',
        }
        
        for i, line in enumerate(lines, start=1):
            for func, suggestion in deprecated.items():
                if re.search(rf'\b{func}\s*\(', line):
                    self.add_finding(
                        rule_id="PHP002",
                        message=f"Deprecated function '{func}' used.",
                        severity=FindingSeverity.WARNING,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion=suggestion,
                    )
    
    def _check_error_suppression(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for error suppression operator (@)."""
        suppression_pattern = re.compile(r'@\$|\@\w+\s*\(')
        
        for i, line in enumerate(lines, start=1):
            if suppression_pattern.search(line):
                self.add_finding(
                    rule_id="PHP003",
                    message="Error suppression operator (@) used. This hides errors and makes debugging difficult.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Handle errors explicitly with try-catch or proper error checking",
                )
    
    def _check_eval_usage(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for eval() usage."""
        eval_pattern = re.compile(r'\beval\s*\(')
        
        for i, line in enumerate(lines, start=1):
            if eval_pattern.search(line):
                self.add_finding(
                    rule_id="PHP004",
                    message="eval() usage detected. This is a security risk and should be avoided.",
                    severity=FindingSeverity.ERROR,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Refactor to avoid eval(). Consider using proper design patterns.",
                )
    
    def _check_global_variables(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for global variable usage."""
        global_pattern = re.compile(r'\bglobal\s+\$')
        
        for i, line in enumerate(lines, start=1):
            if global_pattern.search(line):
                self.add_finding(
                    rule_id="PHP005",
                    message="Global variable usage detected. This creates tight coupling and makes testing difficult.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Use dependency injection or pass variables as function parameters",
                )
    
    def _check_empty_catch(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for empty catch blocks."""
        in_catch = False
        catch_line = 0
        brace_count = 0
        
        for i, line in enumerate(lines, start=1):
            if 'catch' in line and '(' in line:
                in_catch = True
                catch_line = i
                brace_count = line.count('{') - line.count('}')
            elif in_catch:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    catch_content = '\n'.join(lines[catch_line-1:i])
                    if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', catch_content, re.DOTALL):
                        self.add_finding(
                            rule_id="PHP006",
                            message="Empty catch block detected. Handle or log the exception.",
                            severity=FindingSeverity.ERROR,
                            file_path=file_path,
                            line_start=catch_line,
                            suggestion="Add error handling or logging inside the catch block",
                        )
                    in_catch = False
    
    def _check_var_dump(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for debug functions that shouldn't be in production."""
        debug_functions = ['var_dump', 'print_r', 'var_export', 'debug_print_backtrace']
        
        for i, line in enumerate(lines, start=1):
            for func in debug_functions:
                if re.search(rf'\b{func}\s*\(', line):
                    self.add_finding(
                        rule_id="PHP007",
                        message=f"Debug function '{func}' found. Remove before production.",
                        severity=FindingSeverity.WARNING,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Remove debug function or use proper logging",
                    )
                    break
