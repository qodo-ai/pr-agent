import unittest
from pathlib import Path
from pr_agent.beekeeper.tools.beekeeper_pr_best_practices_formatter import BeekeeperPRBestPracticesFormatter

class TestBeekeeperPRBestPracticesFormatter(unittest.TestCase):
    def setUp(self):
        # Find the location of the test resources
        current_file = Path(__file__)
        self.project_root = current_file.parents[4]
        self.test_resources_dir = self.project_root / "tests" / "beekeeper" / "unittest" / "resources" / "guidelines"

    def test_format_guidelines_rdbms(self):
        # Load the rdbms guidelines markdown file
        rdbms_guidelines_path = self.test_resources_dir / "rdbms-guidelines.sql.md"
        with open(rdbms_guidelines_path, 'r') as f:
            markdown_content = f.read()

        # Create mock relevant guidelines dictionary
        mock_guidelines = {
            str(rdbms_guidelines_path): {
                "markdown": markdown_content,
                "file_types": ["sql"],
            }
        }

        # Initialize formatter and format the guidelines
        formatter = BeekeeperPRBestPracticesFormatter()
        formatted_guidelines = formatter.format_guidelines(mock_guidelines)

        # Verify that the output contains properly formatted guidelines
        self.assertIn("- **[Sql-101]** MUST make use of tenant identifier column in all tables", formatted_guidelines)
        self.assertIn("- **[Sql-102]** MUST make use of index on tenant identifier column in all tables", formatted_guidelines)
        self.assertIn("- **[Sql-203]** MUST avoid cascading deletes", formatted_guidelines)
        self.assertIn("- **[Sql-204]** MUST NOT utilize stored procedures", formatted_guidelines)
        self.assertIn("- **[Sql-104]** SHOULD use meaningful column names", formatted_guidelines)
        self.assertIn("- **[Sql-207]** MAY utilize over-filtering for better performance", formatted_guidelines)

        # Verify the number of guidelines extracted
        guidelines_count = formatted_guidelines.count("- **[Sql-")
        self.assertEqual(guidelines_count, 16)  # Adjust this number based on actual guidelines in the file