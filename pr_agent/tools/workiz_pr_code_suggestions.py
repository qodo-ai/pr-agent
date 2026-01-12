"""
Workiz-enhanced PR Code Suggestions

Extends the base PRCodeSuggestions with Workiz-specific features:
- Workiz coding standards enforcement in suggestions
- Cross-repository context for better suggestions
- Custom rules-based suggestions
- NestJS/React/PHP idiomatic patterns
- Fix in Cursor deep links
"""

import re
import time
from functools import partial
from typing import Any, Dict

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.comment_formatter import CommentFormatter


class WorkizPRCodeSuggestions(PRCodeSuggestions):
    """
    Enhanced Code Suggestions for Workiz with additional context and standards.
    
    Extends base PRCodeSuggestions to add:
    - Workiz coding standards in suggestions (functional programming, const, small functions)
    - Cross-repo context from RepoSwarm
    - Custom rules enforcement
    - Language-specific idiomatic patterns (NestJS, React, PHP)
    """

    def __init__(
        self,
        pr_url: str,
        cli_mode: bool = False,
        args: list = None,
        ai_handler: partial[BaseAiHandler] = LiteLLMAIHandler,
    ):
        super().__init__(pr_url, cli_mode, args, ai_handler)
        
        self.workiz_config = get_settings().get("workiz", {})
        self.workiz_enabled = self.workiz_config.get("enabled", True)
        
        self.workiz_context = {
            "rules_findings": [],
            "cross_repo_context": None,
            "analyzer_findings": [],
        }
        
        self._start_time = None
        
        self.comment_formatter = CommentFormatter.from_pr_url(pr_url)
        
        cursor_config = self.workiz_config.get("cursor_integration", {})
        self.cursor_enabled = cursor_config.get("enabled", True)
        self.cursor_include_open_file = cursor_config.get("include_open_file_link", True)
        self.cursor_show_web_fallback = cursor_config.get("show_web_fallback", True)

    async def run(self):
        """
        Enhanced run method with Workiz-specific pipeline.
        
        Pipeline:
        1. Load cross-repo context (if enabled)
        2. Run custom rules to find violations
        3. Inject Workiz coding standards into prompts
        4. Execute base suggestions with enhanced context
        5. Track API usage
        """
        if not self.workiz_enabled:
            get_logger().debug("Workiz enhancements disabled, running base code suggestions")
            return await super().run()

        self._start_time = time.time()
        
        try:
            if not self.git_provider.get_files():
                get_logger().info(
                    f"PR has no files: {self.pr_url}, skipping code suggestions",
                    extra={"context": {"pr_url": self.pr_url}}
                )
                return None

            get_logger().info(
                "Starting Workiz enhanced code suggestions",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "files_count": len(self.git_provider.get_files()),
                }}
            )

            await self._load_cross_repo_context()
            
            await self._run_custom_rules()
            
            self._enhance_suggestion_vars()
            
            result = await super().run()
            
            await self._track_api_usage()
            
            get_logger().info(
                "Workiz code suggestions completed",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "duration_seconds": time.time() - self._start_time,
                    "rules_findings": len(self.workiz_context["rules_findings"]),
                }}
            )
            
            return result

        except Exception as e:
            get_logger().error(
                "Workiz code suggestions failed",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "error": str(e),
                }}
            )
            raise

    async def _load_cross_repo_context(self) -> None:
        """Load cross-repository context from RepoSwarm cache."""
        if not self.workiz_config.get("include_cross_repo_context", True):
            return
            
        get_logger().debug(
            "Loading cross-repo context for suggestions",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        # TODO: Implement in Phase 5
        # - Load from repo_analysis_cache table
        # - Query related code patterns via vector search
        # - Load similar code from other repos
        self.workiz_context["cross_repo_context"] = None

    async def _run_custom_rules(self) -> None:
        """Run custom rules to find violations that need suggestions."""
        get_logger().debug(
            "Running custom rules for suggestions",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        # TODO: Implement in Phase 4
        # - Load rules from workiz_rules.toml
        # - Apply rules to changed files
        # - Collect violations that can be auto-fixed
        self.workiz_context["rules_findings"] = []

    def _enhance_suggestion_vars(self) -> None:
        """Add Workiz context to suggestion variables for prompt injection."""
        workiz_instructions = self._get_workiz_coding_standards()
        
        extra_instructions = self.vars.get("extra_instructions", "")
        self.vars["extra_instructions"] = (
            f"{extra_instructions}\n\n"
            f"## Workiz Coding Standards\n{workiz_instructions}"
        )
        
        if self.workiz_context["rules_findings"]:
            findings_str = self._format_rules_findings()
            self.vars["extra_instructions"] += (
                f"\n\n## Rule Violations to Fix\n{findings_str}"
            )

    def _get_workiz_coding_standards(self) -> str:
        """Get Workiz coding standards for prompt injection."""
        return """When suggesting code improvements, follow these Workiz coding standards:

### Functional Programming
- Use `const` instead of `let` - prefer immutable operations
- Use array methods (map, filter, reduce) instead of for loops
- Avoid mutating arrays with push/splice - use spread operator or concat
- Keep functions small (<15 lines) and focused on one task

### NestJS Patterns
- Use dependency injection (@Injectable, constructor injection)
- Keep controllers thin - business logic belongs in services
- Use DTOs with class-validator decorators for input validation
- Use structured logging with context: `this.logger.log('message', { contextData })`

### React Patterns
- Use functional components with hooks
- Consider React.memo for components with complex props
- Use proper dependency arrays in useEffect/useMemo/useCallback

### Code Quality
- No inline comments - code should be self-documenting
- Use descriptive variable and function names
- Avoid code duplication - extract shared utilities
- Handle errors appropriately

### Security
- Never hardcode secrets or API keys
- Use parameterized queries to prevent SQL injection
- Validate and sanitize all user inputs
"""

    def _format_rules_findings(self) -> str:
        """Format rules findings for prompt injection with Cursor links."""
        findings = self.workiz_context["rules_findings"]
        if not findings:
            return ""
        
        if not self.cursor_enabled:
            return "\n".join(
                f"- [{f['severity']}] {f['rule']}: {f['message']} (line {f.get('line', '?')})"
                for f in findings
            )
        
        normalized_findings = [
            {
                "file": f.get("file", "unknown"),
                "line": f.get("line", 1),
                "message": f.get("message", "Issue detected"),
                "severity": f.get("severity", "warning"),
                "suggestion": f.get("suggestion", f.get("message", "Review and fix this issue")),
                "rule_id": f.get("rule"),
            }
            for f in findings
        ]
        
        return self.comment_formatter.add_cursor_links_to_findings(
            normalized_findings,
            format_type="inline"
        )

    async def _track_api_usage(self) -> None:
        """Track API usage for cost monitoring."""
        duration = time.time() - self._start_time
        
        get_logger().debug(
            "Tracking API usage for suggestions",
            extra={"context": {
                "pr_url": self.pr_url,
                "duration_seconds": duration,
            }}
        )
        
        # TODO: Implement in Phase 3.4
        # - Log model used
        # - Log tokens consumed
        # - Log estimated cost
        # - Store in database
        pass

    def generate_summarized_suggestions(self, data: Dict) -> str:
        """
        Override base method to add Fix in Cursor links to the suggestions output.
        """
        pr_body = super().generate_summarized_suggestions(data)
        
        if not self.cursor_enabled or not pr_body:
            return pr_body
        
        pr_body = self._add_cursor_links_to_suggestions(pr_body)
        
        return pr_body
    
    def _add_cursor_links_to_suggestions(self, pr_body: str) -> str:
        """
        Add Fix in Cursor links to each suggestion in the output.
        
        Parses the markdown/HTML to find file references and adds clickable
        cursor:// links for one-click fixing.
        """
        file_link_pattern = r'\[([^\]]+\.(?:ts|tsx|js|jsx|py|php|java|go|rb|rs|cs))\s*\[(\d+)(?:-(\d+))?\]\]\(([^)]+)\)'
        
        def add_cursor_link(match):
            file_path = match.group(1)
            start_line = int(match.group(2))
            original_link = match.group(0)
            
            cursor_url = self.comment_formatter._build_cursor_agent_url(
                issue_type="Code Suggestion",
                file_path=file_path,
                line_number=start_line,
                suggestion="Apply the suggested code improvement from this PR review",
                rule_id=None,
            )
            
            return f"{original_link} [🔧 Fix in Cursor]({cursor_url})"
        
        enhanced_body = re.sub(file_link_pattern, add_cursor_link, pr_body)
        
        return enhanced_body

    def get_workiz_suggestions_summary(self) -> dict[str, Any]:
        """Get summary of Workiz-specific suggestions context."""
        return {
            "rules_findings_count": len(self.workiz_context["rules_findings"]),
            "has_cross_repo_context": self.workiz_context["cross_repo_context"] is not None,
            "findings": self.workiz_context["rules_findings"],
        }
