"""
Workiz-enhanced PR Reviewer

Extends the base PRReviewer with Workiz-specific features:
- Cross-repository context (RepoSwarm integration)
- Jira ticket context
- Custom rules engine
- Language-specific analyzers
- Review history storage
- API usage tracking
- Bugbot-style inline review comments with Fix in Cursor buttons
"""

import os
import re
import time
from functools import partial
from typing import Any

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger
from pr_agent.tools.pr_reviewer import PRReviewer
from pr_agent.tools.language_analyzers import get_analyzer_for_file
from pr_agent.tools.custom_rules_engine import get_rules_engine
from pr_agent.tools.sql_analyzer import get_sql_analyzer
from pr_agent.tools.security_analyzer import get_security_analyzer
from pr_agent.tools.comment_formatter import CommentFormatter, add_cursor_links_to_review_text
from pr_agent.tools.inline_comment_formatter import format_inline_comment


# File extensions to skip during analysis (non-code files)
SKIP_ANALYZER_EXTENSIONS = {
    '.md', '.markdown', '.txt', '.rst',  # Documentation
    '.json', '.toml', '.yaml', '.yml', '.xml',  # Config files
    '.gitignore', '.dockerignore', '.editorconfig',  # Ignore files
    '.lock', '.sum',  # Lock files
    '.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico',  # Images
    '.env', '.env.example',  # Environment files
    '.css', '.scss', '.less',  # Stylesheets (optional, but lower priority)
}


def _should_analyze_file(file_path: str) -> bool:
    """
    Check if a file should be analyzed based on its extension.
    
    Skips non-code files like markdown, JSON, TOML, etc. that can cause
    false positives when pattern-matching analyzers run on them.
    """
    if '.' not in file_path:
        return True  # No extension, assume it's code
    
    ext = '.' + file_path.rsplit('.', 1)[-1].lower()
    return ext not in SKIP_ANALYZER_EXTENSIONS


def _deduplicate_findings(findings: list[dict]) -> list[dict]:
    """
    Deduplicate findings by (file, line, rule_id).
    
    Multiple analyzers might report the same issue, or the same rule
    might match multiple times on the same line. This ensures we only
    report each unique issue once.
    """
    seen = set()
    unique = []
    for finding in findings:
        key = (
            finding.get('file', ''),
            finding.get('line', 0),
            finding.get('rule_id', '') or finding.get('title', ''),
        )
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


class WorkizPRReviewer(PRReviewer):
    """
    Enhanced PR Reviewer for Workiz with additional context and analysis.
    
    Extends base PRReviewer to add:
    - Custom Workiz rules evaluation
    - Cross-repo context from RepoSwarm
    - Jira ticket integration
    - Review history storage
    - API usage tracking
    """

    def __init__(
        self,
        pr_url: str,
        is_answer: bool = False,
        is_auto: bool = False,
        args: list = None,
        ai_handler: partial[BaseAiHandler] = LiteLLMAIHandler,
    ):
        super().__init__(pr_url, is_answer, is_auto, args, ai_handler)
        
        self.workiz_config = get_settings().get("workiz", {})
        self.workiz_enabled = self.workiz_config.get("enabled", True)
        
        self.workiz_context = {
            "rules_findings": [],
            "cross_repo_context": None,
            "jira_context": None,
            "analyzer_findings": [],
        }
        
        self._start_time = None
        self._api_calls = []
        
        self.comment_formatter = CommentFormatter.from_pr_url(pr_url)
        
        inline_config = self.workiz_config.get("inline_comments", {})
        self.use_inline_comments = inline_config.get("enabled", True)
        self.max_inline_comments = inline_config.get("max_comments", 20)
        self.severity_threshold = inline_config.get("severity_threshold", "low")
        self.show_web_fallback = inline_config.get("show_web_fallback", True)
        
        # Build cursor redirect URL - priority: CURSOR_REDIRECT_URL env > config > WEBHOOK_URL env
        env_cursor_url = os.environ.get("CURSOR_REDIRECT_URL", "")
        config_redirect_url = inline_config.get("cursor_redirect_url", "")
        if env_cursor_url:
            self.cursor_redirect_url = env_cursor_url
        elif config_redirect_url:
            self.cursor_redirect_url = config_redirect_url
        else:
            webhook_url = os.environ.get("WEBHOOK_URL", "")
            if webhook_url:
                base_url = webhook_url.rstrip("/")
                self.cursor_redirect_url = f"{base_url}/api/v1/cursor-redirect"
            else:
                self.cursor_redirect_url = ""
        
        self._org = ""
        self._repo = ""
        self._branch = "main"
        self._parse_repo_info(pr_url)

    async def run(self) -> None:
        """
        Enhanced run method with Workiz-specific pipeline.
        
        Pipeline:
        1. Load cross-repo context (if enabled)
        2. Load Jira context (if ticket linked)
        3. Run language analyzers
        4. Run custom rules engine
        5. Publish Bugbot-style inline review comments
        6. Store review history
        7. Track API usage
        
        Note: When inline comments are enabled (default), the base review's
        batched comment is disabled. Each finding becomes an individual
        inline comment on the specific code line.
        """
        if not self.workiz_enabled:
            get_logger().debug("Workiz enhancements disabled, running base reviewer")
            return await super().run()

        self._start_time = time.time()
        
        try:
            if not self.git_provider.get_files():
                get_logger().info(
                    f"PR has no files: {self.pr_url}, skipping review",
                    extra={"context": {"pr_url": self.pr_url}}
                )
                return None

            get_logger().info(
                "Starting Workiz enhanced PR review",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "files_count": len(self.git_provider.get_files()),
                    "use_inline_comments": self.use_inline_comments,
                }}
            )

            await self._load_cross_repo_context()
            
            await self._load_jira_context()
            
            await self._run_language_analyzers()
            
            await self._run_custom_rules()
            
            self._enhance_review_vars()
            
            # Always run and publish the AI review
            await super().run()
            
            # Additionally publish static analyzer findings as inline comments
            if self.use_inline_comments:
                await self._publish_inline_review_comments()
            
            await self._store_review_history()
            
            await self._track_api_usage()
            
            get_logger().info(
                "Workiz PR review completed",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "duration_seconds": time.time() - self._start_time,
                    "rules_findings": len(self.workiz_context["rules_findings"]),
                    "analyzer_findings": len(self.workiz_context["analyzer_findings"]),
                    "inline_comments_enabled": self.use_inline_comments,
                }}
            )

        except Exception as e:
            get_logger().error(
                "Workiz PR review failed",
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
            "Loading cross-repo context",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        # TODO: Implement in Phase 5
        # - Load from repo_analysis_cache table
        # - Query related code chunks via vector search
        # - Load PubSub topology
        self.workiz_context["cross_repo_context"] = None

    async def _load_jira_context(self) -> None:
        """Load Jira ticket context if ticket is linked to PR."""
        if not self.workiz_config.get("include_jira_context", True):
            return
            
        get_logger().debug(
            "Loading Jira context",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        # TODO: Implement in Phase 6
        # - Extract ticket key from PR title/description/branch
        # - Fetch ticket details and history
        # - Find similar past tickets
        self.workiz_context["jira_context"] = None

    async def _run_language_analyzers(self) -> None:
        """Run language-specific analyzers on changed files."""
        get_logger().debug(
            "Running language analyzers",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        findings = []
        files = self.git_provider.get_files()
        
        sql_analyzer = get_sql_analyzer()
        security_analyzer = get_security_analyzer()
        
        skipped_files = 0
        for file in files:
            try:
                file_path = file.filename if hasattr(file, 'filename') else str(file)
                
                # Skip non-code files (markdown, JSON, TOML, etc.)
                if not _should_analyze_file(file_path):
                    skipped_files += 1
                    continue
                
                try:
                    content = self.git_provider.get_pr_file_content(file_path, self.git_provider.pr.head.ref)
                except Exception:
                    continue
                
                if not content:
                    continue
                
                language_analyzers = get_analyzer_for_file(file_path)
                for analyzer in language_analyzers:
                    try:
                        analyzer_findings = await analyzer.analyze(content, file_path)
                        for finding in analyzer_findings:
                            findings.append({
                                "analyzer": analyzer.name,
                                "rule_id": finding.rule_id,
                                "message": finding.message,
                                "severity": finding.severity.value,
                                "file": file_path,
                                "line": finding.line_start,
                                "suggestion": finding.suggestion,
                            })
                    except Exception as e:
                        get_logger().warning(
                            f"Analyzer {analyzer.name} failed",
                            extra={"context": {"file": file_path, "error": str(e)}}
                        )
                
                try:
                    sql_findings = await sql_analyzer.analyze(content, file_path)
                    for finding in sql_findings:
                        findings.append({
                            "analyzer": "SQLAnalyzer",
                            "rule_id": finding.rule_id,
                            "message": finding.message,
                            "severity": finding.severity.value,
                            "file": file_path,
                            "line": finding.line_start,
                            "suggestion": finding.suggestion,
                        })
                except Exception as e:
                    get_logger().warning(
                        "SQL analyzer failed",
                        extra={"context": {"file": file_path, "error": str(e)}}
                    )
                
                try:
                    security_findings = await security_analyzer.analyze(content, file_path)
                    for finding in security_findings:
                        findings.append({
                            "analyzer": "SecurityAnalyzer",
                            "rule_id": finding.rule_id,
                            "message": finding.message,
                            "severity": finding.severity.value,
                            "file": file_path,
                            "line": finding.line_start,
                            "suggestion": finding.suggestion,
                            "cwe_id": finding.cwe_id,
                        })
                except Exception as e:
                    get_logger().warning(
                        "Security analyzer failed",
                        extra={"context": {"file": file_path, "error": str(e)}}
                    )
                    
            except Exception as e:
                get_logger().warning(
                    "Failed to analyze file",
                    extra={"context": {"file": str(file), "error": str(e)}}
                )
        
        self.workiz_context["analyzer_findings"] = findings
        
        get_logger().info(
            "Language analyzers completed",
            extra={"context": {
                "pr_url": self.pr_url,
                "findings_count": len(findings),
                "files_analyzed": len(files) - skipped_files,
                "files_skipped": skipped_files,
            }}
        )

    async def _run_custom_rules(self) -> None:
        """Run custom rules engine on changed files."""
        get_logger().debug(
            "Running custom rules engine",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        rules_engine = get_rules_engine()
        await rules_engine.load_rules()
        
        files_content = {}
        files = self.git_provider.get_files()
        
        for file in files:
            try:
                file_path = file.filename if hasattr(file, 'filename') else str(file)
                
                # Skip non-code files
                if not _should_analyze_file(file_path):
                    continue
                
                try:
                    content = self.git_provider.get_pr_file_content(file_path, self.git_provider.pr.head.ref)
                    if content:
                        files_content[file_path] = content
                except Exception:
                    continue
            except Exception:
                continue
        
        rule_findings = await rules_engine.apply_rules(files_content)
        
        self.workiz_context["rules_findings"] = [
            {
                "rule": f.rule_id,
                "rule_name": f.rule_name,
                "message": f.message,
                "severity": f.severity,
                "file": f.file_path,
                "line": f.line_start,
                "suggestion": f.suggestion,
            }
            for f in rule_findings
        ]
        
        get_logger().info(
            "Custom rules engine completed",
            extra={"context": {
                "pr_url": self.pr_url,
                "findings_count": len(rule_findings),
                "files_checked": len(files_content),
            }}
        )

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
                    repo = self.git_provider.repo
                    full_name = repo.full_name if hasattr(repo, 'full_name') else str(repo)
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

    def _collect_all_findings(self) -> list[dict]:
        """
        Collect all findings from analyzers and rules into a unified list.
        
        Returns:
            List of normalized finding dicts with keys:
            - title: Issue title
            - severity: "High", "Medium", or "Low"
            - message: Detailed description
            - file: File path
            - line: Line number
            - suggestion: Suggested fix (optional)
            - rule_id: Rule/analyzer identifier
            - source: "analyzer" or "rule"
        """
        all_findings = []
        
        for f in self.workiz_context.get("analyzer_findings", []):
            all_findings.append({
                "title": f.get("rule_id", f.get("analyzer", "Issue")),
                "severity": self._normalize_severity(f.get("severity", "warning")),
                "message": f.get("message", "Issue detected"),
                "file": f.get("file", "unknown"),
                "line": f.get("line", 1),
                "suggestion": f.get("suggestion", ""),
                "rule_id": f.get("rule_id", ""),
                "source": "analyzer",
            })
        
        for f in self.workiz_context.get("rules_findings", []):
            all_findings.append({
                "title": f.get("rule_name", f.get("rule", "Rule Violation")),
                "severity": self._normalize_severity(f.get("severity", "warning")),
                "message": f.get("message", "Rule violation detected"),
                "file": f.get("file", "unknown"),
                "line": f.get("line", 1),
                "suggestion": f.get("suggestion", ""),
                "rule_id": f.get("rule", ""),
                "source": "rule",
            })
        
        # Deduplicate findings by (file, line, rule_id)
        return _deduplicate_findings(all_findings)
    
    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity string to High/Medium/Low."""
        sev_lower = severity.lower().strip()
        if sev_lower in ("error", "failure", "critical", "high"):
            return "High"
        elif sev_lower in ("warning", "medium"):
            return "Medium"
        else:
            return "Low"
    
    def _should_include_finding(self, severity: str) -> bool:
        """Check if finding passes severity threshold."""
        severity_order = {"high": 3, "medium": 2, "low": 1}
        threshold_value = severity_order.get(self.severity_threshold.lower(), 1)
        finding_value = severity_order.get(severity.lower(), 1)
        return finding_value >= threshold_value

    def _get_diff_hunk_ranges(self) -> dict[str, list[dict]]:
        """
        Get the valid line ranges for each file in the PR diff.
        
        Delegates to a shared utility on the git_provider to avoid code duplication.
        """
        try:
            return self.git_provider.get_hunk_ranges()
        except Exception as e:
            get_logger().warning("Failed to get diff hunk ranges", {
                "error": str(e),
                "pr_url": self.pr_url,
            })
            return {}

    def _is_line_in_diff(self, file_path: str, line: int, hunk_ranges: dict[str, list[dict]]) -> bool:
        """Check if a specific line is within any diff hunk for the file."""
        if file_path not in hunk_ranges:
            return False
        
        for hunk in hunk_ranges[file_path]:
            if hunk['start'] <= line <= hunk['end']:
                return True
        return False

    def _adjust_finding_to_diff(
        self, 
        finding: dict, 
        hunk_ranges: dict,
        max_distance: int = 10
    ) -> dict:
        """
        Adjust finding line number to fit inside a valid diff hunk.
        
        Strategy:
        1. If line is inside a hunk → use as-is
        2. If line is within max_distance of a hunk → adjust to hunk boundary
        3. If line is far from any hunk → mark for skipping (skip_inline=True)
        
        Args:
            finding: Dict with file, line, and other finding data
            hunk_ranges: Output from _get_diff_hunk_ranges()
            max_distance: Max lines away from hunk to still adjust (default 10)
            
        Returns:
            Modified finding dict with potentially adjusted line and side parameter
        """
        file_path = finding.get('file', '').strip()
        line = int(finding.get('line', 1))
        
        if file_path not in hunk_ranges:
            finding['skip_inline'] = True
            finding['skip_reason'] = 'file_not_in_diff'
            return finding
        
        ranges = hunk_ranges[file_path]
        
        for hunk in ranges:
            if hunk['start'] <= line <= hunk['end']:
                finding['side'] = hunk['side']
                finding['adjusted'] = False
                return finding
        
        min_distance = float('inf')
        nearest_hunk = None
        best_adjusted_line = None
        
        for hunk in ranges:
            dist_to_end = line - hunk['end']
            dist_from_start = hunk['start'] - line
            
            if dist_to_end > 0 and dist_to_end < min_distance:
                min_distance = dist_to_end
                nearest_hunk = hunk
                best_adjusted_line = hunk['end']
            elif dist_from_start > 0 and dist_from_start < min_distance:
                min_distance = dist_from_start
                nearest_hunk = hunk
                best_adjusted_line = hunk['start']
        
        if nearest_hunk and min_distance <= max_distance:
            finding['original_line'] = line
            finding['line'] = best_adjusted_line
            finding['side'] = nearest_hunk['side']
            finding['adjusted'] = True
            finding['adjustment_distance'] = min_distance
            get_logger().info(f"Adjusted finding line from {line} to {best_adjusted_line} (distance: {min_distance})", {
                "file": file_path,
                "original_line": line,
                "adjusted_line": best_adjusted_line,
                "rule_id": finding.get('rule_id', 'unknown'),
            })
            return finding
        
        finding['skip_inline'] = True
        finding['skip_reason'] = f'too_far_from_diff (distance: {min_distance})'
        return finding

    async def _publish_inline_review_comments(self) -> None:
        """
        Publish each finding as an individual inline review comment.
        
        Creates Bugbot-style comments that appear:
        - Inline on the specific code lines in "Files Changed" tab
        - In the "Conversation" tab as part of a review thread
        
        Uses smart line adjustment to ensure comments land on valid diff lines:
        - If finding line is inside a diff hunk → post directly
        - If finding line is near a hunk (within 10 lines) → adjust to hunk boundary
        - If finding line is far from any hunk → skip (log warning)
        
        Uses event="COMMENT" to ensure comments are non-blocking.
        """
        all_findings = self._collect_all_findings()
        
        if not all_findings:
            get_logger().info("No findings to publish as inline comments", {
                "pr_url": self.pr_url,
            })
            return
        
        try:
            branch = self.git_provider.pr.head.ref if hasattr(self.git_provider.pr, 'head') else "main"
            self._branch = branch
        except Exception:
            self._branch = "main"
        
        hunk_ranges = self._get_diff_hunk_ranges()
        
        if not hunk_ranges:
            get_logger().warning("No diff hunks found - cannot post inline comments", {
                "pr_url": self.pr_url,
            })
            return
        
        comments = []
        skipped_not_in_diff = 0
        skipped_severity = 0
        adjusted_count = 0
        
        for finding in all_findings:
            if not self._should_include_finding(finding["severity"]):
                skipped_severity += 1
                continue
            
            adjusted_finding = self._adjust_finding_to_diff(finding, hunk_ranges)
            
            if adjusted_finding.get('skip_inline', False):
                skipped_not_in_diff += 1
                get_logger().debug(f"Skipping finding - {adjusted_finding.get('skip_reason', 'unknown')}", {
                    "file": adjusted_finding.get('file'),
                    "line": adjusted_finding.get('original_line', adjusted_finding.get('line')),
                    "rule_id": adjusted_finding.get('rule_id', 'unknown'),
                })
                continue
            
            if adjusted_finding.get('adjusted', False):
                adjusted_count += 1
            
            if len(comments) >= self.max_inline_comments:
                get_logger().info(f"Reached max inline comments limit ({self.max_inline_comments})", {
                    "pr_url": self.pr_url,
                    "total_findings": len(all_findings),
                })
                break
            
            side = adjusted_finding.get('side', 'RIGHT')
            
            finding_id = f"{adjusted_finding.get('rule_id', 'unknown')}_{adjusted_finding['file']}_{adjusted_finding['line']}"
            
            body = format_inline_comment(
                title=adjusted_finding["title"],
                severity=adjusted_finding["severity"],
                description=adjusted_finding["message"],
                file_path=adjusted_finding["file"],
                line=adjusted_finding["line"],
                suggestion=adjusted_finding.get("suggestion", ""),
                cursor_redirect_url=self.cursor_redirect_url if self.cursor_redirect_url else "",
                org=self._org,
                repo=self._repo,
                branch=self._branch,
                rule_id=adjusted_finding.get("rule_id", ""),
                pr_number=self.git_provider.pr_num if hasattr(self.git_provider, 'pr_num') else None,
                pr_url=self.pr_url,
                finding_id=finding_id,
            )
            
            comments.append({
                "path": adjusted_finding["file"],
                "line": adjusted_finding["line"],
                "side": side,
                "body": body,
            })
        
        get_logger().info("Prepared findings for inline comments", {
            "pr_url": self.pr_url,
            "total_findings": len(all_findings),
            "comments_to_post": len(comments),
            "adjusted_to_hunk": adjusted_count,
            "skipped_not_in_diff": skipped_not_in_diff,
            "skipped_severity": skipped_severity,
        })
        
        if not comments:
            get_logger().info("No comments passed severity threshold", {
                "pr_url": self.pr_url,
                "threshold": self.severity_threshold,
                "total_findings": len(all_findings),
            })
            return
        
        try:
            self.git_provider.create_review_with_inline_comments(
                comments=comments,
                event="COMMENT",
            )
            
            get_logger().info("Published inline review comments", {
                "pr_url": self.pr_url,
                "comment_count": len(comments),
                "total_findings": len(all_findings),
                "threshold": self.severity_threshold,
            })
            
        except Exception as e:
            error_str = str(e)
            if "422" in error_str and "Line could not be resolved" in error_str:
                get_logger().warning("Some inline comments couldn't be posted (lines not in diff)", {
                    "pr_url": self.pr_url,
                    "comment_count": len(comments),
                    "error": error_str[:200],
                })
                await self._publish_inline_comments_with_fallback(comments)
            else:
                get_logger().error("Failed to publish inline review comments", {
                    "pr_url": self.pr_url,
                    "error": str(e),
                    "comment_count": len(comments),
                })
                raise
    
    async def _publish_inline_comments_with_fallback(self, comments: list[dict]) -> None:
        """
        Fallback: Try posting comments one by one, skipping those that fail.
        
        GitHub returns 422 when a comment line isn't in the diff. This method
        posts comments individually, logging which ones fail.
        """
        success_count = 0
        failed_count = 0
        
        for comment in comments:
            try:
                self.git_provider.create_review_with_inline_comments(
                    comments=[comment],
                    event="COMMENT",
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                get_logger().debug("Skipped comment (line not in diff)", {
                    "file": comment.get("path"),
                    "line": comment.get("line"),
                    "error": str(e)[:100],
                })
        
        get_logger().info("Published inline comments (with fallback)", {
            "pr_url": self.pr_url,
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(comments),
        })

    async def _create_check_run_with_findings(self) -> None:
        """
        Create a GitHub Check Run with annotations for all findings.
        
        This enables:
        - Inline annotations on the PR's Files Changed tab
        - "Fix in Cursor" action buttons
        - Better visibility of issues in the Checks tab
        """
        all_findings = []
        
        for f in self.workiz_context.get("analyzer_findings", []):
            all_findings.append({
                "type": "analyzer",
                "source": f.get("analyzer", "unknown"),
                **f
            })
        
        for f in self.workiz_context.get("rules_findings", []):
            all_findings.append({
                "type": "rule",
                "source": f.get("rule", "unknown"),
                **f
            })
        
        if not all_findings:
            get_logger().debug("No findings to create check run for", {
                "pr_url": self.pr_url
            })
            return
        
        try:
            head_sha = self.git_provider.last_commit_id.sha
            
            builder = CheckRunBuilder(self.check_run_name, head_sha)
            
            severity_counts = {"failure": 0, "warning": 0, "notice": 0}
            for f in all_findings:
                sev = f.get("severity", "warning").lower()
                if sev in ("error", "failure", "critical", "high"):
                    severity_counts["failure"] += 1
                elif sev in ("warning", "medium"):
                    severity_counts["warning"] += 1
                else:
                    severity_counts["notice"] += 1
            
            if severity_counts["failure"] > 0:
                conclusion = "failure"
            elif severity_counts["warning"] > 0:
                conclusion = "action_required"
            else:
                conclusion = "neutral"
            
            builder.set_status("completed", conclusion)
            
            summary = f"Found {len(all_findings)} issues: "
            summary += f"{severity_counts['failure']} errors, "
            summary += f"{severity_counts['warning']} warnings, "
            summary += f"{severity_counts['notice']} notices"
            
            builder.set_output(
                title=f"Review: {len(all_findings)} issues found",
                summary=summary,
                text="Click on annotations to see details. Use the 'Fix in Cursor' button to open fixes in your IDE."
            )
            
            from pr_agent.servers.github_app import store_action_context
            
            action_candidates = []
            
            for i, finding in enumerate(all_findings[:50]):
                file_path = finding.get("file", "unknown")
                line = finding.get("line", 1)
                message = finding.get("message", "Issue detected")
                severity = finding.get("severity", "warning").lower()
                source = finding.get("source", "analyzer")
                suggestion = finding.get("suggestion", "")
                
                if severity in ("error", "failure", "critical", "high"):
                    level = AnnotationLevel.FAILURE
                elif severity in ("warning", "medium"):
                    level = AnnotationLevel.WARNING
                else:
                    level = AnnotationLevel.NOTICE
                
                title = f"[{source}] {finding.get('rule_id', '')}".strip("[] ")
                
                annotation_message = message
                if suggestion:
                    annotation_message += f"\n\nSuggested fix: {suggestion}"
                
                builder.add_annotation(
                    path=file_path,
                    start_line=line,
                    message=annotation_message,
                    level=level,
                    title=title[:255],
                )
                
                if level in (AnnotationLevel.FAILURE, AnnotationLevel.WARNING):
                    action_candidates.append({
                        "finding": finding,
                        "index": i,
                        "severity_rank": 0 if level == AnnotationLevel.FAILURE else 1
                    })
            
            action_candidates.sort(key=lambda x: (x["severity_rank"], x["index"]))
            
            for candidate in action_candidates[:3]:
                finding = candidate["finding"]
                file_path = finding.get("file", "unknown")
                line = finding.get("line", 1)
                
                identifier = encode_action_identifier(file_path, line, finding.get("rule_id", ""))
                
                store_action_context(identifier, {
                    "file_path": file_path,
                    "line": line,
                    "issue_type": finding.get("rule_id") or finding.get("source", "Issue"),
                    "message": finding.get("message", ""),
                    "suggestion": finding.get("suggestion", ""),
                    "code_context": "",
                    "pr_url": self.pr_url,
                })
                
                short_file = file_path.split("/")[-1][:10]
                builder.add_action(
                    label=f"Fix {short_file}:{line}"[:20],
                    identifier=identifier,
                    description="Open Cursor AI to fix"[:40],
                )
            
            check_run_data = builder.build()
            
            self.git_provider.create_check_run(**check_run_data)
            
            get_logger().info("Created check run with findings", {
                "pr_url": self.pr_url,
                "findings_count": len(all_findings),
                "annotations_count": min(len(all_findings), 50),
                "actions_count": min(len(action_candidates), 3),
            })
            
        except Exception as e:
            import traceback
            get_logger().error("Failed to create check run", {
                "pr_url": self.pr_url,
                "error": str(e),
                "traceback": traceback.format_exc(),
            })

    def _enhance_review_vars(self) -> None:
        """Add Workiz context to review variables for prompt injection."""
        workiz_context_str = self._format_workiz_context()
        
        if workiz_context_str:
            extra_instructions = self.vars.get("extra_instructions", "")
            self.vars["extra_instructions"] = (
                f"{extra_instructions}\n\n"
                f"## Workiz-Specific Context\n{workiz_context_str}"
            )

    def _format_workiz_context(self) -> str:
        """Format Workiz context for prompt injection."""
        sections = []
        
        if self.workiz_context["cross_repo_context"]:
            sections.append(
                "### Cross-Repository Context\n"
                f"{self.workiz_context['cross_repo_context']}"
            )
        
        if self.workiz_context["jira_context"]:
            sections.append(
                "### Jira Ticket Context\n"
                f"{self.workiz_context['jira_context']}"
            )
        
        if self.workiz_context["rules_findings"]:
            findings_with_links = self._format_findings_with_cursor_links(
                self.workiz_context["rules_findings"],
                finding_type="rule"
            )
            sections.append(
                f"### Custom Rules Findings\n{findings_with_links}"
            )
        
        if self.workiz_context["analyzer_findings"]:
            findings_with_links = self._format_findings_with_cursor_links(
                self.workiz_context["analyzer_findings"],
                finding_type="analyzer"
            )
            sections.append(
                f"### Language Analyzer Findings\n{findings_with_links}"
            )
        
        return "\n\n".join(sections)
    
    def _format_findings_with_cursor_links(
        self,
        findings: list,
        finding_type: str = "analyzer"
    ) -> str:
        """
        Format findings with Fix in Cursor deep links.
        
        Args:
            findings: List of finding dictionaries
            finding_type: Either "analyzer" or "rule"
        
        Returns:
            Formatted markdown string with Cursor links
        """
        if self.use_inline_comments or not findings:
            if finding_type == "rule":
                return "\n".join(
                    f"- [{f.get('severity', 'warning')}] {f.get('rule', 'unknown')}: {f.get('message', '')}"
                    for f in findings
                )
            else:
                return "\n".join(
                    f"- [{f.get('analyzer', 'unknown')}] {f.get('message', '')}"
                    for f in findings
                )
        
        normalized_findings = []
        for f in findings:
            normalized = {
                "file": f.get("file", "unknown"),
                "line": f.get("line", 1),
                "message": f.get("message", "Issue detected"),
                "severity": f.get("severity", "warning"),
                "suggestion": f.get("suggestion", "Review and fix this issue"),
                "rule_id": f.get("rule_id") or f.get("rule"),
            }
            normalized_findings.append(normalized)
        
        return self.comment_formatter.add_cursor_links_to_findings(
            normalized_findings,
            format_type="inline"
        )

    def _prepare_pr_review(self) -> str:
        """
        Override base method to add Fix in Cursor links to the review output.
        """
        markdown_text = super()._prepare_pr_review()
        
        if self.use_inline_comments or not markdown_text:
            return markdown_text
        
        markdown_text = self._add_cursor_links_to_issues(markdown_text)
        
        return markdown_text
    
    def _add_cursor_links_to_issues(self, markdown_text: str) -> str:
        """
        Add Fix in Cursor links to key issues in the review output.
        
        The review output uses HTML format with links like:
        <a href='...#diff-...R{start}-R{end}'><strong>Issue Header</strong></a>
        
        We add Cursor links after each issue's code block before </details>.
        """
        html_link_pattern = r"<a href='([^']*#diff-[^']*R(\d+)-R(\d+))'><strong>([^<]+)</strong></a>\s*\n\n([^<]+)\n</summary>"
        
        def add_cursor_link(match):
            github_url = match.group(1)
            start_line = int(match.group(2))
            issue_header = match.group(4)
            issue_content = match.group(5)
            original_text = match.group(0)
            
            file_match = re.search(r'/([^/]+\.(ts|tsx|js|jsx|py|php|java|go|rb|rs|cs))R\d+', github_url)
            file_path = file_match.group(1) if file_match else "unknown"
            
            path_match = re.search(r'#diff-[a-f0-9]+R', github_url)
            if path_match:
                file_parts = github_url.split('/files#')[0].split('/')
                if len(file_parts) > 0:
                    pass
            
            cursor_url = self.comment_formatter._build_cursor_agent_url(
                issue_type=issue_header,
                file_path=file_path,
                line_number=start_line,
                suggestion=issue_content.strip()[:200],
                rule_id=None,
            )
            
            cursor_link = f"\n\n[🔧 Fix in Cursor]({cursor_url})"
            
            return original_text.replace("</summary>", f"{cursor_link}\n</summary>")
        
        enhanced_text = re.sub(html_link_pattern, add_cursor_link, markdown_text, flags=re.DOTALL)
        
        simple_details_pattern = r"(</details>)"
        details_blocks = list(re.finditer(r"<details><summary>.*?</details>", markdown_text, re.DOTALL))
        
        for block in details_blocks:
            block_text = block.group(0)
            
            href_match = re.search(r"href='[^']*#diff-[^']*R(\d+)", block_text)
            if not href_match:
                continue
                
            start_line = int(href_match.group(1))
            
            header_match = re.search(r"<strong>([^<]+)</strong>", block_text)
            issue_header = header_match.group(1) if header_match else "Issue"
            
            file_match = re.search(r"```(\w+)\n(.*?)```", block_text, re.DOTALL)
            
            cursor_url = self.comment_formatter._build_cursor_agent_url(
                issue_type=issue_header,
                file_path="file",
                line_number=start_line,
                suggestion=f"Fix the '{issue_header}' issue identified in this code review",
                rule_id=None,
            )
            
            if "</details>" in block_text and f"[🔧" not in block_text:
                new_block = block_text.replace("</details>", f"\n\n[🔧 Fix in Cursor]({cursor_url})\n\n</details>")
                enhanced_text = enhanced_text.replace(block_text, new_block)
        
        return enhanced_text

    async def _store_review_history(self) -> None:
        """Store review in database for analytics and learning."""
        get_logger().debug(
            "Storing review history",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        try:
            from pr_agent.db.review_history import save_review
            
            pr_info = self.git_provider.pr
            repository = getattr(self.git_provider, 'repo', None)
            if repository:
                repo_name = repository.full_name if hasattr(repository, 'full_name') else str(repository)
            else:
                repo_name = self._extract_repo_from_url()
            
            pr_number = pr_info.number if hasattr(pr_info, 'number') else 0
            pr_title = pr_info.title if hasattr(pr_info, 'title') else ""
            pr_author = pr_info.user.login if hasattr(pr_info, 'user') and hasattr(pr_info.user, 'login') else "unknown"
            
            review_output = {
                "prediction": self.prediction[:1000] if self.prediction else None,
                "workiz_findings": self.workiz_context,
            }
            
            findings_count = (
                len(self.workiz_context.get("rules_findings", [])) +
                len(self.workiz_context.get("analyzer_findings", []))
            )
            
            suggestions_count = sum(
                1 for f in self.workiz_context.get("analyzer_findings", [])
                if f.get("suggestion")
            ) + sum(
                1 for f in self.workiz_context.get("rules_findings", [])
                if f.get("suggestion")
            )
            
            duration_ms = int((time.time() - self._start_time) * 1000) if self._start_time else None
            model_used = get_settings().config.get("model", "unknown")
            
            await save_review(
                pr_url=self.pr_url,
                pr_number=pr_number,
                repository=repo_name,
                pr_title=pr_title,
                pr_author=pr_author,
                review_type="auto_review" if getattr(self, 'is_auto', False) else "review",
                review_output=review_output,
                findings_count=findings_count,
                suggestions_count=suggestions_count,
                workiz_context=self.workiz_context,
                duration_ms=duration_ms,
                model_used=model_used,
            )
            
            get_logger().info(
                "Review history stored",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "findings_count": findings_count,
                    "suggestions_count": suggestions_count,
                }}
            )
            
        except Exception as e:
            get_logger().warning(
                "Failed to store review history",
                extra={"context": {"pr_url": self.pr_url, "error": str(e)}}
            )
    
    def _extract_repo_from_url(self) -> str:
        """Extract repository name from PR URL."""
        try:
            parts = self.pr_url.split("/")
            if "github.com" in self.pr_url and len(parts) >= 5:
                return f"{parts[-4]}/{parts[-3]}"
        except Exception:
            pass
        return "unknown/unknown"

    async def _track_api_usage(self) -> None:
        """Track API usage for cost monitoring."""
        duration_ms = int((time.time() - self._start_time) * 1000) if self._start_time else 0
        
        get_logger().debug(
            "Tracking API usage",
            extra={"context": {
                "pr_url": self.pr_url,
                "duration_ms": duration_ms,
            }}
        )
        
        try:
            from pr_agent.db.api_usage import track_api_call
            
            model = get_settings().config.get("model", "unknown")
            
            input_tokens = self._estimate_input_tokens()
            output_tokens = self._estimate_output_tokens()
            
            await track_api_call(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=duration_ms,
                pr_url=self.pr_url,
                command="review",
                success=True,
            )
            
        except Exception as e:
            get_logger().warning(
                "Failed to track API usage",
                extra={"context": {"pr_url": self.pr_url, "error": str(e)}}
            )
    
    def _estimate_input_tokens(self) -> int:
        """Estimate input tokens from diff and context sizes."""
        try:
            diff_size = len(self.patches_diff) if self.patches_diff else 0
            context_size = len(str(self.workiz_context)) if self.workiz_context else 0
            return (diff_size + context_size) // 4
        except Exception:
            return 0
    
    def _estimate_output_tokens(self) -> int:
        """Estimate output tokens from prediction size."""
        try:
            return len(self.prediction) // 4 if self.prediction else 0
        except Exception:
            return 0

    def get_workiz_findings_summary(self) -> dict[str, Any]:
        """Get summary of all Workiz-specific findings."""
        return {
            "rules_findings_count": len(self.workiz_context["rules_findings"]),
            "analyzer_findings_count": len(self.workiz_context["analyzer_findings"]),
            "has_cross_repo_context": self.workiz_context["cross_repo_context"] is not None,
            "has_jira_context": self.workiz_context["jira_context"] is not None,
            "findings": {
                "rules": self.workiz_context["rules_findings"],
                "analyzers": self.workiz_context["analyzer_findings"],
            },
        }
