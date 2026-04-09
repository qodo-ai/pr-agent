import json
from io import BytesIO
from unittest.mock import MagicMock, patch


class TestGiteaProvider:
    @patch('pr_agent.git_providers.gitea_provider.get_settings')
    @patch('pr_agent.git_providers.gitea_provider.giteapy.ApiClient')
    def test_gitea_provider_auth_header(self, mock_api_client_cls, mock_get_settings):
        # Setup settings
        settings = MagicMock()
        settings.get.side_effect = lambda k, d=None: {
            'GITEA.URL': 'https://gitea.example.com',
            'GITEA.PERSONAL_ACCESS_TOKEN': 'test-token',
            'GITEA.REPO_SETTING': None,
            'GITEA.SKIP_SSL_VERIFICATION': False,
            'GITEA.SSL_CA_CERT': None
        }.get(k, d)
        mock_get_settings.return_value = settings

        # Setup ApiClient mock
        mock_api_client = mock_api_client_cls.return_value
        # Mock configuration object on client
        mock_api_client.configuration.api_key = {'Authorization': 'token test-token'}

        # Mock responses for calls made during initialization
        def call_api_side_effect(path, method, **kwargs):
            mock_resp = MagicMock()
            if 'files' in path: # get_change_file_pull_request
                mock_resp.data = BytesIO(b'[]')
                return mock_resp
            if 'commits' in path:
                mock_resp.data = BytesIO(b'[]')
                return mock_resp

            # Default fallback
            mock_resp.data = BytesIO(b'{}')
            return mock_resp

        mock_api_client.call_api.side_effect = call_api_side_effect

        from pr_agent.git_providers.gitea_provider import RepoApi

        client = mock_api_client
        repo_api = RepoApi(client)

        # Now test methods independently

        # 1. get_change_file_pull_request
        mock_api_client.reset_mock()
        mock_resp = MagicMock()
        mock_resp.data = BytesIO(b'[]')
        mock_api_client.call_api.return_value = mock_resp

        repo_api.get_change_file_pull_request('owner', 'repo', 123)

        args, kwargs = mock_api_client.call_api.call_args
        assert '/repos/owner/repo/pulls/123/files' in args[0]
        assert kwargs.get('auth_settings') == ['AuthorizationHeaderToken']
        assert 'token=' not in args[0]

        # 2. get_pull_request_diff
        mock_api_client.reset_mock()
        mock_resp = MagicMock()
        mock_resp.data = BytesIO(b'diff content')
        mock_api_client.call_api.return_value = mock_resp

        repo_api.get_pull_request_diff('owner', 'repo', 123)

        args, kwargs = mock_api_client.call_api.call_args
        assert args[0] == '/repos/owner/repo/pulls/123.diff'
        assert kwargs.get('auth_settings') == ['AuthorizationHeaderToken']

        # 3. get_languages
        mock_api_client.reset_mock()
        mock_resp.data = BytesIO(b'{"Python": 100}')
        mock_api_client.call_api.return_value = mock_resp

        repo_api.get_languages('owner', 'repo')

        args, kwargs = mock_api_client.call_api.call_args
        assert args[0] == '/repos/owner/repo/languages'
        assert kwargs.get('auth_settings') == ['AuthorizationHeaderToken']

        # 4. get_file_content
        mock_api_client.reset_mock()
        mock_resp.data = BytesIO(b'content')
        mock_api_client.call_api.return_value = mock_resp

        repo_api.get_file_content('owner', 'repo', 'sha1', 'file.txt')

        args, kwargs = mock_api_client.call_api.call_args
        assert args[0] == '/repos/owner/repo/raw/file.txt'
        assert kwargs.get('query_params') == [('ref', 'sha1')]
        assert kwargs.get('auth_settings') == ['AuthorizationHeaderToken']

        # 5. get_pr_commits
        mock_api_client.reset_mock()
        mock_resp.data = BytesIO(b'[]')
        mock_api_client.call_api.return_value = mock_resp

        repo_api.get_pr_commits('owner', 'repo', 123)

        args, kwargs = mock_api_client.call_api.call_args
        assert args[0] == '/repos/owner/repo/pulls/123/commits'
        assert kwargs.get('auth_settings') == ['AuthorizationHeaderToken']

    @patch('pr_agent.git_providers.gitea_provider.get_settings')
    @patch('pr_agent.git_providers.gitea_provider.giteapy.ApiClient')
    @patch('pr_agent.git_providers.gitea_provider.filter_ignored')
    def test_init_uses_pr_commits_not_repo_commits(self, mock_filter, mock_api_client_cls, mock_get_settings):
        """Verify __init__ fetches PR-specific commits, not all repo commits.

        Regression test for https://github.com/qodo-ai/pr-agent/issues/2206
        """
        settings = MagicMock()
        settings.get.side_effect = lambda k, d=None: {
            'GITEA.URL': 'https://gitea.example.com',
            'GITEA.PERSONAL_ACCESS_TOKEN': 'test-token',
            'GITEA.REPO_SETTING': None,
            'GITEA.SKIP_SSL_VERIFICATION': False,
            'GITEA.SSL_CA_CERT': None,
        }.get(k, d)
        mock_get_settings.return_value = settings

        mock_api_client = mock_api_client_cls.return_value
        mock_api_client.configuration.api_key = {}

        # Track which endpoints are called
        called_paths = []

        pr_commits_json = json.dumps([
            {"sha": "older_commit_sha", "html_url": "https://gitea.example.com/owner/repo/commit/older_commit_sha"},
            {"sha": "latest_commit_sha", "html_url": "https://gitea.example.com/owner/repo/commit/latest_commit_sha"},
        ])

        mock_pr = MagicMock()
        mock_pr.head.sha = "latest_commit_sha"
        mock_pr.base.sha = "base_sha"
        mock_pr.base.ref = "main"

        def call_api_side_effect(path, method, **kwargs):
            called_paths.append(path)
            mock_resp = MagicMock()
            if 'pulls' in path and 'files' in path:
                mock_resp.data = BytesIO(b'[]')
            elif 'pulls' in path and 'commits' in path:
                mock_resp.data = BytesIO(pr_commits_json.encode())
            elif path.endswith('.diff'):
                mock_resp.data = BytesIO(b'')
            else:
                mock_resp.data = BytesIO(b'{}')
            return mock_resp

        mock_api_client.call_api.side_effect = call_api_side_effect
        mock_filter.side_effect = lambda files, **kw: files

        # Mock repo_get_pull_request to return our PR object
        with patch('pr_agent.git_providers.gitea_provider.giteapy.RepositoryApi.repo_get_pull_request', return_value=mock_pr):
            from pr_agent.git_providers.gitea_provider import GiteaProvider
            provider = GiteaProvider("https://gitea.example.com/owner/repo/pulls/42")

        # Verify PR-specific commits endpoint was called (not repo-level commits)
        pr_commits_calls = [p for p in called_paths if 'commits' in p]
        assert any('/pulls/' in p and '/commits' in p for p in pr_commits_calls), \
            f"Expected PR-specific commits endpoint, got: {pr_commits_calls}"
        assert not any(p.endswith('/commits') and '/pulls/' not in p for p in pr_commits_calls), \
            f"Should not call repo-level commits endpoint, got: {pr_commits_calls}"

        # Verify last_commit has the latest PR commit's SHA
        assert provider.last_commit is not None
        assert provider.last_commit.sha == "latest_commit_sha"
        assert provider.last_commit.html_url == "https://gitea.example.com/owner/repo/commit/latest_commit_sha"
