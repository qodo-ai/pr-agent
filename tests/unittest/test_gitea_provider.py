import io
import json
from unittest.mock import MagicMock

import pytest

from pr_agent.git_providers.gitea_provider import RepoApi


class TestRepoApiPagination:
    """Tests for pagination in RepoApi methods."""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        client = MagicMock()
        client.configuration.api_key = {'Authorization': 'token test-token'}
        return client

    @pytest.fixture
    def repo_api(self, mock_api_client):
        """Create a RepoApi instance with mocked client."""
        return RepoApi(mock_api_client)

    def _make_response(self, data):
        """Helper to create a mock response tuple with JSON data."""
        raw = io.BytesIO(json.dumps(data).encode('utf-8'))
        return (raw,)

    def test_get_change_file_pull_request_single_page(self, repo_api, mock_api_client):
        """Test fetching files when all fit in a single page."""
        files = [{'filename': f'file{i}.txt'} for i in range(10)]
        mock_api_client.call_api.return_value = self._make_response(files)

        result = repo_api.get_change_file_pull_request('owner', 'repo', 1)

        assert len(result) == 10
        assert result == files
        # Should only make one call since results < limit
        assert mock_api_client.call_api.call_count == 1

    def test_get_change_file_pull_request_multiple_pages(self, repo_api, mock_api_client):
        """Test fetching files across multiple pages."""
        # First page returns exactly 50 items (limit), indicating more may exist
        page1_files = [{'filename': f'file{i}.txt'} for i in range(50)]
        # Second page returns 25 items (< limit), indicating last page
        page2_files = [{'filename': f'file{i}.txt'} for i in range(50, 75)]

        mock_api_client.call_api.side_effect = [
            self._make_response(page1_files),
            self._make_response(page2_files),
        ]

        result = repo_api.get_change_file_pull_request('owner', 'repo', 1)

        assert len(result) == 75
        assert result == page1_files + page2_files
        assert mock_api_client.call_api.call_count == 2

    def test_get_change_file_pull_request_empty_response(self, repo_api, mock_api_client):
        """Test handling of empty response."""
        mock_api_client.call_api.return_value = self._make_response([])

        result = repo_api.get_change_file_pull_request('owner', 'repo', 1)

        assert result == []
        assert mock_api_client.call_api.call_count == 1

    def test_get_change_file_pull_request_pagination_url_params(self, repo_api, mock_api_client):
        """Test that pagination parameters are included in URL."""
        mock_api_client.call_api.return_value = self._make_response([{'filename': 'test.txt'}])

        repo_api.get_change_file_pull_request('owner', 'repo', 1)

        call_args = mock_api_client.call_api.call_args
        url = call_args[0][0]
        assert 'page=1' in url
        assert 'limit=50' in url

    def test_get_pr_commits_single_page(self, repo_api, mock_api_client):
        """Test fetching commits when all fit in a single page."""
        commits = [{'sha': f'commit{i}'} for i in range(10)]
        mock_api_client.call_api.return_value = self._make_response(commits)

        result = repo_api.get_pr_commits('owner', 'repo', 1)

        assert len(result) == 10
        assert result == commits
        assert mock_api_client.call_api.call_count == 1

    def test_get_pr_commits_multiple_pages(self, repo_api, mock_api_client):
        """Test fetching commits across multiple pages."""
        # First page returns exactly 50 items (limit), indicating more may exist
        page1_commits = [{'sha': f'commit{i}'} for i in range(50)]
        # Second page returns 20 items (< limit), indicating last page
        page2_commits = [{'sha': f'commit{i}'} for i in range(50, 70)]

        mock_api_client.call_api.side_effect = [
            self._make_response(page1_commits),
            self._make_response(page2_commits),
        ]

        result = repo_api.get_pr_commits('owner', 'repo', 1)

        assert len(result) == 70
        assert result == page1_commits + page2_commits
        assert mock_api_client.call_api.call_count == 2

    def test_get_pr_commits_empty_response(self, repo_api, mock_api_client):
        """Test handling of empty commits response."""
        mock_api_client.call_api.return_value = self._make_response([])

        result = repo_api.get_pr_commits('owner', 'repo', 1)

        assert result == []
        assert mock_api_client.call_api.call_count == 1

    def test_get_pr_commits_three_pages(self, repo_api, mock_api_client):
        """Test fetching commits across three pages."""
        page1 = [{'sha': f'commit{i}'} for i in range(50)]
        page2 = [{'sha': f'commit{i}'} for i in range(50, 100)]
        page3 = [{'sha': f'commit{i}'} for i in range(100, 110)]

        mock_api_client.call_api.side_effect = [
            self._make_response(page1),
            self._make_response(page2),
            self._make_response(page3),
        ]

        result = repo_api.get_pr_commits('owner', 'repo', 1)

        assert len(result) == 110
        assert mock_api_client.call_api.call_count == 3

    def test_pagination_handles_api_exception(self, repo_api, mock_api_client):
        """Test that API exceptions are handled gracefully."""
        from giteapy.rest import ApiException
        mock_api_client.call_api.side_effect = ApiException(status=500, reason="Server Error")

        result = repo_api.get_change_file_pull_request('owner', 'repo', 1)

        assert result == []

    def test_pagination_returns_partial_on_error(self, repo_api, mock_api_client):
        """Test that partial results are returned if error occurs mid-pagination."""
        from giteapy.rest import ApiException
        page1 = [{'filename': f'file{i}.txt'} for i in range(50)]
        
        mock_api_client.call_api.side_effect = [
            self._make_response(page1),
            ApiException(status=500, reason="Server Error"),
        ]

        result = repo_api.get_change_file_pull_request('owner', 'repo', 1)

        # Should return the items from the first page
        assert len(result) == 50
        assert result == page1
