from unittest.mock import MagicMock, patch

import pytest

from pr_agent.algo.types import EDIT_TYPE
from pr_agent.git_providers.gitea_provider import GiteaProvider


class TestGiteaProvider:
    """Unit-tests for GiteaProvider following project style (explicit object construction, minimal patching)."""

    def _provider(self):
        """Create provider instance with patched settings and avoid real HTTP calls."""
        with patch('pr_agent.git_providers.gitea_provider.get_settings') as mock_get_settings, \
                patch('requests.get') as mock_get:
            settings = MagicMock()
            settings.get.side_effect = lambda k, d=None: {
                'GITEA.URL': 'https://gitea.example.com',
                'GITEA.TOKEN': 'test-token'
            }.get(k, d)
            mock_get_settings.return_value = settings
            # Stub the PR fetch triggered during provider initialization
            pr_resp = MagicMock()
            pr_resp.json.return_value = {
                'title': 'stub',
                'body': 'stub',
                'head': {'ref': 'main'},
                'user': {'id': 1}
            }
            pr_resp.raise_for_status = MagicMock()
            mock_get.return_value = pr_resp
            return GiteaProvider('https://gitea.example.com/owner/repo/pulls/123')

    # ---------------- URL parsing ----------------
    def test_parse_pr_url_valid(self):
        owner, repo, pr_num = GiteaProvider._parse_pr_url('https://gitea.example.com/owner/repo/pulls/123')
        assert (owner, repo, pr_num) == ('owner', 'repo', '123')

    def test_parse_pr_url_invalid(self):
        with pytest.raises(ValueError):
            GiteaProvider._parse_pr_url('https://gitea.example.com/owner/repo')

    # ---------------- simple getters ----------------
    def test_get_files(self):
        provider = self._provider()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{'filename': 'a.txt'}, {'filename': 'b.txt'}]
        mock_resp.raise_for_status = MagicMock()
        with patch('requests.get', return_value=mock_resp) as mock_get:
            assert provider.get_files() == ['a.txt', 'b.txt']
            mock_get.assert_called_once()

    def test_get_diff_files(self):
        provider = self._provider()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {'filename': 'f1', 'previous_filename': 'old_f1', 'status': 'renamed', 'patch': ''},
            {'filename': 'f2', 'status': 'added', 'patch': ''},
            {'filename': 'f3', 'status': 'deleted', 'patch': ''},
            {'filename': 'f4', 'status': 'modified', 'patch': ''}
        ]
        mock_resp.raise_for_status = MagicMock()
        with patch('requests.get', return_value=mock_resp):
            res = provider.get_diff_files()
            assert [f.edit_type for f in res] == [EDIT_TYPE.RENAMED, EDIT_TYPE.ADDED, EDIT_TYPE.DELETED,
                                                  EDIT_TYPE.MODIFIED]

    # ---------------- publishing methods ----------------
    def test_publish_description(self):
        provider = self._provider()
        mock_resp = MagicMock();
        mock_resp.raise_for_status = MagicMock()
        with patch('requests.patch', return_value=mock_resp) as mock_patch:
            provider.publish_description('t', 'b');
            mock_patch.assert_called_once()

    def test_publish_comment(self):
        provider = self._provider()
        mock_resp = MagicMock();
        mock_resp.raise_for_status = MagicMock()
        with patch('requests.post', return_value=mock_resp) as mock_post:
            provider.publish_comment('c');
            mock_post.assert_called_once()

    def test_publish_inline_comment(self):
        provider = self._provider()
        mock_resp = MagicMock();
        mock_resp.raise_for_status = MagicMock()
        with patch('requests.post', return_value=mock_resp) as mock_post:
            provider.publish_inline_comment('body', 'file', '10');
            mock_post.assert_called_once()

    # ---------------- labels & reactions ----------------
    def test_get_pr_labels(self):
        provider = self._provider()
        mock_resp = MagicMock();
        mock_resp.raise_for_status = MagicMock();
        mock_resp.json.return_value = [{'name': 'l1'}]
        with patch('requests.get', return_value=mock_resp):
            assert provider.get_pr_labels() == ['l1']

    def test_add_eyes_reaction(self):
        provider = self._provider()
        mock_resp = MagicMock();
        mock_resp.raise_for_status = MagicMock();
        mock_resp.json.return_value = {'id': 7}
        with patch('requests.post', return_value=mock_resp):
            assert provider.add_eyes_reaction(1) == 7

    # ---------------- commit messages & url helpers ----------------
    def test_get_commit_messages(self):
        provider = self._provider()
        mock_resp = MagicMock();
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {'commit': {'message': 'm1'}}, {'commit': {'message': 'm2'}}]
        with patch('requests.get', return_value=mock_resp):
            assert provider.get_commit_messages() == ['m1', 'm2']

    def test_git_url_helpers(self):
        provider = self._provider()
        issues_url = 'https://gitea.example.com/owner/repo/pulls/3'
        assert provider.get_git_repo_url(issues_url) == 'https://gitea.example.com/owner/repo.git'
        prefix, suffix = provider.get_canonical_url_parts('https://gitea.example.com/owner/repo.git', 'dev')
        assert prefix == 'https://gitea.example.com/owner/repo/src/branch/dev'
        assert suffix == ''
