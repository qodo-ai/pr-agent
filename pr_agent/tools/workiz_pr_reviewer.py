"""
Workiz-enhanced PR Reviewer

Extends the base PRReviewer with Workiz-specific features:
- Cross-repository context (RepoSwarm integration)
- Jira ticket context
- Custom rules engine
- Language-specific analyzers
- Review history storage
- API usage tracking
"""

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

    async def run(self) -> None:
        """
        Enhanced run method with Workiz-specific pipeline.
        
        Pipeline:
        1. Load cross-repo context (if enabled)
        2. Load Jira context (if ticket linked)
        3. Run language analyzers
        4. Run custom rules engine
        5. Execute base review with enhanced context
        6. Store review history
        7. Track API usage
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
                }}
            )

            await self._load_cross_repo_context()
            
            await self._load_jira_context()
            
            await self._run_language_analyzers()
            
            await self._run_custom_rules()
            
            self._enhance_review_vars()
            
            await super().run()
            
            await self._store_review_history()
            
            await self._track_api_usage()
            
            get_logger().info(
                "Workiz PR review completed",
                extra={"context": {
                    "pr_url": self.pr_url,
                    "duration_seconds": time.time() - self._start_time,
                    "rules_findings": len(self.workiz_context["rules_findings"]),
                    "analyzer_findings": len(self.workiz_context["analyzer_findings"]),
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
        
        for file in files:
            try:
                file_path = file.filename if hasattr(file, 'filename') else str(file)
                
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
                "files_analyzed": len(files),
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
            findings_str = "\n".join(
                f"- [{f['severity']}] {f['rule']}: {f['message']}"
                for f in self.workiz_context["rules_findings"]
            )
            sections.append(
                f"### Custom Rules Findings\n{findings_str}"
            )
        
        if self.workiz_context["analyzer_findings"]:
            findings_str = "\n".join(
                f"- [{f['analyzer']}] {f['message']}"
                for f in self.workiz_context["analyzer_findings"]
            )
            sections.append(
                f"### Language Analyzer Findings\n{findings_str}"
            )
        
        return "\n\n".join(sections)

    async def _store_review_history(self) -> None:
        """Store review in database for analytics and learning."""
        get_logger().debug(
            "Storing review history",
            extra={"context": {"pr_url": self.pr_url}}
        )
        
        # TODO: Implement in Phase 3.5
        # - Save PR details
        # - Save review comments
        # - Save suggestions
        # - Save findings
        pass

    async def _track_api_usage(self) -> None:
        """Track API usage for cost monitoring."""
        duration = time.time() - self._start_time
        
        get_logger().debug(
            "Tracking API usage",
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
