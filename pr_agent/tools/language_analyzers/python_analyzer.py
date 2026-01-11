"""
Python Analyzer

Analyzes Python code for:
- Code style and patterns
- Type hints
- Common anti-patterns
- Best practices
"""

import re
import logging
from .base_analyzer import BaseAnalyzer, AnalyzerFinding, FindingSeverity

logger = logging.getLogger(__name__)


class PythonAnalyzer(BaseAnalyzer):
    """
    Analyzer for Python files.
    
    Checks for:
    - Type hints usage
    - Function complexity
    - Exception handling
    - Code style
    """
    
    name = "PythonAnalyzer"
    language = "python"
    
    MAX_FUNCTION_LINES = 15
    MAX_FUNCTION_ARGS = 5
    
    async def analyze(self, content: str, file_path: str) -> list[AnalyzerFinding]:
        """Analyze Python content."""
        self.clear_findings()
        
        if not file_path.endswith('.py'):
            return []
        
        lines = content.split('\n')
        
        self._check_type_hints(content, file_path, lines)
        self._check_function_complexity(content, file_path, lines)
        self._check_bare_except(content, file_path, lines)
        self._check_mutable_defaults(content, file_path, lines)
        self._check_print_statements(content, file_path, lines)
        self._check_global_usage(content, file_path, lines)
        self._check_star_imports(content, file_path, lines)
        self._check_assert_in_production(content, file_path, lines)
        
        return self.get_findings()
    
    def _check_type_hints(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for missing type hints in function definitions."""
        func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(([^)]*)\)\s*:')
        typed_pattern = re.compile(r'^\s*def\s+\w+\s*\([^)]*\)\s*->')
        
        for i, line in enumerate(lines, start=1):
            func_match = func_pattern.match(line)
            if func_match:
                func_name = func_match.group(1)
                if func_name.startswith('_') and not func_name.startswith('__'):
                    continue
                
                if not typed_pattern.match(line):
                    self.add_finding(
                        rule_id="PY001",
                        message=f"Function '{func_name}' lacks return type hint.",
                        severity=FindingSeverity.INFO,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion=f"Add return type: def {func_name}(...) -> ReturnType:",
                    )
    
    def _check_function_complexity(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for overly complex functions."""
        func_pattern = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)')
        
        in_function = False
        func_start = 0
        func_name = ""
        func_indent = 0
        
        for i, line in enumerate(lines, start=1):
            match = func_pattern.match(line)
            if match:
                if in_function:
                    func_length = i - func_start
                    if func_length > self.MAX_FUNCTION_LINES:
                        self.add_finding(
                            rule_id="PY002",
                            message=f"Function '{func_name}' is {func_length} lines (max: {self.MAX_FUNCTION_LINES}).",
                            severity=FindingSeverity.WARNING,
                            file_path=file_path,
                            line_start=func_start,
                            line_end=i - 1,
                            suggestion="Break down into smaller functions",
                        )
                
                func_name = match.group(1)
                args = match.group(2)
                func_start = i
                func_indent = len(line) - len(line.lstrip())
                in_function = True
                
                arg_count = len([a for a in args.split(',') if a.strip() and a.strip() != 'self'])
                if arg_count > self.MAX_FUNCTION_ARGS:
                    self.add_finding(
                        rule_id="PY003",
                        message=f"Function '{func_name}' has {arg_count} arguments (max: {self.MAX_FUNCTION_ARGS}).",
                        severity=FindingSeverity.INFO,
                        file_path=file_path,
                        line_start=i,
                        suggestion="Consider using a dataclass or dict for parameters",
                    )
            elif in_function and line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= func_indent and not line.strip().startswith('@'):
                    func_length = i - func_start
                    if func_length > self.MAX_FUNCTION_LINES:
                        self.add_finding(
                            rule_id="PY002",
                            message=f"Function '{func_name}' is {func_length} lines (max: {self.MAX_FUNCTION_LINES}).",
                            severity=FindingSeverity.WARNING,
                            file_path=file_path,
                            line_start=func_start,
                            line_end=i - 1,
                            suggestion="Break down into smaller functions",
                        )
                    in_function = False
    
    def _check_bare_except(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for bare except clauses."""
        bare_except_pattern = re.compile(r'^\s*except\s*:')
        
        for i, line in enumerate(lines, start=1):
            if bare_except_pattern.match(line):
                self.add_finding(
                    rule_id="PY004",
                    message="Bare except clause catches all exceptions including KeyboardInterrupt.",
                    severity=FindingSeverity.ERROR,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Specify exception type: except Exception as e:",
                )
    
    def _check_mutable_defaults(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for mutable default arguments."""
        mutable_default_pattern = re.compile(r'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|\set\(\))')
        
        for i, line in enumerate(lines, start=1):
            if mutable_default_pattern.search(line):
                self.add_finding(
                    rule_id="PY005",
                    message="Mutable default argument detected. This can cause unexpected behavior.",
                    severity=FindingSeverity.ERROR,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Use None as default and create mutable inside function: param=None; if param is None: param = []",
                )
    
    def _check_print_statements(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for print statements (use logging instead)."""
        print_pattern = re.compile(r'\bprint\s*\(')
        
        for i, line in enumerate(lines, start=1):
            if print_pattern.search(line) and 'test' not in file_path.lower():
                self.add_finding(
                    rule_id="PY006",
                    message="print() statement found. Use logging module instead.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Use logger.info(), logger.debug(), etc.",
                )
    
    def _check_global_usage(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for global keyword usage."""
        global_pattern = re.compile(r'^\s*global\s+')
        
        for i, line in enumerate(lines, start=1):
            if global_pattern.match(line):
                self.add_finding(
                    rule_id="PY007",
                    message="Global variable usage detected. This makes code harder to test and maintain.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Pass variables as function arguments or use class attributes",
                )
    
    def _check_star_imports(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for star imports."""
        star_import_pattern = re.compile(r'^\s*from\s+\S+\s+import\s+\*')
        
        for i, line in enumerate(lines, start=1):
            if star_import_pattern.match(line):
                self.add_finding(
                    rule_id="PY008",
                    message="Star import detected. This pollutes namespace and makes dependencies unclear.",
                    severity=FindingSeverity.WARNING,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Import specific names: from module import name1, name2",
                )
    
    def _check_assert_in_production(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for assert statements that may be stripped in production."""
        assert_pattern = re.compile(r'^\s*assert\s+')
        
        if 'test' in file_path.lower():
            return
        
        for i, line in enumerate(lines, start=1):
            if assert_pattern.match(line):
                self.add_finding(
                    rule_id="PY009",
                    message="Assert statement in non-test code. Asserts are stripped with -O flag.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Use explicit if/raise for production validation",
                )
