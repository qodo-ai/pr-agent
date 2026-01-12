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
        Override base method to add Fix in Cursor column to the suggestions table.
        """
        if not self.cursor_enabled:
            return super().generate_summarized_suggestions(data)
        
        try:
            import difflib
            from pr_agent.algo.utils import get_settings
            from pr_agent.tools.pr_code_suggestions import insert_br_after_x_chars, replace_code_tags
            
            pr_body = "## PR Code Suggestions ✨\n\n"

            if len(data.get('code_suggestions', [])) == 0:
                pr_body += "No suggestions found to improve this PR."
                return pr_body

            if get_settings().config.is_auto_command:
                pr_body += "Explore these optional code suggestions:\n\n"

            pr_body += "<table>"
            header = f"Suggestion"
            delta = 58
            header += "&nbsp; " * delta
            pr_body += f"""<thead><tr><td><strong>Category</strong></td><td align=left><strong>{header}</strong></td><td align=center><strong>Impact</strong></td><td align=center><strong>Fix</strong></td></tr>"""
            pr_body += """<tbody>"""
            
            suggestions_labels = dict()
            for suggestion in data['code_suggestions']:
                label = suggestion['label'].strip().strip("'").strip('"')
                if label not in suggestions_labels:
                    suggestions_labels[label] = []
                suggestions_labels[label].append(suggestion)

            suggestions_labels = dict(
                sorted(suggestions_labels.items(), key=lambda x: max([s['score'] for s in x[1]]), reverse=True))
            for label, suggestions in suggestions_labels.items():
                suggestions_labels[label] = sorted(suggestions, key=lambda x: x['score'], reverse=True)

            for label, suggestions in suggestions_labels.items():
                num_suggestions = len(suggestions)
                pr_body += f"""<tr><td rowspan={num_suggestions}>{label.capitalize()}</td>\n"""
                
                for i, suggestion in enumerate(suggestions):
                    relevant_file = suggestion['relevant_file'].strip()
                    relevant_lines_start = int(suggestion['relevant_lines_start'])
                    relevant_lines_end = int(suggestion['relevant_lines_end'])
                    
                    range_str = f"[{relevant_lines_start}]" if relevant_lines_start == relevant_lines_end else f"[{relevant_lines_start}-{relevant_lines_end}]"

                    try:
                        code_snippet_link = self.git_provider.get_line_link(relevant_file, relevant_lines_start, relevant_lines_end)
                    except:
                        code_snippet_link = ""

                    suggestion_content = suggestion['suggestion_content'].rstrip()
                    suggestion_content = insert_br_after_x_chars(suggestion_content, 84)
                    
                    existing_code = suggestion['existing_code'].rstrip() + "\n"
                    improved_code = suggestion['improved_code'].rstrip() + "\n"

                    diff = difflib.unified_diff(existing_code.split('\n'), improved_code.split('\n'), n=999)
                    patch = "\n".join(list(diff)[5:]).strip('\n')
                    example_code = f"```diff\n{patch.rstrip()}\n```\n"

                    if i == 0:
                        pr_body += f"""<td>\n\n"""
                    else:
                        pr_body += f"""<tr><td>\n\n"""
                    
                    suggestion_summary = suggestion['one_sentence_summary'].strip().rstrip('.')
                    if "'<" in suggestion_summary and ">'" in suggestion_summary:
                        suggestion_summary = suggestion_summary.replace("'<", "`<").replace(">'", ">`")
                    if '`' in suggestion_summary:
                        suggestion_summary = replace_code_tags(suggestion_summary)

                    pr_body += f"""\n\n<details><summary>{suggestion_summary}</summary>\n\n___\n\n"""
                    pr_body += f"""**{suggestion_content}**\n\n[{relevant_file} {range_str}]({code_snippet_link})\n\n{example_code.rstrip()}\n"""
                    
                    if suggestion.get('score_why'):
                        pr_body += f"<details><summary>Suggestion importance[1-10]: {suggestion['score']}</summary>\n\n__\n\nWhy: {suggestion['score_why']}\n\n</details>"

                    pr_body += f"</details>"

                    score_int = int(suggestion.get('score', 0))
                    score_str = self._get_score_str(score_int)
                    pr_body += f"</td><td align=center>{score_str}</td>"
                    
                    cursor_url = self._build_suggestion_cursor_url(
                        title=suggestion_summary,
                        file_path=relevant_file,
                        line_number=relevant_lines_start,
                        description=suggestion_content,
                        diff_code=patch,
                    )
                    pr_body += f"""<td align=center><a href="{cursor_url}"><kbd>🔧&nbsp;Fix</kbd></a></td>"""
                    
                    pr_body += f"</tr>"

            pr_body += """</tbody></table>"""
            return pr_body
            
        except Exception as e:
            get_logger().info(f"Failed to generate Workiz suggestions, falling back to base: {e}")
            return super().generate_summarized_suggestions(data)
    
    def _get_score_str(self, score: int) -> str:
        """Convert numeric score to label."""
        if score >= 9:
            return "High"
        elif score >= 7:
            return "Medium"
        return "Low"
    
    def _build_suggestion_cursor_url(
        self,
        title: str,
        file_path: str,
        line_number: int,
        description: str,
        diff_code: str,
    ) -> str:
        """Build cursor://agent/prompt URL with full suggestion context."""
        from urllib.parse import quote
        
        clean_description = re.sub(r'<br\s*/?>', '\n', description)
        
        prompt = f"""Apply this code suggestion from a PR review:

## Suggestion: {title}

**File:** {file_path}
**Line:** {line_number}

**What to do:** {clean_description[:500]}

**Suggested code changes:**
```diff
{diff_code[:1000]}
```

## Instructions:
1. First verify the file and line number are correct
2. Review the suggested diff carefully
3. Apply the changes if they make sense
4. Ensure the fix doesn't break existing functionality
5. Follow the project's coding standards"""
        
        encoded_prompt = quote(prompt, safe='')
        return f"cursor://agent/prompt?prompt={encoded_prompt}"

    def get_workiz_suggestions_summary(self) -> dict[str, Any]:
        """Get summary of Workiz-specific suggestions context."""
        return {
            "rules_findings_count": len(self.workiz_context["rules_findings"]),
            "has_cross_repo_context": self.workiz_context["cross_repo_context"] is not None,
            "findings": self.workiz_context["rules_findings"],
        }
