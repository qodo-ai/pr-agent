from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse
import requests
from pr_agent.git_providers.git_provider import GitProvider
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger
from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo


class GiteaProvider(GitProvider):
    """
    Implements GitProvider for Gitea/Forgejo API v1.
    """

    def __init__(self, pr_url: Optional[str] = None, incremental: Optional[bool] = False):
        self.gitea_url = get_settings().get("GITEA.URL", None)
        self.gitea_token = get_settings().get("GITEA.TOKEN", None)
        if not self.gitea_url:
            raise ValueError("GITEA.URL is not set in the config file")
        if not self.gitea_token:
            raise ValueError("GITEA.TOKEN is not set in the config file")
        self.headers = {
            'Authorization': f'token {self.gitea_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.owner = None
        self.repo = None
        self.pr_num = None
        self.pr = None
        self.pr_url = pr_url
        self.incremental = incremental
        if pr_url:
            self.set_pr(pr_url)

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, str, str]:
        """
        Parse Gitea PR URL to (owner, repo, pr_number)
        """
        parsed_url = urlparse(pr_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 4 or path_parts[2] != 'pulls':
            raise ValueError(f"Invalid PR URL format: {pr_url}")
        return path_parts[0], path_parts[1], path_parts[3]

    def set_pr(self, pr_url: str):
        self.owner, self.repo, self.pr_num = self._parse_pr_url(pr_url)
        self.pr = self._get_pr()

    def _get_pr(self):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{self.pr_num}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def is_supported(self, capability: str) -> bool:
        # Gitea/Forgejo supports most capabilities
        return True

    def get_files(self) -> List[str]:
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{self.pr_num}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return [file['filename'] for file in response.json()]

    def get_diff_files(self) -> List[FilePatchInfo]:
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{self.pr_num}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        diff_files = []
        for file in response.json():
            edit_type = EDIT_TYPE.MODIFIED
            if file.get('status') == 'added':
                edit_type = EDIT_TYPE.ADDED
            elif file.get('status') == 'deleted':
                edit_type = EDIT_TYPE.DELETED
            elif file.get('status') == 'renamed':
                edit_type = EDIT_TYPE.RENAMED

            diff_files.append(
                FilePatchInfo(
                    file.get('previous_filename', ''),
                    file.get('filename', ''),
                    file.get('patch', ''),
                    file['filename'],
                    edit_type=edit_type,
                    old_filename=file.get('previous_filename')
                )
            )
        return diff_files

    def publish_description(self, pr_title: str, pr_body: str):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{self.pr_num}"
        data = {'title': pr_title, 'body': pr_body}
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/{self.pr_num}/comments"
        data = {'body': pr_comment}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str,
                               original_suggestion=None):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{self.pr_num}/reviews"

        data = {
            'event': 'COMMENT',
            'body': original_suggestion or '',
            'commit_id': self.pr.get('head', {}).get('sha', ''),
            'comments': [{
                'body': body,
                'path': relevant_file,
                'line': int(relevant_line_in_file)
            }]
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

    def publish_inline_comments(self, comments: list[dict]):
        for comment in comments:
            try:
                self.publish_inline_comment(
                    comment['body'],
                    comment['relevant_file'],
                    comment['relevant_line_in_file'],
                    comment.get('original_suggestion')
                )
            except Exception as e:
                get_logger().error(f"Failed to publish inline comment on {comment.get('relevant_file')}: {e}")

    def publish_code_suggestions(self, code_suggestions: list) -> bool:
        overall_success = True
        for suggestion in code_suggestions:
            try:
                self.publish_inline_comment(
                    suggestion['body'],
                    suggestion['relevant_file'],
                    suggestion['relevant_line_in_file'],
                    suggestion.get('original_suggestion')
                )
            except Exception as e:
                overall_success = False
                get_logger().error(
                    f"Failed to publish code suggestion on {suggestion.get('relevant_file')}: {e}")
        return overall_success

    def publish_labels(self, labels):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/{self.pr_num}/labels"
        data = {'labels': labels}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

    def get_pr_labels(self, update=False):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/{self.pr_num}/labels"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return [label['name'] for label in response.json()]

    def get_issue_comments(self):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/{self.pr_num}/comments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def remove_initial_comment(self):
        # Implementation depends on how you track the initial comment
        pass

    def remove_comment(self, comment):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/comments/{comment['id']}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

    def add_eyes_reaction(self, issue_comment_id: int, disable_eyes: bool = False) -> Optional[int]:
        if disable_eyes:
            return None
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/comments/{issue_comment_id}/reactions"
        data = {'content': 'eyes'}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()['id']

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/issues/comments/{issue_comment_id}/reactions/{reaction_id}"
        response = requests.delete(url, headers=self.headers)
        return response.status_code == 204

    def get_commit_messages(self):
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{self.pr_num}/commits"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return [commit['commit']['message'] for commit in response.json()]

    def get_pr_branch(self):
        return self.pr['head']['ref']

    def get_user_id(self):
        return self.pr['user']['id']

    def get_pr_description_full(self) -> str:
        return self.pr['body'] or ''

    def get_git_repo_url(self, issues_or_pr_url: str) -> str:
        try:
            parsed_url = urlparse(issues_or_pr_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError(f"Invalid URL format: {issues_or_pr_url}")
            return f"{parsed_url.scheme}://{parsed_url.netloc}/{path_parts[0]}/{path_parts[1]}.git"
        except Exception as e:
            get_logger().exception(f"Failed to get git repo URL from: {issues_or_pr_url}")
            return ""

    def get_canonical_url_parts(self, repo_git_url: str, desired_branch: str) -> Tuple[str, str]:
        try:
            parsed_url = urlparse(repo_git_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError(f"Invalid git repo URL format: {repo_git_url}")

            repo_name = path_parts[1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]

            prefix = f"{parsed_url.scheme}://{parsed_url.netloc}/{path_parts[0]}/{repo_name}/src/branch/{desired_branch}"
            suffix = ""
            return prefix, suffix
        except Exception as e:
            get_logger().exception(f"Failed to get canonical URL parts from: {repo_git_url}")
            return ("", "")

    def get_languages(self) -> Dict[str, float]:
        """
        Get the languages used in the repository and their percentages.
        Returns a dictionary mapping language names to their percentage of use.
        """
        if not self.owner or not self.repo:
            return {}
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}/languages"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_repo_settings(self) -> Dict:
        """
        Get repository settings and configuration.
        Returns a dictionary containing repository settings.
        """
        if not self.owner or not self.repo:
            return {}
        url = f"{self.gitea_url}/api/v1/repos/{self.owner}/{self.repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
