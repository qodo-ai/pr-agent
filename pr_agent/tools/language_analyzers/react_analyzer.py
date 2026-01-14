"""
React Analyzer

Analyzes React component patterns and best practices:
- Component structure (functional vs class)
- Hooks usage
- Props handling
- State management
- Performance patterns
"""

import re
import logging
from .base_analyzer import BaseAnalyzer, AnalyzerFinding, FindingSeverity

logger = logging.getLogger(__name__)


class ReactAnalyzer(BaseAnalyzer):
    """
    Analyzer for React components.
    
    Checks for:
    - Functional components over class components
    - Proper hooks usage
    - Props destructuring
    - Memo/useCallback optimization
    - Key prop in lists
    """
    
    name = "ReactAnalyzer"
    language = "react"
    
    async def analyze(self, content: str, file_path: str) -> list[AnalyzerFinding]:
        """Analyze React component content."""
        self.clear_findings()
        
        if not self._is_react_file(content, file_path):
            return []
        
        lines = content.split('\n')
        
        self._check_class_components(content, file_path, lines)
        self._check_hooks_rules(content, file_path, lines)
        self._check_props_destructuring(content, file_path, lines)
        self._check_key_prop(content, file_path, lines)
        self._check_inline_functions(content, file_path, lines)
        self._check_useeffect_deps(content, file_path, lines)
        self._check_prop_drilling(content, file_path, lines)
        
        return self.get_findings()
    
    def _is_react_file(self, content: str, file_path: str) -> bool:
        """Check if file is a React component."""
        if not (file_path.endswith('.jsx') or file_path.endswith('.tsx')):
            return False
        return 'react' in content.lower() or 'React' in content
    
    def _check_class_components(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for class components (prefer functional)."""
        class_pattern = re.compile(r'class\s+\w+\s+extends\s+(React\.)?Component')
        
        for i, line in enumerate(lines, start=1):
            if class_pattern.search(line):
                self.add_finding(
                    rule_id="REACT001",
                    message="Class component detected. Prefer functional components with hooks.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Convert to functional component using useState, useEffect, etc.",
                )
    
    def _check_hooks_rules(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for hooks rules violations."""
        hook_pattern = re.compile(r'\buse[A-Z]\w*\s*\(')
        conditional_pattern = re.compile(r'^\s*(if|else|switch|for|while)\s*[\({]')
        
        in_conditional = False
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            if conditional_pattern.search(line):
                in_conditional = True
                brace_depth = 1
            elif in_conditional:
                brace_depth += line.count('{') - line.count('}')
                if brace_depth <= 0:
                    in_conditional = False
            
            if in_conditional and hook_pattern.search(line):
                self.add_finding(
                    rule_id="REACT002",
                    message="Hook called inside conditional. Hooks must be called at the top level.",
                    severity=FindingSeverity.ERROR,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Move hook call outside of conditional block",
                )
    
    def _check_props_destructuring(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for props destructuring patterns."""
        props_access_pattern = re.compile(r'props\.\w+')
        
        props_count = len(props_access_pattern.findall(content))
        if props_count > 3:
            first_props = self.find_line_number(content, 'props.')
            if first_props:
                self.add_finding(
                    rule_id="REACT003",
                    message=f"Multiple props.* accesses ({props_count}). Consider destructuring props.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=first_props,
                    suggestion="Destructure props: const { prop1, prop2 } = props; or in function signature",
                )
    
    def _check_key_prop(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for missing key prop in lists."""
        map_pattern = re.compile(r'\.map\s*\(\s*\([^)]*\)\s*=>')
        key_pattern = re.compile(r'key\s*=')
        
        for i, line in enumerate(lines, start=1):
            if map_pattern.search(line):
                context = '\n'.join(lines[i-1:min(i+5, len(lines))])
                if not key_pattern.search(context):
                    self.add_finding(
                        rule_id="REACT004",
                        message="Array.map() without key prop. Add unique key to list items.",
                        severity=FindingSeverity.WARNING,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add key prop: items.map((item) => <Item key={item.id} ... />)",
                    )
    
    def _check_inline_functions(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for inline functions in JSX that could cause re-renders."""
        inline_handler_pattern = re.compile(r'on\w+\s*=\s*\{\s*\([^)]*\)\s*=>')
        
        for i, line in enumerate(lines, start=1):
            if inline_handler_pattern.search(line):
                self.add_finding(
                    rule_id="REACT005",
                    message="Inline arrow function in JSX prop. This creates a new function on each render.",
                    severity=FindingSeverity.INFO,
                    file_path=file_path,
                    line_start=i,
                    code_snippet=line.strip(),
                    suggestion="Extract to useCallback or define as a named function",
                )
    
    def _check_useeffect_deps(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for useEffect dependency issues."""
        useeffect_pattern = re.compile(r'useEffect\s*\(\s*\(\)\s*=>')
        empty_deps_pattern = re.compile(r'useEffect\s*\([^)]+,\s*\[\s*\]\s*\)')
        
        for i, line in enumerate(lines, start=1):
            if useeffect_pattern.search(line):
                context = '\n'.join(lines[i-1:min(i+10, len(lines))])
                
                if '[]' not in context and '], [' not in context:
                    self.add_finding(
                        rule_id="REACT006",
                        message="useEffect without dependency array. This will run on every render.",
                        severity=FindingSeverity.WARNING,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Add dependency array: useEffect(() => { ... }, [dep1, dep2])",
                    )
    
    def _check_prop_drilling(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for potential prop drilling."""
        props_pattern = re.compile(r'(\w+)=\{(\w+)\}')
        
        prop_passes = {}
        for i, line in enumerate(lines, start=1):
            matches = props_pattern.findall(line)
            for prop_name, value_name in matches:
                if prop_name == value_name:
                    prop_passes[prop_name] = prop_passes.get(prop_name, 0) + 1
        
        for prop_name, count in prop_passes.items():
            if count >= 3:
                first_line = self.find_line_number(content, f'{prop_name}={{{prop_name}}}')
                if first_line:
                    self.add_finding(
                        rule_id="REACT007",
                        message=f"Prop '{prop_name}' passed through {count} times. Consider using Context or composition.",
                        severity=FindingSeverity.INFO,
                        file_path=file_path,
                        line_start=first_line,
                        suggestion="Use React Context or component composition to avoid prop drilling",
                    )
