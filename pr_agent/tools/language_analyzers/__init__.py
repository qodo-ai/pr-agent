"""
Language Analyzers Module

Provides language-specific code analysis for enhanced PR reviews.
Each analyzer detects patterns, anti-patterns, and best practices
specific to its target language/framework.

Available Analyzers:
- TypeScriptAnalyzer: TypeScript/JavaScript analysis
- NestJSAnalyzer: NestJS framework patterns
- ReactAnalyzer: React component patterns
- PHPAnalyzer: PHP code analysis
- PythonAnalyzer: Python code analysis

Usage:
    from pr_agent.tools.language_analyzers import get_analyzer_for_file
    
    analyzer = get_analyzer_for_file("src/users/users.service.ts")
    if analyzer:
        findings = await analyzer.analyze(file_content, file_path)
"""

from .base_analyzer import BaseAnalyzer, AnalyzerFinding, FindingSeverity
from .typescript_analyzer import TypeScriptAnalyzer
from .nestjs_analyzer import NestJSAnalyzer
from .react_analyzer import ReactAnalyzer
from .php_analyzer import PHPAnalyzer
from .python_analyzer import PythonAnalyzer

__all__ = [
    "BaseAnalyzer",
    "AnalyzerFinding",
    "FindingSeverity",
    "TypeScriptAnalyzer",
    "NestJSAnalyzer",
    "ReactAnalyzer",
    "PHPAnalyzer",
    "PythonAnalyzer",
    "get_analyzer_for_file",
    "get_analyzers_for_files",
]

# File extension to analyzer mapping
_EXTENSION_ANALYZERS: dict[str, list[type[BaseAnalyzer]]] = {
    ".ts": [TypeScriptAnalyzer, NestJSAnalyzer],
    ".tsx": [TypeScriptAnalyzer, ReactAnalyzer],
    ".js": [TypeScriptAnalyzer],
    ".jsx": [TypeScriptAnalyzer, ReactAnalyzer],
    ".php": [PHPAnalyzer],
    ".py": [PythonAnalyzer],
}


def get_analyzer_for_file(file_path: str) -> list[BaseAnalyzer]:
    """
    Get appropriate analyzers for a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of analyzer instances for the file type
    """
    import os
    _, ext = os.path.splitext(file_path.lower())
    
    analyzer_classes = _EXTENSION_ANALYZERS.get(ext, [])
    return [cls() for cls in analyzer_classes]


def get_analyzers_for_files(file_paths: list[str]) -> dict[str, list[BaseAnalyzer]]:
    """
    Get analyzers for multiple files.
    
    Args:
        file_paths: List of file paths
        
    Returns:
        Dict mapping file paths to their analyzer instances
    """
    return {path: get_analyzer_for_file(path) for path in file_paths}
