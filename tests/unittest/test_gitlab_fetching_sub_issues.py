import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from pr_agent.tools.ticket_pr_compliance_check import extract_tickets, extract_and_cache_pr_tickets
from pr_agent.git_providers.gitlab_provider import GitLabProvider


class TestGitLabTicketCompliance(unittest.TestCase):

    @patch.object(GitLabProvider, 'get_pr_description_full', return_value="Fixes #1 and relates to #2")
    @patch.object(GitLabProvider, '_parse_merge_request_url', return_value=("group/project", 123))
    @patch.object(GitLabProvider, 'gl')
    async def test_extract_tickets(self, mock_gl, mock_parse_mr_url, mock_pr_desc):
        """
        Test extract_tickets() to ensure it extracts tickets correctly
        and fetches their content from GitLab.
        """
        gitlab_provider = GitLabProvider("https://gitlab.com/group/project/-/merge_requests/123")
        gitlab_provider.id_project = "group/project"

        # Mock issue retrieval
        mock_issue = MagicMock()
        mock_issue.iid = 1
        mock_issue.title = "Sample Issue"
        mock_issue.description = "This is a test issue body."
        mock_issue.labels = ["bug", "high priority"]

        # Mock GitLab client
        mock_project = MagicMock()
        mock_gl.projects.get.return_value = mock_project
        mock_project.issues.get.return_value = mock_issue

        tickets = await extract_tickets(gitlab_provider)

        # Verify tickets were extracted correctly
        self.assertIsInstance(tickets, list)
        self.assertGreater(len(tickets), 0, "Expected at least one ticket!")

        # Verify ticket structure
        first_ticket = tickets[0]
        self.assertIn("ticket_id", first_ticket)
        self.assertIn("ticket_url", first_ticket)
        self.assertIn("title", first_ticket)
        self.assertIn("body", first_ticket)
        self.assertIn("labels", first_ticket)

        print("\n Test Passed: extract_tickets() successfully retrieved GitLab ticket info!")

    @patch.object(GitLabProvider, 'get_pr_description_full', return_value="Fixes #1 and relates to #2")
    @patch.object(GitLabProvider, '_parse_merge_request_url', return_value=("group/project", 123))
    @patch.object(GitLabProvider, 'gl')
    async def test_extract_and_cache_pr_tickets(self, mock_gl, mock_parse_mr_url, mock_pr_desc):
        """
        Test extract_and_cache_pr_tickets() to ensure tickets are extracted and cached correctly from GitLab.
        """
        gitlab_provider = GitLabProvider("https://gitlab.com/group/project/-/merge_requests/123")
        gitlab_provider.id_project = "group/project"

        vars = {}  # Simulate the dictionary to store results

        # Mock issue retrieval
        mock_issue = MagicMock()
        mock_issue.iid = 1
        mock_issue.title = "Sample Issue"
        mock_issue.description = "This is a test issue body."
        mock_issue.labels = ["bug", "high priority"]

        # Mock GitLab client
        mock_project = MagicMock()
        mock_gl.projects.get.return_value = mock_project
        mock_project.issues.get.return_value = mock_issue

        # Run function
        await extract_and_cache_pr_tickets(gitlab_provider, vars)

        # Ensure tickets are cached
        self.assertIn("related_tickets", vars)
        self.assertIsInstance(vars["related_tickets"], list)
        self.assertGreater(len(vars["related_tickets"]), 0, "Expected at least one cached ticket!")

        print("\n Test Passed: extract_and_cache_pr_tickets() successfully cached GitLab ticket data!")

    @patch.object(GitLabProvider, 'fetch_sub_issues', return_value={'sub-issue-1', 'sub-issue-2'})
    def test_fetch_sub_issues(self, mock_fetch):
        gitlab_provider = GitLabProvider("https://gitlab.com/group/project/-/merge_requests/123")
        issue_url = "https://gitlab.com/group/project/-/issues/1"
        result = gitlab_provider.fetch_sub_issues(issue_url)
        self.assertIsInstance(result, set)
        self.assertGreater(len(result), 0)

    @patch.object(GitLabProvider, 'fetch_sub_issues', return_value=set())
    def test_fetch_sub_issues_with_no_results(self, mock_fetch):
        gitlab_provider = GitLabProvider("https://gitlab.com/group/project/-/merge_requests/123")
        issue_url = "https://gitlab.com/group/project/-/issues/999"
        result = gitlab_provider.fetch_sub_issues(issue_url)
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    asyncio.run(unittest.main())
    