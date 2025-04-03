import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from pr_agent.beekeeper.tools.beekeeper_pr_best_practices import BeekeeperPRBestPracticesCheck


class TestBeekeeperPRBestPracticesCheck(unittest.TestCase):
    def setUp(self):
        # Find the location of the test resources
        current_file = Path(__file__)
        self.project_root = current_file.parents[4]
        self.test_resources_dir = self.project_root / "tests" / "beekeeper" / "unittest" / "resources" / "guidelines"

        # Load the rdbms guidelines markdown file for comparison
        self.rdbms_guidelines_path = self.test_resources_dir / "rdbms-guidelines.sql.md"
        with open(self.rdbms_guidelines_path, 'r') as f:
            self.markdown_content = f.read()

    @patch('pr_agent.beekeeper.tools.beekeeper_pr_best_practices.get_settings')
    @patch('pr_agent.beekeeper.tools.beekeeper_pr_best_practices.get_git_provider_with_context')
    @patch('pr_agent.beekeeper.tools.beekeeper_pr_best_practices.BeekeeperStyleGuidelinesFetcher')
    @patch('pr_agent.beekeeper.tools.beekeeper_pr_best_practices.get_main_pr_language')
    def test_get_best_practices_includes_sql_guidelines(self, mock_get_main_lang, mock_fetcher_class,
                                                        mock_git_provider, mock_settings):
        # Configure mock settings
        settings_mock = MagicMock()
        settings_mock.pr_best_practices = MagicMock()
        settings_mock.pr_best_practices.auto_extended_mode = False
        settings_mock.pr_best_practices.max_context_tokens = 80000
        settings_mock.pr_code_suggestions = MagicMock()
        settings_mock.pr_code_suggestions.num_code_suggestions_per_chunk = 5
        settings_mock.pr_code_suggestions.max_context_tokens = 100000
        settings_mock.pr_code_suggestions.extra_instructions = ""
        settings_mock.config = MagicMock()
        settings_mock.config.max_model_tokens = 100000
        settings_mock.beekeeper_pr_best_practices_prompt = MagicMock()
        settings_mock.beekeeper_pr_best_practices_prompt.system = "System prompt"
        settings_mock.beekeeper_pr_best_practices_prompt.user = "User prompt"
        mock_settings.return_value = settings_mock

        # Set up mocks
        mock_git_provider.return_value = MagicMock()
        mock_git_provider.return_value.get_files.return_value = [SimpleNamespace(
                filename='database.sql',
            )]
        mock_git_provider.return_value.pr = MagicMock()
        mock_git_provider.return_value.pr.title = "Update SQL schema"
        mock_git_provider.return_value.get_pr_branch.return_value = "feature/update-schema"
        mock_git_provider.return_value.get_pr_description.return_value = ("SQL schema update", [])
        mock_git_provider.return_value.get_commit_messages.return_value = "Update database schema"
        mock_git_provider.return_value.get_languages.return_value = {"sql": 100}
        mock_get_main_lang.return_value = "sql"

        # Mock fetcher to return our test guidelines
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.get_relevant_guidelines.return_value = {
            self.rdbms_guidelines_path: {
                "markdown": self.markdown_content,
                "file_types": ["sql"],
            }
        }

        # Create an instance of BeekeeperPRBestPracticesCheck with mocked dependencies
        bppc = BeekeeperPRBestPracticesCheck("https://github.com/org/repo/pull/123", cli_mode=True)

        # Check that the best practices includes the SQL guidelines
        best_practices = bppc._get_best_practices()

        # Verify SQL guideline content in the best practices
        self.assertIn("MUST make use of tenant identifier column in all tables", best_practices)
        self.assertIn("MUST avoid cascading deletes", best_practices)
        self.assertIn("MUST NOT utilize stored procedures", best_practices)
        self.assertIn("SHOULD use meaningful column names", best_practices)
        self.assertIn("MAY utilize over-filtering for better performance", best_practices)

        # Verify formatting as expected with SQL- prefixes and brackets
        self.assertIn("[Sql-", best_practices)

        # Verify the variables dictionary includes the best practices
        self.assertEqual(bppc.vars["best_practices"], best_practices)