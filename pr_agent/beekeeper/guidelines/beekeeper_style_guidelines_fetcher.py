# pr_agent/beekeeper/guidelines/beekeeper_style_guidelines_fetcher.py
import os
from loguru import logger
from pathlib import Path
import markdown
import html2text

from pr_agent.beekeeper.github.github_helpers import get_all_files_of_type_in_repo_recursive

BEEKEEPER_GUIDELINES_FILENAME_FORMAT = '[random-name].[target-extension].md'

class BeekeeperStyleGuidelinesFetcher:
    def __init__(
            self,
            repo_url='git@github.com:beekpr/beekeeper-engineering-hub',
            token=None,
            branch="master",
            target_folder='guidelines'
    ):
        """
        Fetch style guidelines from a GitHub repository

        Args:
            repo_url: GitHub repository URL
            token: GitHub token for authentication
            branch: Branch to fetch guidelines from
            target_folder: Specific folder in the repo to fetch guidelines from (optional)
        """
        self.repo_url = repo_url
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.branch = branch
        self.target_folder = target_folder
        self.guidelines_cache = {}


    def fetch_guidelines(self, force_refresh=False):
        """Fetch all markdown files from the guidelines repository"""
        if self.guidelines_cache and not force_refresh:
            return self.guidelines_cache

        files = get_all_files_of_type_in_repo_recursive(self.token, self.repo_url, self.target_folder, self.branch, '.md')
        guidelines = self.parse_guidelines(files)

        self.guidelines_cache = guidelines
        logger.info(f"Fetched {len(guidelines)} style guideline files from {self.repo_url}/{self.target_folder or ''}")
        return guidelines


    def parse_guidelines(self, files):
        guidelines = {}
        try:
            for file in files:
                file_content = file.decoded_content.decode('utf-8')
                # Convert markdown to plain text
                text_maker = html2text.HTML2Text()
                text_maker.ignore_links = False
                plain_text = text_maker.handle(markdown.markdown(file_content))

                # Extract target extension from filename if it follows the naming convention
                filename = Path(file.path).name
                parts = filename.split('.')

                if len(parts) >= 3:  # Check for [name].[ext].md pattern
                    file_types = [parts[-2].lower()]  # Get the extension part

                guidelines[file.path] = {
                    "markdown": file_content,
                    "plain_text": plain_text,
                    "file_types": file_types  # Store the target extension
                }
        except Exception as e:
            logger.error(f"Error processing file {file.path}: {str(e)}")
        return guidelines


    def get_relevant_guidelines(self, file_paths):
        """Get guidelines relevant to the given file paths"""
        all_guidelines = self.fetch_guidelines()
        if not all_guidelines:
            return {}

        # Extract file extensions from PR files
        extensions = {Path(file).suffix.lstrip('.').lower() for file in file_paths if Path(file).suffix}

        # Match guidelines to file extensions
        relevant_guidelines = {}
        for guideline_path, content in all_guidelines.items():
            # First check if we have explicit file_types defined
            if content.get("file_types"):
                if any(ext in content["file_types"] for ext in extensions):
                    relevant_guidelines[guideline_path] = content
                    continue

            # Fallback: check for extension in the guideline filename
            guideline_filename = Path(guideline_path).name
            parts = guideline_filename.split('.')
            if len(parts) >= 3 and parts[-2].lower() in extensions:
                relevant_guidelines[guideline_path] = content
                continue

            # Also consider general guidelines
            if "general" in guideline_path.lower() or "common" in guideline_path.lower():
                relevant_guidelines[guideline_path] = content

        return relevant_guidelines