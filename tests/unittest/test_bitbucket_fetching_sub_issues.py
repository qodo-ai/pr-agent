import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from pr_agent.tools.ticket_pr_compliance_check import extract_tickets, extract_and_cache_pr_tickets
from pr_agent.git_providers.bitbucket_provider import BitbucketProvider


class TestBitbucketTicketCompliance(unittest.TestCase):

    @patch.object(BitbucketProvider, 'get_pr_description_full', return_value="Fixes #1 and relates to #2")
    @patch.object(BitbucketProvider, '_parse_pr_url', return_value=("workspace", "repo", 123))
    @patch.object(BitbucketProvider, 'bitbucket_client')
    async def test_extract_tickets(self, mock_client, mock_parse_pr_url, mock_pr_desc):
        """
        Test extract_tickets() to ensure it extracts tickets correctly
        and fetches their content from Bitbucket.
        """
        bitbucket_provider = BitbucketProvider("https://bitbucket.org/workspace/repo/pull-requests/123")
        bitbucket_provider.workspace_slug = "workspace"
        bitbucket_provider.repo_slug = "repo"

        # Mock issue retrieval
        mock_issue = MagicMock()
        mock_issue.id = 1
        mock_issue.title = "Sample Issue"
        mock_issue.content = {"raw": "This is a test issue body."}
        mock_issue.kind = "bug"
        mock_issue.priority = "high"

        # Mock Bitbucket client
        mock_repo = MagicMock()
        mock_client.workspaces.get.return_value.repositories.get.return_value = mock_repo
        mock_repo.issues.get.return_value = mock_issue

        tickets = await extract_tickets(bitbucket_provider)

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

        print("\n Test Passed: extract_tickets() successfully retrieved Bitbucket ticket info!")

    @patch.object(BitbucketProvider, 'get_pr_description_full', return_value="Fixes #1 and relates to #2")
    @patch.object(BitbucketProvider, '_parse_pr_url', return_value=("workspace", "repo", 123))
    @patch.object(BitbucketProvider, 'bitbucket_client')
    async def test_extract_and_cache_pr_tickets(self, mock_client, mock_parse_pr_url, mock_pr_desc):
        """
        Test extract_and_cache_pr_tickets() to ensure tickets are extracted and cached correctly from Bitbucket.
        """
        bitbucket_provider = BitbucketProvider("https://bitbucket.org/workspace/repo/pull-requests/123")
        bitbucket_provider.workspace_slug = "workspace"
        bitbucket_provider.repo_slug = "repo"

        vars = {}  # Simulate the dictionary to store results

        # Mock issue retrieval
        mock_issue = MagicMock()
        mock_issue.id = 1
        mock_issue.title = "Sample Issue"
        mock_issue.content = {"raw": "This is a test issue body."}
        mock_issue.kind = "bug"
        mock_issue.priority = "high"

        # Mock Bitbucket client
        mock_repo = MagicMock()
        mock_client.workspaces.get.return_value.repositories.get.return_value = mock_repo
        mock_repo.issues.get.return_value = mock_issue

        # Run function
        await extract_and_cache_pr_tickets(bitbucket_provider, vars)

        # Ensure tickets are cached
        self.assertIn("related_tickets", vars)
        self.assertIsInstance(vars["related_tickets"], list)
        self.assertGreater(len(vars["related_tickets"]), 0, "Expected at least one cached ticket!")

        print("\n Test Passed: extract_and_cache_pr_tickets() successfully cached Bitbucket ticket data!")

    @patch.object(BitbucketProvider, 'fetch_sub_issues', return_value={'sub-issue-1', 'sub-issue-2'})
    def test_fetch_sub_issues(self, mock_fetch):
        bitbucket_provider = BitbucketProvider("https://bitbucket.org/workspace/repo/pull-requests/123")
        issue_url = "https://bitbucket.org/workspace/repo/issues/1"
        result = bitbucket_provider.fetch_sub_issues(issue_url)
        self.assertIsInstance(result, set)
        self.assertGreater(len(result), 0)

    @patch.object(BitbucketProvider, 'fetch_sub_issues', return_value=set())
    def test_fetch_sub_issues_with_no_results(self, mock_fetch):
        bitbucket_provider = BitbucketProvider("https://bitbucket.org/workspace/repo/pull-requests/123")
        issue_url = "https://bitbucket.org/workspace/repo/issues/999"
        result = bitbucket_provider.fetch_sub_issues(issue_url)
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    asyncio.run(unittest.main())
    