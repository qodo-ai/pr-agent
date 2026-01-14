"""
Custom Rules Engine

Loads and applies custom review rules from:
1. workiz_rules.toml configuration file
2. custom_rules database table (future)

Rules can be:
- Pattern-based (regex matching)
- AST-based (for supported languages)
- LLM-based (semantic analysis)
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pr_agent.config_loader import get_settings

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of custom rules."""
    PATTERN = "pattern"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"


class RuleScope(Enum):
    """Scope of rule application."""
    ALL = "all"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    PYTHON = "python"
    PHP = "php"
    NESTJS = "nestjs"
    REACT = "react"


@dataclass
class CustomRule:
    """
    Represents a custom review rule.
    
    Attributes:
        id: Unique rule identifier
        name: Human-readable rule name
        description: Detailed description
        rule_type: Type of rule (pattern, semantic, structural)
        scope: Language/framework scope
        pattern: Regex pattern (for pattern rules)
        severity: Severity level (error, warning, info, suggestion)
        message: Message to display when rule triggers
        suggestion: Suggested fix
        enabled: Whether rule is active
        metadata: Additional configuration
    """
    id: str
    name: str
    description: str
    rule_type: RuleType
    scope: RuleScope
    severity: str
    message: str
    pattern: str | None = None
    suggestion: str | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleFinding:
    """Finding from a custom rule."""
    rule_id: str
    rule_name: str
    message: str
    severity: str
    file_path: str
    line_start: int
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion: str | None = None


class CustomRulesEngine:
    """
    Engine for loading and applying custom review rules.
    
    Usage:
        engine = CustomRulesEngine()
        await engine.load_rules()
        findings = await engine.apply_rules(files_content)
    """
    
    def __init__(self):
        self._rules: list[CustomRule] = []
        self._loaded = False
    
    async def load_rules(self) -> None:
        """Load rules from configuration and database."""
        if self._loaded:
            return
        
        self._load_rules_from_config()
        await self._load_rules_from_database()
        
        self._loaded = True
        logger.info(
            "Custom rules loaded",
            extra={"context": {"rules_count": len(self._rules)}}
        )
    
    def _load_rules_from_config(self) -> None:
        """Load rules from workiz_rules.toml."""
        try:
            settings = get_settings()
            custom_rules = settings.get("custom_rules", {})
            
            for rule_id, rule_config in custom_rules.items():
                if isinstance(rule_config, str):
                    self._rules.append(CustomRule(
                        id=f"WORKIZ_{rule_id.upper()}",
                        name=rule_id.replace('_', ' ').title(),
                        description=rule_config,
                        rule_type=RuleType.SEMANTIC,
                        scope=RuleScope.ALL,
                        severity="info",
                        message=rule_config,
                    ))
                elif isinstance(rule_config, dict):
                    self._rules.append(CustomRule(
                        id=rule_config.get("id", f"WORKIZ_{rule_id.upper()}"),
                        name=rule_config.get("name", rule_id.replace('_', ' ').title()),
                        description=rule_config.get("description", ""),
                        rule_type=RuleType(rule_config.get("type", "semantic")),
                        scope=RuleScope(rule_config.get("scope", "all")),
                        severity=rule_config.get("severity", "info"),
                        message=rule_config.get("message", ""),
                        pattern=rule_config.get("pattern"),
                        suggestion=rule_config.get("suggestion"),
                        enabled=rule_config.get("enabled", True),
                        metadata=rule_config.get("metadata", {}),
                    ))
            
            logger.debug(
                "Rules loaded from config",
                extra={"context": {"count": len(self._rules)}}
            )
        except Exception as e:
            logger.warning(
                "Failed to load rules from config",
                extra={"context": {"error": str(e)}}
            )
    
    async def _load_rules_from_database(self) -> None:
        """Load rules from database (future implementation)."""
        pass
    
    def get_rules(self, scope: RuleScope | None = None) -> list[CustomRule]:
        """Get all rules, optionally filtered by scope."""
        if scope is None:
            return [r for r in self._rules if r.enabled]
        return [r for r in self._rules if r.enabled and (r.scope == scope or r.scope == RuleScope.ALL)]
    
    def get_pattern_rules(self, scope: RuleScope | None = None) -> list[CustomRule]:
        """Get pattern-based rules."""
        rules = self.get_rules(scope)
        return [r for r in rules if r.rule_type == RuleType.PATTERN and r.pattern]
    
    def get_semantic_rules(self, scope: RuleScope | None = None) -> list[CustomRule]:
        """Get semantic rules (for LLM analysis)."""
        rules = self.get_rules(scope)
        return [r for r in rules if r.rule_type == RuleType.SEMANTIC]
    
    async def apply_rules(
        self,
        files: dict[str, str],
        scope: RuleScope | None = None,
    ) -> list[RuleFinding]:
        """
        Apply rules to file contents.
        
        Args:
            files: Dict mapping file paths to contents
            scope: Optional scope filter
            
        Returns:
            List of rule findings
        """
        if not self._loaded:
            await self.load_rules()
        
        findings: list[RuleFinding] = []
        
        for file_path, content in files.items():
            file_scope = self._detect_scope(file_path)
            applicable_rules = self.get_pattern_rules(file_scope)
            
            for rule in applicable_rules:
                rule_findings = self._apply_pattern_rule(rule, content, file_path)
                findings.extend(rule_findings)
        
        logger.debug(
            "Rules applied",
            extra={"context": {
                "files_count": len(files),
                "findings_count": len(findings),
            }}
        )
        
        return findings
    
    def _detect_scope(self, file_path: str) -> RuleScope:
        """Detect the scope based on file path."""
        file_lower = file_path.lower()
        
        if file_lower.endswith('.tsx') or file_lower.endswith('.jsx'):
            return RuleScope.REACT
        elif '.service.ts' in file_lower or '.controller.ts' in file_lower or '.module.ts' in file_lower:
            return RuleScope.NESTJS
        elif file_lower.endswith('.ts'):
            return RuleScope.TYPESCRIPT
        elif file_lower.endswith('.js'):
            return RuleScope.JAVASCRIPT
        elif file_lower.endswith('.py'):
            return RuleScope.PYTHON
        elif file_lower.endswith('.php'):
            return RuleScope.PHP
        
        return RuleScope.ALL
    
    def _apply_pattern_rule(
        self,
        rule: CustomRule,
        content: str,
        file_path: str,
    ) -> list[RuleFinding]:
        """Apply a pattern-based rule to content."""
        findings: list[RuleFinding] = []
        
        if not rule.pattern:
            return findings
        
        try:
            pattern = re.compile(rule.pattern, re.MULTILINE)
            lines = content.split('\n')
            
            for i, line in enumerate(lines, start=1):
                if pattern.search(line):
                    findings.append(RuleFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        message=rule.message,
                        severity=rule.severity,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion=rule.suggestion,
                    ))
        except re.error as e:
            logger.warning(
                "Invalid regex pattern in rule",
                extra={"context": {"rule_id": rule.id, "error": str(e)}}
            )
        
        return findings
    
    def get_rules_for_prompt(self, scope: RuleScope | None = None) -> str:
        """
        Format semantic rules for inclusion in LLM prompt.
        
        Returns:
            Formatted string of rules for prompt injection
        """
        semantic_rules = self.get_semantic_rules(scope)
        
        if not semantic_rules:
            return ""
        
        rules_text = "## Workiz Coding Standards\n\n"
        rules_text += "Apply the following rules when reviewing code:\n\n"
        
        for rule in semantic_rules:
            rules_text += f"- **{rule.name}**: {rule.description}\n"
            if rule.suggestion:
                rules_text += f"  - Suggestion: {rule.suggestion}\n"
        
        return rules_text


# Global instance
_engine: CustomRulesEngine | None = None


def get_rules_engine() -> CustomRulesEngine:
    """Get the global custom rules engine instance."""
    global _engine
    if _engine is None:
        _engine = CustomRulesEngine()
    return _engine
