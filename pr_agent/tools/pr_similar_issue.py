"""
PR Similar Issue Finder - Simplified with Fuzzy Matching

Uses rapidfuzz for fast, local fuzzy text matching instead of vector embeddings.
No external APIs or databases required.
"""

import time
from typing import List, Tuple, Dict
from rapidfuzz import fuzz, process

from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger


class PRSimilarIssue:
    """
    Find similar issues using fuzzy text matching.

    Replaces vector-based search (Pinecone/LanceDB/Qdrant + OpenAI embeddings)
    with simple, fast fuzzy matching using rapidfuzz.
    """

    def __init__(self, issue_url: str, ai_handler=None, args: list = None):
        """Initialize the similar issue finder."""
        if get_settings().config.git_provider != "github":
            raise Exception("Only github is supported for similar issue tool")

        self.cli_mode = get_settings().CONFIG.CLI_MODE
        self.max_issues_to_scan = get_settings().pr_similar_issue.max_issues_to_scan
        self.number_of_similar_issues = get_settings().pr_similar_issue.get(
            'number_of_similar_issues', 5
        )
        self.min_similarity_score = get_settings().pr_similar_issue.get(
            'min_similarity_score', 60
        )
        self.skip_comments = get_settings().pr_similar_issue.get(
            'skip_comments', False
        )

        self.issue_url = issue_url
        self.git_provider = get_git_provider()()

        # Parse issue URL
        repo_name, issue_number = self.git_provider._parse_issue_url(
            issue_url.split('=')[-1]
        )
        self.git_provider.repo = repo_name
        self.git_provider.repo_obj = self.git_provider.github_client.get_repo(repo_name)
        self.query_issue_number = issue_number

        # In-memory cache for issues
        self.issues_cache: Dict[int, Dict[str, str]] = {}

        get_logger().info(f"Initialized PRSimilarIssue for {repo_name} issue #{issue_number}")

    async def run(self):
        """Main execution method - find and post similar issues."""
        try:
            get_logger().info("Starting similar issue search...")

            # 1. Fetch all issues from GitHub
            get_logger().info("Fetching issues from GitHub...")
            repo_obj = self.git_provider.repo_obj
            issues_list = list(repo_obj.get_issues(state='all'))
            get_logger().info(f"Found {len(issues_list)} total issues")

            # 2. Index issues in memory
            get_logger().info("Indexing issues...")
            self._index_issues(issues_list)

            # 3. Get query issue details
            query_issue = repo_obj.get_issue(self.query_issue_number)
            query_title = query_issue.title
            query_body = query_issue.body or ""

            get_logger().info(f"Query issue: {query_title}")

            # 4. Find similar issues using fuzzy matching
            get_logger().info("Finding similar issues...")
            similar_issues = self._find_similar(
                query_title=query_title,
                query_body=query_body,
                skip_issue_number=self.query_issue_number,
                top_k=self.number_of_similar_issues
            )

            # 5. Post results
            if similar_issues:
                get_logger().info(f"Found {len(similar_issues)} similar issues")
                self._post_results(query_issue, similar_issues)
            else:
                get_logger().info("No similar issues found above threshold")
                if not get_settings().pr_similar_issue.get('skip_comments', False):
                    query_issue.create_comment("No similar issues found.")

            return similar_issues

        except Exception as e:
            get_logger().error(f"Error in PRSimilarIssue.run(): {e}")
            raise

    def _index_issues(self, issues_list: List) -> None:
        """
        Index issues in memory for fast searching.

        Args:
            issues_list: List of GitHub issue objects
        """
        counter = 0

        for issue in issues_list:
            # Skip pull requests
            if issue.pull_request:
                continue

            counter += 1
            if counter >= self.max_issues_to_scan:
                get_logger().info(f"Reached max issues to scan: {self.max_issues_to_scan}")
                break

            # Extract issue content
            title = issue.title
            body = issue.body or ""

            # Optionally include comments
            comments_text = ""
            if not self.skip_comments:
                try:
                    comments = list(issue.get_comments())
                    comments_text = " ".join([c.body for c in comments if c.body])
                except:
                    pass  # Comments not critical

            # Store in cache
            self.issues_cache[issue.number] = {
                'title': title,
                'body': body,
                'comments': comments_text,
                'url': issue.html_url,
                'state': issue.state,
            }

        get_logger().info(f"Indexed {len(self.issues_cache)} issues")

    def _find_similar(
        self,
        query_title: str,
        query_body: str,
        skip_issue_number: int = None,
        top_k: int = 5
    ) -> List[Tuple[float, int, str, str]]:
        """
        Find similar issues using fuzzy text matching.

        Args:
            query_title: Title of query issue
            query_body: Body of query issue
            skip_issue_number: Issue number to skip (the query issue itself)
            top_k: Number of similar issues to return

        Returns:
            List of tuples: (score, issue_number, title, url)
        """
        # Build query string (weight title more by repeating it)
        query_text = f"{query_title} {query_title} {query_body}"

        # Prepare choices for fuzzy matching
        choices = {}
        for issue_num, issue_data in self.issues_cache.items():
            # Skip the query issue itself
            if skip_issue_number and issue_num == skip_issue_number:
                continue

            # Build issue text (weight title 2x)
            issue_text = (
                f"{issue_data['title']} {issue_data['title']} "
                f"{issue_data['body']} {issue_data['comments']}"
            )
            choices[issue_num] = issue_text

        if not choices:
            get_logger().warning("No issues available for comparison")
            return []

        # Use rapidfuzz for fuzzy matching
        # token_sort_ratio: handles word order differences well
        results = process.extract(
            query_text,
            choices,
            scorer=fuzz.token_sort_ratio,
            limit=top_k * 2,  # Get extra in case we need to filter
        )

        # Filter by minimum score and format results
        similar_issues = []
        for matched_text, score, issue_num in results:
            if score >= self.min_similarity_score:
                issue_data = self.issues_cache[issue_num]
                similar_issues.append((
                    score,
                    issue_num,
                    issue_data['title'],
                    issue_data['url']
                ))

            # Stop once we have enough results
            if len(similar_issues) >= top_k:
                break

        return similar_issues

    def _post_results(
        self,
        query_issue,
        similar_issues: List[Tuple[float, int, str, str]]
    ) -> None:
        """
        Post similar issues as a comment.

        Args:
            query_issue: GitHub issue object to comment on
            similar_issues: List of (score, number, title, url) tuples
        """
        # Build comment
        comment_lines = ["### Similar Issues\n___\n"]

        for i, (score, number, title, url) in enumerate(similar_issues, 1):
            # Format score as percentage
            score_pct = f"{score:.1f}%"
            comment_lines.append(
                f"{i}. **[{title}]({url})** (similarity: {score_pct})\n"
            )

        similar_issues_str = "\n".join(comment_lines)

        # Post comment (unless skip_comments is True)
        if not get_settings().pr_similar_issue.get('skip_comments', False):
            try:
                query_issue.create_comment(similar_issues_str)
                get_logger().info("Posted similar issues comment")
            except Exception as e:
                get_logger().error(f"Failed to post comment: {e}")

        # Always log results
        get_logger().info(f"\n{similar_issues_str}")
