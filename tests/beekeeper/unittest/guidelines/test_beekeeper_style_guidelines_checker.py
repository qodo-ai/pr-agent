import os
import unittest
from pathlib import Path

from pr_agent.beekeeper.guidelines.beekeeper_style_guidelines_checker import BeekeeperStyleGuidelinesChecker
from pr_agent.beekeeper.guidelines.beekeeper_style_guidelines_fetcher import BeekeeperStyleGuidelinesFetcher


class TestBeekeeperStyleGuidelinesChecker(unittest.TestCase):
    def setUp(self):
        # Find the location of the real guidelines file
        current_file = Path(__file__)
        self.project_root = current_file.parents[3]
        self.test_resources_dir = self.project_root / "beekeeper" / "unittest" / "resources" / "guidelines"

        # Verify the guidelines file exists
        self.rdbms_file_path = os.path.join(self.test_resources_dir, "rdbms-guidelines.sql.md")
        if not os.path.exists(self.rdbms_file_path):
            raise FileNotFoundError(f"RDBMS guidelines file not found at {self.rdbms_file_path}")

        # Test configuration
        self.config = {
            "STYLE_GUIDELINES_REPO": "test/repo",
            "GITHUB_TOKEN": "test_token",
            "STYLE_GUIDELINES_BRANCH": "test_branch",
            "STYLE_GUIDELINES_FOLDER": "guidelines"
        }

    def test_direct_file_reading_with_rdbms_guidelines(self):
        """Test with the real RDBMS guidelines file directly from the file system"""
        # Create a custom fetcher that reads from the file system
        class LocalFileStyleGuidelinesFetcher(BeekeeperStyleGuidelinesFetcher):
            def __init__(self, repo_url, token, target_folder, rdbms_file_path):
                super().__init__(repo_url, token, target_folder)
                self.rdbms_file_path = rdbms_file_path
                # Immediately load the guidelines
                self.guidelines_cache = self.load_guidelines()

            def load_guidelines(self):
                guidelines = {}
                with open(self.rdbms_file_path, 'r') as f:
                    content = f.read()
                    import markdown
                    import html2text

                    text_maker = html2text.HTML2Text()
                    text_maker.ignore_links = False
                    plain_text = text_maker.handle(markdown.markdown(content))

                    # Use a key that matches what the checker expects
                    guidelines["rdbms-guidelines.sql.md"] = {
                        "markdown": content,
                        "plain_text": plain_text,
                        "file_types": ["sql"]  # Explicitly set for SQL files
                    }
                return guidelines

            def fetch_guidelines(self, force_refresh=False):
                if force_refresh or not self.guidelines_cache:
                    self.guidelines_cache = self.load_guidelines()
                return self.guidelines_cache

        # Create the checker with our custom fetcher
        checker = BeekeeperStyleGuidelinesChecker(self.config)
        checker.fetcher = LocalFileStyleGuidelinesFetcher(
            repo_url=None,
            token=None,
            target_folder=self.test_resources_dir,
            rdbms_file_path=self.rdbms_file_path
        )

        # Test with SQL files
        pr_files = {
            "database/schema.sql": "content of schema.sql",
            "database/migrations/V1__init.sql": "content of migration"
        }

        result = checker.check_files_against_guidelines(pr_files)

        # Print debug info
        print(f"Guidelines content: {checker.fetcher.guidelines_cache}")
        print(f"Test result: {result}")

        # Verify that RDBMS guidelines are included for SQL files
        self.assertIn("SHOULD avoid numeric based enums", result)
        self.assertIn("MUST NOT utilize stored procedures", result)

        # Test with non-SQL files
        pr_files = {
            "app/main.py": "content of main.py"
        }

        result = checker.check_files_against_guidelines(pr_files)

        # Verify that RDBMS guidelines are not included for Python files
        self.assertNotIn("RDBMS", result)


if __name__ == '__main__':
    unittest.main()