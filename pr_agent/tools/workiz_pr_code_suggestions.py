"""
Workiz-enhanced PR Code Suggestions

Extends the base PRCodeSuggestions with Workiz-specific features:
- Workiz coding standards enforcement in suggestions
- Cross-repository context for better suggestions
- Custom rules-based suggestions
- NestJS/React/PHP idiomatic patterns
- Bugbot-style inline review comments with Fix in Cursor buttons
"""

import os
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
from pr_agent.tools.inline_comment_formatter import format_suggestion_comment


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
        
        inline_config = self.workiz_config.get("inline_comments", {})
        self.use_inline_comments = inline_config.get("enabled", True)
        self.max_inline_comments = inline_config.get("max_comments", 20)
        self.severity_threshold = inline_config.get("severity_threshold", "low")
        self.show_web_fallback = inline_config.get("show_web_fallback", True)
        
        # Build cursor redirect URL - use config value or fall back to WEBHOOK_URL env var
        config_redirect_url = inline_config.get("cursor_redirect_url", "")
        if config_redirect_url:
            self.cursor_redirect_url = config_redirect_url
        else:
            webhook_url = os.environ.get("WEBHOOK_URL", "")
            if webhook_url:
                # Ensure we have the correct endpoint path
                base_url = webhook_url.rstrip("/")
                self.cursor_redirect_url = f"{base_url}/api/v1/cursor-redirect"
            else:
                self.cursor_redirect_url = ""
        
        self._suggestions_data = None
        
        self._org = ""
        self._repo = ""
        self._branch = "main"
        self._parse_repo_info(pr_url)

    async def run(self):
        """
        Enhanced run method with Workiz-specific pipeline.
        
        Pipeline:
        1. Load cross-repo context (if enabled)
        2. Run custom rules to find violations
        3. Inject Workiz coding standards into prompts
        4. Execute AI model to generate suggestions (without publishing)
        5. Publish Bugbot-style inline suggestion comments
        6. Track API usage
        
        Note: When inline comments are enabled (default), the base suggestions'
        batched comment is disabled. Each suggestion becomes an individual
        inline comment on the specific code line.
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
                    "use_inline_comments": self.use_inline_comments,
                }}
            )

            await self._load_cross_repo_context()
            
            await self._run_custom_rules()
            
            self._enhance_suggestion_vars()
            
            if self.use_inline_comments:
                original_publish_output = get_settings().config.publish_output
                get_settings().config.publish_output = False
                
                try:
                    result = await super().run()
                finally:
                    get_settings().config.publish_output = original_publish_output
                
                if self._suggestions_data:
                    await self._publish_inline_suggestion_comments()
            else:
                result = await super().run()
            
            await self._track_api_usage()
            
            get_logger().info(
                "Workiz code suggestions completed",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "duration_seconds": time.time() - self._start_time,
                    "rules_findings": len(self.workiz_context["rules_findings"]),
                    "inline_comments_enabled": self.use_inline_comments,
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

    def _parse_repo_info(self, pr_url: str) -> None:
        """
        Extract org, repo, and branch using git_provider.
        
        Prefers git_provider data for accuracy, falls back to URL parsing.
        """
        try:
            # Try to get accurate info from git_provider
            if hasattr(self, 'git_provider') and self.git_provider:
                # Get org/repo from repository object
                if hasattr(self.git_provider, 'repo') and self.git_provider.repo:
                    full_name = self.git_provider.repo.full_name  # "Workiz/repo-name"
                    if full_name and '/' in full_name:
                        parts = full_name.split('/')
                        self._org = parts[0]
                        self._repo = parts[1]
                
                # Get branch from PR head
                if hasattr(self.git_provider, 'pr') and self.git_provider.pr:
                    if hasattr(self.git_provider.pr, 'head') and self.git_provider.pr.head:
                        self._branch = self.git_provider.pr.head.ref
            
            # Fallback to URL parsing if git_provider didn't provide the info
            if not self._org or not self._repo:
                parts = pr_url.replace("https://", "").split("/")
                if "github.com" in pr_url and len(parts) >= 5:
                    self._org = parts[1]
                    self._repo = parts[2]
        except Exception:
            pass

    def _should_include_suggestion(self, score: int) -> bool:
        """Check if suggestion passes the impact score threshold."""
        threshold_map = {"high": 7, "medium": 4, "low": 1}
        threshold = threshold_map.get(self.severity_threshold.lower(), 1)
        return score >= threshold

    async def _publish_inline_suggestion_comments(self) -> None:
        """
        Publish each code suggestion as an individual inline review comment.
        
        Creates Bugbot-style comments that appear:
        - Inline on the specific code lines in "Files Changed" tab
        - In the "Conversation" tab as part of a review thread
        
        Uses event="COMMENT" to ensure comments are non-blocking.
        """
        if not self._suggestions_data:
            get_logger().info("No suggestions data to publish", {
                "pr_url": self.pr_url,
            })
            return
        
        suggestions = self._suggestions_data.get('code_suggestions', [])
        if not suggestions:
            get_logger().info("No code suggestions to publish as inline comments", {
                "pr_url": self.pr_url,
            })
            return
        
        try:
            branch = self.git_provider.pr.head.ref if hasattr(self.git_provider.pr, 'head') else "main"
            self._branch = branch
        except Exception:
            self._branch = "main"
        
        sorted_suggestions = sorted(suggestions, key=lambda x: int(x.get('score', 0)), reverse=True)
        
        comments = []
        for suggestion in sorted_suggestions:
            score = int(suggestion.get('score', 0))
            if not self._should_include_suggestion(score):
                continue
            
            if len(comments) >= self.max_inline_comments:
                get_logger().info(f"Reached max inline comments limit ({self.max_inline_comments})", {
                    "pr_url": self.pr_url,
                    "total_suggestions": len(suggestions),
                })
                break
            
            file_path = suggestion.get('relevant_file', 'unknown').strip()
            line_start = int(suggestion.get('relevant_lines_start', 1))
            line_end = int(suggestion.get('relevant_lines_end', line_start))
            summary = suggestion.get('one_sentence_summary', 'Suggestion').strip()
            content = suggestion.get('suggestion_content', '').strip()
            label = suggestion.get('label', 'improvement').strip()
            existing_code = suggestion.get('existing_code', '').strip()
            improved_code = suggestion.get('improved_code', '').strip()
            
            body = format_suggestion_comment(
                summary=summary,
                description=re.sub(r'<br\s*/?>', '\n', content),
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                existing_code=existing_code,
                improved_code=improved_code,
                label=label,
                cursor_redirect_url=self.cursor_redirect_url if self.cursor_redirect_url else "",
                org=self._org,
                repo=self._repo,
                branch=self._branch,
            )
            
            comments.append({
                "path": file_path,
                "line": line_end,
                "body": body,
            })
        
        if not comments:
            get_logger().info("No suggestions passed impact threshold", {
                "pr_url": self.pr_url,
                "threshold": self.severity_threshold,
                "total_suggestions": len(suggestions),
            })
            return
        
        try:
            self.git_provider.create_review_with_inline_comments(
                comments=comments,
                event="COMMENT",
            )
            
            get_logger().info("Published inline suggestion comments", {
                "pr_url": self.pr_url,
                "comment_count": len(comments),
                "total_suggestions": len(suggestions),
                "threshold": self.severity_threshold,
            })
            
        except Exception as e:
            get_logger().error("Failed to publish inline suggestion comments", {
                "pr_url": self.pr_url,
                "error": str(e),
                "comment_count": len(comments),
            })
            raise

    async def _create_check_run_with_suggestions(self) -> None:
        """
        Create a GitHub Check Run with annotations for all suggestions.
        
        This enables:
        - Inline annotations on the PR's Files Changed tab
        - "Fix in Cursor" action buttons for high-impact suggestions
        """
        if not self._suggestions_data:
            return
            
        suggestions = self._suggestions_data.get('code_suggestions', [])
        if not suggestions:
            get_logger().debug("No suggestions to create check run for", {
                "pr_url": self.pr_url
            })
            return
        
        try:
            head_sha = self.git_provider.last_commit_id.sha
            
            builder = CheckRunBuilder(self.check_run_name, head_sha)
            
            high_impact = sum(1 for s in suggestions if int(s.get('score', 0)) >= 7)
            medium_impact = sum(1 for s in suggestions if 4 <= int(s.get('score', 0)) < 7)
            low_impact = len(suggestions) - high_impact - medium_impact
            
            if high_impact > 0:
                conclusion = "action_required"
            elif medium_impact > 0:
                conclusion = "neutral"
            else:
                conclusion = "success"
            
            builder.set_status("completed", conclusion)
            
            summary = f"Found {len(suggestions)} improvement suggestions: "
            summary += f"{high_impact} high impact, {medium_impact} medium, {low_impact} low"
            
            builder.set_output(
                title=f"Suggestions: {len(suggestions)} improvements",
                summary=summary,
                text="Review the suggestions to improve code quality. Click 'Fix in Cursor' to apply fixes automatically."
            )
            
            from pr_agent.servers.github_app import store_action_context
            
            sorted_suggestions = sorted(suggestions, key=lambda x: int(x.get('score', 0)), reverse=True)
            
            for i, suggestion in enumerate(sorted_suggestions[:50]):
                file_path = suggestion.get('relevant_file', 'unknown').strip()
                start_line = int(suggestion.get('relevant_lines_start', 1))
                end_line = int(suggestion.get('relevant_lines_end', start_line))
                score = int(suggestion.get('score', 0))
                summary_text = suggestion.get('one_sentence_summary', 'Suggestion').strip()
                content = suggestion.get('suggestion_content', '').strip()
                label = suggestion.get('label', 'improvement').strip()
                
                if score >= 7:
                    level = AnnotationLevel.WARNING
                elif score >= 4:
                    level = AnnotationLevel.NOTICE
                else:
                    level = AnnotationLevel.NOTICE
                
                message = f"{summary_text}\n\n{content}"
                
                builder.add_annotation(
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    message=message,
                    level=level,
                    title=f"[{label}] Impact: {score}/10"[:255],
                )
            
            action_candidates = [s for s in sorted_suggestions if int(s.get('score', 0)) >= 7][:3]
            
            for suggestion in action_candidates:
                file_path = suggestion.get('relevant_file', 'unknown').strip()
                start_line = int(suggestion.get('relevant_lines_start', 1))
                summary_text = suggestion.get('one_sentence_summary', 'Fix')
                content = suggestion.get('suggestion_content', '')
                existing_code = suggestion.get('existing_code', '')
                improved_code = suggestion.get('improved_code', '')
                
                identifier = encode_action_identifier(file_path, start_line, summary_text[:10])
                
                store_action_context(identifier, {
                    "file_path": file_path,
                    "line": start_line,
                    "issue_type": summary_text,
                    "message": content,
                    "suggestion": f"Replace:\n{existing_code}\n\nWith:\n{improved_code}",
                    "code_context": existing_code,
                    "pr_url": self.pr_url,
                })
                
                short_file = file_path.split("/")[-1][:10]
                builder.add_action(
                    label=f"Fix {short_file}:{start_line}"[:20],
                    identifier=identifier,
                    description="Open Cursor AI to fix"[:40],
                )
            
            check_run_data = builder.build()
            
            self.git_provider.create_check_run(**check_run_data)
            
            get_logger().info("Created check run with suggestions", {
                "pr_url": self.pr_url,
                "suggestions_count": len(suggestions),
                "annotations_count": min(len(suggestions), 50),
                "actions_count": len(action_candidates),
            })
            
        except Exception as e:
            get_logger().error("Failed to create check run for suggestions", {
                "pr_url": self.pr_url,
                "error": str(e),
            })

    def generate_summarized_suggestions(self, data: Dict) -> str:
        """
        Override base method to add Fix in Cursor column to the suggestions table.
        """
        self._suggestions_data = data
        
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

                    cursor_prompt_text = self._build_cursor_prompt(
                        title=suggestion_summary,
                        file_path=relevant_file,
                        line_number=relevant_lines_start,
                        description=suggestion_content.replace('<br>', '\n'),
                        diff_code=patch,
                    )
                    pr_body += f"\n\n<details><summary>🔧 <strong>Fix with Cursor AI</strong> - Click to copy prompt</summary>\n\n"
                    pr_body += f"Copy this prompt and paste it in Cursor's AI chat:\n\n"
                    pr_body += f"```\n{cursor_prompt_text}\n```\n\n</details>"

                    pr_body += f"</details>"

                    score_int = int(suggestion.get('score', 0))
                    score_str = self._get_score_str(score_int)
                    pr_body += f"</td><td align=center>{score_str}</td>"
                    
                    vscode_url = self._build_suggestion_cursor_url(
                        title=suggestion_summary,
                        file_path=relevant_file,
                        line_number=relevant_lines_start,
                        description=suggestion_content,
                        diff_code=patch,
                    )
                    
                    cursor_prompt = self._build_cursor_prompt(
                        title=suggestion_summary,
                        file_path=relevant_file,
                        line_number=relevant_lines_start,
                        description=suggestion_content,
                        diff_code=patch,
                    )
                    escaped_prompt = cursor_prompt.replace('"', '&quot;').replace('\n', '&#10;')[:500]
                    
                    pr_body += f"""<td align=center><a href="{vscode_url}" title="Open in VS Code Web. For Cursor: copy prompt from expanded suggestion"><kbd>📂&nbsp;Open</kbd></a></td>"""
                    
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
        """
        Build a URL for the Fix in Cursor button.
        
        GitHub blocks custom URL schemes (cursor://) for security.
        We use vscode.dev as a fallback which GitHub allows, and include
        instructions in the link title for using Cursor.
        """
        from urllib.parse import quote
        
        org = self.comment_formatter.org
        repo = self.comment_formatter.repo
        branch = self.comment_formatter.branch
        
        return f"https://vscode.dev/github/{org}/{repo}/blob/{branch}/{file_path}#L{line_number}"
    
    def _build_cursor_prompt(
        self,
        title: str,
        file_path: str,
        line_number: int,
        description: str,
        diff_code: str,
    ) -> str:
        """Build the prompt text for Cursor agent."""
        clean_description = re.sub(r'<br\s*/?>', '\n', description)
        
        return f"""Apply this code suggestion from a PR review:

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

    def get_workiz_suggestions_summary(self) -> dict[str, Any]:
        """Get summary of Workiz-specific suggestions context."""
        return {
            "rules_findings_count": len(self.workiz_context["rules_findings"]),
            "has_cross_repo_context": self.workiz_context["cross_repo_context"] is not None,
            "findings": self.workiz_context["rules_findings"],
        }
